from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.assessments.schemas import ResultResponse


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class AssistantRequest(StrictModel):
    question: str = Field(min_length=1, max_length=1000)
    mode: Literal["formal", "conversation"] = "formal"
    assessment_id: UUID | None = None
    assessment_kind: Literal["first", "periodic", "unspecified"] = "unspecified"
    task: Literal["question", "assessment_result"] = "question"

    @field_validator("question")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Question cannot be blank")
        return value.strip()


class EvidenceReference(StrictModel):
    chunk_id: UUID
    quote: str = Field(min_length=8, max_length=4000)


class GroundedClaim(StrictModel):
    text: str = Field(min_length=1, max_length=2000)
    evidence: list[EvidenceReference] = Field(min_length=1, max_length=5)


class GroundedAnswer(StrictModel):
    status: Literal["answered", "insufficient_evidence", "conflicting_sources"]
    claims: list[GroundedClaim] = Field(max_length=8)


class SupportReview(StrictModel):
    status: Literal["supported", "insufficient_evidence", "conflicting_sources"]
    supported_claims: list[int] = Field(max_length=8)
    answers_question: bool


class Citation(StrictModel):
    chunk_id: UUID
    source_id: str
    title: str
    document_version: str
    locator: str
    page: int | None
    quote: str
    content_sha256: str
    legal_checked_on: date
    original_path: str


class AssistantClaim(StrictModel):
    text: str
    citations: list[Citation]


class AssistantResponse(StrictModel):
    status: Literal["answered", "insufficient_evidence", "conflicting_sources"]
    mode: Literal["formal", "conversation"]
    claims: list[AssistantClaim] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    result: ResultResponse | None = None
