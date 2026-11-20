import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.services.llm_service import llm_service
from app.verification.schemas import VerificationReport, VerificationStatus
from app.verification.engine.decision_engine import decision_engine

logger = logging.getLogger("uvicorn.error")

class AnswerCorrector:
    """
    Manages the iterative answer regeneration and correction loop.
    Enforces negative constraints and bounds retries to prevent hallucination cycles.
    """
    MAX_RETRIES = 2

    def correct_and_verify(
        self,
        question: str,
        initial_answer: str,
        initial_report: VerificationReport,
        evidence_pool: List[Any],
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Executes bounded correction loop:
        Candidate Answer -> Detect Contradictions -> Re-synthesize -> Re-verify.
        """
        current_answer = initial_answer
        current_report = initial_report
        attempt = 0

        while current_report.action_taken == "CORRECT" and attempt < self.MAX_RETRIES:
            attempt += 1
            logger.warning(
                f"[CVE Correction Loop - Attempt #{attempt}] Contradictions detected. "
                "Regenerating answer with strict negative-constraint directives..."
            )

            # Build targeted correction prompt
            correction_prompt = (
                f"CORRECTION DIRECTIVE: The previous answer contained factual contradictions:\n"
                f"{current_report.correction_directive}\n\n"
                f"Strictly re-synthesize the response to the user's question using only verified facts.\n"
                f"Remove any refuted statements.\n"
                f"Question: {question}"
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

        # If contradiction STILL persists after max retries, apply deterministic fallback
        if current_report.overall_status == VerificationStatus.CONTRADICTED:
            logger.warning("Contradiction persisted after max retries. Overriding with strict verified facts.")
            current_answer = self._build_deterministic_override(current_report, evidence_pool)
            current_report = decision_engine.verify_answer(
                answer=current_answer,
                evidence_pool=evidence_pool,
                db=db
            )
            # If a grounded override was produced, return it directly
            if current_answer and not current_answer.startswith("I could not find"):
                return {
                    "final_answer": current_answer,
                    "final_report": current_report,
                    "attempts": attempt + 1
                }

        # If overall status is INSUFFICIENT_EVIDENCE, enforce safe abstention
        if current_report.overall_status == VerificationStatus.INSUFFICIENT_EVIDENCE:
            current_answer = (
                "I could not find sufficient verified information in village records to answer this question. "
                "Please contact the Gram Panchayat office."
            )

        return {
            "final_answer": current_answer,
            "final_report": current_report,
            "attempts": attempt + 1
        }

    def _build_deterministic_override(
        self,
        report: VerificationReport,
        evidence_pool: List[Any]
    ) -> str:
        """Constructs an unembellished factual response directly from verified evidence items."""
        # 1. Check if structured complaint records exist
        for item in evidence_pool:
            if isinstance(item, dict) and item.get("source_type") == "COMPLAINT_RECORD":
                return f"Verified Record Correction: {item.get('evidence_text', '').strip()}"

        # 2. Check knowledge base passages
        for item in evidence_pool:
            text = item.get("evidence_text") or item.get("text") if isinstance(item, dict) else getattr(item, "evidence_text", "")
            if text:
                return f"Verified Knowledge Base Information: {text[:250].strip()}..."

        return "I could not find sufficient verified information in village records to answer this question."


answer_corrector = AnswerCorrector()
