# Learning Manager Demo

This example is currently a learning-plan manager MVP, not a finished content
tutor. The current active direction is a single-project plan graph editor:

```text
Create one learning project
  -> generate an editable plan graph
  -> manually adjust nodes and edges
  -> track node status
  -> enter a focused node learning page
```

The detailed learning content inside each node is intentionally thin for now.
The next iterations should improve plan graph quality first, then deepen
node-level teaching content.

## MVP Roadmap

Current priority: build one genuinely usable learning project before adding
multiple projects.

1. Single project persistence
   - Keep one active project.
   - Save the goal, plan graph, node details, edges, status, and updated time.
   - Restore the project after refresh.

2. Export and import
   - Export the current project as JSON.
   - Import JSON to restore the project.

3. Mind-map editing
   - Add nodes.
   - Delete nodes.
   - Edit node title, type, time, group, and description.
   - Add edges.
   - Delete edges.
   - Re-layout the graph after structural edits.

4. Node status
   - Track not started, in progress, and done.
   - Show status on the node without adding visual clutter.

5. Node learning page
   - Open a node as a focused learning page.
   - Show learning goal, core concepts, steps, practice, self-check, notes, and
     completion state.

6. AI node content generation
   - Generate learning content for a selected node.
   - Support regenerate, simplify, and add-practice actions.

Suggested implementation order:

1. Improve generated plan graph quality.
2. Refine the plan graph frontend interaction and layout.
3. Add AI-generated node learning content.

## Plan Graph Quality

Current focus: make the generated plan useful before deepening node content.

Generation improvements:

1. Prompt the LLM to produce one project only.
2. Prefer 3-5 main phases.
3. Put 2-4 child nodes under each phase.
4. Keep node types clear: goal, phase, concept, practice, project, review, and
   checkpoint.
5. Avoid too many nodes, isolated nodes, and dense cross-links.
6. Keep estimated time realistic.

Validation improvements:

1. Enforce a reasonable node count.
2. Require each phase to have at least one child node.
3. Reject edges that reference missing nodes.
4. Normalize missing status and node metadata.

Frontend plan graph improvements:

1. Keep the plan graph as the primary screen.
2. Reduce overlays that cover the graph.
3. Make editing tools available without dominating the canvas.
4. Keep the right detail panel secondary and dismissible.
5. Preserve user-edited graph structure during re-layout.
6. Keep the bottom generation input compact and centered.

## Run

CLI demo from the repository root:

```bash
.venv/bin/python examples/learning_manager/main.py
```

Legacy static frontend:

```bash
open examples/learning_manager/frontend/index.html
```

The static frontend is an older prototype. Keep it for reference, but the active
MVP work is now in the React Flow plan graph editor below.

Plan graph editor prototype:

```bash
export OPENKERI_DEEPSEEK_API_KEY=your_api_key
.venv/bin/python examples/learning_manager/plan_api.py

cd examples/learning_manager/plan_editor
npm install
npm run dev
```

Then open `http://127.0.0.1:5173/`.

This prototype calls DeepSeek to generate an editable plan graph, renders it
with React Flow, and supports local single-project persistence, export/import,
node editing, node status, node add/delete, edge editing, re-layout, and a basic
node learning page.

## Frontend Structure

This section describes the legacy static frontend, not the current React Flow
plan editor.

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

This behavior describes the legacy static frontend. The current active plan
editor is the React Flow prototype described in the Run section.

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

Older handoff notes for the static frontend:

- Split the frontend out of the previous single-file prototype.
- Added route templates and a planner/scheduler/storage split.
- Upgraded frontend data from flat `project.nodes` toward
  `project.stages[].nodes[]`.
- Added a project picker instead of cycling projects blindly by clicking the
  route bar.
- Started improving the Projects route map so nodes communicate sequence and
  dependency.

Legacy suggested next steps:

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
