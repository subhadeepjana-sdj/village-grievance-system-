"""
MongoDB Persistence Layer & Media Endpoint Tests.

Covers:
  1. Graceful disabled behavior when MONGODB_URI is empty
  2. store_media & get_media persistence with simulated PyMongo collection
  3. upsert_complaint, log_ai_trace, store_kb_document, upsert_feedback, log_audit_event
  4. GET /api/media/{media_id} streams binary bytes with correct Content-Type (and 404 when missing)
  5. GET /api/admin/audit/mongodb-status returns connection & collection counts (with RBAC check)
"""

import os
import sys
import unittest
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

_this_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.abspath(os.path.join(_this_dir, "..", ".."))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from fastapi.testclient import TestClient
from app.api.auth import get_current_user
from app.main import app


class _InMemoryCollection:
    def __init__(self):
        self.docs = []

    def create_index(self, *args, **kwargs):
        return None

    def insert_one(self, doc):
        self.docs.append(dict(doc))

    def find_one(self, query, projection=None):
        for doc in self.docs:
            if all(doc.get(k) == v for k, v in query.items()):
                return dict(doc)
        return None

    def update_one(self, query, update, upsert=False):
        for idx, doc in enumerate(self.docs):
            if all(doc.get(k) == v for k, v in query.items()):
                self.docs[idx].update(update.get("$set", {}))
                return
        if upsert:
            merged = {**query, **update.get("$set", {})}
            self.docs.append(merged)

    def find(self, query=None, projection=None):
        query = query or {}
        out = []
        for doc in self.docs:
            if all(doc.get(k) == v for k, v in query.items()):
                item = dict(doc)
                if projection and projection.get("_id") == 0:
                    item.pop("_id", None)
                out.append(item)
        return out

    def count_documents(self, query):
        return len(self.docs)


class _InMemoryMongoDB:
    def __init__(self):
        self._cols = {}

    def __getitem__(self, name):
        if name not in self._cols:
            self._cols[name] = _InMemoryCollection()
        return self._cols[name]


