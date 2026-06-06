from __future__ import annotations

import json
import re
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from openkeri.llm import LLMMessage

PlanNodeKind = Literal[
    "goal",
    "stage",
    "learn",
    "project",
]

PlanNodeStatus = Literal["not_started", "in_progress", "done"]
PlanEdgeRelation = Literal[
    "contains",
    "next",
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
    relation: PlanEdgeRelation = "contains"
    label: str | None = None

    @model_validator(mode="after")
    def validate_not_self_loop(self) -> PlanGraphEdge:
        if self.source == self.target:
            raise ValueError("edge source and target must be different")
        if not self.label:
            self.label = relation_label(self.relation)
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

        stage_nodes = [node for node in self.nodes if node.kind == "stage"]
        if not 3 <= len(stage_nodes) <= 5:
            raise ValueError("plan graph must contain 3 to 5 stage nodes")

        goal_id = goal_nodes[0].id
        kind_by_id = {node.id: node.kind for node in self.nodes}
        stage_ids = {node.id for node in stage_nodes}
        child_by_stage = {stage_id: 0 for stage_id in stage_ids}
        incoming_by_node = {node.id: 0 for node in self.nodes}
        children_by_source = {node.id: [] for node in self.nodes}
        incident_ids = set()
        for edge in self.edges:
            incident_ids.add(edge.source)
            incident_ids.add(edge.target)
            incoming_by_node[edge.target] += 1
            children_by_source[edge.source].append(edge.target)
            if (
                edge.source in stage_ids
                and edge.target not in stage_ids
                and edge.relation == "contains"
            ):
                child_by_stage[edge.source] += 1

        missing_children = [
            stage_id
            for stage_id, child_count in child_by_stage.items()
            if child_count < 1
        ]
        if missing_children:
            raise ValueError(
                "each stage must have at least one child node: "
                + ", ".join(sorted(missing_children))
            )

        invalid_child_ids = [
            edge.target
            for edge in self.edges
            if edge.source in stage_ids
            and edge.relation == "contains"
            and kind_by_id[edge.target] not in {"learn", "project"}
        ]
        if invalid_child_ids:
            raise ValueError(
                "stage children must be learn or project nodes: "
                + ", ".join(sorted(set(invalid_child_ids)))
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

        unreachable_ids = [
            node.id
            for node in self.nodes
            if node.kind != "goal" and incoming_by_node[node.id] < 1
        ]
        if unreachable_ids:
            raise ValueError(
                "non-goal nodes must have at least one incoming edge: "
                + ", ".join(sorted(unreachable_ids))
            )

        reachable_ids = {goal_id}
        queue = [goal_id]
        while queue:
            source_id = queue.pop(0)
            for target_id in children_by_source[source_id]:
                if target_id not in reachable_ids:
                    reachable_ids.add(target_id)
                    queue.append(target_id)

        disconnected_ids = [
            node.id for node in self.nodes if node.id not in reachable_ids
        ]
        if disconnected_ids:
            raise ValueError(
                "nodes must be reachable from the goal node: "
                + ", ".join(sorted(disconnected_ids))
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
      "kind": "goal|stage|learn|project",
      "description": "specific action or learning purpose",
      "estimated_minutes": 25,
      "group": "optional visual group name",
      "status": "not_started",
      "position": {"x": 0, "y": 0}
    }
  ],
    "edges": [
    {
      "id": "e1",
      "source": "n1",
      "target": "n2",
      "relation": "contains|next",
      "label": "short visible relation label"
    }
  ]
}

Planning rules:
- Generate a single project only. Do not create multiple projects, Today tasks,
  calendars, daily task queues, or weekly schedules.
- Optimize for computer-science and software learning plans. Generate a clean
  learning route, not a dense knowledge graph.
- Use this fixed structure: one goal node, 3 to 5 stage nodes, and learn/project
  child nodes under stages.
- Hard node budget: prefer 10 to 16 total nodes. Never exceed 18 nodes.
- If there are 5 stages, use only 1 to 2 child nodes per stage.
- If there are 4 stages, use 2 to 3 child nodes per stage.
- If there are 3 stages, use 2 to 4 child nodes per stage.
- When plan_brief_context.preview has 5 phases, preserve the 5 stage names but
  compress child nodes aggressively instead of adding every possible detail.
- Use clear node kinds:
  - goal: the final observable capability or result.
  - stage: an ordered route segment that explains why this part comes here.
  - learn: one knowledge point or capability unit. It may include explanation,
    examples, mini labs, exercises, self-checks, resources, and review prompts
    in its description/detail, but it remains one graph node.
  - project: an integrated output that combines multiple learn nodes into a
    runnable, submitable, visible, or otherwise verifiable artifact.
- Do not use concept, task, practice, review, checkpoint, or resource as graph
  node kinds. Fold them into learn/project descriptions and future node detail.
- The goal node is the root. Each stage must be reachable from the goal or a
  previous stage, and each stage must connect to at least one learn/project
  child node.
- Use relation "next" only for the main route: goal -> stage 1 and stage ->
  stage.
- Use relation "contains" only for stage -> learn/project ownership.
- Do not add prerequisite, parallel, resource, convergence, review-loop, or
  cross-stage edges. Mention strong prerequisites, resources, acceptance
  criteria, and review prompts in node descriptions instead of drawing them.
- Keep the visible graph simple and executable: stages show order; children
  show what to learn or build in that stage.
- Use informative edge labels. Prefer "开始", "下一阶段", "学习", or "项目".
- Keep node titles concise enough to fit inside visual cards.
- Use concrete learning actions instead of vague slogans or broad topics.
- Estimate minutes realistically from the requested duration and daily capacity.
  Most learn nodes should be 30 to 120 minutes. Project nodes may be 120 to 240
  minutes. Never invent impossible workloads.
- Set missing status to not_started.
- Positions should make a readable left-to-right graph: goal on the left,
  stages in the middle, children near their stage.

Brief alignment rules:
- If plan_brief_context is provided, treat it as the negotiated source of truth.
- The single goal node must reflect objective.one_sentence.
- Stage nodes should follow preview.phases in order. Use the phase names and
  focus as the primary stage structure unless doing so would violate graph
  limits.
- Child nodes must come from scope.include, success criteria, dynamic sections,
  and the stage focus. Do not introduce broad unrelated topics from
  scope.exclude.
- If risks, assumptions, resources, or review needs are provided, include them
  in learn/project descriptions rather than expanding graph node kinds.
- Dynamic sections should influence node details: practice sections should make
  learn descriptions more hands-on or create project nodes; resource sections
  should be listed inside relevant learn/project descriptions; warning sections
  should become acceptance criteria or review prompts in project descriptions.
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


def relation_label(relation: PlanEdgeRelation) -> str:
    return {
        "contains": "包含",
        "next": "下一阶段",
    }[relation]
