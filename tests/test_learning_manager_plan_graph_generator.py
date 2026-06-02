import pytest

from examples.learning_manager.plan_graph_generator import generate_plan_graph_draft


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
                "title": "数组与哈希",
                "kind": "practice",
                "description": "练习数组遍历、计数和查找。",
                "estimated_minutes": 25,
                "group": "基础",
                "position": {"x": 260, "y": -90},
            },
            {
                "id": "n3",
                "title": "模拟面试",
                "kind": "checkpoint",
                "description": "完成一次限时综合练习。",
                "estimated_minutes": 45,
                "group": "输出",
                "position": {"x": 520, "y": 0},
            },
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2", "label": "开始"},
            {"id": "e2", "source": "n2", "target": "n3", "label": "综合"},
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
    assert draft.edges[1].source == "n2"
    assert "output_language" in client.messages[1].content


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
