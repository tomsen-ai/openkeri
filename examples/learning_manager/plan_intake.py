from __future__ import annotations

import json
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field, ValidationError, model_validator

from openkeri.llm import LLMMessage

IntakeStatus = Literal["needs_choice", "ready"]
RiskLevel = Literal["feasible", "tight", "unrealistic"]
PlanIssueType = Literal[
    "feasibility_mismatch",
    "scope_too_broad",
    "missing_constraint",
    "conflicting_preference",
    "unclear_output",
]

MAX_INTAKE_ROUNDS = 5


class PlanIntakeClient(Protocol):
    def complete_json(self, messages: list[LLMMessage]) -> dict[str, Any]:
        ...


class PlanConstraints(BaseModel):
    duration_days: int
    daily_minutes: int
    total_minutes: int


class PlanIntakeIssue(BaseModel):
    type: PlanIssueType
    summary: str
    reason: str


class PlanIntakeChoice(BaseModel):
    id: str
    label: str
    description: str


class PlanIntakeQuestion(BaseModel):
    id: str
    title: str
    description: str
    choices: list[PlanIntakeChoice] = Field(min_length=2, max_length=4)


class PlanIntakeDecision(BaseModel):
    issue_type: PlanIssueType
    issue_summary: str
    question_id: str
    choice_id: str
    label: str
    description: str


class PlanBriefUserSummary(BaseModel):
    headline: str
    why: str
    focus: str
    not_included: str = ""
    outcome: str


class PlanPhaseSkeleton(BaseModel):
    phase_name: str
    focus: str
    estimated_child_count: int = Field(ge=1, le=6)


class PlanBriefDraft(BaseModel):
    title: str
    refined_goal: str
    scope: str
    excluded_scope: str = ""
    strategy: str
    recommended_pace: str = ""
    expected_outcome: str
    risk_level: RiskLevel
    assumptions: list[str] = Field(default_factory=list)
    user_summary: PlanBriefUserSummary
    skeleton: list[PlanPhaseSkeleton] = Field(default_factory=list)


class PlanBrief(PlanBriefDraft):
    constraints: PlanConstraints
    user_choices: list[PlanIntakeDecision] = Field(default_factory=list)

    def to_prompt_context(self) -> str:
        parts = [
            f"Plan title: {self.title}",
            f"Refined goal: {self.refined_goal}",
            f"Scope: {self.scope}",
            f"Strategy: {self.strategy}",
            f"Recommended pace: {self.recommended_pace}",
            f"Expected outcome: {self.expected_outcome}",
            f"Total available time: {self.constraints.total_minutes} minutes",
        ]
        if self.excluded_scope:
            parts.append(f"Excluded or light-touch scope: {self.excluded_scope}")
        if self.assumptions:
            parts.append("Assumptions: " + "；".join(self.assumptions))
        return "\n".join(parts)


class PlanIntakeState(BaseModel):
    goal: str
    duration_days: int
    daily_minutes: int
    time_is_default: bool = True
    background: str = ""
    intensity: str = ""
    preference: str = ""
    notes: str = ""
    round: int = 0
    decisions: list[PlanIntakeDecision] = Field(default_factory=list)
    pending_issue: PlanIntakeIssue | None = None
    pending_question: PlanIntakeQuestion | None = None

    @property
    def constraints(self) -> PlanConstraints:
        duration_days = max(0, self.duration_days)
        daily_minutes = max(0, self.daily_minutes)
        return PlanConstraints(
            duration_days=duration_days,
            daily_minutes=daily_minutes,
            total_minutes=duration_days * daily_minutes,
        )


class PlanIntakeLLMResponse(BaseModel):
    status: IntakeStatus
    reason: str
    issue: PlanIntakeIssue | None = None
    question: PlanIntakeQuestion | None = None
    brief: PlanBriefDraft | None = None

    @model_validator(mode="after")
    def validate_status_payload(self) -> PlanIntakeLLMResponse:
        if self.status == "needs_choice":
            if self.issue is None:
                raise ValueError("needs_choice response must include an issue")
            if self.question is None:
                raise ValueError("needs_choice response must include a question")
        if self.status == "ready" and self.brief is None:
            raise ValueError("ready response must include a brief")
        return self


class PlanIntakeResult(BaseModel):
    status: IntakeStatus
    reason: str
    state: PlanIntakeState
    issue: PlanIntakeIssue | None = None
    question: PlanIntakeQuestion | None = None
    brief: PlanBrief | None = None

    @model_validator(mode="after")
    def validate_status_payload(self) -> PlanIntakeResult:
        if self.status == "needs_choice":
            if self.issue is None:
                raise ValueError("needs_choice result must include an issue")
            if self.question is None:
                raise ValueError("needs_choice result must include a question")
        if self.status == "ready" and self.brief is None:
            raise ValueError("ready result must include a brief")
        return self


