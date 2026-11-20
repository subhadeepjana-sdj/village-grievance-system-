import os
import sys
import unittest

# Ensure app is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.verification.schemas import (
    ClaimType,
    VerificationStatus,
    VerificationMode,
    AtomicClaim,
    EvidenceItem,
    ClaimVerificationResult,
    VerificationReport,
)
from app.verification.extraction.sentence_splitter import sentence_splitter
from app.verification.extraction.claim_extractor import atomic_claim_extractor


class TestVerificationSchemas(unittest.TestCase):
    """Validates Pydantic data contracts for claim-level verification."""

    def test_atomic_claim_instantiation(self):
        claim = AtomicClaim(
            claim_id="C1",
            claim_text="The complaint GRV-2026-001024 is currently Under Review.",
            claim_type=ClaimType.STATUS,
            source_sentence="Your complaint GRV-2026-001024 is currently Under Review.",
            extracted_entities={"complaint_number": "GRV-2026-001024", "status": "UNDER_REVIEW"}
        )
        self.assertEqual(claim.claim_id, "C1")
        self.assertEqual(claim.claim_type, ClaimType.STATUS)
        self.assertEqual(claim.extracted_entities["complaint_number"], "GRV-2026-001024")

    def test_verification_report_structure(self):
        report = VerificationReport(
            verification_id="VER-001",
            original_answer="Complaint resolved.",
            overall_status=VerificationStatus.SUPPORTED,
            action_taken="SHOW",
            overall_confidence=92.5,
            total_claims=1,
            supported_claims=1,
            contradicted_claims=0,
            insufficient_claims=0,
            claims=[]
        )
        self.assertEqual(report.action_taken, "SHOW")
        self.assertEqual(report.overall_confidence, 92.5)


class TestSentenceSplitter(unittest.TestCase):
    """Tests sentence boundary detection with protected abbreviations and numerals."""

    def test_basic_sentence_splitting(self):
        text = "Water pipeline is leaking in North Ward. Please repair it soon. Sanitation staff was notified."
        sents = sentence_splitter.split_sentences(text)
        self.assertEqual(len(sents), 3)
        self.assertEqual(sents[0], "Water pipeline is leaking in North Ward.")

    def test_abbreviation_protection(self):
        text = "Shri. R. K. Sharma from Dept. of Water visited the site. The cost is Rs. 500.50 approx."
        sents = sentence_splitter.split_sentences(text)
        # Should not split inside "Shri.", "Dept.", or "Rs. 500.50"
        self.assertEqual(len(sents), 2)
        self.assertIn("Shri. R. K. Sharma", sents[0])
        self.assertIn("Rs. 500.50", sents[1])

    def test_bullet_list_splitting(self):
        text = "Requirements:\n1. Aadhaar Card\n2. Ration Card or BPL Certificate\n3. Proof of address"
        sents = sentence_splitter.split_sentences(text)
        self.assertGreaterEqual(len(sents), 3)


class TestAtomicClaimExtractor(unittest.TestCase):
    """Tests decomposition of complex responses into typed atomic propositions."""

    def test_compound_sentence_decomposition(self):
        answer = "Your complaint GRV-2026-001024 is assigned to the Village Water Department and will be resolved within 5 days."
        claims = atomic_claim_extractor.extract_atomic_claims(answer, use_llm=False)

        # Expect at least 2 atomic claims split across "and"
        self.assertGreaterEqual(len(claims), 2)

        # Check entity extraction
        c_types = [c.claim_type for c in claims]
        self.assertTrue(
            ClaimType.DEPARTMENT_ASSIGNMENT in c_types or ClaimType.COMPLAINT_IDENTITY in c_types
        )
        self.assertIn(ClaimType.RESOLUTION_TIMELINE, c_types)

        # Check extracted entities
        timeline_claims = [c for c in claims if c.claim_type == ClaimType.RESOLUTION_TIMELINE]
        self.assertEqual(len(timeline_claims), 1)
        self.assertEqual(timeline_claims[0].extracted_entities.get("timeline_value"), 5)

    def test_meta_sentence_filtering(self):
        answer = "Hello citizen! Thank you for reaching out. The BPL income limit is Rs. 100000 per year."
        claims = atomic_claim_extractor.extract_atomic_claims(answer, use_llm=False)

        # "Hello citizen!" and "Thank you for reaching out." should be filtered out
        self.assertEqual(len(claims), 1)
        self.assertIn("BPL income limit", claims[0].claim_text)
        self.assertEqual(claims[0].claim_type, ClaimType.POLICY_RULE)

    def test_entity_extraction_types(self):
        answer = "Complaint V1024 has status Under Review by Road Department."
        claims = atomic_claim_extractor.extract_atomic_claims(answer, use_llm=False)
        self.assertGreaterEqual(len(claims), 1)

        ent = claims[0].extracted_entities
        self.assertEqual(ent.get("complaint_number"), "V1024")
        self.assertIn(ent.get("department"), ["Road Department", "Roads Department"])
        self.assertEqual(ent.get("status"), "UNDER_REVIEW")


if __name__ == "__main__":
    unittest.main()
