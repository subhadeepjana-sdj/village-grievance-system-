"""
Media Serving Router (`GET /api/media/{media_id}`).

Streams uploaded complaint evidence images and documents persisted in MongoDB
so attachments survive stateless serverless restarts (e.g. Vercel).
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.database.mongodb import mongodb_service

router = APIRouter(prefix="/media", tags=["Media Storage"])


@router.get("/{media_id}")
def get_media_file(media_id: str):
    doc = mongodb_service.get_media(media_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Media file not found or MongoDB not connected.")

    content = bytes(doc["data"])
    content_type = doc.get("content_type") or "application/octet-stream"
    filename = doc.get("filename") or media_id
    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
