from openkeri.agent import RuleBasedTeacher
from openkeri.schemas import (
    CurrentInput,
    Evidence,
    EvidenceItem,
    LearnerMemory,
    LearnerProfile,
    MemoryContext,
    Problem,
    SessionState,
    TeachingContext,
)


def make_current_input(problem_id: str = "leetcode_3") -> CurrentInput:
    return CurrentInput(
        problem=Problem(
            id=problem_id,
            title="Longest Substring Without Repeating Characters",
            description="Given a string s, return the length of the longest substring.",
            target_concepts=["sliding_window", "hash_map"],
            difficulty="medium",
        )
    )


def make_memory_context(hint_count: int = 0) -> MemoryContext:
    return MemoryContext(
        session_state=SessionState(
            session_id="sess_001",
            current_problem_id="leetcode_3",
            hint_count=hint_count,
        ),
        learner_memory=LearnerMemory(
            learner_profile=LearnerProfile(learner_id="learner_001")
        ),
    )


def make_context(
    *,
    evidence_item: EvidenceItem,
    hint_count: int = 0,
    problem_id: str = "leetcode_3",
) -> TeachingContext:
    return TeachingContext(
        current_input=make_current_input(problem_id=problem_id),
        memory_context=make_memory_context(hint_count=hint_count),
        evidence=Evidence(items=[evidence_item]),
    )


def make_evidence_item(
    item_type: str,
    content: dict,
    summary: str | None = None,
) -> EvidenceItem:
    return EvidenceItem(
        id="ev_001",
        type=item_type,
        source="python_code_runner",
        summary=summary,
        content=content,
    )


def test_no_code_submission_returns_hint() -> None:
    output = RuleBasedTeacher().respond(
        make_context(
            evidence_item=make_evidence_item(
                item_type="no_code_submission",
                content={"status": "not_run"},
                summary="No code submission was provided.",
            )
        )
    )

    assert output.diagnosis.status == "no_submission"
    assert output.teaching_action.type == "hint"
    assert output.teaching_action.next_expected_action is not None
    assert output.teaching_action.next_expected_action.type == "answer_question"


def test_unsupported_language_returns_unclear_explanation() -> None:
    output = RuleBasedTeacher().respond(
        make_context(
            evidence_item=make_evidence_item(
                item_type="unsupported_language",
                content={"status": "not_run", "language": "javascript"},
                summary="Unsupported language: javascript.",
            )
        )
    )

    assert output.diagnosis.status == "unclear"
    assert output.diagnosis.issue == "unsupported_language"
    assert output.teaching_action.type == "explanation"


def test_runtime_error_returns_hint_before_threshold() -> None:
    output = RuleBasedTeacher().respond(
        make_context(
            evidence_item=make_evidence_item(
                item_type="execution_result",
                content={"status": "error", "error": "ValueError: boom"},
                summary="The code raised an error: ValueError: boom.",
            ),
            hint_count=0,
        )
    )

    assert output.diagnosis.status == "incorrect"
    assert output.diagnosis.issue == "runtime_error"
    assert output.teaching_action.type == "hint"


def test_failed_abba_case_returns_left_boundary_hint() -> None:
    output = RuleBasedTeacher().respond(
        make_context(
            evidence_item=make_evidence_item(
                item_type="execution_result",
                content={
                    "status": "failed",
                    "failed_cases": [{"input": "abba", "expected": 2, "actual": 3}],
                },
                summary="The code fails on 1 of 4 test cases.",
            ),
            hint_count=0,
        )
    )

    assert output.diagnosis.status == "incorrect"
    assert output.diagnosis.issue == "left_boundary_update_error"
    assert output.diagnosis.concept == "sliding_window"
    assert output.teaching_action.type == "hint"
    assert "left boundary" in output.teaching_action.message
    assert "backward" in output.teaching_action.message
    assert "abba" not in output.teaching_action.message


def test_failed_case_returns_explanation_after_hint_threshold() -> None:
    output = RuleBasedTeacher().respond(
        make_context(
            evidence_item=make_evidence_item(
                item_type="execution_result",
                content={
                    "status": "failed",
                    "failed_cases": [{"input": "abba", "expected": 2, "actual": 3}],
                },
                summary="The code fails on 1 of 4 test cases.",
            ),
            hint_count=2,
        )
    )

    assert output.diagnosis.issue == "left_boundary_update_error"
    assert output.teaching_action.type == "explanation"
    assert "left boundary" in output.teaching_action.message


def test_failed_non_abba_case_returns_generic_failing_test_case() -> None:
    output = RuleBasedTeacher().respond(
        make_context(
            evidence_item=make_evidence_item(
                item_type="execution_result",
                content={
                    "status": "failed",
                    "failed_cases": [{"input": "abcabcbb", "expected": 3, "actual": 0}],
                },
                summary="The code fails on 1 of 4 test cases.",
            ),
            problem_id="other_problem",
        )
    )

    assert output.diagnosis.issue == "failing_test_case"
    assert output.diagnosis.concept == "sliding_window"


def test_passed_execution_returns_correct_explanation() -> None:
    output = RuleBasedTeacher().respond(
        make_context(
            evidence_item=make_evidence_item(
                item_type="execution_result",
                content={"status": "passed", "passed_count": 4, "failed_count": 0},
                summary="All 4 test cases passed.",
            )
        )
    )

    assert output.diagnosis.status == "correct"
    assert output.diagnosis.issue is None
    assert output.teaching_action.type == "explanation"
    assert output.teaching_action.next_expected_action is not None
    assert output.teaching_action.next_expected_action.type == "continue"
