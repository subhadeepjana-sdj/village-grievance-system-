from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: str
    title: str
    message: str
    category: str
    severity: str
    recipient_id: Optional[int] = None
    recipient_role: Optional[str] = "ADMIN"
    related_complaint_id: Optional[int] = None
    related_complaint_number: Optional[str] = None
    group_key: Optional[str] = None
    occurrence_count: int = 1
    action_url: Optional[str] = None
    action_label: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    is_read: bool = False
    requires_action: bool = False
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    dismissed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    items: List[NotificationOut]
    total: int
    page: int
    page_size: int
    pages: int
    unread_count: int
    critical_count: int
    pending_action_count: int


class UnreadCountOut(BaseModel):
    unread_count: int
    critical_count: int
    pending_action_count: int


class NotificationReadUpdate(BaseModel):
    is_read: bool = True


class DailyDigestOut(BaseModel):
    generated_at: datetime
    pending_complaints: int
    overdue_complaints: int
    ai_verification_issues: int
    pending_feedback_reviews: int
    unread_notifications: int
    critical_unread_notifications: int
    highlights: List[str] = []


class NotificationPreferenceOut(BaseModel):
    user_id: int
    enabled_categories: List[str]
    min_severity: str = "INFO"
    in_app_enabled: bool = True
    email_digest_enabled: bool = False
    sms_critical_enabled: bool = False
    smart_grouping_enabled: bool = True
    auto_escalation_enabled: bool = True
    escalation_sla_hours: int = 48
    updated_at: Optional[datetime] = None


class NotificationPreferenceUpdate(BaseModel):
    enabled_categories: Optional[List[str]] = None
    min_severity: Optional[str] = None
    in_app_enabled: Optional[bool] = None
    email_digest_enabled: Optional[bool] = None
    sms_critical_enabled: Optional[bool] = None
    smart_grouping_enabled: Optional[bool] = None
    auto_escalation_enabled: Optional[bool] = None
    escalation_sla_hours: Optional[int] = None
