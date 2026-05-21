from typing import Literal

from pydantic import BaseModel, Field


class Diagnosis(BaseModel):
    status: Literal["correct", "incorrect", "unclear", "no_submission"]
    issue: str | None = None
    concept: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)
    evidence_summary: str | None = None
