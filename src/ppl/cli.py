import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .ai_gateway import AIGateway
from .compiler import Compiler
from .dx import diagnostics_from_exception, format_ppl, init_project
from .execution_graph import ExecutionStatus
from .parser import parse
from .provider import build_adapter, public_config, test_provider, SUPPORTED, apply_program_environment
from .runtime import Runtime, approve_execution
from .store import FileExecutionStore, default_state_dir
from .test_runner import discover_tests, run_test_module


def load(path):
    return Path(path).read_text(encoding="utf-8")


def build_gateway(pir: dict | None = None):
    try:
        if pir is not None:
            apply_program_environment(pir.get("environments"))
        return AIGateway(build_adapter())
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(str(exc)) from exc


def cmd_provider(args):
    if args.provider_command == "list":
        print("Supported providers:")
        for name in SUPPORTED:
            print(f"  - {name}")
        return
    if args.provider_command == "show":
        print(json.dumps(public_config(), indent=2))
        return
    if args.provider_command == "test":
        try:
            result = test_provider()
            print(json.dumps(result, indent=2))
        except Exception as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
            raise SystemExit(1) from exc
        return


def default_input(pir):
    names = [item["name"] for item in pir.get("inputs", [])]
    if "incident" in names:
        return {
            "incident": {
                "description": "Repeated database connection pool failure",
                "application": "Order Management",
                "priority": "P2",
                "id": "INC-1001",
            }
        }
    if "request" in names:
        return {"request": {"text": "hello there", "done": True}}
    if "change" in names:
        return {
            "change": {
                "description": "Increase database connection pool in production",
                "environment": "production",
                "risk": 3,
            }
        }
    if not names:
        return {}
    first = pir["inputs"][0]
    payload = {}
    for field in first.get("fields", []):
        type_name = str(field.get("type", "TEXT")).upper()
        payload[field["name"]] = 1 if type_name in {"NUMBER", "INTEGER"} else "sample"
    return {first["name"]: payload}


def compile_file(path):
    return Compiler().compile(parse(load(path)))


def print_trace(pir, runtime, result):
    print(f"Application: {pir['application']}\n")
    execution = runtime.execution
    if execution is not None:
        print(f"Execution: {execution.execution_id}")
        print(f"Status: {execution.status.value}")
        if execution.wait:
            print(f"Wait: {json.dumps(execution.wait)}")
        print()
    graph = pir.get("graph", {}).get("nodes") or []
    if graph:
        print("Execution graph")
        node_state = execution.nodes if execution else {}
        for node in graph:
            deps = ",".join(node["dependencies"]) or "-"
            live = node_state.get(node["id"])
            status = live.status.value if live else "-"
            worker = (live.metadata.get("worker") if live else None) or "-"
            print(f"  {node['id']:22} {node['operation']:16} status={status:10} worker={worker} deps={deps}")
        print()
    print("Execution trace")
    for step, typ, detail in runtime.trace:
        print(f"{step:24} [{typ}] {detail}")
    print("\nResult:")
    print(json.dumps(result, indent=2))


def cmd_init(args):
    root = init_project(args.target, force=args.force)
    print(f"Created PPL project at {root}")


def cmd_fmt(args):
    path = Path(args.file)
    formatted = format_ppl(path.read_text(encoding="utf-8"))
    if args.write:
        path.write_text(formatted, encoding="utf-8")
        print(f"Formatted {path}")
        return
    sys.stdout.write(formatted)


def cmd_test(args):
    try:
        import pytest
    except ImportError:
        pytest = None
    if pytest is not None:
        raise SystemExit(pytest.main([args.path, "-q"]))
    failures = []
    for path in discover_tests(args.path):
        failures.extend((path.name, name, exc) for name, exc in run_test_module(path))
    if failures:
        for module, name, exc in failures:
            print(f"FAIL {module}::{name}: {exc}")
        raise SystemExit(1)
    print("All discovered tests passed.")


