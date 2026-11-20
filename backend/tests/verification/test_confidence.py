import os
import sys
import unittest

# Ensure app is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.database.session import SessionLocal, engine, Base
from app.database.seed_data import seed_database
from app.verification.schemas import (
    AtomicClaim,
    ClaimType,
    VerificationStatus,
    VerificationMode,
    ClaimVerificationResult,
)
from app.verification.engine.confidence_scorer import confidence_scorer
from app.verification.engine.decision_engine import decision_engine
from app.verification.engine.corrector import answer_corrector


class TestConfidenceAndDecisionEngine(unittest.TestCase):
    """Unit tests for Composite Confidence Scoring, Decision Routing, and Correction Loop."""

    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        seed_database()
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    # ------------------------------------------------------------------ #
    # 1. Confidence Scorer Tests                                         #
    # ------------------------------------------------------------------ #
    def test_claim_confidence_high_entailment(self):
        conf = confidence_scorer.calculate_claim_confidence(
            source_type="KNOWLEDGE_BASE",
            match_score=0.90,
            p_entailment=0.88,
            p_contradiction=0.02
        )
        self.assertGreaterEqual(conf, 0.70)
        self.assertLessEqual(conf, 1.0)

    def test_claim_confidence_high_contradiction_penalized(self):
        conf = confidence_scorer.calculate_claim_confidence(
            source_type="KNOWLEDGE_BASE",
            match_score=0.90,
            p_entailment=0.20,
            p_contradiction=0.75
        )
        # Margin: max(0, 0.20 - 2*0.75) = 0.0
        self.assertEqual(conf, 0.0)

    def test_overall_confidence_all_supported(self):
        claim_results = [
            ClaimVerificationResult(
                claim=AtomicClaim(claim_id="C1", claim_text="Fact 1", claim_type=ClaimType.GENERAL_FACT),
                status=VerificationStatus.SUPPORTED,
                confidence=0.92,
                verification_mode=VerificationMode.NLI_MODEL,
                reason="Supported"
            ),
            ClaimVerificationResult(
                claim=AtomicClaim(claim_id="C2", claim_text="Fact 2", claim_type=ClaimType.GENERAL_FACT),
                status=VerificationStatus.SUPPORTED,
                confidence=0.88,
                verification_mode=VerificationMode.NLI_MODEL,
                reason="Supported"
            )
        ]
        score = confidence_scorer.calculate_overall_confidence(claim_results)
        self.assertGreaterEqual(score, 85.0)

    def test_overall_confidence_contradiction_heavily_penalized(self):
        claim_results = [
            ClaimVerificationResult(
                claim=AtomicClaim(claim_id="C1", claim_text="Fact 1", claim_type=ClaimType.GENERAL_FACT),
                status=VerificationStatus.SUPPORTED,
                confidence=0.92,
                verification_mode=VerificationMode.NLI_MODEL,
                reason="Supported"
            ),
            ClaimVerificationResult(
                claim=AtomicClaim(claim_id="C2", claim_text="False fact", claim_type=ClaimType.GENERAL_FACT),
                status=VerificationStatus.CONTRADICTED,
                confidence=0.95,
                verification_mode=VerificationMode.NLI_MODEL,
                reason="Contradicted"
            )
        ]
        score = confidence_scorer.calculate_overall_confidence(claim_results)
        self.assertLessEqual(score, 35.0)

    # ------------------------------------------------------------------ #
    # 2. Decision Engine End-to-End Tests                                #
    # ------------------------------------------------------------------ #
    def test_decision_engine_supported_answer(self):
        answer = "Your complaint GRV-2026-001024 is currently Under Review by the Village Water Department."
        evidence = [
            {
                "source_type": "COMPLAINT_RECORD",
                "chunk_id": "DB_1024",
                "evidence_text": "COMPLAINT RECORD GRV-2026-001024: Department: Village Water Department. Status: Under Review."
            }
        ]
        report = decision_engine.verify_answer(answer, evidence, db=self.db)
        self.assertEqual(report.overall_status, VerificationStatus.SUPPORTED)
        self.assertEqual(report.action_taken, "SHOW")
        self.assertGreaterEqual(report.overall_confidence, 70.0)
        self.assertIsNone(report.correction_directive)

    def test_decision_engine_contradicted_answer(self):
        answer = "Your complaint GRV-2026-001024 is assigned to Public Works Department."
        evidence = [
            {
                "source_type": "COMPLAINT_RECORD",
                "chunk_id": "DB_1024",
                "evidence_text": "COMPLAINT RECORD GRV-2026-001024: Department: Village Water Department. Status: Under Review."
            }
        ]
        report = decision_engine.verify_answer(answer, evidence, db=self.db)
        self.assertEqual(report.overall_status, VerificationStatus.CONTRADICTED)
        self.assertEqual(report.action_taken, "CORRECT")
        self.assertIsNotNone(report.correction_directive)
        self.assertIn("refuted", report.correction_directive.lower())

    def test_decision_engine_unanswerable_abstention(self):
        answer = "A space rocket launch facility is scheduled for construction in Chandanpur."
        evidence = []  # No evidence
        report = decision_engine.verify_answer(answer, evidence, db=self.db)
        self.assertEqual(report.overall_status, VerificationStatus.INSUFFICIENT_EVIDENCE)
        self.assertEqual(report.action_taken, "ABSTAIN")

    # ------------------------------------------------------------------ #
    # 3. Answer Corrector Tests                                          #
    # ------------------------------------------------------------------ #
    def test_answer_corrector_deterministic_fallback(self):
        question = "Who is handling my complaint GRV-2026-001024?"
        bad_answer = "Your complaint GRV-2026-001024 is handled by Public Works Department."
        evidence = [
            {
                "source_type": "COMPLAINT_RECORD",
                "chunk_id": "DB_1024",
                "evidence_text": "COMPLAINT RECORD GRV-2026-001024: Department: Village Water Department. Status: Under Review."
            }
        ]
        initial_report = decision_engine.verify_answer(bad_answer, evidence, db=self.db)
        self.assertEqual(initial_report.action_taken, "CORRECT")

        # Run correction loop
        res = answer_corrector.correct_and_verify(
            question=question,
            initial_answer=bad_answer,
            initial_report=initial_report,
            evidence_pool=evidence,
            db=self.db
        )
        self.assertIsNotNone(res["final_answer"])
        self.assertIn("Village Water Department", res["final_answer"])


if __name__ == "__main__":
    unittest.main()
