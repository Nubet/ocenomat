import hashlib
import logging
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.integrations.storage import ObjectStorage, StorageUnavailable
from app.modules.assessments.models import Assessment, AssessmentStatus
from app.modules.assessments.service import (
    AssessmentError,
    accessible_assessments,
    edit_assessment,
)
from app.modules.documents.models import Document, JobDescription
from app.modules.documents.schemas import DocumentResponse, DocumentUploadResponse
from app.modules.documents.validation import validate_content, validate_filename
from app.modules.employees.models import Employee
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
    *,
    kind: str = "attachment",
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
            "job_description_uploaded" if kind == "osp" else "document_uploaded",
            allowed_kind=None,
            allowed_status=AssessmentStatus.DRAFT
            if kind == "osp"
            else assessment.status,
        ) as current:
            if current.status == AssessmentStatus.COMPLETED:
                raise AssessmentError("conflict", "Completed assessments are read-only")
            document = Document(
                id=document_id,
                kind=kind,
                assessment_id=None if kind == "osp" else current.id,
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
            if kind == "osp":
                description = record_job_description(
                    session, current.employee_id, document
                )
                current.job_description_id = description.id
            result = DocumentUploadResponse(
                document=DocumentResponse.model_validate(document),
                assessment_revision=current.revision + 1,
            )
            commit_pending = True
        return result
    except Exception as error:
        if attempted:
            discard_uncommitted_object(
                session, document_id, key, storage, commit_pending
            )
        if isinstance(error, SQLAlchemyError):
            raise StorageUnavailable("Document metadata unavailable") from None
        raise


def discard_uncommitted_object(
    session: Session,
    document_id: UUID,
    key: str,
    storage: ObjectStorage,
    commit_pending: bool,
) -> None:
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


def record_job_description(
    session: Session, employee_id: UUID, document: Document
) -> JobDescription:
    session.execute(
        select(Employee.id)
        .where(Employee.id == employee_id)
        .with_for_update(of=Employee)
    )
    version = (
        session.scalar(
            select(func.max(JobDescription.version)).where(
                JobDescription.employee_id == employee_id
            )
        )
        or 0
    ) + 1
    description = JobDescription(
        employee_id=employee_id, document_id=document.id, version=version
    )
    session.add(description)
    session.flush()
    return description


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
    assessment = authorized_assessment(session, user, assessment_id)
    document = session.scalar(
        select(Document).where(
            Document.id == document_id,
            (Document.assessment_id == assessment_id)
            | Document.id.in_(
                select(JobDescription.document_id).where(
                    JobDescription.employee_id == assessment.employee_id
                )
            ),
        )
    )
    if document is None:
        raise AssessmentError("not_found", "Document not found")
    if storage is None:
        raise StorageUnavailable()
    return document, read_document(document, storage)


def read_document(document: Document, storage: ObjectStorage | None) -> bytes:
    if storage is None:
        raise StorageUnavailable()
    content = storage.get(document.object_key, document.size)
    if hashlib.sha256(content).hexdigest() != document.sha256:
        raise StorageUnavailable("Stored file is inconsistent")
    return content


def list_job_descriptions(
    session: Session, user: User, assessment_id: UUID
) -> list[JobDescription]:
    assessment = authorized_assessment(session, user, assessment_id)
    return list(
        session.scalars(
            select(JobDescription)
            .where(JobDescription.employee_id == assessment.employee_id)
            .order_by(JobDescription.version.desc())
        )
    )


def selected_job_description(
    session: Session, assessment: Assessment, description_id: UUID
) -> JobDescription:
    description = session.get(JobDescription, description_id)
    if description is None or description.employee_id != assessment.employee_id:
        raise AssessmentError("not_found", "Job description not found")
    return description


def select_job_description(
    session: Session,
    user: User,
    assessment_id: UUID,
    revision: int,
    description_id: UUID,
) -> Assessment:
    with edit_assessment(
        session,
        user,
        assessment_id,
        revision,
        "job_description_selected",
        allowed_kind=None,
    ) as assessment:
        selected_job_description(session, assessment, description_id)
        assessment.job_description_id = description_id
    return assessment
