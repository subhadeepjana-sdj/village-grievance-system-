import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.ai_records import AICorrectionLog

logger = logging.getLogger("uvicorn.error")

class AuditLogger:
    """
    Persists verification and correction attempts into database audit records
    to maintain a full audit trail for administrative transparency and academic evaluation.
    """

    def persist_correction_history(
        self,
        db: Session,
        response_id: int,
        history: List[Dict[str, Any]]
    ) -> List[AICorrectionLog]:
        """
        Records all iterations of the answer correction lifecycle:
        candidate drafts, verification status, action taken, and prompt directives.
        """
        created_records = []
        try:
            for item in history:
                log_entry = AICorrectionLog(
                    response_id=response_id,
                    attempt_number=item.get("attempt", 1),
                    candidate_answer=item.get("candidate_answer", ""),
                    status=item.get("status", "UNKNOWN"),
                    action=item.get("action", "UNKNOWN"),
                    confidence=float(item.get("confidence", 0.0)),
                    prompt_directive=item.get("prompt_directive")
                )
                db.add(log_entry)
                created_records.append(log_entry)

            db.commit()
            logger.info(f"[AuditLogger] Successfully persisted {len(created_records)} correction log(s) for response_id={response_id}.")
        except Exception as e:
            db.rollback()
            logger.error(f"[AuditLogger] Failed to persist correction history: {e}")

        return created_records


audit_logger = AuditLogger()
