import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .ai_gateway import AIGateway
from .compiler import Compiler
from .dx import diagnostics_from_exception, format_ppl, init_project
from .parser import parse
from .provider import build_adapter
from .runtime import Runtime
from .test_runner import discover_tests, run_test_module


def load(path):
    return Path(path).read_text(encoding="utf-8")


def build_gateway():
    try:
        return AIGateway(build_adapter())
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(str(exc)) from exc


def default_input(pir):
    names = [item["name"] for item in pir.get("inputs", [])]
    if "incident" in names:
        return {
            "incident": {
                "description": "Repeated database connection pool failure",
                "application": "Order Management",
                "priority": "P2",
            }
        }
    if "request" in names:
        return {"request": {"text": "hello there"}}
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
    graph = pir.get("graph", {}).get("nodes") or []
    if graph:
        print("Execution graph")
        for node in graph:
            deps = ",".join(node["dependencies"]) or "-"
            print(f"  {node['id']:22} {node['operation']:16} deps={deps}")
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


def main():
    parser = argparse.ArgumentParser(prog="ppl")
    sub = parser.add_subparsers(dest="command", required=True)
    for cmd in ("check", "compile", "run", "trace"):
        p = sub.add_parser(cmd)
        p.add_argument("file")
        if cmd in ("run", "trace"):
            p.add_argument("--input", default=None)
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
        print("Program is valid.")
        return

    if args.command == "compile":
        print(json.dumps(pir, indent=2))
        return

    input_data = json.loads(load(args.input)) if args.input else default_input(pir)
    runtime = Runtime(pir, gateway=build_gateway())
    result = runtime.run(input_data)
    if args.command == "trace":
        print_trace(pir, runtime, result)
        return
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
