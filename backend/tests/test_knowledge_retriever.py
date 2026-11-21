import os
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import text
from test_documents import MemoryStorage

from app.modules.knowledge.audit import DEFAULT_MANIFEST
from app.modules.knowledge.extraction import sha256
from app.modules.knowledge.ingestion import ingest_source
from app.modules.knowledge.manifest import Manifest
from app.modules.knowledge.models import KnowledgeChunk, KnowledgeSource
from app.modules.knowledge.retriever import (
    PostgresKnowledgeRetriever,
    RetrievalQuery,
    query_terms,
)
from app.modules.knowledge.review import Reviews


@pytest.fixture
def corpus(database):
    _, _, session = database

    def create(*, contents=("Obowiązkowe kryteria oceny.",), **overrides):
        source_id = uuid4().hex
        source = KnowledgeSource(
            source_id=source_id,
            title="Official test law",
            source_type="legal_act",
            assessment_kind="periodic",
            document_version="1",
            original_path="test.html",
            original_filename="test.html",
            original_sha256="0" * 64,
            original_size=1,
            media_type="text/html",
            storage_key=source_id,
            extractor_version="eli-html-v1",
            extraction_sha256="0" * 64,
            legal_status="verified_current",
            verification_status="needs_review",
            warnings=[],
            provenance=dict(
                canonical_document_id=source_id,
                original_sha256="0" * 64,
                official_url="https://eli.gov.pl/test.html",
                legal_checked_on=date.today().isoformat(),
                legal_status_url="https://api.sejm.gov.pl/test",
                usage="context",
                note="Synthetic test evidence, not real law",
            ),
        )
        for name, value in overrides.items():
            setattr(source, name, value)
        session.add(source)
        session.flush()
        chunks = [
            KnowledgeChunk(
                id=uuid4(),
                source_id=source_id,
                chunk_index=index,
                locator=f"html:#para_{index + 1}",
                content=content,
                content_sha256=sha256(content.encode()),
                verification_status="approved",
                warnings=[],
                review={"reviewed_by": "Test reviewer"},
            )
            for index, content in enumerate(contents)
        ]
        session.add_all(chunks)
        session.flush()
        return source, chunks

    return session, create, PostgresKnowledgeRetriever(session)


def test_query_is_plain_terms_with_polish_inflection_and_no_tsquery_injection():
    assert query_terms("Jakie obowiązkowe kryteria?") == "kryte:* | obowi:*"
    assert "!" not in query_terms("!negatywna & (ocena | ' OR 1=1 --)")
    assert query_terms("ocena w służbie cywilnej") == ""


@pytest.mark.integration
def test_retrieval_returns_real_metadata_and_does_not_mutate(corpus):
    session, create, retriever = corpus
    source, chunks = create()
    result = retriever.retrieve(RetrievalQuery(question="obowiązkowych kryteriów"))
    assert result.status == "matched"
    assert len(result.chunks) == 1
    found = result.chunks[0]
    assert found.chunk_id == chunks[0].id
    assert found.source_id == source.source_id
    assert found.locator == "html:#para_1" and found.page is None
    assert found.content == chunks[0].content
    assert found.retrieval_score > 0 and not found.context_only
    assert found.legal_checked_on == date.today()
    assert "original_path" not in found.model_dump()
    assert "storage_key" not in found.model_dump()
    assert not session.dirty


@pytest.mark.integration
@pytest.mark.parametrize(
    "override",
    [
        {"assessment_kind": "first"},
        {"legal_status": "unknown"},
        {"legal_status": "historical"},
        {"verification_status": "rejected"},
        {"source_type": "sample_job_description"},
        {"source_type": "competency_catalog"},
        {"provenance": None},
    ],
)
def test_source_filters_fail_closed_before_returning_content(corpus, override):
    _, create, retriever = corpus
    create(**override)
    result = retriever.retrieve(
        RetrievalQuery(question="kryteria", assessment_kind="periodic")
    )
    assert result.status == "insufficient_evidence" and not result.chunks


