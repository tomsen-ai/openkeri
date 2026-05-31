try:
    from .problems import REFERENCE_PROBLEMS
except ImportError:
    from problems import REFERENCE_PROBLEMS

from openkeri.evidence import ProblemTestSuite
from openkeri.schemas import LearningTask, Problem
from openkeri.tasks import LearningTaskBundle, LearningTaskRegistry

ALGORITHM_PROBLEM_TASK_TYPE = "algorithm_problem"
PROBLEM_RESOURCE = "problem"
TEST_SUITE_RESOURCE = "test_suite"


def build_algorithm_tutor_registry() -> LearningTaskRegistry:
    registry = LearningTaskRegistry()
    for problem_id, (build_problem, build_test_suite) in REFERENCE_PROBLEMS.items():
        problem = build_problem()
        registry.register(
            LearningTaskBundle(
                task=LearningTask(
                    id=problem.id,
                    title=problem.title,
                    description=problem.description,
                    task_type=ALGORITHM_PROBLEM_TASK_TYPE,
                    target_concepts=problem.target_concepts,
                    difficulty=problem.difficulty,
                    metadata={"source_problem_id": problem_id},
                ),
                resources={
                    PROBLEM_RESOURCE: problem,
                    TEST_SUITE_RESOURCE: build_test_suite(),
                },
            )
        )
    return registry


def get_problem(registry: LearningTaskRegistry, task_id: str) -> Problem:
    return registry.get(task_id).resource(PROBLEM_RESOURCE, Problem)


def get_test_suite(registry: LearningTaskRegistry, task_id: str) -> ProblemTestSuite:
    return registry.get(task_id).resource(TEST_SUITE_RESOURCE, ProblemTestSuite)
