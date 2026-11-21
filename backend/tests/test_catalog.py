import os
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook, load_workbook
from sqlalchemy.orm import Session
from test_security import claims, sign

from app.core.database import get_session
from app.main import create_app
from app.modules.assessments.rules import REQUIRED_CRITERIA
from app.modules.catalog.importer import (
    LEVEL_NAMES,
    import_catalog,
    parse_workbook,
    stable_id,
)
from app.modules.users.models import User


@pytest.fixture
def workbook_path(tmp_path):
    workbook = Workbook()
    summary = workbook.active
    for i in range(1, 8):
        summary.cell(i, 1, "Test source")
    summary.append(["Lp.", "Kompetencja", "Liczba wskaźników"])
    for i in range(14):
        name = f"Kompetencja testowa {i}"
        count = 4 if i < 7 else 3
        summary.append([i + 1, name, count])
        sheet = workbook.create_sheet(f"Test {i}")
        sheet.append([name] * 6)
        sheet.append([])
        sheet.append(["Wskaźnik behawioralny", *LEVEL_NAMES])
        for j in range(count):
            sheet.append(
                [f"Zachowanie {i}/{j}", *[f"Żółć\n{i}/{j}/{k}" for k in range(5)]]
            )
    path = tmp_path / "model.xlsx"
    workbook.save(path)
    workbook.close()
    return path


def test_parse_preserves_all_source_text(workbook_path):
    criteria = parse_workbook(workbook_path)
    assert len(criteria) == 14
    assert sum(len(c.indicators) for c in criteria) == 49
    assert criteria[0].indicators[0].levels[2].description == "Żółć\n0/0/2"
    assert criteria[0].indicators[0].levels[2].name == "Na poziomie oczekiwań"
    assert criteria[0].id == stable_id("Kompetencja testowa 0")
    assert criteria == parse_workbook(workbook_path)


@pytest.mark.parametrize(
    "cell,value", [("B4", None), ("B4", "=1+1"), ("B3", "Bad level")]
)
def test_reject_invalid_source(workbook_path, cell, value):
    workbook = load_workbook(workbook_path)
    workbook.worksheets[1][cell] = value
    workbook.save(workbook_path)
    workbook.close()
    with pytest.raises(ValueError):
        parse_workbook(workbook_path)


def test_ids_do_not_depend_on_row_order(workbook_path):
    before = parse_workbook(workbook_path)[0]
    workbook = load_workbook(workbook_path)
    sheet = workbook.worksheets[1]
    first = [c.value for c in sheet[4]]
    second = [c.value for c in sheet[5]]
    for i in range(6):
        sheet.cell(4, i + 1, second[i])
        sheet.cell(5, i + 1, first[i])
    workbook.save(workbook_path)
    workbook.close()
    after = parse_workbook(workbook_path)[0]
    assert before.id == after.id
    assert {i.description: i.id for i in before.indicators} == {
        i.description: i.id for i in after.indicators
    }


@pytest.mark.integration
def test_repeatable_import_and_authorized_catalog(database, workbook_path, key, jwks):
    settings, connection, session = database
    catalog = import_catalog(session, workbook_path, "test-version")
    catalog_id = catalog.id
    expected = [c.model_dump(mode="json") for c in parse_workbook(workbook_path)]
    assert catalog.criteria == expected
    session.rollback()
    assert import_catalog(session, workbook_path, "test-version").id == catalog_id
    session.rollback()
    user = User(auth_subject=uuid4(), display_name="Catalog test")
    session.add(user)
    session.commit()
    app = create_app(settings)

    def override_session():
        with Session(bind=connection, join_transaction_mode="create_savepoint") as db:
            yield db

    app.dependency_overrides[get_session] = override_session
    token = sign(key, claims(sub=str(user.auth_subject)))
    with TestClient(app) as client:
        assert client.get("/api/v1/catalog/criteria").status_code == 401
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/catalog/criteria", headers=headers)
        assert response.status_code == 200
        assert response.json()["criteria"] == expected
        assert (
            client.get(
                f"/api/v1/catalog/criteria?version_id={uuid4()}", headers=headers
            ).status_code
            == 404
        )
    session.rollback()
    workbook = load_workbook(workbook_path)
    workbook.worksheets[1]["B4"] = "Zmiana treści"
    workbook.save(workbook_path)
    workbook.close()
    with pytest.raises(ValueError, match="different source"):
        import_catalog(session, workbook_path, "test-version")


def test_original_source_content():
    source = os.environ.get("KOMPAS_TEST_CATALOG_XLSX")
    if not source:
        pytest.skip("Set KOMPAS_TEST_CATALOG_XLSX to the supplied source workbook")
    criteria = parse_workbook(Path(source))
    for required in REQUIRED_CRITERIA.values():
        assert set(required).issubset(c.id for c in criteria)
    workbook = load_workbook(source, read_only=True, data_only=False)
    try:
        assert len(criteria) == len(workbook.worksheets) - 1 == 14
        for criterion, sheet in zip(criteria, workbook.worksheets[1:], strict=True):
            rows = list(sheet.values)
            assert criterion.name == rows[0][0]
            assert len(criterion.indicators) == len(rows) - 3
            for indicator, row in zip(criterion.indicators, rows[3:], strict=True):
                assert indicator.description == row[0]
                assert [level.description for level in indicator.levels] == list(
                    row[1:]
                )
    finally:
        workbook.close()
