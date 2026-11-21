import hashlib
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path

import pytest
from pypdf import PdfReader
from sqlalchemy import delete, event, func, select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session
from test_arrangements import arrangements as arrangements
from test_assessments import assessment_access as assessment_access
from test_assessments import auth, catalog, create  # noqa: F401
from test_completion import rate_all, summary
from test_document_validation import docx_bytes
from test_documents import MemoryStorage
from test_evaluation import evaluation as evaluation
from test_observations import command, period  # noqa: F401

from app.modules.assessments.models import Assessment, AssessmentEvent, AssessmentStatus
from app.modules.assessments.rules import REQUIRED_CRITERIA
from app.modules.assessments.service import AssessmentError
from app.modules.catalog.models import CatalogVersion
from app.modules.documents.import_osp import import_osp
from app.modules.documents.models import Document, JobDescription
from app.modules.documents.pdf import PERIODIC_TEMPLATES
from app.modules.documents.validation import DOCX_TYPE
from app.modules.employees.models import ManagerEmployeeAssignment
from app.modules.users.models import User

pytestmark = pytest.mark.integration


def details(revision):
    return dict(
        revision=revision,
        office_name="Urząd w Łodzi",
        assessor_department="Wydział żółtej łódki",
        assessor_position="Naczelnik",
        period_end=date.today().isoformat(),
        civil_service_status="employee",
        previous_assessment=None,
        no_promotion_request=True,
    )


@pytest.fixture
def completed(evaluation):
    access = evaluation
    source = access.session.get(CatalogVersion, access.catalog_id)
    source.criteria = [
        {**item, "name": f"Kryterium {index}"}
        for index, item in enumerate(source.criteria)
    ]
    access.session.commit()
    saved = rate_all(access, [5] * 6)
    saved = summary(access, saved["revision"]).json()
    access.completed = command(access, "complete", saved["revision"]).json()
    access.storage = MemoryStorage()
    access.client.app.state.object_storage = access.storage
    return access


def generate(access, *, name="a", changes=None):
    body = details(access.completed["revision"])
    body.update(changes or {})
    return access.client.post(
        access.path + "/documents/periodic-pdf", headers=auth(access, name), json=body
    )


@pytest.mark.parametrize("arrangements", ["B", "C"], indirect=True)
def test_generated_pdf_contains_source_sections_and_only_confirmed_data(
    arrangements, completed
):
    access = completed
    before = access.client.get(access.path, headers=auth(access)).json()
    form = before["form"]
    template_version, source_sha256 = PERIODIC_TEMPLATES[form]
    assert before["required_criterion_ids"] == list(map(str, REQUIRED_CRITERIA[form]))
    assert {
        row["criterion_id"] for row in before["criteria"] if row["required"]
    } == set(map(str, REQUIRED_CRITERIA[form]))
    assert {
        row["criterion_id"] for row in before["criteria"] if not row["required"]
    } == {str(access.additional[0])}
    events = access.session.scalar(select(func.count()).select_from(AssessmentEvent))
    response = generate(access)
    assert response.status_code == 200, response.text
    doc = response.json()
    assert doc["kind"] == "periodic_pdf" and doc["template_version"] == template_version
    assert doc["filename"] == f"Arkusz-{form}-{before['id']}.pdf"
    assert doc["assessment_revision"] == before["revision"]
    assert "generation_data" not in doc and "object_key" not in doc
    content = access.client.get(
        f"{access.path}/documents/{doc['id']}/download", headers=auth(access)
    ).content
    assert hashlib.sha256(content).hexdigest() == doc["sha256"]
    reader = PdfReader(BytesIO(content), strict=True)
    text = "\n".join(page.extract_text() for page in reader.pages)
    for value in (
        f"Załącznik nr {3 if form == 'B' else 4} · ARKUSZ {form}",
        template_version,
        "CZĘŚĆ I",
        "CZĘŚĆ II",
        "Urząd w Łodzi",
        "Wydział żółtej łódki",
        "WNIOSKI DOTYCZĄCE",
        "Pouczenie",
        "Rozwijać wiedzę.",
        "5,00",
        before["employee_snapshot"]["name"],
    ):
        assert value in text
    assert "CZĘŚĆ III" not in text and len(reader.pages) >= 3
    assert "POZYTYWNA\nX" in text
    fonts = [
        obj.get_object()
        for page in reader.pages
        for obj in page["/Resources"]["/Font"].get_object().values()
    ]
    assert any("/ToUnicode" in font for font in fonts)
    stored = access.session.get(Document, doc["id"])
    assert stored.generation_data["source_sha256"] == source_sha256
    assert generate(access).json() == doc
    assert generate(access, changes={"office_name": "Inny urząd"}).status_code == 409
    assert len(access.storage.objects) == 1
    assert access.client.get(access.path, headers=auth(access)).json() == before
    assert (
        access.session.scalar(select(func.count()).select_from(AssessmentEvent))
        == events
    )


