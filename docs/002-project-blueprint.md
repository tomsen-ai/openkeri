# Project Blueprint

This document defines the first engineering shape of openkeri: the runtime
flow, module boundaries, proposed directory structure, MVP behavior, testing
strategy, and initial CI policy.

## Current Product Track

Current development is centered on **Learning Manager / Plan Studio** under
`examples/learning_manager/`.

The older algorithm tutor still documents the first runtime experiment, but new
product work should not treat it as the primary direction. The active product is
a learning plan and knowledge-route workspace:

```text
raw intent
-> LLM slots
-> Python completeness gate
-> dynamic question
-> plan brief
-> user-confirmed brief
-> editable mind map
-> node-level learning workspace
```

The current UI direction intentionally keeps the visible route simple:
`goal/stage/learn/project` nodes rendered as an editable mind map, with graph
edge relations limited to `next` and `contains`. The next major product work is
node detail quality and node-level learning content, rather than adding many
graph-level relationship types.

### Node-Level Learning Direction

The current node-level learning design should stay inside the Learning Manager
track. Do not create a separate product line for it.

The design target is:

```text
Plan Graph
  outer route: goal / stage / learn / project

Node Learning Plan
  inner plan for one learn or project node

Activity Content
  concrete lesson/practice content or Q&A support generated on demand
```

The outer mind map should stay coarse. It should show the learning route, not
every teaching step. A node such as "Arrays and Linked Lists" is intentionally a
capability block. Its internal plan can break the work down into lessons,
practice interactions, Q&A support, and completion evidence.

Key rules:

- The plan graph is the route.
- A node is not a static article. It is a managed learning workspace.
- Node learning design should start from a hand-authored learning experience,
  not from tool abstractions.
- A `NodeLearningPlan` is generated once and persisted.
- Activity content is lazy generated and persisted.
- Prior memory can affect later activity content.
- The node plan should not be silently rewritten by the agent.
- Q&A is a node-level assistant capability, not a replacement for practice.

### Manual-First Node Design

The next design step should not be to implement tools immediately. Tool design
depends on the shape of the learning experience. The first pass should manually
author one complete node learning experience in this blueprint, review it with
the product experience in mind, and only then use it to derive fixtures,
schemas, tools, prompts, and UI.

Recommended first node:

```text
source node: n6 / Arrays and Linked Lists
working title: Linear Structure Pattern Training
stage: Foundation
goal: 30-day algorithm interview prep
```

This node should assume the learner already has basic programming knowledge and
knows the names of arrays, strings, and linked lists. It should not default to a
data-structures textbook explanation. It should train interview problem
handling:

```text
recognize the problem pattern
choose the right template
write stable code
review boundary and pointer mistakes
```

The first manual node should be organized by concrete learning points, not by a
new taxonomy of modules. Each learning point may only use these teaching
actions:

```text
lesson
practice
qa
```

`practice` maps to the formal `coding_practice` activity type later in the
implementation. `qa` is still a contextual node capability, not a replacement
for practice.

Do not introduce extra teaching action names such as drill, lab, worked-example
activity, template lab, or review-extraction activity. If the experience needs
examples, checks, feedback, or mistake capture, those details must live inside
`lesson`, `practice`, or `qa`.

The first manual node should start from these learning points:

| Learning point | lesson | practice | qa |
| --- | --- | --- | --- |
| Two pointers | Explain sorted-array and palindrome signals, left/right movement, and why one pointer move can eliminate candidates. | Practice with `Valid Palindrome` and/or `Two Sum II`. | Answer why `left` or `right` moves, whether `left < right` is required, and when a hash table is or is not preferable. |
| Sliding window | Explain contiguous substring/subarray signals, window boundaries, and hash state such as last-seen index or frequency. | Practice with `Longest Substring Without Repeating Characters`. | Answer why `left` must not move backward, what the window invariant is, and what the hash map stores. |
| Slow write pointer | Explain read/write pointers, in-place array modification, and the meaning of the valid prefix. | Practice with `Move Zeroes` and/or `Remove Duplicates from Sorted Array`. | Answer what `nums[:write]` means, when to write, and when to preserve relative order. |
| Dummy head and merge tail | Explain why a dummy head removes head-change special cases, why `dummy.next` is returned, and how a tail pointer builds a result list. | Practice with `Merge Two Sorted Lists` and the dummy-head part of `Remove Nth Node From End of List`. | Answer when dummy head is necessary, where `prev` or `tail` starts, and why returning `head` can be wrong. |
| Fast/slow pointer | Explain fixed gaps or speed differences, with the nth-from-end case as the primary MVP target. | Practice with `Remove Nth Node From End of List`. | Answer how many steps `fast` moves first, what gap is maintained, and whether the loop condition should be `fast` or `fast.next`. |
| Pointer reversal | Explain the linked-list reversal order: save `next`, rewire `curr.next`, then advance `prev` and `curr`. | Practice with `Reverse Linked List`. | Answer why `next` must be saved first and whether the final return value is `prev` or `curr`. |

