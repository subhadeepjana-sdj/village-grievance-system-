"""
Feature 12 — Model & RAG Management REST API.

Endpoints (all under ``/api/admin``):

Model registry:
  GET  /models                                   — List registered LLM configurations.
  POST /models                                   — Register a new LLM configuration (TESTING).
  PUT  /models/{model_id}/activate               — Activate model if evaluation gate passed.

RAG configurations:
  GET  /rag-config                               — List RAG configurations.
  GET  /rag-config/active                        — Get active Model + RAG + Verification bundle.
  POST /rag-config                               — Create a versioned RAG configuration (TESTING).

Verification configurations:
  GET  /verification-config                      — List verification configurations.
  POST /verification-config                      — Create a versioned verification configuration.

Evaluation gating & Admin approval:
  POST /configs/{config_type}/{config_id}/evaluate — Record evaluation & check quality gate.
  PUT  /configs/{config_type}/{config_id}/approve  — Approve & activate config (retires old active).
"""

import json
import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.model_config import (
    ModelConfiguration,
    RAGConfiguration,
    VerificationConfiguration,
    ConfigurationEvaluation,
    ConfigStatus,
    ConfigType,
)
from app.schemas.model_config import (
    ModelConfigCreate,
    ModelConfigOut,
    RAGConfigCreate,
    RAGConfigOut,
    VerificationConfigCreate,
    VerificationConfigOut,
    EvaluateConfigRequest,
    ConfigurationEvaluationOut,
    ApproveConfigRequest,
    ActiveConfigBundleOut,
)

router = APIRouter(prefix="/admin", tags=["Model & RAG Management"])

# Minimum quality thresholds for passing the promotion gate
MIN_FACTUAL_ACCURACY = 0.80
MAX_HALLUCINATION_RATE = 0.10
MIN_FAITHFULNESS = 0.80


def _require_admin(user: User) -> None:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin role required.")


def _require_admin_or_researcher(user: User) -> None:
    if user.role not in (UserRole.ADMIN, UserRole.RESEARCHER):
        raise HTTPException(status_code=403, detail="Admin or Researcher role required.")


def _get_config_model_cls(config_type: ConfigType):
    if config_type == ConfigType.MODEL:
        return ModelConfiguration
    if config_type == ConfigType.RAG:
        return RAGConfiguration
    return VerificationConfiguration


def _activate_config(db: Session, config_type: ConfigType, config_id: int, approver_id: int, notes: Optional[str] = None):
    model_cls = _get_config_model_cls(config_type)
    target = db.query(model_cls).filter(model_cls.id == config_id).first()
    if not target:
        raise HTTPException(status_code=404, detail=f"{config_type.value} configuration not found.")

    latest_passing_eval = (
        db.query(ConfigurationEvaluation)
        .filter(
            ConfigurationEvaluation.config_type == config_type.value,
            ConfigurationEvaluation.config_id == config_id,
            ConfigurationEvaluation.passed_gate == 1,
        )
        .order_by(ConfigurationEvaluation.created_at.desc())
        .first()
    )
    if not latest_passing_eval:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Evaluation gate not passed for {config_type.value} config {config_id}. "
                "Run a passing evaluation before activating."
            ),
        )

    # Retire any currently active configuration of the same domain
    active_items = (
        db.query(model_cls)
        .filter(model_cls.status == ConfigStatus.ACTIVE.value, model_cls.id != config_id)
        .all()
    )
    for item in active_items:
        item.status = ConfigStatus.RETIRED.value

    now = datetime.datetime.utcnow()
    target.status = ConfigStatus.ACTIVE.value
    target.activated_at = now

    latest_passing_eval.approved_by = approver_id
    latest_passing_eval.approved_at = now
    if notes:
        latest_passing_eval.notes = notes

    db.commit()
    db.refresh(target)
    return target


# ------------------------------------------------------------------ #
#  Model Registry                                                     #
# ------------------------------------------------------------------ #

