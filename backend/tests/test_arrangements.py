from datetime import date, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import delete, select
from test_assessments import assessment_access, auth, catalog, create  # noqa: F401

from app.modules.assessments.models import Assessment, AssessmentEvent, AssessmentStatus
from app.modules.assessments.rules import REQUIRED_CRITERIA
from app.modules.catalog.models import CatalogVersion
from app.modules.employees.models import (
    Employee,
    ManagerEmployeeAssignment,
    PositionKind,
)

pytestmark = pytest.mark.integration


@pytest.fixture
def arrangements(request):
    access = request.getfixturevalue("assessment_access")
    form = getattr(request, "param", "C")
    access.session.get(Employee, access.employees[0]).position_kind = (
        PositionKind.DIRECT_MANAGER if form == "B" else PositionKind.OTHER
    )
    access.additional = [uuid4() for _ in range(4)]
    source = access.session.get(CatalogVersion, access.catalog_id)
    source.criteria = [
        {"id": str(id)} for id in (*REQUIRED_CRITERIA[form], *access.additional)
    ]
    access.session.commit()
    access.assessment = create(access).json()
    access.path = f"/api/v1/assessments/{access.assessment['id']}"
    return access


def criteria(access, revision=1, ids=None, **extra):
    return access.client.put(
        access.path + "/criteria",
        headers=auth(access),
        json={
            "revision": revision,
            "additional": [
                {
                    "criterion_id": str(id),
                    "justification": "  Obowiązki wynikające z OSP.  ",
                }
                for id in (ids if ids is not None else access.additional[:1])
            ],
            **extra,
        },
    )


def dates(access, revision=2, **extra):
    return access.client.patch(
        access.path,
        headers=auth(access),
        json={
            "revision": revision,
            "date_talk": "2026-01-10",
            "date_assessment": "2027-01-10",
            "duties_discussed": True,
            "expectations_discussed": True,
            "arrangements_shared": True,
            **extra,
        },
    )


def transition(access, revision=3):
    return access.client.post(
        access.path + "/transitions",
        headers=auth(access),
        json={"revision": revision, "action": "agree_criteria"},
    )


def test_save_reload_confirm_and_record_author(arrangements):
    access = arrangements
    selected = criteria(access)
    assert selected.status_code == 200
    saved = selected.json()
    assert saved["revision"] == 2 and saved["status"] == "draft"
    assert len(saved["criteria"]) == 6
    assert {row["criterion_id"] for row in saved["criteria"] if row["required"]} == set(
        map(str, REQUIRED_CRITERIA["C"])
    )
    assert (
        next(row for row in saved["criteria"] if not row["required"])["justification"]
        == "Obowiązki wynikające z OSP."
    )
    assert dates(access).status_code == 200
    confirmed = transition(access)
    assert confirmed.status_code == 200
    result = confirmed.json()
    assert result["revision"] == 4 and result["status"] == "criteria_agreed"
    assert result["date_talk"] == "2026-01-10"
    for _ in range(2):
        response = access.client.get(access.path + "?step=timing", headers=auth(access))
        assert response.json() == result
        assert response.headers["cache-control"] == "private, no-store"
    events = list(
        access.session.scalars(
            select(AssessmentEvent)
            .where(AssessmentEvent.assessment_id == access.assessment["id"])
            .order_by(AssessmentEvent.revision)
        )
    )
    assert [event.kind for event in events] == [
        "criteria_updated",
        "dates_updated",
        "criteria_agreed",
    ]
    assert all(
        event.actor_id == access.users["a"].id and event.recorded_at.tzinfo
        for event in events
    )
    assert events[-1].occurred_on == date(2026, 1, 10)
    assert criteria(access, revision=4).status_code == 409
    assert dates(access, revision=4).status_code == 409
    assert transition(access, revision=4).status_code == 409


def test_zero_extras_and_replacement_are_valid(arrangements):
    access = arrangements
    assert len(criteria(access, ids=[]).json()["criteria"]) == 5
    assert (
        len(criteria(access, revision=2, ids=access.additional[:3]).json()["criteria"])
        == 8
    )
    assert len(criteria(access, revision=3, ids=[]).json()["criteria"]) == 5


