from pydantic import BaseModel, Field

from openkeri.tasks.bundle import LearningTaskBundle
from openkeri.tasks.errors import DuplicateLearningTaskError, LearningTaskNotFoundError


class LearningTaskRegistry(BaseModel):
    bundles: dict[str, LearningTaskBundle] = Field(default_factory=dict)

    def register(self, bundle: LearningTaskBundle) -> None:
        task_id = bundle.task.id
        if task_id in self.bundles:
            raise DuplicateLearningTaskError(
                f"Learning task {task_id!r} is already registered."
            )
        self.bundles[task_id] = bundle

    def get(self, task_id: str) -> LearningTaskBundle:
        bundle = self.bundles.get(task_id)
        if bundle is None:
            raise LearningTaskNotFoundError(
                f"Learning task {task_id!r} is not registered."
            )
        return bundle

    def list_tasks(self) -> list[LearningTaskBundle]:
        return list(self.bundles.values())
