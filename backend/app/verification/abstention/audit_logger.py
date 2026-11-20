import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.ai_records import AIAbstentionLog

logger = logging.getLogger("uvicorn.error")


class AbstentionAuditLogger:
    """
    Persists abstention occurrences and provides analytics on missing fields,
    false answer rate trends, and pre-generation bypass efficiency.
    """

    def log_abstention_event(
        self,
        db: Session,
        response_id: Optional[int],
        intent: str,
        reason: str,
        complaint_number: Optional[str] = None,
        missing_fields: Optional[List[str]] = None,
        pre_generation_halt: bool = False
    ) -> Optional[AIAbstentionLog]:
        """
        Records an abstention decision event in the database.
        """
        try:
            missing_json = json.dumps(missing_fields) if missing_fields else None
            entry = AIAbstentionLog(
                response_id=response_id,
                complaint_number=complaint_number,
                intent=intent,
                abstention_reason=reason,
                missing_fields=missing_json,
                pre_generation_halt=1 if pre_generation_halt else 0
            )
            db.add(entry)
            db.commit()
            db.refresh(entry)
            logger.info(
                f"[AbstentionAudit] Logged abstention (reason={reason}, halt={pre_generation_halt}) "
                f"for complaint={complaint_number}."
            )
            return entry
        except Exception as e:
            db.rollback()
            logger.error(f"[AbstentionAudit] Failed to log abstention event: {e}")
            return None

    def get_abstention_statistics(self, db: Session) -> Dict[str, Any]:
        """
        Aggregates operational abstention statistics.
        """
        total_abstentions = db.query(AIAbstentionLog).count()
        pre_gen_halts = (
            db.query(AIAbstentionLog)
            .filter(AIAbstentionLog.pre_generation_halt == 1)
            .count()
        )

        # Reason breakdown
        reasons_query = (
            db.query(AIAbstentionLog.abstention_reason, func.count(AIAbstentionLog.id))
            .group_by(AIAbstentionLog.abstention_reason)
            .all()
        )
        reasons_breakdown = {r: count for r, count in reasons_query}

        return {
            "total_abstentions": total_abstentions,
            "pre_generation_halts": pre_gen_halts,
            "reasons_breakdown": reasons_breakdown,
            "pre_generation_halt_pct": (
                round((pre_gen_halts / total_abstentions) * 100, 2)
                if total_abstentions > 0 else 0.0
            )
        }


abstention_audit_logger = AbstentionAuditLogger()
