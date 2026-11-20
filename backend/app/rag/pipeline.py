import time
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.services.hybrid_retriever import hybrid_retriever
from app.services.llm_service import llm_service
from app.hallucination.decision_engine import decision_engine
from app.models.ai_records import AIQuery, AIResponse, Evidence, VerificationResult

logger = logging.getLogger("uvicorn.error")


class RAGPipeline:
    def run_pipeline(
        self,
        question: str,
        db: Session,
        user_id: Optional[int] = None,
        configuration: str = "rag_verification",
        department_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Full RAG pipeline:
          1. Hybrid retrieval (PostgreSQL structured + Qdrant semantic)
          2. LLM answer generation
          3. Hallucination verification + decision (rag_verification mode)
          4. Audit log persistence

        Parameters
        ----------
        question:          User's natural-language question.
        db:                SQLAlchemy session.
        user_id:           Logged-in user ID (for personalised complaint lookup).
        configuration:     "baseline" | "rag" | "rag_verification"
        department_filter: Optional Qdrant department filter from the API request.
        """
        start_time = time.time()

        # ------------------------------------------------------------------ #
        # 1. Query Analysis & Hybrid Retrieval                                #
        # ------------------------------------------------------------------ #
        retrieval_res = hybrid_retriever.retrieve_evidence(
            query=question,
            db=db,
            user_id=user_id,
            top_k=4,
            department_filter=department_filter,
            verified_only=True   # Only return "verified" Qdrant chunks by default
        )
        evidence_list = retrieval_res.get("evidence", [])

        # ------------------------------------------------------------------ #
        # 2. LLM Answer Generation                                            #
        # ------------------------------------------------------------------ #
        if configuration == "baseline":
            # Configuration A: standalone LLM — no RAG context
            llm_res = llm_service.generate_answer(question, [])
            evidence_list = []
        else:
            # Configurations B & C: LLM grounded on retrieved evidence
            llm_res = llm_service.generate_answer(question, evidence_list)

        # ------------------------------------------------------------------ #
        # 3. Response Decision & Hallucination Verification                   #
        # ------------------------------------------------------------------ #
        if configuration in ["baseline", "rag"]:
            answer = llm_res.get("answer", "")
            decision = "SHOW"
            ver_status = "SUPPORTED" if evidence_list else "INSUFFICIENT_EVIDENCE"
            confidence = 85.0 if evidence_list else 40.0
            ver_results = []
        else:
            # Configuration C: full RAG + NLI verification + correction loop
            decision_res = decision_engine.process_and_decide(question, evidence_list, llm_res)
            answer = decision_res["answer"]
            decision = decision_res["decision"]
            ver_status = decision_res["verification_status"]
            confidence = decision_res["confidence"]
            ver_results = decision_res["verification_results"]

        proc_time = round(time.time() - start_time, 3)

        # ------------------------------------------------------------------ #
        # 4. Audit Log: save Query → Response → Evidence → VerificationResult #
        # ------------------------------------------------------------------ #
        db_query = AIQuery(user_id=user_id, question=question, query_type="GENERAL")
        db.add(db_query)
        db.commit()
        db.refresh(db_query)

        db_response = AIResponse(
            query_id=db_query.id,
            answer=answer,
            decision=decision,
            confidence=confidence,
            processing_time=proc_time,
            configuration=configuration
        )
        db.add(db_response)
        db.commit()
        db.refresh(db_response)

        for ev in evidence_list:
            db_ev = Evidence(
                response_id=db_response.id,
                document_id=ev.get("document_id"),
                chunk_id=ev.get("chunk_id"),
                similarity_score=ev.get("similarity_score", 1.0),
                evidence_text=ev.get("evidence_text", ""),
                source_type=ev.get("source_type", "KNOWLEDGE_BASE")
            )
            db.add(db_ev)

        for vr in ver_results:
            db_vr = VerificationResult(
                response_id=db_response.id,
                claim=vr.get("claim", ""),
                evidence=vr.get("evidence", ""),
                verification_result=vr.get("verification_result", ""),
                confidence=vr.get("confidence", 0.0),
                reason=vr.get("reason", "")
            )
            db.add(db_vr)

        db.commit()

        return {
            "id": db_response.id,
            "question": question,
            "answer": answer,
            "decision": decision,
            "verification_status": ver_status,
            "confidence": confidence,
            "processing_time": proc_time,
            "configuration": configuration,
            "created_at": db_response.created_at,
            "evidences": evidence_list,
            "verification_results": ver_results
        }


rag_pipeline = RAGPipeline()
