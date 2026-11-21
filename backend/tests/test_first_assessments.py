from datetime import date
from io import BytesIO

import pytest
from pydantic import ValidationError
from pypdf import PdfReader
from sqlalchemy import select
from test_assessments import assessment_access as assessment_access
from test_assessments import auth, create
from test_documents import MemoryStorage, upload

from app.modules.assessments.first import validate_conversation
from app.modules.assessments.first_rules import (
    FIRST_ELEMENTS,
    calendar_months,
    first_deadlines,
)
from app.modules.assessments.first_schemas import FirstData, FirstQualification
from app.modules.assessments.models import FirstDeadlineChange


def qualification(**changes):
    return {
        "hired_on": "2025-01-01",
        "contract_end": "2025-12-31",
        "employment_basis": "first_contract",
        "eligibility_confirmed": True,
        "qualification_basis": (
            "Fikcyjna umowa art. 35 ust. 3; sprawdzona historia art. 35 ust. 5"
        ),
        "ksap_graduate": False,
        "nomination_requested": False,
        **changes,
    }


def update(access, saved, action="save", **changes):
    return access.client.put(
        f"/api/v1/assessments/{saved['id']}/first",
        headers=auth(access),
        json={
            "revision": saved["revision"],
            "action": action,
            "data": {**saved["first"], **changes},
        },
    )


def test_calendar_boundaries():
    assert calendar_months(date(2024, 10, 31), 4) == date(2025, 2, 28)
    assert calendar_months(date(2023, 10, 31), 4) == date(2024, 2, 29)
    deadlines = first_deadlines(date(2025, 1, 1), date(2025, 12, 31), date(2025, 2, 3))
    assert deadlines.introduction_by == date(2025, 2, 24)
    assert deadlines.assessment_from == date(2025, 9, 1)
    assert deadlines.assessment_by == date(2025, 11, 30)
    with pytest.raises(ValueError):
        first_deadlines(date(2025, 1, 1), date(2025, 8, 31))


@pytest.mark.parametrize(
    "changes",
    [
        {"eligibility_confirmed": False},
        {"ksap_graduate": True, "nomination_requested": True},
        {"employment_basis": "replacement"},
        {"hired_on": "2015-08-26"},
    ],
)
def test_excluded_qualifications(changes):
    with pytest.raises(ValidationError):
        FirstQualification(**qualification(**changes))


def test_preparatory_service_waiver_does_not_exempt_exam():
    with pytest.raises(ValidationError):
        FirstData(
            **qualification(),
            exam="not_applicable",
            exam_basis="Zwolnienie art. 36 ust. 7",
        )
    with pytest.raises(ValidationError):
        FirstData(**qualification(), scores={key: True for key in FIRST_ELEMENTS})


def test_report_requires_seven_months_and_expired_deadline_for_absence():
    data = FirstData(
        **qualification(),
        intro_on="2025-01-20",
        report_to="2025-09-05",
        report_period_from="2025-01-01",
        report_period_to="2025-07-30",
        report_submitted_on="2025-09-03",
        report_tasks="Zadania",
        report_problems="Problemy",
        report_learning="Wiedza",
        report_conclusions="Wnioski",
        exam="passed",
        conversation_on="2025-09-04",
        conversation_confirmed=True,
    )
    with pytest.raises(ValueError, match="seven worked months"):
        validate_conversation(data)
    validate_conversation(
        data.model_copy(update={"report_period_to": date(2025, 7, 31)})
    )
    missing = data.model_copy(
        update={"report_submitted_on": None, "report_missing": True}
    )
    with pytest.raises(ValueError, match="expired deadline"):
        validate_conversation(missing)
    validate_conversation(
        missing.model_copy(update={"conversation_on": date(2025, 9, 6)})
    )


