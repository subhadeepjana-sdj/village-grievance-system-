from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.auth import get_current_user, get_optional_current_user
from app.models.user import User
from app.models.ai_records import AIQuery, AIResponse, AIResponseCitation
from app.schemas.ai import AIQueryRequest, AIQueryResponse, EvidenceOut, VerificationResultOut, CitationOut
from app.rag.pipeline import rag_pipeline

router = APIRouter(prefix="/ai", tags=["AI Assistant & RAG"])


# ------------------------------------------------------------------ #
#  POST /api/ai/query                                                 #
# ------------------------------------------------------------------ #
@router.post("/query", response_model=AIQueryResponse)
def ask_ai_assistant(
    request: AIQueryRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    user_id = current_user.id if current_user else None
    config = request.configuration or "rag_verification"

    res = rag_pipeline.run_pipeline(
        question=request.question,
        db=db,
        user_id=user_id,
        configuration=config,
        department_filter=request.department   # ← new filter param
    )

    ev_outs = [
        EvidenceOut(
            document_id=e.get("document_id"),
            chunk_id=e.get("chunk_id"),
            similarity_score=e.get("similarity_score"),
            evidence_text=e.get("evidence_text", ""),
            source_type=e.get("source_type", "KB")
        )
        for e in res.get("evidences", [])
    ]

    vr_outs = [
        VerificationResultOut(
            claim=v.get("claim", ""),
            evidence=v.get("evidence"),
            verification_result=v.get("verification_result", "SUPPORTED"),
            confidence=v.get("confidence", 0.0),
            reason=v.get("reason")
        )
        for v in res.get("verification_results", [])
    ]

    cit_outs = [
        CitationOut(
            citation_id=c.get("citation_id", ""),
            claim_text=c.get("claim_text", ""),
            source_type=c.get("source_type", "KNOWLEDGE_BASE"),
            source_id=c.get("source_id", ""),
            document_id=c.get("document_id"),
            chunk_id=c.get("chunk_id"),
            source_field=c.get("source_field"),
            source_value=c.get("source_value"),
            evidence_text=c.get("evidence_text"),
            relevance_score=c.get("relevance_score", 0.0),
            status=c.get("status", "UNVERIFIED"),
            validation_message=c.get("validation_message"),
        )
        for c in res.get("citations", [])
    ]

    return AIQueryResponse(
        id=res["id"],
        question=res["question"],
        answer=res["answer"],
        decision=res["decision"],
        verification_status=res["verification_status"],
        confidence=res["confidence"],
        processing_time=res["processing_time"],
        configuration=res["configuration"],
        created_at=res["created_at"],
        evidences=ev_outs,
        verification_results=vr_outs,
        citations=cit_outs
    )


# ------------------------------------------------------------------ #
#  GET /api/ai/history                                                #
# ------------------------------------------------------------------ #
@router.get("/history", response_model=List[AIQueryResponse])
def get_ai_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    queries = (
        db.query(AIQuery)
        .filter(AIQuery.user_id == current_user.id)
        .order_by(AIQuery.timestamp.desc())
        .limit(20)
        .all()
    )
    history = []
    for q in queries:
        if q.response:
            resp = q.response
            evs = [
                EvidenceOut(
                    document_id=e.document_id,
                    chunk_id=e.chunk_id,
                    similarity_score=e.similarity_score,
                    evidence_text=e.evidence_text,
                    source_type=e.source_type
                )
                for e in resp.evidences
            ]
            vrs = [
                VerificationResultOut(
                    claim=v.claim,
                    evidence=v.evidence,
                    verification_result=v.verification_result,
                    confidence=v.confidence,
                    reason=v.reason
                )
                for v in resp.verification_results
            ]
            history.append(
                AIQueryResponse(
                    id=resp.id,
                    question=q.question,
                    answer=resp.answer,
                    decision=resp.decision,
                    verification_status=(
                        resp.decision
                        if resp.decision in ["SUPPORTED", "CONTRADICTED", "INSUFFICIENT_EVIDENCE"]
                        else "SUPPORTED"
                    ),
                    confidence=resp.confidence,
                    processing_time=resp.processing_time,
                    configuration=resp.configuration,
                    created_at=resp.created_at,
                    evidences=evs,
                    verification_results=vrs
                )
            )
    return history


# ------------------------------------------------------------------ #
#  GET /api/ai/sources/{response_id}                                 #
# ------------------------------------------------------------------ #
@router.get("/sources/{response_id}", response_model=List[EvidenceOut])
def get_response_sources(
    response_id: int,
    db: Session = Depends(get_db)
):
    """
    Return the evidence sources used to generate a specific AI response.

    Useful for citation display and audit: given the ``id`` returned by
    ``POST /api/ai/query``, retrieve every evidence chunk that was fed
    to the LLM for that answer.
    """
    resp = db.query(AIResponse).filter(AIResponse.id == response_id).first()
    if not resp:
        raise HTTPException(status_code=404, detail="AI response not found.")
    return [
        EvidenceOut(
            document_id=e.document_id,
            chunk_id=e.chunk_id,
            similarity_score=e.similarity_score,
            evidence_text=e.evidence_text,
            source_type=e.source_type
        )
        for e in resp.evidences
    ]


# ------------------------------------------------------------------ #
#  GET /api/ai/responses/{response_id}/citations                     #
# ------------------------------------------------------------------ #
@router.get("/responses/{response_id}/citations", response_model=List[CitationOut])
def get_response_citations(
    response_id: int,
    db: Session = Depends(get_db)
):
    """
    Feature 7 — Return structured citations for a specific AI response.

    Each citation links a factual claim in the answer to its
    authoritative source (complaint record, knowledge-base document,
    or government scheme), along with its validation status.
    """
    resp = db.query(AIResponse).filter(AIResponse.id == response_id).first()
    if not resp:
        raise HTTPException(status_code=404, detail="AI response not found.")
    return [
        CitationOut(
            citation_id=c.citation_label,
            claim_text=c.claim_text,
            source_type=c.source_type,
            source_id=c.source_id,
            document_id=c.document_id,
            chunk_id=c.chunk_id,
            source_field=c.source_field,
            source_value=c.source_value,
            evidence_text=c.evidence_text,
            relevance_score=c.relevance_score,
            status=c.validation_status,
            validation_message=c.validation_message,
        )
        for c in resp.citations
    ]
