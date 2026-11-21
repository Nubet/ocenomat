from datetime import datetime
from typing import Annotated
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.modules.assessments.service import AssessmentError
from app.modules.monitoring.schemas import MonitoringResponse, ReminderResponse
from app.modules.monitoring.service import monitoring, send_reminder
from app.modules.users.models import User
from app.modules.users.router import get_current_user

router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])
CurrentUser = Annotated[User, Depends(get_current_user)]
Database = Annotated[Session, Depends(get_session)]


def projection(session: Session, user: User, response: Response, *, hr: bool):
    response.headers["Cache-Control"] = "private, no-store"
    try:
        return monitoring(
            session, user, datetime.now(ZoneInfo("Europe/Warsaw")).date(), hr=hr
        )
    except AssessmentError as error:
        raise HTTPException(403, str(error)) from None
    except SQLAlchemyError:
        raise HTTPException(503, "Monitoring unavailable") from None


@router.get("/personal", response_model=MonitoringResponse)
def personal(user: CurrentUser, session: Database, response: Response):
    return projection(session, user, response, hr=False)


@router.get("/hr", response_model=MonitoringResponse)
def hr(user: CurrentUser, session: Database, response: Response):
    return projection(session, user, response, hr=True)


@router.post(
    "/hr/{assessment_id}/reminders", response_model=ReminderResponse, status_code=201
)
def remind(
    assessment_id: UUID,
    user: CurrentUser,
    session: Database,
    response: Response,
    idempotency_key: Annotated[UUID, Header()],
):
    response.headers["Cache-Control"] = "private, no-store"
    try:
        reminder, created = send_reminder(session, user, assessment_id, idempotency_key)
        response.status_code = 201 if created else 200
        return reminder
    except AssessmentError as error:
        raise HTTPException(
            {"forbidden": 403, "not_found": 404, "conflict": 409}[error.code],
            str(error),
        ) from None
    except SQLAlchemyError:
        raise HTTPException(
            503, "Reminder could not be confirmed; retry with the same key"
        ) from None
