from pathlib import Path

from examples.algorithm_tutor.problems import (
    build_valid_palindrome_problem,
    build_valid_palindrome_test_suite,
)
from openkeri.evidence import PythonCodeRunnerEvidenceCollector
from openkeri.schemas import CodeSubmission, CurrentInput


def test_valid_palindrome_reference_problem_passes_with_correct_solution() -> None:
    collector = PythonCodeRunnerEvidenceCollector(
        test_suites={"valid_palindrome": build_valid_palindrome_test_suite()}
    )
    code = Path("examples/algorithm_tutor/solutions/palindrome_correct.py").read_text(
        encoding="utf-8"
    )

    evidence = collector.collect(
        CurrentInput(
            problem=build_valid_palindrome_problem(),
            code_submission=CodeSubmission(language="python", code=code),
        )
    )

    assert evidence.items[0].type == "execution_result"
    assert evidence.items[0].content["status"] == "passed"


def test_valid_palindrome_reference_problem_fails_with_incorrect_solution() -> None:
    collector = PythonCodeRunnerEvidenceCollector(
        test_suites={"valid_palindrome": build_valid_palindrome_test_suite()}
    )
    code = Path("examples/algorithm_tutor/solutions/palindrome_incorrect.py").read_text(
        encoding="utf-8"
    )

    evidence = collector.collect(
        CurrentInput(
            problem=build_valid_palindrome_problem(),
            code_submission=CodeSubmission(language="python", code=code),
        )
    )

    assert evidence.items[0].type == "execution_result"
    assert evidence.items[0].content["status"] == "failed"
    assert evidence.items[0].content["failed_cases"] == [
        {
            "input": "0P",
            "expected": False,
            "actual": True,
        }
    ]
