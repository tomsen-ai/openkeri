import json

from openkeri.schemas import TeachingContext

DEFAULT_LLM_TEACHER_SYSTEM_PROMPT = """\
You are a teacher agent inside openkeri.

Given a TeachingContext, return one TeacherOutput JSON object.

Rules:
- Return JSON only.
- Use the evidence first. Do not invent unsupported causes.
- If evidence contains failed test cases, reference the failed input, expected
  value, and actual value when useful.
- If evidence contains a runtime error, missing entrypoint, timeout, unsupported
  language, or missing test suite, guide the learner to resolve that blocker
  before discussing algorithmic concepts.
- If the evidence does not support a specific issue, use a generic issue such as
  failing_test_case or set diagnosis.status to unclear.
- diagnosis.status must be one of: correct, incorrect, unclear, no_submission.
- diagnosis.confidence must be between 0.0 and 1.0.
- teaching_action.type must be one of: hint, explanation.
- Prefer hint unless the learner has already received repeated hints.
- Do not reveal a full solution by default.
- Use evidence_refs when evidence supports the diagnosis.
"""

TEACHER_OUTPUT_JSON_SHAPE = {
    "diagnosis": {
        "status": "correct | incorrect | unclear | no_submission",
        "issue": "string or null",
        "concept": "string or null",
        "confidence": 0.0,
        "evidence_refs": ["evidence item id"],
        "evidence_summary": "short evidence-based summary or null",
    },
    "teaching_action": {
        "type": "hint | explanation",
        "message": "learner-facing response",
        "next_expected_action": {
            "type": "revise_code | answer_question | ask_followup | continue",
            "instruction": "what the learner should do next",
        },
    },
}


def build_llm_teacher_user_prompt(context: TeachingContext) -> str:
    context_json = json.dumps(
        context.model_dump(mode="json"),
        ensure_ascii=False,
        indent=2,
    )
    output_shape_json = json.dumps(
        TEACHER_OUTPUT_JSON_SHAPE,
        ensure_ascii=False,
        indent=2,
    )
    return (
        "Produce TeacherOutput for this TeachingContext.\n\n"
        "Expected output JSON shape:\n"
        f"{output_shape_json}\n\n"
        "TeachingContext:\n"
        f"{context_json}"
    )
