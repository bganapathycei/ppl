"""Builtin and pluggable tool handlers for PPL CALL statements."""
from __future__ import annotations

import importlib
import json
import os
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib import request as urllib_request

from .fs import resolve_path
from .v03_runtime import ToolRegistry


def echo(**kwargs: Any) -> dict[str, Any]:
    return {"tool": "echo", "args": kwargs, "status": "ok"}


def write_json(path: str = ".ppl/out.json", data: Any = None, **kwargs: Any) -> dict[str, Any]:
    target = resolve_path(path, create_parents=True)
    payload = data if data is not None else kwargs.get("data", kwargs)
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return {"tool": "write_json", "path": str(target), "status": "ok"}


def read_json(path: str = ".ppl/out.json", **kwargs: Any) -> dict[str, Any]:
    target = resolve_path(path)
    payload = json.loads(target.read_text(encoding="utf-8"))
    return {"tool": "read_json", "path": str(target), "data": payload, "status": "ok"}


def read_text(path: str = "", **kwargs: Any) -> dict[str, Any]:
    target = resolve_path(path or kwargs.get("file", ""))
    text = target.read_text(encoding="utf-8")
    return {"tool": "read_text", "path": str(target), "text": text, "status": "ok"}


def write_text(path: str = "", content: str = "", **kwargs: Any) -> dict[str, Any]:
    target = resolve_path(path or kwargs.get("file", ""), create_parents=True)
    body = content if content != "" else str(kwargs.get("text", kwargs.get("data", "")))
    target.write_text(body, encoding="utf-8")
    return {"tool": "write_text", "path": str(target), "status": "ok"}


def append_text(path: str = "", content: str = "", **kwargs: Any) -> dict[str, Any]:
    target = resolve_path(path or kwargs.get("file", ""), create_parents=True)
    body = content if content != "" else str(kwargs.get("text", kwargs.get("data", "")))
    with target.open("a", encoding="utf-8") as handle:
        handle.write(body)
    return {"tool": "append_text", "path": str(target), "status": "ok"}


def list_dir(path: str = ".", **kwargs: Any) -> dict[str, Any]:
    target = resolve_path(path or kwargs.get("dir", "."))
    entries = sorted(p.name for p in target.iterdir())
    return {"tool": "list_dir", "path": str(target), "entries": entries, "status": "ok"}


def env_get(name: str = "", **kwargs: Any) -> dict[str, Any]:
    key = name or kwargs.get("key", "")
    value = os.getenv(key)
    return {"tool": "env_get", "name": key, "value": value, "status": "ok"}


def http_get(url: str = "", **kwargs: Any) -> dict[str, Any]:
    target = url or kwargs.get("url", "")
    with urllib_request.urlopen(target, timeout=30) as resp:
        body = resp.read().decode("utf-8", errors="replace")
    return {"tool": "http_get", "url": target, "body": body, "status": "ok"}


def http_post(url: str = "", body: str = "", **kwargs: Any) -> dict[str, Any]:
    target = url or kwargs.get("url", "")
    payload = body.encode("utf-8") if body else json.dumps(kwargs.get("json", {})).encode("utf-8")
    req = urllib_request.Request(target, data=payload, method="POST")
    req.add_header("Content-Type", kwargs.get("content_type", "application/json"))
    with urllib_request.urlopen(req, timeout=30) as resp:
        text = resp.read().decode("utf-8", errors="replace")
    return {"tool": "http_post", "url": target, "body": text, "status": "ok"}


def now(**kwargs: Any) -> dict[str, Any]:
    stamp = datetime.now(timezone.utc).isoformat()
    return {"tool": "now", "timestamp": stamp, "status": "ok"}


def format_date(timestamp: str = "", fmt: str = "%Y-%m-%d %H:%M:%S UTC", **kwargs: Any) -> dict[str, Any]:
    raw = timestamp or kwargs.get("value", "")
    dt = datetime.fromisoformat(raw.replace("Z", "+00:00")) if raw else datetime.now(timezone.utc)
    return {"tool": "format_date", "formatted": dt.strftime(fmt), "status": "ok"}


def run_command(command: str = "", **kwargs: Any) -> dict[str, Any]:
    if os.getenv("PPL_ALLOW_SHELL", "").lower() not in {"1", "true", "yes"}:
        raise PermissionError("run_command requires PPL_ALLOW_SHELL=1")
    cmd = command or kwargs.get("cmd", "")
    completed = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False)
    return {
        "tool": "run_command",
        "command": cmd,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "exit_code": completed.returncode,
        "status": "ok" if completed.returncode == 0 else "error",
    }


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
    "read_json": read_json,
    "read_text": read_text,
    "write_text": write_text,
    "append_text": append_text,
    "list_dir": list_dir,
    "env_get": env_get,
    "http_get": http_get,
    "http_post": http_post,
    "now": now,
    "format_date": format_date,
    "run_command": run_command,
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


def build_tool_registry(
    pir_tools: list[dict[str, Any]] | None = None,
    imports: list[str] | None = None,
) -> ToolRegistry:
    from .stdlib import register_imports

    registry = ToolRegistry()
    for name, handler in BUILTINS.items():
        registry.register(name, handler)
    for name, handler in load_tool_overrides().items():
        registry.register(name, handler)
    register_imports(registry, imports or [])
    for tool in pir_tools or []:
        for action in tool.get("actions", []):
            if action not in registry.actions:
                if action == "create_ticket":
                    registry.register(action, create_ticket)
                else:
                    registry.register(action, echo)
    return registry


def resolve_action(target: str) -> str:
    return (target or "").split(".")[-1]
