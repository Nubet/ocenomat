from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.integrations.storage import StorageUnavailable
from app.modules.knowledge.extraction import sha256
from app.modules.knowledge.models import KnowledgeChunk, KnowledgeSource
from app.modules.knowledge.retriever import source_provenance, usable
from app.modules.users.models import User
from app.modules.users.router import get_current_user

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


@router.get("/sources/{source_id}/original", response_class=Response)
def original(
    source_id: str,
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> Response:
    try:
        source = session.get(KnowledgeSource, source_id)
        if source is None or source_provenance(source) is None:
            raise HTTPException(404, "Source not found")
        chunks = session.scalars(
            select(KnowledgeChunk).where(
                KnowledgeChunk.source_id == source_id,
                KnowledgeChunk.verification_status == "approved",
            )
        )
        if not any(usable(part) for part in chunks):
            raise HTTPException(404, "Source not found")
        storage = request.app.state.object_storage
        if storage is None:
            raise StorageUnavailable()
        content = storage.get(source.storage_key, source.original_size)
        if sha256(content) != source.original_sha256:
            raise StorageUnavailable()
        return Response(
            content,
            media_type=source.media_type,
            headers={
                "Content-Disposition": (
                    "attachment; filename*=utf-8''"
                    + quote(source.original_filename, safe="")
                ),
                "Cache-Control": "private, no-store",
                "X-Content-Type-Options": "nosniff",
                "Content-Security-Policy": "sandbox; default-src 'none'",
            },
        )
    except (SQLAlchemyError, StorageUnavailable):
        raise HTTPException(
            503,
            "Source storage unavailable",
            headers={"Cache-Control": "private, no-store"},
        ) from None
