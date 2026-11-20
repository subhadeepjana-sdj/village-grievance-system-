from typing import Dict, Any
from app.services.llm_service import llm_service

class BaselineLLMEvaluator:
    """
    Configuration A: Standalone LLM (Gemini without RAG grounding).
    Evaluates direct generative answers without evidence retrieval or verification.
    """
    def query(self, question: str) -> Dict[str, Any]:
        llm_response = llm_service.generate_answer(question=question, evidence=[])
        return {
            "config": "STANDALONE_LLM",
            "question": question,
            "answer": llm_response.get("answer", ""),
            "evidence": [],
            "verification_status": "UNVERIFIED",
            "decision": "SHOW",
            "confidence": 50.0
        }

baseline_llm = BaselineLLMEvaluator()
