"""
Feature 8 — AI Verification Center API Router
=============================================

Administrative and Research inspection endpoints for the Claim Verification
Engine (CVE). Provides comprehensive visibility into the 7 core questions
regarding LLM generation, claim extraction, evidence retrieval, verification
verdicts, correction attempts, and human-in-the-loop audit feedback.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database.session import get_db
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.ai_records import (
    AIQuery,
    AIResponse,
    Evidence,
    VerificationResult,
    AICorrectionLog,
    AIAbstentionLog,
    AIResponseCitation,
    AIVerificationFeedback,
    ResearchMetric,
)
from app.schemas.verification_center import (
    VerificationOverviewStats,
    InteractionListItem,
    PaginatedInteractions,
    InteractionDetail,
    ClaimDetail,
    EvidenceDetail,
    CorrectionHistoryItem,
    FeedbackCreate,
    FeedbackResponse,
    EvaluationReportItem,
)

router = APIRouter(prefix="/admin/verification", tags=["AI Verification Center"])

AUTHORIZED_ROLES = [UserRole.ADMIN, UserRole.PANCHAYAT_STAFF, UserRole.RESEARCHER]


def _check_admin_or_researcher(user: User):
    if user.role not in AUTHORIZED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. AI Verification Center requires Administrator or Researcher credentials.",
        )


# ------------------------------------------------------------------ #
#  1. GET /api/admin/verification/overview                            #
# ------------------------------------------------------------------ #
@router.get("/overview", response_model=VerificationOverviewStats)
def get_verification_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns high-level verification dashboard summary statistics:
    total interactions, claim distribution, correction counts, abstentions,
    and average confidence.
    """
    _check_admin_or_researcher(current_user)

    responses = db.query(AIResponse).all()
    claims = db.query(VerificationResult).all()
    corrections_count = db.query(AICorrectionLog).count()
    abstentions_count = db.query(AIAbstentionLog).count()

    total_interactions = len(responses)
    total_claims = len(claims)

    supported_count = sum(1 for c in claims if c.verification_result == "SUPPORTED")
    contradicted_count = sum(1 for c in claims if c.verification_result == "CONTRADICTED")
    insufficient_count = sum(1 for c in claims if c.verification_result == "INSUFFICIENT_EVIDENCE")

    show_count = sum(1 for r in responses if r.decision == "SHOW")
    correct_count = sum(1 for r in responses if r.decision == "CORRECT")
    abstain_count = sum(1 for r in responses if r.decision == "ABSTAIN")

    avg_conf = (
        round(sum(r.confidence for r in responses) / total_interactions, 2)
        if total_interactions > 0
        else 0.0
    )
    avg_lat = (
        round(sum(r.processing_time for r in responses) / total_interactions, 3)
        if total_interactions > 0
        else 0.0
    )
    pass_rate = (
        round((show_count / total_interactions) * 100.0, 1)
        if total_interactions > 0
        else 100.0
    )

    return VerificationOverviewStats(
        total_interactions=total_interactions,
        total_claims_verified=total_claims,
        supported_claims=supported_count,
        contradicted_claims=contradicted_count,
        insufficient_claims=insufficient_count,
        total_corrections=corrections_count,
        total_abstentions=abstentions_count,
        avg_confidence=avg_conf,
        avg_latency=avg_lat,
        verification_pass_rate=pass_rate,
        claim_distribution={
            "SUPPORTED": supported_count,
            "CONTRADICTED": contradicted_count,
            "INSUFFICIENT_EVIDENCE": insufficient_count,
        },
        decision_distribution={
            "SHOW": show_count,
            "CORRECT": correct_count,
            "ABSTAIN": abstain_count,
        },
    )


