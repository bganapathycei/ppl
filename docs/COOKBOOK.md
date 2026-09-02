# PPL Cookbook

Practical recipes for daily PPL programs—deterministic scripts first, AI when needed.

## Calculator (no API key)

```bash
ppl run examples/calculator.ppl --input '{"calc": {"a": 4, "b": 5}}' --stdio
```

## Hello world script

```bash
ppl run examples/hello_world.ppl --stdio
```

## File copy / backup

```bash
ppl run examples/file_backup.ppl --input '{"backup": {"source": "README.md", "target": ".ppl/backup.txt"}}'
```

## Cron-friendly logging

Use `PRINT` for human output and `ppl run --stdio` in shell scripts:

```bash
ppl run my-script.ppl --stdio >> daily.log
```

## REST glue with stdlib

```text
IMPORT stdlib.http

WORKFLOW Main
    CALL http_get
        url = "https://httpbin.org/get"
    RETURN "ok"
```

## AI classification (requires provider)

```powershell
$env:PPL_AI_PROVIDER = "openai"
$env:OPENAI_API_KEY = "..."
ppl provider test
ppl run examples/hello_world_ai.ppl
```

## PROMPT templates

```text
PROMPT GreetingTemplate
    Classify as GREETING, QUESTION, or OTHER: {{text}}

AGENT Classifier
    INPUT request
    PROMPT GreetingTemplate WITH text=request.text
    OUTPUT category
```

## Provider profiles

`ppl.providers.json`:

```json
{
  "profiles": {
    "dev": { "provider": "local" },
    "prod": { "provider": "openai", "model": "gpt-4.1-mini" }
  },
  "active_profile": "dev"
}
```

Select with `PPL_PROFILE=prod` or an `ENVIRONMENT Production` block in source.
