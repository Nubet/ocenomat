import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Barrier
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session
from test_security import claims, sign

from app.core.database import create_database_engine, get_session
from app.main import create_app
from app.modules.assessments.completion import complete_assessment, save_summary
from app.modules.assessments.evaluation import confirm_rating, save_answers
from app.modules.assessments.models import Assessment
from app.modules.assessments.rules import REQUIRED_CRITERIA
from app.modules.assessments.schemas import (
    AnswersUpdate,
    AssessmentCreate,
    ConversationUpdate,
    CriteriaUpdate,
    DatesUpdate,
    ObservationCreate,
    RatingConfirm,
    SummaryUpdate,
)
from app.modules.assessments.service import (
    AssessmentError,
    add_observation,
    agree_criteria,
    confirm_conversation,
    create_assessment,
    save_conversation,
    save_criteria,
    save_dates,
    start_period,
)
from app.modules.catalog.models import CatalogVersion
from app.modules.employees.models import (
    Employee,
    ManagerEmployeeAssignment,
    OrganizationalUnit,
    PositionKind,
)
from app.modules.users.models import Role, User, UserRole

pytestmark = pytest.mark.integration


def catalog(version="test", **kwargs):
    return CatalogVersion(
        id=uuid4(),
        version=version,
        source_name="Fictional test catalog",
        source_sha256="0" * 64,
        criteria=[],
        **kwargs,
    )


@pytest.fixture
def assessment_access(database, key, jwks):
    settings, connection, session = database
    users = {}
    for name, roles in {
        "a": [Role.MANAGER],
        "b": [Role.MANAGER],
        "hr": [Role.HR],
        "admin": [Role.ADMIN],
        "mixed": [Role.MANAGER, Role.ADMIN],
        "none": [],
    }.items():
        user = User(
            auth_subject=uuid4(),
            display_name=name,
            roles=[UserRole(role=role) for role in roles],
        )
        session.add(user)
        session.flush()
        users[name] = SimpleNamespace(id=user.id, auth_subject=user.auth_subject)
    unit = OrganizationalUnit(name="Fictional assessment unit")
    source = catalog()
    session.add_all([unit, source])
    session.flush()
    people = [
        Employee(
            name=name,
            position="Test specialist",
            position_kind=PositionKind.OTHER,
            unit_id=unit.id,
        )
        for name in ["Test Anna", "Test Beata", "Test Celina"]
    ]
    session.add_all(people)
    session.flush()
    ids = [person.id for person in people]
    session.add_all(
        [
            ManagerEmployeeAssignment(manager_id=users["a"].id, employee_id=ids[0]),
            ManagerEmployeeAssignment(manager_id=users["a"].id, employee_id=ids[1]),
            ManagerEmployeeAssignment(manager_id=users["b"].id, employee_id=ids[2]),
        ]
    )
    source_id = source.id
    session.commit()
    app = create_app(settings)

    def override_session():
        with Session(bind=connection, join_transaction_mode="create_savepoint") as db:
            yield db

    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as client:
        yield SimpleNamespace(
            client=client,
            users=users,
            employees=ids,
            catalog_id=source_id,
            session=session,
            key=key,
        )


def auth(access, name="a", **overrides):
    return {
        "Authorization": "Bearer "
        + sign(
            access.key, claims(sub=str(access.users[name].auth_subject), **overrides)
        )
    }


def create(access, name="a", employee=0, request_key=None, **extra):
    return access.client.post(
        "/api/v1/assessments",
        headers={**auth(access, name), "Idempotency-Key": str(request_key or uuid4())},
        json={
            "employee_id": str(access.employees[employee]),
            "kind": "periodic",
            **extra,
        },
    )


