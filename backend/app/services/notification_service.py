"""
Central Notification & Alert Generation Service.

Responsibilities:
  - Emit structured alerts across all 8 platform domains cleanly without blocking callers.
  - Smart Notification Grouping: combine repeated alerts sharing a ``group_key``.
  - Cross-container persistence: sync every alert & preference to SQLAlchemy + MongoDB.
  - Automated SLA Deadline & Escalation Scanner + System Health Check.
  - Security Failed-Login Spike Detection + Daily Digest Summary.
"""

import datetime
import json
import logging
import threading
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.database.mongodb import mongodb_service
from app.models.ai_records import AIResponse
from app.models.complaint import Complaint, ComplaintStatus
from app.models.feedback import AIFeedback, FeedbackStatus
from app.models.notification import (
    ALL_NOTIFICATION_CATEGORIES,
    Notification,
    NotificationCategory,
    NotificationPreference,
    NotificationSeverity,
)
from app.models.user import User

logger = logging.getLogger("uvicorn.error")

_SEVERITY_RANK = {
    NotificationSeverity.INFO.value: 1,
    NotificationSeverity.WARNING.value: 2,
    NotificationSeverity.CRITICAL.value: 3,
}

_FAILED_LOGIN_LOCK = threading.Lock()
_FAILED_LOGINS: Dict[str, List[datetime.datetime]] = {}


def _utcnow() -> datetime.datetime:
    return datetime.datetime.utcnow()


def _parse_dt(val: Any) -> Optional[datetime.datetime]:
    if val is None:
        return None
    if isinstance(val, datetime.datetime):
        return val.replace(tzinfo=None) if val.tzinfo else val
    try:
        parsed = datetime.datetime.fromisoformat(str(val).replace("Z", "+00:00"))
        return parsed.replace(tzinfo=None) if parsed.tzinfo else parsed
    except Exception:
        return None


def _notification_to_dict(n: Notification) -> Dict[str, Any]:
    meta = None
    if n.metadata_json:
        try:
            meta = json.loads(n.metadata_json)
        except Exception:
            meta = None
    return {
        "id": n.id,
        "title": n.title,
        "message": n.message,
        "category": n.category,
        "severity": n.severity,
        "recipient_id": n.recipient_id,
        "recipient_role": n.recipient_role,
        "related_complaint_id": n.related_complaint_id,
        "related_complaint_number": n.related_complaint_number,
        "group_key": n.group_key,
        "occurrence_count": n.occurrence_count or 1,
        "action_url": n.action_url,
        "action_label": n.action_label,
        "metadata": meta,
        "is_read": bool(n.is_read),
        "requires_action": bool(n.requires_action),
        "acknowledged_at": n.acknowledged_at,
        "acknowledged_by": n.acknowledged_by,
        "created_at": n.created_at,
        "updated_at": n.updated_at or n.created_at,
        "read_at": n.read_at,
        "dismissed_at": n.dismissed_at,
    }


def _normalize_mongo_notification(doc: Dict[str, Any]) -> Dict[str, Any]:
    created_at = _parse_dt(doc.get("created_at")) or _utcnow()
    updated_at = _parse_dt(doc.get("updated_at")) or created_at
    return {
        "id": str(doc.get("id") or ""),
        "title": str(doc.get("title") or "Notification"),
        "message": str(doc.get("message") or ""),
        "category": str(doc.get("category") or NotificationCategory.SYSTEM.value),
        "severity": str(doc.get("severity") or NotificationSeverity.INFO.value),
        "recipient_id": doc.get("recipient_id"),
        "recipient_role": doc.get("recipient_role") or "ADMIN",
        "related_complaint_id": doc.get("related_complaint_id"),
        "related_complaint_number": doc.get("related_complaint_number"),
        "group_key": doc.get("group_key"),
        "occurrence_count": int(doc.get("occurrence_count") or 1),
        "action_url": doc.get("action_url"),
        "action_label": doc.get("action_label"),
        "metadata": doc.get("metadata") if isinstance(doc.get("metadata"), dict) else None,
        "is_read": bool(doc.get("is_read", False)),
        "requires_action": bool(doc.get("requires_action", False)),
        "acknowledged_at": _parse_dt(doc.get("acknowledged_at")),
        "acknowledged_by": doc.get("acknowledged_by"),
        "created_at": created_at,
        "updated_at": updated_at,
        "read_at": _parse_dt(doc.get("read_at")),
        "dismissed_at": _parse_dt(doc.get("dismissed_at")),
    }


