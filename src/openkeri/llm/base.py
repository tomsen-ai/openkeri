from typing import Any, Literal, Protocol

from pydantic import BaseModel


class LLMMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class LLMClient(Protocol):
    def complete_json(self, messages: list[LLMMessage]) -> dict[str, Any]:
        """Return a JSON-compatible object from chat messages."""
        ...