@pytest.mark.integration
def test_first_attachment_uses_shared_document_authorization(assessment_access):
    access = assessment_access
    saved = create(access, kind="first", qualification=qualification()).json()
    path = f"/api/v1/assessments/{saved['id']}"
    access.client.app.state.object_storage = MemoryStorage()
    assert upload(access, path=path, name="b").status_code == 404
    response = upload(access, path=path)
    assert response.status_code == 201, response.text
    saved = access.client.get(path, headers=auth(access)).json()
    assert saved["revision"] == 2
    assert update(access, saved, intro_on="2025-01-20").status_code == 200


@pytest.mark.integration
@pytest.mark.parametrize(
    "exemption,outcome",
    [(None, "positive"), ("ksap", "positive"), ("replacement", "negative")],
)
def test_first_workflow_authorization_result_and_pdf(
    assessment_access, exemption, outcome
):
    access = assessment_access
    q = qualification(
        ksap_graduate=exemption == "ksap",
        employment_basis="replacement"
        if exemption == "replacement"
        else "first_contract",
        replacement_agreed_on="2025-01-01" if exemption == "replacement" else None,
    )
    response = create(access, kind="first", qualification=q)
    assert response.status_code == 201, response.text
    saved = response.json()
    path = f"/api/v1/assessments/{saved['id']}"
    assert saved["form"] == "P" and saved["result"]["outcome"] == "incomplete"
    assert not saved["required_criterion_ids"] and not saved["criteria"]
    assert (
        access.client.post(
            f"/api/v1/ai/assessments/{saved['id']}/job-description-analysis",
            headers=auth(access),
        ).status_code
        == 422
    )
    for name in ("b", "hr", "admin"):
        assert access.client.get(path, headers=auth(access, name)).status_code == 404
        assert (
            access.client.put(
                path + "/first",
                headers=auth(access, name),
                json={"revision": 1, "data": saved["first"]},
            ).status_code
            == 404
        )
    assert (
        access.client.post(
            path + "/transitions",
            headers=auth(access),
            json={"revision": 1, "action": "start_period"},
        ).status_code
        == 422
    )
    assert (
        update(access, saved, "confirm_introduction", intro_on="2025-01-23").status_code
        == 422
    )
    response = update(
        access,
        saved,
        "confirm_introduction",
        intro_on="2025-01-22",
        intro_confirmed=True,
        arrangements_shared=True,
        report_from="2025-09-01",
        report_to="2025-09-05",
    )
    assert response.status_code == 200, response.text
    saved = response.json()
    assert saved["status"] == "in_progress"
    assert update(access, saved, hired_on="2025-01-02").status_code == 422
    response = update(
        access,
        saved,
        "confirm_conversation",
        report_period_from="2025-01-01",
        report_period_to="2025-08-31",
        report_submitted_on="2025-09-03",
        report_tasks="Zadania.",
        report_problems="Nie odnotowano problemów.",
        report_learning="Nowa wiedza.",
        report_conclusions="Usprawnienia.",
        exam="not_applicable" if exemption else "passed",
        exam_basis="§ 10 ust. 3 pkt 1"
        if exemption == "ksap"
        else "§ 10 ust. 3 pkt 2"
        if exemption
        else "Protokół egzaminu.",
        conversation_on="2025-09-04",
        conversation_confirmed=True,
        conversation_notes="Omówiono wymagane zagadnienia.",
    )
    assert response.status_code == 200, response.text
    saved = response.json()
    scores = dict.fromkeys(FIRST_ELEMENTS, 5)
    if outcome == "negative":
        scores["reliability"] = 3
        scores["cooperation"] = 3
    changes = dict(
        scores=scores,
        assessed_on="2025-09-04",
        unit_head_name="Fikcyjny kierujący",
        unit_head_position="Dyrektor",
        unit_head_agreed=True,
    )
    if outcome == "negative":
        assert update(access, saved, "complete", **changes).status_code == 422
        changes["justification"] = "Dwie oceny poniżej oczekiwań."
    response = update(access, saved, "complete", **changes)
    assert response.status_code == 200, response.text
    completed = response.json()
    assert (
        completed["status"] == "completed" and completed["result"]["outcome"] == outcome
    )
    assert update(access, completed).status_code == 409
    assert update(access, completed, "complete").json() == completed
    access.client.app.state.object_storage = MemoryStorage()
    body = dict(
        revision=completed["revision"],
        office_name="Fikcyjny urząd",
        assessor_department="Wydział",
        assessor_position="Naczelnik",
    )
    response = access.client.post(
        path + "/documents/first-pdf", headers=auth(access), json=body
    )
    assert response.status_code == 200, response.text
    document = response.json()
    assert document["kind"] == "first_pdf"
    assert (
        access.client.post(
            path + "/documents/periodic-pdf", headers=auth(access), json=body
        ).status_code
        == 422
    )
    download = access.client.get(
        f"{path}/documents/{document['id']}/download", headers=auth(access)
    )
    text = "\n".join(
        page.extract_text() for page in PdfReader(BytesIO(download.content)).pages
    )
    assert "ARKUSZ PIERWSZEJ OCENY" in text and "Załącznik nr 3" in text
    assert "POZYTYWNA" in text if outcome == "positive" else "NEGATYWNA" in text
    assert (
        access.client.post(
            path + "/documents/first-pdf", headers=auth(access), json=body
        ).json()
        == document
    )


