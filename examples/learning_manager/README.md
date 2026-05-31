# Learning Manager Demo

This demo shows a minimal learning project manager built on top of openkeri.

Run it from the repository root:

```bash
.venv/bin/python examples/learning_manager/main.py
```

Supported commands:

```text
create-project
today
complete <task_id> [note]
history
review
status
q
```

The demo stores state in `examples/learning_manager/learning_manager_state.json`
by default. Set `OPENKERI_LEARNING_MANAGER_STATE` to point at a different file
when you want to isolate runs or tests.
