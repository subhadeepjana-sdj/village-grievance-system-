import os
import datetime
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
from app.services.qdrant_service import qdrant_service
from app.config import settings

router = APIRouter(prefix="/documents", tags=["Knowledge Base Documents"])


# ------------------------------------------------------------------ #
#  POST /api/documents  — upload + index                              #
# ------------------------------------------------------------------ #
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

    # --- Duplicate detection via SHA-256 file hash ---
    file_hash = document_parser_service.compute_file_hash(abs_path)
    existing = db.query(Document).filter(Document.file_hash == file_hash).first()
    if existing:
        # Clean up the just-saved duplicate before raising
        try:
            os.remove(abs_path)
        except OSError:
            pass
        raise HTTPException(
            status_code=409,
            detail=f"Document already exists (id={existing.id}, title='{existing.title}'). "
                   "Use POST /api/documents/{id}/index to re-index it."
        )

    doc = Document(
        title=title,
        file_path=rel_path,
        document_type=ext,
        source=source or title,
        department=department,
        village=village,
        version=version or "1.0",
        effective_date=effective_date,
        uploaded_by=current_user.name,
        file_hash=file_hash,
        status="pending",
        chunks_count=0
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Trigger: Extract → Token-chunk → Embed → Qdrant upsert
    try:
        chunks_count = document_parser_service.process_and_index_document(
            file_path=abs_path,
            document_id=doc.id,
            title=title,
            department=department or "",
            village=village or "",
            source=source or title,
            category=category or "",
            version=version or "1.0",
            effective_date=effective_date or "",
            status="verified"
        )
        doc.status = "indexed"
        doc.chunks_count = chunks_count
        doc.indexed_at = datetime.datetime.now(datetime.UTC)
    except Exception as e:
        doc.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Document saved but indexing failed: {e}")

    db.commit()
    db.refresh(doc)
    return doc


# ------------------------------------------------------------------ #
#  GET /api/documents                                                 #
# ------------------------------------------------------------------ #
@router.get("", response_model=List[DocumentOut])
def get_documents(db: Session = Depends(get_db)):
    return db.query(Document).order_by(Document.created_at.desc()).all()


# ------------------------------------------------------------------ #
#  DELETE /api/documents/{doc_id} — delete record + Qdrant chunks    #
# ------------------------------------------------------------------ #
@router.delete("/{doc_id}", status_code=204)
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    if current_user.role not in [UserRole.ADMIN, UserRole.PANCHAYAT_STAFF]:
        raise HTTPException(status_code=403, detail="Only Admin or Panchayat Staff can delete documents.")

    # 1. Remove all Qdrant vector chunks so stale embeddings don't persist
    qdrant_service.delete_document_chunks(doc_id)

    # 2. Optionally remove the uploaded file from disk
    try:
        abs_path = os.path.join(settings.UPLOAD_DIR, doc.file_path)
        if os.path.isfile(abs_path):
            os.remove(abs_path)
    except OSError:
        pass  # Non-fatal — log and continue

    # 3. Delete DB record
    db.delete(doc)
    db.commit()


# ------------------------------------------------------------------ #
#  POST /api/documents/{doc_id}/index — explicit re-index            #
# ------------------------------------------------------------------ #
@router.post("/{doc_id}/index", response_model=DocumentOut)
def reindex_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Re-index an existing document:
      1. Delete its current Qdrant chunks.
      2. Re-extract text, re-chunk (token-based), re-embed, re-upsert.
      3. Update status/chunks_count/indexed_at on the Document record.

    Useful after the chunking strategy or embedding model is updated.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.PANCHAYAT_STAFF]:
        raise HTTPException(status_code=403, detail="Only Admin or Panchayat Staff can re-index documents.")

    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    abs_path = os.path.join(settings.UPLOAD_DIR, doc.file_path)
    if not os.path.isfile(abs_path):
        raise HTTPException(status_code=422, detail=f"Source file not found on disk: {doc.file_path}")

    # Step 1: wipe stale vectors
    qdrant_service.delete_document_chunks(doc_id)
    doc.status = "pending"
    db.commit()

    # Step 2: re-index
    try:
        chunks_count = document_parser_service.process_and_index_document(
            file_path=abs_path,
            document_id=doc.id,
            title=doc.title,
            department=doc.department or "",
            village=doc.village or "",
            source=doc.source or doc.title,
            category="",
            version=doc.version,
            effective_date=doc.effective_date or "",
            status="verified"
        )
        doc.status = "indexed"
        doc.chunks_count = chunks_count
        doc.indexed_at = datetime.datetime.now(datetime.UTC)
    except Exception as e:
        doc.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Re-indexing failed: {e}")

    db.commit()
    db.refresh(doc)
    return doc
