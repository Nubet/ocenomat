from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.modules.assessments.first_rules import FIRST_ELEMENTS, first_deadlines
from app.modules.assessments.rules import FIRST_SCORES

FirstText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=10000)]
FirstBasis = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)
]


class FirstQualification(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    hired_on: date
    contract_end: date
    employment_basis: Literal["first_contract", "replacement"]
    eligibility_confirmed: bool = Field(strict=True)
    qualification_basis: FirstBasis
    ksap_graduate: bool = Field(strict=True)
    nomination_requested: bool = Field(strict=True)
    replacement_agreed_on: date | None = None

    @model_validator(mode="after")
    def eligible(self):
        if not self.eligibility_confirmed:
            raise ValueError("Confirm eligibility under articles 35(3),(5) and 37")
        if self.ksap_graduate and self.nomination_requested:
            raise ValueError(
                "KSAP graduate requesting nomination is excluded by art. 37(3)"
            )
        if self.nomination_requested and not self.ksap_graduate:
            raise ValueError("KSAP nomination request requires graduation")
        if (self.employment_basis == "replacement") != (
            self.replacement_agreed_on is not None
        ):
            raise ValueError("Replacement requires the parties' agreement date")
        first_deadlines(self.hired_on, self.contract_end, self.replacement_agreed_on)
        return self


class FirstData(FirstQualification):
    intro_on: date | None = None
    intro_confirmed: bool = Field(default=False, strict=True)
    arrangements_shared: bool = Field(default=False, strict=True)
    report_from: date | None = None
    report_to: date | None = None
    report_period_from: date | None = None
    report_period_to: date | None = None
    report_submitted_on: date | None = None
    report_missing: bool = Field(default=False, strict=True)
    report_tasks: FirstText = ""
    report_problems: FirstText = ""
    report_learning: FirstText = ""
    report_conclusions: FirstText = ""
    exam: Literal["passed", "failed", "not_applicable"] | None = None
    exam_basis: FirstText = ""
    conversation_on: date | None = None
    conversation_notes: FirstText = ""
    conversation_confirmed: bool = Field(default=False, strict=True)
    assessed_on: date | None = None
    scores: dict[str, Annotated[int, Field(strict=True)] | None] = Field(
        default_factory=lambda: dict.fromkeys(FIRST_ELEMENTS)
    )
    justification: FirstText = ""
    development_conclusions: FirstText = ""
    unit_head_name: FirstText = ""
    unit_head_position: FirstText = ""
    unit_head_agreed: bool = Field(default=False, strict=True)

    @model_validator(mode="after")
    def valid_elements_and_exemption(self):
        if set(self.scores) != set(FIRST_ELEMENTS) or any(
            score is not None and score not in FIRST_SCORES
            for score in self.scores.values()
        ):
            raise ValueError(
                "Expected exactly five identified elements scored 3, 5 or 7"
            )
        exempt = self.ksap_graduate or self.employment_basis == "replacement"
        if self.exam == "not_applicable" and (not exempt or not self.exam_basis):
            raise ValueError(
                "Exam exemption requires a statutory reason and recorded basis"
            )
        if exempt and self.exam in ("passed", "failed"):
            raise ValueError(
                "Statutory exam exemption must be recorded as not_applicable"
            )
        if self.report_missing and self.report_submitted_on is not None:
            raise ValueError("A report cannot be both missing and submitted")
        return self


class FirstUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revision: int = Field(strict=True, ge=1)
    data: FirstData
    action: Literal[
        "save", "confirm_introduction", "confirm_conversation", "complete"
    ] = "save"


class FirstDeadlineUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revision: int = Field(strict=True, ge=1)
    reason: Literal["justified_absence", "outside_workplace", "contract_extension"]
    basis: FirstBasis
    circumstance_from: date
    circumstance_to: date
    contract_end: date
    report_from: date
    report_to: date
    notified_on: date


class FirstDeadlineChangeResponse(FirstDeadlineUpdate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    author_id: UUID
    recorded_at: datetime
    previous_contract_end: date
    previous_report_from: date
    previous_report_to: date
