from uuid import UUID

from pydantic import BaseModel

from app.modules.employees.models import PositionKind


class EmployeeResponse(BaseModel):
    id: UUID
    name: str
    position: str
    position_kind: PositionKind
    department: str
