"""
Feature 7 — Citation Generator
================================

Transforms verified claim–evidence pairs into structured ``Citation``
objects.  The generator never fabricates source IDs; it only creates
citations for evidence that was *actually retrieved* by the RAG
pipeline.

Workflow
--------
1. Receive a ``VerificationReport`` and the ``evidence_pool`` list.
2. For each ``ClaimVerificationResult`` in the report:
   a. Locate the matched evidence by ``matched_evidence_id``.
   b. Determine source type (complaint record vs. knowledge base).
   c. For complaint records, extract the specific field being cited
      (``status``, ``department``, etc.) from the claim type taxonomy.
   d. Build a ``Citation`` with full provenance metadata.
3. Return a ``CitationReport`` with inline annotation markers.
"""

import logging
import re
from typing import Dict, List, Optional

from app.verification.citation.schemas import (
    Citation,
    CitationReport,
    CitationStatus,
    SourceReference,
    SourceType,
)
from app.verification.schemas import (
    ClaimType,
    ClaimVerificationResult,
    VerificationReport,
    VerificationStatus,
)

logger = logging.getLogger("uvicorn.error")

# Mapping from ClaimType to the complaint-record field it references
_CLAIM_TYPE_TO_DB_FIELD: Dict[ClaimType, str] = {
    ClaimType.COMPLAINT_IDENTITY: "complaint_number",
    ClaimType.DEPARTMENT_ASSIGNMENT: "department",
    ClaimType.STATUS: "status",
    ClaimType.RESOLUTION_TIMELINE: "expected_resolution_date",
    ClaimType.OFFICIAL_PERSONNEL: "assigned_official",
    ClaimType.POLICY_RULE: "policy_reference",
    ClaimType.PROCEDURE_STEP: "procedure",
    ClaimType.GENERAL_FACT: "description",
}

# Regex to pull complaint numbers from evidence IDs like DB_GRV_1024
_COMPLAINT_ID_PATTERN = re.compile(
    r"DB_(?:GRV[_-]?\d{4}[_-]?\d{3,6}|\d+)",
    re.IGNORECASE,
)


