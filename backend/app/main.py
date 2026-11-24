import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database.session import engine, Base
from app.database.seed_data import seed_database
from app.api import auth, users, complaints, departments, documents, ai, admin, research, verification_center

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn.error")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Evidence-Grounded AI Village Grievance Redressal System API"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded files statically
uploads_dir = settings.UPLOAD_DIR
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# Include Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(complaints.router, prefix=settings.API_V1_STR)
app.include_router(departments.router, prefix=settings.API_V1_STR)
app.include_router(documents.router, prefix=settings.API_V1_STR)
app.include_router(ai.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)
app.include_router(verification_center.router, prefix=settings.API_V1_STR)
app.include_router(research.router, prefix=settings.API_V1_STR)

@app.on_event("startup")
def startup_event():
    logger.info("Initializing database tables & seeding initial data...")
    try:
        seed_database()
    except Exception as e:
        logger.error(f"Error seeding database: {e}")

@app.get("/")
def root():
    return {
        "message": "Welcome to Evidence-Grounded AI Village Grievance Redressal System API",
        "docs": "/docs",
        "version": settings.VERSION
    }

@app.get("/api/health")
@app.get("/health")
def health():
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "database": "connected"
    }
