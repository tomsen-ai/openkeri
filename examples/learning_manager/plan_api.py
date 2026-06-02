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
        if self.path != "/api/generate-plan":
            self.send_json({"error": "not_found"}, status=404)
            return

        try:
            payload = self.read_json()
            goal = str(payload.get("goal", "")).strip()
            if not goal:
                self.send_json({"error": "goal is required"}, status=400)
                return

            client = replace(
                DeepSeekClient.from_env(),
                max_tokens=4096,
                temperature=0.35,
            )
            draft = generate_plan_graph_draft(
                client,
                goal=goal,
                duration_days=coerce_int(payload.get("durationDays"), 30),
                daily_minutes=coerce_int(payload.get("dailyMinutes"), 25),
                preference=str(payload.get("preference", "")).strip(),
            )
        except (ValueError, DeepSeekClientError) as error:
            self.send_json({"error": str(error)}, status=500)
            return

        self.send_json(draft.model_dump(mode="json"))

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
        self.send_header("Access-Control-Allow-Origin", "http://localhost:5173")
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


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), PlanApiHandler)
    print(f"Plan API listening on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
