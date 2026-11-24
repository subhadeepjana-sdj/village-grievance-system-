"""
Feature 7 — Evidence Provenance & Citation System Tests
========================================================

Covers:
  1. Citation schema construction & validation
  2. Citation generator — complaint records & knowledge-base chunks
  3. Citation validator — existence, field-match, staleness, fabrication
  4. Annotated answer generation with inline markers
  5. API schema (CitationOut) serialization
  6. Pipeline integration smoke test
"""

import os
import sys
import unittest

# ── path fixup ─────────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.verification.citation.schemas import (
    Citation,
    CitationReport,
    CitationStatus,
    SourceReference,
    SourceType,
)
from app.verification.citation.citation_generator import citation_generator
from app.verification.citation.citation_validator import citation_validator
from app.verification.schemas import (
    AtomicClaim,
    ClaimType,
    ClaimVerificationResult,
    VerificationMode,
    VerificationReport,
    VerificationStatus,
)
from app.schemas.ai import CitationOut


# ================================================================== #
#  Helpers                                                             #
# ================================================================== #

def _make_claim(
    claim_id: str = "C1",
    text: str = "Status is Under Review",
    claim_type: ClaimType = ClaimType.STATUS,
    entities: dict = None,
) -> AtomicClaim:
    return AtomicClaim(
        claim_id=claim_id,
        claim_text=text,
        claim_type=claim_type,
        extracted_entities=entities or {},
    )


def _make_cvr(
    claim: AtomicClaim = None,
    status: VerificationStatus = VerificationStatus.SUPPORTED,
    matched_evidence_id: str = "DB_GRV-2026-001024",
    matched_evidence_text: str = "Under Review",
    confidence: float = 0.92,
) -> ClaimVerificationResult:
    return ClaimVerificationResult(
        claim=claim or _make_claim(),
        status=status,
        confidence=confidence,
        verification_mode=VerificationMode.DETERMINISTIC_DB,
        matched_evidence_id=matched_evidence_id,
        matched_evidence_text=matched_evidence_text,
        reason="Exact field match against complaint record.",
    )


def _make_report(
    claims: list = None, answer: str = "The complaint is Under Review."
) -> VerificationReport:
    claims = claims or [_make_cvr()]
    return VerificationReport(
        verification_id="VR-TEST-001",
        original_answer=answer,
        overall_status=VerificationStatus.SUPPORTED,
        action_taken="SHOW",
        overall_confidence=92.0,
        claims=claims,
        total_claims=len(claims),
        supported_claims=len(claims),
    )


def _complaint_evidence() -> list:
    """Evidence pool entry from a complaint record."""
    return [
        {
            "source_id": "DB_GRV-2026-001024",
            "source_type": "COMPLAINT_RECORD",
            "evidence_text": "Complaint GRV-2026-001024 | Status: Under Review | Department: Water",
            "similarity_score": 1.0,
            "document_id": None,
            "chunk_id": None,
        }
    ]


def _kb_evidence() -> list:
    """Evidence pool entry from a knowledge-base document chunk."""
    return [
        {
            "source_id": "QDRANT_DOC_5_CHUNK_2",
            "source_type": "KNOWLEDGE_BASE",
            "evidence_text": "Under the Jal Jeevan Mission, all rural households must receive tap water by 2024.",
            "similarity_score": 0.87,
            "document_id": 5,
            "chunk_id": "doc5_chunk2",
        }
    ]


# ================================================================== #
#  Test: Citation Schemas                                              #
# ================================================================== #

class TestCitationSchemas(unittest.TestCase):
    """Verify Pydantic schema construction, defaults, and serialization."""

    def test_source_reference_construction(self):
        ref = SourceReference(
            source_type=SourceType.COMPLAINT_RECORD,
            source_id="GRV-2026-001024",
            source_field="status",
            source_value="Under Review",
        )
        self.assertEqual(ref.source_type, SourceType.COMPLAINT_RECORD)
        self.assertEqual(ref.source_id, "GRV-2026-001024")
        self.assertIsNone(ref.document_id)

    def test_citation_defaults(self):
        cit = Citation(
            citation_id="[1]",
            claim_text="Status is Under Review",
            source=SourceReference(
                source_type=SourceType.COMPLAINT_RECORD,
                source_id="GRV-2026-001024",
            ),
        )
        self.assertEqual(cit.status, CitationStatus.UNVERIFIED)
        self.assertEqual(cit.relevance_score, 0.0)
        self.assertIsNotNone(cit.created_at)

    def test_citation_report_aggregation(self):
        report = CitationReport(response_id=1, total_citations=0)
        self.assertEqual(report.verified_citations, 0)
        self.assertEqual(report.citations, [])


# ================================================================== #
#  Test: Citation Generator                                            #
# ================================================================== #

