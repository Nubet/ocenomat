import os
import re
from collections import Counter
from pathlib import Path

import pytest
from lxml import html
from pydantic import ValidationError
from sqlalchemy import select
from test_documents import MemoryStorage

from app.modules.knowledge.audit import DEFAULT_MANIFEST, audit_source
from app.modules.knowledge.extraction import (
    extract_pdf,
    extract_source,
    normalize_text,
    sha256,
)
from app.modules.knowledge.ingestion import ingest_source
from app.modules.knowledge.manifest import Manifest, SourceSpec
from app.modules.knowledge.models import KnowledgeChunk, KnowledgeSource
from app.modules.knowledge.official_extraction import html_text

ELI = b"""<html><nav>Not law</nav><section id="part_1">
<div data-template="xText">Legal basis.</div>
<div id="para_1"><h3>1.</h3><div>Condition &gt; 4, not 1.</div>
<div id="para_1-pass_1">Except <b>when exempt</b>.</div></div>
<div id="para_2">Entry into force.</div></section>
<section id="part_2"><a href="text.pdf">Annex in PDF</a></section>
<script>Do not extract scripts</script></html>"""


def test_eli_keeps_complete_paragraphs_and_flags_pdf_only_annexes():
    result = extract_source(Path("law.html"), ELI, profile="eli-html-v1")
    assert result.extractor_version == "eli-html-v1"
    assert [f.locator for f in result.fragments] == [
        "html:#part_1/preamble",
        "html:#para_1",
        "html:#para_2",
        "html:#part_2",
    ]
    assert "Condition > 4, not 1." in result.fragments[1].content
    assert "Except when exempt." in result.fragments[1].content
    assert "unsupported_external_annex_requires_original_pdf" in result.warnings
    assert all(f.page is None for f in result.fragments)
    assert "Not law" not in " ".join(f.content for f in result.fragments)
    with pytest.raises(ValueError, match="Duplicate HTML IDs"):
        extract_source(
            Path("law.html"), ELI.replace(b"para_2", b"para_1"), profile="eli-html-v1"
        )
    with pytest.raises(ValueError, match="unordered ELI"):
        extract_source(
            Path("law.html"), ELI.replace(b"para_2", b"para_3"), profile="eli-html-v1"
        )
    with pytest.raises(ValueError, match="exactly one"):
        extract_source(
            Path("law.html"), b"<p>Unexpected template</p>", profile="eli-html-v1"
        )


def test_html_preserves_text_boundaries_cells_and_ignores_active_content():
    node = html.fromstring(
        "<div>A<strong>B</strong><br>C<table><tr><td>1</td><td>not 3</td></tr>"
        "</table><!--Ignore--><script>Ignore</script><style>Ignore</style></div>"
    )
    text = html_text(node)
    assert text.startswith("AB\nC")
    assert "1\tnot 3" in text
    assert "Ignore" not in text


@pytest.fixture
def faq():
    return """<nav>Menu</nav><article id="main-content">
<p class="intro">Wyjaśnienia mają charakter opinii, a nie wiążącej wykładni prawa.</p>
<div><details><summary>1. Czy obowiązuje?</summary>
<p>Nie, z wyjątkiem X<sup>1</sup>.</p>
<p>1. Art. 81 ust. 9.</p></details></div></article>""".encode()


def test_faq_keeps_question_answer_footnote_and_disclaimer(faq):
    result = extract_source(Path("faq.html"), faq, profile="kprm-faq-v1")
    fragment = result.fragments[0]
    assert fragment.content.startswith("Wyjaśnienia mają charakter opinii")
    assert "1. Czy obowiązuje?" in fragment.content
    assert "Nie, z wyjątkiem X1." in fragment.content
    assert "1. Art. 81 ust. 9." in fragment.content
    assert "Menu" not in fragment.content
    original_node = html.fromstring(faq).xpath(fragment.locator.removeprefix("html:"))
    assert len(original_node) == 1 and original_node[0].tag == "details"
    assert "non_binding_opinion" in fragment.warnings
    for before, after in [(b'class="intro"', b'class="other"'), (b"1. Czy", b"2. Czy")]:
        with pytest.raises(ValueError):
            extract_source(
                Path("faq.html"), faq.replace(before, after), profile="kprm-faq-v1"
            )


