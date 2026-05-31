from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

LearningProjectStatus = Literal["active", "paused", "completed"]
LearningTaskType = Literal["practice", "review", "summary", "project"]
LearningTaskStatus = Literal["todo", "doing", "done", "skipped"]
LearningHistoryEventType = Literal[
    "project_created",
    "plan_generated",
    "task_completed",
    "task_skipped",
    "task_reviewed",
]


class LearningProject(BaseModel):
    id: str
    title: str
    goal: str
    status: LearningProjectStatus = "active"
    start_date: date
    target_end_date: date
    focus_areas: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class LearningWorkItem(BaseModel):
    id: str
    project_id: str
    type: LearningTaskType
    title: str
    description: str
    status: LearningTaskStatus = "todo"
    priority: int = 3
    due_date: date
    estimated_minutes: int = 30
    tags: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    related_resources: list[str] = Field(default_factory=list)
    result: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
    review_after_days: int = 0
    source_task_id: str | None = None


class LearningPlanDay(BaseModel):
    date: date
    task_ids: list[str] = Field(default_factory=list)
    review_focus: list[str] = Field(default_factory=list)
    notes: str | None = None


class LearningPlan(BaseModel):
    id: str
    project_id: str
    time_horizon_days: int
    daily_capacity_minutes: int
    days: list[LearningPlanDay] = Field(default_factory=list)
    generated_at: datetime
    version: int = 1


class LearningHistoryEntry(BaseModel):
    id: str
    project_id: str
    task_id: str | None = None
    event_type: LearningHistoryEventType
    summary: str
    detail: str | None = None
    created_at: datetime
    tags: list[str] = Field(default_factory=list)


class LearningManagerState(BaseModel):
    project: LearningProject | None = None
    plan: LearningPlan | None = None
    tasks: list[LearningWorkItem] = Field(default_factory=list)
    history: list[LearningHistoryEntry] = Field(default_factory=list)
    active_task_id: str | None = None
