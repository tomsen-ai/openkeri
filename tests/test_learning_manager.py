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


def test_learning_manager_stage_route_unlocks_next_node(tmp_path) -> None:
    state_path = tmp_path / "learning_manager_state.json"
    env = os.environ.copy()
    env["OPENKERI_LEARNING_MANAGER_STATE"] = str(state_path)

    first = run_learning_manager(
        (
            "create-project 我想用4天系统学算法\n"
            "\n"
            "map\n"
            "complete node_001 normal 25 记录数组遍历\n"
            "today\n"
            "q\n"
        ),
        env,
    )

    assert "openkeri Learning Manager" in first.stdout
    assert "Suggested route:" in first.stdout
    assert "Created project: 算法学习计划" in first.stdout
    assert "Main lesson:" in first.stdout
    assert "node_001 数组" in first.stdout
    assert "stage_001 基础热身" in first.stdout
    assert "● node_001 [practice] 数组 - ready" in first.stdout
    assert "○ node_002 [practice] 哈希 - locked" in first.stdout
    assert "Completed node_001: 数组" in first.stdout
    assert "Difficulty: normal, minutes: 25" in first.stdout
    assert "Unlocked node_002: 哈希" in first.stdout
    assert "node_002 哈希" in first.stdout

    second = run_learning_manager("map\nhistory\nstatus\nq\n", env)

    assert "✓ node_001 [practice] 数组 - done" in second.stdout
    assert "● node_002 [practice] 哈希 - ready" in second.stdout
    assert "History for 算法学习计划" in second.stdout
    assert "task_completed [node_001]" in second.stdout
    assert "Progress: 1/" in second.stdout
    assert "Study minutes: 25" in second.stdout
    assert "Next: node_002 - 哈希" in second.stdout
