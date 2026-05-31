import json
from typing import Any
from urllib.request import Request

import pytest

import openkeri.agent.deepseek_client as deepseek_client_module
from openkeri.agent import DeepSeekClient, DeepSeekClientError, LLMMessage


class FakeHTTPResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeHTTPResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def valid_teacher_output() -> dict[str, Any]:
    return {
        "diagnosis": {
            "status": "incorrect",
            "issue": "left_boundary_update_error",
            "concept": "sliding_window",
            "confidence": 0.84,
            "evidence_refs": ["ev_001"],
            "evidence_summary": "The code fails on input 'abba'.",
        },
        "teaching_action": {
            "type": "hint",
            "message": "Trace the input 'abba'.",
            "next_expected_action": {
                "type": "revise_code",
                "instruction": "Revise the left pointer update logic.",
            },
        },
    }


def test_deepseek_client_posts_chat_completion_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_urlopen(request: Request, timeout: float) -> FakeHTTPResponse:
        assert request.data is not None
        captured["request"] = request
        captured["timeout"] = timeout
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return FakeHTTPResponse(
            {
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": json.dumps(valid_teacher_output())},
                    }
                ]
            }
        )

    monkeypatch.setattr(deepseek_client_module.urllib.request, "urlopen", fake_urlopen)
    client = DeepSeekClient(
        api_key="test-key",
        base_url="https://api.deepseek.com/",
        timeout_seconds=12.0,
    )

    output = client.complete_json([LLMMessage(role="user", content="Return JSON.")])

    request = captured["request"]
    payload = captured["payload"]
    assert request.full_url == "https://api.deepseek.com/chat/completions"
    assert request.get_header("Authorization") == "Bearer test-key"
    assert captured["timeout"] == 12.0
    assert payload["model"] == "deepseek-v4-flash"
    assert payload["messages"] == [{"role": "user", "content": "Return JSON."}]
    assert payload["stream"] is False
    assert payload["response_format"] == {"type": "json_object"}
    assert payload["thinking"] == {"type": "disabled"}
    assert output["diagnosis"]["issue"] == "left_boundary_update_error"


def test_deepseek_client_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENKERI_DEEPSEEK_API_KEY", "env-key")
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setenv("OPENKERI_DEEPSEEK_MODEL", "deepseek-v4-pro")
    monkeypatch.setenv("OPENKERI_DEEPSEEK_BASE_URL", "https://example.com")

    client = DeepSeekClient.from_env()

    assert client.api_key == "env-key"
    assert client.model == "deepseek-v4-pro"
    assert client.base_url == "https://example.com"


def test_deepseek_client_from_env_accepts_generic_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENKERI_DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "generic-key")

    client = DeepSeekClient.from_env()

    assert client.api_key == "generic-key"


def test_deepseek_client_from_env_prefers_openkeri_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENKERI_DEEPSEEK_API_KEY", "openkeri-key")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "generic-key")

    client = DeepSeekClient.from_env()

    assert client.api_key == "openkeri-key"


def test_deepseek_client_from_env_requires_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENKERI_DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    with pytest.raises(ValueError, match="OPENKERI_DEEPSEEK_API_KEY.*DEEPSEEK_API_KEY"):
        DeepSeekClient.from_env()


def test_deepseek_client_rejects_non_object_model_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(request: Request, timeout: float) -> FakeHTTPResponse:
        return FakeHTTPResponse(
            {
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": "[]"},
                    }
                ]
            }
        )

    monkeypatch.setattr(deepseek_client_module.urllib.request, "urlopen", fake_urlopen)
    client = DeepSeekClient(api_key="test-key")

    with pytest.raises(DeepSeekClientError, match="must be an object"):
        client.complete_json([LLMMessage(role="user", content="Return JSON.")])


def test_deepseek_client_rejects_truncated_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(request: Request, timeout: float) -> FakeHTTPResponse:
        return FakeHTTPResponse(
            {
                "choices": [
                    {
                        "finish_reason": "length",
                        "message": {"content": '{"diagnosis":'},
                    }
                ]
            }
        )

    monkeypatch.setattr(deepseek_client_module.urllib.request, "urlopen", fake_urlopen)
    client = DeepSeekClient(api_key="test-key")

    with pytest.raises(DeepSeekClientError, match="truncated"):
        client.complete_json([LLMMessage(role="user", content="Return JSON.")])
