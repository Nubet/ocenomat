from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, date, datetime
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import Select, false, select, text
from sqlalchemy.orm import Session

from app.modules.assessments.models import (
    Assessment,
    AssessmentConversation,
    AssessmentCriterion,
    AssessmentEvent,
    AssessmentObservation,
    AssessmentStatus,
)
from app.modules.assessments.rules import periodic_criteria
from app.modules.assessments.schemas import (
    AssessmentCreate,
    ConversationUpdate,
    CriteriaUpdate,
    DatesUpdate,
    ObservationCreate,
)
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
            "not_found",
            "forbidden",
            "unsupported",
            "conflict",
            "catalog_unavailable",
            "invalid",
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
        .correlate(Assessment)
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


@contextmanager
def edit_assessment(
    session: Session,
    user: User,
    assessment_id: UUID,
    revision: int,
    event: str,
    *,
    allowed_status: AssessmentStatus = AssessmentStatus.DRAFT,
    occurred_on: date | None = None,
    replay_status: AssessmentStatus | None = None,
) -> Iterator[Assessment]:
    try:
        assessment = session.scalar(
            accessible_assessments(user)
            .join(
                ManagerEmployeeAssignment,
                (ManagerEmployeeAssignment.employee_id == Assessment.employee_id)
                & (ManagerEmployeeAssignment.manager_id == user.id),
            )
            .where(Assessment.id == assessment_id)
            .with_for_update(of=[Assessment, ManagerEmployeeAssignment])
            .execution_options(populate_existing=True)
        )
        if assessment is None:
            raise AssessmentError("not_found", "Assessment not found")
        if assessment.status == replay_status and revision in (
            assessment.revision - 1,
            assessment.revision,
        ):
            yield assessment
            session.commit()
            return
        if assessment.revision != revision or assessment.status != allowed_status:
            raise AssessmentError(
                "conflict",
                "Assessment changed or this action is unavailable in its current state",
            )
        yield assessment
        if event == "criteria_agreed":
            occurred_on = assessment.date_talk
        elif event == "conversation_confirmed":
            occurred_on = assessment.conversation.occurred_on
        assessment.revision += 1
        session.add(
            AssessmentEvent(
                assessment_id=assessment.id,
                actor_id=user.id,
                revision=assessment.revision,
                kind=event,
                occurred_on=occurred_on,
            )
        )
        session.flush()
        session.commit()
    except Exception:
        session.rollback()
        raise


def save_criteria(
    session: Session, user: User, assessment_id: UUID, data: CriteriaUpdate
) -> Assessment:
    with edit_assessment(
        session, user, assessment_id, data.revision, "criteria_updated"
    ) as assessment:
        catalog = session.get(CatalogVersion, assessment.catalog_version_id)
        additional = [item.criterion_id for item in data.additional]
        try:
            selected = periodic_criteria(
                assessment.form,
                additional,
                {UUID(item["id"]) for item in catalog.criteria},
            )
        except ValueError as error:
            raise AssessmentError("invalid", str(error)) from None
        reasons = {item.criterion_id: item.justification for item in data.additional}
        # Remove and flush before replacing rows with the same composite identity.
        assessment.criteria.clear()
        session.flush()
        assessment.criteria = [
            AssessmentCriterion(
                criterion_id=id,
                required=id not in reasons,
                justification=reasons.get(id),
            )
            for id in selected
        ]
    return assessment


def save_dates(
    session: Session, user: User, assessment_id: UUID, data: DatesUpdate
) -> Assessment:
    with edit_assessment(
        session, user, assessment_id, data.revision, "dates_updated"
    ) as assessment:
        if data.date_talk > datetime.now(ZoneInfo("Europe/Warsaw")).date() and (
            data.duties_discussed
            or data.expectations_discussed
            or data.arrangements_shared
        ):
            raise AssessmentError(
                "invalid", "A future conversation cannot be confirmed as completed"
            )
        for name, value in data.model_dump(exclude={"revision"}).items():
            setattr(assessment, name, value)
    return assessment


