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
from app.integrations.llm.factory import create_llm_provider
from app.integrations.storage import ObjectStorage
from app.modules.ai.router import router as ai_router
from app.modules.assessments.router import router as assessments_router
from app.modules.catalog.router import router as catalog_router
from app.modules.documents.router import router as documents_router
from app.modules.employees.router import router as employees_router
from app.modules.knowledge.router import router as knowledge_router
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
        storage = (
            ObjectStorage(settings)
            if all(
                (
                    settings.storage_endpoint,
                    settings.storage_access_key,
                    settings.storage_secret_key,
                )
            )
            else None
        )
        app.state.object_storage = storage
        app.state.pdf_font_path = settings.pdf_font_path
        llm = create_llm_provider(settings)
        app.state.llm_provider = llm
        try:
            yield
        finally:
            if llm is not None:
                llm.close()
            if engine is not None:
                engine.dispose()
            if storage is not None:
                storage.close()

    app = FastAPI(title="Kompas Kompetencji API", version="0.1.0", lifespan=lifespan)
    app.include_router(users_router)
    app.include_router(catalog_router)
    app.include_router(employees_router)
    app.include_router(assessments_router)
    app.include_router(documents_router)
    app.include_router(ai_router)
    app.include_router(knowledge_router)
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
