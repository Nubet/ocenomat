from datetime import date, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, select
from test_assessments import assessment_access as assessment_access
from test_assessments import auth, create
from test_first_assessments import qualification

from app.modules.assessments.models import Assessment, AssessmentStatus
from app.modules.employees.models import ManagerEmployeeAssignment
from app.modules.monitoring.models import AssessmentReminder
from app.modules.monitoring.service import monitoring
from app.modules.users.models import User


def remind(access, assessment_id, *, user="hr", key=None):
    return access.client.post(
        f"/api/v1/monitoring/hr/{assessment_id}/reminders",
        headers={**auth(access, user), "Idempotency-Key": str(key or uuid4())},
    )


def test_personal_and_hr_scopes_and_minimal_fields(assessment_access):
    access = assessment_access
    own = create(access).json()
    other = create(access, "b", 2).json()
    personal = access.client.get("/api/v1/monitoring/personal", headers=auth(access))
    assert personal.status_code == 200
    assert personal.headers["cache-control"] == "private, no-store"
    assert [p["id"] for p in personal.json()["processes"]] == [own["id"]]
    assert personal.json()["needs_attention"] == 1
    for role in ("a", "admin", "mixed", "none"):
        assert (
            access.client.get(
                "/api/v1/monitoring/hr", headers=auth(access, role)
            ).status_code
            == 403
        )
    assert access.client.get("/api/v1/monitoring/hr").status_code == 401
    hr = access.client.get("/api/v1/monitoring/hr", headers=auth(access, "hr")).json()
    assert {p["id"] for p in hr["processes"]} == {own["id"], other["id"]}
    assert hr["total"] == 2
    assert set(hr["processes"][0]) == {
        "id",
        "employee_id",
        "employee_name",
        "position",
        "department",
        "assessor_name",
        "kind",
        "form",
        "status",
        "date_assessment",
        "needs_attention",
        "can_remind",
    }
    assert (
        access.client.get(
            "/api/v1/assessments/" + own["id"], headers=auth(access, "hr")
        ).status_code
        == 404
    )
    for role in ("hr", "admin", "none"):
        assert (
            access.client.get(
                "/api/v1/monitoring/personal", headers=auth(access, role)
            ).json()["total"]
            == 0
        )


def test_deadline_boundaries_and_completed_processes(assessment_access):
    access = assessment_access
    saved = create(access).json()
    assessment = access.session.get(Assessment, UUID(saved["id"]))
    today = date(2026, 11, 21)
    assessment.date_talk = today - timedelta(days=100)
    assessment.date_assessment = today + timedelta(days=14)
    access.session.commit()
    user = access.session.get(User, access.users["a"].id)
    result = monitoring(access.session, user, today, hr=False)
    assert len(result.deadlines) == 1
    assert all(d.due_soon and not d.overdue for d in result.deadlines)
    result = monitoring(access.session, user, today - timedelta(days=1), hr=False)
    assert not next(d for d in result.deadlines if d.kind == "assessment").due_soon
    assert result.needs_attention == 0
    result = monitoring(access.session, user, today + timedelta(days=14), hr=False)
    assert result.deadlines[0].due_soon and not result.deadlines[0].overdue
    result = monitoring(access.session, user, today + timedelta(days=15), hr=False)
    assert result.deadlines[0].overdue
    assessment.status = AssessmentStatus.EVALUATION
    access.session.commit()
    assert [
        d.kind for d in monitoring(access.session, user, today, hr=False).deadlines
    ] == ["assessment"]
    assessment.status = AssessmentStatus.COMPLETED
    access.session.commit()
    result = monitoring(access.session, user, today, hr=False)
    assert (
        result.completed == 1 and result.needs_attention == 0 and not result.deadlines
    )


