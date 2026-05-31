from openkeri.agent import DeepSeekClient as AgentDeepSeekClient
from openkeri.agent import LLMMessage as AgentLLMMessage
from openkeri.agent.deepseek_client import DeepSeekClient as LegacyDeepSeekClient
from openkeri.agent.llm_client import LLMMessage as LegacyLLMMessage
from openkeri.llm import DeepSeekClient, LLMMessage


def test_llm_package_exports_provider_and_message_types() -> None:
    assert DeepSeekClient is AgentDeepSeekClient
    assert LLMMessage is AgentLLMMessage


def test_legacy_agent_llm_modules_remain_compatible() -> None:
    assert LegacyDeepSeekClient is DeepSeekClient
    assert LegacyLLMMessage is LLMMessage
