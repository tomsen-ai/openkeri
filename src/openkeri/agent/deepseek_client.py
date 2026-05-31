import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from openkeri.agent.llm_client import LLMMessage

DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-flash"
OPENKERI_DEEPSEEK_API_KEY = "OPENKERI_DEEPSEEK_API_KEY"
OPENKERI_DEEPSEEK_BASE_URL = "OPENKERI_DEEPSEEK_BASE_URL"
OPENKERI_DEEPSEEK_MODEL = "OPENKERI_DEEPSEEK_MODEL"


class DeepSeekClientError(RuntimeError):
    """Raised when DeepSeek cannot return a usable JSON object."""


@dataclass(frozen=True)
class DeepSeekClient:
    api_key: str
    model: str = DEFAULT_DEEPSEEK_MODEL
    base_url: str = DEFAULT_DEEPSEEK_BASE_URL
    timeout_seconds: float = 60.0
    max_tokens: int = 2048
    temperature: float = 0.2

    @classmethod
    def from_env(cls) -> "DeepSeekClient":
        api_key = os.environ.get(OPENKERI_DEEPSEEK_API_KEY, "").strip()
        if not api_key:
            raise ValueError(f"Set {OPENKERI_DEEPSEEK_API_KEY} to use DeepSeekClient.")

        model = os.environ.get(OPENKERI_DEEPSEEK_MODEL, DEFAULT_DEEPSEEK_MODEL).strip()
        base_url = os.environ.get(
            OPENKERI_DEEPSEEK_BASE_URL, DEFAULT_DEEPSEEK_BASE_URL
        ).strip()
        return cls(
            api_key=api_key,
            model=model or DEFAULT_DEEPSEEK_MODEL,
            base_url=base_url or DEFAULT_DEEPSEEK_BASE_URL,
        )

    def complete_json(self, messages: list[LLMMessage]) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": [message.model_dump(mode="json") for message in messages],
            "stream": False,
            "response_format": {"type": "json_object"},
            "thinking": {"type": "disabled"},
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        response = self._post_json(payload)
        content = self._extract_message_content(response)
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise DeepSeekClientError(
                "DeepSeek returned message content that is not valid JSON."
            ) from exc

        if not isinstance(parsed, dict):
            raise DeepSeekClientError("DeepSeek JSON content must be an object.")
        return parsed

    def _post_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            url=f"{self.base_url.rstrip('/')}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request, timeout=self.timeout_seconds
            ) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise DeepSeekClientError(
                f"DeepSeek API request failed with HTTP {exc.code}: {detail}"
            ) from exc
        except urllib.error.URLError as exc:
            raise DeepSeekClientError(
                f"DeepSeek API request failed: {exc.reason}"
            ) from exc

        try:
            parsed = json.loads(body)
        except json.JSONDecodeError as exc:
            raise DeepSeekClientError(
                "DeepSeek API returned a response body that is not valid JSON."
            ) from exc

        if not isinstance(parsed, dict):
            raise DeepSeekClientError("DeepSeek API response must be an object.")
        return parsed

    def _extract_message_content(self, response: dict[str, Any]) -> str:
        choices = response.get("choices")
        if not isinstance(choices, list) or not choices:
            raise DeepSeekClientError("DeepSeek API response has no choices.")

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise DeepSeekClientError("DeepSeek API choice must be an object.")

        if first_choice.get("finish_reason") == "length":
            raise DeepSeekClientError("DeepSeek response was truncated.")

        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise DeepSeekClientError("DeepSeek API choice has no message object.")

        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise DeepSeekClientError("DeepSeek API message content is empty.")
        return content
