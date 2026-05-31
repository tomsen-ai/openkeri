from datetime import UTC, datetime, timedelta

from openkeri.schemas import (
    LearningHistoryEntry,
    LearningManagerState,
    LearningPlan,
    LearningPlanDay,
    LearningProject,
    LearningWorkItem,
)


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
    plan_id = "plan_001"
    normalized_focus_areas = focus_areas or ["general foundations"]

    project = LearningProject(
        id=project_id,
        title=title,
        goal=goal,
        start_date=start_date,
        target_end_date=start_date + timedelta(days=max(duration_days - 1, 0)),
        focus_areas=normalized_focus_areas,
        success_criteria=[
            "Complete the daily tasks",
            "Review the missed points",
            "Write one short takeaway per task",
        ],
        created_at=now,
        updated_at=now,
    )

    tasks: list[LearningWorkItem] = []
    days: list[LearningPlanDay] = []
    next_task_index = 1
    previous_practice_task_id: str | None = None
    previous_focus_area = normalized_focus_areas[0]

    for day_index in range(max(duration_days, 1)):
        day_date = start_date + timedelta(days=day_index)
        focus_area = normalized_focus_areas[day_index % len(normalized_focus_areas)]
        day_task_ids: list[str] = []
        day_review_focus: list[str] = [focus_area]

        practice_task = LearningWorkItem(
            id=f"task_{next_task_index:03d}",
            project_id=project_id,
            type="practice",
            title=f"Practice {focus_area}",
            description=(
                f"Do one focused exercise on {focus_area}, then note the main "
                "mistake or insight."
            ),
            due_date=day_date,
            estimated_minutes=min(daily_capacity_minutes, 35),
            tags=[focus_area, "practice"],
            prerequisites=[],
            related_resources=[focus_area],
            created_at=now,
            review_after_days=2,
        )
        tasks.append(practice_task)
        day_task_ids.append(practice_task.id)
        next_task_index += 1

        if previous_practice_task_id is not None:
            review_task = LearningWorkItem(
                id=f"task_{next_task_index:03d}",
                project_id=project_id,
                type="review",
                title=f"Review {previous_focus_area}",
                description=(
                    f"Review yesterday's work on {previous_focus_area} and "
                    "restate the invariant or rule in one sentence."
                ),
                due_date=day_date,
                estimated_minutes=20,
                tags=[previous_focus_area, "review"],
                prerequisites=[previous_practice_task_id],
                related_resources=[previous_focus_area],
                created_at=now,
                source_task_id=previous_practice_task_id,
            )
            tasks.append(review_task)
            day_task_ids.append(review_task.id)
            day_review_focus.append(previous_focus_area)
            next_task_index += 1

        if (day_index + 1) % 3 == 0:
            summary_task = LearningWorkItem(
                id=f"task_{next_task_index:03d}",
                project_id=project_id,
                type="summary",
                title=f"Summarize {focus_area}",
                description=(
                    "Write a 3-sentence summary of what you learned and one "
                    "thing you still want to improve."
                ),
                due_date=day_date,
                estimated_minutes=15,
                tags=[focus_area, "summary"],
                prerequisites=[practice_task.id],
                related_resources=[focus_area],
                created_at=now,
                review_after_days=7,
            )
            tasks.append(summary_task)
            day_task_ids.append(summary_task.id)
            next_task_index += 1

        if day_index == max(duration_days, 1) - 1:
            project_task = LearningWorkItem(
                id=f"task_{next_task_index:03d}",
                project_id=project_id,
                type="project",
                title=f"Build a mini project with {focus_area}",
                description=(
                    "Combine the studied ideas into a tiny project or outline "
                    "that shows how the concepts work together."
                ),
                due_date=day_date,
                estimated_minutes=min(daily_capacity_minutes, 45),
                tags=[focus_area, "project"],
                prerequisites=[practice_task.id],
                related_resources=normalized_focus_areas,
                created_at=now,
                review_after_days=7,
            )
            tasks.append(project_task)
            day_task_ids.append(project_task.id)
            next_task_index += 1

        days.append(
            LearningPlanDay(
                date=day_date,
                task_ids=day_task_ids,
                review_focus=day_review_focus,
                notes=("Keep the daily scope small enough to finish in one sitting."),
            )
        )

        previous_practice_task_id = practice_task.id
        previous_focus_area = focus_area

    plan = LearningPlan(
        id=plan_id,
        project_id=project_id,
        time_horizon_days=max(duration_days, 1),
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
            summary=f"Generated a {len(days)}-day learning plan.",
            detail=", ".join(normalized_focus_areas),
            created_at=now,
        ),
    ]

    return LearningManagerState(
        project=project,
        plan=plan,
        tasks=tasks,
        history=history,
        active_task_id=tasks[0].id if tasks else None,
    )
