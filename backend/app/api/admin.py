from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.database.mongodb import mongodb_service
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.complaint import Complaint, ComplaintStatus
from app.models.document import Document
from app.models.ai_records import AIQuery, AIResponse

router = APIRouter(prefix="/admin", tags=["Admin Statistics"])

@router.get("/statistics")
def get_admin_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.PANCHAYAT_STAFF, UserRole.RESEARCHER]:
        raise HTTPException(status_code=403, detail="Admin or Staff authorization required.")

    total_users = db.query(User).count()
    sql_complaints = db.query(Complaint).all()

    # Merge SQLAlchemy complaints with MongoDB complaints (deduplicated by complaint_number)
    merged_complaints = {}
    for c in sql_complaints:
        st_val = c.status.value if hasattr(c.status, "value") else str(c.status)
        merged_complaints[c.complaint_number] = st_val.upper()

    if mongodb_service.connected:
        for doc in mongodb_service.list_complaints(role="ADMIN"):
            cnum = doc.get("complaint_number")
            if cnum:
                merged_complaints[cnum] = str(doc.get("status") or "SUBMITTED").upper()

    statuses = list(merged_complaints.values())
    total_complaints = len(statuses)
    pending_complaints = sum(1 for st in statuses if st in ("SUBMITTED", "ACKNOWLEDGED", "ASSIGNED"))
    in_progress_complaints = sum(1 for st in statuses if st in ("UNDER_REVIEW", "IN_PROGRESS"))
    resolved_complaints = sum(1 for st in statuses if st == "RESOLVED")
    total_documents = db.query(Document).count()

    if mongodb_service.connected:
        mongo_users = len(mongodb_service._iter_collection("users"))
        if mongo_users > total_users:
            total_users = mongo_users
        mongo_docs = len(mongodb_service._iter_collection("kb_documents"))
        if mongo_docs > total_documents:
            total_documents = mongo_docs

    total_ai_queries = db.query(AIQuery).count()
    ai_responses = db.query(AIResponse).all()

    if ai_responses:
        total_resp_count = len(ai_responses)
        supported_count = sum(1 for r in ai_responses if r.decision in ["SHOW", "SUPPORTED"])
        contradiction_count = sum(1 for r in ai_responses if r.decision in ["CORRECT", "CONTRADICTED"])
        abstain_count = sum(1 for r in ai_responses if r.decision in ["ABSTAIN", "INSUFFICIENT_EVIDENCE"])
        avg_conf = sum(r.confidence for r in ai_responses) / total_resp_count
        avg_lat = sum(r.processing_time for r in ai_responses) / total_resp_count
    elif mongodb_service.connected:
        traces = mongodb_service.list_ai_traces(limit=500)
        total_resp_count = len(traces)
        total_ai_queries = max(total_ai_queries, total_resp_count)
        supported_count = sum(1 for t in traces if t.get("decision") in ["SHOW", "SUPPORTED"])
        contradiction_count = sum(1 for t in traces if t.get("decision") in ["CORRECT", "CONTRADICTED"])
        abstain_count = sum(1 for t in traces if t.get("decision") in ["ABSTAIN", "INSUFFICIENT_EVIDENCE"])
        avg_conf = (sum(float(t.get("confidence", 0.0)) for t in traces) / total_resp_count) if total_resp_count else 0.0
        avg_lat = (sum(float(t.get("processing_time", 0.0)) for t in traces) / total_resp_count) if total_resp_count else 0.0
    else:
        total_resp_count = 0
        supported_count = 0
        contradiction_count = 0
        abstain_count = 0
        avg_conf = 0.0
        avg_lat = 0.0

    denom = total_resp_count if total_resp_count > 0 else 1

    return {
        "summary": {
            "total_users": total_users,
            "total_complaints": total_complaints,
            "pending_complaints": pending_complaints,
            "in_progress_complaints": in_progress_complaints,
            "resolved_complaints": resolved_complaints,
            "total_documents": total_documents
        },
        "ai_statistics": {
            "total_ai_questions": total_ai_queries,
            "supported_percentage": round((supported_count / denom) * 100.0, 1) if total_resp_count > 0 else 0.0,
            "contradicted_percentage": round((contradiction_count / denom) * 100.0, 1) if total_resp_count > 0 else 0.0,
            "abstain_percentage": round((abstain_count / denom) * 100.0, 1) if total_resp_count > 0 else 0.0,
            "average_confidence": round(avg_conf, 1) if total_resp_count > 0 else 0.0,
            "average_response_time": round(avg_lat, 2) if total_resp_count > 0 else 0.0
        }
    }
