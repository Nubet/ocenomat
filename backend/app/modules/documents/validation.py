import io
import unicodedata
import zlib
from pathlib import PurePosixPath
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

from pypdf import PdfReader
from pypdf.errors import PyPdfError

MAX_FILE_SIZE = 10 * 1024 * 1024
PDF_TYPE = "application/pdf"
DOCX_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class InvalidDocument(ValueError):
    pass


def validate_filename(filename: str) -> str:
    filename = unicodedata.normalize("NFC", filename).strip(" ")
    if (
        not filename
        or len(filename) > 255
        or filename in (".", "..")
        or any(
            char in "/\\" or unicodedata.category(char).startswith("C")
            for char in filename
        )
    ):
        raise InvalidDocument("Use a filename without paths or control characters")
    return filename


def validate_content(content: bytes, filename: str, declared_type: str) -> str:
    if not content or len(content) > MAX_FILE_SIZE:
        raise InvalidDocument("File must contain 1 byte to 10 MiB")
    suffix = PurePosixPath(filename).suffix.lower()
    try:
        if suffix == ".pdf":
            if not content.startswith(b"%PDF-"):
                raise InvalidDocument("Invalid PDF")
            reader = PdfReader(io.BytesIO(content), strict=True)
            try:
                if reader.is_encrypted or not len(reader.pages):
                    raise InvalidDocument("PDF must be unencrypted and contain pages")
            finally:
                reader.close()
            media_type = PDF_TYPE
        elif suffix == ".docx":
            validate_docx(content)
            media_type = DOCX_TYPE
        else:
            raise InvalidDocument("Only PDF and DOCX files are supported")
    except (
        PyPdfError,
        BadZipFile,
        ElementTree.ParseError,
        KeyError,
        ValueError,
        OSError,
        RuntimeError,
        EOFError,
        zlib.error,
    ):
        raise InvalidDocument("Invalid or unsupported PDF/DOCX content") from None
    if declared_type.split(";", 1)[0].strip().lower() not in (
        media_type,
        "application/octet-stream",
    ):
        raise InvalidDocument("Content type does not match the file")
    return media_type


def validate_docx(content: bytes) -> None:
    with ZipFile(io.BytesIO(content)) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        if (
            len(entries) > 256
            or len(names) != len(set(names))
            or sum(entry.file_size for entry in entries) > 32 * 1024 * 1024
            or any(
                entry.flag_bits & 1
                or ".." in PurePosixPath(entry.filename).parts
                or entry.filename.startswith("/")
                or "\\" in entry.filename
                or entry.filename.lower().endswith("vbaproject.bin")
                for entry in entries
            )
        ):
            raise InvalidDocument("Unsupported DOCX archive")
        if archive.testzip() is not None:
            raise InvalidDocument("Corrupt DOCX archive")
        types = read_xml(archive, "[Content_Types].xml")
        document = read_xml(archive, "word/document.xml")
        relationships = read_xml(archive, "_rels/.rels")
        ns = "http://schemas.openxmlformats.org/package/2006/content-types"
        if (
            document.tag
            != "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}document"
            or relationships.tag
            != "{http://schemas.openxmlformats.org/package/2006/relationships}Relationships"
            or types.tag != f"{{{ns}}}Types"
            or document.find(
                "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}body"
            )
            is None
            or not any(
                item.get("Type")
                == "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
                and item.get("Target") in ("word/document.xml", "/word/document.xml")
                and item.get("TargetMode", "Internal") == "Internal"
                for item in relationships
            )
            or not any(
                item.tag == f"{{{ns}}}Override"
                and item.get("PartName") == "/word/document.xml"
                and item.get("ContentType") == DOCX_TYPE + ".main+xml"
                for item in types
            )
        ):
            raise InvalidDocument("Invalid DOCX document structure")


def read_xml(archive: ZipFile, name: str) -> ElementTree.Element:
    if archive.getinfo(name).file_size > 4 * 1024 * 1024:
        raise InvalidDocument("DOCX XML is too large")
    content = archive.read(name)
    if (
        b"\x00" in content
        or b"<!DOCTYPE" in content.upper()
        or b"<!ENTITY" in content.upper()
    ):
        raise InvalidDocument("Unsupported DOCX XML")
    return ElementTree.fromstring(content)