def test_negative_result_keeps_high_mean_but_marks_negative(evaluation):
    access = evaluation
    source = access.session.get(CatalogVersion, access.catalog_id)
    source.criteria = [
        {**item, "name": f"Kryterium {index}"}
        for index, item in enumerate(source.criteria)
    ]
    access.session.commit()
    saved = rate_all(access, [1, 9, 9, 9, 9, 9])
    saved = summary(
        access,
        saved["revision"],
        negative_justification="Nie zrealizował zadań. Zażółć gęślą jaźń.",
    ).json()
    access.completed = command(access, "complete", saved["revision"]).json()
    access.storage = MemoryStorage()
    access.client.app.state.object_storage = access.storage
    doc = generate(access).json()
    reader = PdfReader(
        BytesIO(
            access.storage.objects[access.session.get(Document, doc["id"]).object_key]
        )
    )
    text = "\n".join(page.extract_text() for page in reader.pages)
    assert "NEGATYWNA\nX" in text and "7,67" in text
    assert "Zażółć gęślą jaźń." in text


@pytest.mark.parametrize(
    "changes",
    [
        {"office_name": " "},
        {"period_end": "1900-01-01"},
        {"period_end": (date.today() + timedelta(days=1)).isoformat()},
        {"no_promotion_request": False},
        {"outcome": "positive"},
        {"office_name": "Bad\x00value"},
    ],
)
def test_invalid_generation_never_writes(completed, changes):
    assert generate(completed, changes=changes).status_code == 422
    assert completed.storage.calls == []


@pytest.mark.parametrize("name", ["b", "hr", "admin", "none", "mixed"])
def test_pdf_generation_requires_current_author_and_assignment(completed, name):
    assert generate(completed, name=name).status_code == 404
    assert completed.storage.calls == []


def test_revoked_assignment_cannot_generate_or_download(completed):
    access = completed
    doc = generate(access).json()
    access.session.execute(
        delete(ManagerEmployeeAssignment).where(
            ManagerEmployeeAssignment.manager_id == access.users["a"].id
        )
    )
    access.session.commit()
    access.storage.calls.clear()
    assert generate(access).status_code == 404
    assert (
        access.client.get(
            f"{access.path}/documents/{doc['id']}/download", headers=auth(access)
        ).status_code
        == 404
    )
    assert access.storage.calls == []


@pytest.mark.parametrize("failure", ["storage", "database", "lost_commit", "font"])
def test_generation_failures_and_commit_recovery(completed, monkeypatch, failure):
    access = completed
    if failure == "storage":
        access.storage.fail = {"put"}
    elif failure == "font":
        access.client.app.state.pdf_font_path = "/missing/font.ttf"
    elif failure == "lost_commit":
        commit = Session.commit

        def lost_commit(session):
            commit(session)
            raise OperationalError("COMMIT", {}, Exception("ack lost"))

        monkeypatch.setattr(Session, "commit", lost_commit)

    def fail(session, *_):
        if any(isinstance(item, Document) for item in session.new):
            raise IntegrityError("statement", {}, Exception("private"))

    if failure == "database":
        event.listen(Session, "before_flush", fail)
    try:
        result = generate(access)
    finally:
        if failure == "database":
            event.remove(Session, "before_flush", fail)
    assert result.status_code == 503, result.text
    if failure == "lost_commit":
        assert len(access.storage.objects) == 1
        assert access.session.scalar(select(func.count()).select_from(Document)) == 1
    else:
        assert access.storage.objects == {}
        assert access.session.scalar(select(func.count()).select_from(Document)) == 0


