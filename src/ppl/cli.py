import argparse, json
from pathlib import Path
from .parser import parse
from .compiler import Compiler
from .runtime import Runtime

def load(path):
    return Path(path).read_text(encoding="utf-8")

def main():
    parser = argparse.ArgumentParser(prog="ppl")
    sub = parser.add_subparsers(dest="command", required=True)
    for cmd in ("check","compile","run","trace"):
        p = sub.add_parser(cmd)
        p.add_argument("file")
        if cmd in ("run","trace"): p.add_argument("--input", default=None)
    args = parser.parse_args()
    program = parse(load(args.file))
    pir = Compiler().compile(program)

    if args.command == "check":
        print("PPL Compiler 0.1.0")
        print(f"Application: {pir['application']}")
        print("Parsing              ✓")
        print("Types                ✓")
        print("Agents               ✓")
        print("Workflows            ✓")
        print("Program is valid.")
        return

    if args.command == "compile":
        print(json.dumps(pir, indent=2))
        return

    input_data = json.loads(load(args.input)) if args.input else {
        "incident": {
            "description": "Repeated database connection pool failure",
            "application": "Order Management",
            "priority": "P2"
        }
    }
    runtime = Runtime(pir)
    result = runtime.run(input_data)

    if args.command == "trace":
        print(f"Application: {pir['application']}\n")
        print("Execution trace")
        for step, typ, detail in runtime.trace:
            print(f"{step:24} [{typ}] {detail}")
        print("\nResult:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
