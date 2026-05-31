# Algorithm Tutor Demo

This demo shows the first openkeri reference loop with a deterministic
rule-based teacher.

The reference problems are exposed through a `LearningTaskRegistry` in
`examples/algorithm_tutor/registry.py`. The task type is `algorithm_problem`,
and each task bundle attaches the legacy `Problem` plus its `ProblemTestSuite`
as named resources.

It uses the problem "Longest Substring Without Repeating Characters" and runs
four fixed turns:

1. incorrect submission
2. incorrect submission
3. incorrect submission, now escalated from hint to explanation
4. correct submission

Run it from the repository root:

```bash
.venv/bin/python examples/algorithm_tutor/demo.py
```

The demo does not call an LLM. It is intentionally deterministic so the core
runtime can be tested reliably.

## Interactive Demo

The interactive demo lets you provide a Python solution file path for the same
problems:

```bash
.venv/bin/python examples/algorithm_tutor/interactive.py
```

The process keeps memory in memory while it runs. Submit the same incorrect
solution several times to see the teacher move from `hint` to `explanation`.

Try the included sample files:

```text
examples/algorithm_tutor/solutions/incorrect.py
examples/algorithm_tutor/solutions/correct.py
examples/algorithm_tutor/solutions/palindrome_incorrect.py
examples/algorithm_tutor/solutions/palindrome_correct.py
```

## Mock LLMTeacher Demo

This demo uses `LLMTeacher` with a mock LLM client, so it does not require an API
key:

```bash
.venv/bin/python examples/algorithm_tutor/llm_mock_demo.py
```

## DeepSeek LLMTeacher Demo

This optional demo uses a real DeepSeek API call through `DeepSeekClient`:

```bash
export OPENKERI_DEEPSEEK_API_KEY=your_api_key
.venv/bin/python examples/algorithm_tutor/llm_deepseek_demo.py
```

Optional configuration:

```bash
export OPENKERI_DEEPSEEK_MODEL=deepseek-v4-flash
export OPENKERI_DEEPSEEK_BASE_URL=https://api.deepseek.com
```
