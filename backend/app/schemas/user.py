from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr
from app.models.user import UserRole

class UserOut(BaseModel):
    id: int
    name: str
    phone: Optional[str] = None
    email: EmailStr
    role: UserRole
    village_id: Optional[int] = None
    department_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