class TestMongoDBPersistence(unittest.TestCase):
    """Unit & API tests for MongoDBService and /api/media + /api/admin/audit/mongodb-status."""

    def setUp(self):
        from app.database.mongodb import MongoDBService

        self.svc = MongoDBService()
        self.mock_db = _InMemoryMongoDB()
        self.svc.db = self.mock_db
        self.svc.connected = True
        self.svc.last_error = None
        self.client = TestClient(app)

    @contextmanager
    def _override_user(self, is_admin=True):
        from app.models.user import User, UserRole
        user = User(
            id=1,
            name="Tester",
            email="tester@village.gov.in",
            password_hash="h",
            role=UserRole.ADMIN if is_admin else UserRole.CITIZEN,
        )
        prev = app.dependency_overrides.get(get_current_user)
        app.dependency_overrides[get_current_user] = lambda: user
        try:
            yield
        finally:
            if prev is not None:
                app.dependency_overrides[get_current_user] = prev
            else:
                app.dependency_overrides.pop(get_current_user, None)

    def test_01_disabled_when_uri_missing(self):
        from app.database.mongodb import MongoDBService
        with patch("app.database.mongodb.settings") as mock_settings:
            mock_settings.MONGODB_URI = ""
            mock_settings.MONGODB_DB_NAME = "village_grievance"
            svc = MongoDBService()
            self.assertFalse(svc.connected)
            self.assertIsNone(svc.store_media(b"abc", "a.png", "image/png"))
            self.assertFalse(svc.upsert_complaint({"complaint_number": "GRV-1"}))

    def test_02_store_and_get_media(self):
        media_id = self.svc.store_media(b"\x89PNG\r\n", "evidence.png", "image/png", subfolder="complaints")
        self.assertIsNotNone(media_id)
        fetched = self.svc.get_media(media_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(bytes(fetched["data"]), b"\x89PNG\r\n")
        self.assertEqual(fetched["filename"], "evidence.png")

    def test_03_mirror_collections_and_status(self):
        self.assertTrue(self.svc.upsert_complaint({"complaint_number": "GRV-2026-100", "status": "SUBMITTED"}))
        self.assertTrue(self.svc.upsert_complaint({"complaint_number": "GRV-2026-100", "status": "RESOLVED"}))
        self.assertTrue(self.svc.log_ai_trace({"response_id": 10, "decision": "SHOW"}))
        self.assertTrue(self.svc.store_kb_document({"document_id": 2, "version": "1.0", "title": "Charter"}))
        self.assertTrue(self.svc.upsert_feedback({"feedback_id": 5, "feedback_type": "INCORRECT"}))
        self.assertTrue(self.svc.log_audit_event({"action": "CREATE", "entity_type": "complaint"}))

        status = self.svc.get_status()
        self.assertTrue(status["connected"])
        self.assertEqual(status["collections"]["complaints"], 1)
        self.assertEqual(status["collections"]["ai_traces"], 1)
        self.assertEqual(status["collections"]["kb_documents"], 1)
        self.assertEqual(status["collections"]["ai_feedback"], 1)
        self.assertEqual(status["collections"]["audit_events"], 1)

    def test_04_media_endpoint_serves_binary_and_404(self):
        media_id = self.svc.store_media(b"fake-jpeg-bytes", "photo.jpg", "image/jpeg")
        with patch("app.api.media.mongodb_service", self.svc):
            ok_resp = self.client.get(f"/api/media/{media_id}")
            self.assertEqual(ok_resp.status_code, 200)
            self.assertEqual(ok_resp.content, b"fake-jpeg-bytes")
            self.assertEqual(ok_resp.headers["content-type"], "image/jpeg")

            miss_resp = self.client.get("/api/media/nonexistent-id")
            self.assertEqual(miss_resp.status_code, 404)

    def test_05_mongodb_status_endpoint_and_rbac(self):
        with patch("app.api.audit.mongodb_service", self.svc):
            with self._override_user(is_admin=True):
                resp = self.client.get("/api/admin/audit/mongodb-status")
                self.assertEqual(resp.status_code, 200)
                self.assertTrue(resp.json()["connected"])

            with self._override_user(is_admin=False):
                resp = self.client.get("/api/admin/audit/mongodb-status")
                self.assertEqual(resp.status_code, 403)

    def test_06_user_submits_and_admin_reads_updates_via_mongodb(self):
        from app.database.session import SessionLocal, Base, engine
        from app.database.seed_data import seed_database
        from app.models.complaint import Complaint, ComplaintStatusHistory

        Base.metadata.create_all(bind=engine)
        seed_database(include_demo_data=False)

        with patch("app.api.complaints.mongodb_service", self.svc), \
             patch("app.api.admin.mongodb_service", self.svc):
            # 1. Citizen submits complaint -> persisted in MongoDB
            with self._override_user(is_admin=False):
                create_resp = self.client.post(
                    "/api/complaints",
                    data={
                        "category": "Water Supply",
                        "title": "Broken handpump at Ward 2",
                        "description": "Handpump handle detached completely since morning.",
                        "location": "Ward 2, East Tola",
                        "priority": "HIGH",
                    },
                )
                self.assertEqual(create_resp.status_code, 200)
                cnum = create_resp.json()["complaint_number"]

            # 2. Wipe SQLAlchemy rows to simulate ephemeral/clean container
            db = SessionLocal()
            try:
                db.query(ComplaintStatusHistory).delete()
                db.query(Complaint).delete()
                db.commit()
            finally:
                db.close()

            # 3. Admin logs in on a clean container & sees Citizen's complaint from MongoDB
            with self._override_user(is_admin=True):
                list_resp = self.client.get("/api/complaints")
                self.assertEqual(list_resp.status_code, 200)
                numbers = [c["complaint_number"] for c in list_resp.json()]
                self.assertIn(cnum, numbers)

                stats_resp = self.client.get("/api/admin/statistics")
                self.assertEqual(stats_resp.status_code, 200)
                self.assertGreaterEqual(stats_resp.json()["summary"]["total_complaints"], 1)

                # 4. Admin resolves the MongoDB-only complaint
                patch_resp = self.client.patch(
                    f"/api/complaints/{cnum}",
                    json={"status": "RESOLVED", "remarks": "Replaced valve in Ward 2"},
                )
                self.assertEqual(patch_resp.status_code, 200)
                self.assertEqual(patch_resp.json()["status"], "RESOLVED")
                self.assertEqual(len(patch_resp.json()["history"]), 2)

    def test_07_admin_statistics_zero_without_dummy_fallbacks(self):
        from app.database.session import SessionLocal, Base, engine
        from app.models.ai_records import AIQuery, AIResponse, Evidence, VerificationResult, AIResponseCitation

        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            db.query(AIResponseCitation).delete()
            db.query(VerificationResult).delete()
            db.query(Evidence).delete()
            db.query(AIResponse).delete()
            db.query(AIQuery).delete()
            db.commit()
        finally:
            db.close()

        with patch("app.api.admin.mongodb_service", self.svc):
            with self._override_user(is_admin=True):
                resp = self.client.get("/api/admin/statistics")
                self.assertEqual(resp.status_code, 200)
                ai_stats = resp.json()["ai_statistics"]
                self.assertEqual(ai_stats["total_ai_questions"], 0)
                self.assertEqual(ai_stats["supported_percentage"], 0.0)
                self.assertEqual(ai_stats["average_confidence"], 0.0)


if __name__ == "__main__":
    unittest.main()
