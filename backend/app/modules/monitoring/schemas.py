from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.assessments.models import AssessmentStatus


class MonitoringProcess(BaseModel):
    id: UUID
    employee_id: UUID
    employee_name: str
    position: str
    department: str
    assessor_name: str
    kind: Literal["periodic", "first"]
    form: Literal["B", "C", "P"]
    status: AssessmentStatus
    date_assessment: date | None
    needs_attention: bool
    can_remind: bool


class MonitoringDeadline(BaseModel):
    assessment_id: UUID
    employee_name: str
    kind: Literal["introduction", "report", "assessment"]
    due_on: date
    overdue: bool
    due_soon: bool


class ReminderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    assessment_id: UUID
    sender_id: UUID
    recipient_id: UUID
    created_at: datetime
    channel: Literal["in_app"] = "in_app"
    status: Literal["delivered"] = "delivered"


class MonitoringResponse(BaseModel):
    as_of: date
    attention_window_days: int = 14
    total: int
    in_progress: int
    completed: int
    needs_attention: int
    processes: list[MonitoringProcess]
    deadlines: list[MonitoringDeadline]
    reminders: list[ReminderResponse]
