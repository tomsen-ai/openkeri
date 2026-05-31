from __future__ import annotations

import os
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from planner import build_learning_state
from storage import LearningManagerStore

from openkeri.schemas import (
    LearningHistoryEntry,
    LearningHistoryEventType,
    LearningWorkItem,
)

STATE_PATH_ENV = "OPENKERI_LEARNING_MANAGER_STATE"


class LearningManagerApp:
    def __init__(self, store: LearningManagerStore | None = None) -> None:
        self.store = store or LearningManagerStore(self.default_state_path())
        self.state = self.store.load()

    @staticmethod
    def default_state_path() -> Path:
        return Path(
            os.environ.get(
                STATE_PATH_ENV,
                str(Path(__file__).with_name("learning_manager_state.json")),
            )
        )

    def run(self) -> None:
        print("openkeri Learning Manager")
        print()
        self.print_help()

        while True:
            raw_command = input("> ").strip()
            if not raw_command:
                continue
            if raw_command.lower() in {"q", "quit", "exit"}:
                print("Goodbye.")
                return
            self.handle_command(raw_command)

    def handle_command(self, raw_command: str) -> None:
        command, _, argument = raw_command.partition(" ")
        command = command.lower()
        argument = argument.strip()

        if command == "create-project":
            self.create_project()
            return

        if command == "today":
            self.print_today()
            return

        if command == "complete":
            self.complete_task(argument)
            return

        if command == "history":
            self.print_history()
            return

        if command == "review":
            self.print_review()
            return

        if command == "status":
            self.print_status()
            return

        print(
            "Unknown command. Run 'create-project', 'today', 'complete', "
            "'history', 'review', or 'status'."
        )
        print()

    def create_project(self) -> None:
        print("Create a learning project")
        title = input("Project title: ").strip()
        goal = input("Goal: ").strip()
        duration_raw = input("Duration in days [7]: ").strip()
        focus_raw = input("Focus areas (comma-separated): ").strip()

        try:
            duration_days = int(duration_raw or "7")
        except ValueError:
            print("Duration must be a number.")
            print()
            return

        focus_areas = [item.strip() for item in focus_raw.split(",") if item.strip()]
        if not focus_areas:
            focus_areas = ["general foundations"]

        self.state = build_learning_state(
            title=title,
            goal=goal,
            duration_days=duration_days,
            focus_areas=focus_areas,
        )
        self.store.save(self.state)

        print()
        print(f"Project: {self.state.project.title if self.state.project else title}")
        print(f"Goal: {self.state.project.goal if self.state.project else goal}")
        if self.state.plan is None:
            plan_days = duration_days
        else:
            plan_days = self.state.plan.time_horizon_days
        print(f"Plan days: {plan_days}")
        print()
        self.print_today()

    def complete_task(self, argument: str) -> None:
        if self.state.project is None:
            print("Create a project first.")
            print()
            return

        if not argument:
            print("Usage: complete <task_id> [note]")
            print()
            return

        task_id, _, note = argument.partition(" ")
        task = self.find_task(task_id)
        if task is None:
            print(f"Unknown task: {task_id}")
            print()
            return

        if task.status == "done":
            print(f"Task {task.id} is already done.")
            print()
            return

        if not note:
            note = input("Result note (optional): ").strip()

        task.status = "done"
        task.result = note or "Completed."
        task.completed_at = datetime.now(UTC)
        self.state.active_task_id = task.id
        self.append_history(
            event_type="task_completed",
            summary=f"Completed {task.id}: {task.title}.",
            task_id=task.id,
            detail=task.result,
            tags=task.tags,
        )
        self.store.save(self.state)

        print(f"Completed {task.id}: {task.title}")
        if note:
            print(note)
        print()
        self.print_status()

    def print_today(self) -> None:
        if self.state.project is None or self.state.plan is None:
            print("No project yet. Run create-project first.")
            print()
            return

        today = date.today()
        open_tasks = [
            task
            for task in self.state.tasks
            if task.status != "done" and task.due_date <= today
        ]
        upcoming = [
            task
            for task in self.state.tasks
            if task.status != "done" and task.due_date > today
        ]

        print(f"Today: {today.isoformat()}")
        print("Due now:")
        self.print_task_list(open_tasks)
        print("Upcoming:")
        self.print_task_list(upcoming[:5])
        print()

    def print_history(self) -> None:
        if self.state.project is None:
            print("No project yet. Run create-project first.")
            print()
            return

        print(f"History for {self.state.project.title}")
        for entry in sorted(self.state.history, key=lambda item: item.created_at):
            timestamp = entry.created_at.strftime("%Y-%m-%d %H:%M")
            detail = f" - {entry.detail}" if entry.detail else ""
            task_ref = f" [{entry.task_id}]" if entry.task_id else ""
            print(f"{timestamp} {entry.event_type}{task_ref}: {entry.summary}{detail}")
        print()

    def print_review(self) -> None:
        if self.state.project is None:
            print("No project yet. Run create-project first.")
            print()
            return

        today = date.today()
        due_review_tasks = [
            task
            for task in self.state.tasks
            if task.type == "review"
            and task.status != "done"
            and task.due_date <= today
        ]

        spaced_repetition_reminders = [
            task
            for task in self.state.tasks
            if task.status == "done"
            and task.review_after_days > 0
            and task.completed_at is not None
            and task.completed_at.date() + timedelta(days=task.review_after_days)
            <= today
        ]

        upcoming_due_reviews = [
            task
            for task in self.state.tasks
            if task.type == "review" and task.status != "done" and task.due_date > today
        ][:5]

        print("Review reminders")
        print("Due now:")
        self.print_task_list(due_review_tasks)
        print("Spaced repetition:")
        self.print_task_list(spaced_repetition_reminders)
        print("Upcoming:")
        self.print_task_list(upcoming_due_reviews)
        print()

    def print_status(self) -> None:
        if self.state.project is None:
            print("Project: none")
            print()
            return

        project = self.state.project
        total_tasks = len(self.state.tasks)
        done_tasks = len([task for task in self.state.tasks if task.status == "done"])
        open_tasks = total_tasks - done_tasks
        next_due = self.next_due_task()

        print(f"Project: {project.title}")
        print(f"Goal: {project.goal}")
        window = (
            f"{project.start_date.isoformat()} -> {project.target_end_date.isoformat()}"
        )
        print(f"Window: {window}")
        print(f"Focus areas: {', '.join(project.focus_areas)}")
        print(f"Tasks: {done_tasks} done, {open_tasks} open")
        if next_due is not None:
            print(
                f"Next due: {next_due.id} - {next_due.title} "
                f"({next_due.due_date.isoformat()})"
            )
        print()

    def print_help(self) -> None:
        print("Commands:")
        print("  create-project")
        print("  today")
        print("  complete <task_id> [note]")
        print("  history")
        print("  review")
        print("  status")
        print("  q")
        print()

    def find_task(self, task_id: str) -> LearningWorkItem | None:
        for task in self.state.tasks:
            if task.id == task_id:
                return task
        return None

    def next_due_task(self) -> LearningWorkItem | None:
        pending = [task for task in self.state.tasks if task.status != "done"]
        if not pending:
            return None
        return sorted(
            pending,
            key=lambda task: (task.due_date, task.priority, task.id),
        )[0]

    def print_task_list(self, tasks: list[LearningWorkItem]) -> None:
        if not tasks:
            print("  None")
            return

        for task in sorted(
            tasks,
            key=lambda item: (item.due_date, item.priority, item.id),
        ):
            status = task.status
            source = f" <- {task.source_task_id}" if task.source_task_id else ""
            due = task.due_date.isoformat()
            print(
                f"  {task.id} [{task.type}] {task.title} "
                f"({due}, {task.estimated_minutes}m, {status}){source}"
            )

    def append_history(
        self,
        *,
        event_type: LearningHistoryEventType,
        summary: str,
        task_id: str | None = None,
        detail: str | None = None,
        tags: list[str] | None = None,
    ) -> None:
        next_index = len(self.state.history) + 1
        self.state.history.append(
            LearningHistoryEntry(
                id=f"event_{next_index:03d}",
                project_id=(
                    self.state.project.id if self.state.project else "project_001"
                ),
                task_id=task_id,
                event_type=event_type,
                summary=summary,
                detail=detail,
                created_at=datetime.now(UTC),
                tags=tags or [],
            )
        )
