from typing import Any

from pydantic import BaseModel, Field


class LearningTask(BaseModel):
    id: str
    title: str
    description: str
    task_type: str
    target_concepts: list[str] = Field(default_factory=list)
    difficulty: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
