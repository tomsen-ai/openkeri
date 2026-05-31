import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if SRC.exists():
    sys.path.insert(0, str(SRC))

from app import LearningManagerApp  # noqa: E402


def main() -> None:
    LearningManagerApp().run()


if __name__ == "__main__":
    main()
