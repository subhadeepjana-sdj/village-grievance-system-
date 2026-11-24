"""
Feature 7 — Citation Pydantic Schemas
======================================

Defines the data contracts for citation generation, validation, and API
responses.  Every citation is an atomic link between a *claim* in the
AI-generated answer and the *authoritative source* that supports it.

Design decisions
----------------
* ``SourceType`` mirrors the existing Evidence.source_type enum so that
  citations stay consistent with the retrieval layer.
* ``Citation`` is intentionally flat — one claim ↔ one source — which
  makes validation trivial and serialisation JSON-friendly.
* ``CitationReport`` aggregates per-response statistics for the frontend
  dashboard and research metrics.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ------------------------------------------------------------------ #
#  Enums                                                              #
# ------------------------------------------------------------------ #

class SourceType(str, Enum):
    """Authoritative source category — matches Evidence.source_type."""
    COMPLAINT_RECORD = "COMPLAINT_RECORD"
    KNOWLEDGE_BASE = "KNOWLEDGE_BASE"
    SCHEME = "SCHEME"


class CitationStatus(str, Enum):
    """Validation state of a citation after the validator runs."""
    VERIFIED = "VERIFIED"               # Source exists and field value matches
    UNVERIFIED = "UNVERIFIED"           # Not yet validated
    STALE = "STALE"                     # Source exists but may be outdated
    INVALID = "INVALID"                 # Source missing or field value mismatch
    ACCESS_DENIED = "ACCESS_DENIED"     # Citizen lacks permission to view source


# ------------------------------------------------------------------ #
#  Core Citation Model                                                #
# ------------------------------------------------------------------ #

class SourceReference(BaseModel):
    """
    Minimal reference to the authoritative origin of a cited fact.

    For COMPLAINT_RECORD sources, ``source_id`` is the complaint number
    (e.g. ``GRV-2026-001024``) and ``source_field`` names the column
    (``status``, ``department``, ``category``, …).

    For KNOWLEDGE_BASE / SCHEME sources, ``document_id`` and ``chunk_id``
    identify the Qdrant payload.
    """
    source_type: SourceType
    source_id: str = Field(..., description="Primary key or unique reference ID")
    document_id: Optional[int] = Field(None, description="Document table FK (KB/Scheme)")
    chunk_id: Optional[str] = Field(None, description="Qdrant chunk identifier")
    source_field: Optional[str] = Field(None, description="DB column name (complaint records)")
    source_value: Optional[str] = Field(None, description="Authoritative value of the field")
    page_number: Optional[int] = Field(None, description="Page or section number in doc")


class Citation(BaseModel):
    """
    One atomic citation: *claim_text* is supported by *source*.

    The ``relevance_score`` is inherited from the retrieval layer's
    similarity score (cosine / BM25) and is not re-computed.
    """
    citation_id: str = Field(..., description="Auto-generated label, e.g. [1], [2]")
    claim_text: str = Field(..., description="The factual claim being cited")
    source: SourceReference
    relevance_score: float = Field(0.0, ge=0.0, le=1.0)
    evidence_text: str = Field("", description="Verbatim passage from the source")
    status: CitationStatus = CitationStatus.UNVERIFIED
    validation_message: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ------------------------------------------------------------------ #
#  Aggregate Report                                                   #
# ------------------------------------------------------------------ #

class CitationReport(BaseModel):
    """
    Aggregated citation output for one AI response.

    The ``annotated_answer`` field contains the original answer with
    inline citation markers (``[1]``, ``[2]``, …) appended to the
    sentences they support.
    """
    response_id: int
    citations: List[Citation] = Field(default_factory=list)
    total_citations: int = 0
    verified_citations: int = 0
    invalid_citations: int = 0
    stale_citations: int = 0
    annotated_answer: Optional[str] = None
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extra provenance info: retrieval latency, model version, etc."
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