@pytest.mark.parametrize(
    "kind,form", [(PositionKind.OTHER, "C"), (PositionKind.DIRECT_MANAGER, "B")]
)
def test_creation_resume_and_history_have_separate_uuids(assessment_access, kind, form):
    access = assessment_access
    access.session.get(Employee, access.employees[0]).position_kind = kind
    access.session.commit()
    first = create(access)
    second = create(access)
    assert first.status_code == second.status_code == 201
    one, two = first.json(), second.json()
    assert one["id"] != two["id"]
    assert one["employee_id"] == two["employee_id"] == str(access.employees[0])
    assert one["status"] == "draft" and one["revision"] == 1 and one["form"] == form
    assert one["required_criterion_ids"] == list(map(str, REQUIRED_CRITERIA[form]))
    assert one["assessor_id"] == str(access.users["a"].id)
    assert one["catalog_version_id"] == str(access.catalog_id)
    assert "idempotency_key" not in one
    for _ in range(2):
        response = access.client.get(first.headers["location"], headers=auth(access))
        assert response.status_code == 200 and response.json() == one
        assert response.headers["cache-control"] == "private, no-store"
    history = access.client.get(
        "/api/v1/assessments",
        params={"employee_id": str(access.employees[0])},
        headers=auth(access),
    )
    assert {row["id"] for row in history.json()} == {one["id"], two["id"]}
    assert (
        access.client.get(
            "/api/v1/assessments",
            params={"employee_id": str(access.employees[1])},
            headers=auth(access),
        ).json()
        == []
    )


def test_retry_reuses_assessment_and_conflicting_payload_is_rejected(assessment_access):
    access = assessment_access
    key = uuid4()
    first = create(access, request_key=key)
    replay = create(access, request_key=key)
    assert first.status_code == 201 and replay.status_code == 200
    assert first.json() == replay.json()
    conflict = create(access, request_key=key, employee=1)
    assert conflict.status_code == 409
    assert (
        len(access.client.get("/api/v1/assessments", headers=auth(access)).json()) == 1
    )


@pytest.mark.parametrize("name", ["b", "hr", "admin", "mixed", "none"])
def test_list_and_detail_do_not_grant_automatic_access(assessment_access, name):
    access = assessment_access
    created = create(access).json()
    assert (
        access.client.get("/api/v1/assessments", headers=auth(access, name)).json()
        == []
    )
    assert (
        access.client.get(
            f"/api/v1/assessments/{created['id']}", headers=auth(access, name)
        ).status_code
        == 404
    )
    assert access.client.get(
        f"/api/v1/assessments/{uuid4()}", headers=auth(access, name)
    ).json() == {"detail": "Assessment not found"}
    forbidden = create(access, name=name)
    assert forbidden.status_code == (404 if name in {"b", "mixed"} else 403)


def test_another_assigned_manager_has_independent_history_and_idempotency_scope(
    assessment_access,
):
    access = assessment_access
    access.session.add(
        ManagerEmployeeAssignment(
            manager_id=access.users["b"].id, employee_id=access.employees[0]
        )
    )
    access.session.commit()
    key = uuid4()
    one = create(access, request_key=key).json()
    two = create(access, name="b", request_key=key).json()
    assert one["id"] != two["id"]
    for name, expected in [("a", one), ("b", two)]:
        assert access.client.get(
            "/api/v1/assessments", headers=auth(access, name)
        ).json() == [expected]


def test_revoked_assignment_blocks_reads_and_retries(assessment_access):
    access = assessment_access
    key = uuid4()
    created = create(access, request_key=key).json()
    access.session.execute(
        delete(ManagerEmployeeAssignment).where(
            ManagerEmployeeAssignment.manager_id == access.users["a"].id
        )
    )
    access.session.commit()
    assert access.client.get("/api/v1/assessments", headers=auth(access)).json() == []
    assert (
        access.client.get(
            f"/api/v1/assessments/{created['id']}", headers=auth(access)
        ).status_code
        == 404
    )
    assert create(access, request_key=key).status_code == 404