@pytest.mark.integration
def test_deadline_extension_keeps_previous_dates(assessment_access):
    access = assessment_access
    saved = create(access, kind="first", qualification=qualification()).json()
    saved = update(
        access,
        saved,
        "confirm_introduction",
        intro_on="2025-01-20",
        intro_confirmed=True,
        arrangements_shared=True,
        report_from="2025-09-01",
        report_to="2025-09-05",
    ).json()
    body = dict(
        revision=saved["revision"],
        reason="justified_absence",
        basis="Fikcyjne pismo 1/2025",
        circumstance_from="2025-07-01",
        circumstance_to="2025-07-10",
        contract_end="2025-12-31",
        report_from="2025-09-11",
        report_to="2025-09-15",
        notified_on="2025-07-11",
    )
    path = f"/api/v1/assessments/{saved['id']}/first/deadlines"
    bad = access.client.post(
        path, headers=auth(access), json={**body, "report_to": "2025-09-16"}
    )
    assert bad.status_code == 422
    response = access.client.post(path, headers=auth(access), json=body)
    assert response.status_code == 200, response.text
    assert response.json()["first"]["report_to"] == "2025-09-15"
    history = response.json()["first_deadline_changes"]
    assert len(history) == 1 and history[0]["previous_report_to"] == "2025-09-05"
    assert (
        access.client.get(
            f"/api/v1/assessments/{saved['id']}", headers=auth(access)
        ).json()["first_deadline_changes"]
        == history
    )
    change = access.session.scalar(select(FirstDeadlineChange))
    assert (
        change.previous_report_to == date(2025, 9, 5) and change.basis == body["basis"]
    )


@pytest.mark.integration
def test_contract_extension_requires_more_than_three_months(assessment_access):
    access = assessment_access
    saved = create(access, kind="first", qualification=qualification()).json()
    saved = update(
        access,
        saved,
        "confirm_introduction",
        intro_on="2025-01-20",
        intro_confirmed=True,
        arrangements_shared=True,
        report_from="2025-09-01",
        report_to="2025-09-05",
    ).json()
    path = f"/api/v1/assessments/{saved['id']}/first/deadlines"
    body = dict(
        revision=saved["revision"],
        reason="contract_extension",
        basis="Fikcyjny wniosek pracownika i decyzja dyrektora",
        circumstance_from="2025-04-01",
        circumstance_to="2025-06-30",
        notified_on="2025-07-02",
        contract_end="2026-04-01",
        report_from="2025-12-01",
        report_to="2025-12-05",
    )
    assert access.client.post(path, headers=auth(access), json=body).status_code == 422
    body["circumstance_to"] = "2025-07-01"
    body["contract_end"] = "2026-04-02"
    response = access.client.post(path, headers=auth(access), json=body)
    assert response.status_code == 200, response.text
    assert response.json()["first"]["contract_end"] == "2026-04-02"
    assert access.client.post(path, headers=auth(access), json=body).status_code == 409
