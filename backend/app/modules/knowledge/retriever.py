import re
from datetime import date
from typing import Literal, Protocol
from uuid import UUID

from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.knowledge.extraction import sha256
from app.modules.knowledge.manifest import Provenance
from app.modules.knowledge.models import KnowledgeChunk, KnowledgeSource, search_vector

STOP_WORDS = frozenset(
    "a aby albo czy co do dla i ile jak jaka jakie jaki jest je na nie o od oraz "
    "po sie to w we z za ze ocena oceny ocene ocenie ocen okresowa okresowej "
    "okresowe pierwsza pierwszej pierwsze sluzba sluzby sluzbie cywilnej "
    "paragraf ust pkt art".split()
)


class RetrievalQuery(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    assessment_kind: Literal["first", "periodic", "unspecified"] = "unspecified"
    limit: int = Field(default=5, ge=1, le=10)
    max_characters: int = Field(default=20000, ge=1, le=40000)


class RetrievedChunk(BaseModel):
    chunk_id: UUID
    source_id: str
    canonical_document_id: str
    title: str
    source_type: str
    assessment_kind: str
    document_version: str
    content: str
    content_sha256: str
    locator: str
    page: int | None
    official_url: str
    verification_status: Literal["approved"] = "approved"
    legal_status: Literal["verified_current"] = "verified_current"
    legal_checked_on: date
    retrieval_score: float
    context_only: bool


class RetrievalResult(BaseModel):
    status: Literal["matched", "insufficient_evidence"]
    chunks: list[RetrievedChunk] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)


class KnowledgeRetriever(Protocol):
    def retrieve(self, query: RetrievalQuery) -> RetrievalResult: ...


def source_provenance(source: KnowledgeSource) -> Provenance | None:
    try:
        evidence = Provenance.model_validate(source.provenance)
    except ValidationError:
        return None
    if (
        source.verification_status == "rejected"
        or source.legal_status != "verified_current"
        or source.source_type
        not in (
            "legal_act",
            "legal_appendix",
            "official_guideline",
            "official_form",
            "approved_faq",
        )
        or evidence.usage != "context"
        or not evidence.official_url
        or not evidence.legal_checked_on
        or evidence.legal_checked_on > date.today()
        or not evidence.legal_status_url
        or evidence.original_sha256 != source.original_sha256
    ):
        return None
    return evidence


def query_terms(question: str) -> str:
    normalized = question.lower().translate(str.maketrans("ąćęłńóśźż", "acelnoszz"))
    words = re.findall(r"[a-z0-9]+", normalized)
    # Prefixes cover common Polish inflections without an installed dictionary.
    return " | ".join(
        sorted(
            {
                word[:5] + ":*" if len(word) > 2 else word
                for word in words
                if word not in STOP_WORDS
            }
        )
    )


def usable(chunk: KnowledgeChunk) -> bool:
    return (
        chunk.verification_status == "approved"
        and bool(chunk.review)
        and sha256(chunk.content.encode()) == chunk.content_sha256
        and not any(
            warning.startswith(
                (
                    "unsupported",
                    "no_text",
                    "temporal_",
                    "parallel_",
                    "omitted_",
                    "transitional_",
                )
            )
            for warning in chunk.warnings
        )
    )


