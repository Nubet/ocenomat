from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from jwt.exceptions import PyJWKClientConnectionError, PyJWKClientError

from app.core.config import Settings

bearer = HTTPBearer(auto_error=False)


def unauthorized() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail="Invalid or missing access token",
        headers={"WWW-Authenticate": "Bearer"},
    )


class TokenVerifier:
    def __init__(self, settings: Settings):
        if settings.supabase_url is None:
            raise ValueError("KOMPAS_SUPABASE_URL is required")
        self.issuer = str(settings.supabase_url).rstrip("/") + "/auth/v1"
        self.algorithm = settings.jwt_algorithm
        self.jwks = PyJWKClient(
            self.issuer + "/.well-known/jwks.json",
            cache_keys=False,
            lifespan=300,
            timeout=5,
        )

    def verify(self, token: str) -> UUID:
        try:
            header = jwt.get_unverified_header(token)
            if (
                header.get("alg") != self.algorithm
                or not isinstance(header.get("kid"), str)
                or not header["kid"]
            ):
                raise unauthorized()
            key = self.jwks.get_signing_key(header["kid"])
            if key.algorithm_name != self.algorithm:
                raise unauthorized()
            claims = jwt.decode(
                token,
                key.key,
                algorithms=[self.algorithm],
                issuer=self.issuer,
                audience="authenticated",
                options={"require": ["exp", "iat", "iss", "aud", "sub"]},
            )
            return UUID(claims["sub"])
        except PyJWKClientConnectionError:
            raise HTTPException(
                status_code=503, detail="Identity verification unavailable"
            ) from None
        except (jwt.InvalidTokenError, PyJWKClientError, ValueError, TypeError):
            raise unauthorized() from None


def get_subject(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> UUID:
    if credentials is None:
        raise unauthorized()
    verifier = request.app.state.token_verifier
    if verifier is None:
        raise HTTPException(status_code=503, detail="Identity verification unavailable")
    return verifier.verify(credentials.credentials)
