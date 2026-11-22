from collections.abc import Sequence
from typing import Literal, Protocol, overload

from pydantic import BaseModel, ConfigDict, Field


class Message(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1, max_length=120_000)


class LLMError(Exception):
    def __init__(
        self,
        code: Literal[
            "not_configured",
            "unavailable",
            "timeout",
            "rate_limited",
            "unsupported_model",
            "invalid_response",
        ],
    ):
        self.code = code
        super().__init__(f"Language model: {code}")


class LLMProvider(Protocol):
    @overload
    def generate(
        self,
        messages: Sequence[Message],
        *,
        max_tokens: int | None = None,
        response_model: None = None,
    ) -> str: ...

    @overload
    def generate[T: BaseModel](
        self,
        messages: Sequence[Message],
        *,
        max_tokens: int | None = None,
        response_model: type[T],
    ) -> T: ...

    def generate(
        self,
        messages: Sequence[Message],
        *,
        max_tokens: int | None = None,
        response_model: type[BaseModel] | None = None,
    ) -> str | BaseModel: ...

    def close(self) -> None: ...
