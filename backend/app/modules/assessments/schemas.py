from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.modules.assessments.models import AssessmentStatus
from app.modules.assessments.rules import REQUIRED_CRITERIA
from app.modules.employees.schemas import EmployeeResponse


class AssessmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    employee_id: UUID
    kind: Literal["periodic"]


class AssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: UUID
    assessor_id: UUID
    catalog_version_id: UUID
    employee_snapshot: EmployeeResponse
    kind: Literal["periodic"]
    form: Literal["C"]
    status: AssessmentStatus
    revision: int
    created_at: datetime
    required_criterion_ids: list[UUID] = Field(
        default_factory=lambda: list(REQUIRED_CRITERIA["C"])
    )
    criteria: list["CriterionSelection"]
    date_talk: date | None
    date_assessment: date | None
    duties_discussed: bool
    expectations_discussed: bool
    arrangements_shared: bool
    observations: list["ObservationResponse"]
    conversation: "ConversationResponse | None"


class CriterionSelection(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    criterion_id: UUID
    required: bool
    justification: str | None


class RevisionCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revision: int = Field(strict=True, ge=1)


class AdditionalCriterion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criterion_id: UUID
    justification: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)
    ]


class CriteriaUpdate(RevisionCommand):
    additional: list[AdditionalCriterion] = Field(max_length=3)


class DatesUpdate(RevisionCommand):
    date_talk: date
    date_assessment: date
    duties_discussed: bool = Field(strict=True)
    expectations_discussed: bool = Field(strict=True)
    arrangements_shared: bool = Field(strict=True)

    @model_validator(mode="after")
    def ordered_dates(self):
        if self.date_assessment < self.date_talk:
            raise ValueError(
                "Assessment date must not precede the opening conversation"
            )
        return self


class AssessmentTransition(RevisionCommand):
    action: Literal["agree_criteria", "start_period", "confirm_conversation"]


class ObservationCreate(RevisionCommand):
    criterion_id: UUID
    text: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=10000)
    ]
    occurred_on: date


class ObservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    criterion_id: UUID
    text: str
    occurred_on: date
    author_id: UUID
    recorded_at: datetime


class ConversationUpdate(RevisionCommand):
    agenda: Annotated[str, StringConstraints(strip_whitespace=True, max_length=10000)]
    strengths: Annotated[
        str, StringConstraints(strip_whitespace=True, max_length=10000)
    ]
    growth: Annotated[str, StringConstraints(strip_whitespace=True, max_length=10000)]
    occurred_on: date | None


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    agenda: str
    strengths: str
    growth: str
    occurred_on: date | None
    author_id: UUID
    recorded_at: datetime
    confirmed_at: datetime | None
    confirmed_by: UUID | None
