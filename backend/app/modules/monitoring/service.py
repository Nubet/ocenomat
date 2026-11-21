from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.modules.assessments.first_rules import first_deadlines
from app.modules.assessments.models import Assessment, AssessmentStatus, FirstAssessment
from app.modules.assessments.service import AssessmentError, accessible_assessments
from app.modules.employees.models import (
    Employee,
    ManagerEmployeeAssignment,
    OrganizationalUnit,
)
from app.modules.monitoring.models import AssessmentReminder
from app.modules.monitoring.schemas import (
    MonitoringDeadline,
    MonitoringProcess,
    MonitoringResponse,
    ReminderResponse,
)
from app.modules.users.models import Role, User, UserRole


def require_hr(user: User) -> None:
    if Role.HR not in {role.role for role in user.roles}:
        raise AssessmentError("forbidden", "HR role required")


def monitoring(
    session: Session, user: User, today: date, *, hr: bool
) -> MonitoringResponse:
    if hr:
        require_hr(user)
    assigned = (
        select(ManagerEmployeeAssignment.employee_id)
        .where(
            ManagerEmployeeAssignment.employee_id == Assessment.employee_id,
            ManagerEmployeeAssignment.manager_id == Assessment.assessor_id,
        )
        .exists()
    )
    manager = (
        select(UserRole.user_id)
        .where(
            UserRole.user_id == Assessment.assessor_id, UserRole.role == Role.MANAGER
        )
        .exists()
    )
    statement = (
        select(
            Assessment.id,
            Assessment.employee_id,
            Employee.name.label("employee_name"),
            Employee.position,
            OrganizationalUnit.name.label("department"),
            User.display_name.label("assessor_name"),
            Assessment.kind,
            Assessment.form,
            Assessment.status,
            Assessment.date_assessment,
            (assigned & manager & User.active).label("recipient_available"),
            FirstAssessment.hired_on,
            FirstAssessment.contract_end,
            FirstAssessment.replacement_agreed_on,
            FirstAssessment.report_to,
            FirstAssessment.report_submitted_on,
            FirstAssessment.report_missing,
            FirstAssessment.assessed_on,
        )
        .join(Employee, Employee.id == Assessment.employee_id)
        .join(OrganizationalUnit, OrganizationalUnit.id == Employee.unit_id)
        .join(User, User.id == Assessment.assessor_id)
        .outerjoin(FirstAssessment, FirstAssessment.assessment_id == Assessment.id)
        .order_by(Assessment.created_at.desc(), Assessment.id)
    )
    if not hr:
        statement = statement.where(
            Assessment.id.in_(
                accessible_assessments(user).with_only_columns(Assessment.id)
            )
        )
    processes = []
    deadlines = []
    for row in session.execute(statement).mappings():
        pending: list[tuple[str, date | None]] = []
        completed = row.status == AssessmentStatus.COMPLETED
        assessment_on = row.date_assessment
        bounds = None
        if row.kind == "first" and row.hired_on is not None:
            bounds = first_deadlines(
                row.hired_on, row.contract_end, row.replacement_agreed_on
            )
            assessment_on = row.assessed_on or bounds.assessment_by
        if not completed:
            if bounds is not None:
                if row.status == AssessmentStatus.DRAFT:
                    pending.append(("introduction", bounds.introduction_by))
                if row.status == AssessmentStatus.IN_PROGRESS:
                    if row.report_submitted_on is None and not row.report_missing:
                        pending.append(("report", row.report_to))
                pending.append(("assessment", bounds.assessment_by))
            else:
                pending.append(("assessment", row.date_assessment))
        process_deadlines = [
            MonitoringDeadline(
                assessment_id=row.id,
                employee_name=row.employee_name,
                kind=kind,
                due_on=due,
                overdue=due < today,
                due_soon=today <= due <= today + timedelta(days=14),
            )
            for kind, due in pending
            if due is not None
        ]
        processes.append(
            MonitoringProcess(
                id=row.id,
                employee_id=row.employee_id,
                employee_name=row.employee_name,
                position=row.position,
                department=row.department,
                assessor_name=row.assessor_name,
                kind=row.kind,
                form=row.form,
                status=row.status,
                date_assessment=assessment_on,
                needs_attention=any(d.overdue or d.due_soon for d in process_deadlines)
                or any(due is None for _, due in pending),
                can_remind=hr and not completed and row.recipient_available,
            )
        )
        deadlines.extend(process_deadlines)
    reminders = select(AssessmentReminder).order_by(
        AssessmentReminder.created_at.desc(), AssessmentReminder.id
    )
    if not hr:
        reminders = reminders.where(
            AssessmentReminder.recipient_id == user.id,
            AssessmentReminder.assessment_id.in_([p.id for p in processes]),
        )
    return MonitoringResponse(
        as_of=today,
        total=len(processes),
        in_progress=sum(p.status == AssessmentStatus.IN_PROGRESS for p in processes),
        completed=sum(p.status == AssessmentStatus.COMPLETED for p in processes),
        needs_attention=sum(p.needs_attention for p in processes),
        processes=processes,
        deadlines=sorted(deadlines, key=lambda d: (d.due_on, d.assessment_id, d.kind)),
        reminders=[
            ReminderResponse.model_validate(r) for r in session.scalars(reminders)
        ],
    )


def send_reminder(
    session: Session, user: User, assessment_id: UUID, key: UUID
) -> tuple[AssessmentReminder, bool]:
    require_hr(user)
    try:
        session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:scope, 0))"),
            {"scope": f"reminder:{user.id}:{key}"},
        )
        existing = session.scalar(
            select(AssessmentReminder).where(
                AssessmentReminder.sender_id == user.id,
                AssessmentReminder.idempotency_key == key,
            )
        )
        if existing is not None:
            if existing.assessment_id != assessment_id:
                raise AssessmentError(
                    "conflict", "Idempotency key was used for another process"
                )
            session.commit()
            return existing, False
        assessment = session.scalar(
            select(Assessment.id)
            .where(Assessment.id == assessment_id)
            .with_for_update()
        )
        if assessment is None:
            raise AssessmentError("not_found", "Assessment not found")
        recipient = session.scalar(
            select(User.id)
            .join(Assessment, Assessment.assessor_id == User.id)
            .join(
                ManagerEmployeeAssignment,
                (ManagerEmployeeAssignment.manager_id == User.id)
                & (ManagerEmployeeAssignment.employee_id == Assessment.employee_id),
            )
            .where(
                Assessment.id == assessment_id,
                Assessment.status != AssessmentStatus.COMPLETED,
                User.active,
                select(UserRole.user_id)
                .where(UserRole.user_id == User.id, UserRole.role == Role.MANAGER)
                .exists(),
            )
            .with_for_update(of=[User, ManagerEmployeeAssignment])
        )
        if recipient is None:
            raise AssessmentError(
                "conflict", "Process is closed or its assessor is unavailable"
            )
        reminder = AssessmentReminder(
            assessment_id=assessment_id,
            sender_id=user.id,
            recipient_id=recipient,
            idempotency_key=key,
        )
        session.add(reminder)
        session.flush()
        session.commit()
        return reminder, True
    except Exception:
        session.rollback()
        raise
