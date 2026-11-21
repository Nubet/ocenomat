import io
import json
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec


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
