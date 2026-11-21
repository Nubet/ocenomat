import hashlib
import io
import re
import unicodedata
from pathlib import Path
from zipfile import ZipFile

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph
from openpyxl import load_workbook
from pydantic import BaseModel, ConfigDict, Field
from pypdf import PdfReader

from app.modules.catalog.importer import parse_workbook
from app.modules.documents.validation import (
    DOCX_TYPE,
    PDF_TYPE,
    read_xml,
    validate_content,
)

EXTRACTOR_VERSION = "original-v1"
XLSX_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
MAX_TEXT_SIZE = 2_000_000


def normalize_text(text: str) -> str:
    return " ".join(unicodedata.normalize("NFC", text).split())


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


class Fragment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    locator: str = Field(min_length=1, max_length=500)
    content: str = Field(min_length=1, max_length=100_000)
    page: int | None = Field(default=None, ge=1)
    warnings: list[str] = []

    @property
    def content_sha256(self) -> str:
        return sha256(self.content.encode())


class Extraction(BaseModel):
    media_type: str
    fragments: list[Fragment]
    warnings: list[str] = []
    extractor_version: str = EXTRACTOR_VERSION


def paragraph_text(element) -> str:
    pieces = []
    for node in element.iter():
        if node.tag == qn("w:p") and node is not element:
            pieces.append("\n")
        elif node.tag == qn("w:t"):
            pieces.append(node.text or "")
        elif node.tag in (qn("w:tab"), qn("w:br"), qn("w:cr")):
            pieces.append("\n" if node.tag != qn("w:tab") else "\t")
        elif node.tag == qn("w:checkBox"):
            checked = node.find(qn("w:checked"))
            if checked is None:
                checked = node.find(qn("w:default"))
            value = checked.get(qn("w:val"), "1") if checked is not None else "0"
            pieces.append("☑" if value in ("1", "true", "on") else "☐")
        elif (
            node.tag == "{http://schemas.microsoft.com/office/word/2010/wordml}checkbox"
        ):
            checked = node.find(
                "{http://schemas.microsoft.com/office/word/2010/wordml}checked"
            )
            value = (
                checked.get("{http://schemas.microsoft.com/office/word/2010/wordml}val")
                if checked is not None
                else "0"
            )
            pieces.append("☑" if value in ("1", "true", "on") else "☐")
        elif node.tag in (qn("w:footnoteReference"), qn("w:endnoteReference")):
            pieces.append(f"[{node.tag.split('}')[1]}:{node.get(qn('w:id'))}]")
        elif node.tag == qn("w:sym"):
            pieces.append(f"[symbol:{node.get(qn('w:font'))}:{node.get(qn('w:char'))}]")
    return "".join(pieces).strip()


def docx_blocks(container, prefix: str):
    for index, block in enumerate(container.iter_inner_content(), 1):
        if isinstance(block, Paragraph):
            text = paragraph_text(block._p)
            if text:
                warnings = []
                if block._p.xpath(".//w:numPr") or block.style.name.startswith("List"):
                    warnings.append("automatic_numbering_requires_review")
                if block._p.xpath(".//w:checkBox | .//w:sym | .//w:sdt"):
                    warnings.append("fields_or_symbols_require_review")
                yield Fragment(
                    locator=f"{prefix}/paragraph-{index}",
                    content=text,
                    warnings=warnings,
                )
        elif isinstance(block, Table):
            seen = set()
            for row_index, row in enumerate(block.rows, 1):
                for column, cell in enumerate(row.cells, row.grid_cols_before + 1):
                    if cell._tc in seen:
                        continue
                    seen.add(cell._tc)
                    locator = f"{prefix}/table-{index}/row-{row_index}/column-{column}"
                    yield from docx_blocks(cell, locator)


