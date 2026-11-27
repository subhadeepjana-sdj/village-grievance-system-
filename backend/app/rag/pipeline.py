import time
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.services.hybrid_retriever import hybrid_retriever
from app.services.llm_service import llm_service
from app.verification.correction.correction_controller import correction_controller
from app.verification.correction.audit_logger import audit_logger
from app.verification.abstention.abstention_engine import abstention_engine
from app.verification.abstention.audit_logger import abstention_audit_logger
from app.verification.citation.citation_generator import citation_generator
from app.verification.citation.citation_validator import citation_validator
from app.models.user import User
from app.models.ai_records import AIQuery, AIResponse, Evidence, VerificationResult, AIResponseCitation
from app.database.mongodb import mongodb_service

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
        corr_res = None
        abst_res = None
        if configuration in ["baseline", "rag"]:
            answer = llm_res.get("answer", "")
            decision = "SHOW"
            ver_status = "SUPPORTED" if evidence_list else "INSUFFICIENT_EVIDENCE"
            confidence = 85.0 if evidence_list else 40.0
            ver_results = []
        else:
            # Configuration C: Full 3-Tier Abstention & CVE Verification Engine
            user_obj = db.query(User).filter(User.id == user_id).first() if user_id else None
            abst_res = abstention_engine.process_and_decide(
                query=question,
                evidence_pool=evidence_list,
                db=db,
                current_user=user_obj
            )
            answer = abst_res["final_answer"]
            decision = abst_res["decision"]
            ver_status = abst_res["verification_status"]
            confidence = abst_res["confidence"]
            final_report = abst_res.get("final_report")
            ver_results = [
                {
                    "claim": c.claim.claim_text,
                    "evidence": c.matched_evidence_text,
                    "verification_result": c.status.value,
                    "confidence": c.confidence,
                    "reason": c.reason
                }
                for c in final_report.claims
            ] if final_report else []

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

        # 5. Persist detailed correction attempt audit logs
        if corr_res and "history" in corr_res:
            audit_logger.persist_correction_history(db, db_response.id, corr_res["history"])

        # 6. Persist Abstention Event Audit Log if decision was ABSTAIN
        if abst_res and abst_res.get("is_abstained"):
            abstention_audit_logger.log_abstention_event(
                db=db,
                response_id=db_response.id,
                intent=abst_res.get("intent", "GENERAL_KNOWLEDGE"),
                reason=abst_res.get("abstention_reason", "INSUFFICIENT_EVIDENCE"),
                missing_fields=abst_res.get("missing_fields"),
                pre_generation_halt=abst_res.get("pre_generation_halt", False)
            )

        # ------------------------------------------------------------------ #
        # 7. Feature 7 — Citation Generation & Validation                    #
        # ------------------------------------------------------------------ #
        citation_report = None
        citation_dicts = []
        final_report = abst_res.get("final_report") if abst_res else None
        if final_report and configuration == "rag_verification":
            try:
                citation_report = citation_generator.generate(
                    report=final_report,
                    evidence_pool=evidence_list,
                    response_id=db_response.id,
                )
                citation_report = citation_validator.validate(
                    report=citation_report,
                    db=db,
                )
                # Persist citations to DB
                for cit in citation_report.citations:
                    db_cit = AIResponseCitation(
                        response_id=db_response.id,
                        citation_label=cit.citation_id,
                        source_type=cit.source.source_type.value,
                        source_id=cit.source.source_id,
                        document_id=cit.source.document_id,
                        chunk_id=cit.source.chunk_id,
                        claim_text=cit.claim_text,
                        source_field=cit.source.source_field,
                        source_value=cit.source.source_value,
                        evidence_text=cit.evidence_text,
                        page_number=cit.source.page_number,
                        relevance_score=cit.relevance_score,
                        verified=1 if cit.status.value == "VERIFIED" else 0,
                        validation_status=cit.status.value,
                        validation_message=cit.validation_message,
                    )
                    db.add(db_cit)
                citation_dicts = [
                    {
                        "citation_id": c.citation_id,
                        "claim_text": c.claim_text,
                        "source_type": c.source.source_type.value,
                        "source_id": c.source.source_id,
                        "document_id": c.source.document_id,
                        "chunk_id": c.source.chunk_id,
                        "source_field": c.source.source_field,
                        "source_value": c.source.source_value,
                        "evidence_text": c.evidence_text,
                        "relevance_score": c.relevance_score,
                        "status": c.status.value,
                        "validation_message": c.validation_message,
                    }
                    for c in citation_report.citations
                ]
            except Exception as e:
                logger.warning("Citation generation failed: %s", e)

        db.commit()

        result_payload = {
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
            "verification_results": ver_results,
            "citations": citation_dicts,
        }

        # Mirror complete AI pipeline trace into MongoDB (no-op if disabled)
        mongodb_service.log_ai_trace({
            "response_id": db_response.id,
            "query_id": db_query.id,
            "user_id": user_id,
            "question": question,
            "answer": answer,
            "decision": decision,
            "verification_status": ver_status,
            "confidence": confidence,
            "processing_time": proc_time,
            "configuration": configuration,
            "evidences": evidence_list,
            "verification_results": ver_results,
            "citations": citation_dicts,
            "abstention": {
                "is_abstained": bool(abst_res and abst_res.get("is_abstained")),
                "reason": abst_res.get("abstention_reason") if abst_res else None,
            },
        })

        return result_payload


rag_pipeline = RAGPipeline()
