from typing import Optional
from pydantic import BaseModel

class DepartmentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    contact_information: Optional[str] = None

class DepartmentOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    contact_information: Optional[str] = None

    class Config:
        from_attributes = True
