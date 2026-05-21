from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from openkeri.agent import TeacherAgent
from openkeri.evidence import EvidenceCollector
from openkeri.memory import MemoryStore
from openkeri.schemas import CurrentInput, LearningEvent, TeacherOutput, TeachingContext


@dataclass
class TeachingSession:
    learner_id: str
    session_id: str
    memory_store: MemoryStore
    evidence_collector: EvidenceCollector
    teacher_agent: TeacherAgent

    def handle_turn(self, current_input: CurrentInput) -> TeacherOutput:
        memory_context = self.memory_store.get_context(
            learner_id=self.learner_id,
            session_id=self.session_id,
            problem_id=current_input.problem.id,
        )
        evidence = self.evidence_collector.collect(current_input)
        teaching_context = TeachingContext(
            current_input=current_input,
            memory_context=memory_context,
            evidence=evidence,
        )
        teacher_output = self.teacher_agent.respond(teaching_context)
        event = LearningEvent(
            event_id=uuid4().hex,
            learner_id=self.learner_id,
            session_id=self.session_id,
            current_input=current_input,
            evidence=evidence,
            teacher_output=teacher_output,
            timestamp=datetime.now(UTC),
        )
        self.memory_store.record_event(event)
        return teacher_output
