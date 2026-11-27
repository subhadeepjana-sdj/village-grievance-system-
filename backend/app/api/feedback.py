"""
Feature 9 — AI Feedback & Error Review REST API.

Endpoints:

Citizen / Authenticated user:
  POST /api/feedback                   — Submit feedback on an AI response.
  GET  /api/feedback/my                — List current user's submitted feedback.

Admin / Staff / Researcher:
  GET  /api/admin/feedback             — Paginated feedback list with filters.
  GET  /api/admin/feedback/stats       — Aggregate feedback & root-cause stats.
  GET  /api/admin/feedback/{id}        — Full context (AI answer, evidence, claims, reviews).
  PUT  /api/admin/feedback/{id}/review — Investigate, assign root cause, resolve.
"""

import math
import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.database.session import get_db
from app.database.mongodb import mongodb_service
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.ai_records import AIResponse, AIQuery, Evidence, VerificationResult
from app.models.feedback import (
    AIFeedback,
    FeedbackReview,
    FeedbackStatus,
)
from app.schemas.feedback import (
    FeedbackSubmitRequest,
    FeedbackReviewRequest,
    AIFeedbackOut,
    AIFeedbackDetailOut,
    FeedbackEvidenceSnapshot,
    FeedbackVerificationSnapshot,
    PaginatedFeedback,
    FeedbackStatsOut,
)

router = APIRouter(tags=["AI Feedback & Error Review"])

REVIEW_ROLES = (UserRole.ADMIN, UserRole.PANCHAYAT_STAFF, UserRole.RESEARCHER)


def _require_reviewer(user: User) -> None:
    if user.role not in REVIEW_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Admin, Panchayat Staff, or Researcher role required.",
        )


# ------------------------------------------------------------------ #
#  Citizen Endpoints                                                  #
# ------------------------------------------------------------------ #

