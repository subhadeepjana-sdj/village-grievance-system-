import re
from typing import Dict, Any

class ContradictionDetector:
    DEPARTMENTS = [
        "Village Water Department", "Water Department", 
        "Roads & Infrastructure", "Road Department",
        "Sanitation & Waste Management", "Sanitation Department",
        "Electricity & Power", "Electricity Department",
        "Public Health & Schemes", "Health Department"
    ]

    STATUSES = [
        "SUBMITTED", "ACKNOWLEDGED", "ASSIGNED", 
        "UNDER_REVIEW", "IN_PROGRESS", "RESOLVED", "REJECTED", "CLOSED",
        "Under Review", "In Progress", "Resolved", "Submitted", "Assigned"
    ]

    def verify_claim(self, claim: str, evidence_text: str) -> Dict[str, Any]:
        """
        NLI Semantic Verification:
        Returns:
        {
          "result": "SUPPORTED" | "CONTRADICTED" | "INSUFFICIENT_EVIDENCE",
          "confidence": float (0.0 to 1.0),
          "reason": str
        }
        """
        if not evidence_text or not evidence_text.strip():
            return {
                "result": "INSUFFICIENT_EVIDENCE",
                "confidence": 0.0,
                "reason": "No evidence chunk available to verify this claim."
            }

        claim_lower = claim.lower()
        evidence_lower = evidence_text.lower()

        # 1. Contradiction Detection: Department Mismatch
        claim_dept = self._detect_department(claim)
        evidence_dept = self._detect_department(evidence_text)
        
        if claim_dept and evidence_dept and claim_dept != evidence_dept:
            return {
                "result": "CONTRADICTED",
                "confidence": 0.96,
                "reason": f"Contradiction: Claim asserts department '{claim_dept}', but verified evidence states '{evidence_dept}'."
            }

        # 2. Contradiction Detection: Status Mismatch
        claim_status = self._detect_status(claim)
        evidence_status = self._detect_status(evidence_text)
        
        if claim_status and evidence_status and claim_status.upper() != evidence_status.upper():
            return {
                "result": "CONTRADICTED",
                "confidence": 0.94,
                "reason": f"Contradiction: Claim asserts status '{claim_status}', but verified evidence states '{evidence_status}'."
            }

        # 3. Entailment / Support Check
        claim_words = set(re.findall(r'\w+', claim_lower))
        evidence_words = set(re.findall(r'\w+', evidence_lower))
        
        # Filter out common stop words
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "by", "for", "to", "in", "of", "and", "or", "your", "complaint", "currently"}
        meaningful_claim_words = claim_words - stop_words
        
        if not meaningful_claim_words:
            return {"result": "SUPPORTED", "confidence": 0.8, "reason": "Basic textual support."}

        overlap_ratio = len(meaningful_claim_words.intersection(evidence_words)) / len(meaningful_claim_words)

        if overlap_ratio >= 0.5:
            return {
                "result": "SUPPORTED",
                "confidence": round(0.70 + (overlap_ratio * 0.28), 2),
                "reason": f"High factual entailment ({int(overlap_ratio*100)}% keyword grounding)."
            }
        elif overlap_ratio >= 0.25:
            return {
                "result": "SUPPORTED",
                "confidence": 0.65,
                "reason": "Partial entailment grounding."
            }
        else:
            return {
                "result": "INSUFFICIENT_EVIDENCE",
                "confidence": 0.40,
                "reason": "Insufficient factual grounding in verified evidence."
            }

    def _detect_department(self, text: str) -> str:
        text_lower = text.lower()
        if "water" in text_lower:
            return "Water Department"
        if "road" in text_lower or "infrastructure" in text_lower:
            return "Roads Department"
        if "sanitation" in text_lower or "waste" in text_lower:
            return "Sanitation Department"
        if "electricity" in text_lower or "power" in text_lower:
            return "Electricity Department"
        if "health" in text_lower or "scheme" in text_lower:
            return "Health & Schemes"
        return ""

    def _detect_status(self, text: str) -> str:
        for status in self.STATUSES:
            if status.lower() in text.lower():
                return status
        return ""

contradiction_detector = ContradictionDetector()
