from pathlib import Path

from ppl.cli import default_input
from ppl.compiler import Compiler
from ppl.parser import parse
from ppl.runtime import Runtime
from ppl.store import InMemoryGraphStore

ROOT = Path(__file__).resolve().parents[1]


def compile_example(name: str):
    text = (ROOT / "examples" / name).read_text(encoding="utf-8")
    return Compiler().compile(parse(text))


def run_example(name: str, input_data=None, **kwargs):
    pir = compile_example(name)
    path = ROOT / "examples" / name
    runtime = Runtime(pir, store=InMemoryGraphStore(), program_path=path, interactive=False)
    return runtime, runtime.run(input_data or default_input(pir), **kwargs)


def test_incident_program():
    runtime, result = run_example("incident.ppl")
    assert result == "AUTOMATE"
    assert any("model=" in detail for _, _, detail in runtime.trace)
    condition = None
    for workflow in compile_example("incident.ppl")["workflows"]:
        for step in workflow["steps"]:
            if step["operation"] == "IF":
                condition = step["condition"]
    assert condition["left"] == "AutomationAdvisor.score"


def test_hello_world_resolves_return():
    runtime, result = run_example("hello_world.ppl")
    assert result in {"GREETING", "QUESTION", "OTHER"}
    assert result != "Classifier.category"
    assert "Classifier" in runtime.context


def test_governed_change_parses_and_runs():
    pir = compile_example("governed_change.ppl")
    assert pir["guards"]
    assert pir["authorizations"]
    assert pir["budgets"]
    assert pir["graph"]["nodes"]
    _, result = run_example("governed_change.ppl")
    assert result == "APPROVED"


def test_true_false_condition_literals():
    source = """
APP BoolCheck
INPUT item
    ready: BOOLEAN
AGENT Echo
    INPUT item
    REASON
        determine whether the proposed change is safe
        OUTPUT:
            safe: BOOLEAN
            confidence: CONFIDENCE
    OUTPUT
        safe: BOOLEAN
        confidence: CONFIDENCE
WORKFLOW Main
    RECEIVE item
    RUN Echo
    IF Echo.safe == TRUE
        RETURN "YES"
    ELSE
        RETURN "NO"
"""
    pir = Compiler().compile(parse(source))
    result = Runtime(pir, store=InMemoryGraphStore(), interactive=False).run({"item": {"ready": True}})
    assert result == "YES"


def test_confidence_validation():
    from ppl.schema import SchemaError, validate_output
    validate_output({"confidence": "CONFIDENCE"}, {"confidence": 0.91})
    try:
        validate_output({"confidence": "CONFIDENCE"}, {"confidence": 1.5})
        assert False, "expected SchemaError"
    except SchemaError:
        pass


def test_parallel_join_wait_checkpoint():
    source = """
APP ParallelDemo
INPUT request
    text: TEXT
    done: BOOLEAN
AGENT Left
    INPUT request
    CLASSIFY request.text AS
        GREETING
        OTHER
    OUTPUT
        category
AGENT Right
    INPUT request
    CLASSIFY request.text AS
        QUESTION
        OTHER
    OUTPUT
        category
WORKFLOW Main
    RECEIVE request
    PARALLEL
        RUN Left
        RUN Right
    JOIN Left
    CHECKPOINT after_join
    WAIT request.done
    RETURN Left.category
"""
    pir = Compiler().compile(parse(source))
    runtime = Runtime(pir, store=InMemoryGraphStore(), interactive=False)
    result = runtime.run({"request": {"text": "hello there", "done": True}})
    assert result in {"GREETING", "OTHER"}
    ops = [step for step, _, _ in runtime.trace]
    assert "JOIN" in ops
    assert any(step.startswith("CHECKPOINT") for step in ops)
    assert any(step.startswith("WAIT") for step in ops)


def test_cli_check(capsys, monkeypatch):
    monkeypatch.setattr("sys.argv", ["ppl", "check", str(ROOT / "examples" / "hello_world.ppl")])
    from ppl.cli import main
    main()
    out = capsys.readouterr().out
    assert "PPL Compiler 0.9.0" in out
    assert "Program is valid." in out