def test_employee_and_catalog_snapshots_survive_later_changes(assessment_access):
    access = assessment_access
    key = uuid4()
    old = create(access, request_key=key).json()
    access.session.get(Employee, access.employees[0]).name = "Changed name"
    newer = catalog("newer", imported_at=datetime.now(UTC) + timedelta(seconds=10))
    newer_id = newer.id
    access.session.add(newer)
    access.session.commit()
    assert create(access, request_key=key).json() == old
    new = create(access).json()
    assert new["employee_snapshot"]["name"] == "Changed name"
    assert new["catalog_version_id"] == str(newer_id)
    assert old["employee_snapshot"]["name"] == "Test Anna"
    assert old["catalog_version_id"] == str(access.catalog_id)


def test_form_a_is_explicitly_unsupported_and_does_not_create_rows(assessment_access):
    access = assessment_access
    access.session.get(
        Employee, access.employees[0]
    ).position_kind = PositionKind.OFFICE_HEAD
    access.session.commit()
    response = create(access)
    assert response.status_code == 422 and "Form A" in response.json()["detail"]
    assert access.client.get("/api/v1/assessments", headers=auth(access)).json() == []


@pytest.mark.parametrize(
    "extra",
    [
        {"kind": "first"},
        {"status": "completed"},
        {"revision": 99},
        {"assessor_id": str(uuid4())},
        {"form": "A"},
    ],
)
def test_clients_cannot_choose_unsupported_types_or_server_owned_fields(
    assessment_access, extra
):
    assert create(assessment_access, **extra).status_code == 422


def test_catalog_is_required_without_fallback(assessment_access):
    access = assessment_access
    access.session.execute(delete(CatalogVersion))
    access.session.commit()
    assert create(access).status_code == 503
    assert access.client.get("/api/v1/assessments", headers=auth(access)).json() == []


def test_request_key_and_auth_are_required(assessment_access):
    access = assessment_access
    body = {"employee_id": str(access.employees[0]), "kind": "periodic"}
    for key in [None, "bad-key"]:
        headers = auth(access)
        if key is not None:
            headers["Idempotency-Key"] = key
        assert (
            access.client.post(
                "/api/v1/assessments", json=body, headers=headers
            ).status_code
            == 422
        )
    for method, path in [
        ("GET", "/api/v1/assessments"),
        ("GET", f"/api/v1/assessments/{uuid4()}"),
        ("POST", "/api/v1/assessments"),
    ]:
        assert access.client.request(method, path, json=body).status_code == 401
        assert (
            access.client.request(
                method, path, json=body, headers=auth(access, exp=int(time.time()) - 60)
            ).status_code
            == 401
        )


