import time
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from test_security import claims, sign

from app.core.database import get_session
from app.main import create_app
from app.modules.employees.models import (
    Employee,
    ManagerEmployeeAssignment,
    OrganizationalUnit,
    PositionKind,
)
from app.modules.employees.seed import UNIT_NAME, seed_fictional_employees
from app.modules.users.models import Role, User, UserRole

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    "name,count", [("a", 1), ("mixed", 0), ("hr", 0), ("admin", 0)]
)
def test_assessment_choices_require_assignments_even_with_broad_roles(
    employee_access, name, count
):
    client, users, _, key = employee_access
    response = client.get(
        "/api/v1/employees?assigned_only=true", headers=headers(users[name], key)
    )
    assert response.status_code == 200 and response.json()["total"] == count


@pytest.fixture
def employee_access(database, key, jwks):
    settings, connection, session = database
    users = {}
    for name, roles in {
        "a": [Role.MANAGER],
        "b": [Role.MANAGER],
        "empty": [Role.MANAGER],
        "hr": [Role.HR],
        "admin": [Role.ADMIN],
        "none": [],
        "mixed": [Role.MANAGER, Role.HR],
    }.items():
        users[name] = User(
            auth_subject=uuid4(),
            display_name=name,
            roles=[UserRole(role=role) for role in roles],
        )
    unit = OrganizationalUnit(name="Fictional unit")
    session.add_all([unit, *users.values()])
    session.flush()
    people = [
        Employee(
            name=name,
            position="Test specialist",
            position_kind=PositionKind.OTHER,
            unit_id=unit.id,
        )
        for name in ["Anna Testowa", "Beata Testowa", "Celina Bez Przypisania"]
    ]
    session.add_all(people)
    session.flush()
    session.add_all(
        [
            ManagerEmployeeAssignment(
                manager_id=users[name].id, employee_id=people[index].id
            )
            for index, name in enumerate(["a", "b"])
        ]
    )
    session.commit()
    app = create_app(settings)

    def override_session():
        with Session(bind=connection, join_transaction_mode="create_savepoint") as db:
            yield db

    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as client:
        yield client, users, people, key


def headers(user, key, **overrides):
    return {
        "Authorization": "Bearer "
        + sign(key, claims(sub=str(user.auth_subject), **overrides))
    }


@pytest.mark.parametrize(
    "name,indices",
    [
        ("a", [0]),
        ("b", [1]),
        ("empty", []),
        ("hr", [0, 1, 2]),
        ("admin", [0, 1, 2]),
        ("none", []),
        ("mixed", [0, 1, 2]),
    ],
)
def test_list_is_filtered_in_database(employee_access, name, indices):
    client, users, people, key = employee_access
    response = client.get("/api/v1/employees", headers=headers(users[name], key))
    assert response.status_code == 200
    assert response.json()["total"] == len(indices)
    assert [row["id"] for row in response.json()["items"]] == [
        str(people[index].id) for index in indices
    ]
    assert response.headers["cache-control"] == "private, no-store"
    for row in response.json()["items"]:
        assert set(row) == {"id", "name", "position", "position_kind", "department"}


@pytest.mark.parametrize(
    "name,allowed",
    [
        ("a", True),
        ("b", False),
        ("empty", False),
        ("hr", True),
        ("admin", True),
        ("none", False),
    ],
)
def test_detail_checks_resource_assignment(employee_access, name, allowed):
    client, users, people, key = employee_access
    response = client.get(
        f"/api/v1/employees/{people[0].id}", headers=headers(users[name], key)
    )
    assert response.status_code == (200 if allowed else 404)
    if not allowed:
        missing = client.get(
            f"/api/v1/employees/{uuid4()}", headers=headers(users[name], key)
        )
        assert response.json() == missing.json() == {"detail": "Employee not found"}


def test_search_does_not_leak_and_treats_wildcards_literally(employee_access):
    client, users, people, key = employee_access
    auth = headers(users["a"], key)
    assert client.get("/api/v1/employees?q=anna", headers=auth).json()["total"] == 1
    for q in ["Beata", "%", "_", "\\"]:
        response = client.get("/api/v1/employees", params={"q": q}, headers=auth)
        assert response.status_code == 200 and response.json()["items"] == []
    assert (
        client.get(
            "/api/v1/employees", params={"q": "x" * 101}, headers=auth
        ).status_code
        == 422
    )


@pytest.mark.parametrize(
    "path",
    ["/api/v1/employees", "/api/v1/employees/00000000-0000-0000-0000-000000000001"],
)
def test_missing_and_expired_sessions_are_rejected(employee_access, path):
    client, users, _, key = employee_access
    assert client.get(path).status_code == 401
    assert (
        client.get(
            path, headers=headers(users["a"], key, exp=int(time.time()) - 60)
        ).status_code
        == 401
    )


def test_jwt_role_cannot_grant_access(employee_access):
    client, users, people, key = employee_access
    auth = headers(users["none"], key, role="ADMIN")
    assert client.get("/api/v1/employees", headers=auth).json()["total"] == 0
    assert (
        client.get(f"/api/v1/employees/{people[0].id}", headers=auth).status_code == 404
    )


