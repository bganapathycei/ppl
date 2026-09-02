"""Render PROMPT templates with {{var}} placeholders."""
from __future__ import annotations

import re
from typing import Any


def render_template(template: str, bindings: dict[str, Any]) -> str:
    def repl(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        value = bindings.get(key, "")
        return str(value)

    return re.sub(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}", repl, template)


def prompt_body(name: str, prompts: list[dict[str, Any]]) -> str:
    for item in prompts:
        if item.get("name") == name:
            return "\n".join(item.get("body") or [])
    raise KeyError(f"Unknown PROMPT template: {name}")
