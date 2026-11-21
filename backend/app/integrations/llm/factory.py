from fastapi import HTTPException, Request

from app.core.config import Settings
from app.integrations.llm.openrouter import OpenRouterProvider
from app.integrations.llm.protocol import LLMProvider


def create_llm_provider(settings: Settings) -> LLMProvider | None:
    if settings.llm_api_key is None:
        return None
    return OpenRouterProvider(settings)


def get_llm_provider(request: Request) -> LLMProvider:
    provider = request.app.state.llm_provider
    if provider is None:
        raise HTTPException(status_code=503, detail="Language model is not configured")
    return provider