def _mirror_to_mongo(payload: Dict[str, Any]) -> None:
    mongodb_service.upsert_notification(payload)


def notify_event(
    db: Optional[Session],
    *,
    title: str,
    message: str,
    category: str = NotificationCategory.COMPLAINT.value,
    severity: str = NotificationSeverity.INFO.value,
    related_complaint_id: Optional[int] = None,
    related_complaint_number: Optional[str] = None,
    action_url: Optional[str] = None,
    action_label: Optional[str] = None,
    requires_action: bool = False,
    group_key: Optional[str] = None,
    recipient_id: Optional[int] = None,
    recipient_role: str = "ADMIN",
    metadata: Optional[Dict[str, Any]] = None,
    allow_grouping: bool = True,
) -> Optional[Dict[str, Any]]:
    """
    Create or smart-group a notification record in SQLAlchemy and MongoDB.

    Never raises — logs warnings on storage errors so primary user flows succeed.
    """
    try:
        cat_val = category.value if hasattr(category, "value") else str(category).upper()
        sev_val = severity.value if hasattr(severity, "value") else str(severity).upper()
        now = _utcnow()

        if db is not None:
            existing: Optional[Notification] = None
            if allow_grouping and group_key:
                existing = (
                    db.query(Notification)
                    .filter(
                        Notification.group_key == group_key,
                        Notification.dismissed_at.is_(None),
                        Notification.is_read.is_(False),
                    )
                    .order_by(Notification.created_at.desc())
                    .first()
                )

            if existing is not None:
                existing.title = title
                existing.message = message
                if _SEVERITY_RANK.get(sev_val, 1) > _SEVERITY_RANK.get(existing.severity, 1):
                    existing.severity = sev_val
                existing.occurrence_count = (existing.occurrence_count or 1) + 1
                existing.requires_action = existing.requires_action or requires_action
                if action_url:
                    existing.action_url = action_url
                if action_label:
                    existing.action_label = action_label
                if metadata:
                    existing.metadata_json = json.dumps(metadata)
                existing.updated_at = now
                db.commit()
                db.refresh(existing)
                payload = _notification_to_dict(existing)
                _mirror_to_mongo(payload)
                return payload

            notif = Notification(
                id=str(uuid.uuid4()),
                title=title[:255],
                message=message,
                category=cat_val,
                severity=sev_val,
                recipient_id=recipient_id,
                recipient_role=recipient_role,
                related_complaint_id=related_complaint_id,
                related_complaint_number=related_complaint_number,
                group_key=group_key,
                occurrence_count=1,
                action_url=action_url,
                action_label=action_label,
                metadata_json=json.dumps(metadata) if metadata else None,
                is_read=False,
                requires_action=requires_action,
                created_at=now,
                updated_at=now,
            )
            db.add(notif)
            db.commit()
            db.refresh(notif)
            payload = _notification_to_dict(notif)
            _mirror_to_mongo(payload)
            return payload

        # Fallback: direct MongoDB write when db session unavailable
        payload = {
            "id": str(uuid.uuid4()),
            "title": title[:255],
            "message": message,
            "category": cat_val,
            "severity": sev_val,
            "recipient_id": recipient_id,
            "recipient_role": recipient_role,
            "related_complaint_id": related_complaint_id,
            "related_complaint_number": related_complaint_number,
            "group_key": group_key,
            "occurrence_count": 1,
            "action_url": action_url,
            "action_label": action_label,
            "metadata": metadata,
            "is_read": False,
            "requires_action": requires_action,
            "acknowledged_at": None,
            "acknowledged_by": None,
            "created_at": now,
            "updated_at": now,
            "read_at": None,
            "dismissed_at": None,
        }
        _mirror_to_mongo(payload)
        return payload
    except Exception as exc:
        logger.warning("notify_event skipped due to error: %s", exc)
        return None


