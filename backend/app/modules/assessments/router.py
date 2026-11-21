from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.modules.assessments.models import Assessment
from app.modules.assessments.schemas import AssessmentCreate, AssessmentResponse
from app.modules.assessments.service import (
    AssessmentError,
    accessible_assessments,
    create_assessment,
)
from app.modules.users.models import User
from app.modules.users.router import get_current_user

router = APIRouter(prefix="/api/v1/assessments", tags=["assessments"])


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
        status = {
            "not_found": 404,
            "forbidden": 403,
            "unsupported": 422,
            "conflict": 409,
            "catalog_unavailable": 503,
        }[error.code]
        raise HTTPException(status_code=status, detail=str(error)) from None
    response.status_code = 201 if created else 200
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["Location"] = f"/api/v1/assessments/{assessment.id}"
    return assessment


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
