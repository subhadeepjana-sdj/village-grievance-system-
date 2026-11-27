import os
# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Evidence-Grounded AI Village Grievance Redressal System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    # Database
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "village_grievance")
    
    # Primary DB URL (SQLite fallback supported in session.py if Postgres is offline)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

    # Security
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-key-for-village-grievance-system-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Vector DB
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_COLLECTION: str = "village_knowledge_base"

    # AI / LLM Configuration
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", os.getenv("GEMINI_API_KEY", ""))
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-2.5-flash")
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    
    # Uploads (use /tmp when running on Vercel read-only serverless filesystem)
    UPLOAD_DIR: str = (
        "/tmp/village_uploads"
        if os.getenv("VERCEL")
        else os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "uploads"))
    )

    class Config:
        case_sensitive = True

settings = Settings()
