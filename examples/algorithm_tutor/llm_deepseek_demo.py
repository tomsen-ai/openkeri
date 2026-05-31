from demo import build_current_input, incorrect_code, print_turn
from session_factory import build_llm_session

from openkeri.llm import DeepSeekClient, DeepSeekClientError
from openkeri.memory import InMemoryMemoryStore


def main() -> None:
    try:
        client = DeepSeekClient.from_env()
    except ValueError:
        print("Set OPENKERI_DEEPSEEK_API_KEY or DEEPSEEK_API_KEY to run this demo.")
        return

    memory_store = InMemoryMemoryStore()
    session = build_llm_session(
        memory_store=memory_store,
        problem_id="leetcode_3",
        client=client,
        session_id="sess_llm_deepseek",
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
