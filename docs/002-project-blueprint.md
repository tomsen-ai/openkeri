# Project Blueprint

This document defines the first engineering shape of openkeri: the runtime
flow, module boundaries, proposed directory structure, MVP behavior, testing
strategy, and initial CI policy.

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
