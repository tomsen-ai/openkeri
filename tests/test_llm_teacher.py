from typing import Any

import pytest

from openkeri.agent import LLMMessage, LLMTeacher, LLMTeacherError
from openkeri.schemas import (
    CurrentInput,
    Evidence,
    EvidenceItem,
    LearnerMemory,
    LearnerProfile,
    MemoryContext,
    Problem,
    SessionState,
    TeachingContext,
)


class MockLLMClient:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.messages: list[LLMMessage] = []

    def complete_json(self, messages: list[LLMMessage]) -> dict[str, Any]:
        self.messages = messages
        return self.response


class FailingLLMClient:
    def complete_json(self, messages: list[LLMMessage]) -> dict[str, Any]:
        raise RuntimeError("provider unavailable")


def make_context() -> TeachingContext:
    return TeachingContext(
        current_input=CurrentInput(
            problem=Problem(
                id="leetcode_3",
                title="Longest Substring Without Repeating Characters",
                description="Return the length of the longest substring.",
                target_concepts=["sliding_window", "hash_map"],
                difficulty="medium",
            )
        ),
        memory_context=MemoryContext(
            session_state=SessionState(session_id="sess_001", hint_count=1),
            learner_memory=LearnerMemory(
                learner_profile=LearnerProfile(learner_id="learner_001")
            ),
        ),
        evidence=Evidence(
            items=[
                EvidenceItem(
                    id="ev_001",
                    type="execution_result",
                    source="python_code_runner",
                    summary="The code fails on input 'abba'.",
                    content={"status": "failed"},
                )
            ]
        ),
    )


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


def test_llm_teacher_validates_client_json_response() -> None:
    client = MockLLMClient(valid_teacher_output())
    teacher = LLMTeacher(client=client)

    output = teacher.respond(make_context())

    assert output.diagnosis.issue == "left_boundary_update_error"
    assert output.teaching_action.type == "hint"


def test_llm_teacher_sends_teaching_context_to_client() -> None:
    client = MockLLMClient(valid_teacher_output())
    teacher = LLMTeacher(client=client)

    teacher.respond(make_context())

    assert len(client.messages) == 2
    assert client.messages[0].role == "system"
    assert client.messages[1].role == "user"
    assert "Use the evidence first" in client.messages[0].content
    assert "Do not invent unsupported causes" in client.messages[0].content
    assert "TeachingContext" in client.messages[1].content
    assert "Expected output JSON shape" in client.messages[1].content
    assert "next_expected_action" in client.messages[1].content
    assert "current_input" in client.messages[1].content
    assert "memory_context" in client.messages[1].content
    assert "evidence" in client.messages[1].content
    assert "ev_001" in client.messages[1].content


def test_llm_teacher_rejects_invalid_client_json_response() -> None:
    client = MockLLMClient({"message": "not a TeacherOutput"})
    teacher = LLMTeacher(client=client)

    with pytest.raises(LLMTeacherError, match="invalid TeacherOutput"):
        teacher.respond(make_context())


def test_llm_teacher_does_not_swallow_client_errors() -> None:
    teacher = LLMTeacher(client=FailingLLMClient())

    with pytest.raises(RuntimeError, match="provider unavailable"):
        teacher.respond(make_context())
