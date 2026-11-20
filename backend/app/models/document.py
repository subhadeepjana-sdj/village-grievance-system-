import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.database.session import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    file_path = Column(String(255), nullable=False)
    document_type = Column(String(50), nullable=False, default="PDF")
    source = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    village = Column(String(100), nullable=True)
    version = Column(String(20), nullable=False, default="1.0")
    effective_date = Column(String(50), nullable=True)
    uploaded_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # RAG enhancement fields
    file_hash = Column(String(64), nullable=True, unique=True, index=True)   # SHA-256 of file bytes — prevents duplicate indexing
    status = Column(String(20), nullable=False, default="pending")            # pending | indexed | failed
    chunks_count = Column(Integer, nullable=True, default=0)                  # number of Qdrant points created
    indexed_at = Column(DateTime, nullable=True)                              # timestamp of last successful indexing
