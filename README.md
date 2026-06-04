# openkeri

openkeri is currently focused on **Learning Manager / Plan Studio**: an
AI-assisted learning plan and knowledge-route workspace.

The active product direction is not the older algorithm tutor. The algorithm
tutor remains in `examples/algorithm_tutor/` as an early runtime reference, but
current development should start from `examples/learning_manager/`.

## Active Product

Plan Studio turns a raw learning intent into an editable learning route:

```text
raw intent
-> dynamic intake questions
-> rule-based completeness gate
-> dynamic plan brief
-> editable plan graph
-> node-level learning page
```

The current implementation lives here:

```text
examples/learning_manager/
  plan_api.py              local HTTP API for intake and graph generation
  plan_intake.py           raw intent -> slots -> dynamic questions/brief
  plan_graph_generator.py  brief-aligned plan graph generation and validation
  plan_editor/             React Flow Plan Studio frontend
```

## Current Flow

1. The user enters a natural-language learning goal.
2. The intake model extracts structured slots from the raw intent.
3. Python rules decide whether required information is missing.
4. If needed, the model asks one contextual multiple-choice question.
5. Once enough information is known, the model creates a dynamic plan brief.
6. The user confirms the brief.
7. The graph generator creates an editable learning route aligned to the brief.

This is designed to keep the first screen free-form while avoiding hardcoded
menus and fixed upfront forms.

## Run Plan Studio

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

Open:

```text
http://127.0.0.1:5173/
```

## Verification

```bash
PYTHONPATH=src:. .venv/bin/python -m pytest
.venv/bin/python -m ruff check .
cd examples/learning_manager/plan_editor && npm run build
```

## Legacy Reference

`examples/algorithm_tutor/` is a deterministic teacher-agent runtime reference.
It is useful background for schemas, memory, evidence, and teacher-agent
experiments, but it is not the current product focus.
