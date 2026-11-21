from datetime import datetime

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from app.modules.knowledge.extraction import EXTRACTOR_VERSION, Extraction
from app.modules.knowledge.manifest import VerificationStatus


class FragmentReview(BaseModel):
    model_config = ConfigDict(extra="forbid")
    locator: str = Field(min_length=1, max_length=500)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    status: VerificationStatus
    reason: str = Field(min_length=10, max_length=2000)


class SourceReview(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_id: str
    original_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    extractor_version: str = EXTRACTOR_VERSION
    reviewed_by: str = Field(min_length=1, max_length=200)
    reviewed_at: AwareDatetime
    fragments: list[FragmentReview] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_fragments(self):
        if len({f.locator for f in self.fragments}) != len(self.fragments):
            raise ValueError("Duplicate reviewed fragment")
        if self.reviewed_at > datetime.now(self.reviewed_at.tzinfo):
            raise ValueError("Review time cannot be in the future")
        return self


class Reviews(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sources: list[SourceReview]

    @model_validator(mode="after")
    def unique_sources(self):
        if len({s.source_id for s in self.sources}) != len(self.sources):
            raise ValueError("Duplicate source review")
        return self


def validate_review(
    review: SourceReview, source_id: str, original_hash: str, extraction: Extraction
) -> None:
    if (
        review.source_id != source_id
        or review.original_sha256 != original_hash
        or review.extractor_version != extraction.extractor_version
    ):
        raise ValueError("Review does not match the original or extractor version")
    fragments = {f.locator: f for f in extraction.fragments}
    for item in review.fragments:
        fragment = fragments.get(item.locator)
        if fragment is None or fragment.content_sha256 != item.content_sha256:
            raise ValueError("Review does not match the original fragment")
