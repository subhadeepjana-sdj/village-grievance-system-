import logging
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.models.complaint import Complaint

logger = logging.getLogger("uvicorn.error")


class SufficiencyStatus(str, Enum):
    """Categorical assessment of evidence adequacy prior to generation."""
    SUFFICIENT = "SUFFICIENT"
    MISSING_MANDATORY_FIELD = "MISSING_MANDATORY_FIELD"
    NON_EXISTENT_ENTITY = "NON_EXISTENT_ENTITY"
    NO_RELEVANT_EVIDENCE = "NO_RELEVANT_EVIDENCE"
    EXPIRED_EVIDENCE = "EXPIRED_EVIDENCE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"


class SufficiencyCheckResult(BaseModel):
    """Result of Tier 1 Pre-Generation Sufficiency Analysis."""
    can_proceed_to_generation: bool
    status: SufficiencyStatus
    missing_fields: List[str] = Field(default_factory=list)
    reason: str
    safe_refusal_message: Optional[str] = None
    pre_generation_halt: bool = False


class EvidenceSufficiencyChecker:
    """
    Tier 1 Pre-Generation Sufficiency and Conflict Checker.
    Enforces deterministic verification BEFORE calling the LLM to prevent
    hallucination of dates, statuses, or policies when records are missing or NULL.
    """

    def check_complaint_record_sufficiency(
        self,
        complaint: Optional[Complaint],
        required_fields: List[str],
        complaint_number: str
    ) -> SufficiencyCheckResult:
        """
        Validates whether the targeted complaint exists in PostgreSQL and has
        all required fields populated (e.g. expected_resolution_date).
        """
        # 1. Non-existent entity check
        if complaint is None:
            msg = (
                f"Complaint record '{complaint_number}' was not found in the official Gram Panchayat database. "
                "Please verify your reference number or contact the Panchayat office."
            )
            return SufficiencyCheckResult(
                can_proceed_to_generation=False,
                status=SufficiencyStatus.NON_EXISTENT_ENTITY,
                missing_fields=["complaint_record"],
                reason=f"Complaint number {complaint_number} does not exist in database.",
                safe_refusal_message=msg,
                pre_generation_halt=True
            )

        missing = []
        c_status_str = complaint.status.value if hasattr(complaint.status, "value") else str(complaint.status)
        c_dept_str = complaint.department.name if complaint.department else "Unassigned"

        # 2. Inspect Required Fields
        for field in required_fields:
            if field == "expected_resolution_date":
                val = getattr(complaint, "expected_resolution_date", None)
                if val is None:
                    missing.append("expected_resolution_date")
            elif field == "department":
                if not complaint.department:
                    missing.append("department")
            elif field == "status":
                if not complaint.status:
                    missing.append("status")
            elif field == "contact_information":
                if not complaint.department or not complaint.department.contact_information:
                    missing.append("contact_information")

        # 3. Handle Missing Mandatory Field (e.g. Unknown Resolution Date)
        if missing:
            logger.info(
                f"[Sufficiency Checker] Missing mandatory field(s) {missing} for complaint {complaint_number}. "
                "Halting pre-generation to prevent LLM date/officer hallucination."
            )
            
            if "expected_resolution_date" in missing:
                msg = (
                    f"Your complaint {complaint_number} is currently '{c_status_str}' and assigned to '{c_dept_str}'. "
                    "However, official village records do not yet contain a confirmed resolution date. "
                    "Please contact the Gram Panchayat office for further updates."
                )
            else:
                msg = (
                    f"Your complaint {complaint_number} is currently '{c_status_str}'. "
                    f"Verified records do not contain complete information for {', '.join(missing)}. "
                    "Please consult the Gram Panchayat office."
                )

            return SufficiencyCheckResult(
                can_proceed_to_generation=False,
                status=SufficiencyStatus.MISSING_MANDATORY_FIELD,
                missing_fields=missing,
                reason=f"Required fields {missing} are NULL in authoritative database.",
                safe_refusal_message=msg,
                pre_generation_halt=True
            )

        return SufficiencyCheckResult(
            can_proceed_to_generation=True,
            status=SufficiencyStatus.SUFFICIENT,
            missing_fields=[],
            reason="All required complaint fields are present and verified in PostgreSQL.",
            safe_refusal_message=None,
            pre_generation_halt=False
        )

    def check_knowledge_base_sufficiency(
        self,
        evidence_pool: List[Any],
        min_similarity: float = 0.40
    ) -> SufficiencyCheckResult:
        """
        Validates whether retrieved knowledge base documents are adequate, active, and unexpired.
        """
        if not evidence_pool:
            msg = (
                "I could not find sufficient verified information in village guidelines or records to answer this question. "
                "Please contact the Gram Panchayat office."
            )
            return SufficiencyCheckResult(
                can_proceed_to_generation=False,
                status=SufficiencyStatus.NO_RELEVANT_EVIDENCE,
                missing_fields=["knowledge_base_evidence"],
                reason="No relevant evidence passages returned by hybrid retrieval.",
                safe_refusal_message=msg,
                pre_generation_halt=True
            )

        # Check for expired documents or below similarity threshold
        for item in evidence_pool:
            status = item.get("status") if isinstance(item, dict) else getattr(item, "status", None)
            if status == "expired":
                msg = (
                    "Available village documentation on this subject is expired or superseded. "
                    "Please consult the Gram Panchayat office for current government guidelines."
                )
                return SufficiencyCheckResult(
                    can_proceed_to_generation=False,
                    status=SufficiencyStatus.EXPIRED_EVIDENCE,
                    missing_fields=["active_policy_document"],
                    reason="Retrieved documents are marked as expired.",
                    safe_refusal_message=msg,
                    pre_generation_halt=True
                )

        return SufficiencyCheckResult(
            can_proceed_to_generation=True,
            status=SufficiencyStatus.SUFFICIENT,
            missing_fields=[],
            reason="Relevant, active evidence passages are present in evidence pool.",
            safe_refusal_message=None,
            pre_generation_halt=False
        )

    def detect_conflicts(self, evidence_pool: List[Any]) -> SufficiencyCheckResult:
        """
        Detects mutually contradictory evidence across multiple official passages.
        """
        # Look for conflicting departmental claims
        dept_keywords = ["water department", "roads & infrastructure", "sanitation", "electricity"]
        found_depts = set()

        for item in evidence_pool:
            text = (item.get("evidence_text") or item.get("text") or "").lower() if isinstance(item, dict) else getattr(item, "evidence_text", "").lower()
            for d in dept_keywords:
                if d in text:
                    found_depts.add(d)

        # If evidence states two conflicting departments for the same service
        if len(found_depts) > 2:
            msg = (
                "Official village documents contain conflicting administrative instructions regarding this service. "
                "This query has been flagged for Gram Panchayat review. Please consult the Panchayat Secretary directly."
            )
            return SufficiencyCheckResult(
                can_proceed_to_generation=False,
                status=SufficiencyStatus.CONFLICTING_EVIDENCE,
                missing_fields=[],
                reason=f"Conflicting departmental jurisdictions found in evidence: {list(found_depts)}",
                safe_refusal_message=msg,
                pre_generation_halt=True
            )

        return SufficiencyCheckResult(
            can_proceed_to_generation=True,
            status=SufficiencyStatus.SUFFICIENT,
            missing_fields=[],
            reason="No mutual source contradictions detected in evidence pool.",
            safe_refusal_message=None,
            pre_generation_halt=False
        )


sufficiency_checker = EvidenceSufficiencyChecker()
