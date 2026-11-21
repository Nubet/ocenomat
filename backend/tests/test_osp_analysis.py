import io
import json
import os
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from docx import Document as DocxDocument
from pydantic import ValidationError
from sqlalchemy import delete, update
from test_assessments import assessment_access as assessment_access
from test_assessments import auth, create
from test_assistant import StubProvider, review
from test_documents import MemoryStorage

from app.modules.ai.osp import OspDraft, osp_fragments, validate_recommendations
from app.modules.assessments.models import Assessment
from app.modules.assessments.rules import REQUIRED_CRITERIA
from app.modules.catalog.models import CatalogVersion
from app.modules.documents.validation import DOCX_TYPE
from app.modules.employees.models import ManagerEmployeeAssignment
from app.modules.knowledge.extraction import extract_source

DUTY = "Analizuje ryzyka cyberbezpieczeństwa i opracowuje rekomendacje działań."
EXTRA = uuid4()
CATALOG = [
    {
        "id": str(id),
        "name": f"Test criterion {i}",
        "indicators": [{"description": "Analiza zadań."}],
    }
    for i, id in enumerate(
        (*dict.fromkeys((*REQUIRED_CRITERIA["C"], *REQUIRED_CRITERIA["B"])), EXTRA)
    )
]


def source_bytes():
    doc = DocxDocument()
    doc.add_heading("Zadania dominujące", 1)
    doc.add_paragraph(DUTY)
    table = doc.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "Kierowanie pracownikami"
    table.cell(0, 1).text = "Nie kieruje pracownikami."
    stream = io.BytesIO()
    doc.save(stream)
    return stream.getvalue()


@pytest.fixture
def parts():
    extraction = extract_source(Path("OSP.docx"), source_bytes())
    return osp_fragments(uuid4(), extraction)


def draft(parts, **changes):
    id, part = next((id, part) for id, part in parts.items() if DUTY in part.content)
    return {
        "recommendations": [
            {
                "criterion_id": str(EXTRA),
                "reason": "Zadanie wymaga analizy ryzyk oraz rekomendowania działań.",
                "evidence": [{"fragment_id": str(id), "quote": part.content}],
                **changes,
            }
        ]
    }


@pytest.mark.parametrize("form", ["B", "C"])
def test_recommendations_use_catalog_and_actual_structural_locators(parts, form):
    result = validate_recommendations(
        OspDraft.model_validate(draft(parts)),
        form=form,
        catalog=CATALOG,
        document_id=uuid4(),
        fragments=parts,
    )
    assert len(result) == 1
    assert result[0].criterion_id == EXTRA
    assert result[0].evidence[0].locator == "body/paragraph-2"
    assert result[0].evidence[0].page is None
    assert any("Nie kieruje" in part.content for part in parts.values())


@pytest.mark.parametrize(
    "invalid", ["required", "unknown", "duplicate", "quote", "fragment"]
)
def test_catalog_and_evidence_validation_fail_closed(parts, invalid):
    payload = draft(parts)
    item = payload["recommendations"][0]
    if invalid == "required":
        item["criterion_id"] = str(REQUIRED_CRITERIA["C"][0])
    elif invalid == "unknown":
        item["criterion_id"] = str(uuid4())
    elif invalid == "duplicate":
        payload["recommendations"].append(item)
    elif invalid == "quote":
        item["evidence"][0]["quote"] = "Wymyślone obowiązki pracownika."
    else:
        item["evidence"][0]["fragment_id"] = str(uuid4())
    assert (
        validate_recommendations(
            OspDraft.model_validate(payload),
            form="C",
            catalog=CATALOG,
            document_id=uuid4(),
            fragments=parts,
        )
        is None
    )


def test_pydantic_enforces_maximum_three_and_no_score_fields(parts):
    payload = draft(parts)
    with pytest.raises(ValidationError):
        OspDraft.model_validate({"recommendations": payload["recommendations"] * 4})
    payload["recommendations"][0]["score"] = 9
    with pytest.raises(ValidationError):
        OspDraft.model_validate(payload)


@pytest.fixture
def osp_api(assessment_access):
    access = assessment_access
    catalog = access.session.get(CatalogVersion, access.catalog_id)
    catalog.criteria = CATALOG
    access.session.commit()
    record = create(access).json()
    access.path = f"/api/v1/ai/assessments/{record['id']}/job-description-analysis"
    access.assessment_path = f"/api/v1/assessments/{record['id']}"
    access.storage = MemoryStorage()
    access.client.app.state.object_storage = access.storage
    response = access.client.post(
        access.assessment_path + "/documents",
        params={"kind": "osp", "revision": 1, "filename": "OSP.docx"},
        headers={**auth(access), "Content-Type": DOCX_TYPE},
        content=source_bytes(),
    )
    assert response.status_code == 201, response.text
    document_id = UUID(response.json()["document"]["id"])
    extraction = extract_source(Path("OSP.docx"), source_bytes())
    access.parts = osp_fragments(document_id, extraction)
    access.client.app.state.llm_provider = StubProvider(draft(access.parts), review())
    access.storage.calls.clear()
    return access


