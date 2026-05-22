import json
from dataclasses import dataclass

from openkeri.agent.llm_client import LLMClient, LLMMessage
from openkeri.schemas import TeacherOutput, TeachingContext

DEFAULT_SYSTEM_PROMPT = """\
You are a teacher agent inside openkeri.

Given a TeachingContext, return a TeacherOutput JSON object.

Rules:
- Return JSON only.
- diagnosis.status must be one of: correct, incorrect, unclear, no_submission.
- teaching_action.type must be one of: hint, explanation.
- Prefer hint unless the learner has already received repeated hints.
- Do not reveal a full solution by default.
- Use evidence_refs when evidence supports the diagnosis.
"""


@dataclass
class LLMTeacher:
    client: LLMClient
    system_prompt: str = DEFAULT_SYSTEM_PROMPT

    def respond(self, context: TeachingContext) -> TeacherOutput:
        raw_output = self.client.complete_json(self._build_messages(context))
        return TeacherOutput.model_validate(raw_output)

    def _build_messages(self, context: TeachingContext) -> list[LLMMessage]:
        context_json = json.dumps(
            context.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
        )
        return [
            LLMMessage(role="system", content=self.system_prompt),
            LLMMessage(
                role="user",
                content=(
                    f"Produce TeacherOutput for this TeachingContext:\n{context_json}"
                ),
            ),
        ]
