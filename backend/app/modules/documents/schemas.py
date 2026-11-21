from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator

from app.modules.assessments.schemas import RevisionCommand


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    assessment_id: UUID | None
    kind: Literal["attachment", "osp", "periodic_pdf"]
    template_version: str | None
    assessment_revision: int | None
    filename: str
    media_type: str
    size: int
    sha256: str
    author_id: UUID
    created_at: datetime


class DocumentUploadResponse(BaseModel):
    document: DocumentResponse
    assessment_revision: int


class JobDescriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: UUID
    version: int
    document: DocumentResponse


class JobDescriptionSelection(RevisionCommand):
    job_description_id: UUID


RequiredText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]


class PreviousAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcome: Literal["positive", "negative"]
    level: Literal[1, 2, 3, 4, 5]
    assessed_on: date


class PdfGeneration(RevisionCommand):
    office_name: RequiredText
    assessor_department: RequiredText
    assessor_position: RequiredText
    period_end: date
    civil_service_status: Literal["employee", "official"]
    previous_assessment: PreviousAssessment | None
    no_promotion_request: Literal[True]

    @model_validator(mode="after")
    def previous_applies_to_official(self):
        if (
            self.civil_service_status == "employee"
            and self.previous_assessment is not None
        ):
            raise ValueError(
                "Previous official assessment does not apply to an employee"
            )
        return self
