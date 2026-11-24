"""
Feature 8 — AI Verification Center Test Suite
=============================================

Tests all administrative and research verification inspection endpoints:
  1. GET /api/admin/verification/overview (summary stats, distributions)
  2. GET /api/admin/verification/interactions (list, pagination, filtering)
  3. GET /api/admin/verification/interactions/{id} (7 core audit questions)
  4. GET /api/admin/verification/claims/{id} (claim detail & rationale)
  5. GET /api/admin/verification/evidence/{id} (evidence chunk & grounded claims)
  6. GET /api/admin/verification/corrections/{id} (regeneration history)
  7. GET /api/admin/verification/reports (evaluation metrics)
  8. POST /api/admin/verification/feedback (human-in-the-loop feedback)
  9. Error cases (404 Not Found on invalid IDs)
  10. RBAC Authorization (403 Forbidden for non-admin/researcher)
"""

import os
import sys
import unittest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Path fixup
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import app.models  # Ensure all ORM models are registered in Base.metadata
from app.main import app
from app.database.session import Base, get_db
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.ai_records import (
    AIQuery,
    AIResponse,
    Evidence,
    VerificationResult,
    AICorrectionLog,
    AIAbstentionLog,
    AIResponseCitation,
    AIVerificationFeedback,
    ResearchMetric,
)


