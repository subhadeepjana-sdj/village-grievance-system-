"""
Central Notifications & Alerts System Tests.

Covers:
  1. Auto-generation when citizen submits complaint (HIGH -> CRITICAL + duplicate detection)
  2. Filtering tabs (all, unread, critical, pending_action, complaints, ai_alerts, system_alerts) & search
  3. Read/unread toggle, critical alert acknowledgement, dismiss & history preservation, mark-all-read
  4. Smart notification grouping by group_key
  5. Repeated failed logins emit CRITICAL SECURITY alert
  6. SLA escalation scanner detects overdue complaints
  7. Daily digest & notification preferences endpoints + RBAC enforcement
"""

import datetime
import os
import sys
import unittest
from contextlib import contextmanager

_this_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.abspath(os.path.join(_this_dir, "..", ".."))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from fastapi.testclient import TestClient
from app.api.auth import get_current_user
from app.database.seed_data import seed_database
from app.database.session import Base, SessionLocal, engine
from app.main import app
from app.models.complaint import Complaint, ComplaintPriority, ComplaintStatus, ComplaintStatusHistory
from app.models.notification import Notification, NotificationCategory, NotificationPreference, NotificationSeverity
from app.models.user import User, UserRole
from app.services.notification_service import clear_failed_logins, notify_event, record_failed_login


