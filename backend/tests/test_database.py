import os
from pathlib import Path

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError
from sqlalchemy import text

from alembic import command
from app.core.config import Settings
from app.core.database import create_database_engine
from app.main import create_app


def test_readiness_without_database():
    with TestClient(create_app(Settings(database_url=None))) as client:
        assert client.get("/health").status_code == 200
        response = client.get("/api/v1/health")
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}


def test_readiness_connection_failure():
    settings = Settings(
        database_url="postgresql+psycopg://test:not-a-secret@127.0.0.1:1/unavailable"
    )
    with TestClient(create_app(settings)) as client:
        response = client.get("/api/v1/health")
        assert client.get("/health").status_code == 200
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
    assert "not-a-secret" not in response.text


@pytest.mark.parametrize(
    "url", ["sqlite:///test.db", "invalid", "postgresql://host/db"]
)
def test_database_url_validation(url):
    with pytest.raises(ValidationError):
        Settings(database_url=url)


@pytest.mark.integration
def test_postgresql_readiness_and_migrations(monkeypatch):
    url = os.environ.get("KOMPAS_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set KOMPAS_TEST_DATABASE_URL to a dedicated PostgreSQL database")
    settings = Settings(database_url=SecretStr(url))
    engine = create_database_engine(settings)
    # Only upgrade: never drop or downgrade a database supplied by the operator.
    monkeypatch.setenv("KOMPAS_DATABASE_URL", url)
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    try:
        command.upgrade(config, "head")
        command.upgrade(config, "head")
        command.check(config)
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT version_num FROM alembic_version"))
        with TestClient(create_app(settings)) as client:
            response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    finally:
        engine.dispose()
