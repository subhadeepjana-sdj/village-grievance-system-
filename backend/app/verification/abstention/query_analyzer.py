import re
import logging
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

logger = logging.getLogger("uvicorn.error")


class QueryIntent(str, Enum):
    """Semantic intent classification of citizen queries."""
    STATUS_CHECK = "STATUS_CHECK"
    RESOLUTION_TIMELINE = "RESOLUTION_TIMELINE"
    DEPARTMENT_INQUIRY = "DEPARTMENT_INQUIRY"
    OFFICER_CONTACT = "OFFICER_CONTACT"
    SCHEME_ELIGIBILITY = "SCHEME_ELIGIBILITY"
    PROCEDURE_STEP = "PROCEDURE_STEP"
    GENERAL_KNOWLEDGE = "GENERAL_KNOWLEDGE"


class QueryAnalysis(BaseModel):
    """Structured analytical representation of citizen query requirements."""
    original_query: str
    intent: QueryIntent
    complaint_number: Optional[str] = None
    required_fields: List[str] = Field(default_factory=list)
    is_personalized: bool = False
    requires_complaint_record: bool = False


class QueryAnalyzer:
    """
    Tier 1 Pre-Generation Query Analyzer.
    Identifies what specific factual fields are strictly required to answer the query
    so the system can check evidence sufficiency before calling the LLM.
    """

    COMPLAINT_PATTERN = re.compile(r'\b(GRV-\d{4}-\d{4,6}|V\d{3,5})\b', re.IGNORECASE)

    TIMELINE_TRIGGERS = [
        "when will", "resolution date", "how long", "by when", "deadline",
        "expected date", "timeline", "days will it take", "when can i expect",
        "time to resolve", "how many days", "how much time"
    ]

    DEPT_TRIGGERS = [
        "who is handling", "which department", "assigned to", "who is in charge",
        "handled by", "which office", "responsible department"
    ]

    STATUS_TRIGGERS = [
        "what is the status", "is it resolved", "track complaint", "progress",
        "has it been", "current state", "check status", "latest update"
    ]

    CONTACT_TRIGGERS = [
        "phone number", "officer contact", "contact number", "call", "mobile"
    ]

    SCHEME_TRIGGERS = [
        "scheme", "eligibility", "eligible", "subsidy", "bpl card", "grant", "welfare"
    ]

    PROCEDURE_TRIGGERS = [
        "how to apply", "how do i apply", "procedure", "steps", "documents needed",
        "form", "where to submit"
    ]

    def analyze_query(
        self,
        query: str,
        explicit_complaint_id: Optional[str] = None
    ) -> QueryAnalysis:
        """
        Deconstructs query into intent and required database/document fields.
        """
        q_lower = query.lower().strip()

        # 1. Extract Complaint ID
        complaint_no = explicit_complaint_id
        if not complaint_no:
            match = self.COMPLAINT_PATTERN.search(query)
            if match:
                complaint_no = match.group(1).upper()

        # 2. Identify Intent & Required Attributes
        intent = QueryIntent.GENERAL_KNOWLEDGE
        required_fields: List[str] = []
        requires_record = False

        if any(trigger in q_lower for trigger in self.TIMELINE_TRIGGERS):
            intent = QueryIntent.RESOLUTION_TIMELINE
            required_fields = ["status", "expected_resolution_date"]
            requires_record = True
        elif any(trigger in q_lower for trigger in self.DEPT_TRIGGERS):
            intent = QueryIntent.DEPARTMENT_INQUIRY
            required_fields = ["department"]
            requires_record = True
        elif any(trigger in q_lower for trigger in self.STATUS_TRIGGERS):
            intent = QueryIntent.STATUS_CHECK
            required_fields = ["status"]
            requires_record = True
        elif any(trigger in q_lower for trigger in self.CONTACT_TRIGGERS):
            intent = QueryIntent.OFFICER_CONTACT
            required_fields = ["contact_information"]
            requires_record = True
        elif any(trigger in q_lower for trigger in self.SCHEME_TRIGGERS):
            intent = QueryIntent.SCHEME_ELIGIBILITY
            required_fields = ["eligibility_criteria"]
        elif any(trigger in q_lower for trigger in self.PROCEDURE_TRIGGERS):
            intent = QueryIntent.PROCEDURE_STEP
            required_fields = ["procedure_steps"]

        # If complaint number is present, query is personalized
        is_personalized = bool(complaint_no)
        if is_personalized and not required_fields:
            intent = QueryIntent.STATUS_CHECK
            required_fields = ["status", "department"]
            requires_record = True

        return QueryAnalysis(
            original_query=query,
            intent=intent,
            complaint_number=complaint_no,
            required_fields=required_fields,
            is_personalized=is_personalized,
            requires_complaint_record=requires_record
        )


query_analyzer = QueryAnalyzer()