def agree_criteria(
    session: Session, user: User, assessment_id: UUID, revision: int
) -> Assessment:
    with edit_assessment(
        session, user, assessment_id, revision, "criteria_agreed"
    ) as assessment:
        catalog = session.get(CatalogVersion, assessment.catalog_version_id)
        try:
            expected = periodic_criteria(
                assessment.form,
                [
                    item.criterion_id
                    for item in assessment.criteria
                    if not item.required
                ],
                {UUID(item["id"]) for item in catalog.criteria},
            )
        except ValueError as error:
            raise AssessmentError("invalid", str(error)) from None
        if set(expected) != {
            item.criterion_id for item in assessment.criteria
        } or not all(
            (
                assessment.date_talk,
                assessment.date_assessment,
                assessment.duties_discussed,
                assessment.expectations_discussed,
                assessment.arrangements_shared,
            )
        ):
            raise AssessmentError(
                "invalid",
                "Save criteria, dates and all completed actions "
                "before confirming arrangements",
            )
        assessment.status = AssessmentStatus.CRITERIA_AGREED
    return assessment


def start_period(
    session: Session, user: User, assessment_id: UUID, revision: int
) -> Assessment:
    with edit_assessment(
        session,
        user,
        assessment_id,
        revision,
        "period_started",
        allowed_status=AssessmentStatus.CRITERIA_AGREED,
    ) as assessment:
        assessment.status = AssessmentStatus.IN_PROGRESS
    return assessment


def validate_activity_date(assessment: Assessment, occurred_on: date) -> None:
    if (
        occurred_on < assessment.date_talk
        or occurred_on > datetime.now(ZoneInfo("Europe/Warsaw")).date()
    ):
        raise AssessmentError(
            "invalid",
            "Activity date must be between the opening conversation and today",
        )


def add_observation(
    session: Session, user: User, assessment_id: UUID, data: ObservationCreate
) -> Assessment:
    with edit_assessment(
        session,
        user,
        assessment_id,
        data.revision,
        "observation_added",
        allowed_status=AssessmentStatus.IN_PROGRESS,
        occurred_on=data.occurred_on,
    ) as assessment:
        validate_activity_date(assessment, data.occurred_on)
        if data.criterion_id not in {item.criterion_id for item in assessment.criteria}:
            raise AssessmentError(
                "invalid", "Choose a criterion selected in this assessment"
            )
        assessment.observations.append(
            AssessmentObservation(
                **data.model_dump(exclude={"revision"}),
                author_id=user.id,
            )
        )
    return assessment


def save_conversation(
    session: Session, user: User, assessment_id: UUID, data: ConversationUpdate
) -> Assessment:
    with edit_assessment(
        session,
        user,
        assessment_id,
        data.revision,
        "conversation_updated",
        allowed_status=AssessmentStatus.IN_PROGRESS,
        occurred_on=data.occurred_on,
    ) as assessment:
        if data.occurred_on is not None:
            validate_activity_date(assessment, data.occurred_on)
        if assessment.conversation is None:
            assessment.conversation = AssessmentConversation()
        for name, value in data.model_dump(exclude={"revision"}).items():
            setattr(assessment.conversation, name, value)
        assessment.conversation.author_id = user.id
        assessment.conversation.recorded_at = datetime.now(UTC)
    return assessment


def confirm_conversation(
    session: Session, user: User, assessment_id: UUID, revision: int
) -> Assessment:
    with edit_assessment(
        session,
        user,
        assessment_id,
        revision,
        "conversation_confirmed",
        allowed_status=AssessmentStatus.IN_PROGRESS,
    ) as assessment:
        conversation = assessment.conversation
        if conversation is None or conversation.occurred_on is None:
            raise AssessmentError(
                "invalid", "Save the completed conversation date before confirmation"
            )
        validate_activity_date(assessment, conversation.occurred_on)
        conversation.confirmed_at = datetime.now(UTC)
        conversation.confirmed_by = user.id
        assessment.status = AssessmentStatus.EVALUATION
    return assessment
