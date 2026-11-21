from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.security import get_subject, unauthorized
from app.modules.users.models import Role, User

router = APIRouter(prefix="/api/v1", tags=["users"])


def get_current_user(
    subject: Annotated[UUID, Depends(get_subject)],
    session: Annotated[Session, Depends(get_session)],
) -> User:
    user = session.scalar(
        select(User).where(User.auth_subject == subject, User.active.is_(True))
    )
    if user is None:
        raise unauthorized()
    return user


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_name: str
    roles: list[Role]


@router.get("/me", response_model=UserResponse)
def me(user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    return UserResponse(
        id=user.id,
        display_name=user.display_name,
        roles=sorted(r.role for r in user.roles),
    )
