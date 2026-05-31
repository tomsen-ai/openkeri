import pytest

from examples.algorithm_tutor.registry import (
    ALGORITHM_PROBLEM_TASK_TYPE,
    build_algorithm_tutor_registry,
    get_problem,
    get_test_suite,
)
from openkeri.evidence import ProblemTestSuite
from openkeri.schemas import LearningTask, Problem
from openkeri.tasks import (
    DuplicateLearningTaskError,
    LearningTaskBundle,
    LearningTaskNotFoundError,
    LearningTaskRegistry,
    LearningTaskResourceNotFoundError,
)


def make_bundle(task_id: str = "task_001") -> LearningTaskBundle:
    return LearningTaskBundle(
        task=LearningTask(
            id=task_id,
            title="Trace a short passage",
            description="Read the passage and identify the key evidence.",
            task_type="reading_comprehension",
            target_concepts=["evidence_location"],
        ),
        resources={"rubric": {"required_evidence_count": 2}},
    )


def test_learning_task_registry_registers_and_gets_task_bundle() -> None:
    registry = LearningTaskRegistry()
    bundle = make_bundle()

    registry.register(bundle)

    assert registry.get("task_001") == bundle
    assert registry.list_tasks() == [bundle]


def test_learning_task_registry_rejects_duplicate_task_ids() -> None:
    registry = LearningTaskRegistry()
    registry.register(make_bundle())

    with pytest.raises(DuplicateLearningTaskError):
        registry.register(make_bundle())


def test_learning_task_registry_raises_for_missing_task() -> None:
    registry = LearningTaskRegistry()

    with pytest.raises(LearningTaskNotFoundError):
        registry.get("missing")


def test_learning_task_bundle_returns_typed_resources() -> None:
    bundle = make_bundle()

    rubric = bundle.resource("rubric", dict)

    assert rubric == {"required_evidence_count": 2}


def test_learning_task_bundle_raises_for_missing_resource() -> None:
    bundle = make_bundle()

    with pytest.raises(LearningTaskResourceNotFoundError):
        bundle.resource("missing", dict)


def test_algorithm_tutor_registry_wraps_reference_problems() -> None:
    registry = build_algorithm_tutor_registry()

    assert [bundle.task.id for bundle in registry.list_tasks()] == [
        "leetcode_3",
        "valid_palindrome",
    ]
    assert registry.get("leetcode_3").task.task_type == ALGORITHM_PROBLEM_TASK_TYPE
    assert isinstance(get_problem(registry, "leetcode_3"), Problem)
    assert isinstance(get_test_suite(registry, "leetcode_3"), ProblemTestSuite)
