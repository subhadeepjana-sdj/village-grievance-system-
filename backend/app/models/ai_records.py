import datetime
# pyrefly: ignore [missing-import]
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import relationship
from app.database.session import Base

class AIQuery(Base):
    __tablename__ = "ai_queries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    question = Column(Text, nullable=False)
    query_type = Column(String(50), default="GENERAL", nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="ai_queries")
    response = relationship("AIResponse", back_populates="query", uselist=False)

class AIResponse(Base):
    __tablename__ = "ai_responses"

    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(Integer, ForeignKey("ai_queries.id", ondelete="CASCADE"), nullable=False)
    answer = Column(Text, nullable=False)
    decision = Column(String(50), nullable=False)  # SHOW / CORRECT / ABSTAIN / SUPPORTED / CONTRADICTED / INSUFFICIENT_EVIDENCE
    confidence = Column(Float, nullable=False, default=0.0)
    processing_time = Column(Float, nullable=False, default=0.0)  # seconds
    configuration = Column(String(50), default="rag_verification", nullable=False)  # baseline / rag / rag_verification
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    query = relationship("AIQuery", back_populates="response")
    evidences = relationship("Evidence", back_populates="response", cascade="all, delete-orphan")
    verification_results = relationship("VerificationResult", back_populates="response", cascade="all, delete-orphan")
    correction_logs = relationship("AICorrectionLog", back_populates="response", cascade="all, delete-orphan")
    abstention_logs = relationship("AIAbstentionLog", back_populates="response", cascade="all, delete-orphan")
    citations = relationship("AIResponseCitation", back_populates="response", cascade="all, delete-orphan")

class Evidence(Base):
    __tablename__ = "evidences"

    id = Column(Integer, primary_key=True, index=True)
    response_id = Column(Integer, ForeignKey("ai_responses.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(Integer, nullable=True)
    chunk_id = Column(String(100), nullable=True)
    similarity_score = Column(Float, nullable=True)
    evidence_text = Column(Text, nullable=False)
    source_type = Column(String(50), default="KNOWLEDGE_BASE")  # KNOWLEDGE_BASE / COMPLAINT_RECORD / SCHEME

    response = relationship("AIResponse", back_populates="evidences")

class VerificationResult(Base):
    __tablename__ = "verification_results"

    id = Column(Integer, primary_key=True, index=True)
    response_id = Column(Integer, ForeignKey("ai_responses.id", ondelete="CASCADE"), nullable=False)
    claim = Column(Text, nullable=False)
    evidence = Column(Text, nullable=True)
    verification_result = Column(String(50), nullable=False)  # SUPPORTED / CONTRADICTED / INSUFFICIENT_EVIDENCE
    confidence = Column(Float, default=0.0)
    reason = Column(Text, nullable=True)

    response = relationship("AIResponse", back_populates="verification_results")

class AICorrectionLog(Base):
    __tablename__ = "ai_correction_logs"

    id = Column(Integer, primary_key=True, index=True)
    response_id = Column(Integer, ForeignKey("ai_responses.id", ondelete="CASCADE"), nullable=False)
    attempt_number = Column(Integer, nullable=False, default=1)
    candidate_answer = Column(Text, nullable=False)
    status = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)
    confidence = Column(Float, default=0.0)
    prompt_directive = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    response = relationship("AIResponse", back_populates="correction_logs")

class AIAbstentionLog(Base):
    __tablename__ = "ai_abstention_logs"

    id = Column(Integer, primary_key=True, index=True)
    response_id = Column(Integer, ForeignKey("ai_responses.id", ondelete="CASCADE"), nullable=True)
    complaint_number = Column(String(50), nullable=True, index=True)
    intent = Column(String(50), nullable=False)
    abstention_reason = Column(String(100), nullable=False)
    missing_fields = Column(Text, nullable=True)
    pre_generation_halt = Column(Integer, default=0)  # 1 if halted at Tier 1 before LLM, 0 otherwise
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    response = relationship("AIResponse", back_populates="abstention_logs")


class AIResponseCitation(Base):
    """
    Feature 7 — Persistent citation record.

    Each row links one claim in an AI response to the authoritative
    evidence source that supports it.  The ``verified`` flag is set by
    the Citation Validator after cross-checking against the database.
    """
    __tablename__ = "ai_response_citations"

    id = Column(Integer, primary_key=True, index=True)
    response_id = Column(Integer, ForeignKey("ai_responses.id", ondelete="CASCADE"), nullable=False)
    citation_label = Column(String(20), nullable=False)                 # e.g. "[1]"
    source_type = Column(String(50), nullable=False)                    # COMPLAINT_RECORD / KNOWLEDGE_BASE / SCHEME
    source_id = Column(String(100), nullable=False)                     # complaint number or document ref
    document_id = Column(Integer, nullable=True)                        # FK → documents (optional)
    chunk_id = Column(String(100), nullable=True)                       # Qdrant chunk ID
    claim_text = Column(Text, nullable=False)                           # The factual claim being cited
    source_field = Column(String(100), nullable=True)                   # DB column name (for complaint records)
    source_value = Column(Text, nullable=True)                          # Authoritative value of the field
    evidence_text = Column(Text, nullable=True)                         # Verbatim passage from the source
    page_number = Column(Integer, nullable=True)                        # Page/section number
    relevance_score = Column(Float, default=0.0)                        # Retrieval similarity score
    verified = Column(Integer, default=0)                               # 1 = validated, 0 = unverified
    validation_status = Column(String(50), default="UNVERIFIED")        # VERIFIED / INVALID / STALE / ACCESS_DENIED
    validation_message = Column(Text, nullable=True)                    # Human-readable explanation
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    response = relationship("AIResponse", back_populates="citations")

class ResearchMetric(Base):
    __tablename__ = "research_metrics"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(100), nullable=False, index=True)
    config_type = Column(String(50), nullable=False)  # STANDALONE_LLM / RAG_LLM / RAG_VERIFICATION
    factual_accuracy = Column(Float, nullable=False)
    hallucination_rate = Column(Float, nullable=False)
    faithfulness = Column(Float, nullable=False)
    retrieval_recall = Column(Float, nullable=False)
    precision = Column(Float, nullable=False)
    recall = Column(Float, nullable=False)
    f1_score = Column(Float, nullable=False)
    abstention_accuracy = Column(Float, nullable=False)
    avg_latency = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