def test_generation_requires_completed_current_revision(completed):
    access = completed
    assert (
        generate(
            access, changes={"revision": access.completed["revision"] - 1}
        ).status_code
        == 409
    )
    assessment = access.session.get(Assessment, access.completed["id"])
    assessment.status = AssessmentStatus.EVALUATION
    access.session.commit()
    assert generate(access).status_code == 409
    assert access.storage.calls == []


def test_long_unicode_text_is_not_truncated_or_interpreted_as_markup(completed):
    access = completed
    assessment = access.session.get(Assessment, access.completed["id"])
    assessment.summary.development_conclusions = (
        "Zażółć gęślą jaźń. " * 500
    ) + " <b>OSTATNI FRAGMENT</b>"
    access.session.commit()
    doc = generate(access).json()
    reader = PdfReader(
        BytesIO(
            access.storage.objects[access.session.get(Document, doc["id"]).object_key]
        )
    )
    text = "\n".join(page.extract_text() for page in reader.pages)
    assert "<b>OSTATNI FRAGMENT</b>" in text
    assert text.count("Zażółć") == 500


def test_official_previous_assessment_is_explicit(completed):
    previous = {"outcome": "negative", "level": 2, "assessed_on": "2025-01-01"}
    assert (
        generate(completed, changes={"previous_assessment": previous}).status_code
        == 422
    )
    response = generate(
        completed,
        changes={"civil_service_status": "official", "previous_assessment": previous},
    )
    assert response.status_code == 200, response.text
    doc = completed.session.get(Document, response.json()["id"])
    assert doc.generation_data["previous_assessment"] == previous


@pytest.mark.parametrize("form", ["B", "C"])
def test_template_source_has_not_changed(form):
    source = (
        Path(__file__).parents[2]
        / "docs/hacknation-materials/Ocena okresowa w służbie cywilnej"
        / f"Arkusz oceny {form} (2).docx"
    )
    if not source.exists():
        pytest.skip(f"Requires the supplied form {form} source")
    assert (
        hashlib.sha256(source.read_bytes()).hexdigest() == PERIODIC_TEMPLATES[form][1]
    )


def test_explicit_source_import_is_versioned_and_does_not_create_an_assessment(
    assessment_access, tmp_path
):
    access = assessment_access
    source = tmp_path / "Opis stanowiska.docx"
    source.write_bytes(docx_bytes())
    user = access.session.get(User, access.users["a"].id)
    storage = MemoryStorage()
    first = import_osp(access.session, user, access.employees[0], source, storage)
    repeated = import_osp(access.session, user, access.employees[0], source, storage)
    assert first.id == repeated.id and first.version == 1
    assert first.document.assessment_id is None
    assert access.session.scalar(select(func.count()).select_from(Assessment)) == 0
    source.write_bytes(
        docx_bytes(
            **{
                "word/document.xml": (
                    '<w:document xmlns:w="http://schemas.openxmlformats.org/'
                    'wordprocessingml/2006/main"><w:body><w:p><w:r>'
                    "<w:t>Nowy opis</w:t></w:r></w:p></w:body></w:document>"
                )
            }
        )
    )
    second = import_osp(access.session, user, access.employees[0], source, storage)
    assert second.id != first.id and second.version == 2


@pytest.mark.parametrize("name", ["b", "hr", "admin"])
def test_source_import_requires_assigned_active_manager(
    assessment_access, tmp_path, name
):
    access = assessment_access
    source = tmp_path / "Opis.docx"
    source.write_bytes(docx_bytes())
    storage = MemoryStorage()
    user = access.session.get(User, access.users[name].id)
    with pytest.raises(AssessmentError, match="Assigned employee not found"):
        import_osp(access.session, user, access.employees[0], source, storage)
    assert storage.calls == []


