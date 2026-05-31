from demo import build_current_input, incorrect_code, print_turn
from registry import build_algorithm_tutor_registry, get_test_suite

from openkeri.agent import DeepSeekClient, DeepSeekClientError, LLMTeacher
from openkeri.evidence import PythonCodeRunnerEvidenceCollector
from openkeri.memory import InMemoryMemoryStore
from openkeri.runtime import TeachingSession


def main() -> None:
    try:
        client = DeepSeekClient.from_env()
    except ValueError:
        print("Set OPENKERI_DEEPSEEK_API_KEY to run this demo.")
        return

    task_registry = build_algorithm_tutor_registry()
    memory_store = InMemoryMemoryStore()
    session = TeachingSession(
        learner_id="learner_001",
        session_id="sess_llm_deepseek",
        memory_store=memory_store,
        evidence_collector=PythonCodeRunnerEvidenceCollector(
            test_suites={"leetcode_3": get_test_suite(task_registry, "leetcode_3")}
        ),
        teacher_agent=LLMTeacher(client=client),
    )

    print("openkeri DeepSeek LLMTeacher Demo")
    try:
        output = session.handle_turn(build_current_input(incorrect_code()))
    except DeepSeekClientError as exc:
        print(f"DeepSeek request failed: {exc}")
        return

    print_turn(1, output)


if __name__ == "__main__":
    main()
