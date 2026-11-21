from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import false, func, select
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.modules.employees.models import (
    Employee,
    ManagerEmployeeAssignment,
    OrganizationalUnit,
    PositionKind,
)
from app.modules.employees.schemas import EmployeePage, EmployeeResponse, EmployeeSort
from app.modules.users.models import Role, User
from app.modules.users.router import get_current_user

router = APIRouter(prefix="/api/v1/employees", tags=["employees"])


def visible_employees(user: User, assigned_only: bool = False):
    statement = select(Employee)
    roles = {role.role for role in user.roles}
    # This installation has one organization; no cross-organization grants.
    if not assigned_only and roles & {Role.HR, Role.ADMIN}:
        return statement
    if Role.MANAGER in roles:
        return statement.where(
            select(ManagerEmployeeAssignment.employee_id)
            .where(
                ManagerEmployeeAssignment.manager_id == user.id,
                ManagerEmployeeAssignment.employee_id == Employee.id,
            )
            .exists()
        )
    return statement.where(false())


def serialize_employee(employee: Employee) -> EmployeeResponse:
    return EmployeeResponse(
        id=employee.id,
        name=employee.name,
        position=employee.position,
        position_kind=employee.position_kind,
        department=employee.unit.name,
    )


@router.get("", response_model=EmployeePage)
def employees(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
    response: Response,
    q: Annotated[str, Query(max_length=100)] = "",
    assigned_only: bool = False,
    page: Annotated[int, Query(ge=1, le=1_000_000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    sort: EmployeeSort = EmployeeSort.NAME_ASC,
    position_kind: PositionKind | None = None,
    employee_id: UUID | None = None,
) -> EmployeePage:
    response.headers["Cache-Control"] = "private, no-store"
    statement = visible_employees(user, assigned_only=assigned_only)
    if employee_id is not None:
        statement = statement.where(Employee.id == employee_id)
    if position_kind is not None:
        statement = statement.where(Employee.position_kind == position_kind)
    searchable = func.translate(
        func.lower(Employee.name + " " + Employee.position), "ąćęłńóśźż", "acelnoszz"
    )
    for token in q.lower().translate(str.maketrans("ąćęłńóśźż", "acelnoszz")).split():
        statement = statement.where(searchable.contains(token, autoescape=True))
    total = session.scalar(select(func.count()).select_from(statement.subquery()))
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = min(page, total_pages)
    column, direction = sort.value.split("_")
    sort_column = {
        "name": Employee.name,
        "position": Employee.position,
        "department": OrganizationalUnit.name,
    }[column]
    order = func.lower(sort_column)
    statement = (
        statement.join(Employee.unit)
        .order_by(
            order.desc() if direction == "desc" else order.asc(),
            func.lower(Employee.name),
            Employee.id,
        )
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    return EmployeePage(
        items=[serialize_employee(employee) for employee in session.scalars(statement)],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{employee_id}", response_model=EmployeeResponse)
def employee_detail(
    employee_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
    response: Response,
) -> EmployeeResponse:
    response.headers["Cache-Control"] = "private, no-store"
    employee = session.scalar(visible_employees(user).where(Employee.id == employee_id))
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return serialize_employee(employee)
