import subprocess
import sys


def test_algorithm_tutor_llm_mock_demo_runs() -> None:
    result = subprocess.run(
        [sys.executable, "examples/algorithm_tutor/llm_mock_demo.py"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "openkeri Mock LLMTeacher Demo" in result.stdout
    assert "Diagnosis issue: left_boundary_update_error" in result.stdout
    assert "Teaching action: hint" in result.stdout
