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
    position: PlanNodePosition | None = None

    @field_validator("id")
    @classmethod
    def validate_node_id(cls, value: str) -> str:
        if not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_-]*", value):
            raise ValueError(
                "node id must start with a letter and use letters, numbers, _ or -"
            )
        return value


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
    nodes: list[PlanGraphNode] = Field(min_length=2)
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


def generate_plan_graph_draft(
    client: PlanGraphClient,
    *,
    goal: str,
    duration_days: int,
    daily_minutes: int,
    preference: str = "",
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
You generate editable learning-plan mind maps.

Return only one valid JSON object. Do not include markdown.

The JSON schema:
{
  "title": "short plan title",
  "summary": "one paragraph explaining how to use the plan",
  "nodes": [
    {
      "id": "n1",
      "title": "short node title",
      "kind": "goal|phase|concept|task|practice|review|project|checkpoint|resource",
      "description": "specific action or learning purpose",
      "estimated_minutes": 25,
      "group": "optional visual group name",
      "position": {"x": 0, "y": 0}
    }
  ],
  "edges": [
    {"id": "e1", "source": "n1", "target": "n2", "label": "optional relation"}
  ]
}

Planning rules:
- Do not force every plan into three stages.
- Choose the graph shape that fits the goal: linear, branching, converging,
  hub-and-spoke, or mixed.
- Make one root goal node.
- Prefer 8 to 16 nodes for an MVP preview.
- Use edges to show prerequisites, branches, and synthesis paths.
- Keep node titles concise enough to fit inside visual cards.
- Use concrete learning actions instead of vague slogans.
- Estimate minutes per node from the requested daily capacity.
- Positions should make a readable left-to-right mind map.
""".strip()


def build_user_prompt(
    *,
    goal: str,
    duration_days: int,
    daily_minutes: int,
    preference: str,
) -> str:
    return json.dumps(
        {
            "goal": goal,
            "duration_days": duration_days,
            "daily_minutes": daily_minutes,
            "preference": preference,
            "output_language": "zh-CN",
        },
        ensure_ascii=False,
    )