The node should still avoid a large problem dump. The small practice pool is:

```text
Two Sum II or Valid Palindrome
  target: basic two-pointer movement

Longest Substring Without Repeating Characters
  target: sliding window + hash table

Move Zeroes or Remove Duplicates from Sorted Array
  target: in-place array modification
```

Linked-list practice should emphasize drawing pointer state, deciding whether a
dummy head is needed, naming boundary cases, and reviewing pointer update
order:

```text
Merge Two Sorted Lists
  target: dummy head and merge pointer

Remove Nth Node From End of List
  target: dummy head + fast/slow pointers

Reverse Linked List
  target: next-pointer preservation order
```

The node should not be marked complete just because content was viewed. The
learner should produce a review artifact:

```text
1. My linear-structure pattern recognition table
2. My two-pointer template
3. My sliding-window template
4. My linked-list dummy-head template
5. My linked-list reversal pointer order
6. Two mistakes I made or need to watch
7. Problems I should revisit
```

Completion criteria:

- complete at least four practice problems
- include at least one array/string medium problem
- include at least one linked-list medium problem
- explain the pattern choice for each completed problem
- record at least two personal mistake notes

This manual flow reveals the first tool needs:

```text
generate_training_lesson
select_or_generate_practice_problems
review_solution_or_code
extract_mistakes
update_node_memory
summarize_node_review
answer_contextual_question
```

These tool names are not final. They are observations from the manual flow.
Only after the manual node feels learnable should implementation define stable
tool names and schemas.

### Node Memory And Activities

Node learning needs separate memory layers:

```text
GoalMemory
  plan-level progress, recurring weaknesses, global recommendation

StageMemory
  stage-level progress, stage gaps, readiness for project/next stage

NodeMemory
  node-level progress, mistakes, strengths, gaps, review notes

ActivityEvent
  structured event produced by one interaction
```

`ActivityEvent` should be a structured record, not raw chat history. For
example, a coding-practice review can record the submitted work summary, agent
feedback summary, and a memory patch such as `missing_dummy_head` or
`pointer_update_order`.

For the first algorithm MVP, keep formal activity types small:

```text
lesson
coding_practice
```

Q&A should be available inside the node workspace as contextual support:

```text
qa
```

Q&A must use current goal, stage, node, activity, node memory, and relevant
stage/goal memory. It should answer questions about the current learning work,
not replace the activity flow.

### Node Plan Lifecycle

Node plans and generated activity content should be stable:

```text
First node open:
  no NodeLearningPlan exists
  -> generate NodeLearningPlan
  -> persist it

Later node open:
  NodeLearningPlan exists
  -> load it
  -> load NodeMemory
  -> do not regenerate the plan

Activity open:
  no ActivityContent exists
  -> generate content with memory context
  -> persist it

Later activity open:
  ActivityContent exists
  -> load it
  -> do not regenerate content
```

Regeneration should require an explicit user action. The agent may suggest a
future adjustment, but the MVP should not silently rewrite the user's plan.

### Node Learning Renderer Plan

The current frontend direction is to make node learning data-driven without
making the UI configurable by generated content.

The renderer should be fixed:

```text
NodeLearningWorkspace(plan_data)
  LessonRenderer(lesson_data)
  PracticeRenderer(practice_data)
  QaDrawer(qa_data)
```

Generated or fixture data may fill content, but must not introduce new teaching
actions or custom layouts. Data can define:

- node metadata
- learning points
- lesson slides
- practice problems
- Q&A suggested questions
- completion criteria

