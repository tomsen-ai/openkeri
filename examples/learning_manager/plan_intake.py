from __future__ import annotations

import json
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field, ValidationError, model_validator

from openkeri.llm import LLMMessage

IntakeStatus = Literal["needs_choice", "ready"]
PlanIssueType = Literal[
    "missing_required_slot",
    "missing_optional_slot",
    "conflicting_preference",
    "unclear_output",
]
SlotName = Literal[
    "learning_subject",
    "target_outcome",
    "time_window",
    "available_rhythm",
    "learner_background",
    "preferred_style",
    "use_context",
]
BriefSectionKind = Literal[
    "context",
    "strategy",
    "time",
    "background",
    "output",
    "warning",
    "resources",
    "practice",
]
RouteType = Literal[
    "foundation_first",
    "project_first",
    "practice_first",
    "overview_first",
]

MAX_INTAKE_ROUNDS = 5
MIN_OPTIONAL_SLOTS = 2
REQUIRED_SLOTS: tuple[SlotName, ...] = ("learning_subject", "target_outcome")
OPTIONAL_SLOT_PRIORITY: tuple[SlotName, ...] = (
    "use_context",
    "learner_background",
    "time_window",
    "available_rhythm",
    "preferred_style",
)


class PlanIntakeClient(Protocol):
    def complete_json(self, messages: list[LLMMessage]) -> dict[str, Any]:
        ...


class PlanConstraints(BaseModel):
    duration_days: int
    daily_minutes: int
    total_minutes: int


class IntentSlots(BaseModel):
    learning_subject: str | None = None
    target_outcome: str | None = None
    time_window: str | None = None
    available_rhythm: str | None = None
    learner_background: str | None = None
    preferred_style: str | None = None
    use_context: str | None = None

    def filled_optional_slots(self) -> list[SlotName]:
        return [slot for slot in OPTIONAL_SLOT_PRIORITY if self.slot_value(slot)]

    def missing_optional_slots(self) -> list[SlotName]:
        return [slot for slot in OPTIONAL_SLOT_PRIORITY if not self.slot_value(slot)]

    def missing_required_slots(self) -> list[SlotName]:
        return [slot for slot in REQUIRED_SLOTS if not self.slot_value(slot)]

    def slot_value(self, slot: SlotName) -> str | None:
        value = getattr(self, slot)
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class IntentExtractionResponse(BaseModel):
    slots: IntentSlots
    notes: list[str] = Field(default_factory=list)


class PlanIntakeIssue(BaseModel):
    type: PlanIssueType
    slot: SlotName | None = None
    summary: str
    reason: str


class PlanIntakeChoice(BaseModel):
    id: str
    label: str
    description: str
    fills: dict[SlotName, str] = Field(default_factory=dict)


class PlanIntakeQuestion(BaseModel):
    id: str
    target_slot: SlotName
    title: str
    description: str
    choices: list[PlanIntakeChoice] = Field(min_length=2, max_length=4)


class PlanIntakeDecision(BaseModel):
    issue_type: PlanIssueType
    issue_summary: str
    question_id: str
    target_slot: SlotName
    choice_id: str
    label: str
    description: str
    fills: dict[SlotName, str] = Field(default_factory=dict)


class IntakeCompleteness(BaseModel):
    ready: bool
    reason: str
    missing_required: list[SlotName] = Field(default_factory=list)
    filled_optional: list[SlotName] = Field(default_factory=list)
    missing_optional: list[SlotName] = Field(default_factory=list)
    target_slot: SlotName | None = None
    forced_by_round_limit: bool = False


class BriefObjective(BaseModel):
    one_sentence: str
    outcome: str
    success_criteria: list[str] = Field(min_length=1, max_length=5)


class BriefScope(BaseModel):
    include: list[str] = Field(min_length=1, max_length=8)
    exclude: list[str] = Field(default_factory=list)
    light_touch: list[str] = Field(default_factory=list)


