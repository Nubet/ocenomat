from uuid import uuid4

import pytest
from sqlalchemy import delete, select
from test_arrangements import arrangements  # noqa: F401
from test_assessments import assessment_access, auth, catalog  # noqa: F401
from test_observations import command, conversation, period  # noqa: F401

from app.modules.assessments.models import Assessment, AssessmentEvent, AssessmentStatus
from app.modules.assessments.rules import SUGGESTION_POLICY
from app.modules.catalog.models import CatalogVersion
from app.modules.employees.models import ManagerEmployeeAssignment

pytestmark = pytest.mark.integration


@pytest.fixture
def evaluation(request):
    access = request.getfixturevalue("period")
    source = access.session.get(CatalogVersion, access.catalog_id)
    access.indicators = [uuid4(), uuid4()]
    source.criteria = [
        {
            **item,
            "indicators": [
                {"id": str(id)}
                for id in (
                    access.indicators
                    if item["id"] == str(access.additional[0])
                    else [uuid4(), uuid4()]
                )
            ],
        }
        for item in source.criteria
    ]
    access.session.commit()
    assert conversation(access).status_code == 200
    assert command(access, "confirm_conversation", 6).status_code == 200
    access.criterion = access.additional[0]
    return access


def answers(access, revision=7, levels=(0, 1), **overrides):
    return access.client.put(
        f"{access.path}/criteria/{access.criterion}/answers",
        headers=auth(access),
        json={
            "revision": revision,
            "answers": [
                {"indicator_id": str(id), "level": level, "note": " Przykład. "}
                for id, level in zip(access.indicators, levels, strict=True)
            ],
            **overrides,
        },
    )


def confirm(access, revision=8, score=9):
    return access.client.post(
        f"{access.path}/criteria/{access.criterion}/rating",
        headers=auth(access),
        json={"revision": revision, "score": score},
    )


def test_answers_suggestion_manual_decision_and_invalidation(evaluation):
    access = evaluation
    response = answers(access)
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "private, no-store"
    rating = response.json()["ratings"][0]
    assert rating["suggested_score"] == 1  # Mean 2: lower score wins the tie.
    assert rating["policy_version"] == SUGGESTION_POLICY
    assert rating["score"] is rating["confirmed_by"] is rating["confirmed_at"] is None
    assert rating["author_id"] == str(access.users["a"].id)
    assert rating["recorded_at"]
    assert all(item["note"] == "Przykład." for item in rating["answers"])
    result = confirm(access).json()
    rating = result["ratings"][0]
    assert rating["suggested_score"] == 1 and rating["score"] == 9
    assert rating["confirmed_by"] == str(access.users["a"].id)
    assert rating["confirmed_at"]
    assert result["status"] == "evaluation" and result["revision"] == 9
    assert access.client.get(access.path, headers=auth(access)).json() == result
    same = answers(access, revision=9).json()
    assert same["ratings"][0] == rating
    changed = answers(access, revision=10, levels=(None, 4)).json()["ratings"][0]
    assert changed["suggested_score"] == 9
    assert (
        changed["score"] is changed["confirmed_by"] is changed["confirmed_at"] is None
    )
    assert confirm(access, revision=11, score=7).json()["ratings"][0]["score"] == 7
    events = access.session.scalars(
        select(AssessmentEvent).where(AssessmentEvent.assessment_id == result["id"])
    ).all()
    assert len(events) == 11
    assert all(event.actor_id == access.users["a"].id for event in events)


def test_note_change_invalidates_only_its_criterion(evaluation):
    access = evaluation
    assert answers(access).status_code == 200
    assert confirm(access).status_code == 200
    other = next(
        item.criterion_id
        for item in access.session.get(Assessment, access.assessment["id"]).criteria
        if item.criterion_id != access.criterion
    )
    access.criterion = other
    assert confirm(access, revision=9, score=3).status_code == 200
    access.criterion = access.additional[0]
    payload = [
        {"indicator_id": str(id), "level": level, "note": "Zmieniona notatka"}
        for id, level in zip(access.indicators, (0, 1), strict=True)
    ]
    result = answers(access, revision=10, answers=payload).json()
    assert {item["criterion_id"]: item["score"] for item in result["ratings"]} == {
        str(access.criterion): None,
        str(other): 3,
    }


def test_no_observations_is_not_a_default_positive_score(evaluation):
    access = evaluation
    saved = answers(access, levels=(None, None)).json()["ratings"][0]
    assert saved["suggested_score"] is saved["score"] is None
    assert confirm(access, score=1).json()["ratings"][0]["score"] == 1


def test_manager_can_decide_without_behavioral_suggestion(evaluation):
    result = confirm(evaluation, revision=7, score=3)
    assert result.status_code == 200
    rating = result.json()["ratings"][0]
    assert rating["score"] == 3 and rating["suggested_score"] is None
    assert rating["answers"] == []