@router.post(
    "/feedback",
    response_model=AIFeedbackOut,
    status_code=201,
    summary="Submit feedback on an AI response",
)
def submit_feedback(
    payload: FeedbackSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    response_obj = db.query(AIResponse).filter(AIResponse.id == payload.response_id).first()
    if not response_obj:
        raise HTTPException(status_code=404, detail="AI response not found.")

    feedback = AIFeedback(
        response_id=payload.response_id,
        user_id=current_user.id,
        feedback_type=payload.feedback_type.value,
        description=payload.description,
        status=FeedbackStatus.PENDING.value,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    mongodb_service.upsert_feedback({
        "feedback_id": feedback.id,
        "response_id": feedback.response_id,
        "user_id": feedback.user_id,
        "feedback_type": feedback.feedback_type,
        "description": feedback.description,
        "status": feedback.status,
        "created_at": feedback.created_at,
    })
    mongodb_service.log_audit_event({
        "event_type": "USER_ACTION",
        "action": "CREATE",
        "entity_type": "ai_feedback",
        "entity_id": str(feedback.id),
        "actor_id": current_user.id,
        "actor_role": current_user.role.value,
        "description": f"Feedback submitted ({feedback.feedback_type})",
    })
    return feedback


@router.get(
    "/feedback/my",
    response_model=List[AIFeedbackOut],
    summary="List feedback submitted by the current user",
)
def list_my_feedback(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(AIFeedback)
        .options(joinedload(AIFeedback.reviews))
        .filter(AIFeedback.user_id == current_user.id)
        .order_by(AIFeedback.created_at.desc())
        .all()
    )


# ------------------------------------------------------------------ #
#  Admin Investigation Endpoints                                      #
# ------------------------------------------------------------------ #

@router.get(
    "/admin/feedback/stats",
    response_model=FeedbackStatsOut,
    summary="Aggregate AI feedback & root-cause statistics",
)
def get_feedback_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_reviewer(current_user)

    total = db.query(func.count(AIFeedback.id)).scalar() or 0

    status_rows = (
        db.query(AIFeedback.status, func.count(AIFeedback.id))
        .group_by(AIFeedback.status)
        .all()
    )
    status_counts = {s: c for s, c in status_rows}
    pending = status_counts.get(FeedbackStatus.PENDING.value, 0)
    reviewing = status_counts.get(FeedbackStatus.REVIEWING.value, 0)
    resolved = status_counts.get(FeedbackStatus.RESOLVED.value, 0)

    type_rows = (
        db.query(AIFeedback.feedback_type, func.count(AIFeedback.id))
        .group_by(AIFeedback.feedback_type)
        .all()
    )
    by_type = {t: c for t, c in type_rows}

    cause_rows = (
        db.query(FeedbackReview.root_cause, func.count(FeedbackReview.id))
        .group_by(FeedbackReview.root_cause)
        .all()
    )
    by_root_cause = {rc: c for rc, c in cause_rows}

    resolution_rate = round((resolved / total) * 100.0, 1) if total > 0 else 0.0

    return FeedbackStatsOut(
        total_feedback=total,
        pending_count=pending,
        reviewing_count=reviewing,
        resolved_count=resolved,
        resolution_rate=resolution_rate,
        by_feedback_type=by_type,
        by_root_cause=by_root_cause,
    )


@router.get(
    "/admin/feedback",
    response_model=PaginatedFeedback,
    summary="List all AI feedback with filtering and pagination",
)
def list_admin_feedback(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    feedback_type: Optional[str] = Query(None),
    root_cause: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_reviewer(current_user)

    q = db.query(AIFeedback).options(joinedload(AIFeedback.reviews))

    if status:
        q = q.filter(AIFeedback.status == status.upper())
    if feedback_type:
        q = q.filter(AIFeedback.feedback_type == feedback_type.upper())
    if root_cause:
        q = q.join(FeedbackReview).filter(FeedbackReview.root_cause == root_cause.upper())

    total = q.count()
    items = (
        q.order_by(AIFeedback.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PaginatedFeedback(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, math.ceil(total / page_size)),
    )


@router.get(
    "/admin/feedback/{feedback_id}",
    response_model=AIFeedbackDetailOut,
    summary="Detailed feedback view with AI response, evidence, and verification claims",
)
def get_feedback_detail(
    feedback_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_reviewer(current_user)

    feedback = (
        db.query(AIFeedback)
        .options(joinedload(AIFeedback.reviews))
        .filter(AIFeedback.id == feedback_id)
        .first()
    )
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback record not found.")

    ai_resp = db.query(AIResponse).filter(AIResponse.id == feedback.response_id).first()
    if not ai_resp:
        raise HTTPException(status_code=404, detail="Linked AI response not found.")

    ai_query = db.query(AIQuery).filter(AIQuery.id == ai_resp.query_id).first()
    evidences = db.query(Evidence).filter(Evidence.response_id == ai_resp.id).all()
    verifications = (
        db.query(VerificationResult)
        .filter(VerificationResult.response_id == ai_resp.id)
        .all()
    )

    return AIFeedbackDetailOut(
        feedback=feedback,
        question=ai_query.question if ai_query else None,
        answer=ai_resp.answer,
        decision=ai_resp.decision,
        confidence=ai_resp.confidence,
        configuration=ai_resp.configuration,
        evidences=[
            FeedbackEvidenceSnapshot(
                id=e.id,
                document_id=e.document_id,
                chunk_id=e.chunk_id,
                source_type=e.source_type,
                similarity_score=e.similarity_score,
                evidence_text=e.evidence_text,
            )
            for e in evidences
        ],
        verification_results=[
            FeedbackVerificationSnapshot(
                id=v.id,
                claim=v.claim,
                verification_result=v.verification_result,
                confidence=v.confidence,
                reason=v.reason,
            )
            for v in verifications
        ],
    )


@router.put(
    "/admin/feedback/{feedback_id}/review",
    response_model=AIFeedbackOut,
    summary="Review feedback, classify root cause, and update resolution status",
)
def review_feedback(
    feedback_id: int,
    payload: FeedbackReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in (UserRole.ADMIN, UserRole.PANCHAYAT_STAFF):
        raise HTTPException(
            status_code=403,
            detail="Only Admin or Panchayat Staff can submit feedback reviews.",
        )

    feedback = (
        db.query(AIFeedback)
        .options(joinedload(AIFeedback.reviews))
        .filter(AIFeedback.id == feedback_id)
        .first()
    )
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback record not found.")

    resolved_at = (
        datetime.datetime.utcnow()
        if payload.status == FeedbackStatus.RESOLVED
        else None
    )

    review = FeedbackReview(
        feedback_id=feedback.id,
        admin_id=current_user.id,
        root_cause=payload.root_cause.value,
        corrective_action=payload.corrective_action,
        resolution_notes=payload.resolution_notes,
        resolved_at=resolved_at,
    )
    feedback.status = payload.status.value
    feedback.updated_at = datetime.datetime.utcnow()

    db.add(review)
    db.commit()
    db.refresh(feedback)

    mongodb_service.upsert_feedback({
        "feedback_id": feedback.id,
        "status": feedback.status,
        "latest_review": {
            "admin_id": current_user.id,
            "root_cause": payload.root_cause.value,
            "corrective_action": payload.corrective_action,
            "resolution_notes": payload.resolution_notes,
            "resolved_at": resolved_at,
        },
        "updated_at": feedback.updated_at,
    })
    mongodb_service.log_audit_event({
        "event_type": "ADMIN_ACTION",
        "action": "REVIEW",
        "entity_type": "ai_feedback",
        "entity_id": str(feedback.id),
        "actor_id": current_user.id,
        "actor_role": current_user.role.value,
        "description": f"Feedback reviewed (root_cause={payload.root_cause.value}, status={feedback.status})",
    })
    return feedback
