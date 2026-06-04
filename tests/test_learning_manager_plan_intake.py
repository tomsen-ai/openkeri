import json

import pytest

from examples.learning_manager.plan_intake import (
    MAX_INTAKE_ROUNDS,
    MIN_OPTIONAL_SLOTS,
    IntentSlots,
    PlanIntakeState,
    answer_plan_intake,
    build_system_prompt,
    evaluate_completeness,
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


def slots_response(**slots: str | None) -> dict:
    payload = {
        "learning_subject": None,
        "target_outcome": None,
        "time_window": None,
        "available_rhythm": None,
        "learner_background": None,
        "preferred_style": None,
        "use_context": None,
    }
    payload.update(slots)
    return {"slots": payload, "notes": ["parsed from raw intent"]}


def target_outcome_question() -> dict:
    return {
        "id": "python_outcome",
        "target_slot": "target_outcome",
        "title": "这轮学 Python 更想做成什么？",
        "description": "不同结果会改变计划路线。",
        "choices": [
            {
                "id": "automation",
                "label": "自动化脚本",
                "description": "能写脚本批量整理文件和处理重复任务。",
                "fills": {
                    "target_outcome": "写出自动化脚本",
                    "use_context": "文件和重复任务自动化",
                },
            },
            {
                "id": "data_analysis",
                "label": "数据分析",
                "description": "能读取表格、清洗数据并做简单分析。",
                "fills": {
                    "target_outcome": "完成小型数据分析",
                    "use_context": "数据分析",
                },
            },
        ],
    }


def background_question() -> dict:
    return {
        "id": "learner_background",
        "target_slot": "learner_background",
        "title": "你现在的基础更接近哪种？",
        "description": "基础不同，前几步安排会不同。",
        "choices": [
            {
                "id": "zero",
                "label": "零基础",
                "description": "没有系统学过 Python。",
                "fills": {"learner_background": "零基础"},
            },
            {
                "id": "some",
                "label": "有一点基础",
                "description": "写过简单脚本或看得懂基础语法。",
                "fills": {"learner_background": "有一点 Python 基础"},
            },
        ],
    }


def use_context_question() -> dict:
    return {
        "id": "use_context",
        "target_slot": "use_context",
        "title": "这个脚本主要会用在哪类场景？",
        "description": "使用场景会决定练习材料和项目安排。",
        "choices": [
            {
                "id": "files",
                "label": "整理文件",
                "description": "围绕照片、文档、文件夹规则整理。",
                "fills": {"use_context": "整理照片、文档和文件夹"},
            },
            {
                "id": "office",
                "label": "办公处理",
                "description": "围绕表格、邮件和重复办公任务。",
                "fills": {"use_context": "办公自动化"},
            },
        ],
    }


def brief_response() -> dict:
    return {
        "title": "Python 文件自动化入门",
        "objective": {
            "one_sentence": "30 天内学会用 Python 完成基础文件整理自动化",
            "outcome": "能写出 2-3 个可复用的小脚本",
            "success_criteria": [
                "能批量重命名文件",
                "能按规则移动照片或文档",
            ],
        },
        "scope": {
            "include": ["Python 基础语法", "文件路径", "批量重命名", "文件分类"],
            "exclude": ["Web 后端", "复杂 GUI"],
            "light_touch": ["异常处理"],
        },
        "constraints": {
            "time_window": "30 天",
            "pace": "按短时多次学习设计",
            "learner_background": "零基础",
            "use_context": "整理照片和文档",
        },
        "strategy": {
            "route_type": "project_first",
            "rationale": "目标很实用，适合围绕脚本产出学习必要语法。",
        },
        "assumptions": ["没有精确每日时长时，默认按轻量节奏推进"],
        "risks": ["30 天只适合入门和完成小脚本，不适合系统掌握 Python"],
        "preview": {
            "phases": [
                {
                    "phase_name": "语法热身",
                    "focus": "变量、循环、函数",
                    "estimated_child_count": 3,
                },
                {
                    "phase_name": "文件操作",
                    "focus": "路径、遍历、移动",
                    "estimated_child_count": 3,
                },
                {
                    "phase_name": "脚本产出",
                    "focus": "照片和文档整理",
                    "estimated_child_count": 2,
                },
            ],
        },
        "sections": [
            {
                "id": "context",
                "title": "为什么这样安排",
                "kind": "context",
                "summary": "从文件整理切入，避免铺开太多 Python 主题。",
                "bullets": ["先能做出脚本，再补基础细节"],
                "editable": True,
            },
            {
                "id": "practice",
                "title": "练习方式",
                "kind": "practice",
                "summary": "每个阶段都产出一个可运行的小脚本。",
                "bullets": ["批量重命名", "按日期分类"],
                "editable": True,
            },
        ],
    }


def test_missing_required_slot_asks_dynamic_question() -> None:
    client = FakeIntakeClient(
        [
            slots_response(learning_subject="Python"),
            target_outcome_question(),
        ]
    )

    result = start_plan_intake(
        client,
        goal="我想学 Python",
        duration_days=30,
        daily_minutes=25,
    )

    assert result.status == "needs_choice"
    assert result.completeness.missing_required == ["target_outcome"]
    assert result.question is not None
    assert result.question.target_slot == "target_outcome"
    assert {choice.id for choice in result.question.choices} == {
        "automation",
        "data_analysis",
    }

    extraction_payload = json.loads(client.messages[0][1].content)
    assert extraction_payload["raw_intent"] == "我想学 Python"
    assert extraction_payload["required_slots"] == [
        "learning_subject",
        "target_outcome",
    ]


def test_ready_when_required_and_enough_optional_slots_are_filled() -> None:
    client = FakeIntakeClient(
        [
            slots_response(
                learning_subject="Python 自动化",
                target_outcome="整理照片和文档",
                time_window="30 天",
                learner_background="零基础",
                use_context="个人文件管理",
            ),
            brief_response(),
        ]
    )

    result = start_plan_intake(
        client,
        goal="30 天学 Python 做自动化，主要整理照片和文档，零基础",
        duration_days=30,
        daily_minutes=25,
    )

    assert result.status == "ready"
    assert result.brief is not None
    assert result.completeness.filled_optional[:2] == [
        "use_context",
        "learner_background",
    ]
    assert result.brief.objective.one_sentence.startswith("30 天内学会")
    assert result.brief.schedule.total_minutes == 750
    assert result.brief.preview.phases[0].phase_name == "语法热身"
    assert result.brief.sections[0].kind == "context"


def test_required_filled_but_optional_below_threshold_asks_priority_slot() -> None:
    client = FakeIntakeClient(
        [
            slots_response(
                learning_subject="Python",
                target_outcome="写自动化脚本",
            ),
            use_context_question(),
        ]
    )

    result = start_plan_intake(
        client,
        goal="我想学 Python 写自动化脚本",
        duration_days=30,
        daily_minutes=25,
    )

    assert result.status == "needs_choice"
    assert result.completeness.missing_required == []
    assert result.completeness.target_slot == "use_context"
    assert result.question is not None
    assert result.question.target_slot == "use_context"


def test_optional_priority_uses_context_before_background() -> None:
    state = PlanIntakeState(
        raw_intent="我想学 Python 写自动化脚本",
        duration_days=30,
        daily_minutes=25,
        slots=IntentSlots(
            learning_subject="Python",
            target_outcome="写自动化脚本",
        ),
    )

    completeness = evaluate_completeness(state)

    assert completeness.ready is False
    assert completeness.target_slot == "use_context"
    assert len(completeness.filled_optional) == 0
    assert MIN_OPTIONAL_SLOTS == 2


def test_answer_records_choice_and_next_round_can_return_brief() -> None:
    client = FakeIntakeClient(
        [
            slots_response(learning_subject="Python"),
            target_outcome_question(),
            slots_response(
                learning_subject="Python",
                target_outcome="写出自动化脚本",
                use_context="文件和重复任务自动化",
                learner_background="零基础",
            ),
            brief_response(),
        ]
    )

    first = start_plan_intake(
        client,
        goal="我想学 Python",
        duration_days=30,
        daily_minutes=25,
    )
    result = answer_plan_intake(
        client,
        first.state,
        choice_id="automation",
        notes="主要想整理照片和文档。",
    )

    assert result.status == "ready"
    assert result.brief is not None
    assert result.state.round == 1
    assert result.brief.user_choices[0].choice_id == "automation"
    assert result.brief.slots.target_outcome == "写出自动化脚本"

    second_payload = json.loads(client.messages[2][1].content)
    assert second_payload["conversation_history"][0]["label"] == "自动化脚本"
    assert second_payload["notes"] == "主要想整理照片和文档。"


def test_round_limit_only_for_optional_slots() -> None:
    client = FakeIntakeClient(
        [
            slots_response(
                learning_subject="Python",
                target_outcome="写自动化脚本",
            ),
            brief_response(),
        ]
    )
    state = PlanIntakeState(
        raw_intent="我想学 Python 写自动化脚本",
        duration_days=30,
        daily_minutes=25,
        round=MAX_INTAKE_ROUNDS,
    )

    result = evaluate_plan_intake(client, state)

    assert result.status == "ready"
    assert result.completeness.forced_by_round_limit is True
    assert result.brief is not None


def test_round_limit_does_not_skip_required_slots() -> None:
    client = FakeIntakeClient(
        [
            slots_response(learning_subject="Python"),
            target_outcome_question(),
        ]
    )
    state = PlanIntakeState(
        raw_intent="我想学 Python",
        duration_days=30,
        daily_minutes=25,
        round=MAX_INTAKE_ROUNDS,
    )

    result = evaluate_plan_intake(client, state)

    assert result.status == "needs_choice"
    assert result.completeness.missing_required == ["target_outcome"]


def test_default_time_is_not_treated_as_user_time() -> None:
    client = FakeIntakeClient(
        [
            slots_response(learning_subject="Python"),
            target_outcome_question(),
        ]
    )

    start_plan_intake(
        client,
        goal="准备学 Python",
        duration_days=30,
        daily_minutes=25,
        time_is_default=True,
    )

    payload = json.loads(client.messages[0][1].content)
    assert payload["time_is_default"] is True
    assert payload["default_duration_days"] == 30
    assert "Extract time only from the raw_intent" in payload["time_note"]


def test_rejects_unknown_choice() -> None:
    client = FakeIntakeClient(
        [
            slots_response(learning_subject="Python"),
            target_outcome_question(),
        ]
    )
    first = start_plan_intake(
        client,
        goal="我想学 Python",
        duration_days=30,
        daily_minutes=25,
    )

    with pytest.raises(ValueError, match="unknown intake choice"):
        answer_plan_intake(client, first.state, choice_id="not-a-choice")


def test_rejects_answer_without_pending_question() -> None:
    client = FakeIntakeClient([])
    state = PlanIntakeState(
        raw_intent="90 天准备算法面试",
        duration_days=90,
        daily_minutes=60,
    )

    with pytest.raises(ValueError, match="no pending question"):
        answer_plan_intake(client, state, choice_id="focus_core")


def test_rejects_invalid_slot_response() -> None:
    client = FakeIntakeClient([{"status": "needs_choice"}])

    with pytest.raises(ValueError, match="invalid intent slots"):
        start_plan_intake(
            client,
            goal="3 天精通 Python",
            duration_days=3,
            daily_minutes=15,
        )


def test_rejects_question_for_wrong_slot() -> None:
    client = FakeIntakeClient(
        [
            slots_response(
                learning_subject="Python",
                target_outcome="写自动化脚本",
            ),
            background_question(),
        ]
    )

    with pytest.raises(ValueError, match="target_slot must match"):
        start_plan_intake(
            client,
            goal="我想学 Python 写自动化脚本",
            duration_days=30,
            daily_minutes=25,
        )


def test_plan_intake_prompt_includes_slot_gate_and_dynamic_brief_rules() -> None:
    prompt = build_system_prompt()

    assert "structured intent slots" in prompt
    assert "learning_subject" in prompt
    assert "target_outcome" in prompt
    assert "dynamic intake question" in prompt
    assert "fixed core plus dynamic sections" in prompt
    assert "preview" in prompt