@pytest.mark.parametrize("level", [-1, 5, True, "1", 1.5])
def test_invalid_levels_are_rejected_without_mutation(evaluation, level):
    assert answers(evaluation, levels=(level, 2)).status_code == 422
    assert (
        evaluation.client.get(evaluation.path, headers=auth(evaluation)).json()[
            "revision"
        ]
        == 7
    )


@pytest.mark.parametrize("score", [0, 2, 10, True, "5", 5.5, None])
def test_invalid_manual_scores(evaluation, score):
    assert confirm(evaluation, revision=7, score=score).status_code == 422


@pytest.mark.parametrize(
    "case", ["foreign", "other_criterion", "duplicate", "missing", "long_note", "extra"]
)
def test_answer_set_validated_against_pinned_criterion(evaluation, case):
    access = evaluation
    payload = [
        {"indicator_id": str(id), "level": 2, "note": ""} for id in access.indicators
    ]
    if case == "foreign":
        foreign = uuid4()
        newer = catalog("newer")
        newer.criteria = [
            {"id": str(access.criterion), "indicators": [{"id": str(foreign)}]}
        ]
        access.session.add(newer)
        access.session.commit()
        payload[0]["indicator_id"] = str(foreign)
    elif case == "other_criterion":
        source = access.session.get(CatalogVersion, access.catalog_id)
        other = next(
            item for item in source.criteria if item["id"] != str(access.criterion)
        )
        payload[0]["indicator_id"] = other["indicators"][0]["id"]
    elif case == "duplicate":
        payload[1] = payload[0]
    elif case == "missing":
        payload.pop()
    elif case == "long_note":
        payload[0]["note"] = "x" * 4001
    else:
        payload[0]["suggested_score"] = 9
    assert answers(access, answers=payload).status_code == 422
    assert access.client.get(access.path, headers=auth(access)).json()["ratings"] == []


def test_unselected_criterion_cannot_receive_answers_or_rating(evaluation):
    evaluation.criterion = evaluation.additional[-1]
    assert answers(evaluation).status_code == 422
    assert confirm(evaluation, revision=7).status_code == 422


@pytest.mark.parametrize("operation", [answers, confirm])
def test_stale_write_and_event_failure_roll_back(evaluation, monkeypatch, operation):
    access = evaluation
    assert answers(access).status_code == 200
    saved = confirm(access).json()
    assert operation(access, revision=8).status_code == 409

    def fail(**kwargs):
        raise RuntimeError("Simulated event failure")

    monkeypatch.setattr("app.modules.assessments.service.AssessmentEvent", fail)
    with pytest.raises(RuntimeError, match="Simulated event failure"):
        if operation is answers:
            answers(access, revision=9, levels=(4, 4))
        else:
            confirm(access, revision=9, score=1)
    assert access.client.get(access.path, headers=auth(access)).json() == saved


@pytest.mark.parametrize(
    "name", ["b", "hr", "admin", "mixed", "none", "revoked", "anonymous"]
)
def test_evaluation_requires_author_and_current_assignment(evaluation, name):
    access = evaluation
    if name == "b":
        access.session.add(
            ManagerEmployeeAssignment(
                manager_id=access.users["b"].id, employee_id=access.employees[0]
            )
        )
    if name == "revoked":
        access.session.execute(
            delete(ManagerEmployeeAssignment).where(
                ManagerEmployeeAssignment.manager_id == access.users["a"].id
            )
        )
    access.session.commit()
    headers = (
        {} if name == "anonymous" else auth(access, "a" if name == "revoked" else name)
    )
    for method, suffix, body in [
        ("GET", "", None),
        (
            "PUT",
            f"/criteria/{access.criterion}/answers",
            {
                "revision": 7,
                "answers": [
                    {"indicator_id": str(id), "level": None, "note": ""}
                    for id in access.indicators
                ],
            },
        ),
        ("POST", f"/criteria/{access.criterion}/rating", {"revision": 7, "score": 5}),
    ]:
        assert access.client.request(
            method, access.path + suffix, headers=headers, json=body
        ).status_code == (401 if name == "anonymous" else 404)


@pytest.mark.parametrize(
    "status",
    [
        AssessmentStatus.DRAFT,
        AssessmentStatus.CRITERIA_AGREED,
        AssessmentStatus.IN_PROGRESS,
        AssessmentStatus.COMPLETED,
    ],
)
def test_only_evaluation_is_editable(evaluation, status):
    access = evaluation
    assessment = access.session.get(Assessment, access.assessment["id"])
    assessment.status = status
    access.session.commit()
    assert answers(access).status_code == 409
    assert confirm(access, revision=7).status_code == 409
