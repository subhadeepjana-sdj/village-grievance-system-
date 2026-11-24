from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class AIQueryRequest(BaseModel):
    question: str
    configuration: Optional[str] = "rag_verification"  # baseline | rag | rag_verification
    language: Optional[str] = "en"       # ISO 639-1 language code (e.g. "en", "hi", "bn")
    department: Optional[str] = None     # Optional department filter for Qdrant retrieval


class EvidenceOut(BaseModel):
    document_id: Optional[int] = None
    chunk_id: Optional[str] = None
    similarity_score: Optional[float] = None
    evidence_text: str
    source_type: str


class VerificationResultOut(BaseModel):
    claim: str
    evidence: Optional[str] = None
    verification_result: str  # SUPPORTED / CONTRADICTED / INSUFFICIENT_EVIDENCE
    confidence: float
    reason: Optional[str] = None


class CitationOut(BaseModel):
    """Feature 7 — Structured citation in the API response."""
    citation_id: str                       # e.g. "[1]"
    claim_text: str
    source_type: str                       # COMPLAINT_RECORD / KNOWLEDGE_BASE / SCHEME
    source_id: str
    document_id: Optional[int] = None
    chunk_id: Optional[str] = None
    source_field: Optional[str] = None
    source_value: Optional[str] = None
    evidence_text: Optional[str] = None
    relevance_score: float = 0.0
    status: str = "UNVERIFIED"             # VERIFIED / INVALID / STALE
    validation_message: Optional[str] = None


class AIQueryResponse(BaseModel):
    id: int
    question: str
    answer: str
    decision: str               # SHOW / CORRECT / ABSTAIN
    verification_status: str    # SUPPORTED / CONTRADICTED / INSUFFICIENT_EVIDENCE
    confidence: float
    processing_time: float
    configuration: str
    created_at: datetime
    evidences: List[EvidenceOut] = []
    verification_results: List[VerificationResultOut] = []
    citations: List[CitationOut] = []
