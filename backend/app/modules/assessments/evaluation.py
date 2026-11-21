from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.assessments.models import (
    Assessment,
    AssessmentStatus,
    CriterionRating,
    IndicatorAnswer,
)
from app.modules.assessments.rules import suggest_score
from app.modules.assessments.schemas import AnswersUpdate, RatingConfirm
from app.modules.assessments.service import AssessmentError, edit_assessment
from app.modules.catalog.models import CatalogVersion
from app.modules.users.models import User


def selected_criterion(
    session: Session, assessment: Assessment, criterion_id: UUID
) -> dict:
    if not any(item.criterion_id == criterion_id for item in assessment.criteria):
        raise AssessmentError("invalid", "Criterion is not selected in this assessment")
    catalog = session.get(CatalogVersion, assessment.catalog_version_id)
    for criterion in catalog.criteria:
        if UUID(criterion["id"]) == criterion_id:
            return criterion
    raise AssessmentError("invalid", "Criterion is not in the pinned catalog")


def criterion_rating(
    assessment: Assessment, criterion_id: UUID, user: User
) -> CriterionRating:
    for rating in assessment.ratings:
        if rating.criterion_id == criterion_id:
            return rating
    suggestion = suggest_score([])
    rating = CriterionRating(
        criterion_id=criterion_id,
        suggested_score=suggestion.score,
        policy_version=suggestion.policy_version,
        author_id=user.id,
        recorded_at=datetime.now(UTC),
        answers=[],
    )
    assessment.ratings.append(rating)
    return rating


def save_answers(
    session: Session,
    user: User,
    assessment_id: UUID,
    criterion_id: UUID,
    data: AnswersUpdate,
) -> Assessment:
    with edit_assessment(
        session,
        user,
        assessment_id,
        data.revision,
        "indicator_answers_updated",
        allowed_status=AssessmentStatus.EVALUATION,
    ) as assessment:
        criterion = selected_criterion(session, assessment, criterion_id)
        expected = {UUID(item["id"]) for item in criterion["indicators"]}
        supplied = {item.indicator_id for item in data.answers}
        if supplied != expected or len(supplied) != len(data.answers):
            raise AssessmentError(
                "invalid", "Supply each indicator of the pinned criterion exactly once"
            )
        rating = criterion_rating(assessment, criterion_id, user)
        old = {item.indicator_id: (item.level, item.note) for item in rating.answers}
        new = {item.indicator_id: (item.level, item.note) for item in data.answers}
        if old != new:
            rating.answers.clear()
            session.flush()
            rating.answers = [
                IndicatorAnswer(**item.model_dump()) for item in data.answers
            ]
            suggestion = suggest_score([item.level for item in data.answers])
            rating.suggested_score = suggestion.score
            rating.policy_version = suggestion.policy_version
            rating.author_id = user.id
            rating.recorded_at = datetime.now(UTC)
            rating.score = rating.confirmed_by = rating.confirmed_at = None
    return assessment


def confirm_rating(
    session: Session,
    user: User,
    assessment_id: UUID,
    criterion_id: UUID,
    data: RatingConfirm,
) -> Assessment:
    with edit_assessment(
        session,
        user,
        assessment_id,
        data.revision,
        "criterion_rating_confirmed",
        allowed_status=AssessmentStatus.EVALUATION,
    ) as assessment:
        selected_criterion(session, assessment, criterion_id)
        rating = criterion_rating(assessment, criterion_id, user)
        rating.score = data.score
        rating.confirmed_by = user.id
        rating.confirmed_at = datetime.now(UTC)
    return assessment