def list_all_merged_notifications(db: Session) -> List[Dict[str, Any]]:
    """Merge SQLAlchemy notifications with MongoDB notifications, deduplicated by id."""
    merged: Dict[str, Dict[str, Any]] = {}
    for row in db.query(Notification).order_by(Notification.created_at.desc()).all():
        d = _notification_to_dict(row)
        merged[d["id"]] = d

    if mongodb_service.connected:
        for doc in mongodb_service.list_notifications():
            norm = _normalize_mongo_notification(doc)
            nid = norm["id"]
            if not nid:
                continue
            existing = merged.get(nid)
            if existing is None or str(norm["updated_at"]) >= str(existing["updated_at"]):
                merged[nid] = norm

    items = list(merged.values())
    items.sort(key=lambda item: item.get("created_at") or _utcnow(), reverse=True)
    return items


def compute_unread_summary(items: List[Dict[str, Any]]) -> Dict[str, int]:
    active = [n for n in items if n.get("dismissed_at") is None]
    unread_count = sum(1 for n in active if not n.get("is_read"))
    critical_count = sum(
        1 for n in active if not n.get("is_read") and str(n.get("severity")).upper() == NotificationSeverity.CRITICAL.value
    )
    pending_action_count = sum(
        1 for n in active if n.get("requires_action") and not n.get("acknowledged_at") and not n.get("is_read")
    )
    return {
        "unread_count": unread_count,
        "critical_count": critical_count,
        "pending_action_count": pending_action_count,
    }


def get_or_create_preferences(db: Session, user: User) -> NotificationPreference:
    pref = db.query(NotificationPreference).filter(NotificationPreference.user_id == user.id).first()
    if pref is None and mongodb_service.connected:
        mongo_pref = mongodb_service.get_notification_preference(user.id)
        if mongo_pref:
            pref = NotificationPreference(
                user_id=user.id,
                user_email=user.email,
                enabled_categories_json=json.dumps(mongo_pref.get("enabled_categories") or ALL_NOTIFICATION_CATEGORIES),
                min_severity=mongo_pref.get("min_severity") or NotificationSeverity.INFO.value,
                in_app_enabled=bool(mongo_pref.get("in_app_enabled", True)),
                email_digest_enabled=bool(mongo_pref.get("email_digest_enabled", False)),
                sms_critical_enabled=bool(mongo_pref.get("sms_critical_enabled", False)),
                smart_grouping_enabled=bool(mongo_pref.get("smart_grouping_enabled", True)),
                auto_escalation_enabled=bool(mongo_pref.get("auto_escalation_enabled", True)),
                escalation_sla_hours=int(mongo_pref.get("escalation_sla_hours") or 48),
            )
            db.add(pref)
            db.commit()
            db.refresh(pref)

    if pref is None:
        pref = NotificationPreference(
            user_id=user.id,
            user_email=user.email,
            enabled_categories_json=json.dumps(ALL_NOTIFICATION_CATEGORIES),
        )
        db.add(pref)
        db.commit()
        db.refresh(pref)
        mongodb_service.upsert_notification_preference(preferences_to_dict(pref))
    return pref


def preferences_to_dict(pref: NotificationPreference) -> Dict[str, Any]:
    try:
        cats = json.loads(pref.enabled_categories_json or "[]")
        if not isinstance(cats, list) or not cats:
            cats = list(ALL_NOTIFICATION_CATEGORIES)
    except Exception:
        cats = list(ALL_NOTIFICATION_CATEGORIES)
    return {
        "user_id": pref.user_id,
        "user_email": pref.user_email,
        "enabled_categories": cats,
        "min_severity": pref.min_severity,
        "in_app_enabled": bool(pref.in_app_enabled),
        "email_digest_enabled": bool(pref.email_digest_enabled),
        "sms_critical_enabled": bool(pref.sms_critical_enabled),
        "smart_grouping_enabled": bool(pref.smart_grouping_enabled),
        "auto_escalation_enabled": bool(pref.auto_escalation_enabled),
        "escalation_sla_hours": int(pref.escalation_sla_hours or 48),
        "updated_at": pref.updated_at,
    }


