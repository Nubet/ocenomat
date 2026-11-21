import json
import logging
from typing import Annotated

import httpx
import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict, ValidationError

from app.core.config import Settings
from app.integrations.llm.factory import create_llm_provider, get_llm_provider
from app.integrations.llm.openrouter import OpenRouterProvider
from app.integrations.llm.protocol import LLMError, LLMProvider, Message
from app.main import create_app

MODEL = "anthropic/claude-sonnet-5.5"
SECRET = "test-only-api-key"
PROMPT = "Poufny tekst testowy"
MESSAGES = [Message(role="user", content=PROMPT)]


class Answer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    source_ids: list[str]


def settings(**overrides):
    return Settings(
        **{
            "llm_model": MODEL,
            "llm_api_key": SECRET,
            **overrides,
        }
    )


def metadata():
    return {
        "data": {
            "id": MODEL,
            "endpoints": [
                {
                    "model_id": MODEL,
                    "status": 0,
                    "pricing": {"prompt": "0.000002", "completion": "0.00001"},
                    "max_completion_tokens": 8192,
                    "supported_parameters": [
                        "reasoning",
                        "max_tokens",
                        "response_format",
                        "structured_outputs",
                    ],
                }
            ],
        }
    }


def completion(content="Odpowiedź", **overrides):
    return {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {"content": content},
                **overrides,
            }
        ]
    }


@pytest.fixture
def provider():
    requests = []
    responses = [metadata(), completion()]

    def handler(request):
        requests.append(request)
        result = responses.pop(0)
        if isinstance(result, Exception):
            raise result
        if isinstance(result, httpx.Response):
            return result
        return httpx.Response(200, json=result)

    instance = OpenRouterProvider(settings(), transport=httpx.MockTransport(handler))
    yield instance, responses, requests
    instance.close()


def test_text_and_structured_generation_with_cached_capabilities(provider):
    instance, responses, requests = provider
    llm: LLMProvider = instance
    assert llm.generate(MESSAGES) == "Odpowiedź"
    responses.append(completion('{"text":"Zażółć gęślą jaźń", "source_ids":["a"]}'))
    answer = llm.generate(MESSAGES, max_tokens=100, response_model=Answer)
    assert answer == Answer(text="Zażółć gęślą jaźń", source_ids=["a"])
    assert len(requests) == 3
    assert requests[0].url.path == f"/api/v1/models/{MODEL}/endpoints"
    request = requests[-1]
    assert request.url.path == "/api/v1/chat/completions"
    assert request.headers["authorization"] == f"Bearer {SECRET}"
    body = json.loads(request.content)
    assert body["model"] == MODEL
    assert body["messages"] == [{"role": "user", "content": PROMPT}]
    assert body["max_tokens"] == 100
    assert body["stream"] is False
    assert body["provider"] == {
        "allow_fallbacks": True,
        "require_parameters": True,
        "sort": "latency",
        "data_collection": "deny",
    }
    assert (
        body["response_format"]["json_schema"]["schema"] == Answer.model_json_schema()
    )
    assert body["response_format"]["json_schema"]["strict"] is True
    assert body["reasoning"] == {"effort": "medium", "exclude": True}
    assert "models" not in body
    assert requests[0].extensions["timeout"]["read"] == 60


@pytest.mark.parametrize(
    "content",
    [
        "not json",
        '{"text":"ok"}',
        '{"text":5,"source_ids":[]}',
        '{"text":"ok","source_ids":[],"extra":true}',
    ],
)
def test_invalid_structured_answer(provider, content):
    instance, responses, _ = provider
    responses[-1] = completion(content)
    with pytest.raises(LLMError, match="invalid_response"):
        instance.generate(MESSAGES, response_model=Answer)


@pytest.mark.parametrize(
    "result",
    [
        {},
        [],
        {"error": {"message": SECRET}},
        completion(""),
        completion("   "),
        completion(finish_reason="length"),
        completion(finish_reason="content_filter"),
        completion(message={"content": "refused", "refusal": "refused"}),
        completion(message={"content": None}),
        httpx.Response(200, content=b"invalid json"),
        httpx.Response(200, content=b"x" * (1024 * 1024 + 1)),
    ],
)
def test_invalid_or_incomplete_response(provider, result):
    instance, responses, _ = provider
    responses[-1] = result
    with pytest.raises(LLMError, match="invalid_response"):
        instance.generate(MESSAGES)


@pytest.mark.parametrize(
    ("response", "code"),
    [
        (httpx.Response(400), "unsupported_model"),
        (httpx.Response(404), "unsupported_model"),
        (httpx.Response(401), "unavailable"),
        (httpx.Response(402), "unavailable"),
        (httpx.Response(429), "rate_limited"),
        (httpx.Response(503), "unavailable"),
        (
            httpx.Response(302, headers={"Location": "https://other.example"}),
            "unavailable",
        ),
        (httpx.ReadTimeout(SECRET), "timeout"),
        (httpx.ConnectError(SECRET), "unavailable"),
    ],
)
def test_controlled_errors_without_retries_or_secret_leaks(
    provider, response, code, caplog
):
    instance, responses, requests = provider
    responses[-1] = response
    with caplog.at_level(logging.DEBUG), pytest.raises(LLMError) as error:
        instance.generate(MESSAGES)
    assert error.value.code == code
    assert SECRET not in str(error.value) + caplog.text
    assert PROMPT not in str(error.value) + caplog.text
    assert len(requests) == 2


