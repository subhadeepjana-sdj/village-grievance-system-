from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from app.models.complaint import ComplaintStatus, ComplaintPriority

class ComplaintCreate(BaseModel):
    category: str
    title: str
    description: str
    location: Optional[str] = None
    village_id: Optional[int] = None
    priority: Optional[ComplaintPriority] = ComplaintPriority.MEDIUM

class ComplaintUpdate(BaseModel):
    status: Optional[ComplaintStatus] = None
    department_id: Optional[int] = None
    priority: Optional[ComplaintPriority] = None
    remarks: Optional[str] = None

class ComplaintStatusHistoryOut(BaseModel):
    id: int
    old_status: Optional[str] = None
    new_status: str
    changed_by: str
    remarks: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class ComplaintOut(BaseModel):
    id: int
    complaint_number: str
    user_id: int
    village_id: Optional[int] = None
    department_id: Optional[int] = None
    category: str
    title: str
    description: str
    location: Optional[str] = None
    status: ComplaintStatus
    priority: ComplaintPriority
    file_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Nested relations display
    citizen_name: Optional[str] = None
    department_name: Optional[str] = None
    village_name: Optional[str] = None
    history: List[ComplaintStatusHistoryOut] = []

    class Config:
        from_attributes = True
