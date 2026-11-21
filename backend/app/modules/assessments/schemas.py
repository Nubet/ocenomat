from datetime import date, datetime
from fractions import Fraction
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_serializer,
    model_validator,
)

from app.modules.assessments.first_schemas import (
    FirstData,
    FirstDeadlineChangeResponse,
    FirstQualification,
)
from app.modules.assessments.models import AssessmentStatus
from app.modules.assessments.rules import PERIODIC_SCORES, REQUIRED_CRITERIA
from app.modules.employees.schemas import EmployeeResponse


class AssessmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    employee_id: UUID
    kind: Literal["periodic", "first"]
    qualification: FirstQualification | None = None

    @model_validator(mode="after")
    def first_qualification(self):
        if (self.kind == "first") != (self.qualification is not None):
            raise ValueError("Only first assessments require qualification data")
        return self


class AssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: UUID
    assessor_id: UUID
    catalog_version_id: UUID
    job_description_id: UUID | None
    employee_snapshot: EmployeeResponse
    kind: Literal["periodic", "first"]
    form: Literal["B", "C", "P"]
    first: FirstData | None = None
    first_deadline_changes: list[FirstDeadlineChangeResponse] = Field(
        default_factory=list
    )
    status: AssessmentStatus
    revision: int
    created_at: datetime
    required_criterion_ids: list[UUID] = Field(
        default_factory=lambda data: list(REQUIRED_CRITERIA.get(data["form"], ()))
    )
    criteria: list["CriterionSelection"]
    date_talk: date | None
    date_assessment: date | None
    duties_discussed: bool
    expectations_discussed: bool
    arrangements_shared: bool
    observations: list["ObservationResponse"]
    conversation: "ConversationResponse | None"
    ratings: list["RatingResponse"]
    summary: "SummaryResponse | None"
    result: "ResultResponse"


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
    action: Literal[
        "agree_criteria", "start_period", "confirm_conversation", "complete"
    ]


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


class IndicatorAnswerInput(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    indicator_id: UUID
    level: int | None = Field(strict=True, ge=0, le=4)
    note: Annotated[str, StringConstraints(strip_whitespace=True, max_length=4000)]


class AnswersUpdate(RevisionCommand):
    answers: list[IndicatorAnswerInput] = Field(min_length=1, max_length=49)


class RatingConfirm(RevisionCommand):
    score: int = Field(strict=True)

    @model_validator(mode="after")
    def valid_score(self):
        if self.score not in PERIODIC_SCORES:
            raise ValueError("Expected a periodic score: 1, 3, 5, 7 or 9")
        return self


class RatingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    criterion_id: UUID
    answers: list[IndicatorAnswerInput]
    suggested_score: int | None
    policy_version: str
    author_id: UUID
    recorded_at: datetime
    score: int | None
    confirmed_by: UUID | None
    confirmed_at: datetime | None


class SummaryUpdate(RevisionCommand):
    negative_justification: Annotated[
        str, StringConstraints(strip_whitespace=True, max_length=10000)
    ]
    development_conclusions: Annotated[
        str, StringConstraints(strip_whitespace=True, max_length=10000)
    ]


class SummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    negative_justification: str
    development_conclusions: str
    author_id: UUID
    recorded_at: datetime
    completed_by: UUID | None
    completed_at: datetime | None


class ResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    outcome: Literal["incomplete", "positive", "negative"]
    mean: Fraction | None

    @field_serializer("mean")
    def display_mean(self, value: Fraction | None) -> str | None:
        return format(value, ".2f") if value is not None else None
