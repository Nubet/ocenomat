from datetime import UTC, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.modules.assessments.first_rules import calendar_months, first_deadlines
from app.modules.assessments.first_schemas import (
    FirstData,
    FirstDeadlineUpdate,
    FirstQualification,
    FirstUpdate,
)
from app.modules.assessments.models import (
    Assessment,
    AssessmentEvent,
    AssessmentStatus,
    AssessmentSummary,
    FirstDeadlineChange,
)
from app.modules.assessments.service import AssessmentError, assessment_transaction
from app.modules.users.models import User

INTRO_FIELDS = {
    *FirstQualification.model_fields,
    "intro_on",
    "intro_confirmed",
    "arrangements_shared",
    "report_from",
    "report_to",
}
REPORT_FIELDS = {
    "report_period_from",
    "report_period_to",
    "report_submitted_on",
    "report_missing",
    "report_tasks",
    "report_problems",
    "report_learning",
    "report_conclusions",
    "exam",
    "exam_basis",
    "conversation_on",
    "conversation_notes",
    "conversation_confirmed",
}
DECISION_FIELDS = set(FirstData.model_fields) - INTRO_FIELDS - REPORT_FIELDS


def validate_introduction(data: FirstData) -> None:
    deadlines = first_deadlines(
        data.hired_on, data.contract_end, data.replacement_agreed_on
    )
    today = datetime.now(ZoneInfo("Europe/Warsaw")).date()
    if not (
        data.intro_on
        and data.intro_confirmed
        and data.arrangements_shared
        and (data.replacement_agreed_on or data.hired_on)
        <= data.intro_on
        <= min(today, deadlines.introduction_by)
        and data.report_from
        and data.report_to
        and deadlines.assessment_from
        <= data.report_from
        <= data.report_to
        <= deadlines.assessment_by
    ):
        raise ValueError(
            "Confirm the introduction within 21 days, share arrangements "
            "and set the report window within the statutory assessment period"
        )


def validate_conversation(data: FirstData) -> None:
    today = datetime.now(ZoneInfo("Europe/Warsaw")).date()
    if data.exam is None:
        raise ValueError("Record the exam result or statutory exemption")
    if data.report_submitted_on is not None:
        if not (
            data.report_period_from
            and data.report_period_to
            and data.hired_on
            <= data.report_period_from
            <= data.report_period_to
            <= data.report_submitted_on
            <= today
            and data.report_period_to
            >= calendar_months(data.report_period_from, 7) - timedelta(days=1)
            and all(
                (
                    data.report_tasks,
                    data.report_problems,
                    data.report_learning,
                    data.report_conclusions,
                )
            )
        ):
            raise ValueError(
                "Record all four report sections and at least seven worked months"
            )
        earliest = data.report_submitted_on
    elif data.report_missing:
        earliest = data.report_to + timedelta(days=1)
    else:
        raise ValueError(
            "Record the report or explicitly confirm its absence after the deadline"
        )
    if not (
        data.conversation_on
        and data.conversation_confirmed
        and max(earliest, data.intro_on) <= data.conversation_on <= today
    ):
        raise ValueError(
            "Confirm the evaluation conversation after the report or expired deadline"
        )


def record_event(
    session: Session, assessment: Assessment, user: User, kind: str
) -> None:
    assessment.revision += 1
    session.add(
        AssessmentEvent(
            assessment_id=assessment.id,
            actor_id=user.id,
            revision=assessment.revision,
            kind=kind,
        )
    )