class PostgresKnowledgeRetriever:
    def __init__(self, session: Session):
        self.session = session

    def retrieve(self, query: RetrievalQuery) -> RetrievalResult:
        terms = query_terms(query.question)
        reference = re.search(r"§\s*(\d+)\b", query.question)
        article = re.search(r"\bart\.?\s*(\d+[a-z]*)\b", query.question, re.IGNORECASE)
        if not terms and not reference and not article:
            return RetrievalResult(
                status="insufficient_evidence", diagnostics=["empty_query"]
            )
        tsquery = func.to_tsquery("simple", terms)
        vector = search_vector(KnowledgeChunk.content)
        score = func.ts_rank_cd(vector, tsquery)
        statement = (
            select(KnowledgeChunk, KnowledgeSource, score)
            .join(KnowledgeSource)
            .where(
                KnowledgeChunk.verification_status == "approved",
                KnowledgeSource.verification_status != "rejected",
                KnowledgeSource.legal_status == "verified_current",
                KnowledgeSource.source_type.in_(
                    (
                        "legal_act",
                        "legal_appendix",
                        "official_guideline",
                        "official_form",
                        "approved_faq",
                    )
                ),
                KnowledgeSource.provenance["usage"].astext.in_(("context",))
                | KnowledgeSource.provenance["usage"].astext.is_(None),
            )
        )
        if query.assessment_kind != "unspecified":
            statement = statement.where(
                KnowledgeSource.assessment_kind.in_((query.assessment_kind, "both"))
            )
        if reference:
            statement = statement.where(
                KnowledgeChunk.locator == f"html:#para_{int(reference[1])}"
            )
        elif article:
            statement = statement.where(
                KnowledgeChunk.locator.contains(
                    f"/article-{article[1].lower()}/", autoescape=True
                )
            )
        else:
            statement = statement.where(vector.op("@@")(tsquery))
        candidates = self.session.execute(
            statement.execution_options(populate_existing=True)
            .order_by(
                score.desc(), KnowledgeChunk.source_id, KnowledgeChunk.chunk_index
            )
            .limit(100)
        ).all()
        diagnostics = {"candidate_limit"} if len(candidates) == 100 else set()
        eligible = []
        for chunk, source, rank in candidates:
            evidence = source_provenance(source)
            if evidence is None or not usable(chunk):
                diagnostics.add("ineligible_evidence")
                continue
            eligible.append((chunk, source, rank, evidence))
        # One representation per canonical act; HTML retains whole, anchored paragraphs.
        preferred = {}
        for _, source, _, evidence in sorted(
            eligible,
            key=lambda row: (
                row[1].extractor_version != "eli-html-v1",
                row[1].source_id,
            ),
        ):
            preferred.setdefault(evidence.canonical_document_id, source.source_id)
        selected = {}
        characters = 0
        for chunk, source, rank, evidence in eligible:
            if (
                preferred[evidence.canonical_document_id] != source.source_id
                or chunk.id in selected
            ):
                continue
            context = self._context(chunk, source)
            if context is None:
                diagnostics.add("incomplete_or_unapproved_context")
                continue
            additions = [part for part in context if part.id not in selected]
            size = sum(len(part.content) for part in additions)
            if (
                len(selected) + len(additions) > query.limit
                or characters + size > query.max_characters
            ):
                diagnostics.add("context_limit")
                continue
            for part in additions:
                selected[part.id] = RetrievedChunk(
                    chunk_id=part.id,
                    source_id=source.source_id,
                    canonical_document_id=evidence.canonical_document_id,
                    title=source.title,
                    source_type=source.source_type,
                    assessment_kind=source.assessment_kind,
                    document_version=source.document_version,
                    content=part.content,
                    content_sha256=part.content_sha256,
                    locator=part.locator,
                    page=part.page,
                    official_url=evidence.official_url,
                    legal_checked_on=evidence.legal_checked_on,
                    retrieval_score=float(rank),
                    context_only=part.id != chunk.id,
                )
            characters += size
        return RetrievalResult(
            status="matched" if selected else "insufficient_evidence",
            chunks=list(selected.values()),
            diagnostics=sorted(diagnostics)
            if diagnostics
            else ([] if selected else ["no_match"]),
        )

    def _context(
        self, root: KnowledgeChunk, source: KnowledgeSource
    ) -> list[KnowledgeChunk] | None:
        parts = {root.locator: root}
        pending = [root]
        if (
            source.media_type == "application/pdf"
            and source.extractor_version == "original-v1"
        ):
            # Without structural boundaries, only a complete approved PDF is safe.
            pages = self.session.scalars(
                select(KnowledgeChunk)
                .execution_options(populate_existing=True)
                .where(KnowledgeChunk.source_id == source.source_id)
                .order_by(KnowledgeChunk.chunk_index)
                .limit(11)
            ).all()
            if len(pages) > 10:
                return None
            pending = list(pages)
            parts = {part.locator: part for part in pages}
        for part in pending:
            if not usable(part):
                return None
            for warning in part.warnings:
                if not warning.startswith("required_context:"):
                    continue
                locator = warning.removeprefix("required_context:")
                if locator in parts:
                    continue
                dependency = self.session.scalar(
                    select(KnowledgeChunk)
                    .where(
                        KnowledgeChunk.source_id == source.source_id,
                        KnowledgeChunk.locator == locator,
                    )
                    .execution_options(populate_existing=True)
                )
                if dependency is None or len(parts) >= 10:
                    return None
                parts[locator] = dependency
                pending.append(dependency)
        return sorted(parts.values(), key=lambda part: part.chunk_index)