class CitationGenerator:
    """
    Builds a ``CitationReport`` from verified claims and their matched
    evidence.

    The generator is a pure function (no DB access, no side effects).
    It maps each supported or insufficient claim to the evidence piece
    that was used during verification.  Contradicted claims are still
    cited so the user can see *what* contradicted them.
    """

    def generate(
        self,
        report: VerificationReport,
        evidence_pool: List[Dict],
        response_id: int = 0,
    ) -> CitationReport:
        """
        Parameters
        ----------
        report :        Output of the Decision Engine / Confidence Scorer.
        evidence_pool : Raw evidence dicts from hybrid retriever, each
                        containing ``source_id``, ``source_type``,
                        ``evidence_text``, ``similarity_score``, etc.
        response_id :   DB primary key of the AI response (for FK).

        Returns
        -------
        CitationReport with ordered citations and an annotated answer.
        """
        # Index evidence pool by source_id for O(1) lookup
        ev_index: Dict[str, Dict] = {}
        for ev in evidence_pool:
            sid = ev.get("source_id") or ev.get("chunk_id") or ""
            if sid:
                ev_index[sid] = ev

        citations: List[Citation] = []
        label_counter = 1

        for cvr in report.claims:
            citation = self._build_citation(cvr, ev_index, label_counter)
            if citation:
                citations.append(citation)
                label_counter += 1

        annotated = self._annotate_answer(report.original_answer, citations)

        return CitationReport(
            response_id=response_id,
            citations=citations,
            total_citations=len(citations),
            verified_citations=sum(
                1 for c in citations if c.status == CitationStatus.VERIFIED
            ),
            invalid_citations=sum(
                1 for c in citations if c.status == CitationStatus.INVALID
            ),
            stale_citations=sum(
                1 for c in citations if c.status == CitationStatus.STALE
            ),
            annotated_answer=annotated,
        )

    # ------------------------------------------------------------------ #
    #  Private helpers                                                     #
    # ------------------------------------------------------------------ #

    def _build_citation(
        self,
        cvr: ClaimVerificationResult,
        ev_index: Dict[str, Dict],
        label: int,
    ) -> Optional[Citation]:
        """Create a Citation from a single claim–evidence pair."""

        matched_id = cvr.matched_evidence_id
        if not matched_id:
            # No evidence was matched → no citation can be generated
            return None

        evidence = ev_index.get(matched_id, {})
        source_type_str = evidence.get("source_type", "KNOWLEDGE_BASE")

        try:
            source_type = SourceType(source_type_str)
        except ValueError:
            source_type = SourceType.KNOWLEDGE_BASE

        # Determine source reference fields
        source_field = _CLAIM_TYPE_TO_DB_FIELD.get(cvr.claim.claim_type)
        source_value = self._extract_source_value(cvr, evidence)

        source_ref = SourceReference(
            source_type=source_type,
            source_id=matched_id,
            document_id=evidence.get("document_id"),
            chunk_id=evidence.get("chunk_id"),
            source_field=source_field,
            source_value=source_value,
            page_number=evidence.get("page_number"),
        )

        return Citation(
            citation_id=f"[{label}]",
            claim_text=cvr.claim.claim_text,
            source=source_ref,
            relevance_score=min(
                float(evidence.get("similarity_score", 0.0)), 1.0
            ),
            evidence_text=evidence.get("evidence_text", ""),
            status=CitationStatus.UNVERIFIED,  # Validator sets final status
        )

    @staticmethod
    def _extract_source_value(
        cvr: ClaimVerificationResult, evidence: Dict
    ) -> Optional[str]:
        """
        Pull the authoritative field value from the evidence payload.

        For complaint records the hybrid retriever embeds structured
        fields (``status``, ``department``, etc.) inside the evidence
        text.  We fall back to matched_evidence_text from the CVR.
        """
        entities = cvr.claim.extracted_entities
        claim_type = cvr.claim.claim_type

        # Try extracted entities first (most precise)
        if claim_type == ClaimType.STATUS and "status" in entities:
            return str(entities["status"])
        if claim_type == ClaimType.DEPARTMENT_ASSIGNMENT and "department" in entities:
            return str(entities["department"])
        if claim_type == ClaimType.COMPLAINT_IDENTITY and "complaint_id" in entities:
            return str(entities["complaint_id"])

        # Fallback: use matched evidence text from the verifier
        return cvr.matched_evidence_text

    @staticmethod
    def _annotate_answer(answer: str, citations: List[Citation]) -> str:
        """
        Insert ``[1]``, ``[2]``, … markers into the original answer.

        Strategy: for each citation, find the sentence most related to
        the claim text and append the marker.  Uses simple substring
        matching to avoid heavyweight NLP at serving time.
        """
        if not citations:
            return answer

        sentences = re.split(r"(?<=[.!?])\s+", answer)
        used_labels: Dict[int, str] = {}

        for cit in citations:
            best_idx = 0
            best_overlap = 0.0
            claim_words = set(cit.claim_text.lower().split())

            for idx, sent in enumerate(sentences):
                sent_words = set(sent.lower().split())
                if not claim_words:
                    continue
                overlap = len(claim_words & sent_words) / len(claim_words)
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_idx = idx

            # Append citation label to the best-matching sentence
            if best_idx not in used_labels:
                used_labels[best_idx] = cit.citation_id
            else:
                used_labels[best_idx] += cit.citation_id

        # Rebuild the answer with markers
        annotated_parts = []
        for idx, sent in enumerate(sentences):
            if idx in used_labels:
                sent = sent.rstrip(".!?") + " " + used_labels[idx] + "."
            annotated_parts.append(sent)

        return " ".join(annotated_parts)


# Module-level singleton
citation_generator = CitationGenerator()