@router.get("/models", response_model=List[ModelConfigOut], summary="List model configurations")
def list_models(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin_or_researcher(current_user)
    q = db.query(ModelConfiguration)
    if status:
        q = q.filter(ModelConfiguration.status == status.upper())
    return q.order_by(ModelConfiguration.created_at.desc()).all()


@router.post("/models", response_model=ModelConfigOut, status_code=201, summary="Register a new LLM configuration")
def register_model(
    payload: ModelConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    cfg = ModelConfiguration(
        name=payload.name,
        version=payload.version,
        provider=payload.provider,
        model_identifier=payload.model_identifier,
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
        status=ConfigStatus.TESTING.value,
        description=payload.description,
        created_by=current_user.id,
    )
    db.add(cfg)
    db.commit()
    db.refresh(cfg)
    return cfg


@router.put("/models/{model_id}/activate", response_model=ModelConfigOut, summary="Activate a registered model configuration")
def activate_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    return _activate_config(db, ConfigType.MODEL, model_id, current_user.id)


# ------------------------------------------------------------------ #
#  RAG Configuration                                                  #
# ------------------------------------------------------------------ #

@router.get("/rag-config/active", response_model=ActiveConfigBundleOut, summary="Get active Model, RAG, and Verification bundle")
def get_active_config_bundle(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin_or_researcher(current_user)
    active_model = db.query(ModelConfiguration).filter(ModelConfiguration.status == ConfigStatus.ACTIVE.value).first()
    active_rag = db.query(RAGConfiguration).filter(RAGConfiguration.status == ConfigStatus.ACTIVE.value).first()
    active_verif = db.query(VerificationConfiguration).filter(VerificationConfiguration.status == ConfigStatus.ACTIVE.value).first()
    return ActiveConfigBundleOut(
        active_model=active_model,
        active_rag=active_rag,
        active_verification=active_verif,
    )


@router.get("/rag-config", response_model=List[RAGConfigOut], summary="List RAG configurations")
def list_rag_configs(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin_or_researcher(current_user)
    q = db.query(RAGConfiguration)
    if status:
        q = q.filter(RAGConfiguration.status == status.upper())
    return q.order_by(RAGConfiguration.created_at.desc()).all()


@router.post("/rag-config", response_model=RAGConfigOut, status_code=201, summary="Create a versioned RAG configuration")
def create_rag_config(
    payload: RAGConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    cfg = RAGConfiguration(
        name=payload.name,
        version=payload.version,
        embedding_model=payload.embedding_model,
        top_k=payload.top_k,
        chunk_size=payload.chunk_size,
        chunk_overlap=payload.chunk_overlap,
        similarity_threshold=payload.similarity_threshold,
        reranking_enabled=1 if payload.reranking_enabled else 0,
        status=ConfigStatus.TESTING.value,
        description=payload.description,
        created_by=current_user.id,
    )
    db.add(cfg)
    db.commit()
    db.refresh(cfg)
    return cfg


# ------------------------------------------------------------------ #
#  Verification Configuration                                         #
# ------------------------------------------------------------------ #

@router.get("/verification-config", response_model=List[VerificationConfigOut], summary="List verification configurations")
def list_verification_configs(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin_or_researcher(current_user)
    q = db.query(VerificationConfiguration)
    if status:
        q = q.filter(VerificationConfiguration.status == status.upper())
    return q.order_by(VerificationConfiguration.created_at.desc()).all()


@router.post("/verification-config", response_model=VerificationConfigOut, status_code=201, summary="Create a verification configuration")
def create_verification_config(
    payload: VerificationConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    cfg = VerificationConfiguration(
        name=payload.name,
        version=payload.version,
        nli_model=payload.nli_model,
        supported_threshold=payload.supported_threshold,
        contradiction_threshold=payload.contradiction_threshold,
        max_retries=payload.max_retries,
        abstention_enabled=1 if payload.abstention_enabled else 0,
        status=ConfigStatus.TESTING.value,
        description=payload.description,
        created_by=current_user.id,
    )
    db.add(cfg)
    db.commit()
    db.refresh(cfg)
    return cfg


# ------------------------------------------------------------------ #
#  Evaluation Gating & Admin Approval                                 #
# ------------------------------------------------------------------ #

@router.post(
    "/configs/{config_type}/{config_id}/evaluate",
    response_model=ConfigurationEvaluationOut,
    status_code=201,
    summary="Evaluate a candidate configuration against benchmark thresholds",
)
def evaluate_configuration(
    config_type: ConfigType,
    config_id: int,
    payload: EvaluateConfigRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin_or_researcher(current_user)

    model_cls = _get_config_model_cls(config_type)
    target = db.query(model_cls).filter(model_cls.id == config_id).first()
    if not target:
        raise HTTPException(status_code=404, detail=f"{config_type.value} configuration not found.")

    passed = (
        payload.factual_accuracy >= MIN_FACTUAL_ACCURACY
        and payload.hallucination_rate <= MAX_HALLUCINATION_RATE
        and payload.faithfulness >= MIN_FAITHFULNESS
    )

    metrics = {
        "factual_accuracy": payload.factual_accuracy,
        "hallucination_rate": payload.hallucination_rate,
        "faithfulness": payload.faithfulness,
        "abstention_accuracy": payload.abstention_accuracy,
        "avg_latency_ms": payload.avg_latency_ms,
    }

    ev = ConfigurationEvaluation(
        config_type=config_type.value,
        config_id=config_id,
        evaluation_dataset=payload.evaluation_dataset,
        metrics_json=json.dumps(metrics),
        passed_gate=1 if passed else 0,
        evaluated_by=current_user.id,
        notes=payload.notes,
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev


@router.put(
    "/configs/{config_type}/{config_id}/approve",
    summary="Approve and activate a configuration after passing the evaluation gate",
)
def approve_configuration(
    config_type: ConfigType,
    config_id: int,
    payload: ApproveConfigRequest = ApproveConfigRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    activated = _activate_config(db, config_type, config_id, current_user.id, payload.notes)
    return {
        "config_type": config_type.value,
        "config_id": activated.id,
        "name": activated.name,
        "version": activated.version,
        "status": activated.status,
        "activated_at": activated.activated_at,
    }
