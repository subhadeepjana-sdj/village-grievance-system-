from typing import List, Dict, Any
from app.hallucination.claim_extractor import claim_extractor
from app.hallucination.evidence_matcher import evidence_matcher
from app.hallucination.contradiction_detector import contradiction_detector
from app.hallucination.confidence import confidence_calculator

class HallucinationValidator:
    def validate_response(self, answer: str, raw_claims: List[str], evidence_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Full Hallucination Verification Pipeline:
        Answer -> Claim Extraction -> Evidence Matching -> NLI Verification -> Confidence Calculation -> Summary Verdict
        """
        extracted_claims = claim_extractor.extract_claims(answer, raw_claims)
        verification_records = []

        has_contradiction = False
        supported_count = 0
        insufficient_count = 0

        for claim in extracted_claims:
            match_res = evidence_matcher.find_best_matching_evidence(claim, evidence_list)
            best_ev_item = match_res.get("evidence_item")
            ev_text = best_ev_item.get("evidence_text", "") if best_ev_item else ""

            verdict = contradiction_detector.verify_claim(claim, ev_text)
            res_type = verdict.get("result", "INSUFFICIENT_EVIDENCE")

            if res_type == "CONTRADICTED":
                has_contradiction = True
            elif res_type == "SUPPORTED":
                supported_count += 1
            else:
                insufficient_count += 1

            verification_records.append({
                "claim": claim,
                "evidence": ev_text[:300] if ev_text else None,
                "verification_result": res_type,
                "confidence": verdict.get("confidence", 0.0),
                "reason": verdict.get("reason", "")
            })

        overall_conf = confidence_calculator.calculate_overall_confidence(verification_records)

        # Classify overall verification state
        if has_contradiction:
            overall_state = "CONTRADICTED"
        elif supported_count > 0 and supported_count >= insufficient_count:
            overall_state = "SUPPORTED"
        else:
            overall_state = "INSUFFICIENT_EVIDENCE"

        return {
            "claims": extracted_claims,
            "verification_results": verification_records,
            "overall_state": overall_state,
            "confidence": overall_conf,
            "has_contradiction": has_contradiction,
            "supported_count": supported_count,
            "contradicted_count": sum(1 for v in verification_records if v["verification_result"] == "CONTRADICTED"),
            "insufficient_count": insufficient_count
        }

hallucination_validator = HallucinationValidator()
