from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel

from app.modules.employees.models import PositionKind


class EmployeeResponse(BaseModel):
    id: UUID
    name: str
    position: str
    position_kind: PositionKind
    department: str


class EmployeeSort(StrEnum):
    NAME_ASC = "name_asc"
    NAME_DESC = "name_desc"
    POSITION_ASC = "position_asc"
    POSITION_DESC = "position_desc"
    DEPARTMENT_ASC = "department_asc"
    DEPARTMENT_DESC = "department_desc"


class EmployeePage(BaseModel):
    items: list[EmployeeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
