import io
from pathlib import Path
from zipfile import ZipFile

import pytest
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from pydantic import ValidationError
from pypdf import PdfWriter
from reportlab.pdfgen.canvas import Canvas

from app.modules.knowledge.audit import DEFAULT_MANIFEST, audit_source, compare_markdown
from app.modules.knowledge.extraction import (
    extract_docx,
    extract_pdf,
    extract_source,
    normalize_text,
)
from app.modules.knowledge.manifest import Manifest, SourceSpec, material_path


def docx_bytes(document):
    stream = io.BytesIO()
    document.save(stream)
    return stream.getvalue()


def test_manifest_covers_substantive_originals_only():
    manifest = Manifest.model_validate_json(DEFAULT_MANIFEST.read_text())
    assert len(manifest.sources) == 16
    assert sum(s.markdown_path is not None for s in manifest.sources) == 11
    assert all(
        s.source_type not in ("product_reference", "competition_rules")
        for s in manifest.sources
    )
    appendix = next(
        s for s in manifest.sources if s.source_id == "periodic-criteria-appendix"
    )
    assert appendix.parent_source_id == "periodic-regulation-2016"
    assert not any(s.path.endswith(".zip") for s in manifest.sources)


@pytest.mark.parametrize("path", ["../secret.pdf", "/secret.pdf", "x\\secret.pdf", ""])
def test_manifest_rejects_unsafe_paths(path):
    with pytest.raises(ValidationError):
        SourceSpec(
            source_id="test-source",
            title="Test",
            path=path,
            source_type="legal_act",
            document_version="1",
        )


def test_manifest_rejects_missing_or_cyclic_parents():
    source = dict(
        source_id="test-source",
        title="Test",
        path="test.pdf",
        source_type="legal_act",
        document_version="1",
    )
    for parent in ("test-source", "missing"):
        with pytest.raises(ValidationError):
            Manifest(sources=[{**source, "parent_source_id": parent}])
    with pytest.raises(ValidationError):
        Manifest(sources=[source, source])


def test_material_path_rejects_symlink_escape(tmp_path):
    (tmp_path / "link").symlink_to(Path(__file__))
    with pytest.raises(ValueError):
        material_path(tmp_path, "link")


def test_docx_order_nested_tables_merged_cells_and_hyperlinks():
    document = Document()
    document.add_paragraph("Before")
    table = document.add_table(rows=2, cols=2)
    table.cell(0, 0).merge(table.cell(0, 1)).text = "Merged once"
    table.cell(1, 0).text = "Cell A"
    table.cell(1, 1).add_table(rows=1, cols=1).cell(0, 0).text = "Nested"
    paragraph = document.add_paragraph("After ")
    hyperlink = OxmlElement("w:hyperlink")
    run, text = OxmlElement("w:r"), OxmlElement("w:t")
    text.text = "link text"
    run.append(text)
    hyperlink.append(run)
    paragraph._p.append(hyperlink)
    result = extract_docx(docx_bytes(document))
    assert [f.content for f in result.fragments] == [
        "Before",
        "Merged once",
        "Cell A",
        "Nested",
        "After link text",
    ]
    assert "/table-2/row-1/column-1/" in result.fragments[1].locator
    assert all(f.page is None for f in result.fragments)


@pytest.mark.parametrize("value,expected", [("0", "☐"), ("1", "☑"), ("false", "☐")])
def test_docx_legacy_checkbox_preserves_checked_state(value, expected):
    document = Document()
    paragraph = document.add_paragraph("Choice: ")
    checkbox = OxmlElement("w:checkBox")
    checked = OxmlElement("w:checked")
    checked.set(qn("w:val"), value)
    checkbox.append(checked)
    paragraph.add_run()._r.append(checkbox)
    result = extract_docx(docx_bytes(document))
    assert result.fragments[0].content == f"Choice: {expected}"


def test_docx_footnotes_are_separate_located_original_text():
    document = Document()
    paragraph = document.add_paragraph("A condition")
    reference = OxmlElement("w:footnoteReference")
    reference.set(qn("w:id"), "2")
    paragraph.add_run()._r.append(reference)
    stream = io.BytesIO()
    with (
        ZipFile(io.BytesIO(docx_bytes(document))) as original,
        ZipFile(stream, "w") as target,
    ):
        for entry in original.infolist():
            target.writestr(entry, original.read(entry.filename))
        target.writestr(
            "word/footnotes.xml",
            '<w:footnotes xmlns:w="http://schemas.openxmlformats.org/'
            'wordprocessingml/2006/main"><w:footnote w:id="2"><w:p><w:r>'
            "<w:t>Except when exempt.</w:t></w:r></w:p></w:footnote></w:footnotes>",
        )
    result = extract_docx(stream.getvalue())
    assert "[footnoteReference:2]" in result.fragments[0].content
    assert result.fragments[1].locator == "word/footnotes.xml/item-2"
    assert result.fragments[1].content == "Except when exempt."


def test_pdf_uses_original_page_numbers_and_flags_empty_pages():
    stream = io.BytesIO()
    canvas = Canvas(stream)
    canvas.drawString(20, 700, "Threshold > 4; no score 1.")
    canvas.showPage()
    canvas.drawString(20, 700, "Exception on original page 2.")
    canvas.save()
    result = extract_pdf(stream.getvalue())
    assert [(f.page, f.locator) for f in result.fragments] == [
        (1, "page-1"),
        (2, "page-2"),
    ]
    assert "> 4; no score 1." in result.fragments[0].content
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    blank = io.BytesIO()
    writer.write(blank)
    result = extract_pdf(blank.getvalue())
    assert not result.fragments
    assert "page-1:no_text_requires_ocr" in result.warnings


@pytest.mark.parametrize(
    "before,after",
    [
        ("nie wymaga", "wymaga"),
        ("średnia > 4", "średnia >= 4"),
        ("do 3", "do 4"),
        ("§ 5 ust. 2", "§ 5 ust. 3"),
    ],
)
def test_comparison_never_normalizes_away_meaning(before, after):
    result = compare_markdown(before, after)
    assert not result["normalized_equal"]
    assert result["difference_count"] > 0
    assert normalize_text("  § 5\n  ust. 2 ") == "§ 5 ust. 2"


def test_audit_never_approves_even_identical_markdown(tmp_path):
    document = Document()
    document.add_paragraph("Exact original")
    (tmp_path / "original.docx").write_bytes(docx_bytes(document))
    (tmp_path / "representation.md").write_text("Exact original")
    spec = SourceSpec(
        source_id="test-form",
        title="Test",
        path="original.docx",
        markdown_path="representation.md",
        source_type="official_form",
        document_version="1",
    )
    result = audit_source(tmp_path, spec)
    assert result["markdown_comparison"]["normalized_equal"]
    assert result["verification_status"] == "needs_review"
    assert result["fragments"][0]["verification_status"] == "needs_review"


def test_unsupported_original_cannot_be_replaced_by_markdown():
    with pytest.raises(ValueError, match="Unsupported original"):
        extract_source(Path("source.md"), b"AI interpretation")
