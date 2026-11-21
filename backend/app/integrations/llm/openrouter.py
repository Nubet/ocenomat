import json
from collections.abc import Sequence
from threading import Lock
from typing import Literal

import httpx
from pydantic import BaseModel, Field, ValidationError

from app.core.config import Settings
from app.integrations.llm.protocol import LLMError, Message


class Endpoint(BaseModel):
    model_id: str
    status: int
    supported_parameters: list[str]
    max_completion_tokens: int | None = None


class ModelEndpoints(BaseModel):
    id: str
    endpoints: list[Endpoint]


class CompletionMessage(BaseModel):
    content: str = Field(min_length=1)
    refusal: str | None = None


class Choice(BaseModel):
    finish_reason: Literal["stop"]
    message: CompletionMessage


class Completion(BaseModel):
    choices: list[Choice] = Field(min_length=1, max_length=1)


class OpenRouterProvider:
    def __init__(
        self, settings: Settings, *, transport: httpx.BaseTransport | None = None
    ):
        if not settings.llm_model or not settings.llm_api_key:
            raise LLMError("not_configured")
        key = settings.llm_api_key.get_secret_value()
        if not key.strip():
            raise LLMError("not_configured")
        self.model = settings.llm_model
        self.max_tokens = settings.llm_max_tokens
        self.reasoning_effort = settings.llm_reasoning_effort
        self.client = httpx.Client(
            base_url=str(settings.llm_base_url).rstrip("/") + "/",
            headers={"Authorization": f"Bearer {key}"},
            timeout=settings.llm_timeout_seconds,
            follow_redirects=False,
            trust_env=False,
            transport=transport,
        )
        self._endpoints: list[Endpoint] | None = None
        self._lock = Lock()

    def _request(self, method: str, path: str, body: dict | None = None) -> dict:
        try:
            with self.client.stream(method, path, json=body) as response:
                if response.status_code == 429:
                    raise LLMError("rate_limited")
                if response.status_code in (400, 404, 422):
                    raise LLMError("unsupported_model")
                if not response.is_success:
                    raise LLMError("unavailable")
                content = bytearray()
                for chunk in response.iter_bytes():
                    if len(content) + len(chunk) > 1024 * 1024:
                        raise LLMError("invalid_response")
                    content.extend(chunk)
                data = json.loads(content)
                if not isinstance(data, dict) or "error" in data:
                    raise LLMError("invalid_response")
                return data
        except httpx.TimeoutException:
            raise LLMError("timeout") from None
        except httpx.HTTPError:
            raise LLMError("unavailable") from None
        except ValueError:
            raise LLMError("invalid_response") from None

    def _check_model(self, *, structured: bool, max_tokens: int) -> None:
        with self._lock:
            if self._endpoints is None:
                data = self._request("GET", f"models/{self.model}/endpoints")
                try:
                    model = ModelEndpoints.model_validate(data.get("data"))
                except ValidationError:
                    raise LLMError("invalid_response") from None
                if model.id != self.model:
                    raise LLMError("unsupported_model")
                self._endpoints = model.endpoints
        required = {"max_tokens"}
        if self.reasoning_effort is not None:
            required.add("reasoning")
        if structured:
            required.update(("response_format", "structured_outputs"))
        if not any(
            endpoint.model_id == self.model
            and endpoint.status == 0
            and required.issubset(endpoint.supported_parameters)
            and (
                endpoint.max_completion_tokens is None
                or max_tokens <= endpoint.max_completion_tokens
            )
            for endpoint in self._endpoints
        ):
            raise LLMError("unsupported_model")

    def generate[T: BaseModel](
        self,
        messages: Sequence[Message],
        *,
        max_tokens: int | None = None,
        response_model: type[T] | None = None,
    ) -> str | T:
        tokens = self.max_tokens if max_tokens is None else max_tokens
        if type(tokens) is not int or not 1 <= tokens <= self.max_tokens:
            raise ValueError("Invalid output token limit")
        if (
            not 1 <= len(messages) <= 32
            or sum(len(message.content) for message in messages) > 48_000
        ):
            raise ValueError("Message context exceeds limits")
        self._check_model(structured=response_model is not None, max_tokens=tokens)
        body = {
            "model": self.model,
            "messages": [message.model_dump() for message in messages],
            "max_tokens": tokens,
            "stream": False,
            "provider": {
                "allow_fallbacks": True,
                "require_parameters": True,
                "sort": "latency",
                "data_collection": "deny",
            },
        }
        if self.reasoning_effort is not None:
            body["reasoning"] = {"effort": self.reasoning_effort, "exclude": True}
        if response_model is not None:
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": response_model.__name__,
                    "strict": True,
                    "schema": response_model.model_json_schema(),
                },
            }
        data = self._request("POST", "chat/completions", body)
        try:
            message = Completion.model_validate(data).choices[0].message
            if message.refusal or not message.content.strip():
                raise LLMError("invalid_response")
            if response_model is None:
                return message.content
            return response_model.model_validate_json(message.content, strict=True)
        except ValidationError:
            raise LLMError("invalid_response") from None

    def close(self) -> None:
        self.client.close()
