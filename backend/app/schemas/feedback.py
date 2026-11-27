"""
Feature 9 — AI Feedback & Error Review Pydantic Schemas.
"""

from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.feedback import FeedbackType, FeedbackStatus, RootCauseCategory


class FeedbackSubmitRequest(BaseModel):
    """Payload for citizen feedback submission."""
    response_id: int = Field(..., gt=0, description="ID of the AI response being rated")
    feedback_type: FeedbackType
    description: Optional[str] = Field(None, max_length=2000)


class FeedbackReviewRequest(BaseModel):
    """Payload for admin error investigation & resolution."""
    status: FeedbackStatus = FeedbackStatus.RESOLVED
    root_cause: RootCauseCategory
    corrective_action: Optional[str] = Field(None, max_length=2000)
    resolution_notes: Optional[str] = Field(None, max_length=4000)


class FeedbackReviewOut(BaseModel):
    """Read-only view of an admin review record."""
    id: int
    feedback_id: int
    admin_id: Optional[int] = None
    root_cause: str
    corrective_action: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AIFeedbackOut(BaseModel):
    """Summary view of a citizen feedback entry."""
    id: int
    response_id: int
    user_id: Optional[int] = None
    feedback_type: str
    description: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    reviews: List[FeedbackReviewOut] = []

    class Config:
        from_attributes = True


class FeedbackEvidenceSnapshot(BaseModel):
    id: int
    document_id: Optional[int] = None
    chunk_id: Optional[str] = None
    source_type: str
    similarity_score: Optional[float] = None
    evidence_text: str


class FeedbackVerificationSnapshot(BaseModel):
    id: int
    claim: str
    verification_result: str
    confidence: float
    reason: Optional[str] = None


class AIFeedbackDetailOut(BaseModel):
    """Full investigation context joining feedback with the AI response, evidence, and claims."""
    feedback: AIFeedbackOut
    question: Optional[str] = None
    answer: str
    decision: str
    confidence: float
    configuration: str
    evidences: List[FeedbackEvidenceSnapshot] = []
    verification_results: List[FeedbackVerificationSnapshot] = []


class PaginatedFeedback(BaseModel):
    """Paginated list of feedback entries."""
    items: List[AIFeedbackOut] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
    pages: int = 1


class FeedbackStatsOut(BaseModel):
    """Aggregate metrics for the AI Feedback & Error Review dashboard."""
    total_feedback: int = 0
    pending_count: int = 0
    reviewing_count: int = 0
    resolved_count: int = 0
    resolution_rate: float = 0.0
    by_feedback_type: Dict[str, int] = {}
    by_root_cause: Dict[str, int] = {}
