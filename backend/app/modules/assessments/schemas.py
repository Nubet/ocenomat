from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.assessments.models import AssessmentStatus
from app.modules.employees.schemas import EmployeeResponse


class AssessmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    employee_id: UUID
    kind: Literal["periodic"]


class AssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: UUID
    assessor_id: UUID
    catalog_version_id: UUID
    employee_snapshot: EmployeeResponse
    kind: Literal["periodic"]
    form: Literal["C"]
    status: AssessmentStatus
    revision: int
    created_at: datetime
