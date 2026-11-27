"""
Central Notifications & Alerts Models.

Keeps alert records strictly separated from the underlying source of truth
(complaint status, AI verification results, KB document state) while storing
rich cross-referenced metadata for rapid admin triage, acknowledgement, SLA
escalation tracking, smart grouping, and auditability.
"""

import enum
import uuid
import json
import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from app.database.session import Base


class NotificationCategory(str, enum.Enum):
    COMPLAINT = "COMPLAINT"
    DEADLINE_ESCALATION = "DEADLINE_ESCALATION"
    DEPARTMENT = "DEPARTMENT"
    AI_INTELLIGENCE = "AI_INTELLIGENCE"
    KNOWLEDGE_BASE = "KNOWLEDGE_BASE"
    AI_FEEDBACK = "AI_FEEDBACK"
    SECURITY = "SECURITY"
    SYSTEM = "SYSTEM"


class NotificationSeverity(str, enum.Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


ALL_NOTIFICATION_CATEGORIES = [c.value for c in NotificationCategory]


class Notification(Base):
    """Admin/staff operational alert record with grouping and acknowledgement tracking."""

    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    category = Column(String(64), nullable=False, index=True, default=NotificationCategory.COMPLAINT.value)
    severity = Column(String(20), nullable=False, index=True, default=NotificationSeverity.INFO.value)

    recipient_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    recipient_role = Column(String(32), nullable=True, default="ADMIN")

    related_complaint_id = Column(Integer, ForeignKey("complaints.id", ondelete="SET NULL"), nullable=True)
    related_complaint_number = Column(String(50), nullable=True, index=True)

    group_key = Column(String(160), nullable=True, index=True)
    occurrence_count = Column(Integer, nullable=False, default=1)

    action_url = Column(String(255), nullable=True)
    action_label = Column(String(80), nullable=True)
    metadata_json = Column(Text, nullable=True)

    is_read = Column(Boolean, nullable=False, default=False, index=True)
    requires_action = Column(Boolean, nullable=False, default=False, index=True)

    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(120), nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    read_at = Column(DateTime, nullable=True)
    dismissed_at = Column(DateTime, nullable=True, index=True)


class NotificationPreference(Base):
    """Per-admin alert category filters, channels, smart grouping, and SLA escalation rules."""

    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    user_email = Column(String(100), nullable=True)

    enabled_categories_json = Column(
        Text,
        nullable=False,
        default=lambda: json.dumps(ALL_NOTIFICATION_CATEGORIES),
    )
    min_severity = Column(String(20), nullable=False, default=NotificationSeverity.INFO.value)

    in_app_enabled = Column(Boolean, nullable=False, default=True)
    email_digest_enabled = Column(Boolean, nullable=False, default=False)
    sms_critical_enabled = Column(Boolean, nullable=False, default=False)

    smart_grouping_enabled = Column(Boolean, nullable=False, default=True)
    auto_escalation_enabled = Column(Boolean, nullable=False, default=True)
    escalation_sla_hours = Column(Integer, nullable=False, default=48)

    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
