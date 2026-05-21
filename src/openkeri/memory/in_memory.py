from pydantic import BaseModel, Field

from openkeri.schemas import (
    LearnerMemory,
    LearnerProfile,
    LearningEvent,
    MemoryContext,
    RelatedHistoryItem,
    SessionState,
)


class InMemoryMemoryStore(BaseModel):
    events: list[LearningEvent] = Field(default_factory=list)
    session_states: dict[str, SessionState] = Field(default_factory=dict)
    learner_memories: dict[str, LearnerMemory] = Field(default_factory=dict)

    def get_context(
        self,
        learner_id: str,
        session_id: str,
        problem_id: str | None = None,
    ) -> MemoryContext:
        session_state = self.session_states.get(session_id)
        if session_state is None:
            session_state = SessionState(
                session_id=session_id,
                current_problem_id=problem_id,
            )
            self.session_states[session_id] = session_state
        elif problem_id is not None:
            session_state.current_problem_id = problem_id

        learner_memory = self.learner_memories.get(learner_id)
        if learner_memory is None:
            learner_memory = LearnerMemory(
                learner_profile=LearnerProfile(learner_id=learner_id),
            )
            self.learner_memories[learner_id] = learner_memory

        return MemoryContext(
            session_state=session_state,
            learner_memory=learner_memory,
        )

    def record_event(self, event: LearningEvent) -> MemoryContext:
        self.events.append(event)

        session_state = self._get_or_create_session_state(event)
        learner_memory = self._get_or_create_learner_memory(event.learner_id)

        self._update_session_state(session_state, event)
        self._update_learner_memory(learner_memory, event)

        return MemoryContext(
            session_state=session_state,
            learner_memory=learner_memory,
        )

    def _get_or_create_session_state(self, event: LearningEvent) -> SessionState:
        session_state = self.session_states.get(event.session_id)
        if session_state is None:
            session_state = SessionState(session_id=event.session_id)
            self.session_states[event.session_id] = session_state
        return session_state

    def _get_or_create_learner_memory(self, learner_id: str) -> LearnerMemory:
        learner_memory = self.learner_memories.get(learner_id)
        if learner_memory is None:
            learner_memory = LearnerMemory(
                learner_profile=LearnerProfile(learner_id=learner_id),
            )
            self.learner_memories[learner_id] = learner_memory
        return learner_memory

    def _update_session_state(
        self,
        session_state: SessionState,
        event: LearningEvent,
    ) -> None:
        diagnosis = event.teacher_output.diagnosis
        teaching_action = event.teacher_output.teaching_action

        session_state.current_problem_id = event.current_input.problem.id
        session_state.last_teaching_action = teaching_action.type

        if teaching_action.type == "hint":
            session_state.hint_count += 1

        for action in self._current_actions(event):
            if action not in session_state.recent_actions:
                session_state.recent_actions.append(action)

        if diagnosis.status == "correct":
            session_state.problem_status = "completed"
            session_state.current_phase = "completed"
        elif diagnosis.status == "no_submission":
            session_state.problem_status = "in_progress"
            session_state.current_phase = "question"
        else:
            session_state.problem_status = "in_progress"
            session_state.current_phase = "working"

    def _update_learner_memory(
        self,
        learner_memory: LearnerMemory,
        event: LearningEvent,
    ) -> None:
        diagnosis = event.teacher_output.diagnosis
        if diagnosis.concept is None or diagnosis.issue is None:
            return

        existing_item = self._find_related_history_item(
            learner_memory=learner_memory,
            concept=diagnosis.concept,
            issue=diagnosis.issue,
        )

        if existing_item is not None:
            existing_item.seen_count += 1
            existing_item.last_seen_problem_id = event.current_input.problem.id
            return

        learner_memory.related_history.append(
            RelatedHistoryItem(
                concept=diagnosis.concept,
                issue=diagnosis.issue,
                seen_count=1,
                last_seen_problem_id=event.current_input.problem.id,
            )
        )

    def _find_related_history_item(
        self,
        learner_memory: LearnerMemory,
        concept: str,
        issue: str,
    ) -> RelatedHistoryItem | None:
        for item in learner_memory.related_history:
            if item.concept == concept and item.issue == issue:
                return item
        return None

    def _current_actions(self, event: LearningEvent) -> list[str]:
        actions: list[str] = []
        if event.current_input.code_submission is not None:
            actions.append("submitted_code")
        if event.current_input.student_question is not None:
            actions.append("asked_question")
        return actions
