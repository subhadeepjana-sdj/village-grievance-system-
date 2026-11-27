"""
MongoDB Persistence Service (`pymongo`).

Provides durable cloud/document persistence for unstructured and high-volume
artifacts alongside SQLAlchemy:

Collections:
  - ``complaint_media`` : Uploaded grievance evidence images & attachments (binary)
  - ``complaints``      : Mirrored grievance snapshots & status history
  - ``kb_documents``    : Knowledge base files, extracted text, and version metadata
  - ``ai_traces``       : Complete AI pipeline verification, claim, citation & abstention logs
  - ``ai_feedback``     : Citizen feedback & admin root-cause review records
  - ``audit_events``    : Append-only governance & activity audit trail

Gracefully degrades to no-op when ``MONGODB_URI`` is unset or unreachable,
preserving 100% offline/test compatibility.
"""

import datetime
import logging
import uuid
from typing import Any, Dict, List, Optional

from app.config import settings

logger = logging.getLogger("uvicorn.error")


class MongoDBService:
    """Lazy, resilient MongoDB client wrapper backed by PyMongo."""

    COLLECTIONS = (
        "complaint_media",
        "complaints",
        "kb_documents",
        "ai_traces",
        "ai_feedback",
        "audit_events",
    )

    def __init__(self):
        self.client = None
        self.db = None
        self.connected = False
        self.last_error: Optional[str] = None
        self._connect()

    def _connect(self) -> None:
        uri = (settings.MONGODB_URI or "").strip()
        if not uri:
            self.last_error = "MONGODB_URI not configured"
            return

        try:
            from pymongo import MongoClient, DESCENDING

            client = MongoClient(uri, serverSelectionTimeoutMS=3000)
            client.admin.command("ping")
            db = client[settings.MONGODB_DB_NAME]

            # Ensure indexes idempotently
            db["complaint_media"].create_index("media_id", unique=True)
            db["complaints"].create_index("complaint_number", unique=True)
            db["kb_documents"].create_index("document_id")
            db["ai_traces"].create_index([("created_at", DESCENDING)])
            db["ai_feedback"].create_index("feedback_id")
            db["audit_events"].create_index([("created_at", DESCENDING)])

            self.client = client
            self.db = db
            self.connected = True
            self.last_error = None
            logger.info("Connected to MongoDB database '%s'.", settings.MONGODB_DB_NAME)
        except Exception as exc:
            self.client = None
            self.db = None
            self.connected = False
            self.last_error = str(exc)
            logger.warning("MongoDB connection skipped/failed (%s). Continuing with SQL/Qdrant.", exc)

    def refresh_connection(self) -> bool:
        """Attempt connection if not currently connected."""
        if not self.connected:
            self._connect()
        return self.connected

    # ------------------------------------------------------------------ #
    #  1. Media & Evidence Image Blobs                                    #
    # ------------------------------------------------------------------ #

    def store_media(
        self,
        content: bytes,
        filename: str,
        content_type: str,
        subfolder: str = "complaints",
        entity_ref: Optional[str] = None,
    ) -> Optional[str]:
        """Persist binary media bytes in MongoDB and return its ``media_id``."""
        if not self.connected or self.db is None:
            return None
        try:
            from bson.binary import Binary

            media_id = uuid.uuid4().hex
            self.db["complaint_media"].insert_one({
                "media_id": media_id,
                "filename": filename,
                "content_type": content_type or "application/octet-stream",
                "subfolder": subfolder,
                "entity_ref": entity_ref,
                "size_bytes": len(content),
                "data": Binary(content),
                "created_at": datetime.datetime.now(datetime.UTC),
            })
            return media_id
        except Exception as exc:
            logger.warning("MongoDB store_media failed: %s", exc)
            return None

    def get_media(self, media_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a stored media document by ``media_id``."""
        if not self.connected or self.db is None:
            return None
        try:
            return self.db["complaint_media"].find_one({"media_id": media_id}, {"_id": 0})
        except Exception as exc:
            logger.warning("MongoDB get_media failed: %s", exc)
            return None

    # ------------------------------------------------------------------ #
    #  2. Complaint Snapshots                                             #
    # ------------------------------------------------------------------ #

    def upsert_complaint(self, complaint_doc: Dict[str, Any]) -> bool:
        if not self.connected or self.db is None:
            return False
        try:
            payload = {**complaint_doc, "synced_at": datetime.datetime.now(datetime.UTC)}
            self.db["complaints"].update_one(
                {"complaint_number": complaint_doc["complaint_number"]},
                {"$set": payload},
                upsert=True,
            )
            return True
        except Exception as exc:
            logger.warning("MongoDB upsert_complaint failed: %s", exc)
            return False

    # ------------------------------------------------------------------ #
    #  3. AI Pipeline Traces & Verification Reports                       #
    # ------------------------------------------------------------------ #

    def log_ai_trace(self, trace_doc: Dict[str, Any]) -> bool:
        if not self.connected or self.db is None:
            return False
        try:
            payload = {
                **trace_doc,
                "created_at": trace_doc.get("created_at") or datetime.datetime.now(datetime.UTC),
            }
            self.db["ai_traces"].insert_one(payload)
            return True
        except Exception as exc:
            logger.warning("MongoDB log_ai_trace failed: %s", exc)
            return False

    # ------------------------------------------------------------------ #
    #  4. Knowledge Base Documents & Versions                             #
    # ------------------------------------------------------------------ #

    def store_kb_document(self, kb_doc: Dict[str, Any]) -> bool:
        if not self.connected or self.db is None:
            return False
        try:
            payload = {**kb_doc, "synced_at": datetime.datetime.now(datetime.UTC)}
            self.db["kb_documents"].update_one(
                {
                    "document_id": kb_doc.get("document_id"),
                    "version": kb_doc.get("version", "1.0"),
                },
                {"$set": payload},
                upsert=True,
            )
            return True
        except Exception as exc:
            logger.warning("MongoDB store_kb_document failed: %s", exc)
            return False

    # ------------------------------------------------------------------ #
    #  5. Citizen Feedback & Audit Events                                 #
    # ------------------------------------------------------------------ #

    def upsert_feedback(self, feedback_doc: Dict[str, Any]) -> bool:
        if not self.connected or self.db is None:
            return False
        try:
            payload = {**feedback_doc, "synced_at": datetime.datetime.now(datetime.UTC)}
            self.db["ai_feedback"].update_one(
                {"feedback_id": feedback_doc["feedback_id"]},
                {"$set": payload},
                upsert=True,
            )
            return True
        except Exception as exc:
            logger.warning("MongoDB upsert_feedback failed: %s", exc)
            return False

    def log_audit_event(self, event_doc: Dict[str, Any]) -> bool:
        if not self.connected or self.db is None:
            return False
        try:
            payload = {
                **event_doc,
                "created_at": event_doc.get("created_at") or datetime.datetime.now(datetime.UTC),
            }
            self.db["audit_events"].insert_one(payload)
            return True
        except Exception as exc:
            logger.warning("MongoDB log_audit_event failed: %s", exc)
            return False

    # ------------------------------------------------------------------ #
    #  6. Diagnostics & Health                                            #
    # ------------------------------------------------------------------ #

    def get_status(self) -> Dict[str, Any]:
        counts: Dict[str, int] = {}
        if self.connected and self.db is not None:
            for col in self.COLLECTIONS:
                try:
                    counts[col] = self.db[col].count_documents({})
                except Exception:
                    counts[col] = 0
        return {
            "enabled": bool((settings.MONGODB_URI or "").strip()),
            "connected": self.connected,
            "database": settings.MONGODB_DB_NAME,
            "collections": counts,
            "error": None if self.connected else self.last_error,
        }


mongodb_service = MongoDBService()
