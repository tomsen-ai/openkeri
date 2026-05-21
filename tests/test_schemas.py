from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from openkeri.schemas import (
    CodeSubmission,
    CurrentInput,
    Diagnosis,
    Evidence,
    EvidenceItem,
    LearnerMemory,
    LearnerProfile,
    LearningEvent,
    MemoryContext,
    NextExpectedAction,
    Problem,
    RelatedHistoryItem,
    SessionState,
    TeacherOutput,
    TeachingAction,
    TeachingContext,
)


def make_problem() -> Problem:
    return Problem(
        id="leetcode_3",
        title="Longest Substring Without Repeating Characters",
        description="Given a string s, return the length of the longest substring.",
        target_concepts=["sliding_window", "hash_map"],
        difficulty="medium",
    )


def make_current_input() -> CurrentInput:
    return CurrentInput(
        problem=make_problem(),
        student_question="Why does this fail on abba?",
        code_submission=CodeSubmission(
            language="python",
            code="def lengthOfLongestSubstring(s):\n    return 0",
        ),
    )


def make_memory_context() -> MemoryContext:
    return MemoryContext(
        session_state=SessionState(
            session_id="sess_001",
            current_problem_id="leetcode_3",
            current_phase="working",
            recent_actions=["submitted_code"],
            last_teaching_action="hint",
            hint_count=1,
            problem_status="in_progress",
        ),
        learner_memory=LearnerMemory(
            learner_profile=LearnerProfile(
                learner_id="learner_001",
                level="beginner_intermediate",
                goal="algorithm_interview_prep",
                preferred_language="zh",
                teaching_style="hint_first",
                known_concepts=["array", "hash_map"],
                weak_concepts=["sliding_window"],
                common_mistakes=["left_pointer_update"],
            ),
            related_history=[
                RelatedHistoryItem(
                    concept="sliding_window",
                    issue="left_pointer_update",
                    seen_count=2,
                    last_seen_problem_id="leetcode_3",
                )
            ],
        ),
    )


def make_evidence() -> Evidence:
    return Evidence(
        items=[
            EvidenceItem(
                id="ev_001",
                type="execution_result",
                source="code_runner",
                summary="The code fails on input 'abba'.",
                content={
                    "status": "failed",
                    "passed_count": 8,
                    "failed_count": 1,
                    "failed_cases": [
                        {
                            "input": "abba",
                            "expected": 2,
                            "actual": 3,
                        }
                    ],
                    "error": None,
                },
            )
        ]
    )


def make_teacher_output() -> TeacherOutput:
    return TeacherOutput(
        diagnosis=Diagnosis(
            status="incorrect",
            issue="left_boundary_update_error",
            concept="sliding_window",
            confidence=0.84,
            evidence_refs=["ev_001"],
            evidence_summary="The submitted code returns 3 for 'abba'.",
        ),
        teaching_action=TeachingAction(
            type="hint",
            message="Try tracing the input 'abba'.",
            next_expected_action=NextExpectedAction(
                type="revise_code",
                instruction="Update the left pointer logic and submit again.",
            ),
        ),
    )


def test_current_input_can_be_created() -> None:
    current_input = make_current_input()

    assert current_input.problem.id == "leetcode_3"
    assert current_input.code_submission is not None
    assert current_input.code_submission.language == "python"


def test_memory_context_can_be_created() -> None:
    memory_context = make_memory_context()

    assert memory_context.session_state.hint_count == 1
    assert memory_context.learner_memory.learner_profile.preferred_language == "zh"
    assert memory_context.learner_memory.related_history[0].seen_count == 2


def test_evidence_can_be_created() -> None:
    evidence = make_evidence()

    assert evidence.items[0].id == "ev_001"
    assert evidence.items[0].content["status"] == "failed"


def test_teaching_context_can_be_created() -> None:
    context = TeachingContext(
        current_input=make_current_input(),
        memory_context=make_memory_context(),
        evidence=make_evidence(),
    )

    assert context.current_input.problem.id == "leetcode_3"
    assert context.evidence.items[0].source == "code_runner"


def test_teacher_output_can_be_created() -> None:
    output = make_teacher_output()

    assert output.diagnosis.status == "incorrect"
    assert output.teaching_action.type == "hint"


def test_learning_event_can_be_created() -> None:
    timestamp = datetime(2026, 5, 20, 10, 30, tzinfo=UTC)

    event = LearningEvent(
        event_id="evt_001",
        learner_id="learner_001",
        session_id="sess_001",
        current_input=make_current_input(),
        evidence=make_evidence(),
        teacher_output=make_teacher_output(),
        timestamp=timestamp,
    )

    assert event.timestamp == timestamp
    assert event.teacher_output.diagnosis.issue == "left_boundary_update_error"


def test_invalid_teaching_action_type_raises_validation_error() -> None:
    with pytest.raises(ValidationError):
        TeachingAction(type="slide", message="Show a slide.")


def test_invalid_diagnosis_confidence_raises_validation_error() -> None:
    with pytest.raises(ValidationError):
        Diagnosis(status="incorrect", confidence=1.5)
