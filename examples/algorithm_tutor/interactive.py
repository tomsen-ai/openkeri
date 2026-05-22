from pathlib import Path

from problems import REFERENCE_PROBLEMS

from openkeri.agent import RuleBasedTeacher
from openkeri.evidence import PythonCodeRunnerEvidenceCollector
from openkeri.memory import InMemoryMemoryStore
from openkeri.runtime import TeachingSession
from openkeri.schemas import CodeSubmission, CurrentInput, Problem, TeacherOutput


def build_session(
    memory_store: InMemoryMemoryStore,
    problem_id: str,
) -> TeachingSession:
    _, build_test_suite = REFERENCE_PROBLEMS[problem_id]
    return TeachingSession(
        learner_id="learner_001",
        session_id=f"sess_{problem_id}",
        memory_store=memory_store,
        evidence_collector=PythonCodeRunnerEvidenceCollector(
            test_suites={problem_id: build_test_suite()}
        ),
        teacher_agent=RuleBasedTeacher(),
    )


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
    problem_ids = list(REFERENCE_PROBLEMS)
    print("Choose a problem:")
    for index, problem_id in enumerate(problem_ids, start=1):
        build_problem, _ = REFERENCE_PROBLEMS[problem_id]
        print(f"{index}. {build_problem().title}")
    print()

    while True:
        choice = input("> ").strip()
        if choice.isdigit():
            index = int(choice)
            if 1 <= index <= len(problem_ids):
                problem_id = problem_ids[index - 1]
                build_problem, _ = REFERENCE_PROBLEMS[problem_id]
                return problem_id, build_problem()
        if choice in REFERENCE_PROBLEMS:
            build_problem, _ = REFERENCE_PROBLEMS[choice]
            return choice, build_problem()
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
