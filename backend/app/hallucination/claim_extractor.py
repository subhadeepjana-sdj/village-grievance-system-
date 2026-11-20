import re
from typing import List

class ClaimExtractor:
    def extract_claims(self, text: str, llm_claims: List[str] = None) -> List[str]:
        """
        Extracts atomic claims from a generated text answer.
        If llm_claims are passed and valid, uses them; otherwise splits sentences into atomic facts.
        """
        if llm_claims and isinstance(llm_claims, list) and len(llm_claims) > 0:
            cleaned = [c.strip() for c in llm_claims if c.strip()]
            if cleaned:
                return cleaned

        # Fallback sentence-based claim extractor
        sentences = re.split(r'(?<=[.!?])\s+', text)
        claims = []
        for s in sentences:
            s_clean = s.strip()
            if len(s_clean) > 10 and not s_clean.startswith("Note:") and not s_clean.startswith("Based on"):
                claims.append(s_clean)

        return claims if claims else [text.strip()]

claim_extractor = ClaimExtractor()
