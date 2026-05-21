from datetime import UTC, datetime

from openkeri.memory import InMemoryMemoryStore
from openkeri.schemas import (
    CodeSubmission,
    CurrentInput,
    Diagnosis,
    Evidence,
    LearnerMemory,
    LearningEvent,
    NextExpectedAction,
    Problem,
    RelatedHistoryItem,
    TeacherOutput,
    TeachingAction,
)


def make_current_input() -> CurrentInput:
    return CurrentInput(
        problem=Problem(
            id="leetcode_3",
            title="Longest Substring Without Repeating Characters",
            description="Given a string s, return the length of the longest substring.",
            target_concepts=["sliding_window", "hash_map"],
            difficulty="medium",
        ),
        student_question="Why does this fail on abba?",
        code_submission=CodeSubmission(
            language="python",
            code="def lengthOfLongestSubstring(s):\n    return 0",
        ),
    )


def make_event(
    *,
    status: str = "incorrect",
    action_type: str = "hint",
    concept: str | None = "sliding_window",
    issue: str | None = "left_boundary_update_error",
) -> LearningEvent:
    return LearningEvent(
        event_id="evt_001",
        learner_id="learner_001",
        session_id="sess_001",
        current_input=make_current_input(),
        evidence=Evidence(),
        teacher_output=TeacherOutput(
            diagnosis=Diagnosis(
                status=status,
                issue=issue,
                concept=concept,
                confidence=0.84,
            ),
            teaching_action=TeachingAction(
                type=action_type,
                message="Try tracing the input 'abba'.",
                next_expected_action=NextExpectedAction(
                    type="revise_code",
                    instruction="Update the left pointer logic and submit again.",
                ),
            ),
        ),
        timestamp=datetime(2026, 5, 20, 10, 30, tzinfo=UTC),
    )


def test_get_context_creates_default_session_state_and_learner_memory() -> None:
    store = InMemoryMemoryStore()

    context = store.get_context(
        learner_id="learner_001",
        session_id="sess_001",
        problem_id="leetcode_3",
    )

    assert context.session_state.session_id == "sess_001"
    assert context.session_state.current_problem_id == "leetcode_3"
    assert context.session_state.hint_count == 0
    assert context.learner_memory.learner_profile.learner_id == "learner_001"
    assert context.learner_memory.related_history == []


def test_get_context_returns_existing_session_state_and_learner_memory() -> None:
    store = InMemoryMemoryStore()
    store.get_context(
        learner_id="learner_001",
        session_id="sess_001",
        problem_id="old_problem",
    )

    context = store.get_context(
        learner_id="learner_001",
        session_id="sess_001",
        problem_id="leetcode_3",
    )

    assert context.session_state.current_problem_id == "leetcode_3"
    assert context.learner_memory.learner_profile.learner_id == "learner_001"


def test_record_event_appends_event_and_updates_session_state() -> None:
    store = InMemoryMemoryStore()

    context = store.record_event(make_event())

    assert len(store.events) == 1
    assert context.session_state.current_problem_id == "leetcode_3"
    assert context.session_state.last_teaching_action == "hint"
    assert context.session_state.hint_count == 1
    assert context.session_state.current_phase == "working"
    assert context.session_state.problem_status == "in_progress"
    assert context.session_state.recent_actions == [
        "submitted_code",
        "asked_question",
    ]


def test_record_event_marks_completed_when_diagnosis_is_correct() -> None:
    store = InMemoryMemoryStore()

    context = store.record_event(
        make_event(
            status="correct",
            action_type="explanation",
            concept="sliding_window",
            issue=None,
        )
    )

    assert context.session_state.current_phase == "completed"
    assert context.session_state.problem_status == "completed"
    assert context.session_state.hint_count == 0


def test_record_event_marks_question_phase_when_no_submission() -> None:
    store = InMemoryMemoryStore()

    context = store.record_event(
        make_event(
            status="no_submission",
            action_type="hint",
            concept="sliding_window",
            issue=None,
        )
    )

    assert context.session_state.current_phase == "question"
    assert context.session_state.problem_status == "in_progress"


def test_record_event_adds_related_history_item() -> None:
    store = InMemoryMemoryStore()

    context = store.record_event(make_event())

    assert context.learner_memory.related_history == [
        RelatedHistoryItem(
            concept="sliding_window",
            issue="left_boundary_update_error",
            seen_count=1,
            last_seen_problem_id="leetcode_3",
        )
    ]


def test_record_event_updates_existing_related_history_item() -> None:
    store = InMemoryMemoryStore(
        learner_memories={
            "learner_001": LearnerMemory(
                learner_profile={"learner_id": "learner_001"},
                related_history=[
                    RelatedHistoryItem(
                        concept="sliding_window",
                        issue="left_boundary_update_error",
                        seen_count=2,
                        last_seen_problem_id="old_problem",
                    )
                ],
            )
        }
    )

    context = store.record_event(make_event())

    assert context.learner_memory.related_history[0].seen_count == 3
    assert context.learner_memory.related_history[0].last_seen_problem_id == (
        "leetcode_3"
    )
