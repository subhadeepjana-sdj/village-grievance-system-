"""
Feature 10 — Knowledge Base Management REST API.

Endpoints (all under ``/api/admin/kb``):

Document versions
  POST   /documents/{doc_id}/versions       — Upload a new version of an existing document.
  GET    /documents/{doc_id}/versions        — List all versions of a document.
  GET    /versions/{version_id}              — Get a single version with its processing job.
  PUT    /versions/{version_id}/approve      — Publish a version (supersedes current published).
  PUT    /versions/{version_id}/reject       — Reject a version with a reason.
  POST   /versions/{version_id}/reindex      — Re-trigger the processing pipeline.

Monitoring
  GET    /expiring                            — Documents whose effective_until is within N days.
  GET    /stats                               — Aggregate Knowledge Base statistics.
"""

import os
import math
import hashlib
import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.database.session import get_db
from app.database.mongodb import mongodb_service
from app.api.auth import get_current_user
from app.services.notification_service import notify_event
from app.models.notification import NotificationCategory, NotificationSeverity
from app.models.user import User, UserRole
from app.models.document import Document
from app.models.knowledge_base import (
    DocumentVersion,
    DocumentProcessingJob,
    VersionStatus,
    ProcessingStage,
)
from app.schemas.knowledge_base import (
    DocumentVersionOut,
    VersionApproveRequest,
    VersionRejectRequest,
    ExpiringDocumentOut,
    KBStatsOut,
    PaginatedVersions,
)
from app.config import settings

router = APIRouter(prefix="/admin/kb", tags=["Knowledge Base Management"])


# ------------------------------------------------------------------ #
#  Helpers                                                            #
# ------------------------------------------------------------------ #

def _require_admin_or_staff(user: User) -> None:
    if user.role not in (UserRole.ADMIN, UserRole.PANCHAYAT_STAFF):
        raise HTTPException(status_code=403, detail="Admin or Panchayat Staff role required.")


def _compute_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _next_version_number(db: Session, document_id: int) -> int:
    result = (
        db.query(func.max(DocumentVersion.version_number))
        .filter(DocumentVersion.document_id == document_id)
        .scalar()
    )
    return (result or 0) + 1


# ------------------------------------------------------------------ #
#  POST  /documents/{doc_id}/versions                                 #
# ------------------------------------------------------------------ #

