from typing import Annotated, Literal
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.core.database import get_session
from app.integrations.storage import StorageUnavailable
from app.modules.assessments.router import assessment_http_error
from app.modules.assessments.schemas import AssessmentResponse
from app.modules.assessments.service import AssessmentError
from app.modules.documents import service
from app.modules.documents.generation import generate_periodic_pdf
from app.modules.documents.models import Document, JobDescription
from app.modules.documents.pdf import PdfUnavailable
from app.modules.documents.schemas import (
    DocumentResponse,
    DocumentUploadResponse,
    JobDescriptionResponse,
    JobDescriptionSelection,
    PdfGeneration,
)
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
    kind: Literal["attachment", "osp"] = "attachment",
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
            kind=kind,
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


@router.get("/job-descriptions", response_model=list[JobDescriptionResponse])
def job_descriptions(
    assessment_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
    response: Response,
) -> list[JobDescription]:
    try:
        result = service.list_job_descriptions(session, user, assessment_id)
    except AssessmentError as error:
        raise assessment_http_error(error) from None
    except SQLAlchemyError:
        raise HTTPException(503, "Document metadata unavailable") from None
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.put("/job-descriptions/select", response_model=AssessmentResponse)
def select_description(
    assessment_id: UUID,
    data: JobDescriptionSelection,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
    response: Response,
):
    try:
        result = service.select_job_description(
            session, user, assessment_id, data.revision, data.job_description_id
        )
    except AssessmentError as error:
        raise assessment_http_error(error) from None
    except SQLAlchemyError:
        raise HTTPException(503, "Document metadata unavailable") from None
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.post("/periodic-pdf", response_model=DocumentResponse)
def generate_pdf(
    assessment_id: UUID,
    data: PdfGeneration,
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
    response: Response,
) -> Document:
    try:
        result = generate_periodic_pdf(
            session,
            user,
            assessment_id,
            data,
            request.app.state.object_storage,
            request.app.state.pdf_font_path,
        )
    except AssessmentError as error:
        raise assessment_http_error(error) from None
    except InvalidDocument as error:
        raise HTTPException(422, str(error)) from None
    except (StorageUnavailable, PdfUnavailable, SQLAlchemyError):
        raise HTTPException(503, "Document generation unavailable") from None
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.get(
    "/job-descriptions/{description_id}/download",
    response_class=Response,
    responses={
        200: {
            "content": {
                media: {"schema": {"type": "string", "format": "binary"}}
                for media in (PDF_TYPE, DOCX_TYPE)
            }
        }
    },
)
def download_description(
    assessment_id: UUID,
    description_id: UUID,
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> Response:
    try:
        assessment = service.authorized_assessment(session, user, assessment_id)
        description = service.selected_job_description(
            session, assessment, description_id
        )
        document = description.document
        content = service.read_document(document, request.app.state.object_storage)
    except AssessmentError as error:
        raise assessment_http_error(error) from None
    except (StorageUnavailable, SQLAlchemyError):
        raise HTTPException(503, "Document storage unavailable") from None
    return file_response(document, content)


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
    return file_response(document, content)


def file_response(document: Document, content: bytes) -> Response:
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
