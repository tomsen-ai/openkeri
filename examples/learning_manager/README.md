# Learning Manager / Plan Studio

This is the active openkeri product direction.

Plan Studio is a single-project learning plan and knowledge-route workspace. It
starts from a free-form learning intent, negotiates only the information that is
actually missing, produces a plan brief, and then generates an editable mind map
with a node-level course workspace inside the canvas.

It is not a generic content tutor. The next major area is the course pipeline:
turning a node into a structured lesson/practice/qa experience that can be
reused and expanded.

## Product Flow

```text
Start: raw intent
  -> Intake: slot extraction + rule-based completeness gate
  -> Question: one dynamic contextual choice when required
  -> Brief: fixed core + dynamic sections
  -> Editor: editable mind-map plan canvas
       -> node status, add/delete/edit, import/export
       -> node learning workspace (lesson / practice / qa)
```

The active frontend is `plan_editor/`. The legacy static frontend and CLI demo
still exist for reference, but active work should target the mind-map editor.

The MVP course sample is now **Operating Systems basics**, starting with a node
like `Processes and Threads`. The earlier algorithm-oriented node is still
useful as a renderer reference, but it is no longer the product's first sample.

## Current Architecture

```text
plan_api.py              HTTP API for intake and graph generation
plan_intake.py           raw intent -> slots -> dynamic question or brief
plan_graph_generator.py  brief-aligned graph prompt + graph validation
plan_editor/
  src/main.jsx           React app: start / intake / brief / mind-map editor
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
-> 3 to 5 stage nodes as the route scaffold
-> learn/project child nodes inside each stage
```

It validates:

- exactly one goal node
- 3 to 5 stage nodes
- 8 to 18 total nodes
- no isolated non-goal nodes
- every non-goal node has an incoming edge
- every node is reachable from the goal node
- every stage has at least one child node
- stage children are only `learn` or `project` nodes
- all edges reference existing nodes

The generator now aligns to the brief:

- goal node reflects `objective.one_sentence`
- stage nodes follow `preview.phases`
- child nodes come from scope, success criteria, and dynamic sections
- excluded scope should not be introduced into the graph
- 5-stage briefs are compressed to avoid oversized graphs

Plan graph node kinds are intentionally small, with a computer-learning bias:

```text
goal     final observable capability or result
stage    ordered route segment
learn    one knowledge point or capability unit, with details inside the node
project  integrated output that combines multiple learn units
```

Edges carry a semantic `relation` field so generation, validation, and rendering
do not depend on free-form labels:

```text
next      main route progression
contains  stage owns a learn/project child
```

Former graph-level concepts are folded into node details: concept/practice/lab
content belongs inside `learn`; resources, review prompts, and acceptance
criteria belong inside `learn` or `project`; checkpoints are represented as
project acceptance criteria rather than separate default graph nodes.

## Course Pipeline

The node-level course pipeline should stay simple enough to expand later:

```text
node
-> learning points
-> lesson spec
-> lesson slides
-> practice pack
-> qa prompts
-> review notes / memory
```

The first implementation should make one OS node usable end-to-end before
generalizing the schema or generator.

## Plan Studio UI

The current frontend is a browser-based plan studio:

- start screen: one free-form intent box with example prompts
- intake screen: one dynamic 3-4 choice negotiation question
- brief screen: compact confirmation cards with inline detail editing
- editor screen: `mind-elixir` mind map canvas with import/export and local
  draft persistence
- node inspector: lightweight glass-style detail card for title, type,
  estimated time, status, and description

Development preview shortcuts:

```text
http://127.0.0.1:5173/?preview=intake
http://127.0.0.1:5173/?preview=brief
```

These shortcuts use local fixture data so UI changes can be reviewed without
calling the backend or LLM.

## Current State

Shipped:

1. Single project persistence via localStorage.
2. Export / import JSON.
3. Mind-map editor: add, delete, edit nodes through a `mind-elixir` canvas.
4. Node status: `not_started`, `in_progress`, `done`.
5. Basic node learning page with placeholder content.
6. Raw-intent intake with dynamic questions.
7. Rule-based slot completeness gate.
8. Dynamic plan brief with dynamic sections.
9. Brief-aligned graph generation.
10. DeepSeek transient network retry.
11. Unified Plan Studio UI flow with consistent OpenKeri branding.
12. Compact brief/intake preview modes for frontend iteration.

Known gaps:

- Mind-map editing is intentionally simple; complex cross-links and custom edge
  editing are not exposed in the UI yet.
- Graph layout uses `mind-elixir` tree layout; richer plan-specific layout
  rules may still be needed for large plans.
- Node learning pages still show generic placeholder content.
- Public/free deployment needs call budgets, rate limits, and provider options.

## Next Priorities

**Priority 1: Course Pipeline**

The visible map should stay simple. The next step is to make each node usable as
a course entry point:

- hand-authored learning points for the first OS node
- lesson slides with one clear teaching scene per slide
- practice packs with thinking fields and review criteria
- qa prompts that stay inside the node workspace
- notes and completion evidence written back to the node

**Priority 2: Route Clarity**

The plan graph should feel like an executable learning route, not a dense
knowledge graph. Improve generation and layout for:

- concise `goal/stage/learn/project` generation
- better stage balance and readable child counts
- optional review/project branches without overloading the visible map
- project nodes with requirements and acceptance criteria

The challenge is to keep the visible graph simple while preserving useful
learning detail inside nodes.

**Priority 3: Node-Level Learning**

After route clarity improves, generate node-specific learning content:

- targeted explanation
- 1-2 practice prompts
- self-check questions
- notes and reflection
- next-step recommendation

**Priority 4: Public Service Safety**

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

.venv/bin/python -m ruff format --check .

cd examples/learning_manager/plan_editor && npm run build
```