@pytest.mark.parametrize(
    "case", ["duplicate", "required", "unknown", "limit", "blank", "long", "extra"]
)
def test_invalid_selection_does_not_change_revision_or_events(arrangements, case):
    access = arrangements
    ids = {
        "duplicate": access.additional[:1] * 2,
        "required": [REQUIRED_CRITERIA["C"][0]],
        "unknown": [uuid4()],
        "limit": access.additional,
    }.get(case, access.additional[:1])
    extra = {}
    if case in {"blank", "long"}:
        extra["additional"] = [
            {
                "criterion_id": str(ids[0]),
                "justification": "  " if case == "blank" else "x" * 4001,
            }
        ]
    if case == "extra":
        extra["status"] = "completed"
    assert criteria(access, ids=ids, **extra).status_code == 422
    assert (
        access.client.get(access.path, headers=auth(access)).json() == access.assessment
    )
    assert (
        access.session.scalar(
            select(AssessmentEvent).where(
                AssessmentEvent.assessment_id == access.assessment["id"]
            )
        )
        is None
    )


def test_validation_uses_pinned_catalog_not_latest(arrangements):
    access = arrangements
    newer = catalog("new")
    # An ID only in a later version cannot be selected in this assessment.
    newer.criteria = [{"id": str(uuid4())}]
    access.session.add(newer)
    access.session.commit()
    assert criteria(access, ids=[newer.criteria[0]["id"]]).status_code == 422
    assert criteria(access).status_code == 200


@pytest.mark.parametrize(
    "data",
    [
        {"date_talk": "bad"},
        {"date_assessment": "2025-01-01"},
        {"date_talk": None},
        {
            "date_talk": (date.today() + timedelta(days=365)).isoformat(),
            "date_assessment": (date.today() + timedelta(days=366)).isoformat(),
        },
        {"arrangements_shared": "true"},
        {"status": "completed"},
        {"revision": True},
    ],
)
def test_invalid_dates_and_server_owned_fields_are_rejected(arrangements, data):
    access = arrangements
    assert dates(access, **{"revision": 1, **data}).status_code == 422
    assert (
        access.client.get(access.path, headers=auth(access)).json() == access.assessment
    )


def test_partial_actions_can_be_saved_but_not_confirmed(arrangements):
    access = arrangements
    assert transition(access, revision=1).status_code == 422
    assert criteria(access).status_code == 200
    assert dates(access, arrangements_shared=False).status_code == 200
    assert transition(access).status_code == 422
    assert dates(access, revision=3).status_code == 200
    assert transition(access, revision=4).status_code == 200


def test_future_conversation_can_be_planned_without_inventing_completed_actions(
    arrangements,
):
    access = arrangements
    assert criteria(access).status_code == 200
    response = dates(
        access,
        date_talk=(date.today() + timedelta(days=365)).isoformat(),
        date_assessment=(date.today() + timedelta(days=366)).isoformat(),
        duties_discussed=False,
        expectations_discussed=False,
        arrangements_shared=False,
    )
    assert response.status_code == 200
    assert transition(access).status_code == 422


def test_stale_revision_never_overwrites_saved_work(arrangements):
    access = arrangements
    saved = criteria(access).json()
    assert criteria(access, ids=[]).status_code == 409
    assert dates(access, revision=1).status_code == 409
    assert access.client.get(access.path, headers=auth(access)).json() == saved


def test_failed_event_rolls_back_criteria_replacement(arrangements, monkeypatch):
    access = arrangements
    saved = criteria(access).json()

    def fail_event(**kwargs):
        raise RuntimeError("Simulated event failure")

    monkeypatch.setattr("app.modules.assessments.service.AssessmentEvent", fail_event)
    with pytest.raises(RuntimeError, match="Simulated event failure"):
        criteria(access, revision=2, ids=[])
    assert access.client.get(access.path, headers=auth(access)).json() == saved


@pytest.mark.parametrize(
    "name", ["b", "hr", "admin", "mixed", "none", "revoked", "anonymous"]
)
def test_mutations_require_current_assignment_and_ownership(arrangements, name):
    access = arrangements
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
    for method, suffix, data in [
        ("PUT", "/criteria", {"revision": 1, "additional": []}),
        (
            "PATCH",
            "",
            {
                "revision": 1,
                "date_talk": "2026-01-10",
                "date_assessment": "2027-01-10",
                "duties_discussed": False,
                "expectations_discussed": False,
                "arrangements_shared": False,
            },
        ),
        ("POST", "/transitions", {"revision": 1, "action": "agree_criteria"}),
    ]:
        response = access.client.request(
            method, access.path + suffix, headers=headers, json=data
        )
        assert response.status_code == (401 if name == "anonymous" else 404)
    access.session.expire_all()
    assert (
        access.session.get(Assessment, access.assessment["id"]).status
        == AssessmentStatus.DRAFT
    )
