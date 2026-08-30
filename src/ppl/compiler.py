from .ast import *

class Compiler:
    def compile(self, program):
        if not program.app: raise ValueError("Program must define APP")
        return {
            "version": "0.1",
            "application": program.app.name,
            "inputs": [{"name": x.name, "fields": [{"name": f.name, "type": f.type_name} for f in x.fields]} for x in program.inputs],
            "agents": [self.compile_agent(a) for a in program.agents],
            "workflows": [self.compile_workflow(w) for w in program.workflows],
        }

    def compile_agent(self, a):
        ops = []
        for op in a.operations:
            if isinstance(op, ClassifyOp):
                ops.append({"operation":"CLASSIFY","execution_type":"C","target":op.target,"categories":op.categories})
            elif isinstance(op, ExtractOp):
                ops.append({"operation":"EXTRACT","execution_type":"C","fields":op.fields})
            elif isinstance(op, ReasonOp):
                ops.append({"operation":"REASON","execution_type":"C","instruction":op.instruction,"consider":op.consider})
        return {"name":a.name,"input":a.input_name,"operations":ops,"outputs":a.outputs}

    def compile_workflow(self, w):
        return {"name":w.name,"steps":[self.compile_step(s) for s in w.steps]}

    def compile_step(self, s):
        if isinstance(s, ReceiveStep): return {"operation":"RECEIVE","execution_type":"D","name":s.name}
        if isinstance(s, RunStep): return {"operation":"RUN","execution_type":"D","name":s.name}
        if isinstance(s, ReturnStep): return {"operation":"RETURN","execution_type":"D","value":s.value}
        if isinstance(s, IfStep):
            return {
                "operation":"IF","execution_type":"D","condition":vars(s.condition),
                "then":[self.compile_step(x) for x in s.then_steps],
                "else_if":[{"condition":vars(c),"steps":[self.compile_step(x) for x in st]} for c,st in s.else_if],
                "else":[self.compile_step(x) for x in s.else_steps]
            }
        raise TypeError(type(s).__name__)