Data must not define:

- new teaching action types
- custom UI components
- page layout
- button behavior

For the first pass, keep the data as a local JavaScript object in the Plan
Studio frontend. Do not move it to a JSON fixture, Pydantic schema, API, or LLM
output format until the `Two Pointers` learning point feels usable.

Current implementation snapshot as of 2026-06-09:

- `examples/learning_manager/plan_editor/src/main.jsx` contains a local
  `NODE_LEARNING_PLAN` for `n6 / Arrays & Linked Lists`.
- The active working title remains `Linear Structure Pattern Training`.
- The first filled learning point is `Two Pointers`.
- The remaining learning points are present as route items but do not yet have
  full lesson/practice content.
- `NodeLearningWorkspace` now derives its UI from the local structured data.
- `LessonRenderer`, `PracticeRenderer`, and the Keri drawer are fixed renderers;
  generated data still must not define custom UI.
- `LessonHeader` is now a top-row control next to the `OpenKeri · Plan Studio`
  brand, not a full-width card inside the lesson.
- The node learning shell now follows the Plan Studio generation page visual
  system: light background, brand in the top row, centered work card, and
  responsive spacing.
- The right-bottom Keri launcher uses the OpenKeri brand mark rather than the
  temporary `mascot.png` image.
- Notes are stored per learning point and written back through
  `studyNode.data.learningNotes`, then persisted with the existing local draft.
- Practice drafts and feedback are still frontend state only.
- A local resolver maps the current fixed renderer to real plan nodes whose id
  is `n6` or whose title/description matches `Arrays & Linked Lists`,
  `数组 + 链表`, or `双指针 + 链表`; other nodes use the fallback node workspace.

The lesson renderer should follow a simple OpenMAIC-like slide lecture model,
but without adopting OpenMAIC's full multi-agent classroom complexity:

```text
lesson = slide deck
slide = one teaching scene
```

Initial lesson slide layouts should stay small:

```text
concept
concept_with_example
rule_summary
checkpoint
```

The practice renderer should be a fixed LeetCode-like workspace:

```text
problem list
problem statement
required thinking fields
code editor area
submit/review feedback
```

The Q&A renderer should remain inside the Keri drawer and use the current node,
learning point, lesson slide or practice problem, notes, and memory context. It
should not become a third main-screen flow.

The first implementation order for node-level learning is now:

1. Done: refactor the `Two Pointers` prototype into a fixed renderer plus local
   structured data.
2. Done: use that renderer to make the first learning point navigable:
   lesson slides, practice set, Q&A drawer, notes, and plan dropdown.
3. In progress: review the rendered `Two Pointers` experience before adding more learning
   points.
4. Hand-author and review the complete "Linear Structure Pattern Training" node
   learning design.
5. Convert that approved manual design into a fixture.
6. Derive the first schema fields from the fixture, not from generic agent
   abstractions.
7. Define Pydantic schemas for `NodeLearningPlan`, `NodeActivity`,
   `ActivityContent`, `NodeMemory`, and `ActivityEvent`.
8. Add a local persistence layer for node plans and node memory.
9. Implement node plan generation for algorithm `learn` nodes.
10. Implement lazy activity content generation for `lesson`.
11. Implement lazy activity content generation for `coding_practice`.
12. Add basic node memory display and manual notes.
13. Add coding submission review and structured memory patches.
14. Add contextual node Q&A.

It is not a marketing document. It is an engineering reference for future
implementation work. New modules should fit back into this blueprint or cause
the blueprint to be updated deliberately.

## 1. Project Shape

The first version of openkeri is a small Teacher Agent Runtime.

Its goal is to support a teacher agent through a structured teaching process:

```text
observe current input
-> load memory context
-> collect evidence
-> produce diagnosis
-> choose teaching action
-> update learning memory
```

The first reference implementation is an algorithm tutor for adult technical
learners.

The first version of openkeri does not aim to become:

- a general agent framework
- a chatbot framework
- a full LMS
- a course generation platform
- a multi-agent classroom
- a visual courseware tool

It should first prove one thing:

```text
A teacher agent can use learner input, learning memory, and evidence to produce
a structured diagnosis and choose an appropriate teaching action.
```

## 2. Runtime Flow

