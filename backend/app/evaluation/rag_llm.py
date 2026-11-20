from typing import Dict, Any
from sqlalchemy.orm import Session
from app.services.hybrid_retriever import hybrid_retriever
from app.services.llm_service import llm_service

class RAGLLMEvaluator:
    """
    Configuration B: LLM + RAG.
    Evaluates evidence-grounded generation without NLI verification or correction loops.
    """
    def query(self, question: str, db: Session) -> Dict[str, Any]:
        retrieval_res = hybrid_retriever.retrieve_evidence(question, db, top_k=4)
        evidence = retrieval_res.get("evidence", [])
        llm_response = llm_service.generate_answer(question=question, evidence=evidence)
        return {
            "config": "RAG_LLM",
            "question": question,
            "answer": llm_response.get("answer", ""),
            "evidence": evidence,
            "verification_status": "SUPPORTED" if evidence else "INSUFFICIENT_EVIDENCE",
            "decision": "SHOW",
            "confidence": 85.0 if evidence else 40.0
        }

rag_llm = RAGLLMEvaluator()