def extract_docx(content: bytes) -> Extraction:
    validate_content(content, "source.docx", DOCX_TYPE)
    document = Document(io.BytesIO(content))
    fragments = list(docx_blocks(document, "body"))
    warnings = ["docx_layout_and_merged_cells_require_review"]
    with ZipFile(io.BytesIO(content)) as archive:
        for name in sorted(archive.namelist()):
            if re.fullmatch(
                r"word/(footnotes|endnotes|header\d+|footer\d+)\.xml", name
            ):
                root = read_xml(archive, name)
                for index, element in enumerate(root, 1):
                    text = paragraph_text(element)
                    if text:
                        note_id = element.get(qn("w:id"), str(index))
                        fragments.append(
                            Fragment(locator=f"{name}/item-{note_id}", content=text)
                        )
        body = document.element.body
        if body.xpath(".//w:ins | .//w:del | .//w:altChunk | .//w:txbxContent"):
            warnings.append("unsupported_revision_or_embedded_content")
        if body.xpath("./w:sdt"):
            warnings.append("unsupported_block_content_control")
    return Extraction(media_type=DOCX_TYPE, fragments=fragments, warnings=warnings)


def extract_pdf(content: bytes) -> Extraction:
    validate_content(content, "source.pdf", PDF_TYPE)
    fragments = []
    warnings = ["pdf_tables_footnotes_and_reading_order_require_review"]
    with PdfReader(io.BytesIO(content), strict=True) as reader:
        if len(reader.pages) > 500:
            raise ValueError("Source exceeds 500 pages")
        for index, page in enumerate(reader.pages, 1):
            stream = page.get_contents()
            if stream is not None and len(stream.get_data()) > 8 * 1024 * 1024:
                raise ValueError("PDF page content stream exceeds 8 MiB")
            text = page.extract_text(
                extraction_mode="layout", layout_mode_strip_rotated=False
            ).strip()
            if text:
                fragments.append(
                    Fragment(locator=f"page-{index}", page=index, content=text)
                )
            else:
                warnings.append(f"page-{index}:no_text_requires_ocr")
    return Extraction(media_type=PDF_TYPE, fragments=fragments, warnings=warnings)


def extract_workbook(path: Path, content: bytes) -> Extraction:
    criteria = parse_workbook(path, content=content)
    workbook = load_workbook(
        io.BytesIO(content), read_only=True, data_only=False, keep_links=False
    )
    fragments = []
    try:
        for criterion in criteria:
            sheet = next(
                s
                for s in workbook.worksheets[1:]
                if s.cell(1, 1).value == criterion.name
            )
            rows = [
                row
                for row in sheet.iter_rows(min_row=4)
                if any(c.value is not None for c in row)
            ]
            for indicator, row in zip(criterion.indicators, rows, strict=True):
                text = "\n".join(
                    [
                        criterion.name,
                        indicator.description,
                        *(
                            f"{level.name}: {level.description}"
                            for level in indicator.levels
                        ),
                    ]
                )
                fragments.append(
                    Fragment(
                        locator=f"sheet:{sheet.title}/A{row[0].row}:F{row[0].row}/criterion:{criterion.id}/indicator:{indicator.id}",
                        content=text,
                    )
                )
    finally:
        workbook.close()
    return Extraction(media_type=XLSX_TYPE, fragments=fragments)


def extract_source(
    path: Path, content: bytes, *, profile: str = "original"
) -> Extraction:
    if not content or len(content) > 10 * 1024 * 1024:
        raise ValueError("Source must contain 1 byte to 10 MiB")
    if profile != "original":
        from app.modules.knowledge.official_extraction import extract_official

        extraction = extract_official(path, content, profile)
    else:
        match path.suffix.lower():
            case ".pdf":
                extraction = extract_pdf(content)
            case ".docx":
                extraction = extract_docx(content)
            case ".xlsx":
                extraction = extract_workbook(path, content)
            case _:
                raise ValueError("Unsupported original format")
    if sum(len(f.content) for f in extraction.fragments) > MAX_TEXT_SIZE:
        raise ValueError("Extracted text exceeds 2 million characters")
    return extraction
