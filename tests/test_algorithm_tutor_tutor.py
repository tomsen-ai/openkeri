import os
import subprocess
import sys


def test_algorithm_tutor_tutor_rule_based_submit_status_and_quit(tmp_path) -> None:
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

    stdin = f"2\n1\nsubmit {solution_path}\nstatus\nq\n"
    result = subprocess.run(
        [sys.executable, "examples/algorithm_tutor/tutor.py"],
        input=stdin,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Teacher: Rule-based" in result.stdout
    assert "Problem: Longest Substring Without Repeating Characters" in result.stdout
    assert "Turn 1" in result.stdout
    assert "Diagnosis: incorrect" in result.stdout
    assert "Issue: left_boundary_update_error" in result.stdout
    assert "Hint count: 1" in result.stdout
    assert "Goodbye." in result.stdout


def test_algorithm_tutor_tutor_deepseek_without_key_can_choose_rule_based() -> None:
    env = os.environ.copy()
    env.pop("OPENKERI_DEEPSEEK_API_KEY", None)
    env.pop("DEEPSEEK_API_KEY", None)

    result = subprocess.run(
        [sys.executable, "examples/algorithm_tutor/tutor.py"],
        input="1\n2\n1\nq\n",
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )

    assert "DeepSeek is not configured." in result.stdout
    assert "Teacher: Rule-based" in result.stdout
    assert "Goodbye." in result.stdout


def test_algorithm_tutor_tutor_can_switch_problem() -> None:
    result = subprocess.run(
        [sys.executable, "examples/algorithm_tutor/tutor.py"],
        input="2\n1\nproblems\nswitch valid_palindrome\nstatus\nq\n",
        check=True,
        capture_output=True,
        text=True,
    )

    assert "valid_palindrome - Valid Palindrome" in result.stdout
    assert "Switched to Valid Palindrome." in result.stdout
    assert "Problem: Valid Palindrome" in result.stdout


def test_algorithm_tutor_tutor_can_ask_question() -> None:
    result = subprocess.run(
        [sys.executable, "examples/algorithm_tutor/tutor.py"],
        input="2\n1\nask why does abba fail?\nstatus\nq\n",
        check=True,
        capture_output=True,
        text=True,
    )

    assert "ask <question>" in result.stdout
    assert "Turn 1" in result.stdout
    assert "Diagnosis: no_submission" in result.stdout
    assert "Action: hint" in result.stdout
    assert "Recent actions: asked_question" in result.stdout


def test_algorithm_tutor_tutor_ask_uses_latest_submission(tmp_path) -> None:
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

    stdin = f"2\n1\nsubmit {solution_path}\nask why does abba fail?\nstatus\nq\n"
    result = subprocess.run(
        [sys.executable, "examples/algorithm_tutor/tutor.py"],
        input=stdin,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Turn 2" in result.stdout
    assert "Diagnosis: incorrect" in result.stdout
    assert "Issue: left_boundary_update_error" in result.stdout
    assert "Action: explanation" in result.stdout
    assert "left boundary moves backward" in result.stdout
    assert "Recent actions: submitted_code, asked_question" in result.stdout
