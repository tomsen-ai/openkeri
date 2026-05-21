# openkeri

openkeri is a runtime for building adaptive teacher agents.

The first reference use case is an algorithm tutor for adult technical learners.
The project is currently in early design and MVP scaffolding.

## Core Loop

```text
current_input
+ memory_context
+ evidence
-> diagnosis
-> teaching_action
-> memory_update
```

## Development Status

The repository is not ready for production use. The first implementation will
focus on:

- Pydantic schemas
- in-memory learning memory
- execution evidence for simple algorithm problems
- a rule-based teacher agent
- a minimal runnable demo

See the `docs/` directory for the current design contracts.

## Run The Demo

```bash
.venv/bin/python examples/algorithm_tutor/demo.py
```

The demo is deterministic and does not call an LLM. It shows a learner failing
the same algorithm problem several times, receiving hints first, and then
getting an explanation after memory records repeated struggle.

## Local Verification

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
```
