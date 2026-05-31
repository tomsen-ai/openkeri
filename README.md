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
- learning task registry primitives
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

For a file-based interactive version:

```bash
.venv/bin/python examples/algorithm_tutor/interactive.py
```

For an LLMTeacher integration demo with a mock LLM client:

```bash
.venv/bin/python examples/algorithm_tutor/llm_mock_demo.py
```

For an optional DeepSeek-backed LLMTeacher demo:

```bash
export OPENKERI_DEEPSEEK_API_KEY=your_api_key
.venv/bin/python examples/algorithm_tutor/llm_deepseek_demo.py
```

For the learning project manager demo:

```bash
.venv/bin/python examples/learning_manager/main.py
```

`DeepSeekClient` prefers `OPENKERI_DEEPSEEK_API_KEY` and also accepts the common
`DEEPSEEK_API_KEY` environment variable.

The DeepSeek demo is not part of the default test path. It is intended for local
manual checks when an API key is available.

## Local Verification

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
```
