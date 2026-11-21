import json
import time
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from fastapi import HTTPException
from fastapi.testclient import TestClient
from jwt.exceptions import PyJWKClientConnectionError
from pydantic import ValidationError

from app.core.config import Settings
from app.core.security import TokenVerifier
from app.main import create_app

ISSUER = "https://auth.example.org/auth/v1"


def claims(**changes):
    now = datetime.now(UTC)
    return {
        "iss": ISSUER,
        "aud": "authenticated",
        "iat": now,
        "exp": now + timedelta(minutes=5),
        "sub": str(uuid4()),
        **changes,
    }


def sign(key, payload=None, kid="key-1", algorithm="ES256"):
    return jwt.encode(
        claims() if payload is None else payload,
        key,
        algorithm=algorithm,
        headers={"kid": kid},
    )


@pytest.fixture
def verifier():
    return TokenVerifier(Settings(supabase_url="https://auth.example.org"))


def test_valid_signature_and_cached_jwks(verifier, key, jwks):
    payload = claims()
    token = sign(key, payload)
    assert str(verifier.verify(token)) == payload["sub"]
    verifier.verify(token)
    assert jwks[1] == [ISSUER + "/.well-known/jwks.json"]


@pytest.mark.parametrize(
    "changes",
    [
        {"exp": datetime.now(UTC) - timedelta(seconds=1)},
        {"iss": "https://other.example.org"},
        {"aud": "other"},
        {"sub": "not-a-uuid"},
        {"iat": datetime.now(UTC) + timedelta(minutes=5)},
        {"nbf": datetime.now(UTC) + timedelta(minutes=5)},
    ],
)
def test_invalid_claims(verifier, key, jwks, changes):
    with pytest.raises(HTTPException) as error:
        verifier.verify(sign(key, claims(**changes)))
    assert error.value.status_code == 401


@pytest.mark.parametrize("missing", ["exp", "iat", "iss", "aud", "sub"])
def test_required_claims(verifier, key, jwks, missing):
    payload = claims()
    del payload[missing]
    with pytest.raises(HTTPException) as error:
        verifier.verify(sign(key, payload))
    assert error.value.status_code == 401


def test_forged_signature(verifier, key, jwks):
    forged_key = ec.generate_private_key(ec.SECP256R1())
    with pytest.raises(HTTPException) as error:
        verifier.verify(sign(forged_key))
    assert error.value.status_code == 401


@pytest.mark.parametrize("algorithm", ["HS256", "none"])
def test_reject_algorithm_before_fetching_keys(verifier, algorithm, jwks):
    token = sign("x" * 32 if algorithm == "HS256" else None, algorithm=algorithm)
    with pytest.raises(HTTPException) as error:
        verifier.verify(token)
    assert error.value.status_code == 401
    assert jwks[1] == []


def test_rotation_refreshes_unknown_kid(verifier, key, jwks, monkeypatch):
    verifier.verify(sign(key))
    new_key = ec.generate_private_key(ec.SECP256R1())
    public = json.loads(jwt.algorithms.ECAlgorithm.to_jwk(new_key.public_key()))
    jwks[0]["keys"] = [{**public, "kid": "key-2", "alg": "ES256"}]
    after_cooldown = time.monotonic() + 31
    monkeypatch.setattr("jwt.jwks_client.time.monotonic", lambda: after_cooldown)
    assert verifier.verify(sign(new_key, kid="key-2"))
    assert len(jwks[1]) == 2
    with pytest.raises(HTTPException) as error:
        verifier.verify(sign(key, kid="missing-key"))
    assert error.value.status_code == 401


def test_jwks_failure_is_closed(verifier, key, monkeypatch):
    def unavailable(*args, **kwargs):
        raise PyJWKClientConnectionError("simulated unavailable JWKS")

    monkeypatch.setattr(verifier.jwks, "get_signing_key", unavailable)
    with pytest.raises(HTTPException) as error:
        verifier.verify(sign(key))
    assert error.value.status_code == 503
    assert "simulated" not in error.value.detail


def test_empty_jwks_is_unavailable(verifier, key, jwks):
    jwks[0]["keys"] = []
    with pytest.raises(HTTPException) as error:
        verifier.verify(sign(key))
    assert error.value.status_code == 503


def test_rsa_project(monkeypatch):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key()))
    jwk = jwt.PyJWK.from_dict({**public, "kid": "key-1", "alg": "RS256"})
    verifier = TokenVerifier(
        Settings(supabase_url="https://auth.example.org", jwt_algorithm="RS256")
    )
    monkeypatch.setattr(verifier.jwks, "get_signing_key", lambda kid: jwk)
    assert verifier.verify(sign(key, algorithm="RS256"))


@pytest.mark.parametrize("token", ["malformed", "", "a.b.c"])
def test_malformed_token(verifier, token):
    with pytest.raises(HTTPException) as error:
        verifier.verify(token)
    assert error.value.status_code == 401


def test_missing_token_and_unconfigured_provider():
    with TestClient(create_app(Settings(supabase_url=None))) as client:
        response = client.get("/api/v1/me")
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"
        assert (
            client.get(
                "/api/v1/me", headers={"Authorization": "Bearer placeholder"}
            ).status_code
            == 503
        )


def test_empty_provider_environment_is_unconfigured(monkeypatch):
    monkeypatch.setenv("KOMPAS_SUPABASE_URL", "")
    assert Settings().supabase_url is None


@pytest.mark.parametrize(
    "url", ["http://auth.example.org", "https://auth.example.org/path"]
)
def test_provider_requires_https_origin(url):
    with pytest.raises(ValidationError):
        Settings(supabase_url=url)


def test_token_without_kid(verifier, key, jwks):
    token = jwt.encode(claims(), key, algorithm="ES256")
    with pytest.raises(HTTPException) as error:
        verifier.verify(token)
    assert error.value.status_code == 401
    assert jwks[1] == []