The first version of openkeri follows this runtime flow:

```text
current_input
+ memory_context
-> evidence_collector
-> teacher_agent
-> diagnosis
-> teaching_action
-> memory_update
```

In more detail:

1. Receive current input
   - The current problem.
   - The learner's question, if present.
   - The learner's code submission, if present.

2. Load memory context
   - The Memory Module generates `memory_context` from session state,
     long-term learner memory, preferences, and related history.

3. Collect evidence
   - The Evidence Collector extracts facts from the current input.
   - For the first algorithm tutor, this mainly means running code and
     collecting test results.

4. Produce diagnosis
   - The Teacher Agent uses current input, memory context, and evidence to
     identify the learner's main issue.

5. Choose teaching action
   - The first version supports only `hint` and `explanation`.

6. Return teaching action
   - The teaching action is returned to a frontend, CLI, or caller.

7. Update memory
   - The Memory Module records the learning event and updates session state and
     long-term learner memory.

## 3. Module Responsibilities

### schemas

`schemas` defines the core data structures and contracts.

It includes:

- learning task
- current input
- memory context
- evidence
- diagnosis
- teaching action
- learning event

`schemas` does not contain business logic.

### tasks

`tasks` manages reusable learning task registration.

It includes:

- `LearningTaskBundle`
- `LearningTaskRegistry`
- registry errors for duplicate tasks, missing tasks, and missing resources

The registry stores a generic `LearningTask` plus named resources. It should not
know about one domain, such as algorithm problems. Domain-specific resources are
attached by callers or examples.

For the first algorithm tutor, a task bundle contains:

```text
LearningTask(task_type="algorithm_problem")
+ resource["problem"] = Problem
+ resource["test_suite"] = ProblemTestSuite
```

Future task types may attach different resources, such as rubrics, passages,
retrieval settings, or task-specific diagnosis rules.

### memory

`memory` manages learning memory.

It includes:

- session state as short-term memory
- long-term learner memory
- learning event records
- learner preferences
- related history retrieval
- memory context generation
- memory updates after each teaching turn

`memory` does not produce teaching diagnoses or learner-facing feedback.

The first memory implementation should expose a small `MemoryStore` interface:

```text
get_context(learner_id, session_id, problem_id) -> MemoryContext
record_event(event) -> MemoryContext
```

The first concrete store is `InMemoryMemoryStore`. It keeps:

- learning events
- session states
- learner memories

The v0 implementation does not perform retrieval, compression, embedding
search, or database persistence.

### evidence

`evidence` turns the learner's current action into facts that can support
diagnosis.

For the first algorithm tutor, it mainly handles:

- running code
- executing test cases
- returning pass/fail results
- returning failed cases and runtime errors

`evidence` does not explain why the learner is wrong, and it does not teach.

The first evidence implementation should expose a small `EvidenceCollector`
interface:

```text
collect(current_input) -> Evidence
```

The first concrete collector is `PythonCodeRunnerEvidenceCollector`. Test suites
are passed to the collector, not stored on `Problem`. The collector delegates
Python execution to `PythonSubprocessRunner`, which runs submissions in a
separate Python process and applies a timeout before returning an
`ExecutionResult`.

The v0 Python runner is not a secure sandbox. It is only for trusted local demos
and tests. The subprocess boundary prevents a stuck submission from blocking the
main process indefinitely, but a production runner still needs stronger process
isolation, filesystem restrictions, and resource limits.

### agent

`agent` contains the teacher agent's core judgment.

It handles:

- producing `diagnosis` from evidence
- choosing a teaching action from diagnosis and memory context
- deciding whether to use `hint` or `explanation`

The first agent implementation should expose a small `TeacherAgent` interface:

```text
respond(teaching_context) -> TeacherOutput
```

The first concrete agent is `RuleBasedTeacher`. It reads execution evidence,
session hint count, and problem concepts to produce a structured diagnosis and
either a `hint` or an `explanation`. It is intentionally narrow so the first
runtime loop is deterministic and testable. It remains useful as a baseline and
for deterministic demos, but it is not intended to become a complete rule system
for every task.

