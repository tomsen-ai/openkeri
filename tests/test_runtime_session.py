from openkeri.agent import RuleBasedTeacher
from openkeri.evidence import (
    ProblemTestCase,
    ProblemTestSuite,
    PythonCodeRunnerEvidenceCollector,
)
from openkeri.memory import InMemoryMemoryStore
from openkeri.runtime import TeachingSession
from openkeri.schemas import CodeSubmission, CurrentInput, Problem


def make_problem() -> Problem:
    return Problem(
        id="leetcode_3",
        title="Longest Substring Without Repeating Characters",
        description="Given a string s, return the length of the longest substring.",
        target_concepts=["sliding_window", "hash_map"],
        difficulty="medium",
    )


def make_test_suite() -> ProblemTestSuite:
    return ProblemTestSuite(
        problem_id="leetcode_3",
        entrypoint="lengthOfLongestSubstring",
        test_cases=[
            ProblemTestCase(input="abcabcbb", expected=3),
            ProblemTestCase(input="bbbbb", expected=1),
            ProblemTestCase(input="pwwkew", expected=3),
            ProblemTestCase(input="abba", expected=2),
        ],
    )


def make_session(memory_store: InMemoryMemoryStore) -> TeachingSession:
    return TeachingSession(
        learner_id="learner_001",
        session_id="sess_001",
        memory_store=memory_store,
        evidence_collector=PythonCodeRunnerEvidenceCollector(
            test_suites={"leetcode_3": make_test_suite()}
        ),
        teacher_agent=RuleBasedTeacher(),
    )


def make_current_input(code: str) -> CurrentInput:
    return CurrentInput(
        problem=make_problem(),
        student_question="Why does this fail on abba?",
        code_submission=CodeSubmission(language="python", code=code),
    )


def incorrect_sliding_window_code() -> str:
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


def correct_sliding_window_code() -> str:
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


def test_handle_turn_runs_full_workflow_for_failed_submission() -> None:
    memory_store = InMemoryMemoryStore()
    session = make_session(memory_store)

    output = session.handle_turn(make_current_input(incorrect_sliding_window_code()))

    assert output.diagnosis.status == "incorrect"
    assert output.diagnosis.issue == "left_boundary_update_error"
    assert output.teaching_action.type == "hint"
    assert len(memory_store.events) == 1

    context = memory_store.get_context(
        learner_id="learner_001",
        session_id="sess_001",
        problem_id="leetcode_3",
    )
    assert context.session_state.hint_count == 1
    assert context.session_state.last_teaching_action == "hint"
    assert context.learner_memory.related_history[0].seen_count == 1


def test_handle_turn_uses_updated_memory_on_later_turns() -> None:
    memory_store = InMemoryMemoryStore()
    session = make_session(memory_store)

    session.handle_turn(make_current_input(incorrect_sliding_window_code()))
    session.handle_turn(make_current_input(incorrect_sliding_window_code()))
    output = session.handle_turn(make_current_input(incorrect_sliding_window_code()))

    assert output.diagnosis.issue == "left_boundary_update_error"
    assert output.teaching_action.type == "explanation"

    context = memory_store.get_context(
        learner_id="learner_001",
        session_id="sess_001",
        problem_id="leetcode_3",
    )
    assert context.session_state.hint_count == 2
    assert context.learner_memory.related_history[0].seen_count == 3


def test_handle_turn_records_completed_session_for_correct_submission() -> None:
    memory_store = InMemoryMemoryStore()
    session = make_session(memory_store)

    output = session.handle_turn(make_current_input(correct_sliding_window_code()))

    assert output.diagnosis.status == "correct"
    assert output.teaching_action.type == "explanation"

    context = memory_store.get_context(
        learner_id="learner_001",
        session_id="sess_001",
        problem_id="leetcode_3",
    )
    assert context.session_state.problem_status == "completed"
    assert context.session_state.current_phase == "completed"
    assert len(memory_store.events) == 1
    assert memory_store.events[0].event_id
    assert memory_store.events[0].timestamp.tzinfo is not None