@pytest.mark.integration
@pytest.mark.parametrize(
    "field,value",
    [
        ("usage", "example_only"),
        ("usage", "duplicate_subset"),
        ("usage", "validation_only"),
        ("legal_checked_on", (date.today() + timedelta(days=1)).isoformat()),
        ("legal_checked_on", None),
        ("original_sha256", "1" * 64),
        ("official_url", "https://untrusted.example/test"),
    ],
)
def test_invalid_or_noncontext_provenance_cannot_be_evidence(corpus, field, value):
    session, create, retriever = corpus
    source, _ = create()
    source.provenance = {**source.provenance, field: value}
    session.flush()
    assert not retriever.retrieve(RetrievalQuery(question="kryteria")).chunks


@pytest.mark.integration
@pytest.mark.parametrize(
    "warning",
    [
        "temporal_scope_requires_review",
        "parallel_wordings_require_temporal_review",
        "omitted_amending_articles_not_available",
        "unsupported_external_annex",
    ],
)
def test_approval_alone_does_not_resolve_temporal_or_incomplete_text(corpus, warning):
    session, create, retriever = corpus
    _, chunks = create()
    chunks[0].warnings = [warning]
    session.flush()
    assert not retriever.retrieve(RetrievalQuery(question="kryteria")).chunks


@pytest.mark.integration
@pytest.mark.parametrize(
    "status", ["unverified", "needs_review", "rejected", "corrupted"]
)
def test_unapproved_or_corrupted_chunk_never_leaks(corpus, status):
    session, create, retriever = corpus
    _, chunks = create()
    if status == "corrupted":
        chunks[0].content = "Obowiązkowe kryteria: changed content."
    else:
        chunks[0].verification_status = status
    session.flush()
    assert not retriever.retrieve(RetrievalQuery(question="kryteria")).chunks


@pytest.mark.integration
def test_transitive_context_cycles_and_limits_are_atomic(corpus):
    session, create, retriever = corpus
    _, chunks = create(
        contents=("Kryteria: zasada.", "Wyjątek od zasady.", "Dalszy warunek.")
    )
    for index, chunk in enumerate(chunks):
        chunk.warnings = ["required_context:" + chunks[(index + 1) % 3].locator]
    session.flush()
    result = retriever.retrieve(RetrievalQuery(question="kryteria"))
    assert {c.chunk_id for c in result.chunks} == {c.id for c in chunks}
    assert sum(c.context_only for c in result.chunks) == 2
    for override in ({"limit": 2}, {"max_characters": 5}):
        result = retriever.retrieve(RetrievalQuery(question="kryteria", **override))
        assert not result.chunks and "context_limit" in result.diagnostics
    chunks[2].verification_status = "needs_review"
    session.flush()
    result = retriever.retrieve(RetrievalQuery(question="kryteria"))
    assert (
        not result.chunks and "incomplete_or_unapproved_context" in result.diagnostics
    )


@pytest.mark.integration
def test_dependencies_cannot_cross_sources(corpus):
    session, create, retriever = corpus
    _, first = create(contents=("Kryteria",))
    create(contents=("Other text", "Other condition"))
    first[0].warnings = ["required_context:html:#para_2"]
    session.flush()
    assert not retriever.retrieve(RetrievalQuery(question="kryteria")).chunks


@pytest.mark.integration
def test_html_and_pdf_of_one_canonical_act_are_not_independent_evidence(corpus):
    _, create, retriever = corpus
    html, _ = create()
    create(
        provenance=html.provenance,
        extractor_version="original-v1",
        media_type="application/pdf",
    )
    result = retriever.retrieve(RetrievalQuery(question="kryteria"))
    assert {c.source_id for c in result.chunks} == {html.source_id}