class TestVerificationCenter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up in-memory SQLite database and test seed data."""
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=cls.engine)
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        cls.db = cls.SessionLocal()

        # Seed Users (Admin, Researcher, Citizen)
        cls.admin_user = User(
            id=1,
            name="Admin User",
            email="admin@test.gov",
            password_hash="fakehash",
            role=UserRole.ADMIN,
        )
        cls.researcher_user = User(
            id=2,
            name="Researcher User",
            email="researcher@test.gov",
            password_hash="fakehash",
            role=UserRole.RESEARCHER,
        )
        cls.citizen_user = User(
            id=3,
            name="Citizen User",
            email="citizen@test.gov",
            password_hash="fakehash",
            role=UserRole.CITIZEN,
        )
        cls.db.add_all([cls.admin_user, cls.researcher_user, cls.citizen_user])
        cls.db.commit()

        # Seed AI Interaction: Query -> Response
        cls.query_1 = AIQuery(
            id=1,
            user_id=1,
            question="Who handles complaint GRV-2026-001024?",
            query_type="GENERAL",
        )
        cls.db.add(cls.query_1)
        cls.db.commit()

        cls.response_1 = AIResponse(
            id=1,
            query_id=1,
            answer="Assigned to Village Water Department. Status is Under Review.",
            decision="SHOW",
            confidence=92.5,
            processing_time=1.25,
            configuration="rag_verification",
            created_at=datetime.utcnow(),
        )
        cls.db.add(cls.response_1)
        cls.db.commit()

        # Seed Evidences
        cls.evidence_1 = Evidence(
            id=1,
            response_id=1,
            document_id=10,
            chunk_id="chunk_w1",
            similarity_score=0.95,
            evidence_text="Complaint GRV-2026-001024 handled by Village Water Department.",
            source_type="COMPLAINT_RECORD",
        )
        cls.db.add(cls.evidence_1)

        # Seed Claims (Supported, Contradicted, Insufficient)
        cls.claim_supported = VerificationResult(
            id=1,
            response_id=1,
            claim="Assigned to Village Water Department",
            evidence="Complaint GRV-2026-001024 handled by Village Water Department.",
            verification_result="SUPPORTED",
            confidence=0.98,
            reason="Exact DB match",
        )
        cls.claim_contradicted = VerificationResult(
            id=2,
            response_id=1,
            claim="Handled by Road Department",
            evidence="Dept is Water Department",
            verification_result="CONTRADICTED",
            confidence=0.15,
            reason="Conflicting department in record",
        )
        cls.claim_insufficient = VerificationResult(
            id=3,
            response_id=1,
            claim="Expected to be repaired by tomorrow",
            evidence=None,
            verification_result="INSUFFICIENT_EVIDENCE",
            confidence=0.40,
            reason="No timeline found in database",
        )
        cls.db.add_all([cls.claim_supported, cls.claim_contradicted, cls.claim_insufficient])

        # Seed Correction Logs
        cls.correction_1 = AICorrectionLog(
            id=1,
            response_id=1,
            attempt_number=1,
            candidate_answer="Handled by Road Department.",
            status="CONTRADICTED",
            action="REGENERATE",
            confidence=40.0,
            prompt_directive="Do NOT claim Road Department handles water complaints.",
        )
        cls.db.add(cls.correction_1)

        # Seed Citations
        cls.citation_1 = AIResponseCitation(
            id=1,
            response_id=1,
            citation_label="[1]",
            source_type="COMPLAINT_RECORD",
            source_id="GRV-2026-001024",
            claim_text="Assigned to Village Water Department",
            source_field="department",
            source_value="Village Water Department",
            evidence_text="Complaint GRV-2026-001024 handled by Village Water Department.",
            relevance_score=0.95,
            verified=1,
            validation_status="VERIFIED",
            validation_message="Field match confirmed",
        )
        cls.db.add(cls.citation_1)

        # Seed Research Metric
        cls.metric_1 = ResearchMetric(
            id=1,
            run_id="BENCHMARK-RUN-001",
            config_type="RAG_VERIFICATION",
            factual_accuracy=96.4,
            hallucination_rate=2.1,
            faithfulness=94.5,
            retrieval_recall=91.0,
            precision=95.0,
            recall=93.5,
            f1_score=94.2,
            abstention_accuracy=98.0,
            avg_latency=1.35,
        )
        cls.db.add(cls.metric_1)
        cls.db.commit()

        # Set up FastAPI test client with override
        def override_get_db():
            db = cls.SessionLocal()
            try:
                yield db
            finally:
                db.close()

        def override_get_current_user():
            return cls.admin_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_get_current_user
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        app.dependency_overrides.clear()

    # ------------------------------------------------------------------ #
    #  Tests                                                              #
    # ------------------------------------------------------------------ #

    def test_01_verification_overview_endpoint(self):
        """GET /api/admin/verification/overview returns aggregated metrics."""
        res = self.client.get("/api/admin/verification/overview")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["total_interactions"], 1)
        self.assertEqual(data["total_claims_verified"], 3)
        self.assertEqual(data["supported_claims"], 1)
        self.assertEqual(data["contradicted_claims"], 1)
        self.assertEqual(data["insufficient_claims"], 1)
        self.assertEqual(data["total_corrections"], 1)
        self.assertGreater(data["avg_confidence"], 0)
        self.assertEqual(data["claim_distribution"]["SUPPORTED"], 1)

    def test_02_list_interactions_endpoint(self):
        """GET /api/admin/verification/interactions returns paginated list."""
        res = self.client.get("/api/admin/verification/interactions?page=1&page_size=10")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["total"], 1)
        self.assertEqual(len(data["items"]), 1)
        item = data["items"][0]
        self.assertEqual(item["id"], 1)
        self.assertEqual(item["decision"], "SHOW")
        self.assertEqual(item["claim_count"], 3)
        self.assertTrue(item["had_correction"])

    def test_03_list_interactions_with_filter(self):
        """Filtering by decision works as expected."""
        res = self.client.get("/api/admin/verification/interactions?decision=ABSTAIN")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["total"], 0)

        res_show = self.client.get("/api/admin/verification/interactions?decision=SHOW")
        self.assertEqual(res_show.status_code, 200)
        self.assertEqual(res_show.json()["total"], 1)

    def test_04_interaction_drilldown_7_questions(self):
        """GET /api/admin/verification/interactions/{id} answers all 7 core questions."""
        res = self.client.get("/api/admin/verification/interactions/1")
        self.assertEqual(res.status_code, 200)
        d = res.json()

        # 1. What did the LLM generate?
        self.assertIn("question_1_raw_generation", d)
        self.assertEqual(
            d["question_1_raw_generation"]["raw_candidate_answer"],
            "Handled by Road Department.",
        )
        self.assertTrue(d["question_1_raw_generation"]["had_regeneration"])

        # 2. Which factual claims were extracted?
        self.assertIn("question_2_extracted_claims", d)
        self.assertEqual(len(d["question_2_extracted_claims"]), 3)

        # 3. What evidence was retrieved?
        self.assertIn("question_3_retrieved_evidence", d)
        self.assertEqual(len(d["question_3_retrieved_evidence"]), 1)
        self.assertEqual(d["question_3_retrieved_evidence"][0]["source_type"], "COMPLAINT_RECORD")

        # 4. Which claims were supported?
        self.assertIn("question_4_supported_claims", d)
        self.assertEqual(len(d["question_4_supported_claims"]), 1)
        self.assertEqual(d["question_4_supported_claims"][0]["claim_text"], "Assigned to Village Water Department")

        # 5. Which claims were contradicted?
        self.assertIn("question_5_contradicted_claims", d)
        self.assertEqual(len(d["question_5_contradicted_claims"]), 1)
        self.assertEqual(d["question_5_contradicted_claims"][0]["claim_text"], "Handled by Road Department")

        # 6. Which claims had insufficient evidence?
        self.assertIn("question_6_insufficient_evidence_claims", d)
        self.assertEqual(len(d["question_6_insufficient_evidence_claims"]), 1)
        self.assertEqual(d["question_6_insufficient_evidence_claims"][0]["claim_text"], "Expected to be repaired by tomorrow")

        # 7. What corrections were made?
        self.assertIn("question_7_corrections_made", d)
        self.assertEqual(d["question_7_corrections_made"]["correction_attempts_count"], 1)
        self.assertEqual(
            d["question_7_corrections_made"]["delivered_final_answer"],
            "Assigned to Village Water Department. Status is Under Review.",
        )

        # Citations present
        self.assertEqual(len(d["citations"]), 1)
        self.assertEqual(d["citations"][0]["citation_label"], "[1]")

    def test_05_claim_detail_endpoint(self):
        """GET /api/admin/verification/claims/{id} returns claim rationale and linked citation."""
        res = self.client.get("/api/admin/verification/claims/1")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["claim"], "Assigned to Village Water Department")
        self.assertEqual(data["verification_result"], "SUPPORTED")
        self.assertIsNotNone(data["associated_citation"])
        self.assertEqual(data["associated_citation"]["citation_label"], "[1]")

    def test_06_evidence_detail_endpoint(self):
        """GET /api/admin/verification/evidence/{id} returns evidence text and linked claims."""
        res = self.client.get("/api/admin/verification/evidence/1")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["document_id"], 10)
        self.assertEqual(data["chunk_id"], "chunk_w1")
        self.assertIn("Complaint GRV-2026-001024", data["evidence_text"])
        self.assertGreater(len(data["verified_claims"]), 0)

    def test_07_correction_history_endpoint(self):
        """GET /api/admin/verification/corrections/{response_id} returns regeneration attempts."""
        res = self.client.get("/api/admin/verification/corrections/1")
        self.assertEqual(res.status_code, 200)
        logs = res.json()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["attempt_number"], 1)
        self.assertIn("Do NOT claim", logs[0]["prompt_directive"])

    def test_08_reports_endpoint(self):
        """GET /api/admin/verification/reports returns research evaluation metrics."""
        res = self.client.get("/api/admin/verification/reports")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(len(data), 1)
        self.assertEqual(data[0]["run_id"], "BENCHMARK-RUN-001")
        self.assertEqual(data[0]["factual_accuracy"], 96.4)

    def test_09_feedback_submission(self):
        """POST /api/admin/verification/feedback successfully logs human audit note."""
        payload = {
            "response_id": 1,
            "claim_id": 2,
            "feedback_type": "FALSE_CONTRADICTION",
            "corrected_verdict": "SUPPORTED",
            "notes": "Verified offline: road repair mandate recently transferred to department.",
        }
        res = self.client.post("/api/admin/verification/feedback", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["feedback_type"], "FALSE_CONTRADICTION")
        self.assertEqual(data["notes"], payload["notes"])
        self.assertIsNotNone(data["id"])

    def test_10_feedback_invalid_response_404(self):
        """POST feedback with non-existent response_id returns 404."""
        payload = {
            "response_id": 9999,
            "feedback_type": "GENERAL",
            "notes": "Invalid interaction ID test",
        }
        res = self.client.post("/api/admin/verification/feedback", json=payload)
        self.assertEqual(res.status_code, 404)

    def test_11_interaction_not_found_404(self):
        """GET /api/admin/verification/interactions/9999 returns 404."""
        res = self.client.get("/api/admin/verification/interactions/9999")
        self.assertEqual(res.status_code, 404)

    def test_12_rbac_citizen_forbidden(self):
        """Citizen user accessing /admin/verification receives 403 Forbidden."""
        app.dependency_overrides[get_current_user] = lambda: self.citizen_user
        try:
            res = self.client.get("/api/admin/verification/overview")
            self.assertEqual(res.status_code, 403)
            self.assertIn("Access denied", res.json()["detail"])
        finally:
            app.dependency_overrides[get_current_user] = lambda: self.admin_user


if __name__ == "__main__":
    unittest.main()
