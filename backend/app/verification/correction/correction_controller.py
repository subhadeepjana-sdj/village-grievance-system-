import logging
import time
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.services.llm_service import llm_service
from app.verification.schemas import VerificationReport, VerificationStatus
from app.verification.engine.decision_engine import decision_engine
from app.verification.correction.prompt_builder import correction_prompt_builder

logger = logging.getLogger("uvicorn.error")

class CorrectionController:
    """
    Coordinates the iterative answer correction and regeneration state machine.
    Enforces bounded retries (max 2 retries), negative constraints, and verified deterministic fallbacks.
    """
    MAX_RETRIES = 2

    def process_and_correct(
        self,
        question: str,
        evidence_pool: List[Any],
        initial_answer: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Executes the full Feature 5 lifecycle:
          1. Generate candidate answer (if not provided).
          2. Run Claim Verification Engine (CVE).
          3. If Supported -> Accept immediately (0 retries).
          4. If Contradicted -> Loop:
             - Build prompt with negative constraints and ground truth facts.
             - Re-synthesize answer via LLM.
             - Re-verify with CVE.
             - Break if Supported or retries exhausted.
          5. If Contradiction persists after max retries -> Deterministic verified fallback.
          6. If Insufficient evidence -> Safe polite refusal (Abstain).
        """
        start_time = time.time()
        history = []

        # Step 1: Initial Answer
        if initial_answer is None or not initial_answer.strip():
            llm_res = llm_service.generate_answer(question, evidence_pool)
            current_answer = llm_res.get("answer", "")
        else:
            current_answer = initial_answer

        # Step 2: Initial Verification
        current_report = decision_engine.verify_answer(
            answer=current_answer,
            evidence_pool=evidence_pool,
            db=db
        )

        history.append({
            "attempt": 1,
            "candidate_answer": current_answer,
            "status": current_report.overall_status.value,
            "action": current_report.action_taken,
            "confidence": current_report.overall_confidence,
            "prompt_directive": None
        })

        attempt = 1

        # Step 3: Iterative Correction Loop (Max 2 Retries)
        while current_report.action_taken == "CORRECT" and (attempt - 1) < self.MAX_RETRIES:
            retry_round = attempt  # retry 1, retry 2
            attempt += 1
            logger.warning(
                f"[Correction Engine - Retry #{retry_round}] Contradiction detected. "
                "Synthesizing correction prompt with negative constraints..."
            )

            # Build targeted correction prompt with negative constraints
            correction_prompt = correction_prompt_builder.build_correction_prompt(
                question=question,
                candidate_answer=current_answer,
                report=current_report,
                evidence_pool=evidence_pool,
                attempt=retry_round
            )

            # Re-generate using LLM
            llm_res = llm_service.generate_answer(correction_prompt, evidence_pool)
            current_answer = llm_res.get("answer", "")

            # Re-verify the regenerated answer
            current_report = decision_engine.verify_answer(
                answer=current_answer,
                evidence_pool=evidence_pool,
                db=db
            )

            history.append({
                "attempt": attempt,
                "candidate_answer": current_answer,
                "status": current_report.overall_status.value,
                "action": current_report.action_taken,
                "confidence": current_report.overall_confidence,
                "prompt_directive": correction_prompt
            })

            if current_report.action_taken == "SHOW":
                logger.info(f"[Correction Engine] Answer successfully verified on attempt #{attempt}.")
                break

        # Step 4: Fallback and Safeguard Resolution
        if current_report.overall_status == VerificationStatus.CONTRADICTED:
            logger.warning("[Correction Engine] Contradiction persisted after max retries. Applying deterministic verified fallback.")
            current_answer = correction_prompt_builder.build_deterministic_fallback(current_report, evidence_pool)
            current_report = decision_engine.verify_answer(
                answer=current_answer,
                evidence_pool=evidence_pool,
                db=db
            )
            history.append({
                "attempt": attempt + 1,
                "candidate_answer": current_answer,
                "status": current_report.overall_status.value,
                "action": "SHOW" if current_report.overall_status == VerificationStatus.SUPPORTED else "ABSTAIN",
                "confidence": current_report.overall_confidence,
                "prompt_directive": "DETERMINISTIC_RECORD_OVERRIDE"
            })

        # Step 5: Safe Refusal for Insufficient Evidence
        if current_report.overall_status == VerificationStatus.INSUFFICIENT_EVIDENCE:
            current_answer = (
                "I could not find sufficient verified information in village records to answer this question. "
                "Please contact the Gram Panchayat office."
            )

        elapsed_ms = round((time.time() - start_time) * 1000.0, 2)

        return {
            "final_answer": current_answer,
            "final_report": current_report,
            "total_attempts": len(history),
            "retries_used": max(0, len(history) - 1),
            "action_taken": current_report.action_taken,
            "overall_status": current_report.overall_status.value,
            "overall_confidence": current_report.overall_confidence,
            "history": history,
            "elapsed_ms": elapsed_ms
        }


correction_controller = CorrectionController()
