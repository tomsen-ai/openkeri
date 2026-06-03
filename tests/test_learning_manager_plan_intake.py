import json

import pytest

from examples.learning_manager.plan_intake import (
    MAX_INTAKE_ROUNDS,
    PlanIntakeState,
    answer_plan_intake,
    build_system_prompt,
    evaluate_plan_intake,
    start_plan_intake,
)


class FakeIntakeClient:
    def __init__(self, responses: list[dict]) -> None:
        self.responses = responses
        self.messages = []

    def complete_json(self, messages: list) -> dict:
        self.messages.append(messages)
        if not self.responses:
            raise AssertionError("no fake intake response left")
        return self.responses.pop(0)


def needs_choice_response() -> dict:
    return {
        "status": "needs_choice",
        "reason": "需要先选择计划方向。",
        "issue": {
            "type": "unclear_output",
            "summary": "先确定这次算法面试怎么准备。",
            "reason": "同一个目标可以做成冲刺、系统准备、复盘能力或全貌地图。",
        },
        "question": {
            "id": "algorithm_interview_direction",
            "title": "选择一个计划方向",
            "description": "选择后会继续收敛计划范围和节奏。",
            "choices": [
                {
                    "id": "core_sprint",
                    "label": "核心冲刺",
                    "description": "最高频基础题，快速建立手感。",
                },
                {
                    "id": "systematic_prep",
                    "label": "系统准备",
                    "description": "按题型推进，覆盖更多专题。",
                },
                {
                    "id": "review_skill",
                    "label": "复盘能力",
                    "description": "重点练规划、错题复盘和纠偏。",
                },
                {
                    "id": "overview_map",
                    "label": "全貌地图",
                    "description": "先搞清楚算法面试怎么学。",
                },
            ],
        },
    }


def ready_response() -> dict:
    return {
        "status": "ready",
        "reason": "目标已经收敛，可以生成计划图。",
        "brief": {
            "title": "算法面试核心基础冲刺",
            "refined_goal": "30 天内完成算法面试最高频基础题型入门",
            "scope": "数组、哈希、字符串、双指针、滑窗",
            "excluded_scope": "动态规划、复杂图论、系统性专题训练暂不覆盖",
            "strategy": "focus_core",
            "recommended_pace": "建议每周 3-4 次，每次 30-45 分钟",
            "expected_outcome": "能完成基础高频题入门，不承诺完整准备好算法面试",
            "risk_level": "tight",
            "assumptions": ["用户每天可以稳定投入 25 分钟"],
            "user_summary": {
                "headline": "已收敛为：算法面试核心基础冲刺",
                "why": "你当前总投入约 12.5 小时，不适合完整准备算法面试。",
                "focus": "本轮重点：数组、哈希、字符串、双指针、滑窗。",
                "not_included": "暂不深入：动态规划、复杂图论、系统性专题训练。",
                "outcome": "预期结果：完成基础高频题入门，不承诺完整准备好算法面试。",
            },
            "skeleton": [
                {"phase_name": "基础题型", "focus": "数组、哈希", "estimated_child_count": 3},
                {"phase_name": "字符串与滑窗", "focus": "双指针、滑窗", "estimated_child_count": 3},
                {"phase_name": "综合输出", "focus": "模拟面试与复盘", "estimated_child_count": 2},
            ],
        },
    }


