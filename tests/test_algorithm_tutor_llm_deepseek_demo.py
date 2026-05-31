import os
import subprocess
import sys


def test_algorithm_tutor_llm_deepseek_demo_exits_without_api_key() -> None:
    env = os.environ.copy()
    env.pop("OPENKERI_DEEPSEEK_API_KEY", None)

    result = subprocess.run(
        [sys.executable, "examples/algorithm_tutor/llm_deepseek_demo.py"],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )

    assert "Set OPENKERI_DEEPSEEK_API_KEY to run this demo." in result.stdout
