import re
from typing import Literal

from pydantic import AnyHttpUrl, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="KOMPAS_",
        extra="ignore",
        env_ignore_empty=True,
        hide_input_in_errors=True,
    )

    cors_origins: list[AnyHttpUrl] = []
    database_url: SecretStr | None = None
    supabase_url: AnyHttpUrl | None = None
    jwt_algorithm: Literal["ES256", "RS256"] = "ES256"
    storage_endpoint: AnyHttpUrl | None = None
    storage_access_key: SecretStr | None = None
    storage_secret_key: SecretStr | None = None
    storage_bucket: str = "kompas-private"

    @field_validator("storage_endpoint")
    @classmethod
    def validate_storage_endpoint(cls, value: AnyHttpUrl | None) -> AnyHttpUrl | None:
        if value is not None and (
            value.username
            or value.password
            or value.path not in ("", "/")
            or value.query
            or value.fragment
        ):
            raise ValueError("Storage endpoint must be an HTTP(S) origin")
        return value

    @field_validator("storage_bucket")
    @classmethod
    def validate_storage_bucket(cls, value: str) -> str:
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,61}[a-z0-9]", value):
            raise ValueError(
                "Use a bucket name of 3–63 lowercase letters, digits or hyphens"
            )
        return value

    @field_validator("supabase_url")
    @classmethod
    def validate_supabase_url(cls, value: AnyHttpUrl | None) -> AnyHttpUrl | None:
        if value is not None and (
            value.scheme != "https"
            or value.username
            or value.password
            or value.path not in ("", "/")
            or value.query
            or value.fragment
        ):
            raise ValueError("Supabase URL must be an HTTPS origin")
        return value

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: SecretStr | None) -> SecretStr | None:
        if value is not None:
            try:
                url = make_url(value.get_secret_value())
            except ArgumentError:
                raise ValueError("Invalid PostgreSQL URL") from None
            if url.drivername != "postgresql+psycopg" or not url.database:
                raise ValueError("Use postgresql+psycopg with an explicit database")
        return value

    @field_validator("cors_origins")
    @classmethod
    def validate_origins(cls, origins: list[AnyHttpUrl]) -> list[AnyHttpUrl]:
        for origin in origins:
            if (
                origin.username
                or origin.password
                or origin.path not in ("", "/")
                or origin.query
                or origin.fragment
            ):
                raise ValueError("CORS origins must contain only scheme, host and port")
        return origins
