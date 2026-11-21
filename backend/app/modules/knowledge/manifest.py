from pathlib import Path, PurePosixPath
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SourceType = Literal[
    "legal_act",
    "legal_appendix",
    "official_guideline",
    "official_form",
    "competency_catalog",
    "sample_job_description",
]
VerificationStatus = Literal["unverified", "needs_review", "approved", "rejected"]
LegalStatus = Literal["verified_current", "historical", "unknown"]


class SourceSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str = Field(pattern=r"^[a-z][a-z0-9-]{2,99}$")
    title: str = Field(min_length=1, max_length=300)
    path: str
    markdown_path: str | None = None
    source_type: SourceType
    assessment_kind: Literal["first", "periodic", "both"] = "both"
    document_version: str = Field(min_length=1, max_length=100)
    legal_status: LegalStatus = "unknown"
    parent_source_id: str | None = None

    @field_validator("path", "markdown_path")
    @classmethod
    def relative_path(cls, value: str | None) -> str | None:
        if value is not None and (
            not value
            or PurePosixPath(value).is_absolute()
            or ".." in PurePosixPath(value).parts
            or "\\" in value
        ):
            raise ValueError("Expected a relative path inside the materials directory")
        return value


class Manifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sources: list[SourceSpec] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_sources(self):
        ids = {source.source_id for source in self.sources}
        if len(ids) != len(self.sources):
            raise ValueError("Duplicate source ID")
        if len({source.path for source in self.sources}) != len(self.sources):
            raise ValueError("Duplicate original path")
        for source in self.sources:
            seen = {source.source_id}
            parent = source.parent_source_id
            while parent:
                if parent not in ids or parent in seen:
                    raise ValueError("Missing or cyclic parent source")
                seen.add(parent)
                parent = next(
                    s for s in self.sources if s.source_id == parent
                ).parent_source_id
        return self


def material_path(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError("Source file missing or outside the materials directory")
    return path
