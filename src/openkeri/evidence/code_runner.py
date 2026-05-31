from typing import Any

from pydantic import BaseModel, Field

from openkeri.evidence.python_subprocess_runner import PythonSubprocessRunner
from openkeri.schemas import (
    CurrentInput,
    Evidence,
    EvidenceItem,
    ExecutionResult,
)


class ProblemTestCase(BaseModel):
    input: Any
    expected: Any


class ProblemTestSuite(BaseModel):
    problem_id: str
    entrypoint: str
    test_cases: list[ProblemTestCase]


class PythonCodeRunnerEvidenceCollector(BaseModel):
    """Trusted local Python runner for demos and tests.

    This runner is not a secure sandbox and must not execute untrusted code.
    """

    test_suites: dict[str, ProblemTestSuite] = Field(default_factory=dict)
    runner: PythonSubprocessRunner = Field(default_factory=PythonSubprocessRunner)

    def collect(self, current_input: CurrentInput) -> Evidence:
        if current_input.code_submission is None:
            return self._single_item(
                item_type="no_code_submission",
                summary="No code submission was provided.",
                content={"status": "not_run"},
            )

        if current_input.code_submission.language.lower() != "python":
            return self._single_item(
                item_type="unsupported_language",
                summary=(
                    f"Unsupported language: {current_input.code_submission.language}."
                ),
                content={
                    "status": "not_run",
                    "language": current_input.code_submission.language,
                },
            )

        test_suite = self.test_suites.get(current_input.problem.id)
        if test_suite is None:
            return self._single_item(
                item_type="missing_test_suite",
                summary=f"No test suite found for problem {current_input.problem.id}.",
                content={
                    "status": "not_run",
                    "problem_id": current_input.problem.id,
                },
            )

        execution_result = self.runner.run(
            code=current_input.code_submission.code,
            test_suite=test_suite,
        )

        return self._single_item(
            item_type="execution_result",
            summary=self._execution_summary(execution_result),
            content=execution_result.model_dump(),
        )

    def _single_item(
        self,
        item_type: str,
        summary: str,
        content: dict[str, Any],
    ) -> Evidence:
        return Evidence(
            items=[
                EvidenceItem(
                    id="ev_001",
                    type=item_type,
                    source="python_code_runner",
                    summary=summary,
                    content=content,
                )
            ]
        )

    def _execution_summary(self, execution_result: ExecutionResult) -> str:
        if execution_result.status == "passed":
            return f"All {execution_result.passed_count} test cases passed."
        if execution_result.status == "failed":
            return (
                "The code fails on "
                f"{execution_result.failed_count} of "
                f"{execution_result.passed_count + execution_result.failed_count} "
                "test cases."
            )
        if execution_result.error is not None:
            return f"The code raised an error: {execution_result.error}."
        return "The code was not run."
