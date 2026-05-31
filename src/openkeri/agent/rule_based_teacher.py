from typing import Any, Literal

from pydantic import BaseModel

from openkeri.schemas import (
    Diagnosis,
    EvidenceItem,
    NextExpectedAction,
    TeacherOutput,
    TeachingAction,
    TeachingContext,
)

TeachingActionType = Literal["hint", "explanation"]
NextActionType = Literal["revise_code", "answer_question", "ask_followup", "continue"]


class RuleBasedTeacher(BaseModel):
    hint_threshold: int = 2

    def respond(self, context: TeachingContext) -> TeacherOutput:
        evidence_item = self._first_evidence_item(context)

        if evidence_item is None:
            return self._unclear_output(
                issue="missing_evidence",
                message="I do not have enough evidence to diagnose this turn.",
                next_action_type="ask_followup",
                next_instruction="Provide a question or a code submission.",
            )

        if evidence_item.type == "no_code_submission":
            return self._no_submission_output(context, evidence_item)

        if evidence_item.type in {"unsupported_language", "missing_test_suite"}:
            return self._tooling_limitation_output(context, evidence_item)

        if evidence_item.type == "execution_result":
            return self._execution_output(context, evidence_item)

        return self._unclear_output(
            issue=evidence_item.type,
            message="I cannot use this evidence type yet.",
            next_action_type="ask_followup",
            next_instruction="Provide a Python code submission for this problem.",
        )

    def _execution_output(
        self,
        context: TeachingContext,
        evidence_item: EvidenceItem,
    ) -> TeacherOutput:
        status = evidence_item.content.get("status")
        if status == "passed":
            return self._passed_output(context, evidence_item)
        if status == "failed":
            return self._failed_output(
                context,
                evidence_item,
                force_explanation=self._is_follow_up(context),
            )
        if status == "error":
            return self._runtime_error_output(context, evidence_item)

        return self._unclear_output(
            issue="unknown_execution_status",
            message="The execution result does not contain a usable status.",
            next_action_type="ask_followup",
            next_instruction="Submit the code again or provide more detail.",
        )

    def _no_submission_output(
        self,
        context: TeachingContext,
        evidence_item: EvidenceItem,
    ) -> TeacherOutput:
        concept = self._primary_concept(context)
        return TeacherOutput(
            diagnosis=Diagnosis(
                status="no_submission",
                issue=None,
                concept=concept,
                confidence=0.7,
                evidence_refs=[evidence_item.id],
                evidence_summary=evidence_item.summary,
            ),
            teaching_action=TeachingAction(
                type="hint",
                message=(
                    "Start by describing your current idea, or submit a first "
                    "attempt so we can inspect where it breaks."
                ),
                next_expected_action=NextExpectedAction(
                    type="answer_question",
                    instruction="Describe your approach or submit an initial solution.",
                ),
            ),
        )

    def _tooling_limitation_output(
        self,
        context: TeachingContext,
        evidence_item: EvidenceItem,
    ) -> TeacherOutput:
        concept = self._primary_concept(context)
        return TeacherOutput(
            diagnosis=Diagnosis(
                status="unclear",
                issue=evidence_item.type,
                concept=concept,
                confidence=0.6,
                evidence_refs=[evidence_item.id],
                evidence_summary=evidence_item.summary,
            ),
            teaching_action=TeachingAction(
                type="explanation",
                message=(
                    "I cannot verify this submission with the current local runner. "
                    "For now, use Python and a problem with a configured test suite."
                ),
                next_expected_action=NextExpectedAction(
                    type="ask_followup",
                    instruction=(
                        "Provide a supported Python submission or clarify the setup."
                    ),
                ),
            ),
        )

    def _runtime_error_output(
        self,
        context: TeachingContext,
        evidence_item: EvidenceItem,
    ) -> TeacherOutput:
        action_type = self._hint_or_explanation(context)
        concept = self._primary_concept(context)
        error = evidence_item.content.get("error")
        message = (
            f"Your code raises an error: {error}. Check the failing line and confirm "
            "that your function can run on the provided test input."
        )
        if action_type == "explanation":
            message = (
                f"The submission is not reaching the algorithm logic because it raises "
                f"{error}. Fix the runtime error first, then rerun the tests."
            )

        return TeacherOutput(
            diagnosis=Diagnosis(
                status="incorrect",
                issue="runtime_error",
                concept=concept,
                confidence=0.9,
                evidence_refs=[evidence_item.id],
                evidence_summary=evidence_item.summary,
            ),
            teaching_action=TeachingAction(
                type=action_type,
                message=message,
                next_expected_action=NextExpectedAction(
                    type="revise_code",
                    instruction="Fix the runtime error and submit again.",
                ),
            ),
        )

    def _failed_output(
        self,
        context: TeachingContext,
        evidence_item: EvidenceItem,
        force_explanation: bool = False,
    ) -> TeacherOutput:
        issue = self._diagnose_failed_issue(context, evidence_item)
        concept = (
            "sliding_window"
            if issue == "left_boundary_update_error"
            else (self._primary_concept(context))
        )
        action_type = (
            "explanation" if force_explanation else self._hint_or_explanation(context)
        )
        failed_case = self._first_failed_case(evidence_item)

        if action_type == "hint":
            message = self._failed_hint_message(issue, failed_case)
        else:
            message = self._failed_explanation_message(issue, failed_case)

        return TeacherOutput(
            diagnosis=Diagnosis(
                status="incorrect",
                issue=issue,
                concept=concept,
                confidence=0.84 if issue == "left_boundary_update_error" else 0.7,
                evidence_refs=[evidence_item.id],
                evidence_summary=evidence_item.summary,
            ),
            teaching_action=TeachingAction(
                type=action_type,
                message=message,
                next_expected_action=NextExpectedAction(
                    type="revise_code",
                    instruction="Revise the code and submit again.",
                ),
            ),
        )

    def _passed_output(
        self,
        context: TeachingContext,
        evidence_item: EvidenceItem,
    ) -> TeacherOutput:
        concept = self._primary_concept(context)
        return TeacherOutput(
            diagnosis=Diagnosis(
                status="correct",
                issue=None,
                concept=concept,
                confidence=0.9,
                evidence_refs=[evidence_item.id],
                evidence_summary=evidence_item.summary,
            ),
            teaching_action=TeachingAction(
                type="explanation",
                message=(
                    "The submitted code passes the configured tests. The core pattern "
                    f"for this problem is {concept}: maintain a valid state while "
                    "scanning the input."
                ),
                next_expected_action=NextExpectedAction(
                    type="continue",
                    instruction=(
                        "Move to a related practice problem or summarize the pattern."
                    ),
                ),
            ),
        )

    def _unclear_output(
        self,
        issue: str,
        message: str,
        next_action_type: NextActionType,
        next_instruction: str,
    ) -> TeacherOutput:
        return TeacherOutput(
            diagnosis=Diagnosis(
                status="unclear",
                issue=issue,
                concept=None,
                confidence=0.4,
                evidence_refs=[],
                evidence_summary=None,
            ),
            teaching_action=TeachingAction(
                type="explanation",
                message=message,
                next_expected_action=NextExpectedAction(
                    type=next_action_type,
                    instruction=next_instruction,
                ),
            ),
        )

    def _hint_or_explanation(self, context: TeachingContext) -> TeachingActionType:
        if context.memory_context.session_state.hint_count >= self.hint_threshold:
            return "explanation"
        return "hint"

    def _is_follow_up(self, context: TeachingContext) -> bool:
        return context.current_input.interaction_type == "follow_up"

    def _primary_concept(self, context: TeachingContext) -> str | None:
        concepts = context.current_input.problem.target_concepts
        return concepts[0] if concepts else None

    def _first_evidence_item(self, context: TeachingContext) -> EvidenceItem | None:
        if not context.evidence.items:
            return None
        return context.evidence.items[0]

    def _diagnose_failed_issue(
        self,
        context: TeachingContext,
        evidence_item: EvidenceItem,
    ) -> str:
        if context.current_input.problem.id == "leetcode_3":
            for failed_case in self._failed_cases(evidence_item):
                if failed_case.get("input") == "abba":
                    return "left_boundary_update_error"
        return "failing_test_case"

    def _failed_cases(self, evidence_item: EvidenceItem) -> list[dict[str, Any]]:
        failed_cases = evidence_item.content.get("failed_cases", [])
        if isinstance(failed_cases, list):
            return [case for case in failed_cases if isinstance(case, dict)]
        return []

    def _first_failed_case(self, evidence_item: EvidenceItem) -> dict[str, Any] | None:
        failed_cases = self._failed_cases(evidence_item)
        if not failed_cases:
            return None
        return failed_cases[0]

    def _failed_hint_message(
        self,
        issue: str,
        failed_case: dict[str, Any] | None,
    ) -> str:
        if issue == "left_boundary_update_error":
            return (
                "Your sliding window is close, but the left boundary update needs "
                "attention. Trace the input 'abba': when the second 'b' appears, "
                "where should left move?"
            )

        if failed_case is not None:
            return (
                "The code fails on at least one test case. Start by tracing "
                f"input {failed_case.get('input')!r} and compare your output with "
                f"the expected value {failed_case.get('expected')!r}."
            )

        return "The code fails on the configured tests. Trace one failing case first."

    def _failed_explanation_message(
        self,
        issue: str,
        failed_case: dict[str, Any] | None,
    ) -> str:
        if issue == "left_boundary_update_error":
            case_input = failed_case.get("input") if failed_case is not None else None
            return (
                "This fails because the left boundary moves backward when a "
                f"repeated character is seen in {case_input!r}. In a sliding "
                "window, left should only move forward; otherwise the window "
                "starts including characters that were already excluded."
            )

        if failed_case is not None:
            return (
                "The submission does not match the expected output on a configured "
                f"case: input {failed_case.get('input')!r}, expected "
                f"{failed_case.get('expected')!r}."
            )

        return (
            "The submission fails the configured tests. "
            "Compare the failing case manually."
        )
