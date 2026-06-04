import json

import pytest

from examples.learning_manager.plan_graph_generator import (
    build_system_prompt,
    generate_plan_graph_draft,
)


class FakePlanClient:
    def __init__(self, response: dict) -> None:
        self.response = response
        self.messages = []

    def complete_json(self, messages: list) -> dict:
        self.messages = messages
        return self.response


def valid_plan_graph() -> dict:
    return {
        "title": "算法面试学习计划",
        "summary": "先建立基础，再做题型练习，最后用模拟面试收束。",
        "nodes": [
            {
                "id": "n1",
                "title": "准备算法面试",
                "kind": "goal",
                "description": "明确目标和时间安排。",
                "estimated_minutes": 25,
                "position": {"x": 0, "y": 0},
            },
            {
                "id": "n2",
                "title": "基础题型",
                "kind": "phase",
                "description": "建立数组、哈希和字符串的基本解题框架。",
                "estimated_minutes": 30,
                "group": "基础",
                "position": {"x": 260, "y": -140},
            },
            {
                "id": "n3",
                "title": "数组与哈希",
                "kind": "practice",
                "description": "练习数组遍历、计数和查找。",
                "estimated_minutes": 25,
                "group": "基础",
                "position": {"x": 520, "y": -220},
            },
            {
                "id": "n4",
                "title": "字符串模式",
                "kind": "concept",
                "description": "整理双指针、滑窗和频次统计模板。",
                "estimated_minutes": 35,
                "group": "基础",
                "position": {"x": 520, "y": -80},
            },
            {
                "id": "n5",
                "title": "进阶结构",
                "kind": "phase",
                "description": "学习栈、队列、树和图的常见套路。",
                "estimated_minutes": 30,
                "group": "进阶",
                "position": {"x": 780, "y": 0},
            },
            {
                "id": "n6",
                "title": "树与递归",
                "kind": "practice",
                "description": "完成遍历、深度和路径类练习。",
                "estimated_minutes": 45,
                "group": "进阶",
                "position": {"x": 1040, "y": -80},
            },
            {
                "id": "n7",
                "title": "图搜索",
                "kind": "concept",
                "description": "比较 BFS、DFS 和 visited 设计。",
                "estimated_minutes": 40,
                "group": "进阶",
                "position": {"x": 1040, "y": 80},
            },
            {
                "id": "n8",
                "title": "综合输出",
                "kind": "phase",
                "description": "通过限时练习和复盘收束面试能力。",
                "estimated_minutes": 30,
                "group": "输出",
                "position": {"x": 1300, "y": 120},
            },
            {
                "id": "n9",
                "title": "模拟面试",
                "kind": "checkpoint",
                "description": "完成一次限时综合练习。",
                "estimated_minutes": 45,
                "group": "输出",
                "position": {"x": 1560, "y": 40},
            },
            {
                "id": "n10",
                "title": "错题复盘",
                "kind": "review",
                "description": "归纳高频错误并安排二刷。",
                "estimated_minutes": 30,
                "group": "输出",
                "position": {"x": 1560, "y": 200},
            },
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2", "label": "开始"},
            {"id": "e2", "source": "n2", "target": "n3", "label": "练习"},
            {"id": "e3", "source": "n2", "target": "n4", "label": "概念"},
            {"id": "e4", "source": "n2", "target": "n5", "label": "下一阶段"},
            {"id": "e5", "source": "n5", "target": "n6", "label": "练习"},
            {"id": "e6", "source": "n5", "target": "n7", "label": "概念"},
            {"id": "e7", "source": "n5", "target": "n8", "label": "下一阶段"},
            {"id": "e8", "source": "n8", "target": "n9", "label": "检查"},
            {"id": "e9", "source": "n8", "target": "n10", "label": "复盘"},
        ],
    }


