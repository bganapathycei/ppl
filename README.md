# PPL — Prompt Programming Language

PPL is an experimental AI-native programming language for expressing deterministic computation, AI reasoning, knowledge, tools, workflows, and human decisions as executable software.

> **The prompt is source code. The model is not the runtime.**

PPL source is parsed into an AST, compiled into a portable Prompt Intermediate Representation (PIR), and executed by a runtime that separates deterministic, cognitive, and human operations.

## v0.1

This first draft establishes the language concept and a small reference implementation with:

- `APP`, `INPUT`, `AGENT`, `CLASSIFY`, `EXTRACT`, `REASON`, `OUTPUT`
- `WORKFLOW`, `RECEIVE`, `RUN`
- `IF / ELSE IF / ELSE`, `RETURN`
- AST and PIR representations
- deterministic and cognitive execution paths
- local mock cognitive engine
- CLI commands: `check`, `compile`, `run`, `trace`
- incident-advisor reference example

## Architecture

```text
PPL Source
    |
    v
Lexer -> Parser -> AST -> Semantic Checks -> PIR
                                      |
                                      v
                               PPL Runtime
                               /    |    \\
                              D     C     H
                           Rules    AI   Human
```

`D` = deterministic, `C` = cognitive/model-backed, `H` = human-in-the-loop.

## Example

```text
APP IncidentAdvisor

INPUT incident
    description: TEXT
    application: TEXT
    priority: TEXT

AGENT Analyzer

    INPUT incident

    CLASSIFY incident.description AS
        ACCESS
        NETWORK
        DATABASE
        APPLICATION
        INFRASTRUCTURE
        OTHER

    EXTRACT
        root_cause
        resolution

    REASON
        determine whether the incident is repetitive

    OUTPUT
        category
        root_cause
        resolution
        repetitive
        confidence

WORKFLOW Main

    RECEIVE incident
    RUN Analyzer

    IF Analyzer.confidence >= 0.90
        RETURN "AUTOMATE"
    ELSE
        RETURN "KEEP_HUMAN"
```

## Roadmap

- **0.1** — parser, AST, PIR, runtime skeleton, CLI, reference example
- **0.2** — real AI gateway, structured cognitive outputs, model abstraction, output validation
- **0.3** — knowledge, memory, tools, multi-agent orchestration, human-in-loop
- **0.4** — guards, policy enforcement, evaluation language, debugger, tracing and cost telemetry
- **1.0** — production compiler/runtime, model routing, deployment, enterprise connectors and stable language specification

## Repository principle

Keep the language specification provider-neutral. Runtime semantics should be explicit enough to support multiple execution backends and model providers.