def save_first(
    session: Session, user: User, assessment_id: UUID, command: FirstUpdate
) -> Assessment:
    with assessment_transaction(session, user, assessment_id) as assessment:
        if assessment.kind != "first" or assessment.first is None:
            raise AssessmentError("unsupported", "This is not a first assessment")
        previous = FirstData.model_validate(assessment.first)
        if (
            assessment.status == AssessmentStatus.COMPLETED
            and command.action == "complete"
            and command.revision in (assessment.revision, assessment.revision - 1)
            and command.data == previous
        ):
            return assessment
        allowed = {
            AssessmentStatus.DRAFT: INTRO_FIELDS,
            AssessmentStatus.IN_PROGRESS: REPORT_FIELDS,
            AssessmentStatus.EVALUATION: DECISION_FIELDS,
        }.get(assessment.status)
        if allowed is None or command.revision != assessment.revision:
            raise AssessmentError(
                "conflict", "Assessment changed or is already completed"
            )
        incoming = command.data.model_dump()
        if any(
            incoming[name] != getattr(previous, name)
            for name in incoming
            if name not in allowed
        ):
            raise AssessmentError(
                "invalid",
                "Only fields of the current first-assessment stage can be changed",
            )
        transitions = {
            "confirm_introduction": (
                AssessmentStatus.DRAFT,
                AssessmentStatus.IN_PROGRESS,
            ),
            "confirm_conversation": (
                AssessmentStatus.IN_PROGRESS,
                AssessmentStatus.EVALUATION,
            ),
            "complete": (AssessmentStatus.EVALUATION, AssessmentStatus.COMPLETED),
        }
        transition = transitions.get(command.action)
        if transition is not None and assessment.status != transition[0]:
            raise AssessmentError(
                "conflict", "First-assessment transition is unavailable"
            )
        data = command.data
        try:
            if (
                assessment.status != AssessmentStatus.DRAFT
                or command.action == "confirm_introduction"
            ):
                validate_introduction(data)
            if (
                assessment.status == AssessmentStatus.EVALUATION
                or command.action == "confirm_conversation"
            ):
                validate_conversation(data)
        except ValueError as error:
            raise AssessmentError("invalid", str(error)) from None
        for name, value in incoming.items():
            setattr(assessment.first, name, value)
        if command.action == "complete":
            deadlines = first_deadlines(
                data.hired_on, data.contract_end, data.replacement_agreed_on
            )
            result = assessment.result
            today = datetime.now(ZoneInfo("Europe/Warsaw")).date()
            if not (
                data.assessed_on
                and deadlines.assessment_from
                <= data.assessed_on
                <= min(today, deadlines.assessment_by)
                and data.assessed_on >= data.conversation_on
                and data.unit_head_name
                and data.unit_head_position
                and data.unit_head_agreed
                and result.outcome != "incomplete"
                and (result.outcome != "negative" or data.justification)
            ):
                raise AssessmentError(
                    "invalid",
                    "Confirm all five scores, assessment date, agreement with "
                    "the unit head and justification of a negative result",
                )
            assessment.summary = AssessmentSummary(
                negative_justification=data.justification,
                development_conclusions=data.development_conclusions,
                author_id=user.id,
                recorded_at=datetime.now(UTC),
                outcome=result.outcome,
                score_total=sum(data.scores.values()),
                score_count=5,
                completed_by=user.id,
                completed_at=datetime.now(UTC),
            )
        if transition is not None:
            assessment.status = transition[1]
        record_event(session, assessment, user, f"first_{command.action}")
    return assessment


def change_first_deadlines(
    session: Session, user: User, assessment_id: UUID, command: FirstDeadlineUpdate
) -> Assessment:
    with assessment_transaction(session, user, assessment_id) as assessment:
        if assessment.kind != "first" or assessment.first is None:
            raise AssessmentError("unsupported", "This is not a first assessment")
        if (
            assessment.status != AssessmentStatus.IN_PROGRESS
            or command.revision != assessment.revision
        ):
            raise AssessmentError(
                "conflict",
                "Deadlines can be changed only before confirming "
                "the evaluation conversation",
            )
        data = FirstData.model_validate(assessment.first)
        today = datetime.now(ZoneInfo("Europe/Warsaw")).date()
        duration = (command.circumstance_to - command.circumstance_from).days + 1
        if not (
            data.hired_on
            <= command.circumstance_from
            <= command.circumstance_to
            <= today
            and command.circumstance_to <= command.notified_on <= today
            and data.report_submitted_on is None
            and not data.report_missing
        ):
            raise AssessmentError(
                "invalid",
                "Record the actual circumstance and written notification "
                "before report submission",
            )
        if command.reason == "contract_extension":
            if not (
                command.circumstance_to >= calendar_months(command.circumstance_from, 3)
                and command.contract_end == data.contract_end + timedelta(days=duration)
            ):
                raise AssessmentError(
                    "invalid",
                    "Art. 35(4) requires absence longer than three months and "
                    "an extension by that absence; record the employee request "
                    "and director's decision in the basis",
                )
        elif not (
            command.contract_end == data.contract_end
            and command.report_from == data.report_from + timedelta(days=duration)
            and command.report_to == data.report_to + timedelta(days=duration)
        ):
            raise AssessmentError(
                "invalid",
                "Extend the report window by the duration of absence "
                "or duties outside the workplace",
            )
        changed = data.model_copy(
            update={
                "contract_end": command.contract_end,
                "report_from": command.report_from,
                "report_to": command.report_to,
            }
        )
        try:
            validate_introduction(changed)
        except ValueError as error:
            raise AssessmentError("invalid", str(error)) from None
        assessment.first_deadline_changes.append(
            FirstDeadlineChange(
                assessment_id=assessment.id,
                revision=assessment.revision + 1,
                author_id=user.id,
                previous_contract_end=data.contract_end,
                previous_report_from=data.report_from,
                previous_report_to=data.report_to,
                **command.model_dump(exclude={"revision"}),
            )
        )
        assessment.first.contract_end = changed.contract_end
        assessment.first.report_from = changed.report_from
        assessment.first.report_to = changed.report_to
        record_event(session, assessment, user, "first_deadlines_changed")
    return assessment
