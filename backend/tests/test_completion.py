import pytest
from sqlalchemy import delete, select
from test_arrangements import arrangements as arrangements
from test_assessments import assessment_access, auth, catalog  # noqa: F401
from test_evaluation import answers
from test_evaluation import evaluation as evaluation
from test_observations import command, conversation, period  # noqa: F401

from app.modules.assessments.models import Assessment, AssessmentEvent, AssessmentStatus
from app.modules.employees.models import ManagerEmployeeAssignment

pytestmark = pytest.mark.integration


def summary(access, revision, **extra):
    return access.client.put(
        access.path + "/summary",
        headers=auth(access),
        json={
            "revision": revision,
            "negative_justification": "",
            "development_conclusions": " Rozwijać wiedzę. ",
            **extra,
        },
    )


def rate_all(access, scores):
    saved = access.client.get(access.path, headers=auth(access)).json()
    for criterion, score in zip(saved["criteria"], scores, strict=True):
        response = access.client.post(
            f"{access.path}/criteria/{criterion['criterion_id']}/rating",
            headers=auth(access),
            json={"revision": saved["revision"], "score": score},
        )
        assert response.status_code == 200, response.text
        saved = response.json()
    return saved


@pytest.mark.parametrize(
    "scores,outcome,mean",
    [
        ([3, 3, 5, 5, 3, 5], "negative", "4.00"),
        ([3, 3, 5, 5, 5, 5], "positive", "4.33"),
        ([1, 9, 9, 9, 9, 9], "negative", "7.67"),
        ([9, 9, 9, 9, 9, 9], "positive", "9.00"),
    ],
)
def test_result_boundaries_and_completion_snapshot(evaluation, scores, outcome, mean):
    access = evaluation
    saved = rate_all(access, scores)
    assert saved["result"] == {"outcome": outcome, "mean": mean}
    assert saved["status"] == "evaluation"
    response = access.client.get(access.path + "/result", headers=auth(access))
    assert response.json() == saved["result"]
    assert response.headers["cache-control"] == "private, no-store"
    saved = summary(
        access, saved["revision"], negative_justification=" Konkretne powody. "
    ).json()
    revision = saved["revision"]
    completed = command(access, "complete", revision)
    assert completed.status_code == 200, completed.text
    result = completed.json()
    assert result["status"] == "completed" and result["revision"] == revision + 1
    assert result["summary"]["completed_by"] == str(access.users["a"].id)
    assert result["summary"]["completed_at"]
    assert result["summary"]["development_conclusions"] == "Rozwijać wiedzę."
    assert result["summary"]["recorded_at"] == saved["summary"]["recorded_at"]
    assert result["result"] == {"outcome": outcome, "mean": mean}
    for replay in (revision, revision + 1):
        assert command(access, "complete", replay).json() == result
    assert command(access, "complete", revision - 1).status_code == 409
    assert access.client.get(access.path, headers=auth(access)).json() == result
    events = access.session.scalars(
        select(AssessmentEvent).where(
            AssessmentEvent.assessment_id == result["id"],
            AssessmentEvent.kind == "assessment_completed",
        )
    ).all()
    assert len(events) == 1 and events[0].revision == revision + 1
    assert events[0].actor_id == access.users["a"].id


def test_suggestions_and_invalidated_ratings_do_not_produce_result(evaluation):
    access = evaluation
    assert answers(access, levels=(4, 4)).json()["result"] == {
        "outcome": "incomplete",
        "mean": None,
    }
    saved = rate_all(access, [5] * 6)
    assert saved["result"]["outcome"] == "positive"
    saved = answers(access, revision=saved["revision"], levels=(0, 0)).json()
    assert saved["result"] == {"outcome": "incomplete", "mean": None}
    saved = summary(access, saved["revision"]).json()
    assert command(access, "complete", saved["revision"]).status_code == 422
    assert access.client.get(access.path, headers=auth(access)).json() == saved


def test_negative_requires_saved_nonblank_justification(evaluation):
    access = evaluation
    saved = rate_all(access, [3] * 6)
    assert command(access, "complete", saved["revision"]).status_code == 422
    saved = summary(access, saved["revision"], negative_justification="  \n ").json()
    assert command(access, "complete", saved["revision"]).status_code == 422
    saved = summary(access, saved["revision"], negative_justification="Powody.").json()
    assert command(access, "complete", saved["revision"]).status_code == 200


def test_positive_allows_explicit_empty_development_conclusions(evaluation):
    saved = rate_all(evaluation, [5] * 6)
    saved = summary(evaluation, saved["revision"], development_conclusions="").json()
    assert command(evaluation, "complete", saved["revision"]).status_code == 200


@pytest.mark.parametrize("field", ["negative_justification", "development_conclusions"])
def test_summary_validation_and_stale_revision(evaluation, field):
    access = evaluation
    assert summary(access, 7, **{field: "x" * 10001}).status_code == 422
    assert summary(access, 7, outcome="positive").status_code == 422
    saved = summary(access, 7).json()
    assert summary(access, 7).status_code == 409
    assert command(access, "complete", 7).status_code == 409
    assert access.client.get(access.path, headers=auth(access)).json() == saved


