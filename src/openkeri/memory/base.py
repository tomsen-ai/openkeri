from typing import Protocol

from openkeri.schemas import LearningEvent, MemoryContext


class MemoryStore(Protocol):
    def get_context(
        self,
        learner_id: str,
        session_id: str,
        problem_id: str | None = None,
    ) -> MemoryContext:
        """Return the memory context for one teaching turn."""
        ...

    def record_event(self, event: LearningEvent) -> MemoryContext:
        """Record one learning event and return the updated memory context."""
        ...
