"""
Feature 10 — Knowledge Base Management Pydantic Schemas.

Covers version creation, processing-job status, approval workflow,
expiry monitoring and paginated list responses.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


# ------------------------------------------------------------------ #
#  Processing Job                                                     #
# ------------------------------------------------------------------ #

class ProcessingJobOut(BaseModel):
    """Read-only view of a document version's processing pipeline."""
    id: int
    version_id: int

    extraction_status: str = "PENDING"
    embedding_status: str = "PENDING"
    indexing_status: str = "PENDING"

    chunks_extracted: Optional[int] = 0
    chunks_embedded: Optional[int] = 0
    chunks_indexed: Optional[int] = 0

    error_stage: Optional[str] = None
    error_message: Optional[str] = None

    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ------------------------------------------------------------------ #
#  Document Version                                                   #
# ------------------------------------------------------------------ #

class DocumentVersionCreate(BaseModel):
    """Payload for uploading a new document version (file sent as form-data)."""
    change_summary: Optional[str] = None
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None


class DocumentVersionOut(BaseModel):
    """Read-only view of a document version."""
    id: int
    document_id: int
    version_number: int
    file_path: str
    file_hash: Optional[str] = None
    file_size_bytes: Optional[int] = None
    status: str
    change_summary: Optional[str] = None
    rejection_reason: Optional[str] = None
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None
    created_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    uploaded_by: Optional[int] = None
    approved_by: Optional[int] = None

    processing_job: Optional[ProcessingJobOut] = None

    class Config:
        from_attributes = True


# ------------------------------------------------------------------ #
#  Approval actions                                                   #
# ------------------------------------------------------------------ #

class VersionApproveRequest(BaseModel):
    """Body for approving / publishing a version."""
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None


class VersionRejectRequest(BaseModel):
    """Body for rejecting a version."""
    reason: str = Field(..., min_length=5, description="Reason for rejection")


# ------------------------------------------------------------------ #
#  Expiry monitoring                                                  #
# ------------------------------------------------------------------ #

class ExpiringDocumentOut(BaseModel):
    """A document version whose effective_until date is approaching."""
    version_id: int
    document_id: int
    document_title: str
    version_number: int
    effective_until: datetime
    days_remaining: int
    status: str

    class Config:
        from_attributes = True


# ------------------------------------------------------------------ #
#  Knowledge Base overview statistics                                 #
# ------------------------------------------------------------------ #

class KBStatsOut(BaseModel):
    """Aggregate statistics for the Knowledge Base dashboard."""
    total_documents: int = 0
    total_versions: int = 0
    published_versions: int = 0
    pending_approval: int = 0
    processing: int = 0
    failed_processing: int = 0
    expiring_within_30_days: int = 0
    expired: int = 0


# ------------------------------------------------------------------ #
#  Paginated list                                                     #
# ------------------------------------------------------------------ #

class PaginatedVersions(BaseModel):
    """Paginated list of document versions."""
    items: List[DocumentVersionOut] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
    pages: int = 1
