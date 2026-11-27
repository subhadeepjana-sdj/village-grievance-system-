"""
Feature 11 — Audit Logs Models.

Provides tamper-evident event recording and AI pipeline request tracing.

Tables
------
``audit_events``
    General-purpose audit trail for every significant action in the
    system (create, update, delete, approve, reject, login, etc.).
    Each event carries a ``trace_id`` for correlation across actions
    that belong to the same user request.

``ai_request_audits``
    Detailed trace of everything that happened inside the AI pipeline
    for a single query: which model was used, which documents were
    retrieved, what verification produced, and how long it took.
"""

import enum
import uuid
import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.database.session import Base


# ------------------------------------------------------------------ #
#  Enumerations                                                       #
# ------------------------------------------------------------------ #

class AuditEventType(str, enum.Enum):
    """High-level category of an auditable action."""
    USER_ACTION = "USER_ACTION"
    AI_PIPELINE = "AI_PIPELINE"
    ADMIN_ACTION = "ADMIN_ACTION"
    SYSTEM = "SYSTEM"
    AUTH = "AUTH"


class AuditAction(str, enum.Enum):
    """Specific action within an event type."""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    QUERY = "QUERY"
    VERIFY = "VERIFY"
    CORRECT = "CORRECT"
    ABSTAIN = "ABSTAIN"
    REINDEX = "REINDEX"
    UPLOAD = "UPLOAD"
    PUBLISH = "PUBLISH"
    SUPERSEDE = "SUPERSEDE"
    REVIEW = "REVIEW"
    CONFIG_CHANGE = "CONFIG_CHANGE"


# ------------------------------------------------------------------ #
#  Audit Event                                                        #
# ------------------------------------------------------------------ #

class AuditEvent(Base):
    """
    General-purpose, immutable audit log entry.

    Every significant action — user-initiated or system-generated — is
    recorded here with:

    * A ``trace_id`` (UUID) for grouping related events.
    * ``entity_type`` / ``entity_id`` to locate *what* was affected.
    * ``old_value`` / ``new_value`` for change tracking (JSON strings).
    * ``metadata`` for free-form JSON context (IP address, user-agent, etc.).
    """
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(String(36), nullable=False, index=True, default=lambda: str(uuid.uuid4()))

    # Who
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor_role = Column(String(30), nullable=True)

    # What
    event_type = Column(String(30), nullable=False, default=AuditEventType.USER_ACTION.value)
    action = Column(String(30), nullable=False)

    # On what
    entity_type = Column(String(50), nullable=True, index=True)   # e.g. "complaint", "document_version"
    entity_id = Column(String(50), nullable=True, index=True)     # PK of the entity

    # Change payload
    old_value = Column(Text, nullable=True)   # JSON string
    new_value = Column(Text, nullable=True)   # JSON string

    # Context
    description = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)   # arbitrary JSON (IP, user-agent, etc.)
    ip_address = Column(String(45), nullable=True)

    # When
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    # Relationships
    actor = relationship("User", foreign_keys=[actor_id])


# ------------------------------------------------------------------ #
#  AI Request Audit                                                   #
# ------------------------------------------------------------------ #

class AIRequestAudit(Base):
    """
    Detailed trace of a single AI pipeline execution.

    Links back to the ``ai_queries`` and ``ai_responses`` tables via
    ``query_id``.  Records the full set of model, retrieval and
    verification parameters so an administrator can reproduce and
    explain any AI-generated answer.
    """
    __tablename__ = "ai_request_audits"

    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(String(36), nullable=False, index=True, default=lambda: str(uuid.uuid4()))

    # Links to the AI pipeline
    query_id = Column(Integer, ForeignKey("ai_queries.id", ondelete="CASCADE"), nullable=False, index=True)

    # Model information
    model_name = Column(String(100), nullable=True)
    model_version = Column(String(50), nullable=True)
    prompt_version = Column(String(50), nullable=True)

    # Retrieval information
    embedding_model = Column(String(100), nullable=True)
    retrieved_document_ids = Column(Text, nullable=True)   # JSON array of document IDs
    retrieved_chunk_ids = Column(Text, nullable=True)       # JSON array of chunk IDs
    retrieval_scores = Column(Text, nullable=True)          # JSON array of similarity scores

    # Verification results summary
    total_claims = Column(Integer, nullable=True, default=0)
    supported_claims = Column(Integer, nullable=True, default=0)
    contradicted_claims = Column(Integer, nullable=True, default=0)
    insufficient_claims = Column(Integer, nullable=True, default=0)

    # Pipeline outcome
    final_decision = Column(String(50), nullable=True)   # SHOW / CORRECT / ABSTAIN
    correction_attempts = Column(Integer, nullable=True, default=0)
    abstention_reason = Column(Text, nullable=True)

    # Performance
    response_time_ms = Column(Float, nullable=True, default=0.0)
    retrieval_time_ms = Column(Float, nullable=True, default=0.0)
    verification_time_ms = Column(Float, nullable=True, default=0.0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    query = relationship("AIQuery")
