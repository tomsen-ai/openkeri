import os
import subprocess
import sys


def run_learning_manager(
    stdin: str,
    env: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "examples/learning_manager/main.py"],
        input=stdin,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )


def test_learning_manager_creates_completion_history_and_review(tmp_path) -> None:
    state_path = tmp_path / "learning_manager_state.json"
    env = os.environ.copy()
    env["OPENKERI_LEARNING_MANAGER_STATE"] = str(state_path)

    first = run_learning_manager(
        (
            "create-project\n"
            "30 天学算法\n"
            "掌握数组、双指针和哈希\n"
            "4\n"
            "数组,双指针,哈希\n"
            "complete task_001 记录左边界不回退\n"
            "q\n"
        ),
        env,
    )

    assert "openkeri Learning Manager" in first.stdout
    assert "Project: 30 天学算法" in first.stdout
    assert "task_001 [practice]" in first.stdout
    assert "Completed task_001: Practice 数组" in first.stdout
    assert "记录左边界不回退" in first.stdout

    second = run_learning_manager("history\nreview\nstatus\nq\n", env)

    assert "History for 30 天学算法" in second.stdout
    assert "task_completed [task_001]" in second.stdout
    assert "Review reminders" in second.stdout
    assert "task_003 [review]" in second.stdout
    assert "Tasks: 1 done, 8 open" in second.stdout
