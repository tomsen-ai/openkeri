from registry import build_algorithm_tutor_registry, get_problem, get_test_suite

from openkeri.agent import RuleBasedTeacher
from openkeri.evidence import PythonCodeRunnerEvidenceCollector
from openkeri.memory import InMemoryMemoryStore
from openkeri.runtime import TeachingSession
from openkeri.schemas import CodeSubmission, CurrentInput, TeacherOutput


def incorrect_code() -> str:
    return """
def lengthOfLongestSubstring(s):
    left = 0
    seen = {}
    best = 0
    for right, ch in enumerate(s):
        if ch in seen:
            left = seen[ch] + 1
        seen[ch] = right
        best = max(best, right - left + 1)
    return best
"""


def correct_code() -> str:
    return """
def lengthOfLongestSubstring(s):
    left = 0
    seen = {}
    best = 0
    for right, ch in enumerate(s):
        if ch in seen and seen[ch] >= left:
            left = seen[ch] + 1
        seen[ch] = right
        best = max(best, right - left + 1)
    return best
"""


def build_session(memory_store: InMemoryMemoryStore) -> TeachingSession:
    task_registry = build_algorithm_tutor_registry()
    return TeachingSession(
        learner_id="learner_001",
        session_id="sess_001",
        memory_store=memory_store,
        evidence_collector=PythonCodeRunnerEvidenceCollector(
            test_suites={"leetcode_3": get_test_suite(task_registry, "leetcode_3")}
        ),
        teacher_agent=RuleBasedTeacher(),
    )


def build_current_input(code: str) -> CurrentInput:
    task_registry = build_algorithm_tutor_registry()
    return CurrentInput(
        problem=get_problem(task_registry, "leetcode_3"),
        student_question="Why does this fail on abba?",
        code_submission=CodeSubmission(language="python", code=code),
    )


def print_turn(turn_number: int, output: TeacherOutput) -> None:
    print(f"Turn {turn_number}")
    print(f"Diagnosis status: {output.diagnosis.status}")
    print(f"Diagnosis issue: {output.diagnosis.issue}")
    print(f"Teaching action: {output.teaching_action.type}")
    print(f"Message: {output.teaching_action.message}")
    print()


def main() -> None:
    memory_store = InMemoryMemoryStore()
    session = build_session(memory_store)
    submissions = [
        incorrect_code(),
        incorrect_code(),
        incorrect_code(),
        correct_code(),
    ]

    for index, code in enumerate(submissions, start=1):
        output = session.handle_turn(build_current_input(code))
        print_turn(index, output)

    context = memory_store.get_context(
        learner_id="learner_001",
        session_id="sess_001",
        problem_id="leetcode_3",
    )
    print("Final memory")
    print(f"Hint count: {context.session_state.hint_count}")
    print(f"Problem status: {context.session_state.problem_status}")
    print(f"Related history count: {len(context.learner_memory.related_history)}")


if __name__ == "__main__":
    main()