# ------------------------------------------------------------------ #
#  2. GET /api/admin/verification/interactions                        #
# ------------------------------------------------------------------ #
@router.get("/interactions", response_model=PaginatedInteractions)
def list_interactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    decision: Optional[str] = Query(None, description="SHOW | CORRECT | ABSTAIN"),
    search: Optional[str] = Query(None, description="Search query text"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Paginated list of AI interactions with claim verification summaries.
    Filterable by decision and search string.
    """
    _check_admin_or_researcher(current_user)

    query = db.query(AIResponse).join(AIQuery)

    if decision:
        query = query.filter(AIResponse.decision == decision)
    if search:
        query = query.filter(
            (AIQuery.question.ilike(f"%{search}%")) | (AIResponse.answer.ilike(f"%{search}%"))
        )

    total = query.count()
    responses = (
        query.order_by(desc(AIResponse.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for r in responses:
        c_all = r.verification_results
        items.append(
            InteractionListItem(
                id=r.id,
                query_id=r.query_id,
                question=r.query.question if r.query else "N/A",
                final_answer=r.answer,
                decision=r.decision,
                verification_status=(
                    r.decision
                    if r.decision in ["SUPPORTED", "CONTRADICTED", "INSUFFICIENT_EVIDENCE"]
                    else "SUPPORTED"
                ),
                confidence=r.confidence,
                processing_time=r.processing_time,
                configuration=r.configuration,
                claim_count=len(c_all),
                supported_count=sum(1 for c in c_all if c.verification_result == "SUPPORTED"),
                contradicted_count=sum(1 for c in c_all if c.verification_result == "CONTRADICTED"),
                insufficient_count=sum(1 for c in c_all if c.verification_result == "INSUFFICIENT_EVIDENCE"),
                had_correction=len(r.correction_logs) > 0,
                is_abstained=r.decision == "ABSTAIN" or len(r.abstention_logs) > 0,
                created_at=r.created_at,
            )
        )

    return PaginatedInteractions(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
    )


# ------------------------------------------------------------------ #
#  3. GET /api/admin/verification/interactions/{id}                   #
# ------------------------------------------------------------------ #
@router.get("/interactions/{id}", response_model=InteractionDetail)
def get_interaction_drilldown(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Detailed inspection answering the 7 core questions for an AI response:
      1. What did the LLM generate?
      2. Which factual claims were extracted?
      3. What evidence was retrieved?
      4. Which claims were supported?
      5. Which claims were contradicted?
      6. Which claims had insufficient evidence?
      7. What corrections were made before delivering the final response?
    """
    _check_admin_or_researcher(current_user)

    r = db.query(AIResponse).filter(AIResponse.id == id).first()
    if not r:
        raise HTTPException(status_code=404, detail=f"AI interaction ID {id} not found.")

    # 1. Raw Generation
    first_correction = (
        db.query(AICorrectionLog)
        .filter(AICorrectionLog.response_id == id)
        .order_by(AICorrectionLog.attempt_number.asc())
        .first()
    )
    raw_answer = first_correction.candidate_answer if first_correction else r.answer
    raw_generation = {
        "raw_candidate_answer": raw_answer,
        "configuration": r.configuration,
        "had_regeneration": len(r.correction_logs) > 0,
    }

    # 2. Extracted claims
    extracted = [
        {
            "claim_id": f"C{idx + 1}",
            "db_id": c.id,
            "claim_text": c.claim,
            "verification_result": c.verification_result,
            "confidence": c.confidence,
            "matched_evidence": c.evidence,
            "reason": c.reason,
        }
        for idx, c in enumerate(r.verification_results)
    ]

    # 3. Retrieved evidence
    evidences = [
        {
            "id": e.id,
            "source_type": e.source_type,
            "document_id": e.document_id,
            "chunk_id": e.chunk_id,
            "similarity_score": e.similarity_score,
            "evidence_text": e.evidence_text,
        }
        for e in r.evidences
    ]

    # 4. Supported
    supported = [c for c in extracted if c["verification_result"] == "SUPPORTED"]

    # 5. Contradicted
    contradicted = [c for c in extracted if c["verification_result"] == "CONTRADICTED"]

    # 6. Insufficient evidence
    insufficient = [c for c in extracted if c["verification_result"] == "INSUFFICIENT_EVIDENCE"]

    # 7. Corrections made
    correction_history = [
        {
            "attempt": log.attempt_number,
            "candidate_answer": log.candidate_answer,
            "status": log.status,
            "action": log.action,
            "confidence": log.confidence,
            "prompt_directive": log.prompt_directive,
            "timestamp": log.created_at,
        }
        for log in r.correction_logs
    ]
    corrections_made = {
        "correction_attempts_count": len(r.correction_logs),
        "history": correction_history,
        "delivered_final_answer": r.answer,
        "decision": r.decision,
    }

    # Citations
    citations = [
        {
            "citation_label": cit.citation_label,
            "claim_text": cit.claim_text,
            "source_type": cit.source_type,
            "source_id": cit.source_id,
            "source_field": cit.source_field,
            "source_value": cit.source_value,
            "relevance_score": cit.relevance_score,
            "validation_status": cit.validation_status,
            "validation_message": cit.validation_message,
        }
        for cit in r.citations
    ]

    return InteractionDetail(
        interaction_id=r.id,
        query_id=r.query_id,
        user_id=r.query.user_id if r.query else None,
        question=r.query.question if r.query else "N/A",
        timestamp=r.created_at,
        configuration=r.configuration,
        decision=r.decision,
        confidence=r.confidence,
        processing_time=r.processing_time,
        question_1_raw_generation=raw_generation,
        question_2_extracted_claims=extracted,
        question_3_retrieved_evidence=evidences,
        question_4_supported_claims=supported,
        question_5_contradicted_claims=contradicted,
        question_6_insufficient_evidence_claims=insufficient,
        question_7_corrections_made=corrections_made,
        citations=citations,
    )


# ------------------------------------------------------------------ #
#  4. GET /api/admin/verification/claims/{id}                         #
# ------------------------------------------------------------------ #
@router.get("/claims/{id}", response_model=ClaimDetail)
def get_claim_detail(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Inspect an individual factual claim and its verification rationale."""
    _check_admin_or_researcher(current_user)

    c = db.query(VerificationResult).filter(VerificationResult.id == id).first()
    if not c:
        raise HTTPException(status_code=404, detail=f"Claim ID {id} not found.")

    linked_citation = (
        db.query(AIResponseCitation)
        .filter(
            AIResponseCitation.response_id == c.response_id,
            AIResponseCitation.claim_text == c.claim,
        )
        .first()
    )

    cit_dict = None
    if linked_citation:
        cit_dict = {
            "citation_label": linked_citation.citation_label,
            "source_type": linked_citation.source_type,
            "source_id": linked_citation.source_id,
            "validation_status": linked_citation.validation_status,
        }

    return ClaimDetail(
        id=c.id,
        response_id=c.response_id,
        claim=c.claim,
        evidence=c.evidence,
        verification_result=c.verification_result,
        confidence=c.confidence,
        reason=c.reason,
        associated_citation=cit_dict,
    )


# ------------------------------------------------------------------ #
#  5. GET /api/admin/verification/evidence/{id}                       #
# ------------------------------------------------------------------ #
@router.get("/evidence/{id}", response_model=EvidenceDetail)
def get_evidence_detail(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """View retrieved evidence chunk and all claims it grounded."""
    _check_admin_or_researcher(current_user)

    e = db.query(Evidence).filter(Evidence.id == id).first()
    if not e:
        raise HTTPException(status_code=404, detail=f"Evidence ID {id} not found.")

    # Find claims from the same response referencing this evidence
    claims = (
        db.query(VerificationResult)
        .filter(
            VerificationResult.response_id == e.response_id,
            VerificationResult.evidence.isnot(None),
        )
        .all()
    )
    verified_claim_texts = [c.claim for c in claims]

    return EvidenceDetail(
        id=e.id,
        response_id=e.response_id,
        document_id=e.document_id,
        chunk_id=e.chunk_id,
        similarity_score=e.similarity_score,
        evidence_text=e.evidence_text,
        source_type=e.source_type,
        verified_claims=verified_claim_texts,
    )


# ------------------------------------------------------------------ #
#  6. GET /api/admin/verification/corrections/{response_id}           #
# ------------------------------------------------------------------ #
@router.get("/corrections/{response_id}", response_model=List[CorrectionHistoryItem])
def get_correction_history(
    response_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """View the multi-attempt regeneration history for a specific response."""
    _check_admin_or_researcher(current_user)

    logs = (
        db.query(AICorrectionLog)
        .filter(AICorrectionLog.response_id == response_id)
        .order_by(AICorrectionLog.attempt_number.asc())
        .all()
    )
    return [
        CorrectionHistoryItem(
            id=log.id,
            attempt_number=log.attempt_number,
            candidate_answer=log.candidate_answer,
            status=log.status,
            action=log.action,
            confidence=log.confidence,
            prompt_directive=log.prompt_directive,
            created_at=log.created_at,
        )
        for log in logs
    ]


# ------------------------------------------------------------------ #
#  7. GET /api/admin/verification/reports                             #
# ------------------------------------------------------------------ #
@router.get("/reports", response_model=List[EvaluationReportItem])
def get_evaluation_reports(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve comparative research evaluation benchmarks."""
    _check_admin_or_researcher(current_user)

    metrics = (
        db.query(ResearchMetric)
        .order_by(desc(ResearchMetric.timestamp))
        .limit(limit)
        .all()
    )
    return [
        EvaluationReportItem(
            run_id=m.run_id,
            config_type=m.config_type,
            factual_accuracy=m.factual_accuracy,
            hallucination_rate=m.hallucination_rate,
            faithfulness=m.faithfulness,
            retrieval_recall=m.retrieval_recall,
            precision=m.precision,
            recall=m.recall,
            f1_score=m.f1_score,
            abstention_accuracy=m.abstention_accuracy,
            avg_latency=m.avg_latency,
            timestamp=m.timestamp,
        )
        for m in metrics
    ]


# ------------------------------------------------------------------ #
#  8. POST /api/admin/verification/feedback                           #
# ------------------------------------------------------------------ #
@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_verification_feedback(
    feedback: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Record human-in-the-loop audit feedback or flag an erroneous NLI verdict
    for continuous model evaluation.
    """
    _check_admin_or_researcher(current_user)

    resp = db.query(AIResponse).filter(AIResponse.id == feedback.response_id).first()
    if not resp:
        raise HTTPException(
            status_code=404,
            detail=f"Target AI response ID {feedback.response_id} does not exist.",
        )

    if feedback.claim_id:
        c = db.query(VerificationResult).filter(VerificationResult.id == feedback.claim_id).first()
        if not c:
            raise HTTPException(
                status_code=404,
                detail=f"Target claim ID {feedback.claim_id} does not exist.",
            )

    new_fb = AIVerificationFeedback(
        response_id=feedback.response_id,
        claim_id=feedback.claim_id,
        user_id=current_user.id,
        feedback_type=feedback.feedback_type,
        corrected_verdict=feedback.corrected_verdict,
        notes=feedback.notes,
    )
    db.add(new_fb)
    db.commit()
    db.refresh(new_fb)

    return FeedbackResponse(
        id=new_fb.id,
        response_id=new_fb.response_id,
        claim_id=new_fb.claim_id,
        user_id=new_fb.user_id,
        feedback_type=new_fb.feedback_type,
        corrected_verdict=new_fb.corrected_verdict,
        notes=new_fb.notes,
        created_at=new_fb.created_at,
    )
