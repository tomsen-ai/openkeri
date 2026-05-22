import subprocess
import sys


def test_algorithm_tutor_interactive_runs_with_file_paths(tmp_path) -> None:
    solution_path = tmp_path / "solution.py"
    solution_path.write_text(
        """
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
""",
        encoding="utf-8",
    )

    stdin = f"1\n{solution_path}\n{solution_path}\n{solution_path}\nq\n"
    result = subprocess.run(
        [sys.executable, "examples/algorithm_tutor/interactive.py"],
        input=stdin,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Turn 1" in result.stdout
    assert "Turn 3" in result.stdout
    assert "Teaching action: explanation" in result.stdout
    assert "Goodbye." in result.stdout


def test_algorithm_tutor_interactive_can_run_valid_palindrome() -> None:
    stdin = "2\nexamples/algorithm_tutor/solutions/palindrome_correct.py\nq\n"
    result = subprocess.run(
        [sys.executable, "examples/algorithm_tutor/interactive.py"],
        input=stdin,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Problem: Valid Palindrome" in result.stdout
    assert "Diagnosis status: correct" in result.stdout
    assert "Goodbye." in result.stdout
