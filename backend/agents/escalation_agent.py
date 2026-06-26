import logging
from datetime import datetime, date
from typing import List, Dict, Any
from database import db_session
from ai_service import suggest_reassignment

logger = logging.getLogger(__name__)


class EscalationAgent:

    def run(self, audit_agent=None) -> Dict[str, Any]:
        from agents.audit_agent import audit_agent as default_audit
        if audit_agent is None:
            audit_agent = default_audit

        today = date.today()
        today_str = today.isoformat()
        newly_overdue = []
        escalated_count = 0
        errors = []

        with db_session() as conn:
            # Mark overdue tasks
            rows = conn.execute(
                """SELECT id, task, owner, deadline, priority, status, escalated, sla_hours
                   FROM tasks
                   WHERE status NOT IN ('completed','overdue')
                   AND deadline < ?""",
                (today_str,),
            ).fetchall()

            for row in rows:
                task_id = row["id"]
                try:
                    conn.execute(
                        "UPDATE tasks SET status='overdue', updated_at=datetime('now') WHERE id=?",
                        (task_id,),
                    )
                    newly_overdue.append(dict(row))
                    audit_agent.log_status_update(
                        task_id, row["status"], "overdue",
                        actor="escalation_agent",
                        note="Auto-marked overdue"
                    )
                    audit_agent.log_sla_breach(
                        task_id, row["owner"], row["deadline"], row["sla_hours"]
                    )
                except Exception as e:
                    errors.append(str(e))

            # Escalate un-escalated overdue tasks
            unescalated = conn.execute(
                "SELECT id, task, owner, deadline, priority, sla_hours FROM tasks WHERE status='overdue' AND escalated=0"
            ).fetchall()

            all_owners = [r["owner"] for r in conn.execute("SELECT DISTINCT owner FROM tasks").fetchall()]

            for row in unescalated:
                task_id = row["id"]
                try:
                    deadline_dt = datetime.strptime(row["deadline"], "%Y-%m-%d").date()
                    days_overdue = (today - deadline_dt).days

                    suggestion = suggest_reassignment(
                        task=row["task"], owner=row["owner"],
                        deadline=row["deadline"], days_overdue=days_overdue,
                        priority=row["priority"], other_owners=all_owners,
                    )

                    conn.execute(
                        "UPDATE tasks SET escalated=1, updated_at=datetime('now') WHERE id=?",
                        (task_id,),
                    )
                    audit_agent.log_escalation(
                        task_id, row["task"], row["owner"], days_overdue, suggestion
                    )
                    escalated_count += 1
                except Exception as e:
                    errors.append(f"task {task_id}: {str(e)}")

        return {
            "newly_overdue": len(newly_overdue),
            "escalated": escalated_count,
            "errors": errors,
            "run_at": datetime.now().isoformat(),
        }

    def get_overdue_summary(self) -> List[Dict[str, Any]]:
        today = date.today()
        with db_session() as conn:
            rows = conn.execute(
                "SELECT id, task, owner, deadline, priority, escalated FROM tasks WHERE status='overdue' ORDER BY deadline ASC"
            ).fetchall()
        result = []
        for row in rows:
            try:
                deadline_dt = datetime.strptime(row["deadline"], "%Y-%m-%d").date()
                days_overdue = (today - deadline_dt).days
            except Exception:
                days_overdue = 0
            result.append({**dict(row), "days_overdue": days_overdue})
        return result


escalation_agent = EscalationAgent()