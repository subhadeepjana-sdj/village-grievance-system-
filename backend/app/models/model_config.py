"""
Feature 12 — Model & RAG Management Models.

Provides centralized registry, versioning, evaluation gating, and admin
approval workflows for LLM models, RAG retrieval pipelines, and Claim
Verification Engine (CVE) parameters.

Tables
------
``model_configurations``
    Registry of LLM backends, model versions, and generation parameters.

``rag_configurations``
    Versioned RAG retrieval & chunking configurations.

``verification_configurations``
    Versioned Claim Verification Engine thresholds and NLI settings.

``configuration_evaluations``
    Evaluation gate records tying a benchmark dataset & metrics to a
    candidate configuration before admin approval/activation.
"""

import enum
import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.database.session import Base


class ConfigStatus(str, enum.Enum):
    """Lifecycle status of a model, RAG, or verification configuration."""
    TESTING = "TESTING"
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"


class ConfigType(str, enum.Enum):
    """Configuration domain supported by evaluation gating."""
    MODEL = "MODEL"
    RAG = "RAG"
    VERIFICATION = "VERIFICATION"


class ModelConfiguration(Base):
    """Registered LLM configuration and lifecycle state."""
    __tablename__ = "model_configurations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False, default="1.0")
    provider = Column(String(50), nullable=False)               # groq / ollama / huggingface / openai
    model_identifier = Column(String(150), nullable=False)      # e.g. llama-3.1-8b-instant
    temperature = Column(Float, nullable=False, default=0.1)
    max_tokens = Column(Integer, nullable=False, default=1024)
    status = Column(String(20), nullable=False, default=ConfigStatus.TESTING.value, index=True)
    description = Column(Text, nullable=True)

    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    activated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    creator = relationship("User")


class RAGConfiguration(Base):
    """Versioned RAG retrieval and chunking parameters."""
    __tablename__ = "rag_configurations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False, default="1.0")
    embedding_model = Column(String(150), nullable=False, default="BAAI/bge-small-en-v1.5")
    top_k = Column(Integer, nullable=False, default=5)
    chunk_size = Column(Integer, nullable=False, default=512)
    chunk_overlap = Column(Integer, nullable=False, default=64)
    similarity_threshold = Column(Float, nullable=False, default=0.55)
    reranking_enabled = Column(Integer, nullable=False, default=1)  # 1 = True, 0 = False
    status = Column(String(20), nullable=False, default=ConfigStatus.TESTING.value, index=True)
    description = Column(Text, nullable=True)

    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    activated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    creator = relationship("User")


class VerificationConfiguration(Base):
    """Versioned Claim Verification Engine (NLI + abstention) parameters."""
    __tablename__ = "verification_configurations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False, default="1.0")
    nli_model = Column(String(150), nullable=False, default="MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli")
    supported_threshold = Column(Float, nullable=False, default=0.70)
    contradiction_threshold = Column(Float, nullable=False, default=0.65)
    max_retries = Column(Integer, nullable=False, default=2)
    abstention_enabled = Column(Integer, nullable=False, default=1)  # 1 = True, 0 = False
    status = Column(String(20), nullable=False, default=ConfigStatus.TESTING.value, index=True)
    description = Column(Text, nullable=True)

    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    activated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    creator = relationship("User")


class ConfigurationEvaluation(Base):
    """
    Evaluation gate audit record for a Model, RAG, or Verification config.
    """
    __tablename__ = "configuration_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    config_type = Column(String(20), nullable=False, index=True)   # MODEL / RAG / VERIFICATION
    config_id = Column(Integer, nullable=False, index=True)
    evaluation_dataset = Column(String(150), nullable=False)
    metrics_json = Column(Text, nullable=False)                     # JSON metrics payload
    passed_gate = Column(Integer, nullable=False, default=0)        # 1 = passed, 0 = failed

    evaluated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    evaluator = relationship("User", foreign_keys=[evaluated_by])
    approver = relationship("User", foreign_keys=[approved_by])
