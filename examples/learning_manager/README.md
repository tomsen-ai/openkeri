# Learning Manager Demo

Single-project learning plan MVP. Not a content tutor yet.

Current flow:

```text
Start: input goal
  -> Intake: LLM asks contextual questions (up to 5 rounds, dynamic choices)
  -> Brief: review plan draft + phase skeleton preview
  -> Editor: editable React Flow plan graph
       -> node status, add/delete/edit, edges, re-layout
       -> node learning page (placeholder content)
```

Intake and Brief are standalone pages that run before the graph editor appears.
The graph editor only shows after the user confirms the brief.

The intake loop is now fully LLM-driven: choices are generated dynamically from
the user's actual goal, not from a hardcoded menu. Each round the LLM evaluates
whether it has enough information (WHY / HOW MUCH / WHAT scope) to produce a
plan brief, or asks another contextual question. Max 5 rounds; if still unclear
after round 5, force_ready produces a conservative brief.

## Current State & Priority

**Priority 1: Flow rhythm (intake -> brief -> editor)**

This is the gate that determines whether the product is usable.

Shipped:
- Dynamic LLM-driven intake with contextual choices (no hardcoded menus).
- Plan skeleton preview inside brief (phase names, focus, node counts).
- Graceful retry on plan generation failure (auto-simplify hint, 重新生成
  button on frontend).
- User notes/context input on intake page.
- Conversation history passed through intake rounds so LLM remembers prior
  choices.
- Start / intake / brief pages visually redesigned (dark SaaS style, 8px
  corners, single-screen layouts).

Known gaps:

- Brief page feels like data review rather than "approving a plan." The user
  doesn't yet have a strong sense of buy-in before hitting generate.
- No page transition animations; the jump between screens is abrupt.
- The intake can still feel mechanical when the LLM produces generic questions
  or repetitive choices.
- Time constraints passed from the frontend are always treated as defaults
  (time_is_default=true) — the user can't yet set a hard schedule on the
  start page.

Next backend work:

- Improve the intake system prompt to produce more specific, non-generic
  questions. The current prompt sometimes falls back to pattern-matched choices.
- Add a "refine brief" endpoint so users can edit brief fields and re-negotiate
  without restarting the intake loop.

Next frontend work:

- Animate page transitions (start -> intake -> brief -> editor) so the user
  feels forward momentum.
- Add a brief editing mode before plan generation (inline field editing).

**Priority 2: Plan graph quality**

The generated graph must feel like a real learning route, not a generic
mind map.

- Node titles should be actionable ("手写快排" not "排序算法").
- Phase ordering must be obvious; child nodes should cluster cleanly.
- Time estimates need to be believable and not all identical.

**Priority 3: Node content depth**

Each node learning page currently shows generic placeholder study steps.
Eventually this should be AI-generated, node-specific content with:

- targeted explanation
- 1-2 practice prompts
- self-check questions
- learning notes

This is intentionally last. A beautiful learning page on a bad plan is useless.

## MVP Roadmap (shipped vs next)

Shipped:
1. Single project persistence via localStorage.
2. Export / import JSON.
3. React Flow editor: add, delete, edit nodes and edges; re-layout.
4. Node status (not_started / in_progress / done).
5. Basic node learning page (placeholder content).
6. Dynamic LLM-driven intake loop (contextual choices, up to 5 rounds).
7. Plan skeleton preview in brief (phase names, focus, node counts).
8. Graceful retry when graph generation fails (backend auto-simplify + frontend 重新生成 button).
9. User notes input on intake page.
10. Conversation history passed through intake rounds.
11. Start / intake / brief page visual redesign.

Next:
1. Brief page editing mode (inline field editing before generation).
2. Page transition animations (start -> intake -> brief -> editor).
3. Improve intake prompt quality (reduce generic/repetitive questions).
4. Node content generation per node (backend + frontend).
5. Editor visual polish: node cards, color system, edge styling.

## Architecture

```text
plan_api.py              HTTP server (intake + graph generation)
plan_intake.py           LLM-driven intake loop: goal -> contextual Q&A -> brief
plan_graph_generator.py  LLM prompt + validation for plan graph nodes/edges
plan_editor/
  src/main.jsx           React app: start / intake / brief / editor screens
  src/styles.css         all styles
```

API endpoints:

- `POST /api/intake/start` — start intake from goal
- `POST /api/intake/answer` — answer an intake choice
- `POST /api/generate-plan` — generate plan graph from brief

## Run

Backend:

```bash
export OPENKERI_DEEPSEEK_API_KEY=your_api_key
.venv/bin/python examples/learning_manager/plan_api.py
```

Frontend:

```bash
cd examples/learning_manager/plan_editor
npm install
npm run dev
```

Then open `http://127.0.0.1:5173/`.

Legacy static frontend and CLI demo still exist in `frontend/` and `main.py`
for reference, but active work is on the React Flow plan editor.

## Checks

```bash
cd examples/learning_manager/plan_editor && npm run build

cd /path/to/openkeri
.venv/bin/ruff check examples/learning_manager/plan_api.py \
  examples/learning_manager/plan_intake.py \
  examples/learning_manager/plan_graph_generator.py

PYTHONPATH=src:. pytest \
  tests/test_learning_manager_plan_intake.py \
  tests/test_learning_manager_plan_graph_generator.py \
  tests/test_learning_manager.py

git diff --check
```
