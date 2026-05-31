from typing import Any, TypeVar

from pydantic import BaseModel, Field

from openkeri.schemas import LearningTask
from openkeri.tasks.errors import LearningTaskResourceNotFoundError

ResourceT = TypeVar("ResourceT")


class LearningTaskBundle(BaseModel):
    task: LearningTask
    resources: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def resource(self, name: str, expected_type: type[ResourceT]) -> ResourceT:
        value = self.resources.get(name)
        if value is None:
            raise LearningTaskResourceNotFoundError(
                f"Task {self.task.id!r} has no resource named {name!r}."
            )
        if not isinstance(value, expected_type):
            raise TypeError(
                f"Task {self.task.id!r} resource {name!r} must be "
                f"{expected_type.__name__}."
            )
        return value
