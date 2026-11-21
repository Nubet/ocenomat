from datetime import date, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import delete, select
from test_arrangements import arrangements, criteria, dates, transition  # noqa: F401
from test_assessments import assessment_access, auth  # noqa: F401

from app.modules.assessments.models import Assessment, AssessmentEvent, AssessmentStatus
from app.modules.employees.models import ManagerEmployeeAssignment

pytestmark = pytest.mark.integration


def command(access, action, revision):
    return access.client.post(
        access.path + "/transitions",
        headers=auth(access),
        json={"action": action, "revision": revision},
    )


@pytest.fixture
def period(request):
    access = request.getfixturevalue("arrangements")
    assert criteria(access).status_code == 200
    assert dates(access).status_code == 200
    assert transition(access).status_code == 200
    assert command(access, "start_period", 4).status_code == 200
    return access


def observation(access, revision=5, **extra):
    return access.client.post(
        access.path + "/observations",
        headers=auth(access),
        json={
            "revision": revision,
            "criterion_id": str(access.additional[0]),
            "text": "  Sytuacja — działanie — rezultat.  ",
            "occurred_on": "2026-02-12",
            **extra,
        },
    )


def conversation(access, revision=5, **extra):
    return access.client.put(
        access.path + "/conversation",
        headers=auth(access),
        json={
            "revision": revision,
            "agenda": " Omówienie pracy ",
            "strengths": "Rzetelność",
            "growth": "Dalsze ustalenia",
            "occurred_on": "2026-03-12",
            **extra,
        },
    )


def test_observation_conversation_resume_and_explicit_confirmation(period):
    access = period
    initial = access.client.get(access.path, headers=auth(access)).json()
    assert initial["observations"] == [] and initial["conversation"] is None
    saved = observation(access)
    assert saved.status_code == 200
    row = saved.json()["observations"][0]
    assert row["text"] == "Sytuacja — działanie — rezultat."
    assert row["occurred_on"] == "2026-02-12"
    assert row["author_id"] == str(access.users["a"].id)
    assert row["recorded_at"] and row["id"]
    second = observation(access, revision=6, text="Drugi przykład").json()
    assert len(second["observations"]) == 2
    draft = conversation(access, revision=7, occurred_on=None)
    assert draft.status_code == 200 and draft.json()["status"] == "in_progress"
    assert command(access, "confirm_conversation", 8).status_code == 422
    dated = conversation(access, revision=8)
    assert dated.status_code == 200
    confirmed = command(access, "confirm_conversation", 9)
    assert confirmed.status_code == 200
    result = confirmed.json()
    assert result["status"] == "evaluation" and result["revision"] == 10
    talk = result["conversation"]
    assert talk["agenda"] == "Omówienie pracy"
    assert talk["author_id"] == talk["confirmed_by"] == str(access.users["a"].id)
    assert talk["confirmed_at"] and talk["recorded_at"]
    assert talk["recorded_at"] == dated.json()["conversation"]["recorded_at"]
    for _ in range(2):
        resumed = access.client.get(
            access.path + "?step=conversation", headers=auth(access)
        )
        assert resumed.json() == result
        assert resumed.headers["cache-control"] == "private, no-store"
    events = list(
        access.session.scalars(
            select(AssessmentEvent)
            .where(AssessmentEvent.assessment_id == result["id"])
            .order_by(AssessmentEvent.revision)
        )
    )
    assert [item.kind for item in events][-5:] == [
        "observation_added",
        "observation_added",
        "conversation_updated",
        "conversation_updated",
        "conversation_confirmed",
    ]
    assert events[-1].occurred_on == date(2026, 3, 12)
    assert all(
        item.actor_id == access.users["a"].id and item.recorded_at.tzinfo
        for item in events
    )
    assert observation(access, revision=10).status_code == 409
    assert conversation(access, revision=10).status_code == 409
    assert command(access, "confirm_conversation", 10).status_code == 409


@pytest.mark.parametrize(
    "data",
    [
        {"text": " \n\t "},
        {"text": "x" * 10001},
        {"text": None},
        {"occurred_on": "2026-01-09"},
        {"occurred_on": "bad"},
        {"occurred_on": (date.today() + timedelta(days=2)).isoformat()},
        {"criterion_id": str(uuid4())},
        {"revision": True},
        {"author_id": str(uuid4())},
        {"status": "completed"},
    ],
)
def test_invalid_observation_has_no_side_effects(period, data):
    access = period
    before = access.client.get(access.path, headers=auth(access)).json()
    assert observation(access, **data).status_code == 422
    assert access.client.get(access.path, headers=auth(access)).json() == before


