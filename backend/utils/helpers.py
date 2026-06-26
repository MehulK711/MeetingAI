from datetime import date, datetime
from typing import Dict, Any
from models import TaskResponse


def task_row_to_response(row: Dict[str, Any]) -> TaskResponse:
    try:
        deadline_date = datetime.strptime(row["deadline"], "%Y-%m-%d").date()
        days_until = (deadline_date - date.today()).days
        is_overdue = row["status"] == "overdue" or days_until < 0
    except Exception:
        days_until = None
        is_overdue = False

    return TaskResponse(
        id=row["id"],
        meeting_id=row["meeting_id"],
        task=row["task"],
        owner=row["owner"],
        deadline=row["deadline"],
        priority=row["priority"],
        status=row["status"],
        sla_hours=row.get("sla_hours", 48),
        escalated=bool(row.get("escalated", 0)),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        days_until_deadline=days_until,
        is_overdue=is_overdue,
    )