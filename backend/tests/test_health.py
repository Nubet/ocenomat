import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main import create_app


def test_liveness():
    with TestClient(create_app(Settings())) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize(
    ("origin", "status"),
    [("http://localhost:3000", 200), ("https://untrusted.example", 400)],
)
def test_cors_preflight(origin, status):
    settings = Settings(cors_origins=["http://localhost:3000"])
    with TestClient(create_app(settings)) as client:
        response = client.options(
            "/health",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization",
            },
        )
    assert response.status_code == status
    assert response.headers.get("access-control-allow-origin") == (
        origin if status == 200 else None
    )
    assert "access-control-allow-credentials" not in response.headers


def test_cors_denied_by_default():
    with TestClient(create_app(Settings(cors_origins=[]))) as client:
        response = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.parametrize(
    "origin", ["*", "http://user:password@localhost", "https://example.org/path"]
)
def test_invalid_cors_origin(origin):
    with pytest.raises(ValidationError):
        Settings(cors_origins=[origin])


def test_settings_from_environment(monkeypatch):
    monkeypatch.setenv("KOMPAS_CORS_ORIGINS", '["http://localhost:3000"]')
    assert str(Settings().cors_origins[0]) == "http://localhost:3000/"