def record_failed_login(db: Session, email: str) -> None:
    """Detect repeated failed login attempts and emit a Security notification."""
    if not email:
        return
    key = email.strip().lower()
    now = _utcnow()
    cutoff = now - datetime.timedelta(minutes=15)

    with _FAILED_LOGIN_LOCK:
        attempts = [ts for ts in _FAILED_LOGINS.get(key, []) if ts >= cutoff]
        attempts.append(now)
        _FAILED_LOGINS[key] = attempts
        fail_count = len(attempts)

    if fail_count >= 3:
        notify_event(
            db,
            title="Multiple failed login attempts",
            message=f"{fail_count} repeated unsuccessful login attempts detected for account '{email}' within 15 minutes.",
            category=NotificationCategory.SECURITY.value,
            severity=NotificationSeverity.CRITICAL.value,
            action_url="/admin/ai-monitoring",
            action_label="Review security event",
            requires_action=True,
            group_key=f"security:failed_login:{key}",
            metadata={"email": email, "failed_attempts": fail_count},
        )
    elif fail_count >= 1:
        target_user = db.query(User).filter(User.email == email).first()
        if target_user and target_user.role.value in ("ADMIN", "PANCHAYAT_STAFF"):
            notify_event(
                db,
                title="Failed privileged account login attempt",
                message=f"Incorrect password entered for privileged account '{email}' ({target_user.role.value}).",
                category=NotificationCategory.SECURITY.value,
                severity=NotificationSeverity.WARNING.value,
                action_url="/admin/ai-monitoring",
                action_label="Review security event",
                requires_action=True,
                group_key=f"security:failed_login:{key}",
                metadata={"email": email, "failed_attempts": fail_count},
            )


def clear_failed_logins(email: str) -> None:
    if not email:
        return
    with _FAILED_LOGIN_LOCK:
        _FAILED_LOGINS.pop(email.strip().lower(), None)


