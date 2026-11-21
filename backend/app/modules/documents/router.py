from typing import Annotated
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.core.database import get_session
from app.integrations.storage import StorageUnavailable
from app.modules.assessments.router import assessment_http_error
from app.modules.assessments.service import AssessmentError
from app.modules.documents import service
from app.modules.documents.models import Document
from app.modules.documents.schemas import DocumentResponse, DocumentUploadResponse
from app.modules.documents.validation import (
    DOCX_TYPE,
    MAX_FILE_SIZE,
    PDF_TYPE,
    InvalidDocument,
    validate_filename,
)
from app.modules.users.models import User
from app.modules.users.router import get_current_user

router = APIRouter(
    prefix="/api/v1/assessments/{assessment_id}/documents", tags=["documents"]
)


@router.post(
    "",
    response_model=DocumentUploadResponse,
    status_code=201,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                media_type: {"schema": {"type": "string", "format": "binary"}}
                for media_type in (
                    PDF_TYPE,
                    DOCX_TYPE,
                    "application/octet-stream",
                )
            },
        }
    },
)
async def upload(
    assessment_id: UUID,
    request: Request,
    response: Response,
    revision: Annotated[int, Query(ge=1)],
    filename: Annotated[str, Query(min_length=1, max_length=255)],
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> DocumentUploadResponse:
    try:
        assessment = await run_in_threadpool(
            service.authorized_assessment, session, user, assessment_id
        )
        validate_filename(filename)
        content = bytearray()
        async for chunk in request.stream():
            if len(content) + len(chunk) > MAX_FILE_SIZE:
                raise HTTPException(status_code=413, detail="File exceeds 10 MiB")
            content.extend(chunk)
        storage = request.app.state.object_storage
        if storage is None:
            raise StorageUnavailable()
        result = await run_in_threadpool(
            service.upload_document,
            session,
            user,
            assessment,
            revision,
            filename,
            request.headers.get("content-type", ""),
            bytes(content),
            storage,
        )
        response.headers["Cache-Control"] = "private, no-store"
        return result
    except AssessmentError as error:
        raise assessment_http_error(error) from None
    except InvalidDocument as error:
        raise HTTPException(status_code=422, detail=str(error)) from None
    except (StorageUnavailable, SQLAlchemyError):
        raise HTTPException(
            status_code=503, detail="Document storage unavailable"
        ) from None


@router.get("", response_model=list[DocumentResponse])
def documents(
    assessment_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
    response: Response,
) -> list[Document]:
    try:
        result = service.list_documents(session, user, assessment_id)
    except AssessmentError as error:
        raise assessment_http_error(error) from None
    except SQLAlchemyError:
        raise HTTPException(
            status_code=503, detail="Document metadata unavailable"
        ) from None
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.get(
    "/{document_id}/download",
    response_class=Response,
    responses={
        200: {
            "content": {
                media_type: {"schema": {"type": "string", "format": "binary"}}
                for media_type in (PDF_TYPE, DOCX_TYPE)
            }
        }
    },
)
def download(
    assessment_id: UUID,
    document_id: UUID,
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> Response:
    try:
        storage = request.app.state.object_storage
        document, content = service.download_document(
            session, user, assessment_id, document_id, storage
        )
    except AssessmentError as error:
        raise assessment_http_error(error) from None
    except (StorageUnavailable, SQLAlchemyError):
        raise HTTPException(
            status_code=503, detail="Document storage unavailable"
        ) from None
    filename = quote(document.filename, safe="")
    return Response(
        content,
        media_type=document.media_type,
        headers={
            "Content-Disposition": f"attachment; filename*=utf-8''{filename}",
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )
