"""Builtin and pluggable tool handlers for PPL CALL statements."""
from __future__ import annotations

import importlib
import json
import os
import uuid
from pathlib import Path
from typing import Any, Callable

from .v03_runtime import ToolRegistry


def echo(**kwargs: Any) -> dict[str, Any]:
    return {"tool": "echo", "args": kwargs, "status": "ok"}


def write_json(path: str = ".ppl/out.json", **kwargs: Any) -> dict[str, Any]:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = kwargs.get("data", kwargs)
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return {"tool": "write_json", "path": str(target), "status": "ok"}


def create_ticket(
    title: str = "",
    description: str = "",
    priority: str = "P3",
    log_path: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    ticket_id = f"TKT-{uuid.uuid4().hex[:8]}"
    record = {
        "ticket_id": ticket_id,
        "title": title,
        "description": description,
        "priority": priority,
        **kwargs,
    }
    path = Path(log_path or os.getenv("PPL_TICKET_LOG", ".ppl/tickets.jsonl"))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")
    return {"tool": "create_ticket", "ticket_id": ticket_id, "status": "ok", **record}


BUILTINS: dict[str, Callable[..., Any]] = {
    "echo": echo,
    "write_json": write_json,
    "create_ticket": create_ticket,
}


def _load_callable(spec: str) -> Callable[..., Any]:
    module_name, _, attr = spec.partition(":")
    if not module_name or not attr:
        raise ValueError(f"Invalid tool spec '{spec}'. Use module:function")
    module = importlib.import_module(module_name)
    fn = getattr(module, attr)
    if not callable(fn):
        raise TypeError(f"{spec} is not callable")
    return fn


def load_tool_overrides(path: str | Path | None = None) -> dict[str, Callable[..., Any]]:
    override_path = Path(path or os.getenv("PPL_TOOLS_FILE", "ppl.tools.json"))
    if not override_path.exists():
        return {}
    data = json.loads(override_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("ppl.tools.json must be an object mapping action -> module:function")
    return {name: _load_callable(spec) for name, spec in data.items()}


def build_tool_registry(pir_tools: list[dict[str, Any]] | None = None) -> ToolRegistry:
    registry = ToolRegistry()
    for name, handler in BUILTINS.items():
        registry.register(name, handler)
    for name, handler in load_tool_overrides().items():
        registry.register(name, handler)
    for tool in pir_tools or []:
        for action in tool.get("actions", []):
            if action not in registry.actions:
                # Fall back to create_ticket for ServiceManagement-style demos, else echo.
                if action == "create_ticket":
                    registry.register(action, create_ticket)
                else:
                    registry.register(action, echo)
    return registry


def resolve_action(target: str) -> str:
    return (target or "").split(".")[-1]
