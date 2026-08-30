# PPL Examples

These examples are ordered from beginner to advanced.

## 1. Hello AI

`examples/hello_world.ppl` demonstrates the smallest useful PPL application.

Key ideas:

```text
APP -> INPUT -> AGENT -> CLASSIFY -> WORKFLOW
```

Start here if you are new to PPL.

## 2. Incident Advisor

`examples/incident.ppl` demonstrates two agents working in a deterministic workflow. It combines classification, extraction, reasoning, confidence, and branching.

The important pattern is:

```text
RUN Analyzer
RUN AutomationAdvisor
IF score >= threshold
    RETURN decision
```

## 3. Governed Change

`examples/governed_change.ppl` introduces 0.4 governance concepts:

- `GUARD`
- `AUTHORIZATION`
- `BUDGET`
- confidence-based human approval

This example illustrates an important PPL rule: risky actions should be governed by runtime-enforced controls, not merely by instructions given to a model.

## 4. Enterprise Automation

`examples/enterprise_automation.ppl` exercises knowledge files, persistent memory, tools, and optional human approval. Sample documents live in `examples/knowledge/`.

```text
KNOWLEDGE + MEMORY -> AGENT -> CALL create_ticket -> RETURN
```

## 5. Recommended learning path

1. Read `docs/GETTING_STARTED.md`.
2. Run `hello_world.ppl`.
3. Inspect its compiled representation.
4. Run `incident.ppl` and inspect the trace.
5. Read `docs/SPEC.md` and `docs/PPL_0.9.md`.
6. Study `governed_change.ppl` and `enterprise_automation.ppl`.
7. Build a small read-only business workflow before adding write-capable tools.

## 6. Example application ideas

Good first PPL applications include:

- IT incident triage
- QA defect classification
- invoice document extraction
- customer email routing
- contract clause analysis
- knowledge-grounded support recommendations

For a first production experiment, prefer recommendation-only behavior. Add write actions only after the cognitive behavior is evaluated and appropriate guards and approvals are in place.
