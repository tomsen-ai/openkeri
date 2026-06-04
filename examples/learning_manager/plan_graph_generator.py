from __future__ import annotations

import json
import re
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from openkeri.llm import LLMMessage

PlanNodeKind = Literal[
    "goal",
    "phase",
    "concept",
    "task",
    "practice",
    "review",
    "project",
    "checkpoint",
    "resource",
]

PlanNodeStatus = Literal["not_started", "in_progress", "done"]


class PlanGraphClient(Protocol):
    def complete_json(self, messages: list[LLMMessage]) -> dict[str, Any]:
        ...


class PlanNodePosition(BaseModel):
    x: float
    y: float


class PlanGraphNode(BaseModel):
    id: str
    title: str
    kind: PlanNodeKind
    description: str
    estimated_minutes: int = Field(default=25, ge=0, le=2000)
    group: str | None = None
    status: PlanNodeStatus = "not_started"
    position: PlanNodePosition | None = None

    @field_validator("id")
    @classmethod
    def validate_node_id(cls, value: str) -> str:
        if not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_-]*", value):
            raise ValueError(
                "node id must start with a letter and use letters, numbers, _ or -"
            )
        return value

    @field_validator("estimated_minutes", mode="before")
    @classmethod
    def clamp_estimated_minutes(cls, value: Any) -> int:
        if value is None:
            return 25
        minutes = int(value)
        return max(5, min(minutes, 480))


class PlanGraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str | None = None

    @model_validator(mode="after")
    def validate_not_self_loop(self) -> PlanGraphEdge:
        if self.source == self.target:
            raise ValueError("edge source and target must be different")
        return self


class PlanGraphDraft(BaseModel):
    title: str
    summary: str
    nodes: list[PlanGraphNode] = Field(min_length=8, max_length=18)
    edges: list[PlanGraphEdge] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_edges_reference_nodes(self) -> PlanGraphDraft:
        node_ids = {node.id for node in self.nodes}
        if len(node_ids) != len(self.nodes):
            raise ValueError("node ids must be unique")
        for edge in self.edges:
            if edge.source not in node_ids:
                raise ValueError(
                    f"edge {edge.id} references missing source {edge.source}"
                )
            if edge.target not in node_ids:
                raise ValueError(
                    f"edge {edge.id} references missing target {edge.target}"
                )
        return self

    @model_validator(mode="after")
    def validate_single_project_structure(self) -> PlanGraphDraft:
        goal_nodes = [node for node in self.nodes if node.kind == "goal"]
        if len(goal_nodes) != 1:
            raise ValueError("plan graph must contain exactly one goal node")

        phase_nodes = [node for node in self.nodes if node.kind == "phase"]
        if not 3 <= len(phase_nodes) <= 5:
            raise ValueError("plan graph must contain 3 to 5 phase nodes")

        phase_ids = {node.id for node in phase_nodes}
        child_by_phase = {phase_id: 0 for phase_id in phase_ids}
        incident_ids = set()
        for edge in self.edges:
            incident_ids.add(edge.source)
            incident_ids.add(edge.target)
            if edge.source in phase_ids and edge.target not in phase_ids:
                child_by_phase[edge.source] += 1

        missing_children = [
            phase_id
            for phase_id, child_count in child_by_phase.items()
            if child_count < 1
        ]
        if missing_children:
            raise ValueError(
                "each phase must have at least one child node: "
                + ", ".join(sorted(missing_children))
            )

        isolated_ids = [
            node.id
            for node in self.nodes
            if node.kind != "goal" and node.id not in incident_ids
        ]
        if isolated_ids:
            raise ValueError(
                "non-goal nodes must not be isolated: "
                + ", ".join(sorted(isolated_ids))
            )
        return self


