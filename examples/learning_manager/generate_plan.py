from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if SRC.exists():
    sys.path.insert(0, str(SRC))

from plan_graph_generator import generate_plan_graph_draft  # noqa: E402

from openkeri.llm import DeepSeekClient, DeepSeekClientError  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a learning plan graph.")
    parser.add_argument("goal", help="Learning goal, for example: 30 天准备算法面试")
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--minutes", type=int, default=25)
    parser.add_argument("--preference", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        client = replace(DeepSeekClient.from_env(), max_tokens=4096, temperature=0.35)
        draft = generate_plan_graph_draft(
            client,
            goal=args.goal,
            duration_days=args.days,
            daily_minutes=args.minutes,
            preference=args.preference,
        )
    except (ValueError, DeepSeekClientError) as error:
        print(f"Plan generation failed: {error}", file=sys.stderr)
        return 1

    print(json.dumps(draft.model_dump(mode="json"), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
