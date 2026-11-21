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
from app.modules.employees.seed import seed_fictional_employees
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
    assert response.status_code == 200 and len(response.json()) == count


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
    assert [row["id"] for row in response.json()] == [
        str(people[index].id) for index in indices
    ]
    assert response.headers["cache-control"] == "private, no-store"
    for row in response.json():
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
    assert len(client.get("/api/v1/employees?q=anna", headers=auth).json()) == 1
    for q in ["Beata", "%", "_", "\\"]:
        response = client.get("/api/v1/employees", params={"q": q}, headers=auth)
        assert response.status_code == 200 and response.json() == []
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
    assert client.get("/api/v1/employees", headers=auth).json() == []
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


def test_assignment_foreign_keys_are_enforced(database):
    session = database[2]
    session.add(ManagerEmployeeAssignment(manager_id=uuid4(), employee_id=uuid4()))
    with pytest.raises(IntegrityError):
        session.flush()
