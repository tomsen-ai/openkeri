# Learning Manager Demo

This demo shows a minimal learning project manager built on top of openkeri.

Run it from the repository root:

```bash
.venv/bin/python examples/learning_manager/main.py
```

For the visual prototype, open:

```bash
open examples/learning_manager/frontend/index.html
```

Supported commands:

```text
create-project [one-sentence goal]
today
map
complete <node_id> <easy|normal|hard> <minutes> [note]
history
review
status
q
```

`create-project` first shows a generated stage route draft and then lets you
adjust it with one short refinement before the project is created. The project
map starts with one ready node and unlocks the next node after completion.

The current draft generator is a rule-based fallback. The product direction is
LLM-first draft generation with the rule-based path kept as a fallback so the
demo stays usable without a model key.

The demo stores state in `examples/learning_manager/learning_manager_state.json`
by default. Set `OPENKERI_LEARNING_MANAGER_STATE` to point at a different file
when you want to isolate runs or tests.
