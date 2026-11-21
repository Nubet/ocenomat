from collections.abc import Iterator

from fastapi import HTTPException, Request
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session

from app.core.config import Settings


class Base(DeclarativeBase):
    pass


def create_database_engine(settings: Settings) -> Engine:
    if settings.database_url is None:
        raise ValueError("KOMPAS_DATABASE_URL is required")
    return create_engine(
        settings.database_url.get_secret_value(),
        pool_pre_ping=True,
        pool_timeout=5,
        connect_args={"connect_timeout": 3, "options": "-c statement_timeout=5000"},
        hide_parameters=True,
    )


def get_session(request: Request) -> Iterator[Session]:
    engine = request.app.state.database_engine
    if engine is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    with Session(engine) as session:
        yield session
