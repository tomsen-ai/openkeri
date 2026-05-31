from __future__ import annotations

import re
from dataclasses import dataclass, field

ALGORITHM_FOCUS_AREAS = [
    "数组",
    "哈希",
    "双指针",
    "滑动窗口",
    "栈",
    "二分",
    "树",
    "图",
    "动态规划",
]

ALG_KEYWORDS = (
    "算法",
    "刷题",
    "leetcode",
    "双指针",
    "滑动窗口",
    "滑窗",
    "数组",
    "哈希",
    "栈",
    "二分",
    "树",
    "图",
    "动态规划",
)


@dataclass(slots=True)
class LearningProjectDraft:
    title: str
    goal: str
    duration_days: int
    focus_areas: list[str] = field(default_factory=list)
    milestones: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def build_project_draft(intent_text: str) -> LearningProjectDraft:
    intent = normalize_intent(intent_text)
    duration_days = extract_duration_days(intent)
    focus_areas = extract_focus_areas(intent)
    title = suggest_title(intent, focus_areas)
    goal = suggest_goal(intent, focus_areas, duration_days)
    milestones = build_milestones(focus_areas, duration_days)
    notes = build_notes(duration_days)

    return LearningProjectDraft(
        title=title,
        goal=goal,
        duration_days=duration_days,
        focus_areas=focus_areas,
        milestones=milestones,
        notes=notes,
    )


def normalize_intent(intent_text: str) -> str:
    intent = " ".join(intent_text.split()).strip()
    return intent


def extract_duration_days(intent: str) -> int:
    patterns = [
        (re.compile(r"(?P<value>\d+)\s*(?:天|day|days)", re.IGNORECASE), 1),
        (re.compile(r"(?P<value>\d+)\s*(?:周|week|weeks)", re.IGNORECASE), 7),
        (re.compile(r"(?P<value>\d+)\s*(?:月|month|months)", re.IGNORECASE), 30),
    ]
    for pattern, multiplier in patterns:
        match = pattern.search(intent)
        if match is not None:
            return max(int(match.group("value")) * multiplier, 1)
    return 14


def extract_focus_areas(intent: str) -> list[str]:
    explicit_focus_areas = [topic for topic in ALGORITHM_FOCUS_AREAS if topic in intent]
    if explicit_focus_areas:
        return explicit_focus_areas

    if any(keyword in intent.lower() for keyword in ALG_KEYWORDS):
        return ALGORITHM_FOCUS_AREAS[:7]

    return ["基础概念", "练习", "复盘"]


def suggest_title(intent: str, focus_areas: list[str]) -> str:
    if any(keyword in intent.lower() for keyword in ALG_KEYWORDS):
        return "算法学习计划"
    if "项目" in intent:
        return "项目学习计划"
    if focus_areas:
        return f"{focus_areas[0]}学习计划"
    return "学习计划"


def suggest_goal(intent: str, focus_areas: list[str], duration_days: int) -> str:
    if any(keyword in intent.lower() for keyword in ALG_KEYWORDS):
        focus_preview = "、".join(focus_areas[:4])
        return (
            f"在 {duration_days} 天内系统掌握算法核心套路，"
            f"重点覆盖 {focus_preview}，并形成稳定的复盘习惯。"
        )
    return f"围绕“{intent}”建立一个可执行的学习计划，并持续积累可复盘的学习记录。"


def build_milestones(focus_areas: list[str], duration_days: int) -> list[str]:
    first = "、".join(focus_areas[:2]) or "基础概念"
    middle = "、".join(focus_areas[2:4]) or first
    review = "、".join(focus_areas[:3]) or first
    final = "综合复习 + 小项目作业"

    if duration_days <= 7:
        return [
            f"先把 {first} 学通并完成基础练习。",
            f"再推进 {middle}，开始整理错因和笔记。",
            f"安排一次集中复盘，巩固 {review}。",
            final,
        ]

    return [
        f"第 1 阶段先打牢 {first}，建立解题和复盘节奏。",
        f"第 2 阶段推进 {middle}，把常见套路连起来。",
        f"第 3 阶段围绕 {review} 做错题回顾。",
        final,
    ]


def build_notes(duration_days: int) -> list[str]:
    spacing = 2 if duration_days <= 7 else 3
    return [
        "每天控制在一个可完成的小块里，不要把任务排成负担。",
        f"默认每 {spacing} 天安排一次回顾，优先复盘最近的错因。",
        "练习题只是任务的一种，后面还可以接总结和小项目。",
    ]
