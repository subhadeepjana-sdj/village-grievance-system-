import re
import logging
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel
from app.verification.schemas import AtomicClaim, EvidenceItem, ClaimType

logger = logging.getLogger("uvicorn.error")

class BestEvidenceMatch(BaseModel):
    """Result of mapping an atomic claim to the best supporting evidence chunk."""
    evidence_item: Optional[EvidenceItem] = None
    match_score: float = 0.0
    premise_text: str = ""
    source_id: Optional[str] = None


class EvidenceMapper:
    """
    Identifies and aligns the most relevant evidence passage (premise) for a given claim (hypothesis).
    Applies entity matching, source type routing, and lexical overlap scoring.
    """

    STOP_WORDS = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "in", "on", "at", "to", "for", "of", "with", "by", "from", "up", "about",
        "into", "over", "after", "your", "my", "our", "their", "his", "her",
        "and", "but", "or", "as", "if", "when", "than", "because", "while",
        "complaint", "village", "gram", "panchayat", "information", "regarding"
    }

    def find_best_evidence(
        self,
        claim: AtomicClaim,
        evidence_pool: List[Union[EvidenceItem, Dict[str, Any]]]
    ) -> BestEvidenceMatch:
        """
        Scans candidate evidence pieces and selects the top-scoring premise for NLI evaluation.
        """
        if not evidence_pool:
            return BestEvidenceMatch(
                evidence_item=None,
                match_score=0.0,
                premise_text="",
                source_id=None
            )

        # 1. Normalize items into EvidenceItem models
        normalized_items: List[EvidenceItem] = []
        for item in evidence_pool:
            if isinstance(item, EvidenceItem):
                normalized_items.append(item)
            elif isinstance(item, dict):
                normalized_items.append(
                    EvidenceItem(
                        source_id=str(item.get("chunk_id") or item.get("source_id") or f"chunk_{len(normalized_items)+1}"),
                        source_type=str(item.get("source_type") or "KNOWLEDGE_BASE"),
                        evidence_text=str(item.get("evidence_text") or item.get("text") or ""),
                        department=item.get("department") or item.get("metadata", {}).get("department"),
                        category=item.get("category") or item.get("metadata", {}).get("category"),
                        effective_date=item.get("effective_date") or item.get("metadata", {}).get("effective_date"),
                        status=item.get("status") or item.get("metadata", {}).get("status") or "verified"
                    )
                )

        # 2. Extract content words from hypothesis claim
        claim_words = self._extract_content_words(claim.claim_text)
        if not claim_words:
            claim_words = set(claim.claim_text.lower().split())

        best_item: Optional[EvidenceItem] = None
        best_score = 0.0

        for item in normalized_items:
            ev_text = item.evidence_text
            if not ev_text or not ev_text.strip():
                continue

            ev_words = self._extract_content_words(ev_text)
            if not ev_words:
                continue

            # Base lexical overlap (Jaccard similarity on content words)
            intersection = claim_words.intersection(ev_words)
            overlap_score = len(intersection) / max(len(claim_words), 1)

            # Boost 1: Exact complaint number match
            complaint_num = claim.extracted_entities.get("complaint_number")
            if complaint_num and complaint_num.lower() in ev_text.lower():
                overlap_score += 0.45

            # Boost 2: Department match
            dept_name = claim.extracted_entities.get("department")
            if dept_name and (dept_name.lower() in ev_text.lower() or (item.department and dept_name.lower() in item.department.lower())):
                overlap_score += 0.25

            # Boost 3: Source alignment
            if claim.claim_type in [ClaimType.POLICY_RULE, ClaimType.PROCEDURE_STEP] and item.source_type == "KNOWLEDGE_BASE":
                overlap_score += 0.15
            elif claim.claim_type in [ClaimType.COMPLAINT_IDENTITY, ClaimType.STATUS] and item.source_type == "COMPLAINT_RECORD":
                overlap_score += 0.30

            score = min(round(overlap_score, 4), 1.0)
            if score > best_score:
                best_score = score
                best_item = item

        if best_item and best_score >= 0.10:
            formatted_premise = self._format_premise(best_item)
            return BestEvidenceMatch(
                evidence_item=best_item,
                match_score=best_score,
                premise_text=formatted_premise,
                source_id=best_item.source_id
            )

        return BestEvidenceMatch(
            evidence_item=None,
            match_score=0.0,
            premise_text="",
            source_id=None
        )

    def _extract_content_words(self, text: str) -> set:
        raw_words = re.findall(r'\b[a-zA-Z0-9_\-]+\b', text.lower())
        return {w for w in raw_words if w not in self.STOP_WORDS and len(w) > 2}

    def _format_premise(self, item: EvidenceItem) -> str:
        """Adds contextual metadata header to the premise for NLI comprehension."""
        header_parts = []
        if item.source_type:
            header_parts.append(f"Type: {item.source_type}")
        if item.department:
            header_parts.append(f"Department: {item.department}")
        if item.effective_date:
            header_parts.append(f"Effective: {item.effective_date}")

        header = f"[{' | '.join(header_parts)}]\n" if header_parts else ""
        return f"{header}{item.evidence_text.strip()}"


evidence_mapper = EvidenceMapper()
