from typing import Protocol

from openkeri.schemas import TeacherOutput, TeachingContext


class TeacherAgent(Protocol):
    def respond(self, context: TeachingContext) -> TeacherOutput:
        """Produce a diagnosis and teaching action for one teaching turn."""
        ...