class TestCitationGenerator(unittest.TestCase):
    """Generator produces citations from verified claim–evidence pairs."""

    def test_complaint_record_citation(self):
        """Citation from a complaint-record evidence source."""
        report = _make_report()
        ev_pool = _complaint_evidence()
        result = citation_generator.generate(report, ev_pool, response_id=42)

        self.assertEqual(result.response_id, 42)
        self.assertEqual(result.total_citations, 1)
        cit = result.citations[0]
        self.assertEqual(cit.citation_id, "[1]")
        self.assertEqual(cit.source.source_type, SourceType.COMPLAINT_RECORD)
        self.assertEqual(cit.source.source_id, "DB_GRV-2026-001024")
        self.assertEqual(cit.relevance_score, 1.0)

    def test_knowledge_base_citation(self):
        """Citation from a knowledge-base chunk."""
        claim = _make_claim(
            text="Tap water must be provided to all rural households.",
            claim_type=ClaimType.POLICY_RULE,
        )
        cvr = _make_cvr(
            claim=claim,
            matched_evidence_id="QDRANT_DOC_5_CHUNK_2",
            matched_evidence_text="Under the Jal Jeevan Mission...",
        )
        report = _make_report(claims=[cvr])
        result = citation_generator.generate(report, _kb_evidence())

        self.assertEqual(result.total_citations, 1)
        cit = result.citations[0]
        self.assertEqual(cit.source.source_type, SourceType.KNOWLEDGE_BASE)
        self.assertEqual(cit.source.document_id, 5)
        self.assertEqual(cit.source.chunk_id, "doc5_chunk2")

    def test_no_matched_evidence_id_skips_citation(self):
        """Claims without a matched_evidence_id produce no citation."""
        cvr = _make_cvr(matched_evidence_id=None)
        report = _make_report(claims=[cvr])
        result = citation_generator.generate(report, _complaint_evidence())
        self.assertEqual(result.total_citations, 0)

    def test_multiple_claims_multiple_citations(self):
        """Each claim gets its own numbered citation."""
        cvr1 = _make_cvr(claim=_make_claim("C1", "Status is Under Review"))
        cvr2 = _make_cvr(
            claim=_make_claim("C2", "Department is Water", ClaimType.DEPARTMENT_ASSIGNMENT),
            matched_evidence_id="DB_GRV-2026-001024",
        )
        report = _make_report(claims=[cvr1, cvr2])
        result = citation_generator.generate(report, _complaint_evidence())
        self.assertEqual(result.total_citations, 2)
        self.assertEqual(result.citations[0].citation_id, "[1]")
        self.assertEqual(result.citations[1].citation_id, "[2]")

    def test_annotated_answer_contains_markers(self):
        """The annotated answer includes [1] markers."""
        report = _make_report()
        result = citation_generator.generate(report, _complaint_evidence())
        self.assertIn("[1]", result.annotated_answer)

    def test_source_field_mapping(self):
        """ClaimType.STATUS maps to source_field='status'."""
        report = _make_report()
        result = citation_generator.generate(report, _complaint_evidence())
        self.assertEqual(result.citations[0].source.source_field, "status")

    def test_entity_extraction_for_source_value(self):
        """Extracted entities take priority for source_value."""
        claim = _make_claim(entities={"status": "Under Review"})
        cvr = _make_cvr(claim=claim, matched_evidence_text="Under Review")
        report = _make_report(claims=[cvr])
        result = citation_generator.generate(report, _complaint_evidence())
        self.assertEqual(result.citations[0].source.source_value, "Under Review")


# ================================================================== #
#  Test: Citation Validator                                            #
# ================================================================== #

