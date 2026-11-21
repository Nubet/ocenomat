import hashlib
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.integrations.storage import ObjectStorage, StorageUnavailable
from app.modules.assessments.models import AssessmentStatus
from app.modules.assessments.rules import REQUIRED_CRITERIA
from app.modules.assessments.service import AssessmentError, assessment_transaction
from app.modules.catalog.models import CatalogVersion
from app.modules.documents.models import Document
from app.modules.documents.pdf import (
    SOURCE_SHA256,
    TEMPLATE_VERSION,
    PeriodicPdfData,
    render_periodic_pdf,
)
from app.modules.documents.schemas import PdfGeneration
from app.modules.documents.service import discard_uncommitted_object
from app.modules.documents.validation import MAX_FILE_SIZE, PDF_TYPE, InvalidDocument
from app.modules.users.models import User


def generate_periodic_pdf(
    session: Session,
    user: User,
    assessment_id: UUID,
    data: PdfGeneration,
    storage: ObjectStorage | None,
    font_path: Path,
) -> Document:
    document_id = uuid4()
    key = f"assessments/{assessment_id}/{document_id}"
    attempted = False
    commit_pending = False
    try:
        with assessment_transaction(session, user, assessment_id) as assessment:
            if (
                assessment.status != AssessmentStatus.COMPLETED
                or assessment.revision != data.revision
            ):
                raise AssessmentError(
                    "conflict", "Generate from the current completed revision"
                )
            existing = session.scalar(
                select(Document).where(
                    Document.assessment_id == assessment_id,
                    Document.assessment_revision == data.revision,
                    Document.template_version == TEMPLATE_VERSION,
                )
            )
            generation_data = data.model_dump(mode="json", exclude={"revision"})
            generation_data["source_sha256"] = SOURCE_SHA256
            generation_data["job_description_id"] = (
                str(assessment.job_description_id)
                if assessment.job_description_id
                else None
            )
            if existing is not None:
                if existing.generation_data != generation_data:
                    raise AssessmentError(
                        "conflict",
                        "Document has already been generated with different details",
                    )
                return existing
            summary = assessment.summary
            if (
                assessment.form != "C"
                or summary is None
                or summary.completed_at is None
                or assessment.result.outcome == "incomplete"
                or assessment.conversation is None
                or assessment.conversation.confirmed_at is None
                or assessment.conversation.occurred_on is None
                or assessment.date_talk is None
                or assessment.date_assessment is None
            ):
                raise AssessmentError(
                    "invalid", "Completed assessment data is incomplete"
                )
            if (
                not assessment.date_talk
                <= data.period_end
                <= datetime.now(ZoneInfo("Europe/Warsaw")).date()
            ):
                raise AssessmentError(
                    "invalid",
                    "End date must be between the opening conversation and today",
                )
            if (
                data.previous_assessment is not None
                and data.previous_assessment.assessed_on > assessment.date_talk
            ):
                raise AssessmentError(
                    "invalid", "Previous assessment must precede this period"
                )
            catalog = session.get(CatalogVersion, assessment.catalog_version_id)
            names = {UUID(item["id"]): item["name"] for item in catalog.criteria}
            scores = {
                item.criterion_id: item.score
                for item in assessment.ratings
                if item.confirmed_at is not None
            }
            criteria = sorted(
                assessment.criteria,
                key=lambda item: (
                    not item.required,
                    REQUIRED_CRITERIA["C"].index(item.criterion_id)
                    if item.required
                    else names.get(item.criterion_id, ""),
                ),
            )
            if (
                len(criteria) != summary.score_count
                or sum(scores.get(item.criterion_id) or 0 for item in criteria)
                != summary.score_total
                or any(
                    item.criterion_id not in names
                    or scores.get(item.criterion_id) not in (1, 3, 5, 7, 9)
                    for item in criteria
                )
                or (
                    summary.outcome == "negative"
                    and not summary.negative_justification.strip()
                )
            ):
                raise AssessmentError(
                    "invalid", "Confirmed decisions do not match the completed result"
                )
            content = render_periodic_pdf(
                PeriodicPdfData(
                    assessment_id=str(assessment.id),
                    revision=assessment.revision,
                    employee=assessment.employee_snapshot,
                    assessor_name=user.display_name,
                    criteria=[
                        (
                            names[item.criterion_id],
                            item.required,
                            scores[item.criterion_id],
                        )
                        for item in criteria
                    ],
                    date_talk=assessment.date_talk,
                    date_assessment=assessment.date_assessment,
                    conversation_date=assessment.conversation.occurred_on,
                    result=assessment.result,
                    justification=summary.negative_justification,
                    development_conclusions=summary.development_conclusions,
                    details=data,
                ),
                font_path,
            )
            if len(content) > MAX_FILE_SIZE:
                raise InvalidDocument("Generated PDF exceeds 10 MiB")
            if storage is None:
                raise StorageUnavailable()
            document = Document(
                id=document_id,
                assessment_id=assessment.id,
                kind="periodic_pdf",
                filename=f"Arkusz-C-{assessment.id}.pdf",
                media_type=PDF_TYPE,
                size=len(content),
                sha256=hashlib.sha256(content).hexdigest(),
                object_key=key,
                author_id=user.id,
                template_version=TEMPLATE_VERSION,
                assessment_revision=assessment.revision,
                generation_data=generation_data,
            )
            attempted = True
            storage.put(key, content, PDF_TYPE)
            session.add(document)
            session.flush()
            commit_pending = True
        return document
    except Exception as error:
        if attempted:
            discard_uncommitted_object(
                session, document_id, key, storage, commit_pending
            )
        if isinstance(error, SQLAlchemyError):
            raise StorageUnavailable("Document metadata unavailable") from None
        raise