INTAKE_SCENARIOS = [
    {
        "name": "low_time_algorithm_interview",
        "goal": "30 天准备算法面试",
        "duration_days": 30,
        "daily_minutes": 25,
        "response": needs_choice_response(),
        "expected_status": "needs_choice",
        "expected_issue_type": "unclear_output",
        "expected_choice_ids": {
            "core_sprint",
            "systematic_prep",
            "review_skill",
            "overview_map",
        },
    },
    {
        "name": "broad_machine_learning_goal",
        "goal": "学机器学习",
        "duration_days": 14,
        "daily_minutes": 30,
        "response": {
            "status": "needs_choice",
            "reason": "目标范围太大，需要先收敛主线。",
            "issue": {
                "type": "scope_too_broad",
                "summary": "14 天每天 30 分钟不适合覆盖机器学习全貌和深度实践。",
                "reason": "这个目标包含数学基础、模型、实践和工程工具，需要先选重点。",
            },
            "question": {
                "id": "machine_learning_scope",
                "title": "这轮机器学习先聚焦哪种结果？",
                "description": "选择后会把其他内容降为轻量了解。",
                "choices": [
                    {
                        "id": "core_concepts",
                        "label": "核心概念",
                        "description": "先理解监督学习、评估和常见模型。",
                    },
                    {
                        "id": "small_project",
                        "label": "小项目",
                        "description": "围绕一个可完成项目学习必要知识。",
                    },
                    {
                        "id": "overview_map",
                        "label": "快速全貌",
                        "description": "建立地图，不追求熟练掌握。",
                    },
                ],
            },
        },
        "expected_status": "needs_choice",
        "expected_issue_type": "scope_too_broad",
        "expected_choice_ids": {"core_concepts", "small_project", "overview_map"},
    },
    {
        "name": "clear_algorithm_interview_goal",
        "goal": "90 天准备算法面试",
        "duration_days": 90,
        "daily_minutes": 60,
        "background": "做过一些 LeetCode",
        "intensity": "面试冲刺",
        "preference": "练习优先",
        "response": {
            "status": "ready",
            "reason": "目标、投入和偏好足够明确。",
            "brief": {
                "title": "算法面试系统冲刺计划",
                "refined_goal": "90 天完成算法面试高频题型训练和模拟复盘",
                "scope": "基础题型、树图、动态规划入门、模拟面试和错题复盘",
                "excluded_scope": "不承诺覆盖所有冷门专题",
                "strategy": "practice_first",
                "expected_outcome": (
                    "形成稳定刷题节奏并提升常见题型通过率，不保证面试通过。"
                ),
                "risk_level": "feasible",
                "assumptions": ["用户已有少量刷题基础"],
                "user_summary": {
                    "headline": "算法面试系统冲刺计划",
                    "why": "你的周期和投入足以做阶段化训练。",
                    "focus": "刷题、模拟面试、错题复盘。",
                    "not_included": "不承诺覆盖所有冷门专题。",
                    "outcome": "提升常见题型通过率，不保证面试通过。",
                },
            },
        },
        "expected_status": "ready",
        "expected_risk_level": "feasible",
    },
]


@pytest.mark.parametrize("case", INTAKE_SCENARIOS, ids=lambda case: case["name"])
def test_plan_intake_scenarios(case: dict) -> None:
    client = FakeIntakeClient([case["response"]])

    result = start_plan_intake(
        client,
        goal=case["goal"],
        duration_days=case["duration_days"],
        daily_minutes=case["daily_minutes"],
        background=case.get("background", ""),
        intensity=case.get("intensity", ""),
        preference=case.get("preference", ""),
    )

    assert result.status == case["expected_status"]

    user_payload = json.loads(client.messages[0][1].content)
    assert user_payload["time_is_default"] is True
    assert "total_minutes" not in user_payload

    if result.status == "needs_choice":
        assert result.issue is not None
        assert result.question is not None
        assert result.issue.type == case["expected_issue_type"]
        assert result.state.pending_issue == result.issue
        assert result.state.pending_question == result.question
        assert {choice.id for choice in result.question.choices} == case[
            "expected_choice_ids"
        ]
    else:
        assert result.brief is not None
        assert result.brief.risk_level == case["expected_risk_level"]
        assert result.brief.constraints.total_minutes == (
            case["duration_days"] * case["daily_minutes"]
        )
        assert result.brief.user_summary.headline


