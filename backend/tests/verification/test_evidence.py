import os
import sys
import unittest

# Ensure app is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.database.session import SessionLocal, engine, Base
from app.database.seed_data import seed_database
from app.verification.schemas import (
    AtomicClaim,
    EvidenceItem,
    ClaimType,
    VerificationStatus,
    VerificationMode,
)
from app.verification.evidence.db_verifier import db_verifier
from app.verification.evidence.evidence_mapper import evidence_mapper


class TestEvidenceVerification(unittest.TestCase):
    """Unit tests for Deterministic Database Verification and Evidence Mapping."""

    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        seed_database()
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    # ------------------------------------------------------------------ #
    # 1. Deterministic Database Verifier Tests                           #
    # ------------------------------------------------------------------ #
    def test_db_verifier_supported_identity(self):
        claim = AtomicClaim(
            claim_id="C1",
            claim_text="Complaint number is GRV-2026-001024",
            claim_type=ClaimType.COMPLAINT_IDENTITY,
            extracted_entities={"complaint_number": "GRV-2026-001024"}
        )
        self.assertTrue(db_verifier.can_verify(claim))
        res = db_verifier.verify_claim(claim, self.db)
        self.assertIsNotNone(res)
        self.assertEqual(res.status, VerificationStatus.SUPPORTED)
        self.assertEqual(res.confidence, 1.0)
        self.assertEqual(res.verification_mode, VerificationMode.DETERMINISTIC_DB)

    def test_db_verifier_supported_department(self):
        claim = AtomicClaim(
            claim_id="C2",
            claim_text="Complaint GRV-2026-001024 is assigned to Village Water Department",
            claim_type=ClaimType.DEPARTMENT_ASSIGNMENT,
            extracted_entities={
                "complaint_number": "GRV-2026-001024",
                "department": "Village Water Department"
            }
        )
        res = db_verifier.verify_claim(claim, self.db)
        self.assertIsNotNone(res)
        self.assertEqual(res.status, VerificationStatus.SUPPORTED)
        self.assertEqual(res.confidence, 1.0)
        self.assertIn("correctly handled", res.reason.lower())

    def test_db_verifier_contradicted_department(self):
        claim = AtomicClaim(
            claim_id="C3",
            claim_text="Complaint GRV-2026-001024 is assigned to Public Works Department",
            claim_type=ClaimType.DEPARTMENT_ASSIGNMENT,
            extracted_entities={
                "complaint_number": "GRV-2026-001024",
                "department": "Public Works Department"
            }
        )
        res = db_verifier.verify_claim(claim, self.db)
        self.assertIsNotNone(res)
        self.assertEqual(res.status, VerificationStatus.CONTRADICTED)
        self.assertEqual(res.confidence, 1.0)
        self.assertIn("contradiction", res.reason.lower())
        self.assertIn("village water department", res.reason.lower())

    def test_db_verifier_contradicted_nonexistent_complaint(self):
        claim = AtomicClaim(
            claim_id="C4",
            claim_text="Complaint GRV-9999-000000 has been resolved",
            claim_type=ClaimType.STATUS,
            extracted_entities={"complaint_number": "GRV-9999-000000", "status": "RESOLVED"}
        )
        res = db_verifier.verify_claim(claim, self.db)
        self.assertIsNotNone(res)
        self.assertEqual(res.status, VerificationStatus.CONTRADICTED)
        self.assertEqual(res.confidence, 1.0)
        self.assertIn("does not exist", res.reason.lower())

    def test_db_verifier_insufficient_timeline(self):
        claim = AtomicClaim(
            claim_id="C5",
            claim_text="Complaint GRV-2026-001024 will be resolved within 3 days",
            claim_type=ClaimType.RESOLUTION_TIMELINE,
            extracted_entities={
                "complaint_number": "GRV-2026-001024",
                "timeline_value": 3,
                "timeline_unit": "days"
            }
        )
        res = db_verifier.verify_claim(claim, self.db)
        self.assertIsNotNone(res)
        self.assertEqual(res.status, VerificationStatus.INSUFFICIENT_EVIDENCE)
        self.assertIn("no confirmed sla", res.reason.lower())

    # ------------------------------------------------------------------ #
    # 2. Evidence Mapper Tests                                           #
    # ------------------------------------------------------------------ #
    def test_evidence_mapper_aligns_best_chunk(self):
        claim = AtomicClaim(
            claim_id="C6",
            claim_text="Water connection fees for BPL card holders are completely waived.",
            claim_type=ClaimType.POLICY_RULE,
            extracted_entities={"department": "Village Water Department"}
        )

        evidence_pool = [
            {
                "chunk_id": "ROAD_SLA_01",
                "source_type": "KNOWLEDGE_BASE",
                "text": "Potholes and road repairs must be inspected within 7 days by PWD engineers.",
                "department": "Roads & Infrastructure"
            },
            {
                "chunk_id": "WATER_SUBSIDY_02",
                "source_type": "KNOWLEDGE_BASE",
                "text": "Under Gram Panchayat Water Rules 2026, connection fees for BPL families are 100% subsidized upon valid card submission.",
                "department": "Village Water Department"
            },
            {
                "chunk_id": "ELECTRIC_SLA_03",
                "source_type": "KNOWLEDGE_BASE",
                "text": "Power failure complaints must be resolved in 24 hours.",
                "department": "Electricity & Power"
            }
        ]

        match = evidence_mapper.find_best_evidence(claim, evidence_pool)
        self.assertIsNotNone(match.evidence_item)
        self.assertEqual(match.source_id, "WATER_SUBSIDY_02")
        self.assertGreater(match.match_score, 0.40)
        self.assertIn("100% subsidized", match.premise_text)

    def test_evidence_mapper_empty_pool(self):
        claim = AtomicClaim(
            claim_id="C7",
            claim_text="Arbitrary claim with no evidence.",
            claim_type=ClaimType.GENERAL_FACT
        )
        match = evidence_mapper.find_best_evidence(claim, [])
        self.assertIsNone(match.evidence_item)
        self.assertEqual(match.match_score, 0.0)


if __name__ == "__main__":
    unittest.main()
