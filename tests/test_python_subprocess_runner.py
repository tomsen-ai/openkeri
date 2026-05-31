from openkeri.evidence import (
    ProblemTestCase,
    ProblemTestSuite,
    PythonSubprocessRunner,
)


def make_test_suite() -> ProblemTestSuite:
    return ProblemTestSuite(
        problem_id="double",
        entrypoint="double",
        test_cases=[
            ProblemTestCase(input=2, expected=4),
            ProblemTestCase(input=5, expected=10),
        ],
    )


def test_python_subprocess_runner_returns_passed_result() -> None:
    result = PythonSubprocessRunner().run(
        code="""
def double(value):
    return value * 2
""",
        test_suite=make_test_suite(),
    )

    assert result.status == "passed"
    assert result.passed_count == 2
    assert result.failed_count == 0


def test_python_subprocess_runner_supports_helper_functions() -> None:
    result = PythonSubprocessRunner().run(
        code="""
def multiply_by_two(value):
    return value * 2

def double(value):
    return multiply_by_two(value)
""",
        test_suite=make_test_suite(),
    )

    assert result.status == "passed"


def test_python_subprocess_runner_returns_failed_cases() -> None:
    result = PythonSubprocessRunner().run(
        code="""
def double(value):
    return value
""",
        test_suite=make_test_suite(),
    )

    assert result.status == "failed"
    assert result.failed_cases[0].input == 2
    assert result.failed_cases[0].expected == 4
    assert result.failed_cases[0].actual == 2


def test_python_subprocess_runner_returns_runtime_error() -> None:
    result = PythonSubprocessRunner().run(
        code="""
def double(value):
    raise ValueError("boom")
""",
        test_suite=make_test_suite(),
    )

    assert result.status == "error"
    assert result.passed_count == 0
    assert result.failed_count == 2
    assert result.error is not None
    assert "ValueError: boom" in result.error


def test_python_subprocess_runner_returns_missing_entrypoint_error() -> None:
    result = PythonSubprocessRunner().run(
        code="""
def wrong(value):
    return value * 2
""",
        test_suite=make_test_suite(),
    )

    assert result.status == "error"
    assert result.error is not None
    assert "Entrypoint function not found: double" in result.error


def test_python_subprocess_runner_times_out_infinite_loop() -> None:
    result = PythonSubprocessRunner(timeout_seconds=0.2).run(
        code="""
def double(value):
    while True:
        pass
""",
        test_suite=make_test_suite(),
    )

    assert result.status == "error"
    assert result.failed_count == 2
    assert result.error is not None
    assert "TimeoutError" in result.error


def test_python_subprocess_runner_ignores_submission_stdout() -> None:
    result = PythonSubprocessRunner().run(
        code="""
print("module noise")

def double(value):
    print("function noise")
    return value * 2
""",
        test_suite=make_test_suite(),
    )

    assert result.status == "passed"
