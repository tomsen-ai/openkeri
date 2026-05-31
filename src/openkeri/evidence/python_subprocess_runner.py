import json
import subprocess
import sys
from typing import Any

from pydantic import BaseModel, Field

from openkeri.schemas import ExecutionResult

_CHILD_RUNNER_CODE = r"""
import contextlib
import io
import json
import sys


def emit(result):
    sys.__stdout__.write(json.dumps(result, default=repr))


def main():
    payload = json.loads(sys.stdin.read())
    code = payload["code"]
    entrypoint_name = payload["entrypoint"]
    test_cases = payload["test_cases"]
    namespace = {}

    try:
        with contextlib.redirect_stdout(io.StringIO()):
            with contextlib.redirect_stderr(io.StringIO()):
                exec(code, namespace)
    except Exception as error:
        emit(
            {
                "status": "error",
                "error": f"{type(error).__name__}: {error}",
            }
        )
        return

    entrypoint = namespace.get(entrypoint_name)
    if not callable(entrypoint):
        emit(
            {
                "status": "error",
                "error": f"Entrypoint function not found: {entrypoint_name}",
            }
        )
        return

    passed_count = 0
    failed_cases = []
    for test_case in test_cases:
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                with contextlib.redirect_stderr(io.StringIO()):
                    actual = entrypoint(test_case["input"])
        except Exception as error:
            emit(
                {
                    "status": "error",
                    "passed_count": passed_count,
                    "failed_count": len(test_cases) - passed_count,
                    "failed_cases": failed_cases,
                    "error": f"{type(error).__name__}: {error}",
                }
            )
            return

        expected = test_case["expected"]
        if actual == expected:
            passed_count += 1
        else:
            failed_cases.append(
                {
                    "input": test_case["input"],
                    "expected": expected,
                    "actual": actual,
                }
            )

    failed_count = len(failed_cases)
    emit(
        {
            "status": "passed" if failed_count == 0 else "failed",
            "passed_count": passed_count,
            "failed_count": failed_count,
            "failed_cases": failed_cases,
        }
    )


if __name__ == "__main__":
    main()
"""


class PythonSubprocessRunner(BaseModel):
    """Runs trusted local Python submissions in a separate process.

    This is a stability boundary with timeout handling, not a security sandbox.
    """

    timeout_seconds: float = Field(default=2.0, gt=0)
    output_limit: int = Field(default=4000, gt=0)

    def run(self, code: str, test_suite: Any) -> ExecutionResult:
        payload = self._build_payload(code, test_suite)
        try:
            serialized_payload = json.dumps(payload)
        except TypeError as error:
            return ExecutionResult(
                status="error",
                error=f"RunnerProtocolError: payload is not JSON serializable: {error}",
            )

        try:
            completed = subprocess.run(
                [sys.executable, "-c", _CHILD_RUNNER_CODE],
                input=serialized_payload,
                capture_output=True,
                check=False,
                text=True,
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                status="error",
                failed_count=len(test_suite.test_cases),
                error=(
                    f"TimeoutError: execution exceeded {self.timeout_seconds:g} seconds"
                ),
            )

        if completed.returncode != 0:
            return ExecutionResult(
                status="error",
                error=(f"RunnerProcessError: {self._process_error_detail(completed)}"),
            )

        stdout = completed.stdout.strip()
        if not stdout:
            return ExecutionResult(
                status="error",
                error="RunnerProtocolError: runner produced no JSON output",
            )

        try:
            raw_result = json.loads(stdout)
        except json.JSONDecodeError as error:
            return ExecutionResult(
                status="error",
                error=(
                    "RunnerProtocolError: runner produced invalid JSON: "
                    f"{error}: {self._truncate(stdout)}"
                ),
            )

        if not isinstance(raw_result, dict):
            return ExecutionResult(
                status="error",
                error="RunnerProtocolError: runner JSON output must be an object",
            )
        return ExecutionResult.model_validate(raw_result)

    def _build_payload(self, code: str, test_suite: Any) -> dict[str, Any]:
        return {
            "code": code,
            "entrypoint": test_suite.entrypoint,
            "test_cases": [
                test_case.model_dump(mode="json") for test_case in test_suite.test_cases
            ],
        }

    def _process_error_detail(self, completed: subprocess.CompletedProcess[str]) -> str:
        stderr = completed.stderr.strip()
        if stderr:
            return self._truncate(stderr)

        stdout = completed.stdout.strip()
        if stdout:
            return self._truncate(stdout)

        return f"process exited with code {completed.returncode}"

    def _truncate(self, value: str) -> str:
        if len(value) <= self.output_limit:
            return value
        return f"{value[: self.output_limit]}... [truncated]"