def cmd_repl(_args):
    print(f"PPL {__version__} REPL. Commands: :help :run :clear :quit")
    buffer = []
    while True:
        try:
            line = input("ppl> ")
        except EOFError:
            print()
            return
        stripped = line.strip()
        if stripped in {":quit", ":exit"}:
            return
        if stripped == ":help":
            print("Enter PPL source. Blank line keeps buffering. :run compiles the buffer.")
            continue
        if stripped == ":clear":
            buffer = []
            continue
        if stripped == ":run":
            source = "\n".join(buffer)
            try:
                pir = Compiler().compile(parse(source))
                print(json.dumps({"application": pir["application"], "agents": [a["name"] for a in pir["agents"]]}, indent=2))
            except Exception as exc:
                print(diagnostics_from_exception(exc))
            continue
        buffer.append(line)


def _store_from_args(args):
    root = getattr(args, "store", None) or default_state_dir()
    return FileExecutionStore(root)


def cmd_run_program(args, pir, *, trace: bool = False):
    input_data = json.loads(load(args.input)) if getattr(args, "input", None) else default_input(pir)
    store = _store_from_args(args)
    workers = int(getattr(args, "workers", 0) or 0)
    execution_id = getattr(args, "execution_id", None)
    stdio = bool(getattr(args, "stdio", False))

    if workers > 0:
        from .workers import run_with_workers
        result = run_with_workers(
            args.file,
            pir,
            input_data,
            workers=workers,
            store=store,
            execution_id=execution_id,
        )
        runtime = Runtime(pir, gateway=build_gateway(pir), store=store, program_path=args.file)
        if isinstance(result, dict) and result.get("status") == "WAITING":
            runtime.execution = store.load(result["execution_id"])
        elif execution_id and store.exists(execution_id):
            runtime.execution = store.load(execution_id)
        elif store.list_ids():
            # best-effort: last written id from result
            eid = result.get("execution_id") if isinstance(result, dict) else None
            if eid and store.exists(eid):
                runtime.execution = store.load(eid)
        if trace:
            print_trace(pir, runtime, result)
        elif stdio and runtime.prints:
            for line in runtime.prints:
                print(line)
        else:
            print(json.dumps(result, indent=2))
        if isinstance(result, dict) and result.get("status") == "WAITING":
            raise SystemExit(2)
        return

    runtime = Runtime(pir, gateway=build_gateway(pir), store=store, program_path=args.file)
    result = runtime.run(input_data, execution_id=execution_id)
    if trace:
        print_trace(pir, runtime, result)
    elif stdio and runtime.prints:
        for line in runtime.prints:
            print(line)
        if runtime.return_value is not None and not runtime.prints:
            print(runtime.return_value)
    else:
        print(json.dumps(result, indent=2))
    if isinstance(result, dict) and result.get("status") == "WAITING":
        raise SystemExit(2)


def cmd_resume(args):
    store = _store_from_args(args)
    execution = store.load(args.execution_id)
    program_path = args.file or execution.program_path
    if not program_path:
        raise SystemExit("Execution has no program_path; pass the .ppl file as --file")
    pir = compile_file(program_path)
    runtime = Runtime(pir, gateway=build_gateway(pir), store=store, program_path=program_path)
    result = runtime.run(execution_id=args.execution_id, resume=True)
    print(json.dumps(result, indent=2))
    if isinstance(result, dict) and result.get("status") == "WAITING":
        raise SystemExit(2)


def cmd_approve(args):
    store = _store_from_args(args)
    approve_execution(store, args.execution_id, args.decision)
    if args.resume:
        class NS:
            pass
        ns = NS()
        ns.execution_id = args.execution_id
        ns.file = args.file
        ns.store = args.store
        cmd_resume(ns)
    else:
        print(json.dumps({"execution_id": args.execution_id, "decision": args.decision, "status": "approved"}, indent=2))


