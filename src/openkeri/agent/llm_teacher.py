from dataclasses import dataclass

from pydantic import ValidationError

from openkeri.agent.errors import LLMTeacherError
from openkeri.agent.llm_prompts import (
    DEFAULT_LLM_TEACHER_SYSTEM_PROMPT,
    build_llm_teacher_user_prompt,
)
from openkeri.llm import LLMClient, LLMMessage
from openkeri.schemas import TeacherOutput, TeachingContext


@dataclass
class LLMTeacher:
    client: LLMClient
    system_prompt: str = DEFAULT_LLM_TEACHER_SYSTEM_PROMPT

    def respond(self, context: TeachingContext) -> TeacherOutput:
        raw_output = self.client.complete_json(self._build_messages(context))
        try:
            return TeacherOutput.model_validate(raw_output)
        except ValidationError as exc:
            raise LLMTeacherError("LLM returned invalid TeacherOutput JSON.") from exc

    def _build_messages(self, context: TeachingContext) -> list[LLMMessage]:
        return [
            LLMMessage(role="system", content=self.system_prompt),
            LLMMessage(
                role="user",
                content=build_llm_teacher_user_prompt(context),
            ),
        ]
