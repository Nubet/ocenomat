import argparse
import hashlib
from pathlib import Path
from uuid import uuid5
from zipfile import ZipFile

from openpyxl import load_workbook
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.database import create_database_engine
from app.modules.catalog.identifiers import CATALOG_NAMESPACE, stable_id
from app.modules.catalog.models import CatalogVersion
from app.modules.catalog.schemas import Criterion, Indicator, Level

LEVEL_NAMES = (
    "Znacznie poniżej oczekiwań",
    "Poniżej oczekiwań",
    "Na poziomie oczekiwań",
    "Powyżej oczekiwań",
    "Znacznie powyżej oczekiwań",
)


def source_text(value: object) -> str:
    if not isinstance(value, str) or not value.strip() or value.startswith("="):
        raise ValueError("Expected nonempty source text, not a formula")
    if any(ord(char) < 32 and char not in "\n\r\t" for char in value):
        raise ValueError("Source contains unsupported control characters")
    return value


def parse_workbook(path: Path) -> list[Criterion]:
    if path.suffix.lower() != ".xlsx" or path.stat().st_size > 10 * 1024 * 1024:
        raise ValueError("Expected an XLSX file up to 10 MiB")
    with ZipFile(path) as archive:
        if sum(info.file_size for info in archive.infolist()) > 40 * 1024 * 1024:
            raise ValueError("Expanded workbook exceeds 40 MiB")
    workbook = load_workbook(path, read_only=True, data_only=False, keep_links=False)
    try:
        if len(workbook.worksheets) != 15:
            raise ValueError("Expected summary and 14 competency sheets")
        summary = list(workbook.worksheets[0].values)
        if len(summary) < 8 or tuple(summary[7]) != (
            "Lp.",
            "Kompetencja",
            "Liczba wskaźników",
        ):
            raise ValueError("Unexpected summary header")
        entries = [row for row in summary[8:] if any(cell is not None for cell in row)]
        if len(entries) != 14:
            raise ValueError("Expected 14 summary entries")
        sheets = {}
        for sheet in workbook.worksheets[1:]:
            rows = list(sheet.values)
            if len(rows) < 4 or not rows[0]:
                raise ValueError("Incomplete competency sheet")
            title = source_text(rows[0][0])
            if title in sheets:
                raise ValueError("Duplicate competency sheet")
            sheets[title] = rows
        criteria = []
        for entry in entries:
            if len(entry) != 3 or type(entry[2]) is not int or entry[2] < 1:
                raise ValueError("Invalid summary entry")
            name, count = source_text(entry[1]), entry[2]
            rows = sheets.pop(name, None)
            if rows is None or tuple(rows[2]) != (
                "Wskaźnik behawioralny",
                *LEVEL_NAMES,
            ):
                raise ValueError("Missing competency sheet or unexpected level header")
            criterion_id = stable_id(name)
            indicators = []
            for row in rows[3:]:
                if not any(cell is not None for cell in row):
                    continue
                if len(row) != 6:
                    raise ValueError("Expected indicator and five level descriptions")
                description, *levels = map(source_text, row)
                indicators.append(
                    Indicator(
                        id=stable_id(description, criterion_id),
                        description=description,
                        levels=[
                            Level(level=i, name=label, description=text)
                            for i, (label, text) in enumerate(
                                zip(LEVEL_NAMES, levels, strict=True)
                            )
                        ],
                    )
                )
            if len(indicators) != count:
                raise ValueError("Indicator count differs from source summary")
            if len({indicator.id for indicator in indicators}) != count:
                raise ValueError("Duplicate indicator")
            criteria.append(
                Criterion(id=criterion_id, name=name, indicators=indicators)
            )
        if sheets or len({c.id for c in criteria}) != 14:
            raise ValueError("Duplicate or unreferenced competency")
        if sum(len(c.indicators) for c in criteria) != 49:
            raise ValueError("Expected 49 behavior indicators")
        return criteria
    finally:
        workbook.close()


def import_catalog(session: Session, path: Path, version: str) -> CatalogVersion:
    if not 1 <= len(version) <= 100 or not version.strip():
        raise ValueError("Version must contain 1–100 characters")
    criteria = [c.model_dump(mode="json") for c in parse_workbook(path)]
    checksum = hashlib.sha256(path.read_bytes()).hexdigest()
    version_id = uuid5(CATALOG_NAMESPACE, version)
    with session.begin():
        existing = session.scalar(
            select(CatalogVersion).where(CatalogVersion.version == version)
        )
        if existing is not None:
            if existing.source_sha256 != checksum or existing.criteria != criteria:
                raise ValueError("Version already exists with different source content")
            return existing
        catalog = CatalogVersion(
            id=version_id,
            version=version,
            source_name=path.name,
            source_sha256=checksum,
            criteria=criteria,
        )
        session.add(catalog)
        session.flush()
    return catalog


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import the source competency workbook"
    )
    parser.add_argument("path", type=Path)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    engine = create_database_engine(Settings())
    try:
        with Session(engine) as session:
            import_catalog(session, args.path, args.version)
        print("Competency catalog imported and verified")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
