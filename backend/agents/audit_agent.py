import json
import logging
from typing import Optional, Dict, Any
from database import db_session

logger = logging.getLogger(__name__)


class AuditAgent:
    MEETING_PROCESSED       = "MEETING_PROCESSED"
    TASK_CREATED            = "TASK_CREATED"
    TASK_STATUS_UPDATED     = "TASK_STATUS_UPDATED"
    TASK_ESCALATED          = "TASK_ESCALATED"
    SLA_BREACH_DETECTED     = "SLA_BREACH_DETECTED"
    AI_EXTRACTION_FAILED    = "AI_EXTRACTION_FAILED"

    def log(self, event_type: str, entity_type: str, entity_id: str,
            description: str, actor: str = "system",
            metadata: Optional[Dict[str, Any]] = None) -> int:
        meta_str = json.dumps(metadata) if metadata else None
        try:
            with db_session() as conn:
                cursor = conn.execute(
                    """INSERT INTO audit_logs
                       (event_type, entity_type, entity_id, actor, description, metadata)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (event_type, entity_type, str(entity_id), actor, description, meta_str),
                )
                logger.info(f"[AUDIT] {event_type} | {entity_type}:{entity_id}")
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"[AUDIT WRITE FAILED] {e}")
            return -1

    def log_meeting_processed(self, meeting_id: str, task_count: int, actor: str = "system"):
        self.log(self.MEETING_PROCESSED, "meeting", meeting_id,
                 f"Meeting processed. {task_count} task(s) extracted.",
                 actor=actor, metadata={"task_count": task_count})

    def log_task_created(self, task_id: int, task: str, owner: str,
                         deadline: str, priority: str, meeting_id: str):
        self.log(self.TASK_CREATED, "task", str(task_id),
                 f"Task created: '{task[:60]}' → {owner}, due {deadline} [{priority}]",
                 actor="ml_extraction_agent",
                 metadata={"task": task, "owner": owner, "deadline": deadline,
                           "priority": priority, "meeting_id": meeting_id})

    def log_status_update(self, task_id: int, old_status: str, new_status: str,
                          actor: str = "user", note: Optional[str] = None):
        self.log(self.TASK_STATUS_UPDATED, "task", str(task_id),
                 f"Status: {old_status} → {new_status}" + (f" | {note}" if note else ""),
                 actor=actor,
                 metadata={"old_status": old_status, "new_status": new_status})

    def log_escalation(self, task_id: int, task: str, owner: str,
                       days_overdue: int, suggestion: Optional[Dict] = None):
        self.log(self.TASK_ESCALATED, "task", str(task_id),
                 f"ESCALATED: {days_overdue} day(s) overdue. Owner: {owner}. '{task[:50]}'",
                 actor="escalation_agent",
                 metadata={"days_overdue": days_overdue, "owner": owner,
                           "reassignment": suggestion})

    def log_sla_breach(self, task_id: int, owner: str, deadline: str, sla_hours: int):
        self.log(self.SLA_BREACH_DETECTED, "task", str(task_id),
                 f"SLA breach. Deadline: {deadline}, SLA: {sla_hours}h. Owner: {owner}",
                 actor="sla_monitor",
                 metadata={"deadline": deadline, "sla_hours": sla_hours})

    def log_ai_failure(self, meeting_id: str, error: str):
        self.log(self.AI_EXTRACTION_FAILED, "meeting", meeting_id,
                 f"Extraction failed: {error[:200]}",
                 actor="ml_extraction_agent", metadata={"error": error})


audit_agent = AuditAgent()