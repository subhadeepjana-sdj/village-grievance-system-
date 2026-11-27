"""
Feature 12 — Model & RAG Management Pydantic Schemas.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.model_config import ConfigType


# ------------------------------------------------------------------ #
#  Model Configuration                                                #
# ------------------------------------------------------------------ #

class ModelConfigCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    version: str = Field("1.0", max_length=50)
    provider: str = Field(..., min_length=2, max_length=50)
    model_identifier: str = Field(..., min_length=2, max_length=150)
    temperature: float = Field(0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(1024, ge=64, le=32768)
    description: Optional[str] = None


class ModelConfigOut(BaseModel):
    id: int
    name: str
    version: str
    provider: str
    model_identifier: str
    temperature: float
    max_tokens: int
    status: str
    description: Optional[str] = None
    created_by: Optional[int] = None
    activated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ------------------------------------------------------------------ #
#  RAG Configuration                                                  #
# ------------------------------------------------------------------ #

class RAGConfigCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    version: str = Field("1.0", max_length=50)
    embedding_model: str = Field("BAAI/bge-small-en-v1.5", max_length=150)
    top_k: int = Field(5, ge=1, le=50)
    chunk_size: int = Field(512, ge=64, le=4096)
    chunk_overlap: int = Field(64, ge=0, le=1024)
    similarity_threshold: float = Field(0.55, ge=0.0, le=1.0)
    reranking_enabled: bool = True
    description: Optional[str] = None


class RAGConfigOut(BaseModel):
    id: int
    name: str
    version: str
    embedding_model: str
    top_k: int
    chunk_size: int
    chunk_overlap: int
    similarity_threshold: float
    reranking_enabled: int
    status: str
    description: Optional[str] = None
    created_by: Optional[int] = None
    activated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ------------------------------------------------------------------ #
#  Verification Configuration                                         #
# ------------------------------------------------------------------ #

class VerificationConfigCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    version: str = Field("1.0", max_length=50)
    nli_model: str = Field("MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli", max_length=150)
    supported_threshold: float = Field(0.70, ge=0.0, le=1.0)
    contradiction_threshold: float = Field(0.65, ge=0.0, le=1.0)
    max_retries: int = Field(2, ge=0, le=10)
    abstention_enabled: bool = True
    description: Optional[str] = None


class VerificationConfigOut(BaseModel):
    id: int
    name: str
    version: str
    nli_model: str
    supported_threshold: float
    contradiction_threshold: float
    max_retries: int
    abstention_enabled: int
    status: str
    description: Optional[str] = None
    created_by: Optional[int] = None
    activated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ------------------------------------------------------------------ #
#  Evaluation & Approval                                              #
# ------------------------------------------------------------------ #

class EvaluateConfigRequest(BaseModel):
    evaluation_dataset: str = Field("village_grievance_benchmark_v1", max_length=150)
    factual_accuracy: float = Field(..., ge=0.0, le=1.0)
    hallucination_rate: float = Field(..., ge=0.0, le=1.0)
    faithfulness: float = Field(..., ge=0.0, le=1.0)
    abstention_accuracy: float = Field(0.90, ge=0.0, le=1.0)
    avg_latency_ms: float = Field(500.0, ge=0.0)
    notes: Optional[str] = None


class ConfigurationEvaluationOut(BaseModel):
    id: int
    config_type: str
    config_id: int
    evaluation_dataset: str
    metrics_json: str
    passed_gate: int
    evaluated_by: Optional[int] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ApproveConfigRequest(BaseModel):
    notes: Optional[str] = None


class ActiveConfigBundleOut(BaseModel):
    """Unified view of the currently active AI pipeline configurations."""
    active_model: Optional[ModelConfigOut] = None
    active_rag: Optional[RAGConfigOut] = None
    active_verification: Optional[VerificationConfigOut] = None
