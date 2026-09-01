#!/usr/bin/env python3
"""Serve the PPL visual editor, compile programs, and run them via the real runtime."""

from __future__ import annotations

import argparse
import json
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

EDITOR_DIR = Path(__file__).resolve().parent
ROOT = EDITOR_DIR.parent
sys.path.insert(0, str(ROOT / "src"))

from ppl.ai_gateway import AIGateway  # noqa: E402
from ppl.cli import default_input  # noqa: E402
from ppl.compiler import Compiler  # noqa: E402
from ppl.parser import parse  # noqa: E402
from ppl.provider import build_adapter  # noqa: E402
from ppl.runtime import Runtime  # noqa: E402
from ppl.store import FileExecutionStore, default_state_dir  # noqa: E402

from assistant import assistant_chat, assistant_config  # noqa: E402

RUN_CACHE = EDITOR_DIR / ".run-cache"


def compile_source(source: str) -> dict:
    try:
        pir = Compiler().compile(parse(source))
        return {
            "ok": True,
            "application": pir.get("application"),
            "graph": pir.get("graph") or {"nodes": [], "version": "0.9"},
            "inputs": pir.get("inputs") or [],
            "default_input": default_input(pir),
            "error": None,
        }
    except Exception as exc:
        return {
            "ok": False,
            "application": None,
            "graph": {"nodes": [], "version": "0.9"},
            "inputs": [],
            "default_input": None,
            "error": f"{exc.__class__.__name__}: {exc}",
        }


def _trace_payload(runtime: Runtime) -> list[dict]:
    return [{"step": step, "type": typ, "detail": detail} for step, typ, detail in runtime.trace]


def _node_status_payload(runtime: Runtime) -> list[dict]:
    if runtime.execution is None:
        return []
    return [
        {
            "id": node.node_id,
            "operation": node.operation,
            "status": node.status.value,
        }
        for node in runtime.execution.nodes.values()
    ]


def run_source(
    source: str,
    input_data: dict | None = None,
    *,
    trace: bool = True,
    execution_id: str | None = None,
    human_decision: str | None = None,
) -> dict:
    try:
        pir = Compiler().compile(parse(source))
    except Exception as exc:
        return {"ok": False, "error": f"{exc.__class__.__name__}: {exc}"}

    payload = dict(input_data or default_input(pir))
    if human_decision:
        payload["human_decision"] = human_decision

    RUN_CACHE.mkdir(parents=True, exist_ok=True)
    program_path = RUN_CACHE / "program.ppl"
    program_path.write_text(source, encoding="utf-8")

    try:
        gateway = AIGateway(build_adapter())
    except (ValueError, RuntimeError) as exc:
        return {"ok": False, "error": str(exc)}

    store = FileExecutionStore(default_state_dir())
    if execution_id and store.exists(execution_id):
        pending = store.load(execution_id)
        pending.context.update(payload)
        store.save(pending)

    runtime = Runtime(
        pir,
        gateway=gateway,
        store=store,
        program_path=program_path,
        interactive=False,
    )
    try:
        result = runtime.run(payload, execution_id=execution_id)
    except Exception as exc:
        return {"ok": False, "error": f"{exc.__class__.__name__}: {exc}"}

    waiting = isinstance(result, dict) and result.get("status") == "WAITING"
    response = {
        "ok": True,
        "application": pir.get("application"),
        "result": result,
        "waiting": waiting,
        "execution_id": runtime.execution.execution_id if runtime.execution else None,
        "execution_status": runtime.execution.status.value if runtime.execution else None,
        "wait": runtime.execution.wait if runtime.execution else None,
        "error": None,
    }
    if trace:
        response["trace"] = _trace_payload(runtime)
        response["node_status"] = _node_status_payload(runtime)
    return response


class EditorHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(EDITOR_DIR), **kwargs)

    def log_message(self, format, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), format % args))

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/assistant/config":
            self._send_json(200, assistant_config())
            return
        super().do_GET()

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        if path not in {"/api/compile", "/api/run", "/api/assistant/chat"}:
            self.send_error(404, "Not found")
            return
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError as exc:
            self._send_json(400, {"ok": False, "error": f"Invalid JSON: {exc}"})
            return
        if not isinstance(payload, dict):
            self._send_json(400, {"ok": False, "error": "Request body must be a JSON object"})
            return

        if path == "/api/compile":
            source = payload.get("source")
            if not isinstance(source, str):
                source = ""
            self._send_json(200, compile_source(source))
            return

        if path == "/api/assistant/chat":
            messages = payload.get("messages")
            if not isinstance(messages, list):
                self._send_json(400, {"ok": False, "error": "messages must be an array"})
                return
            provider = payload.get("provider") or ""
            model = payload.get("model") or ""
            current_source = payload.get("current_source")
            if current_source is not None and not isinstance(current_source, str):
                self._send_json(400, {"ok": False, "error": "current_source must be a string"})
                return
            body = assistant_chat(
                messages,
                provider=str(provider),
                model=str(model),
                current_source=current_source or "",
            )
            self._send_json(200 if body.get("ok") else 400, body)
            return

        source = payload.get("source")
        if not isinstance(source, str) or not source.strip():
            self._send_json(400, {"ok": False, "error": "Missing source"})
            return

        input_data = payload.get("input")
        if input_data is not None and not isinstance(input_data, dict):
            self._send_json(400, {"ok": False, "error": "input must be a JSON object"})
            return

        human_decision = payload.get("human_decision")
        if human_decision is not None and not isinstance(human_decision, str):
            self._send_json(400, {"ok": False, "error": "human_decision must be a string"})
            return

        execution_id = payload.get("execution_id")
        if execution_id is not None and not isinstance(execution_id, str):
            self._send_json(400, {"ok": False, "error": "execution_id must be a string"})
            return

        trace = bool(payload.get("trace", True))
        body = run_source(
            source,
            input_data,
            trace=trace,
            execution_id=execution_id,
            human_decision=human_decision,
        )
        self._send_json(200 if body.get("ok") else 400, body)

    def _send_json(self, status: int, body: dict):
        data = json.dumps(body, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Serve the PPL visual editor")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    server = ThreadingHTTPServer((args.host, args.port), EditorHandler)
    print(f"PPL editor at http://{args.host}:{args.port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped", flush=True)
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
