"""
Feature 11 — Audit Logs Pydantic Schemas.

Covers audit-event listing, AI request audit detail, filtering
parameters, and paginated responses.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


# ------------------------------------------------------------------ #
#  Audit Event                                                        #
# ------------------------------------------------------------------ #

class AuditEventOut(BaseModel):
    """Read-only view of an audit event."""
    id: int
    trace_id: str
    actor_id: Optional[int] = None
    actor_role: Optional[str] = None
    event_type: str
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    description: Optional[str] = None
    metadata_json: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaginatedAuditEvents(BaseModel):
    """Paginated list of audit events."""
    items: List[AuditEventOut] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
    pages: int = 1


# ------------------------------------------------------------------ #
#  AI Request Audit                                                   #
# ------------------------------------------------------------------ #

class AIRequestAuditOut(BaseModel):
    """Read-only view of an AI pipeline request audit."""
    id: int
    trace_id: str
    query_id: int

    model_name: Optional[str] = None
    model_version: Optional[str] = None
    prompt_version: Optional[str] = None

    embedding_model: Optional[str] = None
    retrieved_document_ids: Optional[str] = None
    retrieved_chunk_ids: Optional[str] = None
    retrieval_scores: Optional[str] = None

    total_claims: Optional[int] = 0
    supported_claims: Optional[int] = 0
    contradicted_claims: Optional[int] = 0
    insufficient_claims: Optional[int] = 0

    final_decision: Optional[str] = None
    correction_attempts: Optional[int] = 0
    abstention_reason: Optional[str] = None

    response_time_ms: Optional[float] = 0.0
    retrieval_time_ms: Optional[float] = 0.0
    verification_time_ms: Optional[float] = 0.0

    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaginatedAIRequestAudits(BaseModel):
    """Paginated list of AI request audits."""
    items: List[AIRequestAuditOut] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
    pages: int = 1


# ------------------------------------------------------------------ #
#  Trace detail                                                       #
# ------------------------------------------------------------------ #

class TraceDetail(BaseModel):
    """Full trace: all audit events and the AI request audit sharing the same trace_id."""
    trace_id: str
    events: List[AuditEventOut] = []
    ai_request_audit: Optional[AIRequestAuditOut] = None


# ------------------------------------------------------------------ #
#  Audit statistics                                                   #
# ------------------------------------------------------------------ #

class AuditStatsOut(BaseModel):
    """Aggregate statistics for the audit log dashboard."""
    total_events: int = 0
    total_ai_audits: int = 0
    events_today: int = 0
    unique_actors_today: int = 0
    top_actions: List[dict] = []     # [{"action": "CREATE", "count": 42}, ...]
