"""
Feature 9 — AI Feedback & Error Review Tests.

Covers:
  1. Citizen submits feedback on an AI response (201)
  2. Invalid response_id returns 404
  3. Invalid feedback_type returns 422
  4. Citizen retrieves their own feedback (/api/feedback/my)
  5. Admin lists feedback with pagination & status/type filters
  6. Admin detail drilldown includes AI answer, evidence, and verification claims
  7. Admin submits error review with root-cause classification & resolves feedback
  8. Filter feedback by root_cause
  9. Stats aggregation (counts, resolution rate, breakdowns)
  10. RBAC enforcement (citizen blocked from admin endpoints; researcher cannot write review)
"""

import os
import sys
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


class TestAIFeedbackAndErrorReview(unittest.TestCase):
    """Integration tests for Feature 9 AI Feedback & Error Review."""

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
        from app.models.ai_records import AIQuery, AIResponse, Evidence, VerificationResult

        village = Village(name="FBVillage", district="D1", state="S1", pincode="700001")
        db.add(village)
        db.flush()

        admin = User(name="FB Admin", email="fb_admin@test.com", password_hash="h", role=UserRole.ADMIN, village_id=village.id)
        citizen = User(name="FB Citizen", email="fb_cit@test.com", password_hash="h", role=UserRole.CITIZEN, village_id=village.id)
        researcher = User(name="FB Researcher", email="fb_res@test.com", password_hash="h", role=UserRole.RESEARCHER, village_id=village.id)
        db.add_all([admin, citizen, researcher])
        db.flush()

        q = AIQuery(user_id=citizen.id, question="When will my road complaint be resolved?", query_type="TIMELINE")
        db.add(q)
        db.flush()

        resp = AIResponse(
            query_id=q.id,
            answer="Road repairs take 14 days under Panchayat SLA.",
            decision="SHOW",
            confidence=0.88,
            processing_time=1.2,
        )
        db.add(resp)
        db.flush()

        ev = Evidence(
            response_id=resp.id,
            document_id=1,
            chunk_id="chunk-42",
            similarity_score=0.91,
            evidence_text="Rural road maintenance SLA is 14 working days.",
            source_type="KNOWLEDGE_BASE",
        )
        vr = VerificationResult(
            response_id=resp.id,
            claim="Road repairs take 14 days.",
            evidence="Rural road maintenance SLA is 14 working days.",
            verification_result="SUPPORTED",
            confidence=0.93,
        )
        db.add_all([ev, vr])
        db.commit()

        cls.admin_id = admin.id
        cls.citizen_id = citizen.id
        cls.researcher_id = researcher.id
        cls.response_id = resp.id
        db.close()

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=cls.engine)
        cls.engine.dispose()

    @contextmanager
    def _patch_user(self, role="citizen"):
        from app.models.user import User, UserRole
        role_map = {
            "admin": (self.admin_id, UserRole.ADMIN),
            "citizen": (self.citizen_id, UserRole.CITIZEN),
            "researcher": (self.researcher_id, UserRole.RESEARCHER),
        }
        uid, urole = role_map[role]
        mock_user = User(id=uid, name=role, email=f"fb_{role}@test.com", password_hash="h", role=urole)
        prev = app.dependency_overrides.get(get_current_user)
        app.dependency_overrides[get_current_user] = lambda: mock_user
        try:
            yield mock_user
        finally:
            if prev is not None:
                app.dependency_overrides[get_current_user] = prev
            else:
                app.dependency_overrides.pop(get_current_user, None)

    def test_01_citizen_submits_feedback(self):
        with self._patch_user("citizen"):
            resp = self.client.post(
                "/api/feedback",
                json={
                    "response_id": self.response_id,
                    "feedback_type": "INCORRECT",
                    "description": "The SLA was updated to 7 days last month.",
                },
            )
        self.assertEqual(resp.status_code, 201, resp.text)
        body = resp.json()
        self.assertEqual(body["status"], "PENDING")
        self.assertEqual(body["feedback_type"], "INCORRECT")
        self.assertEqual(body["user_id"], self.citizen_id)

    def test_02_submit_feedback_invalid_response_404(self):
        with self._patch_user("citizen"):
            resp = self.client.post(
                "/api/feedback",
                json={"response_id": 99999, "feedback_type": "HELPFUL"},
            )
        self.assertEqual(resp.status_code, 404)

    def test_03_submit_feedback_invalid_type_422(self):
        with self._patch_user("citizen"):
            resp = self.client.post(
                "/api/feedback",
                json={"response_id": self.response_id, "feedback_type": "INVALID_TYPE"},
            )
        self.assertEqual(resp.status_code, 422)

    def test_04_my_feedback(self):
        with self._patch_user("citizen"):
            resp = self.client.get("/api/feedback/my")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertGreaterEqual(len(body), 1)
        self.assertEqual(body[0]["response_id"], self.response_id)

    def test_05_admin_list_and_filter(self):
        # Submit a second HELPFUL feedback
        with self._patch_user("citizen"):
            self.client.post(
                "/api/feedback",
                json={"response_id": self.response_id, "feedback_type": "HELPFUL", "description": "Clear answer"},
            )

        with self._patch_user("admin"):
            resp = self.client.get("/api/admin/feedback?feedback_type=INCORRECT")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["items"][0]["feedback_type"], "INCORRECT")

    def test_06_admin_feedback_detail_drilldown(self):
        with self._patch_user("admin"):
            resp = self.client.get("/api/admin/feedback/1")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["feedback"]["id"], 1)
        self.assertIn("14 days", body["answer"])
        self.assertEqual(len(body["evidences"]), 1)
        self.assertEqual(len(body["verification_results"]), 1)

    def test_07_admin_review_and_resolve(self):
        with self._patch_user("admin"):
            resp = self.client.put(
                "/api/admin/feedback/1/review",
                json={
                    "status": "RESOLVED",
                    "root_cause": "OUTDATED_DOCUMENT",
                    "corrective_action": "Uploaded updated 7-day SLA circular v2.",
                    "resolution_notes": "Confirmed outdated policy doc in KB.",
                },
            )
        self.assertEqual(resp.status_code, 200, resp.text)
        body = resp.json()
        self.assertEqual(body["status"], "RESOLVED")
        self.assertEqual(len(body["reviews"]), 1)
        self.assertEqual(body["reviews"][0]["root_cause"], "OUTDATED_DOCUMENT")
        self.assertIsNotNone(body["reviews"][0]["resolved_at"])

    def test_08_filter_by_root_cause(self):
        with self._patch_user("researcher"):
            resp = self.client.get("/api/admin/feedback?root_cause=OUTDATED_DOCUMENT")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["items"][0]["id"], 1)

    def test_09_feedback_stats(self):
        with self._patch_user("admin"):
            resp = self.client.get("/api/admin/feedback/stats")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["total_feedback"], 2)
        self.assertEqual(body["resolved_count"], 1)
        self.assertEqual(body["pending_count"], 1)
        self.assertEqual(body["resolution_rate"], 50.0)
        self.assertEqual(body["by_root_cause"]["OUTDATED_DOCUMENT"], 1)

    def test_10_rbac_enforcement(self):
        with self._patch_user("citizen"):
            self.assertEqual(self.client.get("/api/admin/feedback").status_code, 403)
            self.assertEqual(self.client.get("/api/admin/feedback/stats").status_code, 403)
            self.assertEqual(
                self.client.put(
                    "/api/admin/feedback/1/review",
                    json={"status": "RESOLVED", "root_cause": "OTHER"},
                ).status_code,
                403,
            )

        # Researcher can read stats/list, but cannot submit review edits
        with self._patch_user("researcher"):
            self.assertEqual(self.client.get("/api/admin/feedback/stats").status_code, 200)
            self.assertEqual(
                self.client.put(
                    "/api/admin/feedback/1/review",
                    json={"status": "RESOLVED", "root_cause": "OTHER"},
                ).status_code,
                403,
            )


if __name__ == "__main__":
    unittest.main()