def generate_plan_graph_draft(
    client: PlanGraphClient,
    *,
    goal: str,
    duration_days: int,
    daily_minutes: int,
    preference: str = "",
    plan_brief_context: dict[str, Any] | None = None,
) -> PlanGraphDraft:
    response = client.complete_json(
        [
            LLMMessage(role="system", content=build_system_prompt()),
            LLMMessage(
                role="user",
                content=build_user_prompt(
                    goal=goal,
                    duration_days=duration_days,
                    daily_minutes=daily_minutes,
                    preference=preference,
                    plan_brief_context=plan_brief_context,
                ),
            ),
        ]
    )
    try:
        return PlanGraphDraft.model_validate(response)
    except ValidationError as exc:
        raise ValueError(f"LLM returned an invalid plan graph: {exc}") from exc


def build_system_prompt() -> str:
    return """
You generate one editable learning-plan graph for exactly one learning project.

Return only one valid JSON object. Do not include markdown.

The JSON schema:
{
  "title": "short plan title",
  "summary": "one paragraph explaining how to use the plan",
  "nodes": [
    {
      "id": "n1",
      "title": "short node title",
      "kind": "goal|phase|concept|practice|review|project|checkpoint|resource",
      "description": "specific action or learning purpose",
      "estimated_minutes": 25,
      "group": "optional visual group name",
      "status": "not_started",
      "position": {"x": 0, "y": 0}
    }
  ],
  "edges": [
    {"id": "e1", "source": "n1", "target": "n2", "label": "optional relation"}
  ]
}

Planning rules:
- Generate a single project only. Do not create multiple projects, Today tasks,
  calendars, daily task queues, or weekly schedules.
- Use this fixed structure: one goal node -> 3 to 5 phase nodes -> each phase
  has child nodes.
- Hard node budget: prefer 10 to 16 total nodes. Never exceed 18 nodes.
- If there are 5 phases, use only 1 to 2 child nodes per phase.
- If there are 4 phases, use 2 to 3 child nodes per phase.
- If there are 3 phases, use 2 to 4 child nodes per phase.
- When plan_brief_context.preview has 5 phases, preserve the 5 phase names but
  compress child nodes aggressively instead of adding every possible detail.
- Use clear node kinds: goal, phase, concept, practice, project, review,
  checkpoint, or resource.
- The goal node is the root. Each phase should connect from the goal or previous
  phase, and each phase must connect to its own child nodes.
- Phase children should be knowledge points, exercises, small projects,
  checkpoints, resources, or reviews.
- Keep the main path obvious: goal -> phase 1 -> phase 2 -> phase 3...
- Avoid isolated nodes, dense cross-links, cycles, and complicated edge
  crossings. Use only a few prerequisite or synthesis edges when necessary.
- Keep node titles concise enough to fit inside visual cards.
- Use concrete learning actions instead of vague slogans or broad topics.
- Estimate minutes realistically from the requested duration and daily capacity.
  Most child nodes should be 15 to 120 minutes. Large project/checkpoint nodes
  may be 120 to 240 minutes. Never invent impossible workloads.
- Set missing status to not_started.
- Positions should make a readable left-to-right graph: goal on the left,
  phases in the middle, children near their phase.

Brief alignment rules:
- If plan_brief_context is provided, treat it as the negotiated source of truth.
- The single goal node must reflect objective.one_sentence.
- Phase nodes should follow preview.phases in order. Use the phase names and
  focus as the primary phase structure unless doing so would violate graph
  limits.
- Child nodes must come from scope.include, success criteria, dynamic sections,
  and the phase focus. Do not introduce broad unrelated topics from
  scope.exclude.
- If risks or assumptions are provided, include them as checkpoint/review
  descriptions rather than expanding the plan scope.
- Dynamic sections should influence node kinds: practice sections should create
  practice/project nodes, resource sections may create one resource node, warning
  sections should create a checkpoint or review node.
""".strip()


def build_user_prompt(
    *,
    goal: str,
    duration_days: int,
    daily_minutes: int,
    preference: str,
    plan_brief_context: dict[str, Any] | None = None,
) -> str:
    return json.dumps(
        {
            "goal": goal,
            "duration_days": duration_days,
            "daily_minutes": daily_minutes,
            "preference": preference,
            "plan_brief_context": plan_brief_context,
            "output_language": "zh-CN",
        },
        ensure_ascii=False,
    )