def start_plan_intake(
    client: PlanIntakeClient,
    *,
    goal: str,
    duration_days: int,
    daily_minutes: int,
    time_is_default: bool = True,
    background: str = "",
    intensity: str = "",
    preference: str = "",
) -> PlanIntakeResult:
    state = PlanIntakeState(
        goal=goal.strip(),
        duration_days=duration_days,
        daily_minutes=daily_minutes,
        time_is_default=time_is_default,
        background=background.strip(),
        intensity=intensity.strip(),
        preference=preference.strip(),
    )
    return evaluate_plan_intake(client, state)


def answer_plan_intake(
    client: PlanIntakeClient,
    state: PlanIntakeState,
    *,
    choice_id: str,
    notes: str = "",
) -> PlanIntakeResult:
    next_state = state.model_copy(deep=True)
    issue = next_state.pending_issue
    question = next_state.pending_question
    if issue is None or question is None:
        raise ValueError("intake state has no pending question")

    choice = next((item for item in question.choices if item.id == choice_id), None)
    if choice is None:
        raise ValueError(f"unknown intake choice: {choice_id}")

    next_state.decisions.append(
        PlanIntakeDecision(
            issue_type=issue.type,
            issue_summary=issue.summary,
            question_id=question.id,
            choice_id=choice.id,
            label=choice.label,
            description=choice.description,
        )
    )
    next_state.round += 1
    next_state.pending_issue = None
    next_state.pending_question = None
    next_state.notes = notes.strip()
    return evaluate_plan_intake(client, next_state)


def evaluate_plan_intake(
    client: PlanIntakeClient,
    state: PlanIntakeState,
) -> PlanIntakeResult:
    force_ready = state.round >= MAX_INTAKE_ROUNDS
    response = complete_intake_response(client, state, force_ready=force_ready)
    if force_ready and response.status != "ready":
        raise ValueError("LLM intake response must be ready after max rounds")
    return build_result_from_response(state, response)


def complete_intake_response(
    client: PlanIntakeClient,
    state: PlanIntakeState,
    *,
    force_ready: bool,
) -> PlanIntakeLLMResponse:
    response = client.complete_json(
        [
            LLMMessage(role="system", content=build_system_prompt()),
            LLMMessage(
                role="user",
                content=build_user_prompt(state=state, force_ready=force_ready),
            ),
        ]
    )
    try:
        return PlanIntakeLLMResponse.model_validate(response)
    except ValidationError as exc:
        raise ValueError(f"LLM returned an invalid intake response: {exc}") from exc


def build_result_from_response(
    state: PlanIntakeState,
    response: PlanIntakeLLMResponse,
) -> PlanIntakeResult:
    next_state = state.model_copy(deep=True)
    if response.status == "needs_choice":
        next_state.pending_issue = response.issue
        next_state.pending_question = response.question
        return PlanIntakeResult(
            status="needs_choice",
            reason=response.reason,
            state=next_state,
            issue=response.issue,
            question=response.question,
        )

    next_state.pending_issue = None
    next_state.pending_question = None
    if response.brief is None:
        raise ValueError("ready response must include a brief")
    return PlanIntakeResult(
        status="ready",
        reason=response.reason,
        state=next_state,
        brief=PlanBrief(
            **response.brief.model_dump(),
            constraints=next_state.constraints,
            user_choices=next_state.decisions,
        ),
    )


