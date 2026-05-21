from typing import Protocol

from openkeri.schemas import CurrentInput, Evidence


class EvidenceCollector(Protocol):
    def collect(self, current_input: CurrentInput) -> Evidence:
        """Collect evidence for one teaching turn."""
        ...
