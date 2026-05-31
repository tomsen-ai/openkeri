class LearningTaskRegistryError(RuntimeError):
    """Base error for learning task registry operations."""


class DuplicateLearningTaskError(LearningTaskRegistryError):
    """Raised when a task id is registered more than once."""


class LearningTaskNotFoundError(LearningTaskRegistryError):
    """Raised when a task id is not present in a registry."""


class LearningTaskResourceNotFoundError(LearningTaskRegistryError):
    """Raised when a named task resource is not present in a bundle."""
