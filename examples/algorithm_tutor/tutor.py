from pathlib import Path

from registry import build_algorithm_tutor_registry, get_problem
from session_factory import (
    DEFAULT_LEARNER_ID,
    build_llm_session,
    build_rule_based_session,
)

from openkeri.agent import LLMTeacherError
from openkeri.llm import DeepSeekClient, DeepSeekClientError
from openkeri.memory import InMemoryMemoryStore
from openkeri.runtime import TeachingSession
from openkeri.schemas import CodeSubmission, CurrentInput, Problem, TeacherOutput

TEACHER_DEEPSEEK = "deepseek"
TEACHER_RULE_BASED = "rule-based"


class AlgorithmTutorApp:
    def __init__(self) -> None:
        self.task_registry = build_algorithm_tutor_registry()
        self.memory_store = InMemoryMemoryStore()
        self.teacher_type = TEACHER_RULE_BASED
        self.deepseek_client: DeepSeekClient | None = None
        self.problem_id = ""
        self.problem: Problem | None = None
        self.sessions: dict[tuple[str, str], TeachingSession] = {}
        self.turn_number = 1

    def run(self) -> None:
        print("openkeri Algorithm Tutor")
        print()
        self.choose_teacher()
        self.choose_problem()
        self.print_help()

        while True:
            raw_command = input("> ").strip()
            if not raw_command:
                continue
            if raw_command.lower() in {"q", "quit", "exit"}:
                print("Goodbye.")
                return
            self.handle_command(raw_command)

    def choose_teacher(self) -> None:
        while True:
            print("Choose teacher:")
            print("1. DeepSeek")
            print("2. Rule-based")
            choice = input("> ").strip().lower()
            print()

            if choice in {"1", "deepseek", "ds"}:
                try:
                    self.deepseek_client = DeepSeekClient.from_env()
                except ValueError:
                    print(
                        "DeepSeek is not configured. Set "
                        "OPENKERI_DEEPSEEK_API_KEY or DEEPSEEK_API_KEY, "
                        "or choose rule-based."
                    )
                    print()
                    continue
                self.teacher_type = TEACHER_DEEPSEEK
                print("Teacher: DeepSeek")
                print()
                return

            if choice in {"2", "rule", "rule-based", "rule_based"}:
                self.teacher_type = TEACHER_RULE_BASED
                print("Teacher: Rule-based")
                print()
                return

            print("Unknown teacher. Enter 1 or 2.")
            print()

    def choose_problem(self) -> None:
        while True:
            self.print_problems()
            choice = input("> ").strip()
            task_id = self.resolve_problem_choice(choice)
            if task_id is not None:
                self.set_problem(task_id)
                print(f"Problem: {self.problem.title if self.problem else task_id}")
                print()
                return
            print("Unknown problem. Enter a number or problem id.")
            print()

    def handle_command(self, raw_command: str) -> None:
        command, _, argument = raw_command.partition(" ")
        command = command.lower()
        argument = argument.strip()

        if command == "submit":
            if not argument:
                print("Usage: submit <solution_file.py>")
                print()
                return
            self.submit_solution(argument)
            return

        if command == "ask":
            if not argument:
                print("Usage: ask <question>")
                print()
                return
            self.ask_question(argument)
            return

        if command == "status":
            self.print_status()
            return

        if command == "problems":
            self.print_problems()
            return

        if command == "switch":
            self.switch_problem(argument)
            return

        self.submit_solution(raw_command)

    def submit_solution(self, path: str) -> None:
        if self.problem is None:
            print("Choose a problem before submitting.")
            print()
            return

        try:
            code = Path(path).read_text(encoding="utf-8")
        except OSError as error:
            print(f"Could not read solution file: {error}")
            print()
            return

        session = self.current_session()
        current_input = CurrentInput(
            problem=self.problem,
            student_question="Why does this fail?",
            code_submission=CodeSubmission(language="python", code=code),
        )

        try:
            output = session.handle_turn(current_input)
        except (DeepSeekClientError, LLMTeacherError) as error:
            print(f"Teacher request failed: {error}")
            print()
            return

        self.print_turn(output)
        self.turn_number += 1

    def ask_question(self, question: str) -> None:
        if self.problem is None:
            print("Choose a problem before asking.")
            print()
            return

        current_input = CurrentInput(
            problem=self.problem,
            student_question=question,
            code_submission=None,
        )

        try:
            output = self.current_session().handle_turn(current_input)
        except (DeepSeekClientError, LLMTeacherError) as error:
            print(f"Teacher request failed: {error}")
            print()
            return

        self.print_turn(output)
        self.turn_number += 1

    def switch_problem(self, choice: str) -> None:
        if not choice:
            print("Usage: switch <problem_id>")
            print()
            return

        task_id = self.resolve_problem_choice(choice)
        if task_id is None:
            print("Unknown problem. Run 'problems' to see available problem ids.")
            print()
            return

        self.set_problem(task_id)
        print(f"Switched to {self.problem.title if self.problem else task_id}.")
        print()

    def current_session(self) -> TeachingSession:
        key = (self.teacher_type, self.problem_id)
        session = self.sessions.get(key)
        if session is not None:
            return session

        session_id = f"sess_{self.teacher_type}_{self.problem_id}"
        if self.teacher_type == TEACHER_DEEPSEEK:
            if self.deepseek_client is None:
                raise RuntimeError("DeepSeek client is not configured.")
            session = build_llm_session(
                memory_store=self.memory_store,
                problem_id=self.problem_id,
                client=self.deepseek_client,
                session_id=session_id,
            )
        else:
            session = build_rule_based_session(
                memory_store=self.memory_store,
                problem_id=self.problem_id,
                session_id=session_id,
            )

        self.sessions[key] = session
        return session

    def set_problem(self, task_id: str) -> None:
        self.problem_id = task_id
        self.problem = get_problem(self.task_registry, task_id)
        self.current_session()

    def resolve_problem_choice(self, choice: str) -> str | None:
        tasks = self.task_registry.list_tasks()
        if choice.isdigit():
            index = int(choice)
            if 1 <= index <= len(tasks):
                return tasks[index - 1].task.id
        if choice in self.task_registry.bundles:
            return choice
        return None

    def print_help(self) -> None:
        print("Enter a solution file path, or command:")
        print("  submit <path>")
        print("  ask <question>")
        print("  status")
        print("  problems")
        print("  switch <problem_id>")
        print("  q")
        print()

    def print_problems(self) -> None:
        print("Choose a problem:")
        for index, bundle in enumerate(self.task_registry.list_tasks(), start=1):
            print(f"{index}. {bundle.task.id} - {bundle.task.title}")
        print()

    def print_status(self) -> None:
        if self.problem is None:
            print("Problem: none")
            print()
            return

        session = self.current_session()
        context = self.memory_store.get_context(
            learner_id=DEFAULT_LEARNER_ID,
            session_id=session.session_id,
            problem_id=self.problem_id,
        )
        recent_actions = ", ".join(context.session_state.recent_actions) or "none"
        print(f"Teacher: {self.teacher_type}")
        print(f"Problem: {self.problem.title}")
        print(f"Hint count: {context.session_state.hint_count}")
        print(f"Problem status: {context.session_state.problem_status}")
        print(f"Recent actions: {recent_actions}")
        print()

    def print_turn(self, output: TeacherOutput) -> None:
        print(f"Turn {self.turn_number}")
        print(f"Diagnosis: {output.diagnosis.status}")
        print(f"Issue: {output.diagnosis.issue}")
        print(f"Action: {output.teaching_action.type}")
        print()
        print(output.teaching_action.message)
        if output.teaching_action.next_expected_action is not None:
            print()
            print(f"Next: {output.teaching_action.next_expected_action.instruction}")
        print()


def main() -> None:
    AlgorithmTutorApp().run()


if __name__ == "__main__":
    main()
