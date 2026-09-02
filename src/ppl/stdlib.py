"""PPL standard library tool bundles."""
from __future__ import annotations

from . import tools

STDLIB_MODULES = {
    "stdlib.files": [
        "read_text",
        "write_text",
        "append_text",
        "read_json",
        "list_dir",
    ],
    "stdlib.http": [
        "http_get",
        "http_post",
    ],
    "stdlib.env": [
        "env_get",
    ],
    "stdlib.time": [
        "now",
        "format_date",
    ],
    "stdlib.shell": [
        "run_command",
    ],
}


def register_imports(registry, modules: list[str]) -> None:
    for module in modules:
        actions = STDLIB_MODULES.get(module)
        if not actions:
            raise ValueError(f"Unknown IMPORT module: {module}")
        for action in actions:
            handler = getattr(tools, action, None)
            if handler is None:
                raise ValueError(f"Missing stdlib handler: {action}")
            registry.register(action, handler)
