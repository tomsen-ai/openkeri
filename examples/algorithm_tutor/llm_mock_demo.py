from typing import Any

from demo import build_current_input, incorrect_code, print_turn
from registry import build_algorithm_tutor_registry, get_test_suite

from openkeri.agent import LLMTeacher
from openkeri.evidence import PythonCodeRunnerEvidenceCollector
from openkeri.llm import LLMMessage
from openkeri.memory import InMemoryMemoryStore
from openkeri.runtime import TeachingSession


class MockLLMClient:
    def complete_json(self, messages: list[LLMMessage]) -> dict[str, Any]:
        return {
            "diagnosis": {
                "status": "incorrect",
                "issue": "left_boundary_update_error",
                "concept": "sliding_window",
                "confidence": 0.82,
                "evidence_refs": ["ev_001"],
                "evidence_summary": "The code fails on input 'abba'.",
            },
            "teaching_action": {
                "type": "hint",
                "message": (
                    "Trace the input 'abba'. Pay attention to whether the left "
                    "pointer ever moves backward after a repeated character."
                ),
                "next_expected_action": {
                    "type": "revise_code",
                    "instruction": "Revise the left pointer update logic.",
                },
            },
        }


def main() -> None:
    task_registry = build_algorithm_tutor_registry()
    memory_store = InMemoryMemoryStore()
    session = TeachingSession(
        learner_id="learner_001",
        session_id="sess_llm_mock",
        memory_store=memory_store,
        evidence_collector=PythonCodeRunnerEvidenceCollector(
            test_suites={"leetcode_3": get_test_suite(task_registry, "leetcode_3")}
        ),
        teacher_agent=LLMTeacher(client=MockLLMClient()),
    )

    print("openkeri Mock LLMTeacher Demo")
    output = session.handle_turn(build_current_input(incorrect_code()))
    print_turn(1, output)


if __name__ == "__main__":
    main()
