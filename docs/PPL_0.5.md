# PPL 0.5 — Developer Experience

PPL 0.5 makes the language easier to learn, inspect, format, test, and prototype.

## Goals

- one-command project scaffolding with `ppl init`
- readable diagnostics
- `ppl fmt` source formatting
- `ppl test` test discovery and execution
- `ppl repl` interactive experimentation
- clear beginner examples and documentation

## Commands

```bash
ppl init my-app
ppl check app.ppl
ppl compile app.ppl
ppl run app.ppl
ppl trace app.ppl
ppl fmt app.ppl
ppl test
ppl repl
```

## Learning path

```text
README.md
  -> docs/GETTING_STARTED.md
  -> examples/hello_world.ppl
  -> examples/incident.ppl
  -> docs/SPEC.md
```

These commands are wired in the `ppl` CLI. `ppl fmt --write` updates a file in place. `ppl test` runs pytest when it is installed.