`LLMTeacher` is an optional agent implementation. It depends on an `LLMClient`
interface instead of a specific provider. Tests and the default LLM demo use a
mock client so CI does not depend on network access, API keys, or model
stability. Its prompt lives in `llm_prompts.py` and must instruct the model to
use evidence first, avoid unsupported causes, and return a valid `TeacherOutput`
JSON object. If the provider returns JSON that does not validate as
`TeacherOutput`, `LLMTeacher` raises `LLMTeacherError`. Provider/API failures are
left to the concrete `LLMClient`.

### llm

`llm` contains provider-neutral LLM client interfaces and provider adapters.

It includes:

- `LLMMessage`
- `LLMClient`
- `DeepSeekClient`

`LLMTeacher` depends on the `LLMClient` protocol rather than a concrete provider.
`DeepSeekClient` is the first real provider implementation. It is optional,
configured through environment variables, and kept outside the default demo path.
It calls the DeepSeek chat completions API with JSON output enabled and returns
the parsed JSON object to `LLMTeacher` for `TeacherOutput` validation.

The project does not currently include a hybrid fallback teacher. If an
`LLMClient` or `LLMTeacher` fails, that error is allowed to propagate to the
caller. Product-specific error handling should live at the calling layer until a
clearer fallback requirement emerges.

### runtime

`runtime` orchestrates the full flow.

It calls:

```text
memory -> evidence -> agent -> memory
```

`runtime` should not contain concrete teaching strategy or storage details.

The first runtime implementation is `TeachingSession`:

```text
handle_turn(current_input) -> TeacherOutput
```

It is a fixed workflow for v0:

```text
get memory context
-> collect evidence
-> build teaching context
-> call teacher agent
-> create learning event
-> record memory
-> return teacher output
```

Future versions may replace the internals with a controlled Teacher Turn Loop,
while keeping the external turn-level interface stable.

### examples

`examples` provides runnable references.

The first example is:

```text
algorithm_tutor
```

It demonstrates:

```text
learner submits code
-> system runs tests
-> teacher agent diagnoses the issue
-> teacher agent returns a hint or explanation
-> memory is updated
```

### tests

`tests` validates core behavior.

The first tests should verify:

- schemas can be created
- evidence can return test results
- agent can produce diagnosis and teaching action from failed evidence
- runtime can execute one complete teaching turn
- memory can record learning events

## 4. Proposed Directory Structure

The first version uses a Python project structure:

```text
openkeri/
  .github/
    workflows/
      ci.yml
  README.md
  pyproject.toml
  docs/
    001-core-contract.md
    002-project-blueprint.md
    003-schema-contract.md
  src/
    openkeri/
      __init__.py
      schemas/
        __init__.py
        current_input.py
        memory.py
        evidence.py
        diagnosis.py
        teaching_action.py
        teacher_output.py
        context.py
        learning_event.py
        task.py
      tasks/
        __init__.py
        bundle.py
        errors.py
        registry.py
      memory/
        __init__.py
        base.py
        in_memory.py
      evidence/
        __init__.py
        base.py
        code_runner.py
        python_subprocess_runner.py
      agent/
        __init__.py
        base.py
        errors.py
        llm_prompts.py
        llm_teacher.py
        rule_based_teacher.py
      llm/
        __init__.py
        base.py
        deepseek.py
      runtime/
        __init__.py
        session.py
  examples/
    algorithm_tutor/
      README.md
      demo.py
      interactive.py
      llm_deepseek_demo.py
      llm_mock_demo.py
      problems.py
      registry.py
      session_factory.py
      tutor.py
      solutions/
        correct.py
        incorrect.py
        palindrome_correct.py
        palindrome_incorrect.py
  tests/
    test_algorithm_tutor_demo.py
    test_algorithm_tutor_interactive.py
    test_algorithm_tutor_llm_deepseek_demo.py
    test_algorithm_tutor_llm_mock_demo.py
    test_algorithm_tutor_problems.py
    test_algorithm_tutor_tutor.py
    test_deepseek_client.py
    test_llm_package.py
    test_schemas.py
    test_memory.py
    test_evidence.py
    test_python_subprocess_runner.py
    test_rule_based_teacher.py
    test_runtime_session.py
    test_tasks_registry.py
```

Directory principles:

