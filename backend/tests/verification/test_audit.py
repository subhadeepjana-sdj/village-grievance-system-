"""
Feature 11 — Audit Logs Tests.

Covers:
  1. List audit events with pagination
  2. Filter audit events by event_type, action, entity_type, actor_id, date range
  3. Trace detail endpoint (/events/trace/{trace_id}) correlating events + AIRequestAudit
  4. Trace not found returns 404
  5. List AI request audits with pagination and filters (final_decision, model_name)
  6. Single AI request audit detail endpoint + 404 handling
  7. Aggregate audit statistics endpoint (/stats)
  8. RBAC: ADMIN and RESEARCHER allowed; CITIZEN and PANCHAYAT_STAFF forbidden (403)
"""

import os
import sys
import uuid
import json
import datetime
import unittest
from contextlib import contextmanager

_this_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.abspath(os.path.join(_this_dir, "..", ".."))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database.session import Base, get_db
from app.api.auth import get_current_user
import app.models  # noqa: F401
from app.main import app


class TestAuditLogs(unittest.TestCase):
    """Integration tests for Feature 11 Audit Logs endpoints."""

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        @event.listens_for(cls.engine, "connect")
        def _set_sqlite_pragma(dbapi_conn, _rec):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        Base.metadata.create_all(bind=cls.engine)
        cls.TestSession = sessionmaker(bind=cls.engine)

        def _override_get_db():
            db = cls.TestSession()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = _override_get_db
        cls.client = TestClient(app)

        db = cls.TestSession()
        from app.models.user import User, UserRole
        from app.models.village import Village
        from app.models.ai_records import AIQuery
        from app.models.audit import AuditEvent, AIRequestAudit, AuditEventType, AuditAction

        village = Village(name="AuditVillage", district="D1", state="S1", pincode="110001")
        db.add(village)
        db.flush()

        admin = User(name="Audit Admin", email="audit_admin@test.com", password_hash="h", role=UserRole.ADMIN, village_id=village.id)
        researcher = User(name="Audit Researcher", email="audit_res@test.com", password_hash="h", role=UserRole.RESEARCHER, village_id=village.id)
        citizen = User(name="Audit Citizen", email="audit_cit@test.com", password_hash="h", role=UserRole.CITIZEN, village_id=village.id)
        staff = User(name="Audit Staff", email="audit_staff@test.com", password_hash="h", role=UserRole.PANCHAYAT_STAFF, village_id=village.id)
        db.add_all([admin, researcher, citizen, staff])
        db.flush()

        cls.trace_1 = str(uuid.uuid4())
        cls.trace_2 = str(uuid.uuid4())

        q1 = AIQuery(user_id=citizen.id, question="What is the status of my water complaint?", query_type="STATUS")
        q2 = AIQuery(user_id=citizen.id, question="What are sanitation rules?", query_type="GENERAL")
        db.add_all([q1, q2])
        db.flush()

        ev1 = AuditEvent(
            trace_id=cls.trace_1,
            actor_id=citizen.id,
            actor_role="CITIZEN",
            event_type=AuditEventType.AI_PIPELINE.value,
            action=AuditAction.QUERY.value,
            entity_type="ai_query",
            entity_id=str(q1.id),
            description="Citizen submitted AI query",
        )
        ev2 = AuditEvent(
            trace_id=cls.trace_1,
            actor_id=None,
            actor_role="SYSTEM",
            event_type=AuditEventType.AI_PIPELINE.value,
            action=AuditAction.VERIFY.value,
            entity_type="ai_response",
            entity_id="1",
            new_value=json.dumps({"decision": "SHOW"}),
            description="Verification completed",
        )
        ev3 = AuditEvent(
            trace_id=cls.trace_2,
            actor_id=admin.id,
            actor_role="ADMIN",
            event_type=AuditEventType.ADMIN_ACTION.value,
            action=AuditAction.APPROVE.value,
            entity_type="document_version",
            entity_id="5",
            old_value=json.dumps({"status": "PENDING_APPROVAL"}),
            new_value=json.dumps({"status": "PUBLISHED"}),
            description="Admin published KB version",
        )
        db.add_all([ev1, ev2, ev3])

        ai_audit_1 = AIRequestAudit(
            trace_id=cls.trace_1,
            query_id=q1.id,
            model_name="llama-3.1-8b",
            model_version="1.0",
            prompt_version="v2",
            embedding_model="bge-small-en-v1.5",
            retrieved_document_ids=json.dumps([1, 2]),
            retrieved_chunk_ids=json.dumps(["c1", "c2"]),
            retrieval_scores=json.dumps([0.89, 0.84]),
            total_claims=2,
            supported_claims=2,
            contradicted_claims=0,
            insufficient_claims=0,
            final_decision="SHOW",
            correction_attempts=0,
            response_time_ms=420.5,
            retrieval_time_ms=35.0,
            verification_time_ms=110.2,
        )
        ai_audit_2 = AIRequestAudit(
            trace_id=cls.trace_2,
            query_id=q2.id,
            model_name="gpt-4o-mini",
            model_version="2024-07",
            prompt_version="v2",
            embedding_model="bge-small-en-v1.5",
            total_claims=1,
            supported_claims=0,
            contradicted_claims=0,
            insufficient_claims=1,
            final_decision="ABSTAIN",
            abstention_reason="INSUFFICIENT_EVIDENCE",
            response_time_ms=280.0,
        )
        db.add_all([ai_audit_1, ai_audit_2])
        db.commit()

        cls.admin_id = admin.id
        cls.researcher_id = researcher.id
        cls.citizen_id = citizen.id
        cls.staff_id = staff.id
        cls.ai_audit_1_id = ai_audit_1.id
        db.close()

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=cls.engine)
        cls.engine.dispose()

    @contextmanager
    def _patch_user(self, role="admin"):
        from app.models.user import User, UserRole
        role_map = {
            "admin": (self.admin_id, UserRole.ADMIN),
            "researcher": (self.researcher_id, UserRole.RESEARCHER),
            "citizen": (self.citizen_id, UserRole.CITIZEN),
            "staff": (self.staff_id, UserRole.PANCHAYAT_STAFF),
        }
        uid, urole = role_map[role]
        mock_user = User(id=uid, name=role, email=f"audit_{role}@test.com", password_hash="h", role=urole)
        prev = app.dependency_overrides.get(get_current_user)
        app.dependency_overrides[get_current_user] = lambda: mock_user
        try:
            yield mock_user
        finally:
            if prev is not None:
                app.dependency_overrides[get_current_user] = prev
            else:
                app.dependency_overrides.pop(get_current_user, None)

    def test_01_list_audit_events(self):
        with self._patch_user("admin"):
            resp = self.client.get("/api/admin/audit/events")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["total"], 3)
        self.assertEqual(len(body["items"]), 3)

    def test_02_filter_audit_events(self):
        with self._patch_user("admin"):
            resp = self.client.get("/api/admin/audit/events?event_type=ADMIN_ACTION&action=approve")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["items"][0]["entity_type"], "document_version")

    def test_03_filter_audit_events_by_actor_and_entity(self):
        with self._patch_user("researcher"):
            resp = self.client.get(f"/api/admin/audit/events?actor_id={self.citizen_id}&entity_type=ai_query")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["items"][0]["action"], "QUERY")

    def test_04_get_trace_detail(self):
        with self._patch_user("admin"):
            resp = self.client.get(f"/api/admin/audit/events/trace/{self.trace_1}")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["trace_id"], self.trace_1)
        self.assertEqual(len(body["events"]), 2)
        self.assertIsNotNone(body["ai_request_audit"])
        self.assertEqual(body["ai_request_audit"]["final_decision"], "SHOW")

    def test_05_trace_not_found_404(self):
        with self._patch_user("admin"):
            resp = self.client.get("/api/admin/audit/events/trace/non-existent-trace-id")
        self.assertEqual(resp.status_code, 404)

    def test_06_list_ai_request_audits_and_filters(self):
        with self._patch_user("admin"):
            resp = self.client.get("/api/admin/audit/ai-requests?final_decision=ABSTAIN")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["items"][0]["model_name"], "gpt-4o-mini")

    def test_07_get_single_ai_request_audit(self):
        with self._patch_user("admin"):
            resp = self.client.get(f"/api/admin/audit/ai-requests/{self.ai_audit_1_id}")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["id"], self.ai_audit_1_id)
        self.assertEqual(body["supported_claims"], 2)

    def test_08_ai_request_audit_not_found_404(self):
        with self._patch_user("admin"):
            resp = self.client.get("/api/admin/audit/ai-requests/99999")
        self.assertEqual(resp.status_code, 404)

    def test_09_audit_stats(self):
        with self._patch_user("admin"):
            resp = self.client.get("/api/admin/audit/stats")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["total_events"], 3)
        self.assertEqual(body["total_ai_audits"], 2)
        self.assertEqual(body["events_today"], 3)
        self.assertEqual(body["unique_actors_today"], 2)
        self.assertGreaterEqual(len(body["top_actions"]), 1)

    def test_10_rbac_citizen_and_staff_forbidden(self):
        for role in ("citizen", "staff"):
            with self._patch_user(role):
                resp = self.client.get("/api/admin/audit/events")
                self.assertEqual(resp.status_code, 403, f"Expected 403 for {role}")

    def test_11_invalid_date_filter_422(self):
        with self._patch_user("admin"):
            resp = self.client.get("/api/admin/audit/events?date_from=not-a-date")
        self.assertEqual(resp.status_code, 422)


if __name__ == "__main__":
    unittest.main()
