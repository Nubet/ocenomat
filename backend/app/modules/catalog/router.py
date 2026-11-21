from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.modules.catalog.models import CatalogVersion
from app.modules.catalog.schemas import CatalogResponse
from app.modules.users.models import User
from app.modules.users.router import get_current_user

router = APIRouter(prefix="/api/v1/catalog", tags=["catalog"])


@router.get("/criteria", response_model=CatalogResponse)
def criteria(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
    version_id: UUID | None = None,
) -> CatalogResponse:
    statement = select(CatalogVersion)
    if version_id is not None:
        statement = statement.where(CatalogVersion.id == version_id)
    catalog = session.scalar(
        statement.order_by(CatalogVersion.imported_at.desc(), CatalogVersion.id).limit(
            1
        )
    )
    if catalog is None:
        raise HTTPException(status_code=404, detail="Catalog version not found")
    return CatalogResponse(
        id=catalog.id,
        version=catalog.version,
        source_name=catalog.source_name,
        source_sha256=catalog.source_sha256,
        criteria=catalog.criteria,
    )