def test_plan_intake_answer_records_choice_and_returns_brief() -> None:
    client = FakeIntakeClient([needs_choice_response(), ready_response()])

    first = start_plan_intake(
        client,
        goal="30 天准备算法面试",
        duration_days=30,
        daily_minutes=25,
    )
    result = answer_plan_intake(client, first.state, choice_id="core_sprint")

    assert result.status == "ready"
    assert result.brief is not None
    assert result.state.round == 1
    assert result.state.pending_question is None
    assert result.brief.constraints.total_minutes == 750
    assert result.brief.user_choices[0].choice_id == "core_sprint"
    assert result.brief.user_summary.headline == "已收敛为：算法面试核心基础冲刺"
    assert "不承诺完整准备好算法面试" in result.brief.expected_outcome
    assert result.brief.recommended_pace == "建议每周 3-4 次，每次 30-45 分钟"

    second_payload = json.loads(client.messages[1][1].content)
    assert second_payload["conversation_history"][0]["user_choice"] == "核心冲刺"


def test_plan_intake_hides_default_time_from_llm_prompt() -> None:
    client = FakeIntakeClient([needs_choice_response()])

    start_plan_intake(
        client,
        goal="准备算法面试",
        duration_days=30,
        daily_minutes=25,
        time_is_default=True,
    )

    payload = json.loads(client.messages[0][1].content)
    assert payload["time_is_default"] is True
    assert "duration_days" not in payload
    assert "daily_minutes" not in payload
    assert "total_minutes" not in payload


def test_plan_intake_rejects_unknown_choice() -> None:
    client = FakeIntakeClient([needs_choice_response()])
    first = start_plan_intake(
        client,
        goal="30 天准备算法面试",
        duration_days=30,
        daily_minutes=25,
    )

    with pytest.raises(ValueError, match="unknown intake choice"):
        answer_plan_intake(client, first.state, choice_id="not-a-choice")


def test_plan_intake_rejects_answer_without_pending_question() -> None:
    client = FakeIntakeClient([])
    state = PlanIntakeState(
        goal="90 天准备算法面试",
        duration_days=90,
        daily_minutes=60,
    )

    with pytest.raises(ValueError, match="no pending question"):
        answer_plan_intake(client, state, choice_id="focus_core")


def test_plan_intake_rejects_invalid_llm_response() -> None:
    client = FakeIntakeClient(
        [
            {
                "status": "needs_choice",
                "reason": "缺少 issue 和 question。",
            }
        ]
    )

    with pytest.raises(ValueError, match="invalid intake response"):
        start_plan_intake(
            client,
            goal="3 天精通 Python",
            duration_days=3,
            daily_minutes=15,
        )


def test_plan_intake_requires_ready_after_max_rounds() -> None:
    client = FakeIntakeClient([needs_choice_response()])
    state = PlanIntakeState(
        goal="3 天精通 Python",
        duration_days=3,
        daily_minutes=15,
        round=MAX_INTAKE_ROUNDS,
    )

    with pytest.raises(ValueError, match="must be ready after max rounds"):
        evaluate_plan_intake(client, state)

    payload = json.loads(client.messages[0][1].content)
    assert payload["force_ready"] is True


def test_plan_intake_allows_ready_after_max_rounds() -> None:
    client = FakeIntakeClient([ready_response()])
    state = PlanIntakeState(
        goal="3 天精通 Python",
        duration_days=3,
        daily_minutes=15,
        round=MAX_INTAKE_ROUNDS,
    )

    result = evaluate_plan_intake(client, state)

    assert result.status == "ready"
    assert result.brief is not None
    assert result.brief.constraints.total_minutes == 45


def test_plan_intake_prompt_includes_product_constraints() -> None:
    prompt = build_system_prompt()

    assert "WHY the user wants to learn this" in prompt
    assert "HOW MUCH they can realistically commit" in prompt
    assert "WHAT specific scope to cover" in prompt
    assert "Do not generate the full plan graph here" in prompt
    assert "force_ready" in prompt
    assert "skeleton" in prompt
