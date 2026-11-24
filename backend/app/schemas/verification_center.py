"""
Feature 8 — AI Verification Center Schemas
===========================================

Data contracts for the Administrative & Research AI Verification Center.
Provides comprehensive inspectability for the 7 core questions:
  1. What did the LLM generate?
  2. Which factual claims were extracted?
  3. What evidence was retrieved?
  4. Which claims were supported?
  5. Which claims were contradicted?
  6. Which claims had insufficient evidence?
  7. What corrections were made before delivering the final response?
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ------------------------------------------------------------------ #
#  Dashboard Overview Statistics                                      #
# ------------------------------------------------------------------ #

class VerificationOverviewStats(BaseModel):
    total_interactions: int
    total_claims_verified: int
    supported_claims: int
    contradicted_claims: int
    insufficient_claims: int
    total_corrections: int
    total_abstentions: int
    avg_confidence: float
    avg_latency: float
    verification_pass_rate: float
    claim_distribution: Dict[str, int] = Field(
        default_factory=lambda: {
            "SUPPORTED": 0,
            "CONTRADICTED": 0,
            "INSUFFICIENT_EVIDENCE": 0
        }
    )
    decision_distribution: Dict[str, int] = Field(
        default_factory=lambda: {
            "SHOW": 0,
            "CORRECT": 0,
            "ABSTAIN": 0
        }
    )


# ------------------------------------------------------------------ #
#  Interaction List Summary                                           #
# ------------------------------------------------------------------ #

class InteractionListItem(BaseModel):
    id: int
    query_id: int
    question: str
    final_answer: str
    decision: str
    verification_status: str
    confidence: float
    processing_time: float
    configuration: str
    claim_count: int
    supported_count: int
    contradicted_count: int
    insufficient_count: int
    had_correction: bool
    is_abstained: bool
    created_at: datetime


class PaginatedInteractions(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[InteractionListItem]


# ------------------------------------------------------------------ #
#  The 7-Question Interaction Detail Drilldown                        #
# ------------------------------------------------------------------ #

class InteractionDetail(BaseModel):
    """Answers the 7 critical audit questions for an AI response."""
    interaction_id: int
    query_id: int
    user_id: Optional[int] = None
    question: str
    timestamp: datetime
    configuration: str
    decision: str
    confidence: float
    processing_time: float

    # Question 1: What did the LLM generate?
    question_1_raw_generation: Dict[str, Any] = Field(
        ...,
        description="Initial raw answer draft before verification, plus candidate prompt/context"
    )

    # Question 2: Which factual claims were extracted?
    question_2_extracted_claims: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of atomic factual propositions decomposed from the candidate text"
    )

    # Question 3: What evidence was retrieved?
    question_3_retrieved_evidence: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Retrieved knowledge-base document chunks and PostgreSQL database records"
    )

    # Question 4: Which claims were supported?
    question_4_supported_claims: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Claims verified as entailed by database ground truth or cross-encoder NLI"
    )

    # Question 5: Which claims were contradicted?
    question_5_contradicted_claims: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Claims refuted by database records or cross-encoder NLI"
    )

    # Question 6: Which claims had insufficient evidence?
    question_6_insufficient_evidence_claims: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Claims without supporting evidence in the verified corpus"
    )

    # Question 7: What corrections were made before delivering the final response?
    question_7_corrections_made: Dict[str, Any] = Field(
        ...,
        description="Correction attempts, negative-constraint directives, and delivered final response"
    )

    # Structured citations
    citations: List[Dict[str, Any]] = Field(default_factory=list)


# ------------------------------------------------------------------ #
#  Individual Claim, Evidence, and Correction Models                  #
# ------------------------------------------------------------------ #

class ClaimDetail(BaseModel):
    id: int
    response_id: int
    claim: str
    evidence: Optional[str] = None
    verification_result: str
    confidence: float
    reason: Optional[str] = None
    associated_citation: Optional[Dict[str, Any]] = None


class EvidenceDetail(BaseModel):
    id: int
    response_id: int
    document_id: Optional[int] = None
    chunk_id: Optional[str] = None
    similarity_score: Optional[float] = None
    evidence_text: str
    source_type: str
    verified_claims: List[str] = Field(default_factory=list)


class CorrectionHistoryItem(BaseModel):
    id: int
    attempt_number: int
    candidate_answer: str
    status: str
    action: str
    confidence: float
    prompt_directive: Optional[str] = None
    created_at: datetime


# ------------------------------------------------------------------ #
#  Human-in-the-Loop Feedback                                         #
# ------------------------------------------------------------------ #

class FeedbackCreate(BaseModel):
    response_id: int
    claim_id: Optional[int] = None
    feedback_type: str = Field(..., description="FALSE_CONTRADICTION | FALSE_ENTAILMENT | MISSED_HALLUCINATION | GENERAL")
    corrected_verdict: Optional[str] = Field(None, description="SUPPORTED | CONTRADICTED | INSUFFICIENT_EVIDENCE")
    notes: str = Field(..., min_length=3, description="Audit rationale or correction details")


class FeedbackResponse(BaseModel):
    id: int
    response_id: int
    claim_id: Optional[int]
    user_id: Optional[int]
    feedback_type: str
    corrected_verdict: Optional[str]
    notes: str
    created_at: datetime


# ------------------------------------------------------------------ #
#  Evaluation & Research Reports                                      #
# ------------------------------------------------------------------ #

class EvaluationReportItem(BaseModel):
    run_id: str
    config_type: str
    factual_accuracy: float
    hallucination_rate: float
    faithfulness: float
    retrieval_recall: float
    precision: float
    recall: float
    f1_score: float
    abstention_accuracy: float
    avg_latency: float
    timestamp: datetime
