import os
import uuid
from typing import Tuple
from fastapi import UploadFile, HTTPException, status
from app.config import settings

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
    "image/jpeg",
    "image/png",
    "image/jpg",
    "image/webp"
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

def save_uploaded_file(file: UploadFile, subfolder: str = "documents") -> Tuple[str, str]:
    # 1. Check extension
    filename = file.filename or "uploaded_file"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{ext}'. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # 2. Check MIME type (soft validation for standard web uploads)
    content_type = file.content_type or ""
    if content_type and content_type not in ALLOWED_MIME_TYPES:
        # Warning/fallback check if octet-stream
        if content_type != "application/octet-stream":
            logger_msg = f"Non-standard MIME type: {content_type}"

    # 3. Read content and validate size
    contents = file.file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum limit of {MAX_FILE_SIZE / (1024*1024)} MB."
        )

    # 4. Generate safe unique filename
    target_dir = os.path.join(settings.UPLOAD_DIR, subfolder)
    os.makedirs(target_dir, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}{ext}"
    target_path = os.path.join(target_dir, unique_name)

    # 5. Save to disk securely
    with open(target_path, "wb") as f:
        f.write(contents)

    rel_path = os.path.join("uploads", subfolder, unique_name).replace("\\", "/")
    return target_path, rel_path