@pytest.mark.parametrize(
    "change",
    [
        {"status": 1},
        {"model_id": "other/model:free"},
        {"supported_parameters": ["max_tokens", "response_format"]},
        {"max_completion_tokens": 1},
    ],
)
def test_unsupported_endpoint_blocks_generation(provider, change):
    instance, responses, requests = provider
    responses[0]["data"]["endpoints"][0].update(change)
    with pytest.raises(LLMError, match="unsupported_model"):
        instance.generate(MESSAGES, response_model=Answer)
    assert len(requests) == 1


def test_text_does_not_require_schema_support(provider):
    instance, responses, _ = provider
    responses[0]["data"]["endpoints"][0]["supported_parameters"] = [
        "max_tokens",
        "reasoning",
    ]
    assert instance.generate(MESSAGES) == "Odpowiedź"


def test_presentation_defaults_and_models_without_reasoning():
    config = Settings()
    assert config.llm_model == MODEL
    assert config.llm_max_tokens == 8192
    assert config.llm_reasoning_effort == "medium"
    requests = []

    def handler(request):
        requests.append(request)
        if request.method == "GET":
            data = metadata()
            data["data"]["endpoints"][0]["supported_parameters"] = ["max_tokens"]
            return httpx.Response(200, json=data)
        return httpx.Response(200, json=completion())

    instance = OpenRouterProvider(
        settings(llm_reasoning_effort=None), transport=httpx.MockTransport(handler)
    )
    try:
        assert instance.generate(MESSAGES) == "Odpowiedź"
        body = json.loads(requests[-1].content)
        assert body["max_tokens"] == 8192
        assert "reasoning" not in body
    finally:
        instance.close()


@pytest.mark.parametrize(
    "data",
    [
        {},
        {"data": {}},
        {
            "data": {
                "id": MODEL,
                "endpoints": [
                    {
                        "model_id": MODEL,
                        "supported_parameters": [],
                    },
                ],
            }
        },
    ],
)
def test_bad_capability_metadata(provider, data):
    instance, responses, requests = provider
    responses[0] = data
    with pytest.raises(LLMError, match="invalid_response"):
        instance.generate(MESSAGES)
    assert len(requests) == 1


@pytest.mark.parametrize("limit", [0, -1, True, 8193])
def test_token_limit_checked_before_network(provider, limit):
    instance, _, requests = provider
    with pytest.raises(ValueError):
        instance.generate(MESSAGES, max_tokens=limit)
    assert not requests


@pytest.mark.parametrize(
    "messages",
    [
        [],
        MESSAGES * 33,
        [
            Message(role="user", content="x" * 30_000),
            Message(role="user", content="x" * 30_000),
        ],
    ],
)
def test_context_limit_checked_before_network(provider, messages):
    instance, _, requests = provider
    with pytest.raises(ValueError):
        instance.generate(messages)
    assert not requests


@pytest.mark.parametrize(
    "overrides",
    [
        {"llm_api_key": None},
        {"llm_api_key": " "},
    ],
)
def test_missing_configuration(overrides):
    with pytest.raises(LLMError, match="not_configured"):
        OpenRouterProvider(settings(**overrides))


@pytest.mark.parametrize(
    "overrides",
    [
        {"llm_model": "model-without-provider"},
        {"llm_model": "openrouter/auto"},
        {"llm_model": "openrouter/free"},
        {"llm_base_url": "http://example.org"},
        {"llm_base_url": "https://user:secret@example.org"},
        {"llm_base_url": "https://example.org/?key=secret"},
        {"llm_timeout_seconds": 0},
        {"llm_max_tokens": 0},
        {"llm_provider": "other"},
    ],
)
def test_invalid_configuration(overrides):
    with pytest.raises(ValidationError):
        settings(**overrides)


def test_secret_is_redacted_and_settings_use_environment(monkeypatch):
    monkeypatch.setenv("KOMPAS_LLM_API_KEY", SECRET)
    monkeypatch.setenv("KOMPAS_LLM_MODEL", MODEL)
    config = Settings()
    assert config.llm_model == MODEL
    assert SECRET not in str(config)


def test_dependency_can_be_replaced_without_network():
    class FakeProvider:
        closed = False

        def generate(self, messages, **kwargs):
            assert messages == MESSAGES
            return "Test bez sieci"

        def close(self):
            self.closed = True

    fake = FakeProvider()
    app = create_app(Settings())

    @app.get("/test-llm")
    def test_endpoint(provider: Annotated[LLMProvider, Depends(get_llm_provider)]):
        return {"answer": provider.generate(MESSAGES)}

    with TestClient(app) as client:
        assert app.state.llm_provider is None
        assert client.get("/test-llm").status_code == 503
        app.dependency_overrides[get_llm_provider] = lambda: fake
        assert client.get("/test-llm").json() == {"answer": "Test bez sieci"}
    assert create_llm_provider(Settings()) is None


def test_provider_lifecycle_without_network(monkeypatch):
    class FakeProvider:
        closed = False

        def close(self):
            self.closed = True

    fake = FakeProvider()
    monkeypatch.setattr("app.main.create_llm_provider", lambda _: fake)
    app = create_app(Settings())
    with TestClient(app):
        assert app.state.llm_provider is fake
        assert not fake.closed
    assert fake.closed
