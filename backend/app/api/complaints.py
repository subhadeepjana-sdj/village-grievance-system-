import random
import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.database.mongodb import mongodb_service
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.department import Department
from app.models.complaint import Complaint, ComplaintStatus, ComplaintPriority, ComplaintStatusHistory
from app.schemas.complaint import ComplaintOut, ComplaintUpdate, ComplaintStatusHistoryOut
from app.utils.file_upload import save_uploaded_file

router = APIRouter(prefix="/complaints", tags=["Complaints"])

def generate_complaint_number() -> str:
    year = datetime.datetime.now().year
    seq = random.randint(100000, 999999)
    return f"GRV-{year}-{seq}"

@router.post("", response_model=ComplaintOut)
def create_complaint(
    category: str = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    location: Optional[str] = Form(None),
    village_id: Optional[int] = Form(None),
    priority: Optional[str] = Form("MEDIUM"),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    file_rel_path = None
    if file and file.filename:
        _, file_rel_path = save_uploaded_file(file, subfolder="complaints", use_mongo_url=True)

    c_num = generate_complaint_number()
    p_enum = ComplaintPriority[priority.upper()] if priority and priority.upper() in ComplaintPriority.__members__ else ComplaintPriority.MEDIUM

    complaint = Complaint(
        complaint_number=c_num,
        user_id=current_user.id,
        village_id=village_id or current_user.village_id,
        category=category,
        title=title,
        description=description,
        location=location,
        status=ComplaintStatus.SUBMITTED,
        priority=p_enum,
        file_path=file_rel_path
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    # Initial status history record
    history = ComplaintStatusHistory(
        complaint_id=complaint.id,
        old_status=None,
        new_status=ComplaintStatus.SUBMITTED.value,
        changed_by=current_user.name,
        remarks="Complaint submitted by citizen."
    )
    db.add(history)
    db.commit()

    # Mirror full complaint snapshot & audit event to MongoDB (no-op if disabled)
    out = _build_complaint_out(complaint)
    _mirror_complaint_to_mongo(out, citizen_email=current_user.email)
    mongodb_service.log_audit_event({
        "event_type": "USER_ACTION",
        "action": "CREATE",
        "entity_type": "complaint",
        "entity_id": complaint.complaint_number,
        "actor_id": current_user.id,
        "actor_role": current_user.role.value,
        "description": f"Complaint {complaint.complaint_number} created",
    })

    # Prepare response data
    return out

@router.get("", response_model=List[ComplaintOut])
def get_complaints(
    status_filter: Optional[str] = None,
    category_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Complaint)

    # Role-based Authorization Scoping
    if current_user.role == UserRole.CITIZEN:
        query = query.filter(Complaint.user_id == current_user.id)
    elif current_user.role == UserRole.DEPARTMENT_OFFICIAL:
        if current_user.department_id:
            query = query.filter(Complaint.department_id == current_user.department_id)
    # PANCHAYAT_STAFF, ADMIN, RESEARCHER see all village complaints

    if status_filter:
        query = query.filter(Complaint.status == status_filter.upper())
    if category_filter:
        query = query.filter(Complaint.category.ilike(f"%{category_filter}%"))

    sql_complaints = query.order_by(Complaint.created_at.desc()).all()
    merged: Dict[str, ComplaintOut] = {}
    for c in sql_complaints:
        built = _build_complaint_out(c)
        merged[built.complaint_number] = built

    if mongodb_service.connected:
        mongo_docs = mongodb_service.list_complaints(
            role=current_user.role.value,
            user_id=current_user.id,
            user_email=current_user.email,
            department_id=current_user.department_id,
            status_filter=status_filter,
            category_filter=category_filter,
        )
        for doc in mongo_docs:
            cnum = doc.get("complaint_number")
            if not cnum:
                continue
            mongo_out = _mongo_doc_to_complaint_out(doc)
            existing = merged.get(cnum)
            if existing is None or str(mongo_out.updated_at) >= str(existing.updated_at):
                merged[cnum] = mongo_out

    results = list(merged.values())
    results.sort(key=lambda item: item.created_at, reverse=True)
    return results

@router.get("/{complaint_id}", response_model=ComplaintOut)
def get_complaint_by_id(
    complaint_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    c = None
    if complaint_id.isdigit():
        c = db.query(Complaint).filter(Complaint.id == int(complaint_id)).first()
    if not c:
        c = db.query(Complaint).filter(Complaint.complaint_number.ilike(complaint_id)).first()

    if c:
        if current_user.role == UserRole.CITIZEN and c.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Unauthorized access to this complaint.")
        return _build_complaint_out(c)

    if mongodb_service.connected:
        doc = mongodb_service.get_complaint(complaint_id)
        if doc:
            if current_user.role == UserRole.CITIZEN:
                if doc.get("user_id") != current_user.id and doc.get("citizen_email") != current_user.email:
                    raise HTTPException(status_code=403, detail="Unauthorized access to this complaint.")
            return _mongo_doc_to_complaint_out(doc)

    raise HTTPException(status_code=404, detail="Complaint not found")

@router.patch("/{complaint_id}", response_model=ComplaintOut)
def update_complaint(
    complaint_id: str,
    update_data: ComplaintUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Enforce role permission
    if current_user.role == UserRole.CITIZEN:
        raise HTTPException(status_code=403, detail="Citizens cannot directly modify complaint status or department assignment.")

    c = None
    if complaint_id.isdigit():
        c = db.query(Complaint).filter(Complaint.id == int(complaint_id)).first()
    if not c:
        c = db.query(Complaint).filter(Complaint.complaint_number.ilike(complaint_id)).first()

    if c:
        old_st = c.status.value if hasattr(c.status, 'value') else c.status

        if update_data.status:
            c.status = ComplaintStatus[update_data.status.upper()]
        if update_data.department_id is not None:
            c.department_id = update_data.department_id
        if update_data.priority:
            c.priority = ComplaintPriority[update_data.priority.upper()]

        c.updated_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(c)

        new_st = c.status.value if hasattr(c.status, 'value') else c.status

        # Record status history audit
        history = ComplaintStatusHistory(
            complaint_id=c.id,
            old_status=old_st,
            new_status=new_st,
            changed_by=f"{current_user.name} ({current_user.role.value})",
            remarks=update_data.remarks or f"Status updated to {new_st}"
        )
        db.add(history)
        db.commit()

        built = _build_complaint_out(c)
        citizen_email = c.citizen.email if c.citizen else None
        _mirror_complaint_to_mongo(built, citizen_email=citizen_email)
        mongodb_service.log_audit_event({
            "event_type": "ADMIN_ACTION",
            "action": "UPDATE",
            "entity_type": "complaint",
            "entity_id": c.complaint_number,
            "actor_id": current_user.id,
            "actor_role": current_user.role.value,
            "old_value": old_st,
            "new_value": new_st,
            "description": update_data.remarks or f"Status updated to {new_st}",
        })
        return built

    # Cross-container fallback: update directly in MongoDB when complaint lives in MongoDB
    if mongodb_service.connected:
        doc = mongodb_service.get_complaint(complaint_id)
        if doc:
            old_st = str(doc.get("status") or "SUBMITTED")
            now = datetime.datetime.now(datetime.UTC)
            fields_to_set: Dict[str, Any] = {"updated_at": now}
            if update_data.status:
                fields_to_set["status"] = ComplaintStatus[update_data.status.upper()].value
            if update_data.department_id is not None:
                fields_to_set["department_id"] = update_data.department_id
                dept = db.query(Department).filter(Department.id == update_data.department_id).first()
                if dept:
                    fields_to_set["department_name"] = dept.name
            if update_data.priority:
                fields_to_set["priority"] = ComplaintPriority[update_data.priority.upper()].value

            new_st = fields_to_set.get("status", old_st)
            history_entry = {
                "old_status": old_st,
                "new_status": new_st,
                "changed_by": f"{current_user.name} ({current_user.role.value})",
                "remarks": update_data.remarks or f"Status updated to {new_st}",
                "timestamp": now,
            }
            updated_doc = mongodb_service.update_complaint_doc(complaint_id, fields_to_set, history_entry)
            if updated_doc:
                mongodb_service.log_audit_event({
                    "event_type": "ADMIN_ACTION",
                    "action": "UPDATE",
                    "entity_type": "complaint",
                    "entity_id": updated_doc.get("complaint_number", complaint_id),
                    "actor_id": current_user.id,
                    "actor_role": current_user.role.value,
                    "old_value": old_st,
                    "new_value": new_st,
                    "description": update_data.remarks or f"Status updated to {new_st}",
                })
                return _mongo_doc_to_complaint_out(updated_doc)

    raise HTTPException(status_code=404, detail="Complaint not found")

@router.get("/{complaint_id}/history", response_model=List[ComplaintStatusHistoryOut])
def get_complaint_history(
    complaint_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    c = None
    if complaint_id.isdigit():
        c = db.query(Complaint).filter(Complaint.id == int(complaint_id)).first()
    if not c:
        c = db.query(Complaint).filter(Complaint.complaint_number.ilike(complaint_id)).first()
    if c:
        return db.query(ComplaintStatusHistory).filter(ComplaintStatusHistory.complaint_id == c.id).order_by(ComplaintStatusHistory.timestamp.asc()).all()

    if mongodb_service.connected:
        doc = mongodb_service.get_complaint(complaint_id)
        if doc:
            return _mongo_doc_to_complaint_out(doc).history

    raise HTTPException(status_code=404, detail="Complaint not found")

def _mirror_complaint_to_mongo(out: ComplaintOut, citizen_email: Optional[str] = None) -> None:
    payload = out.model_dump()
    payload["status"] = out.status.value if hasattr(out.status, "value") else str(out.status)
    payload["priority"] = out.priority.value if hasattr(out.priority, "value") else str(out.priority)
    if citizen_email:
        payload["citizen_email"] = citizen_email
    mongodb_service.upsert_complaint(payload)

def _mongo_doc_to_complaint_out(doc: Dict[str, Any]) -> ComplaintOut:
    raw_st = str(doc.get("status") or "SUBMITTED").upper()
    st_enum = ComplaintStatus[raw_st] if raw_st in ComplaintStatus.__members__ else ComplaintStatus.SUBMITTED
    raw_pr = str(doc.get("priority") or "MEDIUM").upper()
    pr_enum = ComplaintPriority[raw_pr] if raw_pr in ComplaintPriority.__members__ else ComplaintPriority.MEDIUM

    now = datetime.datetime.now(datetime.UTC)
    created_at = doc.get("created_at") or now
    updated_at = doc.get("updated_at") or created_at

    history_items = []
    for idx, h in enumerate(doc.get("history") or [], start=1):
        history_items.append(
            ComplaintStatusHistoryOut(
                id=int(h.get("id") or idx),
                old_status=h.get("old_status"),
                new_status=str(h.get("new_status") or st_enum.value),
                changed_by=str(h.get("changed_by") or "System"),
                remarks=h.get("remarks"),
                timestamp=h.get("timestamp") or created_at,
            )
        )

    return ComplaintOut(
        id=int(doc.get("id") or 0),
        complaint_number=str(doc.get("complaint_number") or ""),
        user_id=int(doc.get("user_id") or 0),
        village_id=doc.get("village_id"),
        department_id=doc.get("department_id"),
        category=str(doc.get("category") or "Other"),
        title=str(doc.get("title") or ""),
        description=str(doc.get("description") or ""),
        location=doc.get("location"),
        status=st_enum,
        priority=pr_enum,
        file_path=doc.get("file_path"),
        created_at=created_at,
        updated_at=updated_at,
        citizen_name=doc.get("citizen_name") or "Citizen",
        department_name=doc.get("department_name") or "Unassigned",
        village_name=doc.get("village_name") or "Gram Panchayat",
        history=history_items,
    )

def _build_complaint_out(c: Complaint) -> ComplaintOut:
    return ComplaintOut(
        id=c.id,
        complaint_number=c.complaint_number,
        user_id=c.user_id,
        village_id=c.village_id,
        department_id=c.department_id,
        category=c.category,
        title=c.title,
        description=c.description,
        location=c.location,
        status=c.status,
        priority=c.priority,
        file_path=c.file_path,
        created_at=c.created_at,
        updated_at=c.updated_at,
        citizen_name=c.citizen.name if c.citizen else "Citizen",
        department_name=c.department.name if c.department else "Unassigned",
        village_name=c.village.name if c.village else "Gram Panchayat",
        history=[
            ComplaintStatusHistoryOut(
                id=h.id,
                old_status=h.old_status,
                new_status=h.new_status,
                changed_by=h.changed_by,
                remarks=h.remarks,
                timestamp=h.timestamp
            )
            for h in c.history
        ]
    )
