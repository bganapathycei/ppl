# Knowledge Memory and Tools

## Knowledge

`KNOWLEDGE` blocks declare authoritative external context:

```text
KNOWLEDGE ITOperations
    SOURCE runbooks
    SOURCE application_catalog
    SOURCE historical_incidents
```

### File resolution

`SOURCE name` loads the first match:

1. `knowledge/name.md` (or `.txt` / `.json`) next to the `.ppl` file
2. `examples/knowledge/` (bundled samples)
3. `PPL_KNOWLEDGE_DIR` override

Agents attach knowledge with:

```text
AGENT Analyzer
    USE KNOWLEDGE ITOperations
```

Knowledge text is injected into cognitive `REASON` / `CLASSIFY` / `EXTRACT` requests.

### Bundled knowledge files

| File | Content |
|---|---|
| `examples/knowledge/runbooks.md` | Operational runbooks |
| `examples/knowledge/application_catalog.md` | Application inventory |
| `examples/knowledge/historical_incidents.md` | Past incident patterns |

---

## Memory

```text
MEMORY IncidentHistory
    KEY incident.id
    READ incidents
    WRITE outcomes
```

### Persistence

Default path: `.ppl/memory/<AppName>.json`  
Override: `PPL_MEMORY_DIR`

Memory survives across runs keyed by `KEY` field. Used by agents via `USE MEMORY IncidentHistory`.

---

## Tools

```text
TOOL ServiceManagement
    ACTION create_ticket
    INPUT
        title: TEXT
        description: TEXT
        priority: TEXT
    OUTPUT
        ticket_id: ID
```

Invoke from workflow:

```text
CALL ServiceManagement.create_ticket
    title = "Automation candidate"
    description = Analyzer.root_cause
    priority = incident.priority
```

### Builtin actions

| Action | Behavior |
|---|---|
| `echo` | Returns arguments (debug/demo) |
| `write_json` | Writes JSON to a path |
| `create_ticket` | Appends ticket record to `.ppl/tickets.jsonl` |

Builtins are **fail-closed**: unknown actions error rather than silently no-op.

### Custom tool overrides

Map actions to Python callables in `ppl.tools.json`:

```json
{
  "create_ticket": "mymodule:create_ticket"
}
```

Override file path: `PPL_TOOLS_FILE`  
Ticket log path: `PPL_TICKET_LOG` (default `.ppl/tickets.jsonl`)

> **Note:** Custom `module:function` overrides require a Python environment with that module importable. Frozen/binary distributions may not support arbitrary imports.

---

## Example program

See `examples/enterprise_automation.ppl`:

```text
KNOWLEDGE + MEMORY → AGENT → CALL create_ticket → RETURN
```

```bash
ppl run examples/enterprise_automation.ppl
# → "DATABASE" + ticket line in .ppl/tickets.jsonl
```

---

**See also:** [[Examples]] · [[Language Reference]]