@router.post(
    "/documents/{doc_id}/versions",
    response_model=DocumentVersionOut,
    status_code=201,
    summary="Upload a new version of a document",
)
def upload_version(
    doc_id: int,
    file: UploadFile = File(...),
    change_summary: Optional[str] = Form(None),
    effective_from: Optional[str] = Form(None),
    effective_until: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin_or_staff(current_user)

    document = db.query(Document).filter(Document.id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Save file
    upload_dir = os.path.join(settings.UPLOAD_DIR, "kb_versions")
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"doc{doc_id}_v{_next_version_number(db, doc_id)}_{file.filename}"
    abs_path = os.path.join(upload_dir, filename)
    with open(abs_path, "wb") as f:
        f.write(file.file.read())

    file_hash = _compute_sha256(abs_path)
    file_size = os.path.getsize(abs_path)
    rel_path = os.path.relpath(abs_path, settings.UPLOAD_DIR)

    # Parse optional datetime fields
    eff_from = None
    eff_until = None
    if effective_from:
        try:
            eff_from = datetime.datetime.fromisoformat(effective_from)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid effective_from date format. Use ISO 8601.")
    if effective_until:
        try:
            eff_until = datetime.datetime.fromisoformat(effective_until)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid effective_until date format. Use ISO 8601.")

    version = DocumentVersion(
        document_id=doc_id,
        version_number=_next_version_number(db, doc_id),
        file_path=rel_path,
        file_hash=file_hash,
        file_size_bytes=file_size,
        status=VersionStatus.UPLOADED.value,
        change_summary=change_summary,
        effective_from=eff_from,
        effective_until=eff_until,
        uploaded_by=current_user.id,
    )
    db.add(version)
    db.flush()   # get version.id for the processing job

    # Create a processing job placeholder
    job = DocumentProcessingJob(version_id=version.id)
    db.add(job)
    db.commit()
    db.refresh(version)

    mongodb_service.store_kb_document({
        "document_id": doc_id,
        "version_id": version.id,
        "version": f"v{version.version_number}",
        "title": document.title,
        "file_hash": version.file_hash,
        "status": version.status,
        "change_summary": version.change_summary,
        "uploaded_by": current_user.id,
        "created_at": version.created_at,
    })
    return version


# ------------------------------------------------------------------ #
#  GET  /documents/{doc_id}/versions                                  #
# ------------------------------------------------------------------ #

@router.get(
    "/documents/{doc_id}/versions",
    response_model=PaginatedVersions,
    summary="List all versions of a document",
)
def list_versions(
    doc_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by version status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin_or_staff(current_user)

    document = db.query(Document).filter(Document.id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    query = (
        db.query(DocumentVersion)
        .options(joinedload(DocumentVersion.processing_job))
        .filter(DocumentVersion.document_id == doc_id)
    )
    if status:
        query = query.filter(DocumentVersion.status == status.upper())

    total = query.count()
    items = (
        query.order_by(DocumentVersion.version_number.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PaginatedVersions(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, math.ceil(total / page_size)),
    )


# ------------------------------------------------------------------ #
#  GET  /versions/{version_id}                                        #
# ------------------------------------------------------------------ #

@router.get(
    "/versions/{version_id}",
    response_model=DocumentVersionOut,
    summary="Get a single version with its processing job",
)
def get_version(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin_or_staff(current_user)

    version = (
        db.query(DocumentVersion)
        .options(joinedload(DocumentVersion.processing_job))
        .filter(DocumentVersion.id == version_id)
        .first()
    )
    if not version:
        raise HTTPException(status_code=404, detail="Document version not found.")
    return version


# ------------------------------------------------------------------ #
#  PUT  /versions/{version_id}/approve                                #
# ------------------------------------------------------------------ #

@router.put(
    "/versions/{version_id}/approve",
    response_model=DocumentVersionOut,
    summary="Approve and publish a document version",
)
def approve_version(
    version_id: int,
    body: VersionApproveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only Admin can approve document versions.")

    version = (
        db.query(DocumentVersion)
        .options(joinedload(DocumentVersion.processing_job))
        .filter(DocumentVersion.id == version_id)
        .first()
    )
    if not version:
        raise HTTPException(status_code=404, detail="Document version not found.")

    if version.status not in (VersionStatus.PENDING_APPROVAL.value, VersionStatus.UPLOADED.value):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve a version with status '{version.status}'. "
                   f"Expected PENDING_APPROVAL or UPLOADED.",
        )

    # Supersede any currently-published version for this document
    published = (
        db.query(DocumentVersion)
        .filter(
            DocumentVersion.document_id == version.document_id,
            DocumentVersion.status == VersionStatus.PUBLISHED.value,
        )
        .all()
    )
    for pv in published:
        pv.status = VersionStatus.SUPERSEDED.value

    # Publish
    version.status = VersionStatus.PUBLISHED.value
    version.approved_at = datetime.datetime.utcnow()
    version.approved_by = current_user.id
    if body.effective_from:
        version.effective_from = body.effective_from
    if body.effective_until:
        version.effective_until = body.effective_until

    db.commit()
    db.refresh(version)

    mongodb_service.store_kb_document({
        "document_id": version.document_id,
        "version_id": version.id,
        "version": f"v{version.version_number}",
        "status": version.status,
        "approved_by": current_user.id,
        "approved_at": version.approved_at,
    })
    mongodb_service.log_audit_event({
        "event_type": "ADMIN_ACTION",
        "action": "PUBLISH",
        "entity_type": "document_version",
        "entity_id": str(version.id),
        "actor_id": current_user.id,
        "actor_role": current_user.role.value,
        "description": f"Published KB version {version.id}",
    })
    notify_event(
        db,
        title="Document version approved and published",
        message=f"Document #{version.document_id} v{version.version_number} approved and published by {current_user.name}.",
        category=NotificationCategory.KNOWLEDGE_BASE.value,
        severity=NotificationSeverity.INFO.value,
        action_url="/knowledge-base",
        action_label="Open Knowledge Base",
        requires_action=False,
        group_key=f"kb_publish:{version.id}",
    )
    return version


# ------------------------------------------------------------------ #
#  PUT  /versions/{version_id}/reject                                 #
# ------------------------------------------------------------------ #

@router.put(
    "/versions/{version_id}/reject",
    response_model=DocumentVersionOut,
    summary="Reject a document version",
)
def reject_version(
    version_id: int,
    body: VersionRejectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only Admin can reject document versions.")

    version = (
        db.query(DocumentVersion)
        .options(joinedload(DocumentVersion.processing_job))
        .filter(DocumentVersion.id == version_id)
        .first()
    )
    if not version:
        raise HTTPException(status_code=404, detail="Document version not found.")

    if version.status in (VersionStatus.PUBLISHED.value, VersionStatus.SUPERSEDED.value):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reject a version with status '{version.status}'.",
        )

    version.status = VersionStatus.REJECTED.value
    version.rejection_reason = body.reason
    db.commit()
    db.refresh(version)

    mongodb_service.store_kb_document({
        "document_id": version.document_id,
        "version_id": version.id,
        "version": f"v{version.version_number}",
        "status": version.status,
        "rejection_reason": version.rejection_reason,
    })
    mongodb_service.log_audit_event({
        "event_type": "ADMIN_ACTION",
        "action": "REJECT",
        "entity_type": "document_version",
        "entity_id": str(version.id),
        "actor_id": current_user.id,
        "actor_role": current_user.role.value,
        "description": f"Rejected KB version {version.id}: {body.reason}",
    })
    notify_event(
        db,
        title="Knowledge base version rejected",
        message=f"Document #{version.document_id} v{version.version_number} was rejected: {body.reason}",
        category=NotificationCategory.KNOWLEDGE_BASE.value,
        severity=NotificationSeverity.WARNING.value,
        action_url="/knowledge-base",
        action_label="Open Knowledge Base",
        requires_action=True,
        group_key=f"kb_reject:{version.id}",
    )
    return version


# ------------------------------------------------------------------ #
#  POST /versions/{version_id}/reindex                                #
# ------------------------------------------------------------------ #

@router.post(
    "/versions/{version_id}/reindex",
    response_model=DocumentVersionOut,
    summary="Re-trigger the processing pipeline for a version",
)
def reindex_version(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin_or_staff(current_user)

    version = (
        db.query(DocumentVersion)
        .options(joinedload(DocumentVersion.processing_job))
        .filter(DocumentVersion.id == version_id)
        .first()
    )
    if not version:
        raise HTTPException(status_code=404, detail="Document version not found.")

    # Reset processing job
    job = version.processing_job
    if not job:
        job = DocumentProcessingJob(version_id=version.id)
        db.add(job)
    else:
        job.extraction_status = ProcessingStage.PENDING.value
        job.embedding_status = ProcessingStage.PENDING.value
        job.indexing_status = ProcessingStage.PENDING.value
        job.chunks_extracted = 0
        job.chunks_embedded = 0
        job.chunks_indexed = 0
        job.error_stage = None
        job.error_message = None
        job.started_at = None
        job.completed_at = None

    version.status = VersionStatus.PROCESSING.value
    db.commit()
    db.refresh(version)

    mongodb_service.store_kb_document({
        "document_id": version.document_id,
        "version_id": version.id,
        "version": f"v{version.version_number}",
        "status": version.status,
    })
    mongodb_service.log_audit_event({
        "event_type": "ADMIN_ACTION",
        "action": "REINDEX",
        "entity_type": "document_version",
        "entity_id": str(version.id),
        "actor_id": current_user.id,
        "actor_role": current_user.role.value,
        "description": f"Re-indexed KB version {version.id}",
    })
    return version


# ------------------------------------------------------------------ #
#  GET  /expiring                                                     #
# ------------------------------------------------------------------ #

@router.get(
    "/expiring",
    response_model=list[ExpiringDocumentOut],
    summary="Documents expiring within N days",
)
def get_expiring_documents(
    days: int = Query(30, ge=1, le=365, description="Lookahead window in days"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin_or_staff(current_user)

    now = datetime.datetime.utcnow()
    cutoff = now + datetime.timedelta(days=days)

    rows = (
        db.query(DocumentVersion, Document.title)
        .join(Document, DocumentVersion.document_id == Document.id)
        .filter(
            DocumentVersion.status == VersionStatus.PUBLISHED.value,
            DocumentVersion.effective_until.isnot(None),
            DocumentVersion.effective_until <= cutoff,
        )
        .order_by(DocumentVersion.effective_until.asc())
        .all()
    )

    results = []
    for version, doc_title in rows:
        delta = version.effective_until - now
        results.append(
            ExpiringDocumentOut(
                version_id=version.id,
                document_id=version.document_id,
                document_title=doc_title,
                version_number=version.version_number,
                effective_until=version.effective_until,
                days_remaining=max(0, delta.days),
                status="EXPIRED" if delta.days < 0 else "EXPIRING",
            )
        )
    return results


# ------------------------------------------------------------------ #
#  GET  /stats                                                        #
# ------------------------------------------------------------------ #

@router.get(
    "/stats",
    response_model=KBStatsOut,
    summary="Knowledge Base aggregate statistics",
)
def get_kb_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin_or_staff(current_user)

    now = datetime.datetime.utcnow()
    cutoff = now + datetime.timedelta(days=30)

    total_docs = db.query(func.count(Document.id)).scalar() or 0
    total_versions = db.query(func.count(DocumentVersion.id)).scalar() or 0

    def _count_by_status(s: str) -> int:
        return (
            db.query(func.count(DocumentVersion.id))
            .filter(DocumentVersion.status == s)
            .scalar()
        ) or 0

    # Expiring / expired
    expiring = (
        db.query(func.count(DocumentVersion.id))
        .filter(
            DocumentVersion.status == VersionStatus.PUBLISHED.value,
            DocumentVersion.effective_until.isnot(None),
            DocumentVersion.effective_until <= cutoff,
            DocumentVersion.effective_until > now,
        )
        .scalar()
    ) or 0

    expired = (
        db.query(func.count(DocumentVersion.id))
        .filter(
            DocumentVersion.status == VersionStatus.PUBLISHED.value,
            DocumentVersion.effective_until.isnot(None),
            DocumentVersion.effective_until <= now,
        )
        .scalar()
    ) or 0

    # Failed processing
    failed = (
        db.query(func.count(DocumentProcessingJob.id))
        .filter(
            (DocumentProcessingJob.extraction_status == ProcessingStage.FAILED.value)
            | (DocumentProcessingJob.embedding_status == ProcessingStage.FAILED.value)
            | (DocumentProcessingJob.indexing_status == ProcessingStage.FAILED.value)
        )
        .scalar()
    ) or 0

    return KBStatsOut(
        total_documents=total_docs,
        total_versions=total_versions,
        published_versions=_count_by_status(VersionStatus.PUBLISHED.value),
        pending_approval=_count_by_status(VersionStatus.PENDING_APPROVAL.value),
        processing=_count_by_status(VersionStatus.PROCESSING.value),
        failed_processing=failed,
        expiring_within_30_days=expiring,
        expired=expired,
    )
