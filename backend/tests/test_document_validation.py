import io
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from pypdf import PdfWriter

from app.modules.documents.validation import (
    DOCX_TYPE,
    MAX_FILE_SIZE,
    PDF_TYPE,
    InvalidDocument,
    validate_content,
    validate_filename,
)


def pdf_bytes(encrypted=False):
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    if encrypted:
        writer.encrypt("test-only")
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def docx_bytes(**overrides):
    entries = {
        "[Content_Types].xml": (
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Override PartName="/word/document.xml" '
            f'ContentType="{DOCX_TYPE}.main+xml"/>'
            "</Types>"
        ),
        "_rels/.rels": (
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Target="word/document.xml" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"/>'
            "</Relationships>"
        ),
        "word/document.xml": '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p/></w:body></w:document>',
        **overrides,
    }
    output = io.BytesIO()
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for name, content in entries.items():
            archive.writestr(name, content)
    return output.getvalue()


@pytest.mark.parametrize(
    "filename",
    [
        "../x.pdf",
        "a/b.pdf",
        "a\\b.docx",
        "\r\nx.pdf",
        "\x00x.pdf",
        "",
        " ",
        ".",
        "..",
        "a" * 256,
        "x\u202epdf",
    ],
)
def test_rejects_unsafe_names(filename):
    with pytest.raises(InvalidDocument):
        validate_filename(filename)


def test_unicode_names_are_preserved_and_normalized():
    assert validate_filename("  Zażółć ge\u0328śla.PDF  ") == "Zażółć gęśla.PDF"


@pytest.mark.parametrize(
    "content,filename,media_type",
    [
        (pdf_bytes(), "Ocena.PDF", PDF_TYPE),
        (docx_bytes(), "Opis.docx", DOCX_TYPE),
        (pdf_bytes(), "Ocena.pdf", "application/octet-stream"),
    ],
)
def test_validates_real_file_structure(content, filename, media_type):
    assert validate_content(content, filename, media_type) in (PDF_TYPE, DOCX_TYPE)


@pytest.mark.parametrize(
    "content,filename,media_type",
    [
        (b"", "x.pdf", PDF_TYPE),
        (b"x" * (MAX_FILE_SIZE + 1), "x.pdf", PDF_TYPE),
        (b"%PDF-1.7\nnot a PDF", "x.pdf", PDF_TYPE),
        (pdf_bytes(encrypted=True), "x.pdf", PDF_TYPE),
        (pdf_bytes(), "x.docx", DOCX_TYPE),
        (docx_bytes(), "x.pdf", PDF_TYPE),
        (pdf_bytes(), "x.pdf", "text/html"),
        (pdf_bytes(), "x.exe", PDF_TYPE),
        (docx_bytes(**{"word/document.xml": "broken"}), "x.docx", DOCX_TYPE),
        (docx_bytes(**{"word/vbaProject.bin": b"macro"}), "x.docx", DOCX_TYPE),
        (docx_bytes(**{"../escape": b"x"}), "x.docx", DOCX_TYPE),
        (
            docx_bytes(
                **{"word/document.xml": '<!DOCTYPE x [<!ENTITY secret "x">]><x/>'}
            ),
            "x.docx",
            DOCX_TYPE,
        ),
        (
            docx_bytes(**{"word/document.xml": b"x" * (4 * 1024 * 1024 + 1)}),
            "x.docx",
            DOCX_TYPE,
        ),
        (docx_bytes(**{"extra": b"x" * (32 * 1024 * 1024)}), "x.docx", DOCX_TYPE),
    ],
)
def test_rejects_spoofed_corrupt_encrypted_or_expanding_files(
    content, filename, media_type
):
    with pytest.raises(InvalidDocument):
        validate_content(content, filename, media_type)
