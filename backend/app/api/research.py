from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.ai_records import ResearchMetric
from app.schemas.research import ResearchRunResponse, ResearchMetricsOut
from app.evaluation.evaluator import research_evaluator

router = APIRouter(prefix="/research", tags=["Research & Evaluation"])

@router.post("/run", response_model=ResearchRunResponse)
def run_research_experiment(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.RESEARCHER, UserRole.PANCHAYAT_STAFF]:
        raise HTTPException(status_code=403, detail="Only Researcher, Staff or Admin can execute experimental benchmark runs.")

    res = research_evaluator.run_comparative_experiment(db)
    return res

@router.get("/metrics", response_model=List[ResearchMetricsOut])
def get_latest_metrics(
    db: Session = Depends(get_db)
):
    metrics = db.query(ResearchMetric).order_by(ResearchMetric.timestamp.desc()).limit(15).all()
    return metrics
