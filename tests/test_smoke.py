from pathlib import Path
from ppl.parser import parse
from ppl.compiler import Compiler
from ppl.runtime import Runtime

def test_incident_program():
    text = Path("examples/incident.ppl").read_text()
    pir = Compiler().compile(parse(text))
    result = Runtime(pir).run({
        "incident": {
            "description": "Repeated database connection pool failure",
            "application": "Order Management",
            "priority": "P2"
        }
    })
    assert result == "AUTOMATE"
