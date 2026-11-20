from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ClaimType(str, Enum):
    """Semantic taxonomy of factual claims in village grievance redressal."""
    COMPLAINT_IDENTITY = "complaint_identity"        # e.g., "Complaint number is GRV-2024-001024"
    DEPARTMENT_ASSIGNMENT = "department_assignment"  # e.g., "Assigned to Village Water Department"
    STATUS = "status"                                # e.g., "Status is Under Review"
    RESOLUTION_TIMELINE = "resolution_timeline"      # e.g., "Will be resolved within 5 days"
    OFFICIAL_PERSONNEL = "official_personnel"        # e.g., "Handled by Panchayat Secretary Amit Roy"
    POLICY_RULE = "policy_rule"                      # e.g., "BPL card is mandatory for water subsidy"
    PROCEDURE_STEP = "procedure_step"                # e.g., "Applicant must submit Form-IV at office"
    GENERAL_FACT = "general_fact"                    # Non-specific descriptive assertion


class VerificationStatus(str, Enum):
    """Three-way verdict for claim-level verification."""
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class VerificationMode(str, Enum):
    """Which engine performed the claim check."""
    DETERMINISTIC_DB = "DETERMINISTIC_DB"   # Exact SQL lookup against authoritative tables
    NLI_MODEL = "NLI_MODEL"                 # DeBERTa-v3 cross-encoder natural language inference
    FALLBACK = "FALLBACK"                   # Heuristic lexical overlap / abstention


class AtomicClaim(BaseModel):
    """Represents a single atomic, non-decomposable factual claim."""
    claim_id: str = Field(..., description="Unique claim identifier, e.g. C1, C2")
    claim_text: str = Field(..., description="Isolated atomic proposition text")
    claim_type: ClaimType = Field(default=ClaimType.GENERAL_FACT, description="Category of fact")
    source_sentence: Optional[str] = Field(None, description="Original sentence from which claim was split")
    extracted_entities: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted key-values: complaint_id, department, status, number_of_days, etc."
    )


class EvidenceItem(BaseModel):
    """Normalized evidence piece supplied to the verification pipeline."""
    source_id: str = Field(..., description="Unique reference ID: e.g. DB_GRV_1024 or QDRANT_DOC_12_CHUNK_3")
    source_type: str = Field(..., description="COMPLAINT_RECORD | KNOWLEDGE_BASE | OFFICIAL_PORTAL")
    evidence_text: str = Field(..., description="Raw premise text against which claims are compared")
    department: Optional[str] = None
    category: Optional[str] = None
    effective_date: Optional[str] = None
    status: Optional[str] = "verified"


class ClaimVerificationResult(BaseModel):
    """Detailed verification outcome for a single atomic claim."""
    claim: AtomicClaim
    status: VerificationStatus
    confidence: float = Field(..., ge=0.0, le=1.0, description="Verification confidence score")
    verification_mode: VerificationMode
    matched_evidence_id: Optional[str] = None
    matched_evidence_text: Optional[str] = None
    probabilities: Dict[str, float] = Field(
        default_factory=dict,
        description="Class probability distribution: entailment, contradiction, neutral"
    )
    reason: str = Field(..., description="Explainable rationale behind the decision")


class VerificationReport(BaseModel):
    """Top-level aggregate verification report for an AI-generated answer."""
    verification_id: str
    original_answer: str
    overall_status: VerificationStatus
    action_taken: str = Field(..., description="SHOW | CORRECT | ABSTAIN")
    overall_confidence: float = Field(..., ge=0.0, le=100.0)
    claims: List[ClaimVerificationResult] = Field(default_factory=list)
    total_claims: int = 0
    supported_claims: int = 0
    contradicted_claims: int = 0
    insufficient_claims: int = 0
    correction_directive: Optional[str] = None
    execution_time_ms: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
