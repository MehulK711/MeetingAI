import logging
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from database import db_session

logger = logging.getLogger(__name__)

PRIORITY_WEIGHTS = {"high": 3, "medium": 2, "low": 1}
STATUS_WEIGHTS   = {"overdue": 4, "in-progress": 3, "pending": 2, "completed": 0}


class DecisionAgent:

    def score_task(self, task: Dict[str, Any]) -> float:
        priority = PRIORITY_WEIGHTS.get(task.get("priority", "low"), 1)
        status   = STATUS_WEIGHTS.get(task.get("status", "pending"), 1)
        try:
            deadline = datetime.strptime(task["deadline"], "%Y-%m-%d").date()
            days_left = (deadline - date.today()).days
            if days_left < 0:   recency = 3.0
            elif days_left == 0: recency = 2.5
            elif days_left <= 2: recency = 2.0
            elif days_left <= 7: recency = 1.5
            else:                recency = 1.0
        except Exception:
            recency = 1.0
        return round(priority * max(status, 1) * recency, 2)

    def get_owner_workload(self) -> Dict[str, Dict[str, Any]]:
        with db_session() as conn:
            rows = conn.execute(
                """SELECT owner,
                          COUNT(*) as total,
                          SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed,
                          SUM(CASE WHEN status='overdue'   THEN 1 ELSE 0 END) as overdue,
                          SUM(CASE WHEN status='in-progress' THEN 1 ELSE 0 END) as in_progress,
                          SUM(CASE WHEN priority='high'    THEN 1 ELSE 0 END) as high_priority
                   FROM tasks GROUP BY owner"""
            ).fetchall()
        result = {}
        for row in rows:
            d = dict(row)
            owner = d.pop("owner")
            total = d["total"]
            d["completion_rate"] = round((d["completed"] / max(total, 1)) * 100, 1)
            d["overload_risk"]   = total > 5 or d["high_priority"] > 2
            result[owner] = d
        return result

    @staticmethod
    def _days_until(deadline_str: str) -> Optional[int]:
        try:
            return (datetime.strptime(deadline_str, "%Y-%m-%d").date() - date.today()).days
        except Exception:
            return None


decision_agent = DecisionAgent()