class TestNotificationsCenter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        seed_database(include_demo_data=False)
        cls.client = TestClient(app)

    def setUp(self):
        db = SessionLocal()
        try:
            db.query(Notification).delete()
            db.query(NotificationPreference).delete()
            db.query(ComplaintStatusHistory).delete()
            db.query(Complaint).delete()
            db.commit()
        finally:
            db.close()

    @contextmanager
    def _as_user(self, role: UserRole):
        db = SessionLocal()
        try:
            email = "admin@village.gov.in" if role == UserRole.ADMIN else "citizen@village.gov.in"
            user = db.query(User).filter(User.email == email).first()
            assert user is not None
        finally:
            db.close()

        prev = app.dependency_overrides.get(get_current_user)
        app.dependency_overrides[get_current_user] = lambda: user
        try:
            yield user
        finally:
            if prev is not None:
                app.dependency_overrides[get_current_user] = prev
            else:
                app.dependency_overrides.pop(get_current_user, None)

    def test_01_citizen_complaint_creates_admin_notification_and_duplicate_alert(self):
        with self._as_user(UserRole.CITIZEN):
            r1 = self.client.post(
                "/api/complaints",
                data={
                    "category": "Water Supply",
                    "title": "Main pipe leakage in Ward 4",
                    "description": "Urgent potable water pipeline burst since morning.",
                    "location": "Ward 4",
                    "priority": "HIGH",
                },
            )
            self.assertEqual(r1.status_code, 200)
            cnum1 = r1.json()["complaint_number"]

            # Second submission in same category within 24h triggers duplicate warning
            r2 = self.client.post(
                "/api/complaints",
                data={
                    "category": "Water Supply",
                    "title": "Water leak still active in Ward 4",
                    "description": "Follow up report on broken main pipe.",
                    "location": "Ward 4",
                    "priority": "MEDIUM",
                },
            )
            self.assertEqual(r2.status_code, 200)

        with self._as_user(UserRole.ADMIN):
            res = self.client.get("/api/admin/notifications", params={"search": cnum1})
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["total"], 2)
            by_title = {item["title"]: item for item in data["items"]}
            self.assertIn("High-priority complaint received", by_title)
            self.assertEqual(by_title["High-priority complaint received"]["severity"], "CRITICAL")
            self.assertEqual(by_title["High-priority complaint received"]["category"], "COMPLAINT")
            self.assertEqual(by_title["High-priority complaint received"]["related_complaint_number"], cnum1)

            self.assertIn("Potential duplicate complaint detected", by_title)
            self.assertEqual(by_title["Potential duplicate complaint detected"]["severity"], "WARNING")

    def test_02_filters_read_acknowledge_dismiss_history_and_mark_all(self):
        db = SessionLocal()
        try:
            n1 = notify_event(
                db,
                title="AI verification contradiction detected",
                message="Query #AI-900 had contradicted claims.",
                category=NotificationCategory.AI_INTELLIGENCE.value,
                severity=NotificationSeverity.CRITICAL.value,
                action_url="/admin/ai-monitoring",
                requires_action=True,
                allow_grouping=False,
            )
            n2 = notify_event(
                db,
                title="Knowledge base document indexed",
                message="Charter PDF processed.",
                category=NotificationCategory.KNOWLEDGE_BASE.value,
                severity=NotificationSeverity.INFO.value,
                requires_action=False,
                allow_grouping=False,
            )
        finally:
            db.close()

        assert n1 is not None and n2 is not None

        with self._as_user(UserRole.ADMIN):
            counts = self.client.get("/api/admin/notifications/unread-count").json()
            self.assertEqual(counts["unread_count"], 2)
            self.assertEqual(counts["critical_count"], 1)
            self.assertEqual(counts["pending_action_count"], 1)

            # Filter by ai_alerts
            ai_list = self.client.get("/api/admin/notifications", params={"filter": "ai_alerts"}).json()
            self.assertEqual(ai_list["total"], 2)

            # Acknowledge critical notification
            ack = self.client.patch(f"/api/admin/notifications/{n1['id']}/acknowledge")
            self.assertEqual(ack.status_code, 200)
            self.assertTrue(ack.json()["is_read"])
            self.assertIsNotNone(ack.json()["acknowledged_at"])

            # Dismiss n2 & confirm hidden from active feed but visible in history
            dis = self.client.patch(f"/api/admin/notifications/{n2['id']}/dismiss")
            self.assertEqual(dis.status_code, 200)
            active = self.client.get("/api/admin/notifications").json()
            self.assertEqual(active["total"], 1)

            history = self.client.get("/api/admin/notifications", params={"include_dismissed": True}).json()
            self.assertEqual(history["total"], 2)

            # Mark unread then mark all read
            unread_toggle = self.client.patch(
                f"/api/admin/notifications/{n1['id']}/read",
                json={"is_read": False},
            )
            self.assertFalse(unread_toggle.json()["is_read"])
            mall = self.client.patch("/api/admin/notifications/mark-all-read")
            self.assertEqual(mall.status_code, 200)
            self.assertEqual(mall.json()["marked_read"], 1)

    def test_03_smart_grouping_and_failed_login_security_alerts(self):
        db = SessionLocal()
        try:
            clear_failed_logins("admin@village.gov.in")
            for _ in range(3):
                record_failed_login(db, "admin@village.gov.in")
            rows = db.query(Notification).filter(Notification.category == NotificationCategory.SECURITY.value).all()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].occurrence_count, 3)
            self.assertEqual(rows[0].severity, "CRITICAL")
            clear_failed_logins("admin@village.gov.in")
        finally:
            db.close()

    def test_04_sla_escalation_digest_preferences_and_rbac(self):
        db = SessionLocal()
        try:
            citizen = db.query(User).filter(User.email == "citizen@village.gov.in").first()
            assert citizen is not None
            overdue = Complaint(
                complaint_number="GRV-2026-999001",
                user_id=citizen.id,
                category="Water Supply",
                title="Old unresolved water grievance",
                description="Waiting past deadline.",
                status=ComplaintStatus.UNDER_REVIEW,
                priority=ComplaintPriority.HIGH,
                created_at=datetime.datetime.utcnow() - datetime.timedelta(hours=72),
            )
            db.add(overdue)
            db.commit()
        finally:
            db.close()

        with self._as_user(UserRole.CITIZEN):
            forbidden = self.client.get("/api/admin/notifications")
            self.assertEqual(forbidden.status_code, 403)

        with self._as_user(UserRole.ADMIN):
            scan = self.client.post("/api/admin/notifications/scan-sla")
            self.assertEqual(scan.status_code, 200)
            self.assertGreaterEqual(scan.json()["critical_count"], 1)

            digest = self.client.get("/api/admin/notifications/digest")
            self.assertEqual(digest.status_code, 200)
            self.assertGreaterEqual(digest.json()["overdue_complaints"], 1)

            prefs = self.client.get("/api/admin/notifications/preferences")
            self.assertEqual(prefs.status_code, 200)
            upd = self.client.put(
                "/api/admin/notifications/preferences",
                json={"min_severity": "WARNING", "escalation_sla_hours": 24, "email_digest_enabled": True},
            )
            self.assertEqual(upd.status_code, 200)
            self.assertEqual(upd.json()["min_severity"], "WARNING")
            self.assertEqual(upd.json()["escalation_sla_hours"], 24)
            self.assertTrue(upd.json()["email_digest_enabled"])


if __name__ == "__main__":
    unittest.main()