def test_other_employee_osp_is_not_available_through_an_assessment(
    assessment_access, tmp_path
):
    access = assessment_access
    source = tmp_path / "Opis.docx"
    source.write_bytes(docx_bytes())
    storage = MemoryStorage()
    user = access.session.get(User, access.users["a"].id)
    description = import_osp(access.session, user, access.employees[1], source, storage)
    assessment = create(access).json()
    access.client.app.state.object_storage = storage
    path = f"/api/v1/assessments/{assessment['id']}/documents"
    assert (
        access.client.put(
            path + "/job-descriptions/select",
            headers=auth(access),
            json={"revision": 1, "job_description_id": str(description.id)},
        ).status_code
        == 404
    )
    assert (
        access.client.get(
            f"{path}/job-descriptions/{description.id}/download", headers=auth(access)
        ).status_code
        == 404
    )
    assert (
        access.client.get(
            f"{path}/{description.document_id}/download", headers=auth(access)
        ).status_code
        == 404
    )


def test_source_import_failed_put_removes_object_and_metadata(
    assessment_access, tmp_path
):
    from app.integrations.storage import StorageUnavailable

    access = assessment_access
    source = tmp_path / "Opis.docx"
    source.write_bytes(docx_bytes())
    storage = MemoryStorage()
    storage.fail = {"put"}
    user = access.session.get(User, access.users["a"].id)
    with pytest.raises(StorageUnavailable):
        import_osp(access.session, user, access.employees[0], source, storage)
    assert storage.objects == {}
    assert access.session.scalar(select(func.count()).select_from(JobDescription)) == 0


def test_versioned_osp_can_be_reused_without_changing_historical_selection(
    assessment_access,
):
    access = assessment_access
    access.client.app.state.object_storage = MemoryStorage()
    first = create(access).json()
    path = f"/api/v1/assessments/{first['id']}/documents"

    def upload(revision):
        return access.client.post(
            path,
            params={
                "kind": "osp",
                "revision": revision,
                "filename": "Opis stanowiska.docx",
            },
            headers={**auth(access), "Content-Type": DOCX_TYPE},
            content=docx_bytes(),
        )

    assert upload(1).status_code == 201
    versions = access.client.get(
        path + "/job-descriptions", headers=auth(access)
    ).json()
    description = versions[0]
    assert (
        description["version"] == 1
        and description["employee_id"] == first["employee_id"]
    )
    selected = access.client.get(
        path.removesuffix("/documents"), headers=auth(access)
    ).json()
    assert (
        selected["job_description_id"] == description["id"]
        and selected["revision"] == 2
    )
    assert upload(1).status_code == 409
    second = create(access).json()
    second_path = f"/api/v1/assessments/{second['id']}/documents"
    selected = access.client.put(
        second_path + "/job-descriptions/select",
        headers=auth(access),
        json={"revision": 1, "job_description_id": description["id"]},
    )
    assert selected.status_code == 200, selected.text
    assert selected.json()["job_description_id"] == description["id"]
    assert (
        access.client.get(
            f"{second_path}/job-descriptions/{description['id']}/download",
            headers=auth(access),
        ).content
        == docx_bytes()
    )
    assert upload(2).status_code == 201
    versions = access.client.get(
        path + "/job-descriptions", headers=auth(access)
    ).json()
    assert [item["version"] for item in versions] == [2, 1]
    assert (
        access.client.get(
            second_path.removesuffix("/documents"), headers=auth(access)
        ).json()["job_description_id"]
        == description["id"]
    )
    record = access.session.get(Assessment, first["id"])
    record.status = AssessmentStatus.CRITERIA_AGREED
    access.session.commit()
    assert upload(3).status_code == 409
    assert (
        access.client.put(
            path + "/job-descriptions/select",
            headers=auth(access),
            json={"revision": 3, "job_description_id": description["id"]},
        ).status_code
        == 409
    )
    for name in ("b", "hr", "admin"):
        assert (
            access.client.get(
                path + "/job-descriptions", headers=auth(access, name)
            ).status_code
            == 404
        )
        assert (
            access.client.get(
                f"{path}/job-descriptions/{description['id']}/download",
                headers=auth(access, name),
            ).status_code
            == 404
        )
    assert len(access.session.scalars(select(JobDescription)).all()) == 2
