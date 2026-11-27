"""
Central Admin Notifications & Alerts REST API.

Endpoints under ``/api/admin/notifications``:
  GET    /                  — Paginated, filterable notification feed + summary counts.
  GET    /unread-count      — Lightweight unread / critical / pending-action counts for polling.
  PATCH  /{id}/read         — Mark a single notification read or unread.
  PATCH  /{id}/acknowledge  — Acknowledge a critical / action-required alert (preserves audit trail).
  PATCH  /{id}/dismiss      — Dismiss notification from active feed (kept in alert history).
  PATCH  /mark-all-read     — Mark all active unread notifications as read.
  POST   /scan-sla          — Run SLA deadline escalation & system health check.
  GET    /digest            — Daily operational digest summary.
  GET    /preferences       — Fetch current admin's notification preferences.
  PUT    /preferences       — Update current admin's notification preferences.
"""

import datetime
import json
import math
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database.mongodb import mongodb_service
from app.database.session import get_db
from app.models.notification import (
    ALL_NOTIFICATION_CATEGORIES,
    Notification,
    NotificationCategory,
    NotificationSeverity,
)
from app.models.user import User, UserRole
from app.schemas.notification import (
    DailyDigestOut,
    NotificationListResponse,
    NotificationOut,
    NotificationPreferenceOut,
    NotificationPreferenceUpdate,
    NotificationReadUpdate,
    UnreadCountOut,
)
from app.services.notification_service import (
    build_daily_digest,
    compute_unread_summary,
    get_or_create_preferences,
    list_all_merged_notifications,
    preferences_to_dict,
    scan_sla_escalations_and_system_health,
)

router = APIRouter(prefix="/admin/notifications", tags=["Admin Notifications & Alerts"])

ADMIN_NOTIFICATION_ROLES = (UserRole.ADMIN, UserRole.PANCHAYAT_STAFF, UserRole.RESEARCHER)


def _require_admin_reviewer(user: User) -> None:
    if user.role not in ADMIN_NOTIFICATION_ROLES:
        raise HTTPException(status_code=403, detail="Admin, Panchayat Staff, or Researcher role required.")


def _filter_items(
    items: List[Dict[str, Any]],
    *,
    filter_tab: str = "all",
    category: Optional[str] = None,
    severity: Optional[str] = None,
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    include_dismissed: bool = False,
) -> List[Dict[str, Any]]:
    ft = (filter_tab or "all").strip().lower()
    out: List[Dict[str, Any]] = []

    dt_from = None
    dt_to = None
    if date_from:
        try:
            dt_from = datetime.datetime.fromisoformat(date_from.replace("Z", ""))
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid date_from format.")
    if date_to:
        try:
            dt_to = datetime.datetime.fromisoformat(date_to.replace("Z", ""))
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid date_to format.")

    q = (search or "").strip().lower()
    cat_filter = (category or "").strip().upper()
    sev_filter = (severity or "").strip().upper()

    for n in items:
        if not include_dismissed and n.get("dismissed_at") is not None:
            continue

        if ft == "unread" and n.get("is_read"):
            continue
        elif ft == "critical" and str(n.get("severity")).upper() != NotificationSeverity.CRITICAL.value:
            continue
        elif ft == "pending_action" and not (n.get("requires_action") and not n.get("is_read")):
            continue
        elif ft == "complaints" and str(n.get("category")).upper() not in (
            NotificationCategory.COMPLAINT.value,
            NotificationCategory.DEADLINE_ESCALATION.value,
            NotificationCategory.DEPARTMENT.value,
        ):
            continue
        elif ft == "ai_alerts" and str(n.get("category")).upper() not in (
            NotificationCategory.AI_INTELLIGENCE.value,
            NotificationCategory.AI_FEEDBACK.value,
            NotificationCategory.KNOWLEDGE_BASE.value,
        ):
            continue
        elif ft == "system_alerts" and str(n.get("category")).upper() not in (
            NotificationCategory.SECURITY.value,
            NotificationCategory.SYSTEM.value,
        ):
            continue

        if cat_filter and str(n.get("category")).upper() != cat_filter:
            continue
        if sev_filter and str(n.get("severity")).upper() != sev_filter:
            continue

        created_at = n.get("created_at")
        if dt_from and isinstance(created_at, datetime.datetime) and created_at < dt_from:
            continue
        if dt_to and isinstance(created_at, datetime.datetime) and created_at > dt_to:
            continue

        if q:
            haystack = " ".join([
                str(n.get("title") or ""),
                str(n.get("message") or ""),
                str(n.get("related_complaint_number") or ""),
                str(n.get("category") or ""),
            ]).lower()
            if q not in haystack:
                continue

        out.append(n)

    return out