class TestCitationValidator(unittest.TestCase):
    """
    Validator cross-checks citations against the live database.

    Uses an in-memory SQLite database with seeded complaint data.
    """

    @classmethod
    def setUpClass(cls):
        """Create an in-memory SQLite DB with a test complaint."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.database.session import Base
        # Import all models so they're registered with Base.metadata
        import app.models  # noqa: F401

        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)
        cls.db = cls.Session()

        # Seed prerequisite data
        from app.models.village import Village
        from app.models.department import Department
        from app.models.user import User, UserRole
        from app.models.complaint import Complaint, ComplaintStatus

        village = Village(id=1, name="Test Village", district="District", state="State", pincode="700001")
        dept = Department(id=1, name="Water", description="Water dept")
        user = User(id=1, name="Test", email="t@t.com", password_hash="x", role=UserRole.CITIZEN)
        complaint = Complaint(
            id=1,
            complaint_number="GRV-2026-001024",
            user_id=1,
            village_id=1,
            department_id=1,
            category="Water Supply",
            title="Water pipe broken",
            description="No water supply",
            status=ComplaintStatus.UNDER_REVIEW,
        )
        cls.db.add_all([village, dept, user, complaint])
        cls.db.commit()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def _build_complaint_citation(self, source_value="Under Review"):
        return Citation(
            citation_id="[1]",
            claim_text="Status is Under Review",
            source=SourceReference(
                source_type=SourceType.COMPLAINT_RECORD,
                source_id="DB_GRV-2026-001024",
                source_field="status",
                source_value=source_value,
            ),
            evidence_text="Complaint GRV-2026-001024 | Status: Under Review",
        )

    def test_valid_complaint_citation_verified(self):
        """Existing complaint with matching field value → VERIFIED."""
        cit = self._build_complaint_citation()
        report = CitationReport(response_id=1, citations=[cit], total_citations=1)
        result = citation_validator.validate(report, self.db)
        self.assertEqual(result.citations[0].status, CitationStatus.VERIFIED)
        self.assertEqual(result.verified_citations, 1)

    def test_mismatched_field_value_stale(self):
        """Cited value doesn't match current DB → STALE."""
        cit = self._build_complaint_citation(source_value="Resolved")
        report = CitationReport(response_id=1, citations=[cit], total_citations=1)
        result = citation_validator.validate(report, self.db)
        self.assertEqual(result.citations[0].status, CitationStatus.STALE)
        self.assertEqual(result.stale_citations, 1)

    def test_fabricated_complaint_invalid(self):
        """Citing a complaint that doesn't exist → INVALID."""
        cit = Citation(
            citation_id="[1]",
            claim_text="Some claim",
            source=SourceReference(
                source_type=SourceType.COMPLAINT_RECORD,
                source_id="DB_GRV-9999-999999",
            ),
        )
        report = CitationReport(response_id=1, citations=[cit], total_citations=1)
        result = citation_validator.validate(report, self.db)
        self.assertEqual(result.citations[0].status, CitationStatus.INVALID)
        self.assertIn("not found", result.citations[0].validation_message)

    def test_kb_citation_with_chunk_id_verified(self):
        """Knowledge-base citation with chunk_id → VERIFIED (deferred)."""
        cit = Citation(
            citation_id="[1]",
            claim_text="Policy claim",
            source=SourceReference(
                source_type=SourceType.KNOWLEDGE_BASE,
                source_id="QDRANT_DOC_5_CHUNK_2",
                chunk_id="doc5_chunk2",
            ),
        )
        report = CitationReport(response_id=1, citations=[cit], total_citations=1)
        result = citation_validator.validate(report, self.db)
        self.assertEqual(result.citations[0].status, CitationStatus.VERIFIED)

    def test_kb_citation_no_ids_invalid(self):
        """Knowledge-base citation with no document_id or chunk_id → INVALID."""
        cit = Citation(
            citation_id="[1]",
            claim_text="Unknown doc",
            source=SourceReference(
                source_type=SourceType.KNOWLEDGE_BASE,
                source_id="UNKNOWN",
            ),
        )
        report = CitationReport(response_id=1, citations=[cit], total_citations=1)
        result = citation_validator.validate(report, self.db)
        self.assertEqual(result.citations[0].status, CitationStatus.INVALID)

    def test_complaint_exists_no_field_check(self):
        """Citation with no source_field → still VERIFIED if complaint exists."""
        cit = Citation(
            citation_id="[1]",
            claim_text="Some claim about complaint",
            source=SourceReference(
                source_type=SourceType.COMPLAINT_RECORD,
                source_id="DB_GRV-2026-001024",
            ),
        )
        report = CitationReport(response_id=1, citations=[cit], total_citations=1)
        result = citation_validator.validate(report, self.db)
        self.assertEqual(result.citations[0].status, CitationStatus.VERIFIED)


# ================================================================== #
#  Test: API Schema Serialization                                      #
# ================================================================== #

class TestCitationAPISchema(unittest.TestCase):
    """Ensure CitationOut Pydantic model serializes correctly."""

    def test_citation_out_construction(self):
        cit = CitationOut(
            citation_id="[1]",
            claim_text="Status is Under Review",
            source_type="COMPLAINT_RECORD",
            source_id="GRV-2026-001024",
            source_field="status",
            source_value="Under Review",
            relevance_score=0.95,
            status="VERIFIED",
            validation_message="Field match confirmed.",
        )
        data = cit.model_dump()
        self.assertEqual(data["citation_id"], "[1]")
        self.assertEqual(data["status"], "VERIFIED")
        self.assertIsNone(data["document_id"])

    def test_citation_out_defaults(self):
        cit = CitationOut(
            citation_id="[2]",
            claim_text="Some claim",
            source_type="KNOWLEDGE_BASE",
            source_id="DOC_1",
        )
        self.assertEqual(cit.status, "UNVERIFIED")
        self.assertEqual(cit.relevance_score, 0.0)


if __name__ == "__main__":
    unittest.main()