def test_generate_plan_graph_draft_validates_response() -> None:
    client = FakePlanClient(valid_plan_graph())

    draft = generate_plan_graph_draft(
        client,
        goal="我想用 30 天准备算法面试",
        duration_days=30,
        daily_minutes=25,
    )

    assert draft.title == "算法面试学习计划"
    assert draft.nodes[0].kind == "goal"
    assert draft.nodes[0].status == "not_started"
    assert draft.edges[1].source == "n2"
    assert "output_language" in client.messages[1].content


def test_generate_plan_graph_draft_includes_structured_brief_context() -> None:
    client = FakePlanClient(valid_plan_graph())
    brief_context = {
        "title": "Python 文件自动化入门",
        "objective": {
            "one_sentence": "30 天内学会用 Python 写基础文件整理脚本",
            "outcome": "能完成 2-3 个整理照片和文档的小脚本",
            "success_criteria": ["批量重命名文件", "按规则移动照片"],
        },
        "scope": {
            "include": ["Python 基础", "文件路径", "批量重命名"],
            "exclude": ["Web 后端"],
        },
        "preview": {
            "phases": [
                {"phase_name": "语法热身", "focus": "变量、循环、函数"},
                {"phase_name": "文件操作", "focus": "路径、遍历、移动"},
                {"phase_name": "脚本产出", "focus": "照片和文档整理"},
            ],
        },
        "sections": [
            {
                "kind": "practice",
                "title": "练习方式",
                "summary": "每个阶段都产出一个小脚本。",
            }
        ],
    }

    generate_plan_graph_draft(
        client,
        goal="30 天内学会用 Python 写基础文件整理脚本",
        duration_days=30,
        daily_minutes=25,
        preference="Use negotiated brief.",
        plan_brief_context=brief_context,
    )

    payload = json.loads(client.messages[1].content)
    assert payload["plan_brief_context"] == brief_context
    assert payload["plan_brief_context"]["objective"]["one_sentence"].startswith(
        "30 天内"
    )
    assert payload["plan_brief_context"]["scope"]["exclude"] == ["Web 后端"]


def test_graph_prompt_includes_brief_alignment_rules() -> None:
    prompt = build_system_prompt()

    assert "Brief alignment rules" in prompt
    assert "negotiated source of truth" in prompt
    assert "preview.phases" in prompt
    assert "scope.exclude" in prompt
    assert "If there are 5 phases" in prompt


def test_generate_plan_graph_draft_rejects_missing_edge_target() -> None:
    payload = valid_plan_graph()
    payload["edges"][0]["target"] = "missing"
    client = FakePlanClient(payload)

    with pytest.raises(ValueError, match="invalid plan graph"):
        generate_plan_graph_draft(
            client,
            goal="学英语阅读",
            duration_days=14,
            daily_minutes=20,
        )


def test_generate_plan_graph_draft_rejects_too_few_phases() -> None:
    payload = valid_plan_graph()
    payload["nodes"][7]["kind"] = "practice"
    client = FakePlanClient(payload)

    with pytest.raises(ValueError, match="3 to 5 phase"):
        generate_plan_graph_draft(
            client,
            goal="准备算法面试",
            duration_days=30,
            daily_minutes=25,
        )


def test_generate_plan_graph_draft_rejects_isolated_non_goal_node() -> None:
    payload = valid_plan_graph()
    payload["edges"] = [
        edge
        for edge in payload["edges"]
        if edge["source"] != "n10" and edge["target"] != "n10"
    ]
    client = FakePlanClient(payload)

    with pytest.raises(ValueError, match="isolated"):
        generate_plan_graph_draft(
            client,
            goal="准备算法面试",
            duration_days=30,
            daily_minutes=25,
        )


def test_generate_plan_graph_draft_clamps_estimated_minutes() -> None:
    payload = valid_plan_graph()
    payload["nodes"][2]["estimated_minutes"] = 2
    payload["nodes"][3]["estimated_minutes"] = 9999
    client = FakePlanClient(payload)

    draft = generate_plan_graph_draft(
        client,
        goal="准备算法面试",
        duration_days=30,
        daily_minutes=25,
    )

    assert draft.nodes[2].estimated_minutes == 5
    assert draft.nodes[3].estimated_minutes == 480