def scan_sla_escalations_and_system_health(db: Session, sla_hours: int = 48) -> int:
    """
    Evaluate active grievances for SLA deadline approaching/exceeded or unassigned
    delays, plus check MongoDB connectivity errors when configured. Returns number of alerts emitted.
    """
    emitted = 0
    now = _utcnow()
    open_statuses = (
        ComplaintStatus.SUBMITTED,
        ComplaintStatus.ACKNOWLEDGED,
        ComplaintStatus.ASSIGNED,
        ComplaintStatus.UNDER_REVIEW,
        ComplaintStatus.IN_PROGRESS,
    )
    active_complaints = (
        db.query(Complaint)
        .filter(Complaint.status.in_(open_statuses))
        .all()
    )

    for c in active_complaints:
        deadline = c.expected_resolution_date or (
            (c.created_at + datetime.timedelta(hours=sla_hours)) if c.created_at else None
        )
        if deadline and deadline < now:
            hours_overdue = max(1, int((now - deadline).total_seconds() // 3600))
            notify_event(
                db,
                title="Grievance deadline exceeded",
                message=(
                    f"{c.complaint_number} ({c.title}) has exceeded its resolution deadline by "
                    f"{hours_overdue}h and triggered SLA escalation."
                ),
                category=NotificationCategory.DEADLINE_ESCALATION.value,
                severity=NotificationSeverity.CRITICAL.value,
                related_complaint_id=c.id,
                related_complaint_number=c.complaint_number,
                action_url=f"/track?id={c.complaint_number}",
                action_label="Review escalation",
                requires_action=True,
                group_key=f"sla_overdue:{c.complaint_number}",
                metadata={"hours_overdue": hours_overdue, "status": c.status.value},
            )
            emitted += 1
        elif deadline and (deadline - now) <= datetime.timedelta(hours=12):
            hours_left = max(1, int((deadline - now).total_seconds() // 3600))
            notify_event(
                db,
                title="Complaint approaching resolution deadline",
                message=f"{c.complaint_number} has ~{hours_left}h remaining before SLA deadline.",
                category=NotificationCategory.DEADLINE_ESCALATION.value,
                severity=NotificationSeverity.WARNING.value,
                related_complaint_id=c.id,
                related_complaint_number=c.complaint_number,
                action_url=f"/track?id={c.complaint_number}",
                action_label="View complaint",
                requires_action=True,
                group_key=f"sla_approaching:{c.complaint_number}",
            )
            emitted += 1

        if c.department_id is None and c.created_at and (now - c.created_at) >= datetime.timedelta(hours=24):
            notify_event(
                db,
                title="Complaint pending department assignment",
                message=f"{c.complaint_number} has been awaiting department assignment for over 24 hours.",
                category=NotificationCategory.DEADLINE_ESCALATION.value,
                severity=NotificationSeverity.WARNING.value,
                related_complaint_id=c.id,
                related_complaint_number=c.complaint_number,
                action_url="/panchayat/dashboard",
                action_label="Assign department",
                requires_action=True,
                group_key=f"pending_dept:{c.complaint_number}",
            )
            emitted += 1

    # System health alert only if MongoDB URI is explicitly configured but connection failed
    if (settings.MONGODB_URI or "").strip() and not mongodb_service.connected:
        notify_event(
            db,
            title="MongoDB connection unavailable",
            message=f"Primary database fallback active: {mongodb_service.last_error or 'Unable to reach MongoDB cluster.'}",
            category=NotificationCategory.SYSTEM.value,
            severity=NotificationSeverity.CRITICAL.value,
            action_url="/admin/ai-monitoring",
            action_label="Inspect system health",
            requires_action=True,
            group_key="system:mongodb_down",
        )
        emitted += 1

    return emitted


def build_daily_digest(db: Session) -> Dict[str, Any]:
    """Generate a live operational summary across pending cases, escalations, and AI issues."""
    now = _utcnow()
    open_statuses = (
        ComplaintStatus.SUBMITTED,
        ComplaintStatus.ACKNOWLEDGED,
        ComplaintStatus.ASSIGNED,
        ComplaintStatus.UNDER_REVIEW,
        ComplaintStatus.IN_PROGRESS,
    )
    active_complaints = db.query(Complaint).filter(Complaint.status.in_(open_statuses)).all()
    pending_count = len(active_complaints)
    overdue_count = sum(
        1
        for c in active_complaints
        if (c.expected_resolution_date and c.expected_resolution_date < now)
        or (c.created_at and (now - c.created_at) > datetime.timedelta(hours=48))
    )
    ai_issues = (
        db.query(AIResponse)
        .filter(AIResponse.decision.in_(["CORRECT", "CONTRADICTED", "ABSTAIN", "INSUFFICIENT_EVIDENCE"]))
        .count()
    )
    pending_feedback = (
        db.query(AIFeedback)
        .filter(AIFeedback.status == FeedbackStatus.PENDING.value)
        .count()
    )
    all_notifs = list_all_merged_notifications(db)
    summary = compute_unread_summary(all_notifs)

    highlights: List[str] = []
    if overdue_count > 0:
        highlights.append(f"{overdue_count} overdue grievance(s) require escalation review.")
    if pending_count > 0:
        highlights.append(f"{pending_count} active grievance(s) awaiting resolution.")
    if ai_issues > 0:
        highlights.append(f"{ai_issues} AI verification interception(s) logged (contradiction/abstention).")
    if pending_feedback > 0:
        highlights.append(f"{pending_feedback} citizen AI feedback report(s) pending admin review.")

    return {
        "generated_at": now,
        "pending_complaints": pending_count,
        "overdue_complaints": overdue_count,
        "ai_verification_issues": ai_issues,
        "pending_feedback_reviews": pending_feedback,
        "unread_notifications": summary["unread_count"],
        "critical_unread_notifications": summary["critical_count"],
        "highlights": highlights,
    }
