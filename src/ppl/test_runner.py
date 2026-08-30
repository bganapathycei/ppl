from pathlib import Path
from .parser import parse
from .compiler import Compiler

def discover_tests(root: str='tests'):
    return sorted(Path(root).glob('test_*.py'))

def run_test_module(path):
    namespace={'__name__':'__ppl_test__'}
    exec(path.read_text(encoding='utf-8'), namespace)
    failures=[]
    for name, value in namespace.items():
        if name.startswith('test_') and callable(value):
            try: value()
            except Exception as exc: failures.append((name, exc))
    return failures

def validate_file(path: str):
    program=parse(Path(path).read_text(encoding='utf-8'))
    return Compiler().compile(program)
