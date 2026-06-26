import uuid
import logging
from fastapi import APIRouter, HTTPException, status
from models import MeetingInput, MeetingResponse
from ai_service import extract_tasks_from_meeting
from database import db_session
from agents.audit_agent import audit_agent
from agents.escalation_agent import escalation_agent
from utils.helpers import task_row_to_response

router = APIRouter(prefix="/api", tags=["meetings"])
logger = logging.getLogger(__name__)


@router.post("/process-meeting", response_model=MeetingResponse,
             status_code=status.HTTP_201_CREATED)
async def process_meeting(payload: MeetingInput):
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Meeting text cannot be empty.")

    meeting_id = payload.meeting_id or f"mtg_{uuid.uuid4().hex[:12]}"

    try:
        extracted_tasks = extract_tasks_from_meeting(payload.text)
    except ValueError as e:
        audit_agent.log_ai_failure(meeting_id, str(e))
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        audit_agent.log_ai_failure(meeting_id, str(e))
        raise HTTPException(status_code=502, detail=str(e))

    if not extracted_tasks:
        raise HTTPException(status_code=422,
                            detail="No actionable tasks found in the meeting text.")

    created_tasks = []
    with db_session() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO meetings (id, raw_text, task_count) VALUES (?, ?, ?)",
            (meeting_id, payload.text, len(extracted_tasks)),
        )
        for t in extracted_tasks:
            cursor = conn.execute(
                """INSERT INTO tasks (meeting_id, task, owner, deadline, priority, status)
                   VALUES (?, ?, ?, ?, ?, 'pending')""",
                (meeting_id, t["task"], t["owner"], t["deadline"], t["priority"]),
            )
            task_id = cursor.lastrowid
            audit_agent.log_task_created(
                task_id, t["task"], t["owner"], t["deadline"], t["priority"], meeting_id
            )
            row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
            created_tasks.append(task_row_to_response(dict(row)))

    audit_agent.log_meeting_processed(meeting_id, len(created_tasks))

    try:
        escalation_agent.run()
    except Exception as e:
        logger.warning(f"Post-meeting escalation failed: {e}")

    return MeetingResponse(
        meeting_id=meeting_id,
        task_count=len(created_tasks),
        tasks=created_tasks,
        message=f"Successfully extracted {len(created_tasks)} task(s) from meeting.",
    )


@router.post("/escalate")
async def trigger_escalation():
    try:
        result = escalation_agent.run()
        return {
            "status": "ok",
            "newly_overdue": result["newly_overdue"],
            "escalated": result["escalated"],
            "errors": result["errors"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Escalation failed: {str(e)}")