def test_seed_is_explicit_repeatable_and_preserves_existing_records(database):
    _, _, session = database
    subject = uuid4()
    manager = User(
        auth_subject=subject,
        display_name="Seed manager",
        roles=[UserRole(role=Role.MANAGER)],
    )
    session.add(manager)
    session.commit()
    seed_fictional_employees(session, subject)
    session.rollback()
    seed_fictional_employees(session, subject)
    assert session.scalar(select(func.count()).select_from(Employee)) == 4
    assert (
        session.scalar(select(func.count()).select_from(ManagerEmployeeAssignment)) == 3
    )
    employee = session.scalar(select(Employee))
    employee.name = "Changed by operator"
    session.commit()
    seed_fictional_employees(session, subject)
    assert session.get(Employee, employee.id).name == "Changed by operator"
    unit = session.scalar(select(OrganizationalUnit))
    assert unit.name == UNIT_NAME
    unit.name = "Jednostka testowa — dane fikcyjne"
    session.commit()
    seed_fictional_employees(session, subject)
    assert unit.name == UNIT_NAME
    unit.name = "Departament zmieniony przez operatora"
    session.commit()
    seed_fictional_employees(session, subject)
    assert unit.name == "Departament zmieniony przez operatora"


def test_seed_rejects_unknown_or_wrong_role_without_partial_data(database):
    _, _, session = database
    with pytest.raises(ValueError, match="MANAGER"):
        seed_fictional_employees(session, uuid4())
    subject = uuid4()
    admin = User(
        auth_subject=subject, display_name="Admin", roles=[UserRole(role=Role.ADMIN)]
    )
    session.add(admin)
    session.commit()
    with pytest.raises(ValueError, match="MANAGER"):
        seed_fictional_employees(session, subject)
    assert session.scalar(select(func.count()).select_from(Employee)) == 0


def test_pagination_counts_only_visible_matches_and_clamps_pages(employee_access):
    client, users, people, key = employee_access
    auth = headers(users["hr"], key)
    pages = [
        client.get(
            "/api/v1/employees",
            headers=auth,
            params={
                "page_size": 1,
                "page": page,
                "sort": "name_desc",
            },
        ).json()
        for page in range(1, 4)
    ]
    assert [page["items"][0]["id"] for page in pages] == [
        str(person.id) for person in reversed(people)
    ]
    assert all(page["total"] == page["total_pages"] == 3 for page in pages)
    assert [page["page"] for page in pages] == [1, 2, 3]
    assert (
        client.get("/api/v1/employees?page_size=1&page=999", headers=auth).json()[
            "page"
        ]
        == 3
    )
    hidden = client.get(
        "/api/v1/employees?q=Beata&page=2&page_size=1", headers=headers(users["a"], key)
    ).json()
    assert hidden == {
        "items": [],
        "page": 1,
        "page_size": 1,
        "total": 0,
        "total_pages": 1,
    }


def test_name_position_search_and_kind_filter_are_combined(employee_access, database):
    client, users, people, key = employee_access
    session = database[2]
    people[0].name = "Żaneta Łącka"
    people[0].position = "Naczelnik wydziału"
    people[0].position_kind = PositionKind.DIRECT_MANAGER
    session.commit()
    auth = headers(users["hr"], key)
    for q in ["ŁĄCKA", "lacka zaneta", "naczelnik", "wydzialu zaneta"]:
        data = client.get(
            "/api/v1/employees",
            headers=auth,
            params={
                "q": q,
                "position_kind": "DIRECT_MANAGER",
                "page_size": 1,
            },
        ).json()
        assert data["total"] == 1 and data["items"][0]["id"] == str(people[0].id)
    data = client.get(
        "/api/v1/employees?q=naczelnik&position_kind=OTHER", headers=auth
    ).json()
    assert data["total"] == 0
    assert client.get("/api/v1/employees?sort=position_asc", headers=auth).json()[
        "items"
    ][0]["id"] == str(people[0].id)
    assert (
        client.get("/api/v1/employees?sort=department_desc", headers=auth).status_code
        == 200
    )
    data = client.get(
        "/api/v1/employees",
        headers=headers(users["mixed"], key),
        params={
            "assigned_only": "true",
            "employee_id": str(people[0].id),
        },
    ).json()
    assert data["total"] == 0


@pytest.mark.parametrize(
    "params",
    [
        {"page": 0},
        {"page": 1_000_001},
        {"page_size": 0},
        {"page_size": 101},
        {"sort": "name; DROP TABLE employees"},
        {"position_kind": "ADMIN"},
    ],
)
def test_invalid_directory_parameters_are_rejected(employee_access, params):
    client, users, _, key = employee_access
    assert (
        client.get(
            "/api/v1/employees", headers=headers(users["hr"], key), params=params
        ).status_code
        == 422
    )


def test_assignment_foreign_keys_are_enforced(database):
    session = database[2]
    session.add(ManagerEmployeeAssignment(manager_id=uuid4(), employee_id=uuid4()))
    with pytest.raises(IntegrityError):
        session.flush()
