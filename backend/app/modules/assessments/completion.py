from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.assessments.models import (
    Assessment,
    AssessmentStatus,
    AssessmentSummary,
)
from app.modules.assessments.rules import periodic_criteria
from app.modules.assessments.schemas import SummaryUpdate
from app.modules.assessments.service import AssessmentError, edit_assessment
from app.modules.catalog.models import CatalogVersion
from app.modules.users.models import User


def save_summary(
    session: Session, user: User, assessment_id: UUID, data: SummaryUpdate
) -> Assessment:
    with edit_assessment(
        session,
        user,
        assessment_id,
        data.revision,
        "summary_updated",
        allowed_status=AssessmentStatus.EVALUATION,
    ) as assessment:
        if assessment.summary is None:
            assessment.summary = AssessmentSummary()
        for name, value in data.model_dump(exclude={"revision"}).items():
            setattr(assessment.summary, name, value)
        assessment.summary.author_id = user.id
        assessment.summary.recorded_at = datetime.now(UTC)
    return assessment


def complete_assessment(
    session: Session, user: User, assessment_id: UUID, revision: int
) -> Assessment:
    with edit_assessment(
        session,
        user,
        assessment_id,
        revision,
        "assessment_completed",
        allowed_status=AssessmentStatus.EVALUATION,
        replay_status=AssessmentStatus.COMPLETED,
    ) as assessment:
        if assessment.status == AssessmentStatus.COMPLETED:
            return assessment
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
        conversation = assessment.conversation
        if (
            set(expected) != {item.criterion_id for item in assessment.criteria}
            or conversation is None
            or not all(
                (
                    assessment.date_talk,
                    assessment.date_assessment,
                    assessment.duties_discussed,
                    assessment.expectations_discussed,
                    assessment.arrangements_shared,
                    conversation.occurred_on,
                    conversation.confirmed_at,
                    conversation.confirmed_by,
                )
            )
        ):
            raise AssessmentError(
                "invalid", "Complete arrangements and confirm the conversation"
            )
        result = assessment.result
        if result.outcome == "incomplete":
            raise AssessmentError(
                "invalid", "Confirm every selected criterion before completion"
            )
        summary = assessment.summary
        if summary is None or (
            result.outcome == "negative" and not summary.negative_justification.strip()
        ):
            raise AssessmentError(
                "invalid", "Save the summary and justify a negative result"
            )
        summary.outcome = result.outcome
        summary.score_total = sum(item.score for item in assessment.ratings)
        summary.score_count = len(assessment.criteria)
        summary.completed_by = user.id
        summary.completed_at = datetime.now(UTC)
        assessment.status = AssessmentStatus.COMPLETED
    return assessment
