import time
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.complaint import Complaint
from app.models.user import User
from app.verification.schemas import VerificationReport, VerificationStatus
from app.verification.abstention.query_analyzer import query_analyzer, QueryIntent, QueryAnalysis
from app.verification.abstention.sufficiency_checker import (
    sufficiency_checker,
    SufficiencyStatus,
    SufficiencyCheckResult
)
from app.verification.correction.correction_controller import correction_controller

logger = logging.getLogger("uvicorn.error")


class AbstentionEngine:
    """
    Tier 3 Master Abstention Decision Engine.
    Executes the 3-tier protection pipeline:
      Tier 1: Pre-generation query analysis, citizen authorization, and evidence sufficiency check.
      Tier 2: Controlled LLM generation and claim-level verification (if sufficient).
      Tier 3: Final multi-factor decision policy (SHOW, CORRECT, ABSTAIN).
    """

    def process_and_decide(
        self,
        query: str,
        evidence_pool: List[Any],
        db: Optional[Session] = None,
        current_user: Optional[User] = None,
        explicit_complaint_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes complete Abstention Decision Pipeline.
        Returns:
        {
            "final_answer": str,
            "decision": "SHOW" | "CORRECT" | "ABSTAIN",
            "verification_status": "SUPPORTED" | "CONTRADICTED" | "INSUFFICIENT_EVIDENCE",
            "confidence": float,
            "is_abstained": bool,
            "abstention_reason": str | None,
            "missing_fields": list,
            "pre_generation_halt": bool,
            "elapsed_ms": float,
            "final_report": VerificationReport | None
        }
        """
        start_time = time.time()

        # ------------------------------------------------------------------ #
        # Step 1: Query Intent Analysis                                      #
        # ------------------------------------------------------------------ #
        analysis: QueryAnalysis = query_analyzer.analyze_query(
            query=query,
            explicit_complaint_id=explicit_complaint_id
        )

        complaint_obj: Optional[Complaint] = None

        # ------------------------------------------------------------------ #
        # Step 2: Citizen Authorization & Complaint Entity Lookup            #
        # ------------------------------------------------------------------ #
        if analysis.complaint_number and db is not None:
            complaint_obj = (
                db.query(Complaint)
                .filter(Complaint.complaint_number == analysis.complaint_number)
                .first()
            )

            # Security Check: Authorization
            if complaint_obj and current_user:
                # If citizen role, ensure complaint belongs to current user
                is_citizen = getattr(current_user.role, "value", str(current_user.role)) == "CITIZEN"
                if is_citizen and complaint_obj.user_id != current_user.id:
                    logger.warning(
                        f"[Security Alert] Citizen user_id={current_user.id} attempted unauthorized access "
                        f"to complaint {analysis.complaint_number} (owner user_id={complaint_obj.user_id})."
                    )
                    elapsed_ms = round((time.time() - start_time) * 1000.0, 2)
                    return {
                        "final_answer": "You are not authorized to view the details of this complaint record.",
                        "decision": "ABSTAIN",
                        "verification_status": VerificationStatus.INSUFFICIENT_EVIDENCE.value,
                        "confidence": 0.0,
                        "is_abstained": True,
                        "abstention_reason": "UNAUTHORIZED_ACCESS",
                        "missing_fields": [],
                        "pre_generation_halt": True,
                        "elapsed_ms": elapsed_ms,
                        "final_report": None
                    }

        # ------------------------------------------------------------------ #
        # Step 3: Tier 1 Pre-Generation Sufficiency Checking                 #
        # ------------------------------------------------------------------ #
        # Check A: If query targets a specific complaint record
        if analysis.requires_complaint_record and analysis.complaint_number:
            suff_res: SufficiencyCheckResult = sufficiency_checker.check_complaint_record_sufficiency(
                complaint=complaint_obj,
                required_fields=analysis.required_fields,
                complaint_number=analysis.complaint_number
            )

            if not suff_res.can_proceed_to_generation:
                logger.info(
                    f"[Abstention Engine] Halting pre-generation: {suff_res.status.value} - {suff_res.reason}"
                )
                elapsed_ms = round((time.time() - start_time) * 1000.0, 2)
                return {
                    "final_answer": suff_res.safe_refusal_message or "Information unavailable.",
                    "decision": "ABSTAIN",
                    "verification_status": VerificationStatus.INSUFFICIENT_EVIDENCE.value,
                    "confidence": 0.0,
                    "is_abstained": True,
                    "abstention_reason": suff_res.status.value,
                    "missing_fields": suff_res.missing_fields,
                    "pre_generation_halt": True,
                    "elapsed_ms": elapsed_ms,
                    "final_report": None
                }

        # Check B: Source conflicts in evidence pool
        conflict_res = sufficiency_checker.detect_conflicts(evidence_pool)
        if not conflict_res.can_proceed_to_generation:
            elapsed_ms = round((time.time() - start_time) * 1000.0, 2)
            return {
                "final_answer": conflict_res.safe_refusal_message or "Conflicting documents detected.",
                "decision": "ABSTAIN",
                "verification_status": VerificationStatus.INSUFFICIENT_EVIDENCE.value,
                "confidence": 0.0,
                "is_abstained": True,
                "abstention_reason": conflict_res.status.value,
                "missing_fields": [],
                "pre_generation_halt": True,
                "elapsed_ms": elapsed_ms,
                "final_report": None
            }

        # Check C: Knowledge base sufficiency if no complaint record targeted
        if not analysis.complaint_number:
            kb_res = sufficiency_checker.check_knowledge_base_sufficiency(evidence_pool)
            if not kb_res.can_proceed_to_generation:
                elapsed_ms = round((time.time() - start_time) * 1000.0, 2)
                return {
                    "final_answer": kb_res.safe_refusal_message or "No relevant guidelines available.",
                    "decision": "ABSTAIN",
                    "verification_status": VerificationStatus.INSUFFICIENT_EVIDENCE.value,
                    "confidence": 0.0,
                    "is_abstained": True,
                    "abstention_reason": kb_res.status.value,
                    "missing_fields": kb_res.missing_fields,
                    "pre_generation_halt": True,
                    "elapsed_ms": elapsed_ms,
                    "final_report": None
                }

        # ------------------------------------------------------------------ #
        # Step 4: Tier 2 Generation & CVE Correction Loop                   #
        # ------------------------------------------------------------------ #
        corr_res = correction_controller.process_and_correct(
            question=query,
            evidence_pool=evidence_pool,
            db=db
        )

        final_answer = corr_res["final_answer"]
        decision = corr_res["action_taken"]
        overall_status = corr_res["overall_status"]
        confidence = corr_res["overall_confidence"]
        report = corr_res.get("final_report")

        # ------------------------------------------------------------------ #
        # Step 5: Tier 3 Final Abstention Decision Check                     #
        # ------------------------------------------------------------------ #
        is_abstained = False
        abstention_reason = None

        if decision == "ABSTAIN" or overall_status == VerificationStatus.INSUFFICIENT_EVIDENCE.value:
            is_abstained = True
            abstention_reason = "POST_GENERATION_INSUFFICIENT_EVIDENCE"
            if not final_answer or final_answer.startswith("I could not find"):
                final_answer = (
                    "I could not find sufficient verified information in village records to answer this question. "
                    "Please contact the Gram Panchayat office."
                )

        elapsed_ms = round((time.time() - start_time) * 1000.0, 2)

        return {
            "final_answer": final_answer,
            "decision": decision,
            "verification_status": overall_status,
            "confidence": confidence,
            "is_abstained": is_abstained,
            "abstention_reason": abstention_reason,
            "missing_fields": [],
            "pre_generation_halt": False,
            "elapsed_ms": elapsed_ms,
            "final_report": report
        }


abstention_engine = AbstentionEngine()
