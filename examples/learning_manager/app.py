from __future__ import annotations

import os
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from draft_generator import LearningProjectDraft, build_project_draft
from planner import build_learning_state
from storage import LearningManagerStore

from openkeri.schemas import (
    LearningHistoryEntry,
    LearningHistoryEventType,
    LearningWorkItem,
)

STATE_PATH_ENV = "OPENKERI_LEARNING_MANAGER_STATE"
DIFFICULTY_VALUES = {"easy", "normal", "hard"}


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
            self.create_project(argument)
            return

        if command == "today":
            self.print_today()
            return

        if command == "map":
            self.print_map()
            return

        if command == "complete":
            self.complete_node(argument)
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
            "Unknown command. Run 'create-project', 'today', 'map', 'complete', "
            "'history', 'review', or 'status'."
        )
        print()

    def create_project(self, seed_text: str) -> None:
        print("Create a learning project")
        if not seed_text:
            seed_text = input("What do you want to learn? ").strip()

        if not seed_text:
            print("Please describe a learning goal in one sentence.")
            print()
            return

        draft = build_project_draft(seed_text)
        self.print_draft(draft)

        refinement = input("Adjust it (or press Enter to accept): ").strip()
        if refinement:
            draft = build_project_draft(f"{seed_text} {refinement}")
            print()
            self.print_draft(draft)

        self.state = build_learning_state(
            title=draft.title,
            goal=draft.goal,
            duration_days=draft.duration_days,
            focus_areas=draft.focus_areas,
        )
        self.store.save(self.state)

        print()
        project_title = self.state.project.title if self.state.project else draft.title
        print(f"Created project: {project_title}")
        print()
        self.print_today()

    def complete_node(self, argument: str) -> None:
        if self.state.project is None:
            print("Create a project first.")
            print()
            return

        node_id, difficulty, minutes_text, note = self.parse_completion(argument)
        if not node_id or difficulty not in DIFFICULTY_VALUES or minutes_text is None:
            print("Usage: complete <node_id> <easy|normal|hard> <minutes> [note]")
            print()
            return

        node = self.find_node(node_id)
        if node is None:
            print(f"Unknown node: {node_id}")
            print()
            return

        if node.status == "locked":
            print(f"Node {node.id} is still locked.")
            print()
            return

        try:
            minutes_spent = int(minutes_text)
        except ValueError:
            print("Minutes must be a number.")
            print()
            return

        node.status = "done"
        node.result = note or "Completed."
        node.difficulty = difficulty
        node.minutes_spent = minutes_spent
        node.completed_at = datetime.now(UTC)
        self.state.active_task_id = node.id

        unlocked = self.unlock_next_node(node)
        self.append_history(
            event_type="task_completed",
            summary=f"Completed {node.id}: {node.title}.",
            task_id=node.id,
            detail=node.result,
            tags=[difficulty, *node.tags],
        )
        self.store.save(self.state)

        print(f"Completed {node.id}: {node.title}")
        print(f"Difficulty: {difficulty}, minutes: {minutes_spent}")
        if note:
            print(note)
        if unlocked is not None:
            print(f"Unlocked {unlocked.id}: {unlocked.title}")
        else:
            print("Route complete.")
        print()

    def print_today(self) -> None:
        if self.state.project is None:
            print("No project yet. Run create-project first.")
            print()
            return

        main_node = self.next_main_node()
        review_node = self.next_review_node()

        print(f"Today: {date.today().isoformat()}")
        print()
        print("Main lesson:")
        if main_node is None:
            print("  None. The current route is complete.")
        else:
            print(
                f"  {main_node.id} {main_node.title} "
                f"({main_node.stage_title}, {main_node.estimated_minutes}m, "
                f"{main_node.status})"
            )
            next_node = self.node_after(main_node)
            if next_node is not None:
                print(f"  Next unlock: {next_node.id} {next_node.title}")

        print()
        print("Review:")
        if review_node is None:
            print("  None")
        else:
            print(f"  {review_node.id} {review_node.title}")
        print()

    def print_map(self) -> None:
        if self.state.project is None:
            print("No project yet. Run create-project first.")
            print()
            return

        print(f"Map: {self.state.project.title}")
        for stage_id, stage_title in self.stage_order():
            print()
            print(f"{stage_id} {stage_title}")
            for node in self.nodes_for_stage(stage_id):
                print(
                    f"  {self.status_icon(node.status)} {node.id} "
                    f"[{node.type}] {node.title} - {node.status}"
                )
        print()

    def print_review(self) -> None:
        if self.state.project is None:
            print("No project yet. Run create-project first.")
            print()
            return

        today = date.today()
        review_due = [
            node
            for node in self.state.tasks
            if node.status == "done"
            and node.review_after_days > 0
            and node.completed_at is not None
            and node.completed_at.date() + timedelta(days=node.review_after_days)
            <= today
        ]

        print("Review reminders")
        self.print_node_list(review_due)
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

    def print_status(self) -> None:
        if self.state.project is None:
            print("Project: none")
            print()
            return

        project = self.state.project
        done_nodes = [node for node in self.state.tasks if node.status == "done"]
        total_minutes = sum(node.minutes_spent or 0 for node in done_nodes)
        hard_nodes = len([node for node in done_nodes if node.difficulty == "hard"])

        print(f"Project: {project.title}")
        print(f"Goal: {project.goal}")
        print(f"Progress: {len(done_nodes)}/{len(self.state.tasks)} nodes")
        print(f"Study minutes: {total_minutes}")
        print(f"Hard nodes: {hard_nodes}")
        next_node = self.next_main_node()
        if next_node is not None:
            print(f"Next: {next_node.id} - {next_node.title}")
        print()

    def print_help(self) -> None:
        print("Commands:")
        print("  create-project [one-sentence goal]")
        print("  today")
        print("  map")
        print("  complete <node_id> <easy|normal|hard> <minutes> [note]")
        print("  history")
        print("  review")
        print("  status")
        print("  q")
        print()

    def print_draft(self, draft: LearningProjectDraft) -> None:
        print()
        print("Suggested route:")
        print(f"Title: {draft.title}")
        print(f"Goal: {draft.goal}")
        print(f"Duration: {draft.duration_days} days")
        print(f"Focus areas: {', '.join(draft.focus_areas)}")
        print("Milestones:")
        for index, milestone in enumerate(draft.milestones, start=1):
            print(f"  {index}. {milestone}")
        print()

    def next_main_node(self) -> LearningWorkItem | None:
        for status in ("active", "ready"):
            matching = [
                node
                for node in self.state.tasks
                if node.status == status and node.type != "review"
            ]
            if matching:
                return sorted(matching, key=lambda node: node.node_order)[0]
        return None

    def next_review_node(self) -> LearningWorkItem | None:
        due = [
            node
            for node in self.state.tasks
            if node.status == "review_due"
            or (
                node.status == "done"
                and node.review_after_days > 0
                and node.completed_at is not None
                and node.completed_at.date() + timedelta(days=node.review_after_days)
                <= date.today()
            )
        ]
        if not due:
            return None
        return sorted(due, key=lambda node: node.node_order)[0]

    def unlock_next_node(
        self, completed_node: LearningWorkItem
    ) -> LearningWorkItem | None:
        next_node = self.node_after(completed_node)
        if next_node is None:
            if self.state.project is not None:
                self.state.project.status = "completed"
            return None
        if next_node.status == "locked":
            next_node.status = "ready"
        return next_node

    def node_after(self, node: LearningWorkItem) -> LearningWorkItem | None:
        later_nodes = [
            candidate
            for candidate in self.state.tasks
            if candidate.node_order > node.node_order
        ]
        if not later_nodes:
            return None
        return sorted(later_nodes, key=lambda candidate: candidate.node_order)[0]

    def find_node(self, node_id: str) -> LearningWorkItem | None:
        for node in self.state.tasks:
            if node.id == node_id:
                return node
        return None

    def stage_order(self) -> list[tuple[str, str]]:
        stages: list[tuple[str, str]] = []
        for node in sorted(self.state.tasks, key=lambda item: item.node_order):
            if node.stage_id is None or node.stage_title is None:
                continue
            stage = (node.stage_id, node.stage_title)
            if stage not in stages:
                stages.append(stage)
        return stages

    def nodes_for_stage(self, stage_id: str) -> list[LearningWorkItem]:
        return sorted(
            [node for node in self.state.tasks if node.stage_id == stage_id],
            key=lambda node: node.node_order,
        )

    def print_node_list(self, nodes: list[LearningWorkItem]) -> None:
        if not nodes:
            print("  None")
            return
        for node in sorted(nodes, key=lambda item: item.node_order):
            print(f"  {node.id} {node.title} ({node.status})")

    def parse_completion(
        self,
        argument: str,
    ) -> tuple[str, str, str | None, str]:
        node_id, _, rest = argument.partition(" ")
        difficulty, _, rest = rest.partition(" ")
        minutes, _, note = rest.partition(" ")
        return (
            node_id.strip(),
            difficulty.strip(),
            minutes.strip() or None,
            note.strip(),
        )

    def status_icon(self, status: str) -> str:
        if status == "done":
            return "✓"
        if status in {"ready", "active"}:
            return "●"
        if status == "review_due":
            return "↻"
        return "○"

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
