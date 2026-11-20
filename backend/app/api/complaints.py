import random
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.auth import get_current_user
from app.models.user import User, UserRole
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
        _, file_rel_path = save_uploaded_file(file, subfolder="complaints")

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

    # Prepare response data
    return _build_complaint_out(complaint)

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

    complaints = query.order_by(Complaint.created_at.desc()).all()
    return [_build_complaint_out(c) for c in complaints]

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
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Authorization check
    if current_user.role == UserRole.CITIZEN and c.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access to this complaint.")

    return _build_complaint_out(c)

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
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")

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

    return _build_complaint_out(c)

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
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")

    histories = db.query(ComplaintStatusHistory).filter(ComplaintStatusHistory.complaint_id == c.id).order_by(ComplaintStatusHistory.timestamp.asc()).all()
    return histories

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