def test_concurrent_retries_create_exactly_one_record(database):
    settings, _, _ = database
    engine = create_database_engine(settings)
    user_id, employee_id, unit_id, catalog_id, subject, key = [
        uuid4() for _ in range(6)
    ]
    indicator_id = uuid4()
    try:
        with Session(engine) as session, session.begin():
            session.add_all(
                [
                    User(
                        id=user_id,
                        auth_subject=subject,
                        display_name="Concurrent test",
                        roles=[UserRole(role=Role.MANAGER)],
                    ),
                    OrganizationalUnit(id=unit_id, name=f"Concurrency {unit_id}"),
                    CatalogVersion(
                        id=catalog_id,
                        version=str(catalog_id),
                        source_name="Concurrent test",
                        source_sha256="0" * 64,
                        criteria=[
                            {"id": str(id), "indicators": [{"id": str(indicator_id)}]}
                            for id in REQUIRED_CRITERIA["C"]
                        ],
                    ),
                ]
            )
            session.flush()
            session.add(
                Employee(
                    id=employee_id,
                    name="Concurrent employee",
                    position="Test",
                    position_kind=PositionKind.OTHER,
                    unit_id=unit_id,
                )
            )
            session.flush()
            session.add(
                ManagerEmployeeAssignment(manager_id=user_id, employee_id=employee_id)
            )

        def worker(_):
            with Session(engine) as session:
                user = session.get(User, user_id)
                assessment, created = create_assessment(
                    session,
                    user,
                    AssessmentCreate(employee_id=employee_id, kind="periodic"),
                    key,
                )
                return assessment.id, created

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(worker, range(2)))
        assert len({id for id, _ in results}) == 1
        assert sorted(created for _, created in results) == [False, True]
        assessment_id = results[0][0]
        barrier = Barrier(2)

        def edit_worker(_):
            with Session(engine) as session:
                user = session.get(User, user_id)
                stale = session.get(Assessment, assessment_id)
                assert stale.revision == 1
                barrier.wait(timeout=5)
                try:
                    saved = save_criteria(
                        session,
                        user,
                        assessment_id,
                        CriteriaUpdate(revision=1, additional=[]),
                    )
                    return saved.revision
                except AssessmentError as error:
                    return error.code

        with ThreadPoolExecutor(max_workers=2) as pool:
            edits = list(pool.map(edit_worker, range(2)))
        assert set(edits) == {2, "conflict"}
        with Session(engine) as session:
            user = session.get(User, user_id)
            today = datetime.now(UTC).date() - timedelta(days=1)
            save_dates(
                session,
                user,
                assessment_id,
                DatesUpdate(
                    revision=2,
                    date_talk=today,
                    date_assessment=today,
                    duties_discussed=True,
                    expectations_discussed=True,
                    arrangements_shared=True,
                ),
            )
            agree_criteria(session, user, assessment_id, 3)
            start_period(session, user, assessment_id, 4)
            save_conversation(
                session,
                user,
                assessment_id,
                ConversationUpdate(
                    revision=5,
                    agenda="",
                    strengths="",
                    growth="",
                    occurred_on=today,
                ),
            )

        barrier = Barrier(2)

        def activity_worker(index):
            with Session(engine) as session:
                user = session.get(User, user_id)
                stale = session.get(Assessment, assessment_id)
                assert stale.revision == 6
                barrier.wait(timeout=5)
                try:
                    if index == 0:
                        saved = add_observation(
                            session,
                            user,
                            assessment_id,
                            ObservationCreate(
                                revision=6,
                                criterion_id=REQUIRED_CRITERIA["C"][0],
                                text="Concurrent observation",
                                occurred_on=today,
                            ),
                        )
                    else:
                        saved = confirm_conversation(session, user, assessment_id, 6)
                    return saved.revision
                except AssessmentError as error:
                    return error.code

        with ThreadPoolExecutor(max_workers=2) as pool:
            activities = list(pool.map(activity_worker, range(2)))
        assert set(activities) == {7, "conflict"}
        with Session(engine) as session:
            saved = session.get(Assessment, assessment_id)
            assert (saved.status.value, len(saved.observations)) in {
                ("in_progress", 1),
                ("evaluation", 0),
            }
            assert (
                session.scalar(
                    select(func.count())
                    .select_from(Assessment)
                    .where(Assessment.assessor_id == user_id)
                )
                == 1
            )
            user = session.get(User, user_id)
            if saved.status.value == "in_progress":
                saved = confirm_conversation(
                    session, user, assessment_id, saved.revision
                )
            saved = confirm_rating(
                session,
                user,
                assessment_id,
                REQUIRED_CRITERIA["C"][0],
                RatingConfirm(revision=saved.revision, score=3),
            )
            revision = saved.revision

        barrier = Barrier(2)

        def evaluation_worker(index):
            with Session(engine) as session:
                user = session.get(User, user_id)
                stale = session.get(Assessment, assessment_id)
                assert stale.ratings[0].score == 3
                barrier.wait(timeout=5)
                try:
                    if index == 0:
                        saved = save_answers(
                            session,
                            user,
                            assessment_id,
                            REQUIRED_CRITERIA["C"][0],
                            AnswersUpdate(
                                revision=revision,
                                answers=[
                                    {
                                        "indicator_id": indicator_id,
                                        "level": 4,
                                        "note": "Concurrent",
                                    }
                                ],
                            ),
                        )
                    else:
                        saved = confirm_rating(
                            session,
                            user,
                            assessment_id,
                            REQUIRED_CRITERIA["C"][0],
                            RatingConfirm(revision=revision, score=9),
                        )
                    return saved.revision
                except AssessmentError as error:
                    return error.code

        with ThreadPoolExecutor(max_workers=2) as pool:
            assert set(pool.map(evaluation_worker, range(2))) == {
                revision + 1,
                "conflict",
            }
        with Session(engine) as session:
            rating = session.get(Assessment, assessment_id).ratings[0]
            assert (rating.suggested_score, rating.score) in {(9, None), (None, 9)}
            user = session.get(User, user_id)
            for criterion_id in REQUIRED_CRITERIA["C"]:
                saved = session.get(Assessment, assessment_id)
                confirm_rating(
                    session,
                    user,
                    assessment_id,
                    criterion_id,
                    RatingConfirm(revision=saved.revision, score=5),
                )
            saved = save_summary(
                session,
                user,
                assessment_id,
                SummaryUpdate(
                    revision=saved.revision,
                    negative_justification="",
                    development_conclusions="",
                ),
            )
            revision = saved.revision

        barrier = Barrier(2)

        def completion_worker(index):
            with Session(engine) as session:
                user = session.get(User, user_id)
                stale = session.get(Assessment, assessment_id)
                assert all(rating.score == 5 for rating in stale.ratings)
                barrier.wait(timeout=5)
                try:
                    if index == 0:
                        saved = complete_assessment(
                            session, user, assessment_id, revision
                        )
                    else:
                        saved = save_answers(
                            session,
                            user,
                            assessment_id,
                            REQUIRED_CRITERIA["C"][0],
                            AnswersUpdate(
                                revision=revision,
                                answers=[
                                    {
                                        "indicator_id": indicator_id,
                                        "level": 0,
                                        "note": "Changed",
                                    }
                                ],
                            ),
                        )
                    return saved.revision
                except AssessmentError as error:
                    return error.code

        with ThreadPoolExecutor(max_workers=2) as pool:
            assert set(pool.map(completion_worker, range(2))) == {
                revision + 1,
                "conflict",
            }
        with Session(engine) as session:
            saved = session.get(Assessment, assessment_id)
            user = session.get(User, user_id)
            if saved.status.value == "completed":
                assert saved.result.outcome == "positive"
                assert all(rating.score == 5 for rating in saved.ratings)
            else:
                assert saved.result.outcome == "incomplete"
                saved = confirm_rating(
                    session,
                    user,
                    assessment_id,
                    REQUIRED_CRITERIA["C"][0],
                    RatingConfirm(revision=saved.revision, score=5),
                )
            revision = saved.revision

        barrier = Barrier(2)

        def retry_completion(_):
            with Session(engine) as session:
                user = session.get(User, user_id)
                stale = session.get(Assessment, assessment_id)
                assert stale.revision == revision
                barrier.wait(timeout=5)
                saved = complete_assessment(session, user, assessment_id, revision)
                return saved.revision, saved.summary.completed_at

        with ThreadPoolExecutor(max_workers=2) as pool:
            assert len(set(pool.map(retry_completion, range(2)))) == 1
    finally:
        with Session(engine) as session, session.begin():
            session.execute(delete(Assessment).where(Assessment.assessor_id == user_id))
            session.execute(
                delete(ManagerEmployeeAssignment).where(
                    ManagerEmployeeAssignment.manager_id == user_id
                )
            )
            session.execute(delete(Employee).where(Employee.id == employee_id))
            session.execute(
                delete(OrganizationalUnit).where(OrganizationalUnit.id == unit_id)
            )
            session.execute(
                delete(CatalogVersion).where(CatalogVersion.id == catalog_id)
            )
            session.execute(delete(UserRole).where(UserRole.user_id == user_id))
            session.execute(delete(User).where(User.id == user_id))
        engine.dispose()