def cmd_worker(args):
    from .workers import _worker_loop
    import threading

    stop = threading.Event()
    program = args.file
    if not program:
        raise SystemExit("ppl worker requires --file pointing at the .ppl program")
    print(f"Worker listening on {args.store or default_state_dir()} for {program}")
    try:
        _worker_loop(str(args.store or default_state_dir()), program, args.name or "worker-cli", stop)
    except KeyboardInterrupt:
        stop.set()
        print("Worker stopped.")


def main():
    parser = argparse.ArgumentParser(prog="ppl")
    sub = parser.add_subparsers(dest="command", required=True)

    for cmd in ("check", "compile"):
        p = sub.add_parser(cmd)
        p.add_argument("file")
        if cmd == "check":
            p.add_argument("--strict", action="store_true", help="Warn when cognitive nodes use local provider")

    for cmd in ("run", "trace"):
        p = sub.add_parser(cmd)
        p.add_argument("file")
        p.add_argument("--input", default=None)
        p.add_argument("--execution-id", default=None)
        p.add_argument("--workers", type=int, default=0)
        p.add_argument("--store", default=None)
        p.add_argument("--stdio", action="store_true", help="Print PRINT output instead of JSON")

    provider = sub.add_parser("provider")
    provider_sub = provider.add_subparsers(dest="provider_command", required=True)
    provider_sub.add_parser("show")
    provider_sub.add_parser("test")
    provider_sub.add_parser("list")

    resume = sub.add_parser("resume")
    resume.add_argument("execution_id")
    resume.add_argument("--file", default=None)
    resume.add_argument("--store", default=None)

    approve = sub.add_parser("approve")
    approve.add_argument("execution_id")
    approve.add_argument("decision")
    approve.add_argument("--file", default=None)
    approve.add_argument("--store", default=None)
    approve.add_argument("--resume", action="store_true")

    worker = sub.add_parser("worker")
    worker.add_argument("--file", required=True)
    worker.add_argument("--store", default=None)
    worker.add_argument("--name", default=None)

    init = sub.add_parser("init")
    init.add_argument("target")
    init.add_argument("--force", action="store_true")
    fmt = sub.add_parser("fmt")
    fmt.add_argument("file")
    fmt.add_argument("-w", "--write", action="store_true")
    test = sub.add_parser("test")
    test.add_argument("path", nargs="?", default="tests")
    sub.add_parser("repl")
    args = parser.parse_args()

    if args.command == "init":
        cmd_init(args)
        return
    if args.command == "fmt":
        cmd_fmt(args)
        return
    if args.command == "test":
        cmd_test(args)
        return
    if args.command == "repl":
        cmd_repl(args)
        return
    if args.command == "resume":
        try:
            cmd_resume(args)
        except Exception as exc:
            print(diagnostics_from_exception(exc))
            raise SystemExit(1) from exc
        return
    if args.command == "approve":
        try:
            cmd_approve(args)
        except Exception as exc:
            print(diagnostics_from_exception(exc))
            raise SystemExit(1) from exc
        return
    if args.command == "worker":
        cmd_worker(args)
        return
    if args.command == "provider":
        cmd_provider(args)
        return

    try:
        pir = compile_file(args.file)
    except Exception as exc:
        print(diagnostics_from_exception(exc))
        raise SystemExit(1) from exc

    if args.command == "check":
        print(f"PPL Compiler {__version__}")
        print(f"Application: {pir['application']}")
        print("Parsing              OK")
        print("Types                OK")
        print("Agents               OK")
        print("Workflows            OK")
        print("Graph                OK")
        if getattr(args, "strict", False):
            cfg = public_config()
            has_cognitive = any(a.get("operations") for a in pir.get("agents", []))
            if has_cognitive and cfg.get("provider") in {"local", "mock", ""}:
                print("Warning              Cognitive nodes with local provider")
        print("Program is valid.")
        return

    if args.command == "compile":
        print(json.dumps(pir, indent=2))
        return

    if args.command in {"run", "trace"}:
        try:
            cmd_run_program(args, pir, trace=args.command == "trace")
        except SystemExit:
            raise
        except Exception as exc:
            print(diagnostics_from_exception(exc))
            raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
