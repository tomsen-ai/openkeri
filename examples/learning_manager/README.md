# Learning Manager Demo

This example is currently a learning-plan manager MVP, not a finished content
tutor. The product direction is:

```text
Create a learning project
  -> generate stages and route nodes
  -> schedule today's small tasks
  -> enter a lightweight session
  -> complete a node and unlock the next one
```

The detailed learning content inside each node is intentionally thin for now.
The next iterations should improve the planning framework first, then deepen
node-level teaching content.

## Run

CLI demo from the repository root:

```bash
.venv/bin/python examples/learning_manager/main.py
```

Frontend MVP:

```bash
open examples/learning_manager/frontend/index.html
```

The frontend is static and currently stores state in `localStorage`; there is no
backend API yet.

## Frontend Structure

```text
frontend/
  index.html              page structure
  styles.css              visual styling
  app.js                  render logic and UI events
  data/templates.js       route templates for algorithm / reading / custom
  lib/planner.js          creates Project -> Stage -> Node data
  lib/scheduler.js        builds the Today queue from all projects
  lib/storage.js          localStorage persistence
```

Current frontend data shape:

```text
state
  activeProjectId
  session { projectId, nodeId }
  projects[]
    stages[]
      nodes[]
    history[]
```

Keep the frontend lightweight until the interaction model settles. When a
backend is introduced, `lib/storage.js` is the first replacement point.

## Current Frontend Behavior

- `Today` shows scheduled tasks from multiple projects.
- `Projects` shows one active project as a staged route map.
- Clicking the colored route bar opens a project picker.
- Clicking an unlocked node opens a lightweight session page.
- Completing a session marks the node done, unlocks the next node, and writes
  history.
- `Create` generates a full project route from goal, type, duration, and daily
  minutes.

Known rough edges:

- The project route UI is still being tuned. The current direction is a light
  knowledge-route map with visible node relationships, not isolated dashboard
  cards.
- Node content is placeholder text. Do not spend too much time on teaching
  depth before the project/stage/node framework feels right.
- The browser may keep old `localStorage` state after data-shape changes. Clear
  local storage for `openkeri.frontend.v4` if the prototype looks inconsistent.

## CLI Commands

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

## Handoff Notes

Recent work focused on the frontend MVP split and project-map interaction:

- Split the frontend out of the previous single-file prototype.
- Added route templates and a planner/scheduler/storage split.
- Upgraded frontend data from flat `project.nodes` toward
  `project.stages[].nodes[]`.
- Added a project picker instead of cycling projects blindly by clicking the
  route bar.
- Started improving the Projects route map so nodes communicate sequence and
  dependency.

Suggested next steps:

1. Continue refining the Projects route map so it feels like a real knowledge
   route: clearer path, dependencies, node type, and current position.
2. Make the project picker feel integrated with the route bar and creation flow.
3. Improve Create route generation for different project types without adding a
   backend yet.
4. Keep Session lightweight: short content, steps, note, completion.
5. Once the frontend loop is stable, decide whether to back it with the existing
   Python schema/API or keep it static longer.

Useful checks:

```bash
node --check examples/learning_manager/frontend/app.js
PYTHONPATH=src:. pytest tests/test_learning_manager.py tests/test_schemas.py
git diff --check
```
