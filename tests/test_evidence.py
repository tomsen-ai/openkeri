from openkeri.evidence import (
    ProblemTestCase,
    ProblemTestSuite,
    PythonCodeRunnerEvidenceCollector,
)
from openkeri.schemas import CodeSubmission, CurrentInput, Problem


def make_problem() -> Problem:
    return Problem(
        id="leetcode_3",
        title="Longest Substring Without Repeating Characters",
        description="Given a string s, return the length of the longest substring.",
        target_concepts=["sliding_window", "hash_map"],
        difficulty="medium",
    )


def make_current_input(code: str | None, language: str = "python") -> CurrentInput:
    return CurrentInput(
        problem=make_problem(),
        code_submission=(
            CodeSubmission(language=language, code=code) if code is not None else None
        ),
    )


def make_collector() -> PythonCodeRunnerEvidenceCollector:
    return PythonCodeRunnerEvidenceCollector(
        test_suites={
            "leetcode_3": ProblemTestSuite(
                problem_id="leetcode_3",
                entrypoint="lengthOfLongestSubstring",
                test_cases=[
                    ProblemTestCase(input="abcabcbb", expected=3),
                    ProblemTestCase(input="bbbbb", expected=1),
                    ProblemTestCase(input="pwwkew", expected=3),
                    ProblemTestCase(input="abba", expected=2),
                ],
            )
        }
    )


def test_collect_returns_no_code_submission_evidence() -> None:
    evidence = make_collector().collect(make_current_input(code=None))

    assert evidence.items[0].type == "no_code_submission"
    assert evidence.items[0].content["status"] == "not_run"


def test_collect_returns_unsupported_language_evidence() -> None:
    evidence = make_collector().collect(
        make_current_input(code="function solve() {}", language="javascript")
    )

    assert evidence.items[0].type == "unsupported_language"
    assert evidence.items[0].content["language"] == "javascript"


def test_collect_returns_missing_test_suite_evidence() -> None:
    collector = PythonCodeRunnerEvidenceCollector()

    evidence = collector.collect(make_current_input(code="def f(s): return 0"))

    assert evidence.items[0].type == "missing_test_suite"
    assert evidence.items[0].content["problem_id"] == "leetcode_3"


def test_collect_returns_passed_execution_evidence() -> None:
    code = """
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

    evidence = make_collector().collect(make_current_input(code=code))

    item = evidence.items[0]
    assert item.type == "execution_result"
    assert item.content["status"] == "passed"
    assert item.content["passed_count"] == 4
    assert item.content["failed_count"] == 0


def test_collect_returns_failed_execution_evidence() -> None:
    code = """
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

    evidence = make_collector().collect(make_current_input(code=code))

    item = evidence.items[0]
    assert item.type == "execution_result"
    assert item.content["status"] == "failed"
    assert item.content["failed_cases"] == [
        {
            "input": "abba",
            "expected": 2,
            "actual": 3,
        }
    ]


def test_collect_returns_error_execution_evidence_for_runtime_error() -> None:
    code = """
def lengthOfLongestSubstring(s):
    raise ValueError("boom")
"""

    evidence = make_collector().collect(make_current_input(code=code))

    item = evidence.items[0]
    assert item.type == "execution_result"
    assert item.content["status"] == "error"
    assert "ValueError: boom" in item.content["error"]


def test_collect_returns_error_execution_evidence_for_missing_entrypoint() -> None:
    evidence = make_collector().collect(
        make_current_input(code="def wrong(s): return 0")
    )

    item = evidence.items[0]
    assert item.type == "execution_result"
    assert item.content["status"] == "error"
    assert "Entrypoint function not found" in item.content["error"]
