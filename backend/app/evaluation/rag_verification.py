from typing import Dict, Any
from sqlalchemy.orm import Session
from app.rag.pipeline import rag_pipeline

class RAGVerificationEvaluator:
    """
    Configuration C: LLM + RAG + Hallucination Verification + Response Decision Engine.
    Executes full multi-stage pipeline: Retrieval -> Gemini Generation -> Claim Extraction ->
    NLI Contradiction Detection -> Confidence Scoring -> Response Decision (SHOW/CORRECT/ABSTAIN).
    """
    def query(self, question: str, db: Session, user_id: int = None) -> Dict[str, Any]:
        return rag_pipeline.run_pipeline(
            question=question,
            db=db,
            user_id=user_id,
            configuration="rag_verification"
        )

rag_verification = RAGVerificationEvaluator()
