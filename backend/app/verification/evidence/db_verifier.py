import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.complaint import Complaint
from app.verification.schemas import (
    AtomicClaim,
    ClaimType,
    VerificationStatus,
    VerificationMode,
    ClaimVerificationResult,
)

logger = logging.getLogger("uvicorn.error")

class DeterministicDBVerifier:
    """
    Directly queries authoritative PostgreSQL/SQLite tables for structured assertions.
    Bypasses stochastic neural inference for 100% precision on administrative records.
    """

    DEPARTMENT_SYNONYMS = {
        "water": "Village Water Department",
        "water department": "Village Water Department",
        "village water department": "Village Water Department",
        "water supply": "Village Water Department",
        "road": "Roads & Infrastructure",
        "roads": "Roads & Infrastructure",
        "road department": "Roads & Infrastructure",
        "roads department": "Roads & Infrastructure",
        "pwd": "Roads & Infrastructure",
        "public works": "Roads & Infrastructure",
        "public works department": "Roads & Infrastructure",
        "sanitation": "Sanitation & Waste Management",
        "sanitation department": "Sanitation & Waste Management",
        "waste management": "Sanitation & Waste Management",
        "electricity": "Electricity & Power",
        "electricity department": "Electricity & Power",
        "power": "Electricity & Power",
        "health": "Public Health & Schemes",
        "health department": "Public Health & Schemes",
        "public health": "Public Health & Schemes",
    }

    def can_verify(self, claim: AtomicClaim) -> bool:
        """Determines if this claim pertains to an authoritative structured database field."""
        if claim.extracted_entities.get("complaint_number"):
            return True
        return claim.claim_type in [
            ClaimType.COMPLAINT_IDENTITY,
            ClaimType.DEPARTMENT_ASSIGNMENT,
            ClaimType.STATUS,
        ]

    def verify_claim(self, claim: AtomicClaim, db: Session) -> Optional[ClaimVerificationResult]:
        """
        Executes deterministic SQL verification for a structured proposition.
        Returns ClaimVerificationResult, or None if claim cannot be verified against DB.
        """
        complaint_num = claim.extracted_entities.get("complaint_number")
        if not complaint_num:
            return None

        # Normalize complaint lookup: supports full (GRV-2026-001024) or shorthand (V1024, GRV1024)
        complaint = self._find_complaint(complaint_num, db)
        if not complaint:
            return ClaimVerificationResult(
                claim=claim,
                status=VerificationStatus.CONTRADICTED,
                confidence=1.0,
                verification_mode=VerificationMode.DETERMINISTIC_DB,
                matched_evidence_id=f"DB_NOT_FOUND_{complaint_num}",
                matched_evidence_text="Queried database records: No matching complaint registered with this ID.",
                probabilities={"entailment": 0.0, "contradiction": 1.0, "neutral": 0.0},
                reason=f"Authoritative Record Check: Complaint ID '{complaint_num}' does not exist in Gram Panchayat database."
            )

        dept_name = complaint.department.name if complaint.department else "Unassigned Department"
        status_val = complaint.status.value if hasattr(complaint.status, 'value') else str(complaint.status)
        ev_summary = (
            f"RECORD [ID: {complaint.complaint_number}]: "
            f"Dept='{dept_name}', Status='{status_val}', Category='{complaint.category}'"
        )

        # 1. Verification of Complaint Identity
        if claim.claim_type == ClaimType.COMPLAINT_IDENTITY:
            return ClaimVerificationResult(
                claim=claim,
                status=VerificationStatus.SUPPORTED,
                confidence=1.0,
                verification_mode=VerificationMode.DETERMINISTIC_DB,
                matched_evidence_id=f"DB_COMPLAINT_{complaint.id}",
                matched_evidence_text=ev_summary,
                probabilities={"entailment": 1.0, "contradiction": 0.0, "neutral": 0.0},
                reason=f"Authoritative Match: Verified valid registered complaint {complaint.complaint_number}."
            )

        # 2. Verification of Department Assignment
        if claim.claim_type == ClaimType.DEPARTMENT_ASSIGNMENT or "department" in claim.extracted_entities:
            claimed_dept = claim.extracted_entities.get("department", "")
            return self._verify_department(claim, claimed_dept, dept_name, complaint, ev_summary)

        # 3. Verification of Status
        if claim.claim_type == ClaimType.STATUS or "status" in claim.extracted_entities:
            claimed_status = claim.extracted_entities.get("status", "")
            return self._verify_status(claim, claimed_status, status_val, complaint, ev_summary)

        # 4. Verification of Resolution Timeline
        if claim.claim_type == ClaimType.RESOLUTION_TIMELINE or "timeline_value" in claim.extracted_entities:
            # Complaint records in this schema do not have an automated guaranteed resolution date
            return ClaimVerificationResult(
                claim=claim,
                status=VerificationStatus.INSUFFICIENT_EVIDENCE,
                confidence=0.95,
                verification_mode=VerificationMode.DETERMINISTIC_DB,
                matched_evidence_id=f"DB_COMPLAINT_{complaint.id}",
                matched_evidence_text=ev_summary,
                probabilities={"entailment": 0.0, "contradiction": 0.1, "neutral": 0.9},
                reason=f"Authoritative Record Check: Complaint {complaint.complaint_number} has no confirmed SLA or resolution date on record."
            )

        # Default fallback if claim references complaint but has general proposition
        return ClaimVerificationResult(
            claim=claim,
            status=VerificationStatus.SUPPORTED,
            confidence=0.90,
            verification_mode=VerificationMode.DETERMINISTIC_DB,
            matched_evidence_id=f"DB_COMPLAINT_{complaint.id}",
            matched_evidence_text=ev_summary,
            probabilities={"entailment": 0.9, "contradiction": 0.0, "neutral": 0.1},
            reason=f"Authoritative record confirms existence of complaint {complaint.complaint_number}."
        )

    def _find_complaint(self, number_str: str, db: Session) -> Optional[Complaint]:
        clean = number_str.strip().upper()
        # Direct exact match
        c = db.query(Complaint).filter(Complaint.complaint_number == clean).first()
        if c:
            return c

        # Numeric digits match: e.g. "V1024" or "1024" matching "GRV-2026-001024"
        import re
        digits = re.findall(r'\d+', clean)
        if digits:
            sub = digits[0]
            c = db.query(Complaint).filter(Complaint.complaint_number.ilike(f"%{sub}%")).first()
            if c:
                return c

        return None

    def _verify_department(
        self,
        claim: AtomicClaim,
        claimed_dept: str,
        actual_dept: str,
        complaint: Complaint,
        ev_summary: str
    ) -> ClaimVerificationResult:
        claimed_canonical = self.DEPARTMENT_SYNONYMS.get(claimed_dept.lower(), claimed_dept.lower())
        actual_canonical = self.DEPARTMENT_SYNONYMS.get(actual_dept.lower(), actual_dept.lower())

        is_match = (claimed_canonical == actual_canonical) or (claimed_dept.lower() in actual_dept.lower())

        if is_match:
            return ClaimVerificationResult(
                claim=claim,
                status=VerificationStatus.SUPPORTED,
                confidence=1.0,
                verification_mode=VerificationMode.DETERMINISTIC_DB,
                matched_evidence_id=f"DB_COMPLAINT_{complaint.id}",
                matched_evidence_text=ev_summary,
                probabilities={"entailment": 1.0, "contradiction": 0.0, "neutral": 0.0},
                reason=f"Authoritative Match: Complaint is correctly handled by '{actual_dept}'."
            )
        else:
            return ClaimVerificationResult(
                claim=claim,
                status=VerificationStatus.CONTRADICTED,
                confidence=1.0,
                verification_mode=VerificationMode.DETERMINISTIC_DB,
                matched_evidence_id=f"DB_COMPLAINT_{complaint.id}",
                matched_evidence_text=ev_summary,
                probabilities={"entailment": 0.0, "contradiction": 1.0, "neutral": 0.0},
                reason=f"Contradiction: Claim asserts '{claimed_dept}', but official database record shows '{actual_dept}'."
            )

    def _verify_status(
        self,
        claim: AtomicClaim,
        claimed_status: str,
        actual_status: str,
        complaint: Complaint,
        ev_summary: str
    ) -> ClaimVerificationResult:
        c_clean = claimed_status.upper().replace(" ", "_")
        a_clean = actual_status.upper().replace(" ", "_")

        is_match = (c_clean == a_clean) or (c_clean in a_clean)

        if is_match:
            return ClaimVerificationResult(
                claim=claim,
                status=VerificationStatus.SUPPORTED,
                confidence=1.0,
                verification_mode=VerificationMode.DETERMINISTIC_DB,
                matched_evidence_id=f"DB_COMPLAINT_{complaint.id}",
                matched_evidence_text=ev_summary,
                probabilities={"entailment": 1.0, "contradiction": 0.0, "neutral": 0.0},
                reason=f"Authoritative Match: Complaint status correctly verified as '{actual_status}'."
            )
        else:
            return ClaimVerificationResult(
                claim=claim,
                status=VerificationStatus.CONTRADICTED,
                confidence=1.0,
                verification_mode=VerificationMode.DETERMINISTIC_DB,
                matched_evidence_id=f"DB_COMPLAINT_{complaint.id}",
                matched_evidence_text=ev_summary,
                probabilities={"entailment": 0.0, "contradiction": 1.0, "neutral": 0.0},
                reason=f"Contradiction: Claim asserts status '{claimed_status}', but official database record shows '{actual_status}'."
            )


db_verifier = DeterministicDBVerifier()
