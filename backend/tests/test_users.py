import os
from pathlib import Path
from uuid import uuid4

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy.orm import Session
from test_security import claims, sign

from alembic import command
from app.core.config import Settings
from app.core.database import create_database_engine, get_session
from app.main import create_app
from app.modules.users.bootstrap import bootstrap_admin
from app.modules.users.models import Role, User, UserRole

pytestmark = pytest.mark.integration


@pytest.fixture
def database(monkeypatch):
    url = os.environ.get("KOMPAS_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires a dedicated PostgreSQL test database")
    monkeypatch.setenv("KOMPAS_DATABASE_URL", url)
    command.upgrade(Config(str(Path(__file__).parents[1] / "alembic.ini")), "head")
    settings = Settings(
        database_url=SecretStr(url), supabase_url="https://auth.example.org"
    )
    engine = create_database_engine(settings)
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            with Session(
                bind=connection, join_transaction_mode="create_savepoint"
            ) as session:
                yield settings, connection, session
        finally:
            transaction.rollback()
    engine.dispose()


@pytest.mark.parametrize(
    "active,exists,status", [(True, True, 200), (False, True, 401), (True, False, 401)]
)
def test_me_uses_database_identity(database, key, jwks, active, exists, status):
    settings, connection, session = database
    subject = uuid4()
    if exists:
        user = User(
            auth_subject=subject,
            display_name="Test Manager",
            active=active,
            roles=[UserRole(role=Role.MANAGER), UserRole(role=Role.HR)],
        )
        session.add(user)
        session.commit()
        user_id = str(user.id)
    app = create_app(settings)

    def override_session():
        with Session(bind=connection, join_transaction_mode="create_savepoint") as db:
            yield db

    app.dependency_overrides[get_session] = override_session
    token = sign(
        key, claims(sub=str(subject), role="ADMIN", email="untrusted@example.org")
    )
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/me", headers={"Authorization": f"Bearer {token}"}
        )
    assert response.status_code == status
    if status == 200:
        assert response.json() == {
            "id": user_id,
            "display_name": "Test Manager",
            "roles": ["HR", "MANAGER"],
        }
    else:
        assert response.json() == {"detail": "Invalid or missing access token"}


def test_bootstrap_creates_only_first_admin(database):
    _, _, session = database
    subject = uuid4()
    user = bootstrap_admin(session, subject, "  Test Admin  ")
    assert user.auth_subject == subject
    assert user.display_name == "Test Admin"
    assert [r.role for r in user.roles] == [Role.ADMIN]
    session.rollback()
    with pytest.raises(ValueError, match="already exists"):
        bootstrap_admin(session, uuid4(), "Second admin")


def test_bootstrap_rejects_blank_name(database):
    with pytest.raises(ValueError, match="Display name"):
        bootstrap_admin(database[2], uuid4(), " ")
