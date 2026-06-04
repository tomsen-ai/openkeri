# Learning Manager / Plan Studio

This is the active openkeri product direction.

Plan Studio is a single-project learning plan and knowledge-route workspace. It
starts from a free-form learning intent, negotiates only the information that is
actually missing, produces a plan brief, and then generates an editable graph.

It is not a content tutor yet. Node-level learning content is the next major
area after route quality and graph layout are stable.

## Product Flow

```text
Start: raw intent
  -> Intake: slot extraction + rule-based completeness gate
  -> Question: one dynamic contextual choice when required
  -> Brief: fixed core + dynamic sections
  -> Editor: editable React Flow plan graph
       -> node status, add/delete/edit, edges, re-layout
       -> node learning page (placeholder content)
```

The active frontend is `plan_editor/`. The legacy static frontend and CLI demo
still exist for reference, but active work should target the React Flow editor.

## Current Architecture

```text
plan_api.py              HTTP API for intake and graph generation
plan_intake.py           raw intent -> slots -> dynamic question or brief
plan_graph_generator.py  brief-aligned graph prompt + graph validation
plan_editor/
  src/main.jsx           React app: start / intake / brief / editor screens
  src/styles.css         app styling
```

API endpoints:

- `POST /api/intake/start` — start intake from raw intent.
- `POST /api/intake/answer` — answer one dynamic intake choice.
- `POST /api/generate-plan` — generate a plan graph from the confirmed brief.

## Intake Model

The intake is not a fixed questionnaire. The first input is a raw natural
language intent, such as:

```text
我想 30 天提升英语口语，主要用于工作会议表达观点、做简单汇报和回应同事问题；目前能日常交流，但会议上不够流畅，每天晚上能练一会儿。
```

The model extracts slots:

```text
required:
- learning_subject
- target_outcome

optional:
- use_context
- learner_background
- time_window
- available_rhythm
- preferred_style
```

Python rules decide whether the flow can continue:

```text
required slots missing -> ask one dynamic question
required slots filled + at least 2 optional slots -> generate brief
required slots filled + optional slots below threshold -> ask next priority slot
round limit reached -> allow only if required slots are filled
```

This keeps the start screen simple while avoiding generic plans.

## Plan Brief

The brief has a stable core plus dynamic sections.

Stable core:

- objective
- scope
- constraints
- strategy
- assumptions
- risks
- preview phases

Dynamic sections:

- context
- strategy
- time
- background
- output
- warning
- resources
- practice

The brief is the product's planning contract. The graph generator receives the
confirmed brief as structured context, not just as a loose text preference.

## Plan Graph

The graph generator currently uses this structure:

```text
one goal node
-> 3 to 5 phase nodes
-> child concept/practice/project/review/checkpoint/resource nodes
```

It validates:

- exactly one goal node
- 3 to 5 phase nodes
- 8 to 18 total nodes
- no isolated non-goal nodes
- every phase has at least one child node
- all edges reference existing nodes

The generator now aligns to the brief:

- goal node reflects `objective.one_sentence`
- phase nodes follow `preview.phases`
- child nodes come from scope, success criteria, and dynamic sections
- excluded scope should not be introduced into the graph
- 5-phase briefs are compressed to avoid oversized graphs

## Current State

Shipped:

1. Single project persistence via localStorage.
2. Export / import JSON.
3. React Flow editor: add, delete, edit nodes and edges; re-layout.
4. Node status: `not_started`, `in_progress`, `done`.
5. Basic node learning page with placeholder content.
6. Raw-intent intake with dynamic questions.
7. Rule-based slot completeness gate.
8. Dynamic plan brief with dynamic sections.
9. Brief-aligned graph generation.
10. DeepSeek transient network retry.

Known gaps:

- Brief page UI is only structurally compatible with the new brief; it still
  needs a better confirmation experience.
- Graph layout is still mostly route-like and phase-linear. Some learning plans
  need richer graph shapes: parallel branches, prerequisite clusters, review
  loops, convergence nodes, and optional side paths.
- Node learning pages still show generic placeholder content.
- Public/free deployment needs call budgets, rate limits, and provider options.

## Next Priorities

**Priority 1: Knowledge-Graph Route Quality**

The plan graph should not always feel linear. Improve generation and layout for:

- parallel tracks
- prerequisite clusters
- optional branches
- convergence/synthesis nodes
- review loops
- resource side paths
- better edge labeling

The challenge is to keep graph readability while allowing non-linear structure.

**Priority 2: Node-Level Learning**

After route quality improves, generate node-specific learning content:

- targeted explanation
- 1-2 practice prompts
- self-check questions
- notes and reflection
- next-step recommendation

**Priority 3: Public Service Safety**

Before any public free deployment:

- request/session/IP limits
- daily model call budget
- graph retry budget
- model provider configuration
- self-host/BYOK path

## Run

Backend:

```bash
export OPENKERI_DEEPSEEK_API_KEY=your_api_key
PYTHONPATH=src:. .venv/bin/python examples/learning_manager/plan_api.py
```

Frontend:

```bash
cd examples/learning_manager/plan_editor
npm install
npm run dev
```

Then open:

```text
http://127.0.0.1:5173/
```

## Checks

```bash
PYTHONPATH=src:. .venv/bin/python -m pytest \
  tests/test_learning_manager_plan_intake.py \
  tests/test_learning_manager_plan_graph_generator.py \
  tests/test_learning_manager.py

.venv/bin/python -m ruff check \
  examples/learning_manager/plan_api.py \
  examples/learning_manager/plan_intake.py \
  examples/learning_manager/plan_graph_generator.py

cd examples/learning_manager/plan_editor && npm run build
```
