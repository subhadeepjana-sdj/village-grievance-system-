from typing import Optional
from pydantic import BaseModel, EmailStr
from app.models.user import UserRole

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    name: str
    phone: Optional[str] = None
    email: EmailStr
    password: str
    role: Optional[UserRole] = UserRole.CITIZEN
    village_id: Optional[int] = None
    department_id: Optional[int] = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    name: str
    email: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    user_id: Optional[int] = None