class BriefConstraints(BaseModel):
    time_window: str | None = None
    pace: str | None = None
    learner_background: str | None = None
    use_context: str | None = None


class BriefStrategy(BaseModel):
    route_type: RouteType
    rationale: str


class PlanPhaseSkeleton(BaseModel):
    phase_name: str
    focus: str
    estimated_child_count: int = Field(ge=1, le=6)


class BriefPreview(BaseModel):
    phases: list[PlanPhaseSkeleton] = Field(min_length=3, max_length=5)


class BriefSection(BaseModel):
    id: str
    title: str
    kind: BriefSectionKind
    summary: str
    bullets: list[str] = Field(default_factory=list)
    editable: bool = True


class PlanBriefDraft(BaseModel):
    title: str
    objective: BriefObjective
    scope: BriefScope
    constraints: BriefConstraints = Field(default_factory=BriefConstraints)
    strategy: BriefStrategy
    assumptions: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    preview: BriefPreview
    sections: list[BriefSection] = Field(min_length=2, max_length=5)


class PlanBrief(PlanBriefDraft):
    schedule: PlanConstraints
    slots: IntentSlots
    user_choices: list[PlanIntakeDecision] = Field(default_factory=list)

    def to_prompt_context(self) -> str:
        parts = [
            f"Plan title: {self.title}",
            f"Objective: {self.objective.one_sentence}",
            f"Outcome: {self.objective.outcome}",
            "Success criteria: " + "；".join(self.objective.success_criteria),
            "Include: " + "；".join(self.scope.include),
            f"Route type: {self.strategy.route_type}",
            f"Strategy rationale: {self.strategy.rationale}",
            f"Total default planning budget: {self.schedule.total_minutes} minutes",
        ]
        if self.scope.exclude:
            parts.append("Exclude: " + "；".join(self.scope.exclude))
        if self.scope.light_touch:
            parts.append("Light touch: " + "；".join(self.scope.light_touch))
        if self.assumptions:
            parts.append("Assumptions: " + "；".join(self.assumptions))
        if self.risks:
            parts.append("Risks: " + "；".join(self.risks))
        section_text = [
            f"{section.title}: {section.summary}" for section in self.sections
        ]
        if section_text:
            parts.append("Dynamic brief sections:\n" + "\n".join(section_text))
        return "\n".join(parts)


class PlanIntakeState(BaseModel):
    raw_intent: str
    duration_days: int
    daily_minutes: int
    time_is_default: bool = True
    notes: str = ""
    round: int = 0
    slots: IntentSlots = Field(default_factory=IntentSlots)
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


