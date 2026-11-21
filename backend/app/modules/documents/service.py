import hashlib
import logging
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.integrations.storage import ObjectStorage, StorageUnavailable
from app.modules.assessments.models import Assessment, AssessmentStatus
from app.modules.assessments.service import (
    AssessmentError,
    accessible_assessments,
    edit_assessment,
)
from app.modules.documents.models import Document
from app.modules.documents.schemas import DocumentResponse, DocumentUploadResponse
from app.modules.documents.validation import validate_content, validate_filename
from app.modules.users.models import User

logger = logging.getLogger(__name__)


def authorized_assessment(
    session: Session, user: User, assessment_id: UUID
) -> Assessment:
    assessment = session.scalar(
        accessible_assessments(user).where(Assessment.id == assessment_id)
    )
    if assessment is None:
        raise AssessmentError("not_found", "Assessment not found")
    return assessment


def upload_document(
    session: Session,
    user: User,
    assessment: Assessment,
    revision: int,
    filename: str,
    declared_type: str,
    content: bytes,
    storage: ObjectStorage,
) -> DocumentUploadResponse:
    filename = validate_filename(filename)
    media_type = validate_content(content, filename, declared_type)
    document_id = uuid4()
    key = f"assessments/{assessment.id}/{document_id}"
    attempted = False
    commit_pending = False
    try:
        with edit_assessment(
            session,
            user,
            assessment.id,
            revision,
            "document_uploaded",
            allowed_status=assessment.status,
        ) as current:
            if current.status == AssessmentStatus.COMPLETED:
                raise AssessmentError("conflict", "Completed assessments are read-only")
            document = Document(
                id=document_id,
                assessment_id=current.id,
                filename=filename,
                media_type=media_type,
                size=len(content),
                sha256=hashlib.sha256(content).hexdigest(),
                object_key=key,
                author_id=user.id,
            )
            attempted = True
            storage.put(key, content, media_type)
            session.add(document)
            session.flush()
            result = DocumentUploadResponse(
                document=DocumentResponse.model_validate(document),
                assessment_revision=current.revision + 1,
            )
            commit_pending = True
        return result
    except Exception as error:
        if attempted:
            safe_to_delete = not commit_pending
            if commit_pending:
                # A lost COMMIT acknowledgement must not delete a persisted file.
                try:
                    safe_to_delete = session.get(Document, document_id) is None
                except SQLAlchemyError:
                    logger.error("Storage reconciliation required for object %s", key)
            if safe_to_delete:
                try:
                    storage.delete(key)
                except StorageUnavailable:
                    logger.error("Storage cleanup required for object %s", key)
        if isinstance(error, SQLAlchemyError):
            raise StorageUnavailable("Document metadata unavailable") from None
        raise


def list_documents(session: Session, user: User, assessment_id: UUID) -> list[Document]:
    authorized_assessment(session, user, assessment_id)
    return list(
        session.scalars(
            select(Document)
            .where(Document.assessment_id == assessment_id)
            .order_by(Document.created_at, Document.id)
        )
    )


def download_document(
    session: Session,
    user: User,
    assessment_id: UUID,
    document_id: UUID,
    storage: ObjectStorage | None,
) -> tuple[Document, bytes]:
    authorized_assessment(session, user, assessment_id)
    document = session.scalar(
        select(Document).where(
            Document.id == document_id, Document.assessment_id == assessment_id
        )
    )
    if document is None:
        raise AssessmentError("not_found", "Document not found")
    if storage is None:
        raise StorageUnavailable()
    content = storage.get(document.object_key, document.size)
    if hashlib.sha256(content).hexdigest() != document.sha256:
        raise StorageUnavailable("Stored file is inconsistent")
    return document, content