@pytest.mark.integration
def test_pdf_page_boundaries_cannot_drop_a_distant_exception(corpus):
    session, create, retriever = corpus
    _, chunks = create(
        contents=("Kryteria: zasada.", "Ciąg dalszy.", "Wyjątek i zastrzeżenia."),
        extractor_version="original-v1",
        media_type="application/pdf",
    )
    result = retriever.retrieve(RetrievalQuery(question="kryteria"))
    assert {c.chunk_id for c in result.chunks} == {c.id for c in chunks}
    chunks[2].verification_status = "needs_review"
    session.flush()
    assert not retriever.retrieve(RetrievalQuery(question="kryteria")).chunks


@pytest.mark.integration
def test_explicit_paragraph_and_no_match(corpus):
    _, create, retriever = corpus
    _, chunks = create(contents=("Pierwszy przepis", "Drugi przepis"))
    result = retriever.retrieve(RetrievalQuery(question="§ 2"))
    assert [c.chunk_id for c in result.chunks] == [chunks[1].id]
    for question in ("§ 999", "art. 81", "teleportacja kosmitów", "   ", "ocena"):
        result = retriever.retrieve(RetrievalQuery(question=question))
        assert result.status == "insufficient_evidence" and not result.chunks


@pytest.mark.integration
def test_simple_dictionary_and_gin_index_are_available(corpus):
    session, _, _ = corpus
    assert session.scalar(text("SELECT 'simple'::regconfig::text")) == "simple"
    session.execute(text("SET LOCAL enable_seqscan = off"))
    plan = session.scalars(
        text(
            "EXPLAIN SELECT id FROM knowledge_chunks WHERE "
            "to_tsvector('simple'::regconfig, "
            "translate(lower(content), 'ąćęłńóśźż', 'acelnoszz')) "
            "@@ to_tsquery('simple', 'kryte:*')"
        )
    ).all()
    assert "ix_knowledge_chunks_search" in "\n".join(plan)


@pytest.mark.integration
def test_original_reviewed_corpus_retrieval_quality(database):
    root = os.environ.get("KOMPAS_TEST_KNOWLEDGE_MATERIALS")
    if not root:
        pytest.skip("Requires original source materials")
    _, _, session = database
    manifest = Manifest.model_validate_json(DEFAULT_MANIFEST.read_text())
    reviews = Reviews.model_validate_json(
        (DEFAULT_MANIFEST.parent / "knowledge-reviews.json").read_text()
    )
    storage = MemoryStorage()
    for review in reviews.sources:
        source = next(s for s in manifest.sources if s.source_id == review.source_id)
        ingest_source(session, Path(root), source, storage, review)
    retriever = PostgresKnowledgeRetriever(session)
    cases = [
        ("periodic", "Jakie są obowiązkowe kryteria arkusza C?", "html:#para_4"),
        ("periodic", "Ile kryteriów dodatkowych można wybrać?", "html:#para_5"),
        ("periodic", "Kiedy przyznaje się ocenę negatywną?", "html:#para_11"),
        ("periodic", "Jaka jest skala punktowa?", "html:#para_11"),
        ("first", "Jakie są warunki pozytywnej pierwszej oceny?", "html:#para_10"),
        ("first", "Kto jest zwolniony z egzaminu?", "html:#para_10"),
        ("first", "Ile miesięcy obejmuje sprawozdanie?", "html:#para_6"),
        ("first", "Kiedy przeprowadza się rozmowę wstępną?", "html:#para_3"),
        ("first", "Jaka jest skala punktowa?", "html:#para_9"),
    ]
    for kind, question, expected in cases:
        result = retriever.retrieve(
            RetrievalQuery(question=question, assessment_kind=kind)
        )
        assert expected in [c.locator for c in result.chunks], (question, result)
        assert all(c.assessment_kind == kind for c in result.chunks)
        assert all(c.source_id.endswith("html-v1") for c in result.chunks)
    assert not retriever.retrieve(
        RetrievalQuery(question="podróże międzygalaktyczne")
    ).chunks
