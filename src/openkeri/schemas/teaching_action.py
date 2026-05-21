from typing import Literal

from pydantic import BaseModel


class NextExpectedAction(BaseModel):
    type: Literal["revise_code", "answer_question", "ask_followup", "continue"]
    instruction: str


class TeachingAction(BaseModel):
    type: Literal["hint", "explanation"]
    message: str
    next_expected_action: NextExpectedAction | None = None
