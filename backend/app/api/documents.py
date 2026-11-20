import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.document import Document
from app.schemas.document import DocumentOut
from app.utils.file_upload import save_uploaded_file
from app.services.document_parser import document_parser_service

router = APIRouter(prefix="/documents", tags=["Knowledge Base Documents"])

@router.post("", response_model=DocumentOut)
def upload_document(
    title: str = Form(...),
    department: Optional[str] = Form(None),
    village: Optional[str] = Form(None),
    source: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    version: Optional[str] = Form("1.0"),
    effective_date: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.PANCHAYAT_STAFF, UserRole.RESEARCHER]:
        raise HTTPException(status_code=403, detail="Only Admin, Staff or Researcher can upload knowledge documents.")

    abs_path, rel_path = save_uploaded_file(file, subfolder="kb_documents")
    ext = os.path.splitext(file.filename)[1].upper().replace(".", "")

    doc = Document(
        title=title,
        file_path=rel_path,
        document_type=ext,
        source=source or title,
        department=department,
        village=village,
        version=version or "1.0",
        effective_date=effective_date,
        uploaded_by=current_user.name
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Trigger Text Extraction -> Chunking -> Vector Embedding -> Qdrant Indexing
    chunks_count = document_parser_service.process_and_index_document(
        file_path=abs_path,
        document_id=doc.id,
        title=title,
        department=department or "",
        village=village or "",
        source=source or title,
        category=category or "",
        version=version or "1.0",
        effective_date=effective_date or ""
    )

    return doc

@router.get("", response_model=List[DocumentOut])
def get_documents(db: Session = Depends(get_db)):
    return db.query(Document).order_by(Document.created_at.desc()).all()
