from pathlib import Path

from registry import build_algorithm_tutor_registry, get_problem
from session_factory import build_rule_based_session

from openkeri.memory import InMemoryMemoryStore
from openkeri.runtime import TeachingSession
from openkeri.schemas import CodeSubmission, CurrentInput, Problem, TeacherOutput


def build_session(
    memory_store: InMemoryMemoryStore,
    problem_id: str,
) -> TeachingSession:
    return build_rule_based_session(memory_store=memory_store, problem_id=problem_id)


def build_current_input(problem: Problem, code: str) -> CurrentInput:
    return CurrentInput(
        problem=problem,
        student_question="Why does this fail?",
        code_submission=CodeSubmission(language="python", code=code),
    )


def run_solution_file(
    session: TeachingSession,
    problem: Problem,
    path: str | Path,
) -> TeacherOutput:
    code = Path(path).read_text(encoding="utf-8")
    return session.handle_turn(build_current_input(problem, code))


def choose_problem() -> tuple[str, Problem]:
    task_registry = build_algorithm_tutor_registry()
    tasks = task_registry.list_tasks()
    print("Choose a problem:")
    for index, bundle in enumerate(tasks, start=1):
        print(f"{index}. {bundle.task.title}")
    print()

    while True:
        choice = input("> ").strip()
        if choice.isdigit():
            index = int(choice)
            if 1 <= index <= len(tasks):
                task_id = tasks[index - 1].task.id
                return task_id, get_problem(task_registry, task_id)
        if choice in task_registry.bundles:
            return choice, get_problem(task_registry, choice)
        print("Unknown problem. Enter a number or problem id.")


def print_turn(turn_number: int, output: TeacherOutput) -> None:
    print(f"Turn {turn_number}")
    print(f"Diagnosis status: {output.diagnosis.status}")
    print(f"Diagnosis issue: {output.diagnosis.issue}")
    print(f"Teaching action: {output.teaching_action.type}")
    print(f"Message: {output.teaching_action.message}")
    print()


def main() -> None:
    print("openkeri Algorithm Tutor")
    problem_id, problem = choose_problem()
    memory_store = InMemoryMemoryStore()
    session = build_session(memory_store, problem_id)
    turn_number = 1

    print()
    print(f"Problem: {problem.title}")
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
            output = run_solution_file(session, problem, raw_path)
        except OSError as error:
            print(f"Could not read solution file: {error}")
            print()
            continue

        print_turn(turn_number, output)
        turn_number += 1


if __name__ == "__main__":
    main()
