from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.modules.assessments.completion import complete_assessment, save_summary
from app.modules.assessments.evaluation import confirm_rating, save_answers
from app.modules.assessments.models import Assessment
from app.modules.assessments.rules import Result
from app.modules.assessments.schemas import (
    AnswersUpdate,
    AssessmentCreate,
    AssessmentResponse,
    AssessmentTransition,
    ConversationUpdate,
    CriteriaUpdate,
    DatesUpdate,
    ObservationCreate,
    RatingConfirm,
    ResultResponse,
    SummaryUpdate,
)
from app.modules.assessments.service import (
    AssessmentError,
    accessible_assessments,
    add_observation,
    agree_criteria,
    confirm_conversation,
    create_assessment,
    save_conversation,
    save_criteria,
    save_dates,
    start_period,
)
from app.modules.users.models import User
from app.modules.users.router import get_current_user

router = APIRouter(prefix="/api/v1/assessments", tags=["assessments"])


def assessment_http_error(error: AssessmentError) -> HTTPException:
    status = {
        "not_found": 404,
        "forbidden": 403,
        "unsupported": 422,
        "invalid": 422,
        "conflict": 409,
        "catalog_unavailable": 503,
    }[error.code]
    return HTTPException(status_code=status, detail=str(error))


@router.get("", response_model=list[AssessmentResponse])
def assessments(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
    response: Response,
    employee_id: UUID | None = None,
) -> list[Assessment]:
    response.headers["Cache-Control"] = "private, no-store"
    statement = accessible_assessments(user)
    if employee_id is not None:
        statement = statement.where(Assessment.employee_id == employee_id)
    return list(
        session.scalars(statement.order_by(Assessment.created_at.desc(), Assessment.id))
    )


@router.post("", response_model=AssessmentResponse, status_code=201)
def create(
    data: AssessmentCreate,
    key: Annotated[UUID, Header(alias="Idempotency-Key")],
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
    response: Response,
) -> Assessment:
    try:
        assessment, created = create_assessment(session, user, data, key)
    except AssessmentError as error:
        raise assessment_http_error(error) from None
    response.status_code = 201 if created else 200
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["Location"] = f"/api/v1/assessments/{assessment.id}"
    return assessment


@router.put("/{assessment_id}/criteria", response_model=AssessmentResponse)
def update_criteria(
    assessment_id: UUID,
    data: CriteriaUpdate,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
    response: Response,
) -> Assessment:
    try:
        result = save_criteria(session, user, assessment_id, data)
    except AssessmentError as error:
        raise assessment_http_error(error) from None
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.patch("/{assessment_id}", response_model=AssessmentResponse)
def update_dates(
    assessment_id: UUID,
    data: DatesUpdate,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
    response: Response,
) -> Assessment:
    try:
        result = save_dates(session, user, assessment_id, data)
    except AssessmentError as error:
        raise assessment_http_error(error) from None
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.post("/{assessment_id}/transitions", response_model=AssessmentResponse)
def transition(
    assessment_id: UUID,
    data: AssessmentTransition,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
    response: Response,
) -> Assessment:
    try:
        operation = {
            "agree_criteria": agree_criteria,
            "start_period": start_period,
            "confirm_conversation": confirm_conversation,
            "complete": complete_assessment,
        }[data.action]
        result = operation(session, user, assessment_id, data.revision)
    except AssessmentError as error:
        raise assessment_http_error(error) from None
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.post("/{assessment_id}/observations", response_model=AssessmentResponse)
def create_observation(
    assessment_id: UUID,
    data: ObservationCreate,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
    response: Response,
) -> Assessment:
    try:
        result = add_observation(session, user, assessment_id, data)
    except AssessmentError as error:
        raise assessment_http_error(error) from None
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.put("/{assessment_id}/conversation", response_model=AssessmentResponse)
def update_conversation(
    assessment_id: UUID,
    data: ConversationUpdate,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
    response: Response,
) -> Assessment:
    try:
        result = save_conversation(session, user, assessment_id, data)
    except AssessmentError as error:
        raise assessment_http_error(error) from None
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.put(
    "/{assessment_id}/criteria/{criterion_id}/answers",
    response_model=AssessmentResponse,
)
def update_answers(
    assessment_id: UUID,
    criterion_id: UUID,
    data: AnswersUpdate,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
    response: Response,
) -> Assessment:
    try:
        result = save_answers(session, user, assessment_id, criterion_id, data)
    except AssessmentError as error:
        raise assessment_http_error(error) from None
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.post(
    "/{assessment_id}/criteria/{criterion_id}/rating", response_model=AssessmentResponse
)
def approve_rating(
    assessment_id: UUID,
    criterion_id: UUID,
    data: RatingConfirm,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
    response: Response,
) -> Assessment:
    try:
        result = confirm_rating(session, user, assessment_id, criterion_id, data)
    except AssessmentError as error:
        raise assessment_http_error(error) from None
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.put("/{assessment_id}/summary", response_model=AssessmentResponse)
def update_summary(
    assessment_id: UUID,
    data: SummaryUpdate,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
    response: Response,
) -> Assessment:
    try:
        result = save_summary(session, user, assessment_id, data)
    except AssessmentError as error:
        raise assessment_http_error(error) from None
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.get("/{assessment_id}/result", response_model=ResultResponse)
def assessment_result(
    assessment_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
    response: Response,
) -> Result:
    return assessment_detail(assessment_id, user, session, response).result


@router.get("/{assessment_id}", response_model=AssessmentResponse)
def assessment_detail(
    assessment_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
    response: Response,
) -> Assessment:
    assessment = session.scalar(
        accessible_assessments(user).where(Assessment.id == assessment_id)
    )
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    response.headers["Cache-Control"] = "private, no-store"
    return assessment
