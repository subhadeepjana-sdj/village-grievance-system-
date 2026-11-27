"""
Feature 12 — Model & RAG Management Tests.

Covers:
  1. Register a new LLM configuration (starts as TESTING)
  2. List model configurations
  3. Create RAG & Verification configuration versions
  4. Evaluation gate blocks activation when no passing evaluation exists (400)
  5. Evaluation gate fails when hallucination_rate > 0.10 or factual_accuracy < 0.80
  6. Passing evaluation allows activation / approval
  7. Activating a new configuration automatically retires the previous ACTIVE one
  8. Active configuration bundle endpoint (/admin/rag-config/active)
  9. RBAC enforcement (citizens blocked 403; researchers can evaluate/read but cannot approve/register)
  10. 404 on non-existent config
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


class TestModelAndRAGManagement(unittest.TestCase):
    """Integration tests for Feature 12 Model & RAG Management."""

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

        village = Village(name="MCVillage", district="D1", state="S1", pincode="700002")
        db.add(village)
        db.flush()

        admin = User(name="MC Admin", email="mc_admin@test.com", password_hash="h", role=UserRole.ADMIN, village_id=village.id)
        researcher = User(name="MC Researcher", email="mc_res@test.com", password_hash="h", role=UserRole.RESEARCHER, village_id=village.id)
        citizen = User(name="MC Citizen", email="mc_cit@test.com", password_hash="h", role=UserRole.CITIZEN, village_id=village.id)
        db.add_all([admin, researcher, citizen])
        db.commit()

        cls.admin_id = admin.id
        cls.researcher_id = researcher.id
        cls.citizen_id = citizen.id
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
        }
        uid, urole = role_map[role]
        mock_user = User(id=uid, name=role, email=f"mc_{role}@test.com", password_hash="h", role=urole)
        prev = app.dependency_overrides.get(get_current_user)
        app.dependency_overrides[get_current_user] = lambda: mock_user
        try:
            yield mock_user
        finally:
            if prev is not None:
                app.dependency_overrides[get_current_user] = prev
            else:
                app.dependency_overrides.pop(get_current_user, None)

    def test_01_register_and_list_models(self):
        with self._patch_user("admin"):
            resp = self.client.post(
                "/api/admin/models",
                json={
                    "name": "Llama 3.1 8B Grounded",
                    "version": "1.0",
                    "provider": "groq",
                    "model_identifier": "llama-3.1-8b-instant",
                    "temperature": 0.1,
                    "max_tokens": 1024,
                },
            )
            self.assertEqual(resp.status_code, 201, resp.text)
            self.assertEqual(resp.json()["status"], "TESTING")

            list_resp = self.client.get("/api/admin/models")
            self.assertEqual(list_resp.status_code, 200)
            self.assertEqual(len(list_resp.json()), 1)

    def test_02_create_rag_and_verification_configs(self):
        with self._patch_user("admin"):
            rag_resp = self.client.post(
                "/api/admin/rag-config",
                json={
                    "name": "BGE Dense Top-5",
                    "version": "2.0",
                    "top_k": 5,
                    "chunk_size": 512,
                    "similarity_threshold": 0.60,
                },
            )
            self.assertEqual(rag_resp.status_code, 201, rag_resp.text)

            verif_resp = self.client.post(
                "/api/admin/verification-config",
                json={
                    "name": "DeBERTa Strict Gate",
                    "version": "1.2",
                    "supported_threshold": 0.72,
                    "contradiction_threshold": 0.65,
                    "max_retries": 2,
                },
            )
            self.assertEqual(verif_resp.status_code, 201, verif_resp.text)

    def test_03_activate_blocked_without_passing_eval(self):
        with self._patch_user("admin"):
            resp = self.client.put("/api/admin/models/1/activate")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Evaluation gate not passed", resp.json()["detail"])

    def test_04_failed_evaluation_still_blocks_activation(self):
        with self._patch_user("researcher"):
            eval_resp = self.client.post(
                "/api/admin/configs/MODEL/1/evaluate",
                json={
                    "evaluation_dataset": "village_bench_v1",
                    "factual_accuracy": 0.72,
                    "hallucination_rate": 0.18,
                    "faithfulness": 0.75,
                },
            )
        self.assertEqual(eval_resp.status_code, 201)
        self.assertEqual(eval_resp.json()["passed_gate"], 0)

        with self._patch_user("admin"):
            act_resp = self.client.put("/api/admin/models/1/activate")
        self.assertEqual(act_resp.status_code, 400)

    def test_05_passing_evaluation_allows_activation(self):
        with self._patch_user("researcher"):
            eval_resp = self.client.post(
                "/api/admin/configs/MODEL/1/evaluate",
                json={
                    "evaluation_dataset": "village_bench_v1",
                    "factual_accuracy": 0.93,
                    "hallucination_rate": 0.03,
                    "faithfulness": 0.95,
                },
            )
        self.assertEqual(eval_resp.status_code, 201)
        self.assertEqual(eval_resp.json()["passed_gate"], 1)

        with self._patch_user("admin"):
            act_resp = self.client.put("/api/admin/models/1/activate")
        self.assertEqual(act_resp.status_code, 200)
        self.assertEqual(act_resp.json()["status"], "ACTIVE")

    def test_06_activating_second_model_retires_first(self):
        with self._patch_user("admin"):
            m2 = self.client.post(
                "/api/admin/models",
                json={
                    "name": "Llama 3.3 70B",
                    "version": "2.0",
                    "provider": "groq",
                    "model_identifier": "llama-3.3-70b-versatile",
                },
            ).json()
            self.client.post(
                f"/api/admin/configs/MODEL/{m2['id']}/evaluate",
                json={
                    "factual_accuracy": 0.96,
                    "hallucination_rate": 0.02,
                    "faithfulness": 0.97,
                },
            )
            approve_resp = self.client.put(
                f"/api/admin/configs/MODEL/{m2['id']}/approve",
                json={"notes": "Promoted after superior benchmark results"},
            )
            self.assertEqual(approve_resp.status_code, 200)
            self.assertEqual(approve_resp.json()["status"], "ACTIVE")

            models = {m["id"]: m for m in self.client.get("/api/admin/models").json()}
            self.assertEqual(models[1]["status"], "RETIRED")
            self.assertEqual(models[m2["id"]]["status"], "ACTIVE")

    def test_07_approve_rag_and_verification_and_fetch_active_bundle(self):
        with self._patch_user("admin"):
            self.client.post(
                "/api/admin/configs/RAG/1/evaluate",
                json={"factual_accuracy": 0.90, "hallucination_rate": 0.04, "faithfulness": 0.91},
            )
            self.client.put("/api/admin/configs/RAG/1/approve", json={})

            self.client.post(
                "/api/admin/configs/VERIFICATION/1/evaluate",
                json={"factual_accuracy": 0.92, "hallucination_rate": 0.03, "faithfulness": 0.94},
            )
            self.client.put("/api/admin/configs/VERIFICATION/1/approve", json={})

            bundle = self.client.get("/api/admin/rag-config/active")
        self.assertEqual(bundle.status_code, 200)
        body = bundle.json()
        self.assertEqual(body["active_model"]["name"], "Llama 3.3 70B")
        self.assertEqual(body["active_rag"]["name"], "BGE Dense Top-5")
        self.assertEqual(body["active_verification"]["name"], "DeBERTa Strict Gate")

    def test_08_rbac_enforcement(self):
        with self._patch_user("citizen"):
            self.assertEqual(self.client.get("/api/admin/models").status_code, 403)
            self.assertEqual(self.client.get("/api/admin/rag-config/active").status_code, 403)

        with self._patch_user("researcher"):
            self.assertEqual(self.client.get("/api/admin/models").status_code, 200)
            self.assertEqual(
                self.client.post(
                    "/api/admin/models",
                    json={"name": "Unauthorized", "provider": "groq", "model_identifier": "llama-3.1-8b"},
                ).status_code,
                403,
            )

    def test_09_not_found_404(self):
        with self._patch_user("admin"):
            resp = self.client.post(
                "/api/admin/configs/RAG/9999/evaluate",
                json={"factual_accuracy": 0.9, "hallucination_rate": 0.05, "faithfulness": 0.9},
            )
        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