def build_system_prompt() -> str:
    return """
You are a learning-plan advisor. Your job is to help the user converge from a
rough learning goal into a concrete, actionable plan draft.

Return only one valid JSON object. Do not include markdown.

Core behavior:
- Your job is to understand three things before generating the plan brief:
  1) WHY the user wants to learn this (motivation, background, prior knowledge)
  2) HOW MUCH they can realistically commit (time, intensity, pace preference)
  3) WHAT specific scope to cover (which topics/skills to include or exclude)
- You may ask the user at most 5 rounds of questions before producing the final
  plan brief. Each round should present 2-4 contextual options, OR ask the user
  to clarify their situation if the options cannot cover it.
- The options must be specific to the user's goal AND reveal background context.
  Bad: "core sprint / systematic prep / overview map" (generic for everyone).
  Good: "quick scripting for automation" / "systematic fundamentals for career
  switch" / "build a data-analysis mini-project" (specific to Python learners).
  Each option should implicitly capture WHY and HOW MUCH.
- If the user provides notes/extra context, use that information to skip
  unnecessary questions or to shape better options.
- You decide when you have enough information to return "ready". If the user's
  goal is already clear and specific, return "ready" on the first round.
- If the user's goal is vague, ask a clarifying question that reveals their
  motivation or background first, before asking about scope or intensity.
- If the user provided no hard time constraint (time_is_default=true), do NOT
  judge their time as insufficient. Treat time as flexible and focus on what
  kind of learning route fits their goal best.
- Only use "feasibility_mismatch" when the user explicitly states a hard
  deadline or fixed availability that is physically impossible.
- Do not promise impossible outcomes.
- Do not generate the full plan graph here. Only return the intake status or
  the PlanBrief.

Round rules:
- Track which round you are on via the "round" field in the user prompt.
- If force_ready is true (max rounds reached), you MUST return status "ready"
  with a conservative but useful PlanBrief.
- Otherwise, you may return either "needs_choice" (to ask another question) or
  "ready" (if the goal is clear enough).

Brief rules:
- A ready response must include a complete PlanBrief.
- The brief must include a "skeleton" array with 3-5 phase entries. Each entry
  has: phase_name (string), focus (string), estimated_child_count (1-6).
- The skeleton gives the user a preview of the plan structure before the full
  graph is generated.

Allowed issue types for needs_choice:
- feasibility_mismatch: only when hard constraints are physically impossible.
- scope_too_broad: the goal is too broad and needs a narrower target.
- missing_constraint: a necessary constraint is missing.
- conflicting_preference: user constraints/preferences conflict.
- unclear_output: the plan can proceed only after choosing a clearer output.

JSON schema for needs_choice:
{
  "status": "needs_choice",
  "reason": "short reason",
  "issue": {
    "type": "unclear_output",
    "summary": "one sentence issue",
    "reason": "specific explanation grounded in the user's inputs"
  },
  "question": {
    "id": "stable_question_id",
    "title": "direct question title",
    "description": "why the user must choose",
    "choices": [
      {
        "id": "stable_choice_id",
        "label": "short label",
        "description": "what changes if selected"
      }
    ]
  }
}

JSON schema for ready:
{
  "status": "ready",
  "reason": "short reason",
  "brief": {
    "title": "short plan title",
    "refined_goal": "honest narrowed goal",
    "scope": "what this plan will cover",
    "excluded_scope": "what this plan will not cover or only lightly touch",
    "strategy": "short strategy id or phrase",
    "recommended_pace": "suggested rhythm, not a hard requirement",
    "expected_outcome": "realistic outcome, with no false promise",
    "risk_level": "feasible|tight|unrealistic",
    "assumptions": ["important assumption"],
    "user_summary": {
      "headline": "direct user-facing headline",
      "why": "why this plan is shaped this way",
      "focus": "main focus",
      "not_included": "excluded or light-touch parts",
      "outcome": "realistic expected result"
    },
    "skeleton": [
      {
        "phase_name": "phase name",
        "focus": "what this phase covers",
        "estimated_child_count": 3
      }
    ]
  }
}
""".strip()


def build_user_prompt(*, state: PlanIntakeState, force_ready: bool) -> str:
    conversation = []
    for d in state.decisions:
        conversation.append(
            {
                "advisor_question": d.issue_summary,
                "user_choice": d.label,
                "user_choice_description": d.description,
            }
        )
    payload: dict[str, Any] = {
        "goal": state.goal,
        "time_is_default": state.time_is_default,
        "time_note": (
            "No hard schedule was provided. Do not judge feasibility based on time. "
            "Suggest a flexible recommended pace and focus on choosing the right "
            "learning route."
            if state.time_is_default
            else "The user provided these time constraints."
        ),
        "background": state.background,
        "intensity": state.intensity,
        "preference": state.preference,
        "user_notes": state.notes,
        "round": state.round,
        "max_rounds": MAX_INTAKE_ROUNDS,
        "rounds_remaining": MAX_INTAKE_ROUNDS - state.round,
        "force_ready": force_ready,
        "conversation_history": conversation,
        "output_language": "zh-CN",
    }
    if not state.time_is_default:
        payload.update(
            {
                "duration_days": state.constraints.duration_days,
                "daily_minutes": state.constraints.daily_minutes,
                "total_minutes": state.constraints.total_minutes,
                "total_hours": round(state.constraints.total_minutes / 60, 2),
            }
        )
    return json.dumps(
        payload,
        ensure_ascii=False,
    )