def _update_notification_record(
    db: Session,
    notif_id: str,
    updates: Dict[str, Any],
) -> Dict[str, Any]:
    row = db.query(Notification).filter(Notification.id == notif_id).first()
    if row:
        for k, v in updates.items():
            setattr(row, k, v)
        row.updated_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(row)
        payload = {
            "id": row.id,
            "title": row.title,
            "message": row.message,
            "category": row.category,
            "severity": row.severity,
            "recipient_id": row.recipient_id,
            "recipient_role": row.recipient_role,
            "related_complaint_id": row.related_complaint_id,
            "related_complaint_number": row.related_complaint_number,
            "group_key": row.group_key,
            "occurrence_count": row.occurrence_count or 1,
            "action_url": row.action_url,
            "action_label": row.action_label,
            "is_read": bool(row.is_read),
            "requires_action": bool(row.requires_action),
            "acknowledged_at": row.acknowledged_at,
            "acknowledged_by": row.acknowledged_by,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
            "read_at": row.read_at,
            "dismissed_at": row.dismissed_at,
        }
        mongodb_service.upsert_notification(payload)
        return payload

    if mongodb_service.connected:
        doc = mongodb_service.get_notification(notif_id)
        if doc:
            merged = {**doc, **updates, "updated_at": datetime.datetime.utcnow()}
            mongodb_service.upsert_notification(merged)
            return merged

    raise HTTPException(status_code=404, detail="Notification not found.")


@router.get("", response_model=NotificationListResponse)
def list_notifications(
    filter: str = Query("all", description="all | unread | critical | pending_action | complaints | ai_alerts | system_alerts"),
    category: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    include_dismissed: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin_reviewer(current_user)
    all_items = list_all_merged_notifications(db)
    summary = compute_unread_summary(all_items)

    filtered = _filter_items(
        all_items,
        filter_tab=filter,
        category=category,
        severity=severity,
        search=search,
        date_from=date_from,
        date_to=date_to,
        include_dismissed=include_dismissed,
    )
    total = len(filtered)
    start = (page - 1) * page_size
    page_items = [NotificationOut(**item) for item in filtered[start : start + page_size]]

    return NotificationListResponse(
        items=page_items,
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, math.ceil(total / page_size)) if total > 0 else 1,
        unread_count=summary["unread_count"],
        critical_count=summary["critical_count"],
        pending_action_count=summary["pending_action_count"],
    )


@router.get("/unread-count", response_model=UnreadCountOut)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin_reviewer(current_user)
    all_items = list_all_merged_notifications(db)
    return UnreadCountOut(**compute_unread_summary(all_items))


@router.patch("/mark-all-read")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin_reviewer(current_user)
    now = datetime.datetime.utcnow()

    unread_rows = (
        db.query(Notification)
        .filter(Notification.dismissed_at.is_(None), Notification.is_read.is_(False))
        .all()
    )
    updated_count = 0
    for row in unread_rows:
        row.is_read = True
        row.read_at = now
        row.updated_at = now
        updated_count += 1
    db.commit()

    if mongodb_service.connected:
        for doc in mongodb_service.list_notifications():
            if doc.get("dismissed_at") is None and not doc.get("is_read"):
                mongodb_service.upsert_notification({**doc, "is_read": True, "read_at": now, "updated_at": now})
                updated_count += 1

    return {"marked_read": updated_count}


