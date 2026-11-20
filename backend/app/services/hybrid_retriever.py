import re
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.complaint import Complaint
from app.models.department import Department
from app.models.village import Village
from app.services.embedding_service import embedding_service
from app.services.qdrant_service import qdrant_service

logger = logging.getLogger("uvicorn.error")

class HybridRetriever:
    COMPLAINT_PATTERN = re.compile(r'(GRV-\d{4}-\d+|\bV\d+\b|\bGRV\d+\b)', re.IGNORECASE)

    def retrieve_evidence(self, query: str, db: Session, user_id: Optional[int] = None, top_k: int = 4) -> Dict[str, Any]:
        evidence_items = []
        structured_matches = []
        
        # 1. Structured Search: Check if user mentions explicit complaint numbers or words like "my complaint"
        complaint_matches = self.COMPLAINT_PATTERN.findall(query)
        
        if complaint_matches:
            for raw_num in complaint_matches:
                clean_num = raw_num.upper()
                # Query DB
                complaints = db.query(Complaint).filter(
                    (Complaint.complaint_number.ilike(f"%{clean_num}%")) | 
                    (Complaint.complaint_number == clean_num)
                ).all()
                
                for c in complaints:
                    dept_name = c.department.name if c.department else "Unassigned Department"
                    village_name = c.village.name if c.village else "Gram Panchayat"
                    citizen_name = c.citizen.name if c.citizen else "Citizen"
                    
                    text_repr = (
                        f"COMPLAINT RECORD [ID: {c.complaint_number}]:\n"
                        f"- Category: {c.category}\n"
                        f"- Title: {c.title}\n"
                        f"- Status: {c.status.value if hasattr(c.status, 'value') else c.status}\n"
                        f"- Department Handling: {dept_name}\n"
                        f"- Priority: {c.priority.value if hasattr(c.priority, 'value') else c.priority}\n"
                        f"- Submitted By: {citizen_name}\n"
                        f"- Location / Village: {c.location or village_name}\n"
                        f"- Submitted Date: {c.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                        f"- Description: {c.description}"
                    )
                    
                    evidence_items.append({
                        "document_id": None,
                        "chunk_id": f"db_complaint_{c.id}",
                        "similarity_score": 1.0,
                        "evidence_text": text_repr,
                        "source_type": "COMPLAINT_RECORD",
                        "metadata": {
                            "complaint_number": c.complaint_number,
                            "status": c.status.value if hasattr(c.status, 'value') else c.status,
                            "department": dept_name,
                            "category": c.category
                        }
                    })
                    structured_matches.append(c.complaint_number)

        # Also fallback search user's recent complaints if user asks "my complaint status" without explicit number
        if not evidence_items and user_id and any(kw in query.lower() for kw in ["my complaint", "my grievance", "my issue", "status of complaint"]):
            recent_complaints = db.query(Complaint).filter(Complaint.user_id == user_id).order_by(Complaint.created_at.desc()).limit(3).all()
            for c in recent_complaints:
                dept_name = c.department.name if c.department else "Unassigned Department"
                text_repr = (
                    f"CITIZEN RECENT COMPLAINT RECORD [ID: {c.complaint_number}]:\n"
                    f"- Title: {c.title}\n"
                    f"- Category: {c.category}\n"
                    f"- Status: {c.status.value if hasattr(c.status, 'value') else c.status}\n"
                    f"- Department Handling: {dept_name}\n"
                    f"- Description: {c.description}"
                )
                evidence_items.append({
                    "document_id": None,
                    "chunk_id": f"db_user_complaint_{c.id}",
                    "similarity_score": 0.95,
                    "evidence_text": text_repr,
                    "source_type": "COMPLAINT_RECORD",
                    "metadata": {
                        "complaint_number": c.complaint_number,
                        "status": c.status.value if hasattr(c.status, 'value') else c.status,
                        "department": dept_name
                    }
                })

        # 2. Semantic Search in Qdrant Vector DB
        query_vec = embedding_service.generate_embedding(query)
        qdrant_hits = qdrant_service.search_similar(query_vec, top_k=top_k)
        
        for hit in qdrant_hits:
            payload = hit.get("payload", {})
            evidence_items.append({
                "document_id": payload.get("document_id"),
                "chunk_id": payload.get("chunk_id", f"qdrant_{hit.get('id')}"),
                "similarity_score": round(hit.get("score", 0.0), 4),
                "evidence_text": payload.get("text", ""),
                "source_type": "KNOWLEDGE_BASE",
                "metadata": {
                    "source": payload.get("source", "Knowledge Base"),
                    "department": payload.get("department", ""),
                    "category": payload.get("category", "")
                }
            })

        return {
            "query": query,
            "structured_matches": structured_matches,
            "evidence": evidence_items
        }

hybrid_retriever = HybridRetriever()