@pytest.mark.parametrize(
    "data",
    [
        {"agenda": "x" * 10001},
        {"strengths": None},
        {"growth": "x" * 10001},
        {"occurred_on": "2026-01-09"},
        {"occurred_on": "bad"},
        {"occurred_on": (date.today() + timedelta(days=2)).isoformat()},
        {"confirmed_by": str(uuid4())},
        {"revision": 0},
        {"confirmed_at": "2026-03-12"},
    ],
)
def test_invalid_conversation_preserves_previous_work(period, data):
    access = period
    saved = conversation(access).json()
    assert conversation(access, **{"revision": 6, **data}).status_code == 422
    assert access.client.get(access.path, headers=auth(access)).json() == saved


def test_unknown_or_unselected_criterion_is_rejected(period):
    assert (
        observation(period, criterion_id=str(period.additional[1])).status_code == 422
    )


def test_conversation_and_observations_are_optional(period):
    access = period
    assert command(access, "confirm_conversation", 5).status_code == 422
    assert conversation(access, agenda="", strengths="", growth="").status_code == 200
    assert command(access, "confirm_conversation", 6).status_code == 200


def test_completed_assessment_rejects_all_activity_changes(period):
    access = period
    assessment = access.session.get(Assessment, access.assessment["id"])
    assessment.status = AssessmentStatus.COMPLETED
    access.session.commit()
    assert observation(access).status_code == 409
    assert conversation(access).status_code == 409
    assert command(access, "confirm_conversation", 5).status_code == 409


def test_confirmation_failure_rolls_back_status_and_confirmation(period, monkeypatch):
    access = period
    saved = conversation(access).json()

    def fail(**kwargs):
        raise RuntimeError("Simulated event failure")

    monkeypatch.setattr("app.modules.assessments.service.AssessmentEvent", fail)
    with pytest.raises(RuntimeError, match="Simulated event failure"):
        command(access, "confirm_conversation", 6)
    assert access.client.get(access.path, headers=auth(access)).json() == saved


@pytest.mark.parametrize("operation", [observation, conversation])
def test_conflict_and_event_failure_preserve_work(period, monkeypatch, operation):
    access = period
    saved = operation(access).json()
    assert operation(access).status_code == 409
    assert access.client.get(access.path, headers=auth(access)).json() == saved

    def fail(**kwargs):
        raise RuntimeError("Simulated event failure")

    monkeypatch.setattr("app.modules.assessments.service.AssessmentEvent", fail)
    with pytest.raises(RuntimeError, match="Simulated event failure"):
        operation(access, revision=6)
    assert access.client.get(access.path, headers=auth(access)).json() == saved


@pytest.mark.parametrize(
    "name", ["b", "hr", "admin", "mixed", "none", "revoked", "anonymous"]
)
def test_read_and_write_require_author_and_current_assignment(period, name):
    access = period
    assert observation(access).status_code == 200
    assert conversation(access, revision=6).status_code == 200
    if name == "b":
        access.session.add(
            ManagerEmployeeAssignment(
                manager_id=access.users["b"].id, employee_id=access.employees[0]
            )
        )
        access.session.commit()
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
    for method, suffix, payload in [
        ("GET", "", None),
        (
            "POST",
            "/observations",
            {
                "revision": 7,
                "criterion_id": str(access.additional[0]),
                "text": "test",
                "occurred_on": "2026-02-12",
            },
        ),
        (
            "PUT",
            "/conversation",
            {
                "revision": 7,
                "agenda": "",
                "strengths": "",
                "growth": "",
                "occurred_on": None,
            },
        ),
        ("POST", "/transitions", {"revision": 7, "action": "confirm_conversation"}),
    ]:
        response = access.client.request(
            method, access.path + suffix, headers=headers, json=payload
        )
        assert response.status_code == (401 if name == "anonymous" else 404)
    access.session.expire_all()
    assert access.session.get(Assessment, access.assessment["id"]).revision == 7


def test_navigation_does_not_start_period_and_draft_cannot_skip_steps(request):
    access = request.getfixturevalue("arrangements")
    assert command(access, "start_period", 1).status_code == 409
    assert observation(access, revision=1).status_code == 409
    assert conversation(access, revision=1).status_code == 409
    assert command(access, "confirm_conversation", 1).status_code == 409
    assert criteria(access).status_code == 200
    assert dates(access).status_code == 200
    assert transition(access).status_code == 200
    assert (
        access.client.get(access.path + "?step=period", headers=auth(access)).json()[
            "status"
        ]
        == "criteria_agreed"
    )
    assert command(access, "start_period", 3).status_code == 409
    assert command(access, "start_period", 4).status_code == 200
    assert command(access, "start_period", 5).status_code == 409
    access.session.expire_all()
    assert (
        access.session.get(Assessment, access.assessment["id"]).status
        == AssessmentStatus.IN_PROGRESS
    )
