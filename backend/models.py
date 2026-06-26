from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class MeetingInput(BaseModel):
    text: str = Field(..., min_length=10, max_length=10000)
    meeting_id: Optional[str] = None

    @validator("text")
    def text_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Meeting text cannot be empty")
        return v.strip()


class TaskStatusUpdate(BaseModel):
    task_id: int
    status: str = Field(..., pattern="^(pending|in-progress|completed|overdue)$")
    actor: Optional[str] = "user"
    note: Optional[str] = None


class TaskResponse(BaseModel):
    id: int
    meeting_id: str
    task: str
    owner: str
    deadline: str
    priority: str
    status: str
    sla_hours: int
    escalated: bool
    created_at: str
    updated_at: str
    days_until_deadline: Optional[int] = None
    is_overdue: bool = False


class AuditLogResponse(BaseModel):
    id: int
    event_type: str
    entity_type: str
    entity_id: str
    actor: str
    description: str
    metadata: Optional[str]
    created_at: str


class MeetingResponse(BaseModel):
    meeting_id: str
    task_count: int
    tasks: List[TaskResponse]
    message: str


class AnalyticsResponse(BaseModel):
    total_tasks: int
    pending: int
    in_progress: int
    completed: int
    overdue: int
    escalated: int
    completion_rate: float
    overdue_rate: float
    priority_breakdown: dict
    owner_breakdown: dict