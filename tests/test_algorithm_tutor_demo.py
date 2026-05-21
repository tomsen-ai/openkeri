import subprocess
import sys


def test_algorithm_tutor_demo_runs() -> None:
    result = subprocess.run(
        [sys.executable, "examples/algorithm_tutor/demo.py"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Turn 1" in result.stdout
    assert "Turn 4" in result.stdout
    assert "Diagnosis issue: left_boundary_update_error" in result.stdout
    assert "Diagnosis status: correct" in result.stdout
    assert "Problem status: completed" in result.stdout
