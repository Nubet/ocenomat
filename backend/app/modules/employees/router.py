from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import false, select
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.modules.employees.models import Employee, ManagerEmployeeAssignment
from app.modules.employees.schemas import EmployeeResponse
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


@router.get("", response_model=list[EmployeeResponse])
def employees(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
    response: Response,
    q: Annotated[str, Query(max_length=100)] = "",
    assigned_only: bool = False,
) -> list[EmployeeResponse]:
    response.headers["Cache-Control"] = "private, no-store"
    statement = visible_employees(user, assigned_only=assigned_only)
    if q.strip():
        statement = statement.where(Employee.name.icontains(q.strip(), autoescape=True))
    return [
        serialize_employee(employee)
        for employee in session.scalars(statement.order_by(Employee.name, Employee.id))
    ]


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