- `schemas` defines data and contracts, not process.
- `tasks` registers learning tasks and their named resources.
- `memory` manages memory, not teaching judgment.
- `evidence` collects facts, not interpretation.
- `agent` diagnoses and chooses teaching action.
- `llm` defines provider-neutral LLM client interfaces and provider adapters.
- `runtime` orchestrates modules, not concrete strategy.
- `examples` shows how to use the framework.
- `tests` keep the loop stable.

## 5. First MVP Behavior

The first MVP only needs to support one minimal algorithm tutoring loop.
The tutor CLI supports two learner actions in that loop: submitting a Python
solution file and asking a follow-up question for the current problem.

Input:

```text
algorithm problem
optional learner question
learner code submission
memory context
test cases
```

Flow:

```text
1. Run learner code
2. Collect test result
3. If the code fails, produce diagnosis
4. Choose hint or explanation
5. Return teaching_action
6. Record learning_event
```

Output:

```text
diagnosis
teaching_action
```

Example:

```json
{
  "diagnosis": {
    "status": "incorrect",
    "issue": "left_boundary_update_error",
    "concept": "sliding_window",
    "evidence": "The submitted code fails on input 'abba'."
  },
  "teaching_action": {
    "type": "hint",
    "message": "Try tracing your code with input 'abba'. When the second 'b' appears, where should the left pointer move?",
    "next_expected_action": {
      "type": "revise_code",
      "instruction": "Update the left pointer logic and submit again."
    }
  }
}
```

The first version does not need to support:

- multi-problem recommendation
- visualizations
- code annotation
- slides
- complex multi-turn dialogue
- a real database
- a general-purpose fallback teacher
- a per-task diagnosis rule layer

## 6. Learning Loop Roadmap

openkeri should evolve toward a full learning loop, not only better
explanations.

The target learning loop is:

```text
diagnose -> teach -> practice -> assess -> remediate -> review -> update memory
```

The current implementation is only the first slice:

```text
v0: diagnose + hint/explanation + memory update
```

Future phases should expand the loop:

```text
v1: practice generation + assessment
v2: mistake book + review scheduling
v3: adaptive learning path
```

These phases should be added without turning openkeri into a generic chatbot or
a course generator. The runtime should keep producing structured domain objects
instead of only learner-facing text.

## 7. Testing Strategy

Every implementation step should include a minimal verification.

The first testing strategy is:

### schemas tests

Verify that core objects can be created and contain required fields.

### memory tests

Verify that memory can:

- write a learning event
- read session memory
- generate memory context

### evidence tests

Verify that:

- correct code returns passed
- incorrect code returns failed
- failed results include failed cases
- runtime errors are captured

### agent tests

Verify that:

- failed evidence can produce a diagnosis
- the default teaching action is a hint
- high hint count can lead to an explanation

### runtime tests

Verify the complete flow:

```text
current_input + memory
-> evidence
-> diagnosis
-> teaching_action
-> memory_update
```

The goal is not to cover every algorithm problem. The goal is to make the core
loop repeatable and testable.

## 8. CI Policy

CI should be added as soon as the first testable implementation exists.

The first CI pipeline should be minimal:

```text
install dependencies
run ruff check
run pytest
```

The first version should not include CD.

It should not automatically publish to PyPI, build Docker images, deploy docs,
or create releases. Those can be added after the project has a working alpha and
a stable package boundary.

Recommended first CI triggers:

```text
push
pull_request
```

Recommended first CI checks:

```text
ruff check
ruff format --check
pytest
```

Type checking may be added after the data model stabilizes.

## 9. Open Questions

These questions remain open:

- How should the code runner be isolated safely?
- How should `hint` vs `explanation` selection be defined?

These decisions have already been made for v0:

- Schemas use Pydantic v2.
- The first version includes LLMTeacher integration but does not depend on a
  real LLM API by default.
- DeepSeek is available as an optional `LLMClient`, but it is not required for
  CI or the default demos.
- Provider and `LLMTeacher` failures currently propagate to the caller; no
  generic fallback teacher is part of v0.
- A per-task diagnosis rule layer is deferred. Rule-based task diagnosis may be
  added later for high-value, high-confidence cases, but it is not required for
  every task.
- The first memory implementation is in-memory.
- The first runnable demo is a deterministic script.
- The first reference problem is `leetcode_3`.
- The first code runner supports only Python.
