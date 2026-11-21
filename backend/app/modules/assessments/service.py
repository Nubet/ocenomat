from typing import Literal
from uuid import UUID

from sqlalchemy import Select, false, select, text
from sqlalchemy.orm import Session

from app.modules.assessments.models import Assessment
from app.modules.assessments.schemas import AssessmentCreate
from app.modules.catalog.models import CatalogVersion
from app.modules.employees.models import (
    Employee,
    ManagerEmployeeAssignment,
    PositionKind,
)
from app.modules.users.models import Role, User


class AssessmentError(Exception):
    def __init__(
        self,
        code: Literal[
            "not_found", "forbidden", "unsupported", "conflict", "catalog_unavailable"
        ],
        message: str,
    ):
        self.code = code
        super().__init__(message)


def accessible_assessments(user: User) -> Select[tuple[Assessment]]:
    statement = select(Assessment)
    if Role.MANAGER not in {role.role for role in user.roles}:
        return statement.where(false())
    return statement.where(
        Assessment.assessor_id == user.id,
        select(ManagerEmployeeAssignment.employee_id)
        .where(
            ManagerEmployeeAssignment.manager_id == user.id,
            ManagerEmployeeAssignment.employee_id == Assessment.employee_id,
        )
        .exists(),
    )


def create_assessment(
    session: Session, user: User, data: AssessmentCreate, key: UUID
) -> tuple[Assessment, bool]:
    if Role.MANAGER not in {role.role for role in user.roles}:
        raise AssessmentError(
            "forbidden", "Only an assigned manager can create an assessment"
        )
    try:
        # Serialize retries of one request; the unique constraint is a second guard.
        session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:scope, 0))"),
            {"scope": f"assessment:{user.id}:{key}"},
        )
        existing = session.scalar(
            select(Assessment).where(
                Assessment.assessor_id == user.id, Assessment.idempotency_key == key
            )
        )
        employee = session.scalar(
            select(Employee)
            .join(
                ManagerEmployeeAssignment,
                ManagerEmployeeAssignment.employee_id == Employee.id,
            )
            .where(
                Employee.id == data.employee_id,
                ManagerEmployeeAssignment.manager_id == user.id,
            )
            .with_for_update(of=[Employee, ManagerEmployeeAssignment])
        )
        if employee is None:
            raise AssessmentError("not_found", "Employee not found")
        if existing is not None:
            if existing.employee_id != data.employee_id or existing.kind != data.kind:
                raise AssessmentError(
                    "conflict", "Idempotency key was used for a different request"
                )
            session.commit()
            return existing, False
        if employee.position_kind != PositionKind.OTHER:
            form = "A" if employee.position_kind == PositionKind.OFFICE_HEAD else "B"
            raise AssessmentError(
                "unsupported",
                f"Form {form} is not supported yet; only periodic form C is available",
            )
        catalog = session.scalar(
            select(CatalogVersion)
            .order_by(CatalogVersion.imported_at.desc(), CatalogVersion.id)
            .limit(1)
        )
        if catalog is None:
            raise AssessmentError(
                "catalog_unavailable",
                "Import a competency catalog before creating an assessment",
            )
        assessment = Assessment(
            employee_id=employee.id,
            assessor_id=user.id,
            catalog_version_id=catalog.id,
            employee_snapshot={
                "id": str(employee.id),
                "name": employee.name,
                "position": employee.position,
                "position_kind": employee.position_kind.value,
                "department": employee.unit.name,
            },
            kind=data.kind,
            form="C",
            idempotency_key=key,
        )
        session.add(assessment)
        session.flush()
        session.commit()
        return assessment, True
    except Exception:
        session.rollback()
        raise
