"""
Feature 10 — Knowledge Base Management Models.

Provides document versioning, processing-pipeline tracking, approval
workflow and expiry monitoring on top of the existing ``Document`` model.

Tables
------
``document_versions``
    Each row is an immutable snapshot of a document file.  A document may
    have many versions; only one can be ``Published`` at a time.

``document_processing_jobs``
    One-to-one with a ``DocumentVersion``.  Tracks the three-stage
    processing pipeline (extraction → embedding → indexing).
"""

import enum
import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database.session import Base


# ------------------------------------------------------------------ #
#  Enumerations                                                       #
# ------------------------------------------------------------------ #

class VersionStatus(str, enum.Enum):
    """Lifecycle status of a document version."""
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    PUBLISHED = "PUBLISHED"
    SUPERSEDED = "SUPERSEDED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"


class ProcessingStage(str, enum.Enum):
    """Status of an individual processing step."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


# ------------------------------------------------------------------ #
#  Document Version                                                   #
# ------------------------------------------------------------------ #

class DocumentVersion(Base):
    """
    Immutable snapshot of a document file.

    * ``document_id`` links back to the master ``documents`` table.
    * ``version_number`` is monotonically incremented per document.
    * Only one version per document may be ``PUBLISHED`` at a time.
    * ``effective_from`` / ``effective_until`` control the validity
      window for expiry monitoring.
    """
    __tablename__ = "document_versions"
    __table_args__ = (
        UniqueConstraint("document_id", "version_number", name="uq_doc_version"),
    )

    id = Column(Integer, primary_key=True, index=True)

    # --- Foreign keys ---
    document_id = Column(
        Integer,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    uploaded_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # --- Version metadata ---
    version_number = Column(Integer, nullable=False, default=1)
    file_path = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=True, index=True)      # SHA-256
    file_size_bytes = Column(Integer, nullable=True)

    # --- Approval / lifecycle ---
    status = Column(
        String(30),
        nullable=False,
        default=VersionStatus.UPLOADED.value,
    )
    change_summary = Column(Text, nullable=True)                    # What changed?
    rejection_reason = Column(Text, nullable=True)

    # --- Validity window ---
    effective_from = Column(DateTime, nullable=True)
    effective_until = Column(DateTime, nullable=True)

    # --- Timestamps ---
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # --- Relationships ---
    document = relationship("Document")
    uploader = relationship("User", foreign_keys=[uploaded_by])
    approver = relationship("User", foreign_keys=[approved_by])
    processing_job = relationship(
        "DocumentProcessingJob",
        back_populates="version",
        uselist=False,
        cascade="all, delete-orphan",
    )


# ------------------------------------------------------------------ #
#  Document Processing Job                                            #
# ------------------------------------------------------------------ #

class DocumentProcessingJob(Base):
    """
    Tracks the three-stage processing pipeline for a document version.

    Stages (in order):
        1. **extraction** — text / table extraction from PDF, DOCX, etc.
        2. **embedding**  — sentence / chunk embedding via the active model.
        3. **indexing**    — upserting vectors into Qdrant.

    Each stage has its own status column so the admin dashboard can show
    exactly *where* a job is stuck and retry from that point.
    """
    __tablename__ = "document_processing_jobs"

    id = Column(Integer, primary_key=True, index=True)

    version_id = Column(
        Integer,
        ForeignKey("document_versions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # --- Per-stage status ---
    extraction_status = Column(
        String(20),
        nullable=False,
        default=ProcessingStage.PENDING.value,
    )
    embedding_status = Column(
        String(20),
        nullable=False,
        default=ProcessingStage.PENDING.value,
    )
    indexing_status = Column(
        String(20),
        nullable=False,
        default=ProcessingStage.PENDING.value,
    )

    # --- Metrics ---
    chunks_extracted = Column(Integer, nullable=True, default=0)
    chunks_embedded = Column(Integer, nullable=True, default=0)
    chunks_indexed = Column(Integer, nullable=True, default=0)

    # --- Error reporting ---
    error_stage = Column(String(20), nullable=True)
    error_message = Column(Text, nullable=True)

    # --- Timestamps ---
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # --- Relationship ---
    version = relationship("DocumentVersion", back_populates="processing_job")
