from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class DocumentOut(BaseModel):
    id: int
    title: str
    file_path: str
    document_type: str
    source: Optional[str] = None
    department: Optional[str] = None
    village: Optional[str] = None
    version: str
    effective_date: Optional[str] = None
    uploaded_by: Optional[str] = None
    created_at: datetime

    # RAG enhancement fields
    file_hash: Optional[str] = None
    status: str = "pending"
    chunks_count: Optional[int] = 0
    indexed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