@pytest.mark.parametrize("operation", ["summary", "complete"])
def test_completion_event_failure_is_atomic(evaluation, monkeypatch, operation):
    access = evaluation
    saved = rate_all(access, [5] * 6)
    saved = summary(access, saved["revision"]).json()

    def fail(**kwargs):
        raise RuntimeError("Simulated event failure")

    monkeypatch.setattr("app.modules.assessments.service.AssessmentEvent", fail)
    with pytest.raises(RuntimeError, match="Simulated event failure"):
        if operation == "summary":
            summary(access, saved["revision"], development_conclusions="Changed")
        else:
            command(access, "complete", saved["revision"])
    assert access.client.get(access.path, headers=auth(access)).json() == saved


@pytest.mark.parametrize("missing", ["duties_discussed", "conversation", "criteria"])
def test_completion_rechecks_prerequisites(evaluation, missing):
    access = evaluation
    saved = rate_all(access, [5] * 6)
    saved = summary(access, saved["revision"]).json()
    record = access.session.get(Assessment, saved["id"])
    if missing == "criteria":
        criterion = next(item for item in record.criteria if item.required)
        criterion.required = False
        criterion.justification = "Invalid selection"
    elif missing == "conversation":
        record.conversation.confirmed_at = None
    else:
        record.duties_discussed = False
    access.session.commit()
    assert command(access, "complete", saved["revision"]).status_code == 422


def test_every_mutation_is_blocked_after_completion(evaluation):
    access = evaluation
    saved = rate_all(access, [5] * 6)
    saved = summary(access, saved["revision"]).json()
    saved = command(access, "complete", saved["revision"]).json()
    rev = saved["revision"]
    assert summary(access, rev).status_code == 409
    assert answers(access, revision=rev).status_code == 409
    assert (
        access.client.post(
            f"{access.path}/criteria/{access.criterion}/rating",
            headers=auth(access),
            json={"revision": rev, "score": 1},
        ).status_code
        == 409
    )
    assert conversation(access, revision=rev).status_code == 409
    for method, suffix, body in [
        ("PUT", "/criteria", {"revision": rev, "additional": []}),
        (
            "PATCH",
            "",
            {
                "revision": rev,
                "date_talk": "2026-01-10",
                "date_assessment": "2027-01-10",
                "duties_discussed": True,
                "expectations_discussed": True,
                "arrangements_shared": True,
            },
        ),
        (
            "POST",
            "/observations",
            {
                "revision": rev,
                "criterion_id": str(access.criterion),
                "text": "Late observation",
                "occurred_on": "2026-03-12",
            },
        ),
    ]:
        assert (
            access.client.request(
                method, access.path + suffix, headers=auth(access), json=body
            ).status_code
            == 409
        )
    for action in ("agree_criteria", "start_period", "confirm_conversation"):
        assert command(access, action, rev).status_code == 409
    assert access.client.get(access.path, headers=auth(access)).json() == saved


def test_completed_replay_still_requires_current_assignment(evaluation):
    access = evaluation
    saved = rate_all(access, [5] * 6)
    saved = summary(access, saved["revision"]).json()
    assert command(access, "complete", saved["revision"]).status_code == 200
    access.session.execute(
        delete(ManagerEmployeeAssignment).where(
            ManagerEmployeeAssignment.manager_id == access.users["a"].id,
        )
    )
    access.session.commit()
    assert command(access, "complete", saved["revision"]).status_code == 404


def test_draft_result_is_incomplete_and_get_does_not_mutate(arrangements):
    access = arrangements
    before = access.client.get(access.path, headers=auth(access)).json()
    assert access.client.get(access.path + "/result", headers=auth(access)).json() == {
        "outcome": "incomplete",
        "mean": None,
    }
    assert access.client.get(access.path, headers=auth(access)).json() == before


@pytest.mark.parametrize(
    "name", ["b", "hr", "admin", "mixed", "none", "revoked", "anonymous"]
)
def test_result_summary_and_completion_require_current_author(evaluation, name):
    access = evaluation
    if name == "revoked":
        access.session.execute(
            delete(ManagerEmployeeAssignment).where(
                ManagerEmployeeAssignment.manager_id == access.users["a"].id,
            )
        )
        access.session.commit()
    headers = (
        {} if name == "anonymous" else auth(access, "a" if name == "revoked" else name)
    )
    for method, suffix, body in [
        ("GET", "/result", None),
        (
            "PUT",
            "/summary",
            {
                "revision": 7,
                "negative_justification": "",
                "development_conclusions": "",
            },
        ),
        ("POST", "/transitions", {"revision": 7, "action": "complete"}),
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
    ],
)
def test_summary_and_completion_unavailable_before_evaluation(evaluation, status):
    record = evaluation.session.get(Assessment, evaluation.assessment["id"])
    record.status = status
    evaluation.session.commit()
    assert summary(evaluation, 7).status_code == 409
    assert command(evaluation, "complete", 7).status_code == 409
