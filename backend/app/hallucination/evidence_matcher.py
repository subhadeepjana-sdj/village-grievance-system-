from typing import List, Dict, Any

class EvidenceMatcher:
    def find_best_matching_evidence(self, claim: str, evidence_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Matches a claim against all evidence chunks based on keyword overlap & semantic relevance."""
        claim_words = set(claim.lower().split())
        best_match = None
        best_score = 0.0

        for item in evidence_list:
            text = item.get("evidence_text", "").lower()
            text_words = set(text.split())
            if not text_words:
                continue
            
            overlap = len(claim_words.intersection(text_words)) / max(len(claim_words), 1)
            
            # Boost score for exact entity matches (e.g. Department names, complaint IDs)
            if any(num in text for num in self._extract_numbers(claim)):
                overlap += 0.4

            if overlap > best_score:
                best_score = overlap
                best_match = item

        return {
            "evidence_item": best_match,
            "match_score": round(min(best_score, 1.0), 4)
        }

    def _extract_numbers(self, text: str) -> List[str]:
        import re
        return re.findall(r'\b\d+\b', text)

evidence_matcher = EvidenceMatcher()
