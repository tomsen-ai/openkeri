from typing import Any, Literal

from pydantic import BaseModel, Field


class FailedCase(BaseModel):
    input: Any
    expected: Any
    actual: Any


class ExecutionResult(BaseModel):
    status: Literal["passed", "failed", "error", "not_run"]
    passed_count: int = 0
    failed_count: int = 0
    failed_cases: list[FailedCase] = Field(default_factory=list)
    error: str | None = None


class EvidenceItem(BaseModel):
    id: str
    type: str
    source: str
    summary: str | None = None
    content: dict[str, Any]


class Evidence(BaseModel):
    items: list[EvidenceItem] = Field(default_factory=list)
