"""File-backed knowledge and persistent JSON memory for PPL 0.9."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .v03_runtime import KnowledgeSource, MemoryStore, build_context


def knowledge_roots(program_dir: Path | None = None) -> list[Path]:
    roots: list[Path] = []
    env = os.getenv("PPL_KNOWLEDGE_DIR")
    if env:
        roots.append(Path(env))
    if program_dir is not None:
        roots.append(program_dir / "knowledge")
        roots.append(program_dir)
    roots.append(Path.cwd() / "knowledge")
    roots.append(Path.cwd() / "examples" / "knowledge")
    return roots


def _read_source_file(source: str, roots: list[Path]) -> str | None:
    names = [
        source,
        f"{source}.md",
        f"{source}.txt",
        f"{source}.json",
    ]
    for root in roots:
        for name in names:
            path = root / name
            if path.is_file():
                return path.read_text(encoding="utf-8")
    return None


def load_knowledge_sources(
    declarations: list[dict[str, Any]],
    program_dir: Path | None = None,
) -> list[KnowledgeSource]:
    roots = knowledge_roots(program_dir)
    loaded: list[KnowledgeSource] = []
    for item in declarations:
        documents: dict[str, str] = {}
        for source in item.get("sources", []):
            text = _read_source_file(source, roots)
            documents[source] = text if text is not None else f"(missing knowledge source: {source})"
        loaded.append(KnowledgeSource(item["name"], documents))
    return loaded


def memory_path(app_name: str, program_dir: Path | None = None) -> Path:
    if os.getenv("PPL_MEMORY_DIR"):
        return Path(os.getenv("PPL_MEMORY_DIR", ".ppl/memory")) / f"{app_name}.json"
    return (Path.cwd() / ".ppl" / "memory") / f"{app_name}.json"


class FileMemoryStore(MemoryStore):
    def __init__(self, name: str, path: Path):
        super().__init__(name=name)
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    self.records = data
            except json.JSONDecodeError:
                self.records = {}

    def write(self, key: str, value: Any) -> None:
        super().write(key, value)
        self.flush()

    def flush(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.records, indent=2), encoding="utf-8")


def load_memory(declarations: list[dict[str, Any]], app_name: str) -> FileMemoryStore | MemoryStore:
    if not declarations:
        return MemoryStore("default")
    decl = declarations[0]
    path = memory_path(app_name)
    store = FileMemoryStore(decl.get("name") or "default", path)
    store.key = decl.get("key")  # type: ignore[attr-defined]
    return store


def resolve_memory_key(key_expr: str | None, context: dict[str, Any]) -> str | None:
    if not key_expr:
        return None
    cur: Any = context
    for part in key_expr.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return key_expr
    return str(cur)


def knowledge_for_agent(
    sources: list[KnowledgeSource],
    names: list[str],
    query: str,
) -> list[dict[str, Any]]:
    selected = [s for s in sources if s.name in names] if names else sources
    return build_context(selected, None, query).get("knowledge", [])
