from datetime import date
from pathlib import Path, PurePosixPath
from typing import Literal
from urllib.parse import urlsplit

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


def validate_official_url(value: str | None) -> str | None:
    if value is not None:
        url = urlsplit(value)
        if (
            url.scheme != "https"
            or url.hostname
            not in ("eli.gov.pl", "api.sejm.gov.pl", "isap.sejm.gov.pl", "www.gov.pl")
            or url.username
            or url.password
            or url.port not in (None, 443)
        ):
            raise ValueError("Expected an HTTPS URL on an official source host")
    return value


class Representation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    url: str | None = None
    relation: Literal["identical_bytes", "equivalent_text", "alternative_format"]
    _official_url = field_validator("url")(validate_official_url)


class Provenance(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    canonical_document_id: str = Field(min_length=1, max_length=200)
    original_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    official_url: str | None = None
    preferred_text_path: str | None = None
    usage: Literal["context", "validation_only", "example_only", "duplicate_subset"] = (
        "context"
    )
    legal_checked_on: date | None = None
    legal_status_url: str | None = None
    note: str = Field(min_length=1)
    representations: list[Representation] = []
    _official_urls = field_validator("official_url", "legal_status_url")(
        validate_official_url
    )


class SourceSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str = Field(pattern=r"^[a-z][a-z0-9-]{2,99}$")
    title: str = Field(min_length=1, max_length=300)
    path: str
    markdown_path: str | None = None
    source_type: SourceType
    assessment_kind: Literal["first", "periodic", "both"] = "both"
    document_version: str = Field(min_length=1, max_length=100)
    extraction_profile: Literal[
        "original", "eli-html-v1", "kprm-faq-v1", "statute-2026-590-v1"
    ] = "original"
    legal_status: LegalStatus = "unknown"
    parent_source_id: str | None = None
    provenance: Provenance | None = None

    @model_validator(mode="after")
    def provenance_paths(self):
        if self.extraction_profile != "original":
            expected_suffix = (
                ".pdf" if self.extraction_profile == "statute-2026-590-v1" else ".html"
            )
            expected_type = (
                "official_guideline"
                if self.extraction_profile == "kprm-faq-v1"
                else "legal_act"
            )
            if (
                not self.provenance
                or not self.provenance.official_url
                or Path(self.path).suffix.lower() != expected_suffix
                or self.source_type != expected_type
            ):
                raise ValueError(
                    "Extraction profile requires a matching official original"
                )
        if self.provenance:
            if any(
                r.relation == "identical_bytes"
                and r.sha256 != self.provenance.original_sha256
                for r in self.provenance.representations
            ):
                raise ValueError(
                    "Identical representations must share the original checksum"
                )
            paths = [r.path for r in self.provenance.representations]
            if len(paths) != len(set(paths)):
                raise ValueError("Duplicate representation path")
            for path in paths:
                self.relative_path(path)
                if Path(path).suffix.lower() not in (
                    ".pdf",
                    ".html",
                    ".htm",
                    ".docx",
                    ".xlsx",
                ):
                    raise ValueError(
                        "Auxiliary Markdown cannot be an original representation"
                    )
            preferred = self.provenance.preferred_text_path
            if preferred and preferred not in [self.path, *paths]:
                raise ValueError(
                    "Preferred text must identify a declared original representation"
                )
        if self.legal_status == "verified_current" and not (
            self.provenance
            and self.provenance.legal_checked_on
            and self.provenance.legal_status_url
        ):
            raise ValueError("Current legal status requires dated official evidence")
        return self

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
