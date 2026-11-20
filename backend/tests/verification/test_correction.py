import os
import sys
import unittest

# Ensure app is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.database.session import SessionLocal, engine, Base
from app.database.seed_data import seed_database
from app.models.ai_records import AIQuery, AIResponse, AICorrectionLog
from app.verification.schemas import (
    AtomicClaim,
    ClaimType,
    VerificationStatus,
    VerificationMode,
    ClaimVerificationResult,
    VerificationReport,
)
from app.verification.correction.prompt_builder import correction_prompt_builder
from app.verification.correction.correction_controller import correction_controller
from app.verification.correction.audit_logger import audit_logger


class TestCorrectionEngine(unittest.TestCase):
    """Unit tests for Answer Correction & Regeneration Engine (Feature 5)."""

    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        seed_database()
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    # ------------------------------------------------------------------ #
    # 1. Prompt Builder Tests                                            #
    # ------------------------------------------------------------------ #
    def test_prompt_builder_includes_negative_constraints(self):
        question = "Who is handling my complaint GRV-2026-001024?"
        bad_answer = "Your complaint is handled by Public Works Department and will be done in 3 days."
        
        claims = [
            ClaimVerificationResult(
                claim=AtomicClaim(claim_id="C1", claim_text="Handled by Public Works Department", claim_type=ClaimType.DEPARTMENT_ASSIGNMENT),
                status=VerificationStatus.CONTRADICTED,
                confidence=0.95,
                verification_mode=VerificationMode.DETERMINISTIC_DB,
                reason="Department mismatch: Database record states 'Village Water Department'.",
                matched_evidence_text="COMPLAINT RECORD GRV-2026-001024: Department: Village Water Department. Status: Under Review."
            ),
            ClaimVerificationResult(
                claim=AtomicClaim(claim_id="C2", claim_text="Will be done in 3 days", claim_type=ClaimType.RESOLUTION_TIMELINE),
                status=VerificationStatus.INSUFFICIENT_EVIDENCE,
                confidence=0.0,
                verification_mode=VerificationMode.FALLBACK,
                reason="No confirmed resolution date found."
            )
        ]

        report = VerificationReport(
            verification_id="VER-TEST-1",
            original_answer=bad_answer,
            overall_status=VerificationStatus.CONTRADICTED,
            action_taken="CORRECT",
            overall_confidence=30.0,
            claims=claims,
            total_claims=2,
            supported_claims=0,
            contradicted_claims=1,
            insufficient_claims=1
        )

        evidence = [
            {
                "source_type": "COMPLAINT_RECORD",
                "chunk_id": "DB_1024",
                "evidence_text": "COMPLAINT RECORD GRV-2026-001024: Department: Village Water Department. Status: Under Review."
            }
        ]

        prompt = correction_prompt_builder.build_correction_prompt(
            question=question,
            candidate_answer=bad_answer,
            report=report,
            evidence_pool=evidence,
            attempt=1
        )

        self.assertIn("REFUTED CLAIM", prompt)
        self.assertIn("Handled by Public Works Department", prompt)
        self.assertIn("Village Water Department", prompt)
        self.assertIn("UNVERIFIED CLAIM", prompt)
        self.assertIn("Will be done in 3 days", prompt)
        self.assertIn("NEGATIVE CONSTRAINTS", prompt)
        self.assertIn("Do NOT repeat any of the refuted claims", prompt)
        self.assertIn("Do NOT invent, assume, or extrapolate resolution dates", prompt)

    def test_deterministic_fallback_generation(self):
        evidence = [
            {
                "source_type": "COMPLAINT_RECORD",
                "chunk_id": "DB_1024",
                "evidence_text": "COMPLAINT RECORD GRV-2026-001024: Department: Village Water Department. Status: Under Review."
            }
        ]
        fallback = correction_prompt_builder.build_deterministic_fallback(None, evidence)
        self.assertIn("Village Water Department", fallback)
        self.assertIn("GRV-2026-001024", fallback)

    # ------------------------------------------------------------------ #
    # 2. Correction Controller State Machine Tests                       #
    # ------------------------------------------------------------------ #
    def test_correct_answer_accepted_immediately(self):
        question = "What is the status of my complaint GRV-2026-001024?"
        good_answer = "Your complaint GRV-2026-001024 is currently Under Review by the Village Water Department."
        evidence = [
            {
                "source_type": "COMPLAINT_RECORD",
                "chunk_id": "DB_1024",
                "evidence_text": "COMPLAINT RECORD GRV-2026-001024: Department: Village Water Department. Status: Under Review."
            }
        ]

        res = correction_controller.process_and_correct(
            question=question,
            evidence_pool=evidence,
            initial_answer=good_answer,
            db=self.db
        )

        self.assertEqual(res["action_taken"], "SHOW")
        self.assertEqual(res["overall_status"], "SUPPORTED")
        self.assertEqual(res["retries_used"], 0)
        self.assertEqual(res["total_attempts"], 1)
        self.assertIn("Village Water Department", res["final_answer"])

    def test_wrong_department_corrected_in_loop(self):
        question = "Who is handling my complaint GRV-2026-001024?"
        bad_answer = "Your complaint GRV-2026-001024 is assigned to Public Works Department."
        evidence = [
            {
                "source_type": "COMPLAINT_RECORD",
                "chunk_id": "DB_1024",
                "evidence_text": "COMPLAINT RECORD GRV-2026-001024: Department: Village Water Department. Status: Under Review."
            }
        ]

        res = correction_controller.process_and_correct(
            question=question,
            evidence_pool=evidence,
            initial_answer=bad_answer,
            db=self.db
        )

        # Must be corrected using ground truth
        self.assertEqual(res["action_taken"], "SHOW")
        self.assertGreaterEqual(res["retries_used"], 1)
        self.assertIn("Village Water Department", res["final_answer"])
        self.assertNotIn("Public Works Department", res["final_answer"])

    def test_wrong_status_corrected_in_loop(self):
        question = "Has my complaint GRV-2026-001024 been resolved?"
        bad_answer = "Your complaint GRV-2026-001024 has already been Resolved."
        evidence = [
            {
                "source_type": "COMPLAINT_RECORD",
                "chunk_id": "DB_1024",
                "evidence_text": "COMPLAINT RECORD GRV-2026-001024: Department: Village Water Department. Status: Under Review."
            }
        ]

        res = correction_controller.process_and_correct(
            question=question,
            evidence_pool=evidence,
            initial_answer=bad_answer,
            db=self.db
        )

        self.assertEqual(res["action_taken"], "SHOW")
        self.assertGreaterEqual(res["retries_used"], 1)
        self.assertIn("Under Review", res["final_answer"])

    def test_no_relevant_evidence_abstains(self):
        question = "Will there be a submarine base built in Chandanpur?"
        bad_answer = "Yes, a submarine base will open in Chandanpur by 2027."
        evidence = []  # No evidence

        res = correction_controller.process_and_correct(
            question=question,
            evidence_pool=evidence,
            initial_answer=bad_answer,
            db=self.db
        )

        self.assertEqual(res["action_taken"], "ABSTAIN")
        self.assertEqual(res["overall_status"], "INSUFFICIENT_EVIDENCE")
        self.assertIn("could not find sufficient verified information", res["final_answer"])

    # ------------------------------------------------------------------ #
    # 3. Audit Logging Persistence Test                                  #
    # ------------------------------------------------------------------ #
    def test_audit_logger_persists_history(self):
        # Create a mock AIQuery and AIResponse
        query = AIQuery(question="Test question for audit logging", query_type="GENERAL")
        self.db.add(query)
        self.db.commit()
        self.db.refresh(query)

        response = AIResponse(
            query_id=query.id,
            answer="Final verified answer",
            decision="SHOW",
            confidence=92.0,
            processing_time=0.45,
            configuration="rag_verification"
        )
        self.db.add(response)
        self.db.commit()
        self.db.refresh(response)

        history = [
            {
                "attempt": 1,
                "candidate_answer": "Initial draft answer with error",
                "status": "CONTRADICTED",
                "action": "CORRECT",
                "confidence": 35.0,
                "prompt_directive": "Refuted: department mismatch."
            },
            {
                "attempt": 2,
                "candidate_answer": "Final verified answer",
                "status": "SUPPORTED",
                "action": "SHOW",
                "confidence": 92.0,
                "prompt_directive": "Verified: Water department."
            }
        ]

        persisted = audit_logger.persist_correction_history(self.db, response.id, history)
        self.assertEqual(len(persisted), 2)

        # Query back from DB
        db_logs = self.db.query(AICorrectionLog).filter(AICorrectionLog.response_id == response.id).all()
        self.assertEqual(len(db_logs), 2)
        self.assertEqual(db_logs[0].status, "CONTRADICTED")
        self.assertEqual(db_logs[1].status, "SUPPORTED")
        self.assertEqual(db_logs[0].action, "CORRECT")
        self.assertEqual(db_logs[1].action, "SHOW")


if __name__ == "__main__":
    unittest.main()
