from typing import Literal

from pydantic import BaseModel


class Problem(BaseModel):
    id: str
    title: str
    description: str
    target_concepts: list[str]
    difficulty: str | None = None


class CodeSubmission(BaseModel):
    language: str
    code: str


class CurrentInput(BaseModel):
    interaction_type: Literal["submission", "follow_up"] = "submission"
    problem: Problem
    student_question: str | None = None
    code_submission: CodeSubmission | None = None
