import json
from collections import Counter
from pathlib import Path
from typing import Any

from examples.learning_manager.plan_graph_generator import PlanGraphDraft

FIXTURE_DIR = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "learning_manager"
    / "test_fixtures"
)
ALGORITHM_INTERVIEW_FIXTURE = (
    FIXTURE_DIR / "algorithm_interview_30d_plan_editor_export.json"
)


def test_manual_algorithm_interview_fixture_is_valid_plan_graph() -> None:
    project = json.loads(ALGORITHM_INTERVIEW_FIXTURE.read_text(encoding="utf-8"))

    draft = PlanGraphDraft.model_validate(editor_export_to_plan_graph(project))

    assert project["title"] == "30天算法面试冲刺计划"
    assert project["goal"] == "我想用 30 天准备算法面试，重点是能自己规划和复盘"
    assert len(draft.nodes) == 16
    assert len(draft.edges) == 15
    assert Counter(node.kind for node in draft.nodes) == {
        "goal": 1,
        "stage": 4,
        "learn": 7,
        "project": 4,
    }
    assert {edge.relation for edge in draft.edges} == {"next", "contains"}
    assert [edge.target for edge in draft.edges if edge.relation == "next"] == [
        "n2",
        "n3",
        "n4",
        "n5",
    ]
    assert any("动态规划" in node.title for node in draft.nodes)


def editor_export_to_plan_graph(project: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": project["title"],
        "summary": project["summary"],
        "nodes": [
            {
                "id": node["id"],
                "title": node["data"]["title"],
                "kind": node["data"]["kind"],
                "description": node["data"].get("description", ""),
                "estimated_minutes": node["data"].get("estimated_minutes", 0),
                "group": node["data"].get("group") or None,
                "status": node["data"].get("status", "not_started"),
                "position": node.get("position"),
            }
            for node in project["nodes"]
        ],
        "edges": [
            {
                "id": edge["id"],
                "source": edge["source"],
                "target": edge["target"],
                "relation": edge["relation"],
                "label": edge.get("label") or None,
            }
            for edge in project["graphEdges"]
        ],
    }
