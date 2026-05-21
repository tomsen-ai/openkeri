from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field

from openkeri.schemas import (
    CurrentInput,
    Evidence,
    EvidenceItem,
    ExecutionResult,
    FailedCase,
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

        execution_result = self._run_python_code(
            code=current_input.code_submission.code,
            test_suite=test_suite,
        )

        return self._single_item(
            item_type="execution_result",
            summary=self._execution_summary(execution_result),
            content=execution_result.model_dump(),
        )

    def _run_python_code(
        self,
        code: str,
        test_suite: ProblemTestSuite,
    ) -> ExecutionResult:
        namespace: dict[str, Any] = {}
        try:
            exec(code, {}, namespace)
        except Exception as error:
            return ExecutionResult(
                status="error",
                error=f"{type(error).__name__}: {error}",
            )

        entrypoint = namespace.get(test_suite.entrypoint)
        if not callable(entrypoint):
            return ExecutionResult(
                status="error",
                error=f"Entrypoint function not found: {test_suite.entrypoint}",
            )

        return self._run_test_cases(entrypoint, test_suite)

    def _run_test_cases(
        self,
        entrypoint: Callable[..., Any],
        test_suite: ProblemTestSuite,
    ) -> ExecutionResult:
        passed_count = 0
        failed_cases: list[FailedCase] = []

        for test_case in test_suite.test_cases:
            try:
                actual = entrypoint(test_case.input)
            except Exception as error:
                return ExecutionResult(
                    status="error",
                    passed_count=passed_count,
                    failed_count=len(test_suite.test_cases) - passed_count,
                    failed_cases=failed_cases,
                    error=f"{type(error).__name__}: {error}",
                )

            if actual == test_case.expected:
                passed_count += 1
            else:
                failed_cases.append(
                    FailedCase(
                        input=test_case.input,
                        expected=test_case.expected,
                        actual=actual,
                    )
                )

        failed_count = len(failed_cases)
        status = "passed" if failed_count == 0 else "failed"
        return ExecutionResult(
            status=status,
            passed_count=passed_count,
            failed_count=failed_count,
            failed_cases=failed_cases,
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
