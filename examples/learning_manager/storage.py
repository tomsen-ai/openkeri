import json
from pathlib import Path

from openkeri.schemas import LearningManagerState


class LearningManagerStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> LearningManagerState:
        if not self.path.exists():
            return LearningManagerState()

        raw = self.path.read_text(encoding="utf-8")
        return LearningManagerState.model_validate_json(raw)

    def save(self, state: LearningManagerState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            state.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
        )
        self.path.write_text(payload, encoding="utf-8")
