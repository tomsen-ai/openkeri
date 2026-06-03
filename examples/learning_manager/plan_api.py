from __future__ import annotations

import json
import sys
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if SRC.exists():
    sys.path.insert(0, str(SRC))

from plan_graph_generator import generate_plan_graph_draft  # noqa: E402
from plan_intake import (  # noqa: E402
    PlanBrief,
    PlanIntakeState,
    answer_plan_intake,
    start_plan_intake,
)

from openkeri.llm import DeepSeekClient, DeepSeekClientError  # noqa: E402

HOST = "127.0.0.1"
PORT = 8765


class PlanApiHandler(BaseHTTPRequestHandler):
    server_version = "OpenKeriPlanAPI/0.1"

    def do_OPTIONS(self) -> None:
        self.send_json({}, status=204)

    def do_GET(self) -> None:
        if self.path == "/health":
            self.send_json({"ok": True})
            return
        self.send_json({"error": "not_found"}, status=404)

    def do_POST(self) -> None:
        if self.path == "/api/intake/start":
            self.handle_intake_start()
            return
        if self.path == "/api/intake/answer":
            self.handle_intake_answer()
            return
        if self.path == "/api/generate-plan":
            self.handle_generate_plan()
            return

        self.send_json({"error": "not_found"}, status=404)

    def handle_intake_start(self) -> None:
        try:
            payload = self.read_json()
            goal = str(payload.get("goal", "")).strip()
            if not goal:
                self.send_json({"error": "goal is required"}, status=400)
                return

            client = make_deepseek_client()
            time_is_default = (
                "durationDays" not in payload and "dailyMinutes" not in payload
            )
            result = start_plan_intake(
                client,
                goal=goal,
                duration_days=coerce_int(payload.get("durationDays"), 30),
                daily_minutes=coerce_int(payload.get("dailyMinutes"), 25),
                time_is_default=time_is_default,
                background=str(payload.get("background", "")).strip(),
                intensity=str(payload.get("intensity", "")).strip(),
                preference=str(payload.get("preference", "")).strip(),
            )
        except (ValueError, DeepSeekClientError) as error:
            self.send_json({"error": str(error)}, status=500)
            return

        self.send_json(result.model_dump(mode="json"))

    def handle_intake_answer(self) -> None:
        try:
            payload = self.read_json()
            state_payload = payload.get("state")
            if not isinstance(state_payload, dict):
                self.send_json({"error": "state is required"}, status=400)
                return
            choice_id = str(payload.get("choiceId", "")).strip()
            if not choice_id:
                self.send_json({"error": "choiceId is required"}, status=400)
                return

            state = PlanIntakeState.model_validate(state_payload)
            client = make_deepseek_client()
            result = answer_plan_intake(
                client, state, choice_id=choice_id,
                notes=str(payload.get("notes", "")).strip(),
            )
        except (ValueError, DeepSeekClientError) as error:
            self.send_json({"error": str(error)}, status=500)
            return

        self.send_json(result.model_dump(mode="json"))

    def handle_generate_plan(self) -> None:
        try:
            payload = self.read_json()
        except (ValueError, DeepSeekClientError) as error:
            self.send_json({"error": str(error)}, status=400)
            return

        goal = str(payload.get("goal", "")).strip()
        if not goal:
            self.send_json({"error": "goal is required"}, status=400)
            return

        brief_payload = payload.get("brief")
        brief = (
            PlanBrief.model_validate(brief_payload)
            if isinstance(brief_payload, dict)
            else None
        )
        duration_days = coerce_int(payload.get("durationDays"), 30)
        daily_minutes = coerce_int(payload.get("dailyMinutes"), 25)
        if brief is not None:
            goal = brief.refined_goal
            duration_days = brief.constraints.duration_days
            daily_minutes = brief.constraints.daily_minutes

        preference = build_generation_preference(payload, brief)
        client = make_deepseek_client()

        try:
            draft = generate_plan_graph_draft(
                client,
                goal=goal,
                duration_days=duration_days,
                daily_minutes=daily_minutes,
                preference=preference,
            )
        except (ValueError, DeepSeekClientError) as error:
            error_text = str(error)
            if _is_plan_generation_retryable(error_text):
                try:
                    client = make_deepseek_client()
                    retry_preference = (
                        f"{preference}\n\n"
                        "IMPORTANT: The previous attempt failed because the graph "
                        "was too large or structurally invalid. Please simplify: "
                        "use fewer nodes (aim for 10-14 total), keep phases to 3-4, "
                        "and ensure every phase has at least one child node."
                    )
                    draft = generate_plan_graph_draft(
                        client,
                        goal=goal,
                        duration_days=duration_days,
                        daily_minutes=daily_minutes,
                        preference=retry_preference,
                    )
                except (ValueError, DeepSeekClientError) as retry_error:
                    self.send_json({"error": str(retry_error)}, status=500)
                    return
            else:
                self.send_json({"error": error_text}, status=500)
                return

        response = draft.model_dump(mode="json")
        if brief is not None:
            response["brief"] = brief.model_dump(mode="json")
        self.send_json(response)

    def read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ValueError("request body must be a JSON object")
        return parsed

    def send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        origin = self.headers.get("Origin")
        allowed_origin = origin if origin in {
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        } else "http://localhost:5173"
        self.send_header("Access-Control-Allow-Origin", allowed_origin)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if status != 204:
            self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}")


def coerce_int(value: object, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _is_plan_generation_retryable(error_text: str) -> bool:
    lower = error_text.lower()
    retryable_keywords = [
        "too_long",
        "too short",
        "min_length",
        "max_length",
        "at most",
        "at least",
        "isolated",
        "must contain",
        "invalid plan graph",
    ]
    return any(keyword in lower for keyword in retryable_keywords)


def make_deepseek_client() -> DeepSeekClient:
    return replace(
        DeepSeekClient.from_env(),
        max_tokens=4096,
        temperature=0.35,
    )


def build_generation_preference(
    payload: dict[str, Any],
    brief: PlanBrief | None,
) -> str:
    preference = str(payload.get("preference", "")).strip()
    if brief is None:
        return preference
    context = brief.to_prompt_context()
    return f"{preference}\n\nUse this negotiated PlanBrief:\n{context}".strip()


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), PlanApiHandler)
    print(f"Plan API listening on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
