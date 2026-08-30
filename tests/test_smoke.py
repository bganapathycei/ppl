from pathlib import Path
from ppl.parser import parse
from ppl.compiler import Compiler
from ppl.runtime import Runtime
from ppl.schema import SchemaError

def make_runtime():
    text=Path('examples/incident.ppl').read_text()
    return Runtime(Compiler().compile(parse(text)))

def test_incident_program():
    runtime=make_runtime()
    result=runtime.run({'incident':{'description':'Repeated database connection pool failure','application':'Order Management','priority':'P2'}})
    assert result=='AUTOMATE'
    assert any('model=' in detail for _,_,detail in runtime.trace)

def test_confidence_validation():
    from ppl.schema import validate_output
    validate_output({'confidence':'CONFIDENCE'},{'confidence':0.91})
    try:
        validate_output({'confidence':'CONFIDENCE'},{'confidence':1.5})
        assert False, 'expected SchemaError'
    except SchemaError:
        pass
