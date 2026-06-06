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
        "title": "Python 文件自动化学习计划",
        "summary": "先热身语法，再学习文件系统操作，最后用脚本项目整合。",
        "nodes": [
            {
                "id": "n1",
                "title": "学会 Python 文件自动化",
                "kind": "goal",
                "description": "30 天内能写出整理真实文件夹的基础脚本。",
                "estimated_minutes": 25,
                "position": {"x": 0, "y": 0},
            },
            {
                "id": "n2",
                "title": "语法热身",
                "kind": "stage",
                "description": "先补齐写脚本需要的最小 Python 语法。",
                "estimated_minutes": 30,
                "group": "语法",
                "position": {"x": 260, "y": -140},
            },
            {
                "id": "n3",
                "title": "变量、循环与函数",
                "kind": "learn",
                "description": "理解变量、for 循环、函数拆分，并完成小脚本练习。",
                "estimated_minutes": 60,
                "group": "语法",
                "position": {"x": 520, "y": -220},
            },
            {
                "id": "n4",
                "title": "列表与字典",
                "kind": "learn",
                "description": "掌握列表遍历、字典计数和基础数据整理练习。",
                "estimated_minutes": 60,
                "group": "语法",
                "position": {"x": 520, "y": -80},
            },
            {
                "id": "n5",
                "title": "文件系统操作",
                "kind": "stage",
                "description": "学习路径、遍历、读写和错误处理。",
                "estimated_minutes": 30,
                "group": "文件",
                "position": {"x": 780, "y": 0},
            },
            {
                "id": "n6",
                "title": "pathlib 路径对象",
                "kind": "learn",
                "description": "理解路径拼接、后缀判断、目录遍历和常见路径错误。",
                "estimated_minutes": 80,
                "group": "文件",
                "position": {"x": 1040, "y": -80},
            },
            {
                "id": "n7",
                "title": "文件读写与异常",
                "kind": "learn",
                "description": "练习读取文本、写入结果，并处理不存在或权限错误。",
                "estimated_minutes": 80,
                "group": "文件",
                "position": {"x": 1040, "y": 80},
            },
            {
                "id": "n8",
                "title": "脚本自动化",
                "kind": "stage",
                "description": "把路径和规则组合成可运行的小脚本。",
                "estimated_minutes": 30,
                "group": "脚本",
                "position": {"x": 1300, "y": 120},
            },
            {
                "id": "n9",
                "title": "批量重命名规则",
                "kind": "learn",
                "description": "设计文件名规则，包含小实验、边界情况和自测。",
                "estimated_minutes": 80,
                "group": "脚本",
                "position": {"x": 1560, "y": 40},
            },
            {
                "id": "n10",
                "title": "批量重命名脚本",
                "kind": "project",
                "description": (
                    "综合 pathlib、文件遍历和规则判断，做出可运行脚本；"
                    "验收标准包括不覆盖同名文件。"
                ),
                "estimated_minutes": 180,
                "group": "脚本",
                "position": {"x": 1560, "y": 200},
            },
        ],
        "edges": [
            {
                "id": "e1",
                "source": "n1",
                "target": "n2",
                "relation": "next",
                "label": "开始",
            },
            {
                "id": "e2",
                "source": "n2",
                "target": "n3",
                "relation": "contains",
                "label": "学习",
            },
            {
                "id": "e3",
                "source": "n2",
                "target": "n4",
                "relation": "contains",
                "label": "学习",
            },
            {
                "id": "e4",
                "source": "n2",
                "target": "n5",
                "relation": "next",
                "label": "下一阶段",
            },
            {
                "id": "e5",
                "source": "n5",
                "target": "n6",
                "relation": "contains",
                "label": "学习",
            },
            {
                "id": "e6",
                "source": "n5",
                "target": "n7",
                "relation": "contains",
                "label": "学习",
            },
            {
                "id": "e7",
                "source": "n5",
                "target": "n8",
                "relation": "next",
                "label": "下一阶段",
            },
            {
                "id": "e8",
                "source": "n8",
                "target": "n9",
                "relation": "contains",
                "label": "学习",
            },
            {
                "id": "e9",
                "source": "n8",
                "target": "n10",
                "relation": "contains",
                "label": "项目",
            },
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

    assert draft.title == "Python 文件自动化学习计划"
    assert draft.nodes[0].kind == "goal"
    assert draft.nodes[0].status == "not_started"
    assert draft.edges[1].source == "n2"
    assert "output_language" in client.messages[1].content


def test_generate_plan_graph_draft_rejects_old_non_linear_relations() -> None:
    payload = valid_plan_graph()
    payload["edges"].extend(
        [
            {
                "id": "e10",
                "source": "n3",
                "target": "n9",
                "relation": "converges",
                "label": "汇合",
            },
            {
                "id": "e11",
                "source": "n10",
                "target": "n4",
                "relation": "reviews",
                "label": "复盘",
            },
            {
                "id": "e12",
                "source": "n4",
                "target": "n6",
                "relation": "prerequisite",
                "label": "前置",
            },
        ]
    )
    client = FakePlanClient(payload)

    with pytest.raises(ValueError, match="invalid plan graph"):
        generate_plan_graph_draft(
            client,
            goal="准备算法面试",
            duration_days=30,
            daily_minutes=25,
        )


def test_generate_plan_graph_draft_fills_default_edge_label() -> None:
    payload = valid_plan_graph()
    payload["edges"][0]["relation"] = "next"
    payload["edges"][0]["label"] = None
    client = FakePlanClient(payload)

    draft = generate_plan_graph_draft(
        client,
        goal="准备算法面试",
        duration_days=30,
        daily_minutes=25,
    )

    assert draft.edges[0].label == "下一阶段"


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
    assert "If there are 5 stages" in prompt
    assert "computer-science and software learning plans" in prompt
    assert "goal|stage|learn|project" in prompt
    assert '"relation": "contains|next"' in prompt
    assert (
        "Do not use concept, task, practice, review, checkpoint, or resource" in prompt
    )


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


def test_generate_plan_graph_draft_rejects_too_few_stages() -> None:
    payload = valid_plan_graph()
    payload["nodes"][7]["kind"] = "learn"
    client = FakePlanClient(payload)

    with pytest.raises(ValueError, match="3 to 5 stage"):
        generate_plan_graph_draft(
            client,
            goal="学 Python 文件自动化",
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


def test_generate_plan_graph_draft_rejects_unreachable_non_goal_node() -> None:
    payload = valid_plan_graph()
    payload["edges"] = [edge for edge in payload["edges"] if edge["target"] != "n5"]
    client = FakePlanClient(payload)

    with pytest.raises(ValueError, match="incoming edge"):
        generate_plan_graph_draft(
            client,
            goal="准备算法面试",
            duration_days=30,
            daily_minutes=25,
        )


def test_generate_plan_graph_draft_rejects_disconnected_cycle() -> None:
    payload = valid_plan_graph()
    payload["edges"] = [
        edge
        for edge in payload["edges"]
        if edge["source"] not in {"n5", "n6", "n7"} and edge["target"] != "n5"
    ]
    payload["edges"].extend(
        [
            {"id": "e10", "source": "n5", "target": "n6", "label": "练习"},
            {
                "id": "e11",
                "source": "n6",
                "target": "n7",
                "relation": "contains",
                "label": "包含",
            },
            {
                "id": "e12",
                "source": "n7",
                "target": "n5",
                "relation": "contains",
                "label": "包含",
            },
            {
                "id": "e13",
                "source": "n5",
                "target": "n8",
                "relation": "next",
                "label": "下一阶段",
            },
        ]
    )
    client = FakePlanClient(payload)

    with pytest.raises(ValueError, match="reachable from the goal"):
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
