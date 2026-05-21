# Algorithm Tutor Demo

This demo shows the first openkeri reference loop with a deterministic
rule-based teacher.

It uses the problem "Longest Substring Without Repeating Characters" and runs
four fixed turns:

1. incorrect submission
2. incorrect submission
3. incorrect submission, now escalated from hint to explanation
4. correct submission

Run it from the repository root:

```bash
python examples/algorithm_tutor/demo.py
```

The demo does not call an LLM. It is intentionally deterministic so the core
runtime can be tested reliably.
