import logging
from typing import List, Dict, Any
from app.hallucination.validator import hallucination_validator
from app.services.llm_service import llm_service

logger = logging.getLogger("uvicorn.error")

class ResponseDecisionEngine:
    MAX_RETRY_LIMIT = 2

    def process_and_decide(
        self, 
        question: str, 
        evidence_list: List[Dict[str, Any]], 
        initial_answer_dict: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Runs Response Decision Engine workflow:
        Answer -> Verification -> (SHOW / REGENERATE-CORRECT / ABSTAIN)
        """
        current_answer = initial_answer_dict.get("answer", "")
        current_claims = initial_answer_dict.get("claims", [])
        
        attempt = 0
        validation = hallucination_validator.validate_response(current_answer, current_claims, evidence_list)

        # Correction Loop if CONTRADICTED
        while validation["has_contradiction"] and attempt < self.MAX_RETRY_LIMIT:
            attempt += 1
            logger.warning(f"[Correction Loop - Retry #{attempt}] Contradiction detected in LLM response. Regenerating using evidence...")

            # Strict correction prompt focusing on verified evidence
            corrected_dict = llm_service.generate_answer(
                question=f"CORRECTION REQUEST: The previous answer contained contradictions. Re-synthesize strictly using evidence:\nQuestion: {question}",
                evidence=evidence_list
            )
            current_answer = corrected_dict.get("answer", "")
            current_claims = corrected_dict.get("claims", [])
            validation = hallucination_validator.validate_response(current_answer, current_claims, evidence_list)

        # If contradiction STILL persists after retries, forcibly rewrite using exact evidence facts
        if validation["has_contradiction"]:
            logger.warning("Contradiction persisted after max retries. Overriding with strict evidence facts.")
            current_answer = self._build_deterministic_corrected_answer(evidence_list)
            validation = hallucination_validator.validate_response(current_answer, [], evidence_list)

        # Final Response Classification
        overall_state = validation["overall_state"]
        
        if overall_state == "SUPPORTED":
            final_decision = "SHOW"
        elif overall_state == "CONTRADICTED":
            final_decision = "CORRECT"
        else:
            final_decision = "ABSTAIN"
            current_answer = "I could not find sufficient verified information in village records to answer this question. Please contact the Gram Panchayat office."

        return {
            "answer": current_answer,
            "decision": final_decision,
            "verification_status": overall_state,
            "confidence": validation["confidence"],
            "verification_results": validation["verification_results"],
            "evidences": evidence_list,
            "attempts": attempt + 1
        }

    def _build_deterministic_corrected_answer(self, evidence_list: List[Dict[str, Any]]) -> str:
        complaint_evs = [e for e in evidence_list if e.get("source_type") == "COMPLAINT_RECORD"]
        if complaint_evs:
            return f"Verified Record Correction: {complaint_evs[0]['evidence_text']}"
        kb_evs = [e for e in evidence_list if e.get("evidence_text")]
        if kb_evs:
            return f"Verified Knowledge Base Correction: {kb_evs[0]['evidence_text'][:300]}"
        return "I could not find sufficient verified information to answer this question."

decision_engine = ResponseDecisionEngine()
