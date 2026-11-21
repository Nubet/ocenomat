import io
import json
import os
from pathlib import Path
from types import SimpleNamespace

import jwt
import pytest
from alembic.config import Config
from cryptography.hazmat.primitives.asymmetric import ec
from pydantic import SecretStr
from sqlalchemy.orm import Session

from alembic import command
from app.core.config import Settings
from app.core.database import create_database_engine


@pytest.fixture
def key():
    return ec.generate_private_key(ec.SECP256R1())


@pytest.fixture
def jwks(monkeypatch, key):
    public = json.loads(jwt.algorithms.ECAlgorithm.to_jwk(key.public_key()))
    state = {"keys": [{**public, "kid": "key-1", "alg": "ES256", "use": "sig"}]}
    calls = []

    def urlopen(request, **kwargs):
        calls.append(request.full_url)
        return io.BytesIO(json.dumps(state).encode())

    monkeypatch.setattr(
        "jwt.jwks_client.urllib.request.build_opener",
        lambda *handlers: SimpleNamespace(open=urlopen),
    )
    return state, calls


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
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                with Session(
                    bind=connection, join_transaction_mode="create_savepoint"
                ) as session:
                    yield settings, connection, session
            finally:
                transaction.rollback()
    finally:
        engine.dispose()