def test_first_statutory_deadlines_without_exposing_report(assessment_access):
    access = assessment_access
    saved = create(access, kind="first", qualification=qualification()).json()
    assert saved["kind"] == "first"
    user = access.session.get(User, access.users["hr"].id)
    result = monitoring(access.session, user, date(2025, 1, 22), hr=True)
    assert {(d.kind, d.due_on) for d in result.deadlines} == {
        ("introduction", date(2025, 1, 22)),
        ("assessment", date(2025, 11, 30)),
    }
    assert result.needs_attention == 1
    assert result.processes[0].date_assessment == date(2025, 11, 30)
    assessment = access.session.get(Assessment, UUID(saved["id"]))
    assessment.status = AssessmentStatus.IN_PROGRESS
    assessment.first.report_to = date(2025, 9, 5)
    assessment.first.report_tasks = "PRIVATE REPORT"
    access.session.commit()
    result = monitoring(access.session, user, date(2025, 9, 4), hr=True)
    assert {d.kind for d in result.deadlines} == {
        "report",
        "assessment",
    }
    assert "PRIVATE REPORT" not in result.model_dump_json()
    assessment.first.report_submitted_on = date(2025, 9, 3)
    access.session.commit()
    result = monitoring(access.session, user, date(2025, 9, 4), hr=True)
    assert [d.kind for d in result.deadlines] == ["assessment"]
    assert result.needs_attention == 0


def test_reminder_is_delivered_to_real_recipient_once(assessment_access):
    access = assessment_access
    saved = create(access).json()
    key = uuid4()
    sent = remind(access, saved["id"], key=key)
    assert sent.status_code == 201
    assert sent.json()["channel"] == "in_app" and sent.json()["status"] == "delivered"
    assert sent.json()["recipient_id"] == str(access.users["a"].id)
    replay = remind(access, saved["id"], key=key)
    assert replay.status_code == 200 and replay.json() == sent.json()
    assert len(access.session.scalars(select(AssessmentReminder)).all()) == 1
    personal = access.client.get(
        "/api/v1/monitoring/personal", headers=auth(access)
    ).json()
    assert personal["reminders"] == [sent.json()]
    other = access.client.get(
        "/api/v1/monitoring/personal", headers=auth(access, "b")
    ).json()
    assert other["reminders"] == []
    second = create(access, employee=1).json()
    assert remind(access, second["id"], key=key).status_code == 409
    hr = access.client.get("/api/v1/monitoring/hr", headers=auth(access, "hr")).json()
    assert hr["reminders"] == [sent.json()]


@pytest.mark.parametrize("role", ["a", "admin", "mixed", "none"])
def test_only_hr_can_send(assessment_access, role):
    access = assessment_access
    saved = create(access).json()
    assert remind(access, saved["id"], user=role).status_code == 403
    assert not access.session.scalars(select(AssessmentReminder)).all()


@pytest.mark.parametrize("unavailable", ["completed", "unassigned", "inactive"])
def test_no_false_delivery_to_unavailable_process(assessment_access, unavailable):
    access = assessment_access
    saved = create(access).json()
    if unavailable == "completed":
        access.session.get(
            Assessment, UUID(saved["id"])
        ).status = AssessmentStatus.COMPLETED
    elif unavailable == "unassigned":
        access.session.execute(
            delete(ManagerEmployeeAssignment).where(
                ManagerEmployeeAssignment.manager_id == access.users["a"].id
            )
        )
    else:
        access.session.get(User, access.users["a"].id).active = False
    access.session.commit()
    assert remind(access, saved["id"]).status_code == 409
    assert not access.session.scalars(select(AssessmentReminder)).all()
    result = access.client.get(
        "/api/v1/monitoring/hr", headers=auth(access, "hr")
    ).json()
    assert not result["processes"][0]["can_remind"]


def test_removed_assignment_hides_existing_reminders(assessment_access):
    access = assessment_access
    saved = create(access).json()
    assert remind(access, saved["id"]).status_code == 201
    access.session.execute(
        delete(ManagerEmployeeAssignment).where(
            ManagerEmployeeAssignment.manager_id == access.users["a"].id
        )
    )
    access.session.commit()
    result = access.client.get(
        "/api/v1/monitoring/personal", headers=auth(access)
    ).json()
    assert not result["processes"] and not result["reminders"]
    assert remind(access, str(uuid4())).status_code == 404
