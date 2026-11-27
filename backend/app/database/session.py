import os
import sys
import logging

# Ensure site-packages loaded
user_site = os.path.expanduser(r"~\AppData\Roaming\Python\Python314\site-packages")
if os.path.exists(user_site) and user_site not in sys.path:
    sys.path.insert(0, user_site)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

logger = logging.getLogger("uvicorn.error")

Base = declarative_base()

# Attempt Postgres connection first; fallback gracefully to SQLite if Postgres is unavailable
def get_engine():
    db_url = settings.DATABASE_URL
    try:
        if "postgresql" in db_url:
            engine = create_engine(db_url, pool_pre_ping=True, connect_args={"connect_timeout": 3})
            connection = engine.connect()
            connection.close()
            logger.info("Successfully connected to PostgreSQL database.")
            return engine
    except Exception as e:
        logger.warning(f"Could not connect to PostgreSQL ({e}). Falling back to SQLite database.")

    db_dir = (
        "/tmp/village_data"
        if os.getenv("VERCEL")
        else os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
    )
    os.makedirs(db_dir, exist_ok=True)
    sqlite_url = f"sqlite:///{os.path.join(db_dir, 'village_grievance.db')}"
    logger.info(f"Using SQLite database at: {sqlite_url}")
    return create_engine(sqlite_url, connect_args={"check_same_thread": False})

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
