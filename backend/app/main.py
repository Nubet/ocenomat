from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.database import create_database_engine, get_session
from app.core.security import TokenVerifier
from app.modules.assessments.router import router as assessments_router
from app.modules.catalog.router import router as catalog_router
from app.modules.employees.router import router as employees_router
from app.modules.users.router import router as users_router


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings if settings is not None else Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_database_engine(settings) if settings.database_url else None
        app.state.database_engine = engine
        app.state.token_verifier = (
            TokenVerifier(settings) if settings.supabase_url else None
        )
        try:
            yield
        finally:
            if engine is not None:
                engine.dispose()

    app = FastAPI(title="Kompas Kompetencji API", version="0.1.0", lifespan=lifespan)
    app.include_router(users_router)
    app.include_router(catalog_router)
    app.include_router(employees_router)
    app.include_router(assessments_router)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin).rstrip("/") for origin in settings.cors_origins],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
    )

    @app.get("/health", response_model=HealthResponse, tags=["health"])
    def health() -> HealthResponse:
        return HealthResponse()

    @app.get("/api/v1/health", response_model=HealthResponse, tags=["health"])
    def readiness(session: Annotated[Session, Depends(get_session)]) -> HealthResponse:
        try:
            session.execute(text("SELECT 1"))
        except SQLAlchemyError:
            raise HTTPException(
                status_code=503, detail="Database unavailable"
            ) from None
        return HealthResponse()

    return app
