from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from openkeri.schemas import (
    KnowledgeArea,
    LearningGoal,
    LearningHistoryEntry,
    LearningManagerState,
    LearningPlan,
    LearningPlanDay,
    LearningProject,
    LearningWorkItem,
)


@dataclass(frozen=True)
class StageTemplate:
    id: str
    title: str
    description: str
    topics: list[str]


def build_learning_state(
    title: str,
    goal: str,
    duration_days: int,
    focus_areas: list[str],
    daily_capacity_minutes: int = 60,
) -> LearningManagerState:
    now = datetime.now(UTC)
    start_date = now.date()
    project_id = "project_001"
    goal_id = "goal_001"
    plan_id = "plan_001"
    normalized_focus_areas = focus_areas or ["基础概念", "练习", "复盘"]
    stages = build_stage_templates(normalized_focus_areas)

    knowledge_areas = [
        KnowledgeArea(
            id=f"area_{index:03d}",
            project_id=project_id,
            title=focus_area,
            tags=[focus_area],
        )
        for index, focus_area in enumerate(normalized_focus_areas, start=1)
    ]
    area_id_by_focus = {area.title: area.id for area in knowledge_areas}

    learning_goal = LearningGoal(
        id=goal_id,
        title=title,
        description=goal,
        target_outcomes=[
            "Follow the stage route",
            "Finish one recommended node at a time",
            "Keep a short note after each completed node",
        ],
        constraints=[f"{daily_capacity_minutes} minutes per day"],
        created_at=now,
        updated_at=now,
    )

    project = LearningProject(
        id=project_id,
        goal_id=goal_id,
        title=title,
        goal=goal,
        start_date=start_date,
        target_end_date=start_date + timedelta(days=max(duration_days - 1, 0)),
        focus_areas=normalized_focus_areas,
        knowledge_area_ids=[area.id for area in knowledge_areas],
        success_criteria=[
            "Complete the stage route",
            "Review difficult nodes",
            "Finish the final project node",
        ],
        created_at=now,
        updated_at=now,
    )

    nodes: list[LearningWorkItem] = []
    node_index = 1
    previous_node_id: str | None = None

    for stage in stages:
        for topic in stage.topics:
            node_id = f"node_{node_index:03d}"
            node_type = "project" if topic == "综合项目" else "practice"
            if topic in {"阶段复盘", "综合复盘"}:
                node_type = "summary"

            nodes.append(
                LearningWorkItem(
                    id=node_id,
                    project_id=project_id,
                    type=node_type,
                    title=topic,
                    description=build_node_description(topic, stage.title),
                    status="ready" if node_index == 1 else "locked",
                    stage_id=stage.id,
                    stage_title=stage.title,
                    node_order=node_index,
                    due_date=start_date + timedelta(days=node_index - 1),
                    estimated_minutes=min(daily_capacity_minutes, 30),
                    tags=[stage.title, topic],
                    prerequisites=([previous_node_id] if previous_node_id else []),
                    related_resources=[topic],
                    knowledge_area_ids=(
                        [area_id_by_focus[topic]] if topic in area_id_by_focus else []
                    ),
                    created_at=now,
                    review_after_days=2,
                )
            )
            previous_node_id = node_id
            node_index += 1

    days = [
        LearningPlanDay(
            date=start_date + timedelta(days=index),
            task_ids=[node.id],
            review_focus=node.tags[-1:],
            notes="Follow the next unlocked node on the route.",
        )
        for index, node in enumerate(nodes)
    ]

    plan = LearningPlan(
        id=plan_id,
        project_id=project_id,
        time_horizon_days=max(duration_days, len(nodes), 1),
        daily_capacity_minutes=daily_capacity_minutes,
        days=days,
        generated_at=now,
    )

    history = [
        LearningHistoryEntry(
            id="event_001",
            project_id=project_id,
            event_type="project_created",
            summary=f"Created project {title}.",
            detail=goal,
            created_at=now,
        ),
        LearningHistoryEntry(
            id="event_002",
            project_id=project_id,
            event_type="plan_generated",
            summary=f"Generated a {len(stages)}-stage route.",
            detail=", ".join(stage.title for stage in stages),
            created_at=now,
        ),
    ]

    return LearningManagerState(
        goals=[learning_goal],
        project=project,
        plan=plan,
        tasks=nodes,
        knowledge_areas=knowledge_areas,
        history=history,
        active_task_id=nodes[0].id if nodes else None,
    )


def build_stage_templates(focus_areas: list[str]) -> list[StageTemplate]:
    first = focus_areas[:3] or ["基础概念"]
    second = focus_areas[3:6] or focus_areas[:2] or ["核心练习"]
    third = focus_areas[6:] or focus_areas[-2:] or ["综合训练"]

    return [
        StageTemplate(
            id="stage_001",
            title="基础热身",
            description="Build the starting vocabulary and basic moves.",
            topics=[*first, "阶段复盘"],
        ),
        StageTemplate(
            id="stage_002",
            title="核心套路",
            description="Practice the main patterns and connect them.",
            topics=[*second, "阶段复盘"],
        ),
        StageTemplate(
            id="stage_003",
            title="综合训练",
            description="Combine the route into review and output.",
            topics=[*third, "综合复盘", "综合项目"],
        ),
    ]


def build_node_description(topic: str, stage_title: str) -> str:
    if topic in {"阶段复盘", "综合复盘"}:
        return f"Review the completed nodes in {stage_title} and write one takeaway."
    if topic == "综合项目":
        return "Build a small final artifact that uses the main ideas from this route."
    return f"Study and practice {topic}, then leave a short note before moving on."