@pytest.mark.integration
def test_analysis_is_authorized_read_only_and_uses_selected_osp(osp_api):
    access = osp_api
    before = access.client.get(access.assessment_path, headers=auth(access)).json()
    response = access.client.post(access.path, headers=auth(access))
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "recommended" and len(data["required"]) == 5
    assert data["recommendations"][0]["evidence"][0]["quote"] == DUTY
    assert data["assessment_revision"] == 2
    assert response.headers["cache-control"] == "private, no-store"
    assert (
        before == access.client.get(access.assessment_path, headers=auth(access)).json()
    )
    assert "object_key" not in response.text
    context = json.loads(access.client.app.state.llm_provider.calls[0][0][1].content)
    assert any("Nie kieruje" in part["content"] for part in context["osp"])
    assert "Test Anna" not in json.dumps(context)


@pytest.mark.integration
@pytest.mark.parametrize("name", ["b", "hr", "admin", "none"])
def test_private_osp_is_never_read_or_sent_for_unauthorized_user(osp_api, name):
    assert (
        osp_api.client.post(osp_api.path, headers=auth(osp_api, name)).status_code
        == 404
    )
    assert not osp_api.storage.calls
    assert not osp_api.client.app.state.llm_provider.calls


@pytest.mark.integration
def test_missing_osp_and_invalid_model_selection_are_honest_refusals(osp_api):
    access = osp_api
    fresh = create(access).json()
    response = access.client.post(
        f"/api/v1/ai/assessments/{fresh['id']}/job-description-analysis",
        headers=auth(access),
    )
    assert response.json()["status"] == "insufficient_evidence"
    assert not access.client.app.state.llm_provider.calls
    access.client.app.state.llm_provider.results[0]["recommendations"][0][
        "criterion_id"
    ] = str(REQUIRED_CRITERIA["C"][0])
    response = access.client.post(access.path, headers=auth(access))
    assert response.json()["status"] == "insufficient_evidence"
    assert not response.json()["recommendations"]


@pytest.mark.integration
def test_semantically_unrelated_recommendation_is_not_shown(osp_api):
    osp_api.client.app.state.llm_provider.results[1] = review(
        status="insufficient_evidence", supported_claims=[]
    )
    response = osp_api.client.post(osp_api.path, headers=auth(osp_api))
    assert response.json()["status"] == "insufficient_evidence"
    assert not response.json()["recommendations"]


@pytest.mark.integration
def test_revocation_before_second_model_call_prevents_sending_osp_again(osp_api):
    access = osp_api
    provider = access.client.app.state.llm_provider
    payload = provider.results[0]

    def revoke():
        access.session.get_bind().execute(
            delete(ManagerEmployeeAssignment).where(
                ManagerEmployeeAssignment.manager_id == access.users["a"].id
            )
        )
        return payload

    provider.results[0] = revoke
    assert access.client.post(access.path, headers=auth(access)).status_code == 404
    assert len(provider.calls) == 1


@pytest.mark.integration
def test_changed_assessment_context_does_not_return_stale_suggestions(osp_api):
    access = osp_api
    provider = access.client.app.state.llm_provider

    def change():
        access.session.get_bind().execute(
            update(Assessment).values(revision=Assessment.revision + 1)
        )
        return review()

    provider.results[1] = change
    assert access.client.post(access.path, headers=auth(access)).status_code == 409


@pytest.mark.parametrize(
    "name,needle",
    [
        ("OSP DC WZKSOiC 6 starszy specjalista.docx", "cyber"),
        ("OSP DSI WWI 5 radca.docx", "inteligenc"),
        ("OSP DWM WKAM 1 naczelnik wydziału.docx", "międzynarod"),
    ],
)
def test_three_original_osps_keep_structured_duties_and_stable_fragment_ids(
    name, needle
):
    root = os.environ.get("KOMPAS_TEST_KNOWLEDGE_MATERIALS")
    if not root:
        pytest.skip("Requires original job descriptions")
    path = (
        Path(root)
        / "Kompetencje wspierające analizę OSP + przykładowe OSP/OSP_word"
        / name
    )
    content = path.read_bytes()
    extraction = extract_source(path, content)
    id = uuid4()
    fragments = osp_fragments(id, extraction)
    assert fragments == osp_fragments(id, extract_source(path, content))
    assert all(
        part.page is None and part.locator.startswith(("body/", "word/"))
        for part in fragments.values()
    )
    assert any(needle in part.content.lower() for part in fragments.values())
    assert "zadania" in " ".join(part.content.lower() for part in fragments.values())
