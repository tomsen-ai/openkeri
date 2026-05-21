from pathlib import Path

from demo import build_current_input, build_session, print_turn

from openkeri.memory import InMemoryMemoryStore
from openkeri.runtime import TeachingSession
from openkeri.schemas import TeacherOutput


def run_solution_file(session: TeachingSession, path: str | Path) -> TeacherOutput:
    code = Path(path).read_text(encoding="utf-8")
    return session.handle_turn(build_current_input(code))


def main() -> None:
    memory_store = InMemoryMemoryStore()
    session = build_session(memory_store)
    turn_number = 1

    print("openkeri Algorithm Tutor")
    print("Problem: Longest Substring Without Repeating Characters")
    print("Enter a Python solution file path, or 'q' to quit.")
    print()

    while True:
        raw_path = input("> ").strip()
        if raw_path.lower() in {"q", "quit", "exit"}:
            print("Goodbye.")
            return
        if not raw_path:
            continue

        try:
            output = run_solution_file(session, raw_path)
        except OSError as error:
            print(f"Could not read solution file: {error}")
            print()
            continue

        print_turn(turn_number, output)
        turn_number += 1


if __name__ == "__main__":
    main()
