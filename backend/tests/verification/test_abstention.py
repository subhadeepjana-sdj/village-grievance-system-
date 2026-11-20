import os
import sys
import unittest

# Ensure app is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.database.session import SessionLocal, engine, Base
from app.database.seed_data import seed_database
from app.models import Complaint, User, UserRole, AIQuery, AIResponse, AIAbstentionLog
from app.verification.abstention.query_analyzer import query_analyzer, QueryIntent
from app.verification.abstention.sufficiency_checker import (
    sufficiency_checker,
    SufficiencyStatus,
    SufficiencyCheckResult
)
from app.verification.abstention.abstention_engine import abstention_engine
from app.verification.abstention.audit_logger import abstention_audit_logger


class TestAbstentionMechanism(unittest.TestCase):
    """Unit and Integration tests for Feature 6 — Abstention Mechanism."""

    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        seed_database()
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    # ------------------------------------------------------------------ #
    # 1. Query Analyzer Tests                                            #
    # ------------------------------------------------------------------ #
    def test_query_analyzer_intent_resolution_timeline(self):
        query = "When will my road repair complaint GRV-2026-001025 be resolved?"
        analysis = query_analyzer.analyze_query(query)
        self.assertEqual(analysis.intent, QueryIntent.RESOLUTION_TIMELINE)
        self.assertEqual(analysis.complaint_number, "GRV-2026-001025")
        self.assertIn("expected_resolution_date", analysis.required_fields)
        self.assertTrue(analysis.requires_complaint_record)

    def test_query_analyzer_intent_department_inquiry(self):
        query = "Who is handling my complaint GRV-2026-001024?"
        analysis = query_analyzer.analyze_query(query)
        self.assertEqual(analysis.intent, QueryIntent.DEPARTMENT_INQUIRY)
        self.assertEqual(analysis.complaint_number, "GRV-2026-001024")
        self.assertIn("department", analysis.required_fields)

    def test_query_analyzer_intent_status_check(self):
        query = "What is the status of complaint GRV-2026-001024?"
        analysis = query_analyzer.analyze_query(query)
        self.assertEqual(analysis.intent, QueryIntent.STATUS_CHECK)
        self.assertEqual(analysis.complaint_number, "GRV-2026-001024")
        self.assertIn("status", analysis.required_fields)

    # ------------------------------------------------------------------ #
    # 2. Evidence Sufficiency Checker Tests                              #
    # ------------------------------------------------------------------ #
    def test_sufficiency_checker_missing_resolution_date_halts(self):
        complaint = self.db.query(Complaint).filter(Complaint.complaint_number == "GRV-2026-001025").first()
        self.assertIsNotNone(complaint)
        self.assertIsNone(complaint.expected_resolution_date)

        res = sufficiency_checker.check_complaint_record_sufficiency(
            complaint=complaint,
            required_fields=["status", "expected_resolution_date"],
            complaint_number="GRV-2026-001025"
        )

        self.assertFalse(res.can_proceed_to_generation)
        self.assertTrue(res.pre_generation_halt)
        self.assertEqual(res.status, SufficiencyStatus.MISSING_MANDATORY_FIELD)
        self.assertIn("expected_resolution_date", res.missing_fields)
        self.assertIn("do not yet contain a confirmed resolution date", res.safe_refusal_message)

    def test_sufficiency_checker_non_existent_complaint_halts(self):
        res = sufficiency_checker.check_complaint_record_sufficiency(
            complaint=None,
            required_fields=["status"],
            complaint_number="GRV-9999-999999"
        )
        self.assertFalse(res.can_proceed_to_generation)
        self.assertTrue(res.pre_generation_halt)
        self.assertEqual(res.status, SufficiencyStatus.NON_EXISTENT_ENTITY)
        self.assertIn("was not found", res.safe_refusal_message)

    def test_sufficiency_checker_expired_evidence_halts(self):
        evidence_pool = [
            {
                "source_type": "KNOWLEDGE_BASE",
                "chunk_id": "EXP_01",
                "evidence_text": "Sanitation subsidy circular 2021",
                "status": "expired"
            }
        ]
        res = sufficiency_checker.check_knowledge_base_sufficiency(evidence_pool)
        self.assertFalse(res.can_proceed_to_generation)
        self.assertEqual(res.status, SufficiencyStatus.EXPIRED_EVIDENCE)
        self.assertIn("expired or superseded", res.safe_refusal_message)

    def test_sufficiency_checker_conflicting_sources_halts(self):
        evidence_pool = [
            {"evidence_text": "Drainage repairs are managed by the Village Water Department."},
            {"evidence_text": "Drainage systems are strictly under Roads & Infrastructure."},
            {"evidence_text": "Sanitation team is responsible for clearing all village drainage."}
        ]
        res = sufficiency_checker.detect_conflicts(evidence_pool)
        self.assertFalse(res.can_proceed_to_generation)
        self.assertEqual(res.status, SufficiencyStatus.CONFLICTING_EVIDENCE)
        self.assertIn("conflicting administrative instructions", res.safe_refusal_message)

    # ------------------------------------------------------------------ #
    # 3. Master Abstention Engine End-to-End Tests                       #
    # ------------------------------------------------------------------ #
    def test_abstention_engine_pre_generation_halt_on_missing_date(self):
        query = "When will my road repair complaint GRV-2026-001025 be resolved?"
        res = abstention_engine.process_and_decide(
            query=query,
            evidence_pool=[],
            db=self.db
        )

        self.assertEqual(res["decision"], "ABSTAIN")
        self.assertEqual(res["verification_status"], "INSUFFICIENT_EVIDENCE")
        self.assertTrue(res["is_abstained"])
        self.assertTrue(res["pre_generation_halt"])
        self.assertEqual(res["abstention_reason"], "MISSING_MANDATORY_FIELD")
        self.assertIn("do not yet contain a confirmed resolution date", res["final_answer"])
        self.assertLess(res["elapsed_ms"], 50.0)  # Very fast pre-generation bypass

    def test_abstention_engine_unauthorized_citizen_access_denied(self):
        # Create another citizen
        other_citizen = self.db.query(User).filter(User.email == "citizen@village.gov.in").first()
        complaint = self.db.query(Complaint).filter(Complaint.complaint_number == "GRV-2026-001024").first()
        
        # Fake malicious user with different user_id
        unauthorized_user = User(id=9999, email="other@village.gov.in", role=UserRole.CITIZEN)

        res = abstention_engine.process_and_decide(
            query="Tell me about complaint GRV-2026-001024",
            evidence_pool=[],
            db=self.db,
            current_user=unauthorized_user
        )

        self.assertEqual(res["decision"], "ABSTAIN")
        self.assertEqual(res["abstention_reason"], "UNAUTHORIZED_ACCESS")
        self.assertIn("not authorized", res["final_answer"])

    # ------------------------------------------------------------------ #
    # 4. Abstention Audit Logger Tests                                   #
    # ------------------------------------------------------------------ #
    def test_abstention_audit_logger_records_and_stats(self):
        entry = abstention_audit_logger.log_abstention_event(
            db=self.db,
            response_id=None,
            intent="RESOLUTION_TIMELINE",
            reason="MISSING_MANDATORY_FIELD",
            complaint_number="GRV-2026-001025",
            missing_fields=["expected_resolution_date"],
            pre_generation_halt=True
        )

        self.assertIsNotNone(entry)
        self.assertEqual(entry.complaint_number, "GRV-2026-001025")
        self.assertEqual(entry.abstention_reason, "MISSING_MANDATORY_FIELD")
        self.assertEqual(entry.pre_generation_halt, 1)

        stats = abstention_audit_logger.get_abstention_statistics(self.db)
        self.assertGreaterEqual(stats["total_abstentions"], 1)
        self.assertGreaterEqual(stats["pre_generation_halts"], 1)
        self.assertIn("MISSING_MANDATORY_FIELD", stats["reasons_breakdown"])


if __name__ == "__main__":
    unittest.main()
