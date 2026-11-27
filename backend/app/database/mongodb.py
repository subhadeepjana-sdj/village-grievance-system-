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
        "users",
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
            db["users"].create_index("email", unique=True)
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
    #  0. Users (Cross-Container Auth Sync)                               #
    # ------------------------------------------------------------------ #

    def upsert_user(self, user_doc: Dict[str, Any]) -> bool:
        if not self.connected or self.db is None or not user_doc.get("email"):
            return False
        try:
            payload = {**user_doc, "synced_at": datetime.datetime.now(datetime.UTC)}
            self.db["users"].update_one(
                {"email": user_doc["email"]},
                {"$set": payload},
                upsert=True,
            )
            return True
        except Exception as exc:
            logger.warning("MongoDB upsert_user failed: %s", exc)
            return False

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        if not self.connected or self.db is None or not email:
            return None
        try:
            return self.db["users"].find_one({"email": email}, {"_id": 0})
        except Exception as exc:
            logger.warning("MongoDB get_user_by_email failed: %s", exc)
            return None

    # ------------------------------------------------------------------ #
    #  2. Complaint Snapshots & Cross-Session Sync                        #
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

    def _iter_collection(self, collection_name: str) -> List[Dict[str, Any]]:
        if not self.connected or self.db is None:
            return []
        try:
            col = self.db[collection_name]
            if hasattr(col, "find"):
                docs = list(col.find({}, {"_id": 0}))
            elif hasattr(col, "docs"):
                docs = [dict(d) for d in col.docs]
            else:
                docs = []
            for d in docs:
                d.pop("_id", None)
            return docs
        except Exception as exc:
            logger.warning("MongoDB _iter_collection(%s) failed: %s", collection_name, exc)
            return []

    def list_complaints(
        self,
        role: str,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        department_id: Optional[int] = None,
        status_filter: Optional[str] = None,
        category_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Read complaints from MongoDB with role-based scoping matching SQLAlchemy."""
        docs = self._iter_collection("complaints")
        if not docs:
            return []

        results: List[Dict[str, Any]] = []
        role_upper = (role or "").upper()
        for doc in docs:
            if role_upper == "CITIZEN":
                matches_id = user_id is not None and doc.get("user_id") == user_id
                matches_email = bool(user_email) and doc.get("citizen_email") == user_email
                if not (matches_id or matches_email):
                    continue
            elif role_upper == "DEPARTMENT_OFFICIAL" and department_id is not None:
                if doc.get("department_id") != department_id:
                    continue

            if status_filter and str(doc.get("status", "")).upper() != status_filter.upper():
                continue
            if category_filter and category_filter.lower() not in str(doc.get("category", "")).lower():
                continue

            results.append(doc)

        def _sort_key(item: Dict[str, Any]) -> str:
            ts = item.get("created_at")
            if isinstance(ts, datetime.datetime):
                return ts.isoformat()
            return str(ts or "")

        results.sort(key=_sort_key, reverse=True)
        return results

    def get_complaint(self, complaint_id: str) -> Optional[Dict[str, Any]]:
        """Look up a complaint in MongoDB by numeric id or case-insensitive complaint_number."""
        if not self.connected or self.db is None or not complaint_id:
            return None
        target = str(complaint_id).strip()
        target_int = int(target) if target.isdigit() else None
        for doc in self._iter_collection("complaints"):
            if target_int is not None and doc.get("id") == target_int:
                return doc
            if str(doc.get("complaint_number", "")).lower() == target.lower():
                return doc
        return None

    def update_complaint_doc(
        self,
        complaint_id: str,
        fields_to_set: Dict[str, Any],
        history_entry: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update an existing MongoDB complaint snapshot in place and append status history."""
        existing = self.get_complaint(complaint_id)
        if not existing:
            return None

        updated = {**existing, **fields_to_set, "synced_at": datetime.datetime.now(datetime.UTC)}
        history = list(existing.get("history") or [])
        if history_entry:
            next_id = len(history) + 1
            entry = {"id": history_entry.get("id") or next_id, **history_entry}
            history.append(entry)
        updated["history"] = history

        if self.upsert_complaint(updated):
            return updated
        return None

    def list_ai_traces(self, limit: int = 100) -> List[Dict[str, Any]]:
        docs = self._iter_collection("ai_traces")
        docs.sort(key=lambda d: str(d.get("created_at") or ""), reverse=True)
        return docs[:limit]

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
