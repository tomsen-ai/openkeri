from pydantic import BaseModel, Field


class SessionState(BaseModel):
    session_id: str
    current_problem_id: str | None = None
    current_phase: str = "working"
    recent_actions: list[str] = Field(default_factory=list)
    last_teaching_action: str | None = None
    hint_count: int = 0
    problem_status: str = "in_progress"
    last_diagnosis_status: str | None = None
    last_diagnosis_issue: str | None = None
    last_diagnosis_concept: str | None = None
    last_diagnosis_summary: str | None = None
    last_failed_case_input: str | None = None
    last_failed_case_expected: str | None = None
    last_failed_case_actual: str | None = None


class LearnerProfile(BaseModel):
    learner_id: str
    level: str | None = None
    goal: str | None = None
    preferred_language: str = "en"
    teaching_style: str = "hint_first"
    known_concepts: list[str] = Field(default_factory=list)
    weak_concepts: list[str] = Field(default_factory=list)
    common_mistakes: list[str] = Field(default_factory=list)


class RelatedHistoryItem(BaseModel):
    concept: str
    issue: str
    seen_count: int = 1
    last_seen_problem_id: str | None = None


class LearnerMemory(BaseModel):
    learner_profile: LearnerProfile
    related_history: list[RelatedHistoryItem] = Field(default_factory=list)


class MemoryContext(BaseModel):
    session_state: SessionState
    learner_memory: LearnerMemory
