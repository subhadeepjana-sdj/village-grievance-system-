from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.department import Department
from app.schemas.department import DepartmentOut, DepartmentCreate
from app.api.auth import get_current_user
from app.models.user import User, UserRole

router = APIRouter(prefix="/departments", tags=["Departments"])

@router.get("", response_model=List[DepartmentOut])
def get_departments(db: Session = Depends(get_db)):
    return db.query(Department).all()

@router.post("", response_model=DepartmentOut)
def create_department(
    dept_in: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.PANCHAYAT_STAFF]:
        raise HTTPException(status_code=403, detail="Only Staff or Admin can create departments.")

    dept = Department(
        name=dept_in.name,
        description=dept_in.description,
        contact_information=dept_in.contact_information
    )
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept
