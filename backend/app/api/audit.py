"""
Feature 11 — Audit Logs REST API.

Endpoints (all under ``/api/admin/audit``):

General audit events
  GET  /events                 — Paginated, filterable audit event list.
  GET  /events/trace/{trace_id}  — Full trace (all events + AI audit sharing a trace_id).

AI pipeline audits
  GET  /ai-requests            — Paginated AI request audit list.
  GET  /ai-requests/{id}       — Single AI request audit detail.

Dashboard
  GET  /stats                  — Aggregate audit statistics.
"""

import math
import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, desc

from app.database.session import get_db
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.audit import AuditEvent, AIRequestAudit
from app.schemas.audit import (
    AuditEventOut,
    PaginatedAuditEvents,
    AIRequestAuditOut,
    PaginatedAIRequestAudits,
    TraceDetail,
    AuditStatsOut,
)

router = APIRouter(prefix="/admin/audit", tags=["Audit Logs"])


# ------------------------------------------------------------------ #
#  Helpers                                                            #
# ------------------------------------------------------------------ #

def _require_admin_or_researcher(user: User) -> None:
    if user.role not in (UserRole.ADMIN, UserRole.RESEARCHER):
        raise HTTPException(status_code=403, detail="Admin or Researcher role required.")


# ------------------------------------------------------------------ #
#  GET /events                                                        #
# ------------------------------------------------------------------ #

@router.get(
    "/events",
    response_model=PaginatedAuditEvents,
    summary="Paginated, filterable audit event list",
)
def list_audit_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    event_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    actor_id: Optional[int] = Query(None),
    date_from: Optional[str] = Query(None, description="ISO 8601 start date"),
    date_to: Optional[str] = Query(None, description="ISO 8601 end date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin_or_researcher(current_user)

    q = db.query(AuditEvent)

    if event_type:
        q = q.filter(AuditEvent.event_type == event_type.upper())
    if action:
        q = q.filter(AuditEvent.action == action.upper())
    if entity_type:
        q = q.filter(AuditEvent.entity_type == entity_type)
    if entity_id:
        q = q.filter(AuditEvent.entity_id == entity_id)
    if actor_id:
        q = q.filter(AuditEvent.actor_id == actor_id)
    if date_from:
        try:
            q = q.filter(AuditEvent.created_at >= datetime.datetime.fromisoformat(date_from))
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid date_from format.")
    if date_to:
        try:
            q = q.filter(AuditEvent.created_at <= datetime.datetime.fromisoformat(date_to))
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid date_to format.")

    total = q.count()
    items = (
        q.order_by(AuditEvent.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PaginatedAuditEvents(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, math.ceil(total / page_size)),
    )


# ------------------------------------------------------------------ #
#  GET /events/trace/{trace_id}                                       #
# ------------------------------------------------------------------ #

@router.get(
    "/events/trace/{trace_id}",
    response_model=TraceDetail,
    summary="Full trace — all events and AI audit sharing a trace_id",
)
def get_trace(
    trace_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin_or_researcher(current_user)

    events = (
        db.query(AuditEvent)
        .filter(AuditEvent.trace_id == trace_id)
        .order_by(AuditEvent.created_at.asc())
        .all()
    )
    ai_audit = (
        db.query(AIRequestAudit)
        .filter(AIRequestAudit.trace_id == trace_id)
        .first()
    )

    if not events and not ai_audit:
        raise HTTPException(status_code=404, detail="No audit records found for this trace_id.")

    return TraceDetail(
        trace_id=trace_id,
        events=events,
        ai_request_audit=ai_audit,
    )


# ------------------------------------------------------------------ #
#  GET /ai-requests                                                   #
# ------------------------------------------------------------------ #

@router.get(
    "/ai-requests",
    response_model=PaginatedAIRequestAudits,
    summary="Paginated AI request audit list",
)
def list_ai_request_audits(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    final_decision: Optional[str] = Query(None),
    model_name: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin_or_researcher(current_user)

    q = db.query(AIRequestAudit)

    if final_decision:
        q = q.filter(AIRequestAudit.final_decision == final_decision.upper())
    if model_name:
        q = q.filter(AIRequestAudit.model_name == model_name)
    if date_from:
        try:
            q = q.filter(AIRequestAudit.created_at >= datetime.datetime.fromisoformat(date_from))
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid date_from format.")
    if date_to:
        try:
            q = q.filter(AIRequestAudit.created_at <= datetime.datetime.fromisoformat(date_to))
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid date_to format.")

    total = q.count()
    items = (
        q.order_by(AIRequestAudit.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PaginatedAIRequestAudits(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, math.ceil(total / page_size)),
    )


# ------------------------------------------------------------------ #
#  GET /ai-requests/{audit_id}                                        #
# ------------------------------------------------------------------ #

@router.get(
    "/ai-requests/{audit_id}",
    response_model=AIRequestAuditOut,
    summary="Single AI request audit detail",
)
def get_ai_request_audit(
    audit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin_or_researcher(current_user)

    audit = db.query(AIRequestAudit).filter(AIRequestAudit.id == audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="AI request audit not found.")
    return audit


# ------------------------------------------------------------------ #
#  GET /stats                                                         #
# ------------------------------------------------------------------ #

@router.get(
    "/stats",
    response_model=AuditStatsOut,
    summary="Aggregate audit statistics",
)
def get_audit_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin_or_researcher(current_user)

    today_start = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    total_events = db.query(func.count(AuditEvent.id)).scalar() or 0
    total_ai_audits = db.query(func.count(AIRequestAudit.id)).scalar() or 0

    events_today = (
        db.query(func.count(AuditEvent.id))
        .filter(AuditEvent.created_at >= today_start)
        .scalar()
    ) or 0

    unique_actors = (
        db.query(func.count(func.distinct(AuditEvent.actor_id)))
        .filter(AuditEvent.created_at >= today_start, AuditEvent.actor_id.isnot(None))
        .scalar()
    ) or 0

    # Top 5 actions
    top_actions_rows = (
        db.query(AuditEvent.action, func.count(AuditEvent.id).label("cnt"))
        .group_by(AuditEvent.action)
        .order_by(desc("cnt"))
        .limit(5)
        .all()
    )
    top_actions = [{"action": a, "count": c} for a, c in top_actions_rows]

    return AuditStatsOut(
        total_events=total_events,
        total_ai_audits=total_ai_audits,
        events_today=events_today,
        unique_actors_today=unique_actors,
        top_actions=top_actions,
    )
