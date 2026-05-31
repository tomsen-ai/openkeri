from registry import build_algorithm_tutor_registry, get_test_suite

from openkeri.agent import LLMTeacher, RuleBasedTeacher, TeacherAgent
from openkeri.evidence import PythonCodeRunnerEvidenceCollector
from openkeri.llm import LLMClient
from openkeri.memory import InMemoryMemoryStore
from openkeri.runtime import TeachingSession

DEFAULT_LEARNER_ID = "learner_001"


def build_rule_based_session(
    memory_store: InMemoryMemoryStore,
    problem_id: str,
    session_id: str | None = None,
) -> TeachingSession:
    return build_algorithm_tutor_session(
        memory_store=memory_store,
        problem_id=problem_id,
        teacher_agent=RuleBasedTeacher(),
        session_id=session_id or f"sess_{problem_id}",
    )


def build_llm_session(
    memory_store: InMemoryMemoryStore,
    problem_id: str,
    client: LLMClient,
    session_id: str | None = None,
) -> TeachingSession:
    return build_algorithm_tutor_session(
        memory_store=memory_store,
        problem_id=problem_id,
        teacher_agent=LLMTeacher(client=client),
        session_id=session_id or f"sess_llm_{problem_id}",
    )


def build_algorithm_tutor_session(
    memory_store: InMemoryMemoryStore,
    problem_id: str,
    teacher_agent: TeacherAgent,
    session_id: str,
) -> TeachingSession:
    task_registry = build_algorithm_tutor_registry()
    return TeachingSession(
        learner_id=DEFAULT_LEARNER_ID,
        session_id=session_id,
        memory_store=memory_store,
        evidence_collector=PythonCodeRunnerEvidenceCollector(
            test_suites={problem_id: get_test_suite(task_registry, problem_id)}
        ),
        teacher_agent=teacher_agent,
    )
