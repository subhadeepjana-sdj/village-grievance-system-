"""
Feature 9 — AI Feedback & Error Review Models.

Enables citizens and end-users to report issues with AI answers, and allows
administrators/researchers to investigate root causes and track resolution.

Tables
------
``ai_feedback``
    Citizen-facing feedback linked to an ``AIResponse``. Tracks
    feedback category (Helpful, Incorrect, Incomplete, Misleading) and
    investigation status (Pending, Reviewing, Resolved).

``feedback_reviews``
    Administrative investigation records attached to an ``AIFeedback``.
    Captures root-cause classification (Retrieval, Outdated_Document,
    Model_Generation, Verification_Failure), corrective action, and
    resolution timestamp.
"""

import enum
import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.database.session import Base


class FeedbackType(str, enum.Enum):
    """Citizen feedback classification for an AI response."""
    HELPFUL = "HELPFUL"
    INCORRECT = "INCORRECT"
    INCOMPLETE = "INCOMPLETE"
    MISLEADING = "MISLEADING"


class FeedbackStatus(str, enum.Enum):
    """Triage lifecycle status of a citizen feedback entry."""
    PENDING = "PENDING"
    REVIEWING = "REVIEWING"
    RESOLVED = "RESOLVED"


class RootCauseCategory(str, enum.Enum):
    """Root-cause classification assigned during admin error review."""
    RETRIEVAL = "RETRIEVAL"
    OUTDATED_DOCUMENT = "OUTDATED_DOCUMENT"
    MODEL_GENERATION = "MODEL_GENERATION"
    VERIFICATION_FAILURE = "VERIFICATION_FAILURE"
    OTHER = "OTHER"


class AIFeedback(Base):
    """
    Citizen/user feedback submitted against a generated AI response.
    """
    __tablename__ = "ai_feedback"

    id = Column(Integer, primary_key=True, index=True)
    response_id = Column(
        Integer,
        ForeignKey("ai_responses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    feedback_type = Column(String(30), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(
        String(20),
        nullable=False,
        default=FeedbackStatus.PENDING.value,
        index=True,
    )

    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    response = relationship("AIResponse")
    user = relationship("User")
    reviews = relationship(
        "FeedbackReview",
        back_populates="feedback",
        cascade="all, delete-orphan",
        order_by="FeedbackReview.created_at.desc()",
    )


class FeedbackReview(Base):
    """
    Administrative error-review and root-cause investigation record.
    """
    __tablename__ = "feedback_reviews"

    id = Column(Integer, primary_key=True, index=True)
    feedback_id = Column(
        Integer,
        ForeignKey("ai_feedback.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    admin_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    root_cause = Column(String(40), nullable=False, index=True)
    corrective_action = Column(Text, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    feedback = relationship("AIFeedback", back_populates="reviews")
    admin = relationship("User")
