import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from models import TaskStatusUpdate, TaskResponse, AuditLogResponse, AnalyticsResponse
from database import db_session
from agents.audit_agent import audit_agent
from agents.decision_agent import decision_agent
from utils.helpers import task_row_to_response

router = APIRouter(prefix="/api", tags=["tasks"])
logger = logging.getLogger(__name__)


@router.get("/tasks", response_model=List[TaskResponse])
async def get_tasks(
    status: Optional[str]   = Query(None),
    priority: Optional[str] = Query(None),
    owner: Optional[str]    = Query(None),
):
    with db_session() as conn:
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []
        if status:
            query += " AND status=?";   params.append(status)
        if priority:
            query += " AND priority=?"; params.append(priority)
        if owner:
            query += " AND owner LIKE ?"; params.append(f"%{owner}%")
        query += """ ORDER BY
            CASE status WHEN 'overdue' THEN 1 WHEN 'in-progress' THEN 2
                        WHEN 'pending' THEN 3 ELSE 4 END,
            CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
            deadline ASC"""
        rows = conn.execute(query, params).fetchall()
    return [task_row_to_response(dict(r)) for r in rows]


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int):
    with db_session() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found.")
    return task_row_to_response(dict(row))


@router.put("/update-task-status", response_model=TaskResponse)
async def update_task_status(payload: TaskStatusUpdate):
    with db_session() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id=?", (payload.task_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Task {payload.task_id} not found.")

        old_status = row["status"]
        if old_status == payload.status:
            return task_row_to_response(dict(row))

        conn.execute(
            "UPDATE tasks SET status=?, updated_at=datetime('now') WHERE id=?",
            (payload.status, payload.task_id),
        )
        if payload.status == "completed":
            conn.execute("UPDATE tasks SET escalated=0 WHERE id=?", (payload.task_id,))

        updated = conn.execute("SELECT * FROM tasks WHERE id=?", (payload.task_id,)).fetchone()

    audit_agent.log_status_update(
        payload.task_id, old_status, payload.status,
        actor=payload.actor or "user", note=payload.note
    )
    return task_row_to_response(dict(updated))


@router.get("/logs", response_model=List[AuditLogResponse])
async def get_logs(
    limit: int = Query(100, ge=1, le=500),
    event_type: Optional[str] = None,
):
    with db_session() as conn:
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params = []
        if event_type:
            query += " AND event_type=?"; params.append(event_type)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(query, params).fetchall()
    return [AuditLogResponse(**dict(r)) for r in rows]


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics():
    with db_session() as conn:
        totals = conn.execute("""
            SELECT COUNT(*) as total,
               SUM(CASE WHEN status='pending'     THEN 1 ELSE 0 END) as pending,
               SUM(CASE WHEN status='in-progress' THEN 1 ELSE 0 END) as in_progress,
               SUM(CASE WHEN status='completed'   THEN 1 ELSE 0 END) as completed,
               SUM(CASE WHEN status='overdue'     THEN 1 ELSE 0 END) as overdue,
               SUM(CASE WHEN escalated=1          THEN 1 ELSE 0 END) as escalated
            FROM tasks""").fetchone()

        priority_rows = conn.execute(
            "SELECT priority, COUNT(*) as count FROM tasks GROUP BY priority"
        ).fetchall()

        owner_rows = conn.execute("""
            SELECT owner,
                   COUNT(*) as total,
                   SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed,
                   SUM(CASE WHEN status='overdue'   THEN 1 ELSE 0 END) as overdue
            FROM tasks GROUP BY owner""").fetchall()

    t = dict(totals)
    total = max(t["total"], 1)

    return AnalyticsResponse(
        total_tasks=t["total"],
        pending=t["pending"] or 0,
        in_progress=t["in_progress"] or 0,
        completed=t["completed"] or 0,
        overdue=t["overdue"] or 0,
        escalated=t["escalated"] or 0,
        completion_rate=round(((t["completed"] or 0) / total) * 100, 1),
        overdue_rate=round(((t["overdue"] or 0) / total) * 100, 1),
        priority_breakdown={r["priority"]: r["count"] for r in priority_rows},
        owner_breakdown={
            r["owner"]: {"total": r["total"], "completed": r["completed"], "overdue": r["overdue"]}
            for r in owner_rows
        },
    )


@router.get("/workload")
async def get_workload():
    return decision_agent.get_owner_workload()