def test_profiles_are_explicit_and_statute_is_bound_to_audited_edition():
    with pytest.raises(ValueError, match="Unsupported original"):
        extract_source(Path("law.html"), ELI)
    with pytest.raises(ValueError, match="checksum"):
        extract_source(Path("law.pdf"), b"other edition", profile="statute-2026-590-v1")
    with pytest.raises(ValueError, match="profile or format"):
        extract_source(Path("law.docx"), ELI, profile="eli-html-v1")
    with pytest.raises(ValidationError, match="matching official original"):
        SourceSpec(
            source_id="test-html",
            title="Test",
            path="law.html",
            source_type="legal_act",
            document_version="1",
            extraction_profile="eli-html-v1",
        )


@pytest.fixture(scope="module")
def originals():
    directory = os.environ.get("KOMPAS_TEST_KNOWLEDGE_MATERIALS")
    if not directory:
        pytest.skip("Requires original source materials")
    root = Path(directory)
    manifest = Manifest.model_validate_json(DEFAULT_MANIFEST.read_text())
    return {
        s.extraction_profile + ":" + s.assessment_kind: (
            s,
            (root / s.path).read_bytes(),
        )
        for s in manifest.sources
        if s.extraction_profile != "original"
    }


def test_original_eli_paragraphs_and_faq_are_complete(originals):
    for kind, count in [("periodic", 19), ("first", 18)]:
        spec, content = originals[f"eli-html-v1:{kind}"]
        result = extract_source(
            Path(spec.path), content, profile=spec.extraction_profile
        )
        assert len(result.fragments) == count
        assert {f.locator for f in result.fragments if "#para_" in f.locator} == {
            f"html:#para_{i}" for i in range(1, 15)
        }
        document = html.fromstring(content.decode("utf-8"))
        for fragment in result.fragments:
            if "#para_" in fragment.locator:
                element = document.get_element_by_id(fragment.locator.split("#")[1])
                assert normalize_text(fragment.content) == normalize_text(
                    element.text_content()
                )
        assert "unsupported_external_annex_requires_original_pdf" in result.warnings
    spec, content = originals["kprm-faq-v1:both"]
    result = extract_source(Path(spec.path), content, profile=spec.extraction_profile)
    assert len(result.fragments) == 31
    document = html.fromstring(content.decode("utf-8"))
    for fragment in result.fragments:
        question = document.xpath(fragment.locator.removeprefix("html:"))[0]
        assert normalize_text(question.text_content()) in normalize_text(
            fragment.content
        )
        assert "nie wiążącej wykładni prawa" in fragment.content
    assert "nie podlega wydłużeniu" in result.fragments[18].content
    assert "Art. 81 ust. 7" in result.fragments[18].content


