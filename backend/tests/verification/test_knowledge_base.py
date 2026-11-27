"""
Feature 10 — Knowledge Base Management Tests.

Covers:
  1. Upload a new document version
  2. List versions with pagination
  3. Approve a version (auto-supersedes previous published)
  4. Reject a version with reason
  5. Re-index / re-trigger processing pipeline
  6. Expiry monitoring — expiring and expired documents
  7. KB aggregate statistics
  8. RBAC — citizens cannot access admin KB endpoints
  9. Version status lifecycle validation
  10. Processing job is created with version
"""

import os
import sys
import math
import datetime
import tempfile
import unittest
from contextlib import contextmanager
from io import BytesIO
from unittest.mock import patch

# ------------------------------------------------------------------ #
#  Path setup — run from project root or backend/                     #
# ------------------------------------------------------------------ #
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
import app.models  # noqa: F401 — register all models with Base before importing app
from app.main import app


# ------------------------------------------------------------------ #
#  Test setup                                                         #
# ------------------------------------------------------------------ #

class TestKnowledgeBaseManagement(unittest.TestCase):
    """Integration tests for the Knowledge Base Management endpoints."""

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

        # Seed a minimal admin, citizen and document
        db = cls.TestSession()
        from app.models.user import User, UserRole
        from app.models.village import Village
        from app.models.document import Document

        village = Village(name="TestVillage", district="TestDistrict", state="TestState", pincode="123456")
        db.add(village)
        db.flush()

        admin = User(
            name="Admin User", email="kb_admin@test.com",
            password_hash="hashed", role=UserRole.ADMIN, village_id=village.id,
        )
        citizen = User(
            name="Citizen User", email="kb_citizen@test.com",
            password_hash="hashed", role=UserRole.CITIZEN, village_id=village.id,
        )
        staff = User(
            name="Staff User", email="kb_staff@test.com",
            password_hash="hashed", role=UserRole.PANCHAYAT_STAFF, village_id=village.id,
        )
        db.add_all([admin, citizen, staff])
        db.flush()

        doc = Document(
            title="Water Supply Guidelines",
            file_path="kb_documents/water_supply.pdf",
            document_type="PDF",
            source="State Water Board",
            department="Water",
            version="1.0",
            status="indexed",
        )
        db.add(doc)
        db.commit()

        cls.admin_id = admin.id
        cls.citizen_id = citizen.id
        cls.staff_id = staff.id
        cls.doc_id = doc.id
        db.close()

        # Create a temporary upload directory
        cls._temp_dir = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=cls.engine)
        cls.engine.dispose()
        import shutil
        shutil.rmtree(cls._temp_dir, ignore_errors=True)

    # ---- Auth helpers ------------------------------------------------

    def _auth_header(self, role="admin"):
        """Return a mock Authorization header by patching get_current_user."""
        return role

    @contextmanager
    def _patch_user(self, role="admin"):
        """Context manager that overrides FastAPI get_current_user dependency."""
        from app.models.user import User, UserRole
        role_map = {
            "admin": (self.admin_id, UserRole.ADMIN),
            "citizen": (self.citizen_id, UserRole.CITIZEN),
            "staff": (self.staff_id, UserRole.PANCHAYAT_STAFF),
        }
        uid, urole = role_map[role]
        mock_user = User(id=uid, name=f"{role}", email=f"kb_{role}@test.com",
                         password_hash="h", role=urole)
        prev = app.dependency_overrides.get(get_current_user)
        app.dependency_overrides[get_current_user] = lambda: mock_user
        try:
            yield mock_user
        finally:
            if prev is not None:
                app.dependency_overrides[get_current_user] = prev
            else:
                app.dependency_overrides.pop(get_current_user, None)

    def _upload_version(self, doc_id=None, role="admin", **form_extras):
        """Helper to upload a version and return the response."""
        doc_id = doc_id or self.doc_id
        with self._patch_user(role):
            data = {"change_summary": "Updated regulations", **form_extras}
            files = {"file": ("update_v2.pdf", BytesIO(b"PDF content v2"), "application/pdf")}
            # Patch settings.UPLOAD_DIR to temp dir
            with patch("app.api.knowledge_base.settings") as mock_settings:
                mock_settings.UPLOAD_DIR = self._temp_dir
                resp = self.client.post(
                    f"/api/admin/kb/documents/{doc_id}/versions",
                    data=data,
                    files=files,
                )
        return resp

    # ================================================================ #
    #  Tests                                                           #
    # ================================================================ #

    def test_01_upload_version(self):
        """POST /admin/kb/documents/{id}/versions creates a version + processing job."""
        resp = self._upload_version()
        self.assertEqual(resp.status_code, 201, resp.text)
        body = resp.json()
        self.assertEqual(body["document_id"], self.doc_id)
        self.assertEqual(body["version_number"], 1)
        self.assertEqual(body["status"], "UPLOADED")
        self.assertIsNotNone(body["file_hash"])
        # Processing job should be created
        self.assertIsNotNone(body.get("processing_job"))
        self.assertEqual(body["processing_job"]["extraction_status"], "PENDING")

    def test_02_list_versions(self):
        """GET /admin/kb/documents/{id}/versions returns paginated list."""
        # Upload a second version
        self._upload_version()

        with self._patch_user("admin"):
            resp = self.client.get(f"/api/admin/kb/documents/{self.doc_id}/versions")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertGreaterEqual(body["total"], 2)
        self.assertEqual(body["page"], 1)
        self.assertIsInstance(body["items"], list)

    def test_03_get_single_version(self):
        """GET /admin/kb/versions/{id} returns version with processing job."""
        # Use the first version we created (id=1)
        with self._patch_user("admin"):
            resp = self.client.get("/api/admin/kb/versions/1")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["id"], 1)
        self.assertIn("processing_job", body)

    def test_04_approve_version(self):
        """PUT /admin/kb/versions/{id}/approve publishes and supersedes prior."""
        # Approve version 1
        with self._patch_user("admin"):
            resp = self.client.put(
                "/api/admin/kb/versions/1/approve",
                json={"effective_until": "2027-12-31T00:00:00"},
            )
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["status"], "PUBLISHED")
        self.assertIsNotNone(body["approved_at"])

    def test_05_approve_supersedes_previous(self):
        """Approving a new version supersedes the currently-published one."""
        with self._patch_user("admin"):
            resp = self.client.put(
                "/api/admin/kb/versions/2/approve",
                json={},
            )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "PUBLISHED")

        # Version 1 should now be SUPERSEDED
        with self._patch_user("admin"):
            resp = self.client.get("/api/admin/kb/versions/1")
        self.assertEqual(resp.json()["status"], "SUPERSEDED")

    def test_06_reject_version(self):
        """PUT /admin/kb/versions/{id}/reject sets status to REJECTED."""
        # Upload a third version to reject
        resp = self._upload_version()
        vid = resp.json()["id"]

        with self._patch_user("admin"):
            resp = self.client.put(
                f"/api/admin/kb/versions/{vid}/reject",
                json={"reason": "Formatting does not meet standards"},
            )
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["status"], "REJECTED")
        self.assertEqual(body["rejection_reason"], "Formatting does not meet standards")

    def test_07_cannot_reject_published(self):
        """Rejecting a PUBLISHED version returns 400."""
        with self._patch_user("admin"):
            resp = self.client.put(
                "/api/admin/kb/versions/2/reject",
                json={"reason": "Too late"},
            )
        self.assertEqual(resp.status_code, 400)

    def test_08_reindex_version(self):
        """POST /admin/kb/versions/{id}/reindex resets processing job."""
        with self._patch_user("admin"):
            resp = self.client.post("/api/admin/kb/versions/2/reindex")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["status"], "PROCESSING")
        job = body["processing_job"]
        self.assertEqual(job["extraction_status"], "PENDING")
        self.assertEqual(job["embedding_status"], "PENDING")
        self.assertEqual(job["indexing_status"], "PENDING")

    def test_09_expiring_documents(self):
        """GET /admin/kb/expiring returns documents expiring within N days."""
        # Upload and approve a new version with an effective_until date within 15 days
        upload_resp = self._upload_version()
        self.assertEqual(upload_resp.status_code, 201)
        vid = upload_resp.json()["id"]

        soon = (datetime.datetime.utcnow() + datetime.timedelta(days=10)).isoformat()
        with self._patch_user("admin"):
            app_resp = self.client.put(
                f"/api/admin/kb/versions/{vid}/approve",
                json={"effective_until": soon},
            )
            self.assertEqual(app_resp.status_code, 200, app_resp.text)
            resp = self.client.get("/api/admin/kb/expiring?days=30")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIsInstance(body, list)
        # Should find the version we just set to expire
        expiring_ids = [item["version_id"] for item in body]
        self.assertIn(vid, expiring_ids)

    def test_10_kb_stats(self):
        """GET /admin/kb/stats returns aggregate statistics."""
        with self._patch_user("admin"):
            resp = self.client.get("/api/admin/kb/stats")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertGreaterEqual(body["total_documents"], 1)
        self.assertGreaterEqual(body["total_versions"], 2)
        self.assertIsInstance(body["published_versions"], int)
        self.assertIsInstance(body["failed_processing"], int)

    def test_11_rbac_citizen_blocked(self):
        """Citizens cannot access admin KB endpoints."""
        with self._patch_user("citizen"):
            resp = self.client.get(f"/api/admin/kb/documents/{self.doc_id}/versions")
        self.assertEqual(resp.status_code, 403)

    def test_12_rbac_citizen_cannot_approve(self):
        """Citizens cannot approve versions."""
        with self._patch_user("citizen"):
            resp = self.client.put("/api/admin/kb/versions/1/approve", json={})
        self.assertEqual(resp.status_code, 403)

    def test_13_staff_can_upload(self):
        """Panchayat Staff can upload new versions."""
        resp = self._upload_version(role="staff")
        self.assertEqual(resp.status_code, 201)

    def test_14_staff_cannot_approve(self):
        """Panchayat Staff cannot approve versions (admin-only)."""
        with self._patch_user("staff"):
            resp = self.client.put("/api/admin/kb/versions/1/approve", json={})
        self.assertEqual(resp.status_code, 403)

    def test_15_version_not_found(self):
        """Accessing a non-existent version returns 404."""
        with self._patch_user("admin"):
            resp = self.client.get("/api/admin/kb/versions/9999")
        self.assertEqual(resp.status_code, 404)

    def test_16_document_not_found_on_upload(self):
        """Uploading a version for a non-existent document returns 404."""
        resp = self._upload_version(doc_id=9999)
        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
