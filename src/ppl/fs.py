"""Filesystem helpers with optional root allowlist."""
from __future__ import annotations

import os
from pathlib import Path


def fs_roots() -> list[Path]:
    raw = os.getenv("PPL_FS_ROOT")
    if raw:
        return [Path(part.strip()).resolve() for part in raw.split(os.pathsep) if part.strip()]
    return [Path.cwd().resolve()]


def resolve_path(path: str | Path, *, create_parents: bool = False) -> Path:
    candidate = Path(str(path))
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    resolved = candidate.resolve()
    roots = fs_roots()
    if roots and not any(resolved == root or root in resolved.parents for root in roots):
        raise PermissionError(f"Path not allowed by PPL_FS_ROOT: {resolved}")
    if create_parents:
        resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved
