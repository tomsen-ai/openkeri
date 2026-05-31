from dataclasses import dataclass

from pydantic import ValidationError

from openkeri.agent.errors import LLMTeacherError
from openkeri.agent.llm_prompts import (
    DEFAULT_LLM_TEACHER_SYSTEM_PROMPT,
    build_llm_teacher_user_prompt,
)
from openkeri.llm import LLMClient, LLMMessage
from openkeri.schemas import (
    Diagnosis,
    EvidenceItem,
    TeacherOutput,
    TeachingContext,
)


@dataclass
class LLMTeacher:
    client: LLMClient
    system_prompt: str = DEFAULT_LLM_TEACHER_SYSTEM_PROMPT

    def respond(self, context: TeachingContext) -> TeacherOutput:
        raw_output = self.client.complete_json(self._build_messages(context))
        try:
            output = TeacherOutput.model_validate(raw_output)
        except ValidationError as exc:
            raise LLMTeacherError("LLM returned invalid TeacherOutput JSON.") from exc

        if context.current_input.interaction_type == "follow_up":
            return self._normalize_follow_up_output(context, output)
        return output

    def _build_messages(self, context: TeachingContext) -> list[LLMMessage]:
        return [
            LLMMessage(role="system", content=self.system_prompt),
            LLMMessage(
                role="user",
                content=build_llm_teacher_user_prompt(context),
            ),
        ]

    def _normalize_follow_up_output(
        self,
        context: TeachingContext,
        output: TeacherOutput,
    ) -> TeacherOutput:
        diagnosis = output.diagnosis
        teaching_action = output.teaching_action
        teaching_action.type = "explanation"
        teaching_action.message = self._build_follow_up_message(context, diagnosis)
        if teaching_action.next_expected_action is not None:
            teaching_action.next_expected_action.instruction = (
                self._build_follow_up_instruction(context, diagnosis)
            )
        return output

    def _build_follow_up_message(
        self,
        context: TeachingContext,
        diagnosis: Diagnosis,
    ) -> str:
        failed_case = self._first_failed_case(context.evidence.items)
        case_input = failed_case.get("input") if failed_case is not None else None

        if diagnosis.issue == "left_boundary_update_error":
            if case_input is not None:
                return (
                    "The repeated character only matters while it is still inside "
                    f"the active window. In {case_input!r}, the boundary update "
                    "must keep the window moving forward; otherwise it reuses a "
                    "character that should already be outside the window."
                )
            return (
                "The repeated character only matters while it is still inside the "
                "active window. The boundary must keep moving forward so the "
                "window never includes an excluded character again."
            )

        if failed_case is not None:
            return (
                "Trace the failing case step by step and check whether the window "
                "invariant is still being preserved. The issue is in how the state "
                "changes when a repeated value appears inside the active range."
            )

        return (
            "Focus on the stored issue and explain the invariant that breaks, "
            "rather than giving a replacement line of code."
        )

    def _build_follow_up_instruction(
        self,
        context: TeachingContext,
        diagnosis: Diagnosis,
    ) -> str:
        if diagnosis.issue == "left_boundary_update_error":
            return (
                "Trace the active window and make sure the left boundary only "
                "moves forward."
            )
        return (
            "Trace the failing case and restate the invariant before changing the code."
        )

    def _first_failed_case(
        self,
        evidence_items: list[EvidenceItem],
    ) -> dict[str, object] | None:
        if not evidence_items:
            return None

        content = evidence_items[0].content
        if content.get("status") != "failed":
            return None

        failed_cases = content.get("failed_cases", [])
        if not isinstance(failed_cases, list) or not failed_cases:
            return None

        first_failed_case = failed_cases[0]
        if isinstance(first_failed_case, dict):
            return first_failed_case
        return None
