from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

LearningProjectStatus = Literal["active", "paused", "completed", "archived"]
LearningTaskType = Literal[
    "intake",
    "plan",
    "learn",
    "practice",
    "review",
    "reflection",
    "summary",
    "project",
    "checkpoint",
]
LearningTaskStatus = Literal[
    "locked",
    "ready",
    "active",
    "done",
    "review_due",
    "skipped",
    "blocked",
    "deferred",
    "todo",
    "doing",
]
LearningHistoryEventType = Literal[
    "project_created",
    "plan_generated",
    "plan_revised",
    "task_completed",
    "task_skipped",
    "task_blocked",
    "task_reviewed",
    "resource_added",
    "artifact_added",
    "reflection_recorded",
]
KnowledgeResourceType = Literal[
    "article",
    "book",
    "video",
    "course",
    "paper",
    "note",
    "artifact",
    "link",
    "other",
]
KnowledgeResourceStatus = Literal["candidate", "active", "done", "archived"]
LearningArtifactType = Literal[
    "note",
    "summary",
    "solution",
    "project",
    "mind_map",
    "code",
    "other",
]
PlanRevisionReason = Literal[
    "scope_changed",
    "progress_update",
    "blocked",
    "deadline_changed",
    "manual_adjustment",
]


class LearningGoal(BaseModel):
    id: str
    title: str
    description: str
    target_outcomes: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class LearningProject(BaseModel):
    id: str
    goal_id: str | None = None
    title: str
    goal: str
    status: LearningProjectStatus = "active"
    start_date: date
    target_end_date: date
    focus_areas: list[str] = Field(default_factory=list)
    knowledge_area_ids: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class KnowledgeArea(BaseModel):
    id: str
    project_id: str
    title: str
    description: str | None = None
    parent_id: str | None = None
    tags: list[str] = Field(default_factory=list)


class KnowledgeResourceRef(BaseModel):
    id: str
    project_id: str
    title: str
    type: KnowledgeResourceType = "other"
    uri: str | None = None
    source: str | None = None
    status: KnowledgeResourceStatus = "candidate"
    area_ids: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class LearningWorkItem(BaseModel):
    id: str
    project_id: str
    type: LearningTaskType
    title: str
    description: str
    status: LearningTaskStatus = "locked"
    stage_id: str | None = None
    stage_title: str | None = None
    node_order: int = 0
    priority: int = 3
    due_date: date
    estimated_minutes: int = 30
    tags: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    related_resources: list[str] = Field(default_factory=list)
    knowledge_area_ids: list[str] = Field(default_factory=list)
    resource_ids: list[str] = Field(default_factory=list)
    artifact_ids: list[str] = Field(default_factory=list)
    result: str | None = None
    difficulty: str | None = None
    minutes_spent: int | None = None
    created_at: datetime
    completed_at: datetime | None = None
    review_after_days: int = 0
    source_task_id: str | None = None


class LearningArtifact(BaseModel):
    id: str
    project_id: str
    title: str
    type: LearningArtifactType = "other"
    uri: str | None = None
    summary: str | None = None
    task_ids: list[str] = Field(default_factory=list)
    resource_ids: list[str] = Field(default_factory=list)
    knowledge_area_ids: list[str] = Field(default_factory=list)
    created_at: datetime


class LearningReflection(BaseModel):
    id: str
    project_id: str
    task_id: str | None = None
    summary: str
    learned: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    created_at: datetime


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


class PlanRevision(BaseModel):
    id: str
    project_id: str
    plan_id: str
    from_version: int
    to_version: int
    reason: PlanRevisionReason
    summary: str
    affected_task_ids: list[str] = Field(default_factory=list)
    created_at: datetime


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
    goals: list[LearningGoal] = Field(default_factory=list)
    project: LearningProject | None = None
    plan: LearningPlan | None = None
    tasks: list[LearningWorkItem] = Field(default_factory=list)
    knowledge_areas: list[KnowledgeArea] = Field(default_factory=list)
    resources: list[KnowledgeResourceRef] = Field(default_factory=list)
    artifacts: list[LearningArtifact] = Field(default_factory=list)
    reflections: list[LearningReflection] = Field(default_factory=list)
    revisions: list[PlanRevision] = Field(default_factory=list)
    history: list[LearningHistoryEntry] = Field(default_factory=list)
    active_task_id: str | None = None