def test_original_statute_separates_notice_variants_and_complete_continuations(
    originals,
):
    spec, content = originals["statute-2026-590-v1:both"]
    result = extract_source(Path(spec.path), content, profile=spec.extraction_profile)
    fragments = {f.locator: f for f in result.fragments}
    assert len(fragments) == len(result.fragments)
    assert "Art. 35. Ustawa wchodzi" in normalize_text(
        fragments["notice/page-2"].content
    )
    assert (
        "Stosunek pracy pracownika"
        in fragments["annex/page-16/article-35/part-1"].content
    )
    assert "Art. 37. 1." in fragments["annex/page-17/article-37/part-1"].content
    assert "12 miesięcy" in fragments["annex/page-16/article-35/part-1"].content
    assert (
        "po upływie 8 miesięcy" in fragments["annex/page-17/article-38/part-1"].content
    )
    first = fragments["annex/page-24/article-81/part-1"]
    second = fragments["annex/page-25/article-81/part-1"]
    assert "co 24 miesiące" in first.content
    assert "może zmienić termin" in first.content
    assert "więcej niż 6 miesięcy" in normalize_text(second.content)
    assert "required_context:" + second.locator in first.warnings
    assert "required_context:" + first.locator in second.warnings
    assert "1 stycznia 2027 r." in fragments["annex/page-22/footnotes"].content
    assert (
        "required_context:annex/page-22/footnotes"
        in fragments["annex/page-22/article-71/part-1"].warnings
    )
    assert (
        "wejdzie w życie po upływie 7 dni"
        in fragments["annex/page-4/footnotes"].content
    )
    for part in (1, 2):
        assert (
            "parallel_wordings_require_temporal_review"
            in fragments[f"annex/page-12/article-28/part-{part}"].warnings
        )
    assert (
        "omitted_amending_articles_not_available"
        in fragments["annex/page-34/article-132–190/part-1"].warnings
    )
    for fragment in result.fragments:
        for warning in fragment.warnings:
            if warning.startswith("required_context:"):
                assert warning.removeprefix("required_context:") in fragments
        assert fragment.page and "temporal_scope_requires_review" in fragment.warnings
    raw = extract_pdf(content)
    expected = "\n".join(
        line
        for page in raw.fragments
        for line in page.content.splitlines()
        if page.page < 3
        or not re.fullmatch(r"\s*(?:Dziennik Ustaw.*Poz\. 590|2026-04-30)\s*", line)
    )
    assert Counter(expected.split()) == Counter(
        "\n".join(f.content for f in result.fragments).split()
    )


def test_audit_uses_explicit_profile_and_refuses_changed_original(tmp_path):
    (tmp_path / "law.html").write_bytes(ELI)
    spec = SourceSpec(
        source_id="test-html",
        title="Test",
        path="law.html",
        source_type="legal_act",
        document_version="1",
        extraction_profile="eli-html-v1",
        provenance=dict(
            canonical_document_id="test",
            original_sha256=sha256(ELI),
            official_url="https://eli.gov.pl/api/acts/DU/2016/470/text.html",
            note="Test evidence",
        ),
    )
    report = audit_source(tmp_path, spec)
    assert report["extractor_version"] == "eli-html-v1"
    assert all(f["verification_status"] == "needs_review" for f in report["fragments"])
    (tmp_path / "law.html").write_bytes(ELI.replace(b"not 1", b"not 2"))
    with pytest.raises(ValueError, match="provenance checksum"):
        audit_source(tmp_path, spec)


@pytest.mark.integration
@pytest.mark.parametrize("profile", ["eli-html-v1", "kprm-faq-v1"])
def test_official_html_reuses_idempotent_importer(database, tmp_path, faq, profile):
    _, _, session = database
    content = ELI if profile == "eli-html-v1" else faq
    path = tmp_path / "official.html"
    path.write_bytes(content)
    spec = SourceSpec(
        source_id="test-official-html",
        title="Test",
        path=path.name,
        source_type="legal_act" if profile == "eli-html-v1" else "official_guideline",
        document_version="1",
        extraction_profile=profile,
        provenance=dict(
            canonical_document_id="test",
            original_sha256=sha256(content),
            official_url="https://www.gov.pl/test",
            note="Test evidence",
        ),
    )
    storage = MemoryStorage()
    for _ in range(2):
        ingest_source(session, tmp_path, spec, storage)
    source = session.get(KnowledgeSource, spec.source_id)
    chunks = list(
        session.scalars(
            select(KnowledgeChunk)
            .where(KnowledgeChunk.source_id == spec.source_id)
            .order_by(KnowledgeChunk.chunk_index)
        )
    )
    extraction = extract_source(path, content, profile=profile)
    assert source.extractor_version == profile
    assert [(c.locator, c.content_sha256, c.warnings) for c in chunks] == [
        (f.locator, f.content_sha256, f.warnings) for f in extraction.fragments
    ]
    assert all(c.verification_status == "needs_review" for c in chunks)
    assert source.verification_status == "needs_review"
    assert [name for name, _ in storage.calls].count("put") == 1