@router.patch("/{notif_id}/read", response_model=NotificationOut)
def set_notification_read(
    notif_id: str,
    body: Optional[NotificationReadUpdate] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin_reviewer(current_user)
    is_read = body.is_read if body is not None else True
    updates = {
        "is_read": is_read,
        "read_at": datetime.datetime.utcnow() if is_read else None,
    }
    return NotificationOut(**_update_notification_record(db, notif_id, updates))


@router.patch("/{notif_id}/acknowledge", response_model=NotificationOut)
def acknowledge_notification(
    notif_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin_reviewer(current_user)
    now = datetime.datetime.utcnow()
    updates = {
        "is_read": True,
        "read_at": now,
        "acknowledged_at": now,
        "acknowledged_by": f"{current_user.name} ({current_user.role.value})",
    }
    return NotificationOut(**_update_notification_record(db, notif_id, updates))


@router.patch("/{notif_id}/dismiss", response_model=NotificationOut)
def dismiss_notification(
    notif_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin_reviewer(current_user)
    now = datetime.datetime.utcnow()
    updates = {
        "is_read": True,
        "read_at": now,
        "dismissed_at": now,
    }
    return NotificationOut(**_update_notification_record(db, notif_id, updates))


@router.post("/scan-sla")
def run_sla_and_health_scan(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin_reviewer(current_user)
    pref = get_or_create_preferences(db, current_user)
    emitted = scan_sla_escalations_and_system_health(db, sla_hours=pref.escalation_sla_hours or 48)
    all_items = list_all_merged_notifications(db)
    return {
        "alerts_processed": emitted,
        **compute_unread_summary(all_items),
    }


@router.get("/digest", response_model=DailyDigestOut)
def get_daily_digest(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin_reviewer(current_user)
    return DailyDigestOut(**build_daily_digest(db))


@router.get("/preferences", response_model=NotificationPreferenceOut)
def get_notification_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin_reviewer(current_user)
    pref = get_or_create_preferences(db, current_user)
    return NotificationPreferenceOut(**preferences_to_dict(pref))


@router.put("/preferences", response_model=NotificationPreferenceOut)
def update_notification_preferences(
    payload: NotificationPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin_reviewer(current_user)
    pref = get_or_create_preferences(db, current_user)

    if payload.enabled_categories is not None:
        valid = [c for c in payload.enabled_categories if c in ALL_NOTIFICATION_CATEGORIES]
        pref.enabled_categories_json = json.dumps(valid)
    if payload.min_severity is not None:
        sev = payload.min_severity.upper()
        if sev not in ("INFO", "WARNING", "CRITICAL"):
            raise HTTPException(status_code=422, detail="min_severity must be INFO, WARNING, or CRITICAL.")
        pref.min_severity = sev
    if payload.in_app_enabled is not None:
        pref.in_app_enabled = payload.in_app_enabled
    if payload.email_digest_enabled is not None:
        pref.email_digest_enabled = payload.email_digest_enabled
    if payload.sms_critical_enabled is not None:
        pref.sms_critical_enabled = payload.sms_critical_enabled
    if payload.smart_grouping_enabled is not None:
        pref.smart_grouping_enabled = payload.smart_grouping_enabled
    if payload.auto_escalation_enabled is not None:
        pref.auto_escalation_enabled = payload.auto_escalation_enabled
    if payload.escalation_sla_hours is not None:
        if payload.escalation_sla_hours < 1 or payload.escalation_sla_hours > 720:
            raise HTTPException(status_code=422, detail="escalation_sla_hours must be between 1 and 720.")
        pref.escalation_sla_hours = payload.escalation_sla_hours

    pref.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(pref)

    pref_dict = preferences_to_dict(pref)
    mongodb_service.upsert_notification_preference(pref_dict)
    return NotificationPreferenceOut(**pref_dict)