class PlanIntakeResult(BaseModel):
    status: IntakeStatus
    reason: str
    state: PlanIntakeState
    completeness: IntakeCompleteness
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
    raw_parts = [goal.strip()]
    for value in (background.strip(), intensity.strip(), preference.strip()):
        if value:
            raw_parts.append(value)
    state = PlanIntakeState(
        raw_intent="\n".join(raw_parts),
        duration_days=duration_days,
        daily_minutes=daily_minutes,
        time_is_default=time_is_default,
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
            target_slot=question.target_slot,
            choice_id=choice.id,
            label=choice.label,
            description=choice.description,
            fills=choice.fills,
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
    extracted_slots = complete_slot_extraction(client, state)
    next_state = state.model_copy(deep=True)
    next_state.slots = merge_slots(next_state.slots, extracted_slots)
    next_state.slots = apply_decision_fills(next_state.slots, next_state.decisions)

    completeness = evaluate_completeness(next_state)
    if completeness.ready:
        brief = complete_brief(client, next_state, completeness)
        next_state.pending_issue = None
        next_state.pending_question = None
        return PlanIntakeResult(
            status="ready",
            reason=completeness.reason,
            state=next_state,
            completeness=completeness,
            brief=brief,
        )

    issue = issue_for_completeness(completeness)
    question = complete_question(client, next_state, issue)
    next_state.pending_issue = issue
    next_state.pending_question = question
    return PlanIntakeResult(
        status="needs_choice",
        reason=completeness.reason,
        state=next_state,
        completeness=completeness,
        issue=issue,
        question=question,
    )


def complete_slot_extraction(
    client: PlanIntakeClient,
    state: PlanIntakeState,
) -> IntentSlots:
    response = client.complete_json(
        [
            LLMMessage(role="system", content=build_slot_extraction_system_prompt()),
            LLMMessage(role="user", content=build_state_prompt(state)),
        ]
    )
    try:
        return IntentExtractionResponse.model_validate(response).slots
    except ValidationError as exc:
        raise ValueError(f"LLM returned invalid intent slots: {exc}") from exc


def complete_question(
    client: PlanIntakeClient,
    state: PlanIntakeState,
    issue: PlanIntakeIssue,
) -> PlanIntakeQuestion:
    response = client.complete_json(
        [
            LLMMessage(role="system", content=build_question_system_prompt()),
            LLMMessage(
                role="user",
                content=json.dumps(
                    {
                        "state": state_prompt_payload(state),
                        "issue": issue.model_dump(mode="json"),
                        "output_language": "zh-CN",
                    },
                    ensure_ascii=False,
                ),
            ),
        ]
    )
    try:
        question = PlanIntakeQuestion.model_validate(response)
    except ValidationError as exc:
        raise ValueError(f"LLM returned invalid intake question: {exc}") from exc
    if question.target_slot != issue.slot:
        raise ValueError("LLM intake question target_slot must match requested slot")
    return question


def complete_brief(
    client: PlanIntakeClient,
    state: PlanIntakeState,
    completeness: IntakeCompleteness,
) -> PlanBrief:
    response = client.complete_json(
        [
            LLMMessage(role="system", content=build_brief_system_prompt()),
            LLMMessage(
                role="user",
                content=json.dumps(
                    {
                        "state": state_prompt_payload(state),
                        "completeness": completeness.model_dump(mode="json"),
                        "output_language": "zh-CN",
                    },
                    ensure_ascii=False,
                ),
            ),
        ]
    )
    try:
        draft = PlanBriefDraft.model_validate(response)
    except ValidationError as exc:
        raise ValueError(f"LLM returned invalid plan brief: {exc}") from exc
    return PlanBrief(
        **draft.model_dump(),
        schedule=state.constraints,
        slots=state.slots,
        user_choices=state.decisions,
    )


def evaluate_completeness(state: PlanIntakeState) -> IntakeCompleteness:
    missing_required = state.slots.missing_required_slots()
    filled_optional = state.slots.filled_optional_slots()
    missing_optional = state.slots.missing_optional_slots()

    if missing_required:
        target_slot = missing_required[0]
        return IntakeCompleteness(
            ready=False,
            reason=f"Missing required slot: {target_slot}.",
            missing_required=missing_required,
            filled_optional=filled_optional,
            missing_optional=missing_optional,
            target_slot=target_slot,
        )

    if len(filled_optional) >= MIN_OPTIONAL_SLOTS:
        return IntakeCompleteness(
            ready=True,
            reason="Required slots and enough adjustable slots are filled.",
            filled_optional=filled_optional,
            missing_optional=missing_optional,
        )

    if state.round >= MAX_INTAKE_ROUNDS:
        return IntakeCompleteness(
            ready=True,
            reason=(
                "Required slots are filled; optional slot collection hit the "
                "round limit."
            ),
            filled_optional=filled_optional,
            missing_optional=missing_optional,
            forced_by_round_limit=True,
        )

    target_slot = missing_optional[0] if missing_optional else None
    return IntakeCompleteness(
        ready=False,
        reason=(
            "Required slots are filled, but not enough adjustable slots are known."
        ),
        filled_optional=filled_optional,
        missing_optional=missing_optional,
        target_slot=target_slot,
    )


def issue_for_completeness(completeness: IntakeCompleteness) -> PlanIntakeIssue:
    if completeness.target_slot is None:
        raise ValueError("incomplete intake must include target_slot")

    if completeness.target_slot in REQUIRED_SLOTS:
        return PlanIntakeIssue(
            type="missing_required_slot",
            slot=completeness.target_slot,
            summary=f"Need {slot_label(completeness.target_slot)} before planning.",
            reason=(
                "This field changes the whole learning route, so the plan should "
                "not continue without it."
            ),
        )

    return PlanIntakeIssue(
        type="missing_optional_slot",
        slot=completeness.target_slot,
        summary=(
            "Need one more adjustable detail: "
            f"{slot_label(completeness.target_slot)}."
        ),
        reason=(
            "The core goal is clear, but one more detail will make the brief "
            "less generic."
        ),
    )


def merge_slots(existing: IntentSlots, extracted: IntentSlots) -> IntentSlots:
    payload = existing.model_dump()
    for slot in (*REQUIRED_SLOTS, *OPTIONAL_SLOT_PRIORITY):
        value = extracted.slot_value(slot)
        if value:
            payload[slot] = value
    return IntentSlots.model_validate(payload)


def apply_decision_fills(
    slots: IntentSlots,
    decisions: list[PlanIntakeDecision],
) -> IntentSlots:
    payload = slots.model_dump()
    for decision in decisions:
        for slot, value in decision.fills.items():
            stripped = value.strip()
            if stripped:
                payload[slot] = stripped
        if not decision.fills:
            payload[decision.target_slot] = decision.description
    return IntentSlots.model_validate(payload)


def build_system_prompt() -> str:
    """Compatibility helper used by tests and docs."""
    return "\n\n".join(
        [
            build_slot_extraction_system_prompt(),
            build_question_system_prompt(),
            build_brief_system_prompt(),
        ]
    )


def build_slot_extraction_system_prompt() -> str:
    return """
You extract structured intent slots from a user's raw learning intent and prior
intake choices.

Return only one valid JSON object. Do not include markdown.

Rules:
- Preserve uncertainty by leaving a slot null when the user did not say it.
- Do not invent exact time, pace, or background.
- Natural time hints inside the raw_intent, such as "30 天", "两周", "每天半小时",
  or "晚上有点时间", should be extracted into time_window or available_rhythm.
- Prior choices and notes may fill slots if they clearly state a route,
  background, use context, or style.
- Output language should follow the user's language.

Slots:
- learning_subject: what the user wants to learn.
- target_outcome: what the user wants to be able to do or produce.
- time_window: overall window such as "30 天" or "两周", if stated.
- available_rhythm: recurring availability such as "每天半小时", if stated.
- learner_background: current level or prior experience.
- preferred_style: route preference such as project-first, practice-first,
  systematic, overview-first, exam/interview sprint.
- use_context: why or where the skill will be used, such as work, exam, hobby,
  interview, concrete project, or personal need.

JSON schema:
{
  "slots": {
    "learning_subject": "string or null",
    "target_outcome": "string or null",
    "time_window": "string or null",
    "available_rhythm": "string or null",
    "learner_background": "string or null",
    "preferred_style": "string or null",
    "use_context": "string or null"
  },
  "notes": ["short extraction note"]
}
""".strip()


def build_question_system_prompt() -> str:
    return """
You generate exactly one dynamic intake question for the requested target slot.

Return only one valid JSON object. Do not include markdown.

Rules:
- Ask only about the provided issue.slot.
- The question and choices must be specific to the raw_intent and known slots.
- Do not ask for exact time if the requested slot is not time-related.
- Choices should be mutually exclusive enough to change the plan.
- Each choice must include a fills object that fills the target slot and may
  fill other slots only when the choice clearly implies them.
- Provide 2 to 4 choices.

JSON schema:
{
  "id": "stable_question_id",
  "target_slot": "one requested slot name",
  "title": "direct question",
  "description": "why this matters",
  "choices": [
    {
      "id": "stable_choice_id",
      "label": "short label",
      "description": "what changes if selected",
      "fills": {"target_slot_name": "slot value"}
    }
  ]
}
""".strip()


def build_brief_system_prompt() -> str:
    return """
You create a dynamic plan brief after the intake slots pass the rule-based
completeness gate.

Return only one valid JSON object. Do not include markdown.

The brief has a fixed core plus dynamic sections.

Core rules:
- objective, scope, strategy, assumptions, risks, and preview are required.
- The brief should reflect the raw_intent and filled slots, not a generic plan.
- If optional slots are missing because the round limit was reached, use
  assumptions instead of pretending the user provided them.
- The preview must contain 3 to 5 phase skeleton entries.
- Keep scope realistic. Do not promise mastery, passing exams, or job outcomes.
- Dynamic sections should be chosen from what matters for this specific goal:
  context, strategy, time, background, output, warning, resources, practice.
- Return 2 to 5 sections.

JSON schema:
{
  "title": "short brief title",
  "objective": {
    "one_sentence": "clear narrowed objective",
    "outcome": "realistic expected outcome",
    "success_criteria": ["observable success criterion"]
  },
  "scope": {
    "include": ["included topic or activity"],
    "exclude": ["excluded topic or activity"],
    "light_touch": ["light-touch topic"]
  },
  "constraints": {
    "time_window": "string or null",
    "pace": "string or null",
    "learner_background": "string or null",
    "use_context": "string or null"
  },
  "strategy": {
    "route_type": "foundation_first|project_first|practice_first|overview_first",
    "rationale": "why this route fits"
  },
  "assumptions": ["important assumption"],
  "risks": ["risk or tradeoff"],
  "preview": {
    "phases": [
      {
        "phase_name": "phase name",
        "focus": "phase focus",
        "estimated_child_count": 3
      }
    ]
  },
  "sections": [
    {
      "id": "stable_section_id",
      "title": "section title",
      "kind": "context|strategy|time|background|output|warning|resources|practice",
      "summary": "short section summary",
      "bullets": ["optional bullet"],
      "editable": true
    }
  ]
}
""".strip()


def build_state_prompt(state: PlanIntakeState) -> str:
    return json.dumps(state_prompt_payload(state), ensure_ascii=False)


def state_prompt_payload(state: PlanIntakeState) -> dict[str, Any]:
    return {
        "raw_intent": state.raw_intent,
        "time_is_default": state.time_is_default,
        "time_note": (
            "No separate hard schedule control was provided. Extract time only "
            "from the raw_intent or prior choices."
            if state.time_is_default
            else "The caller provided default duration/day values separately."
        ),
        "default_duration_days": state.constraints.duration_days,
        "default_daily_minutes": state.constraints.daily_minutes,
        "notes": state.notes,
        "round": state.round,
        "max_rounds": MAX_INTAKE_ROUNDS,
        "min_optional_slots": MIN_OPTIONAL_SLOTS,
        "current_slots": state.slots.model_dump(mode="json"),
        "required_slots": list(REQUIRED_SLOTS),
        "optional_slot_priority": list(OPTIONAL_SLOT_PRIORITY),
        "conversation_history": [
            decision.model_dump(mode="json") for decision in state.decisions
        ],
        "output_language": "zh-CN",
    }


def slot_label(slot: SlotName) -> str:
    labels = {
        "learning_subject": "learning subject",
        "target_outcome": "target outcome",
        "time_window": "time window",
        "available_rhythm": "available rhythm",
        "learner_background": "learner background",
        "preferred_style": "preferred style",
        "use_context": "use context",
    }
    return labels[slot]
