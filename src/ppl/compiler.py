from .ast import *
from .execution_graph import ExecutionGraph, GraphNode


def _schema_from_outputs(outputs):
    schema = {}
    for item in outputs:
        if ":" in item:
            name, type_name = map(str.strip, item.split(":", 1))
            schema[name] = type_name
    return schema


class Compiler:
    def compile(self, program):
        if not program.app:
            raise ValueError("Program must define APP")
        policies = {
            p.name: {
                "name": p.name,
                "reasoning_model": p.reason_model,
                "classification_model": p.classify_model,
                "extraction_model": p.extract_model,
                "max_retries": p.max_retries,
                "fallback_model": p.fallback_model,
            }
            for p in program.model_policies
        }
        workflows = [self.compile_workflow(w) for w in program.workflows]
        graph = self.compile_graph(workflows)
        if graph["nodes"]:
            ExecutionGraph([
                GraphNode(
                    node["id"],
                    node["operation"],
                    node["dependencies"],
                    metadata=dict(node.get("metadata") or {}),
                )
                for node in graph["nodes"]
            ])
        return {
            "version": "0.9",
            "application": program.app.name,
            "inputs": [
                {"name": x.name, "fields": [{"name": f.name, "type": f.type_name} for f in x.fields]}
                for x in program.inputs
            ],
            "model_policies": policies,
            "guards": [{"name": g.name, "rules": g.rules} for g in program.guards],
            "authorizations": [{"name": a.name, "requires": a.requires} for a in program.authorizations],
            "budgets": [
                {"max_cost": b.max_cost, "max_latency": b.max_latency, "max_steps": b.max_steps}
                for b in program.budgets
            ],
            "environments": [{"name": e.name, "body": e.body} for e in program.environments],
            "knowledge": [{"name": k.name, "sources": k.sources} for k in program.knowledge],
            "memory": [{"name": m.name, "key": m.key, "body": m.body} for m in program.memories],
            "tools": [{"name": t.name, "actions": t.actions, "body": t.body} for t in program.tools],
            "agents": [self.compile_agent(a) for a in program.agents],
            "workflows": workflows,
            "graph": graph,
        }

    def compile_agent(self, a):
        output_schema = _schema_from_outputs(a.outputs)
        ops = []
        for op in a.operations:
            if isinstance(op, ClassifyOp):
                ops.append({
                    "operation": "CLASSIFY",
                    "execution_type": "C",
                    "target": op.target,
                    "categories": op.categories,
                    "schema": {"category": "CLASSIFICATION", "confidence": "CONFIDENCE"},
                })
            elif isinstance(op, ExtractOp):
                ops.append({
                    "operation": "EXTRACT",
                    "execution_type": "C",
                    "fields": op.fields,
                    "schema": op.schema or {f: "TEXT" for f in op.fields},
                })
            elif isinstance(op, ReasonOp):
                schema = op.schema or {k: v for k, v in output_schema.items() if k not in {"category"}}
                ops.append({
                    "operation": "REASON",
                    "execution_type": "C",
                    "instruction": op.instruction,
                    "consider": op.consider,
                    "schema": schema or {"confidence": "CONFIDENCE"},
                })
        return {
            "name": a.name,
            "input": a.input_name,
            "policy": a.policy,
            "knowledge": a.knowledge,
            "memory": a.memory,
            "operations": ops,
            "outputs": a.outputs,
        }

    def compile_workflow(self, w):
        return {"name": w.name, "steps": [self.compile_step(s) for s in w.steps]}

    def compile_step(self, s):
        if isinstance(s, ReceiveStep):
            return {"operation": "RECEIVE", "execution_type": "D", "name": s.name}
        if isinstance(s, RunStep):
            return {"operation": "RUN", "execution_type": "D", "name": s.name}
        if isinstance(s, ReturnStep):
            return {"operation": "RETURN", "execution_type": "D", "value": s.value, "literal": s.literal}
        if isinstance(s, IfStep):
            return {
                "operation": "IF",
                "execution_type": "D",
                "condition": vars(s.condition),
                "then": [self.compile_step(x) for x in s.then_steps],
                "else_if": [
                    {"condition": vars(c), "steps": [self.compile_step(x) for x in st]}
                    for c, st in s.else_if
                ],
                "else": [self.compile_step(x) for x in s.else_steps],
            }
        if isinstance(s, HumanApprovalStep):
            return {
                "operation": "HUMAN_APPROVAL",
                "execution_type": "H",
                "question": s.question,
                "options": s.options,
            }
        if isinstance(s, ParallelStep):
            return {
                "operation": "PARALLEL",
                "execution_type": "D",
                "steps": [self.compile_step(x) for x in s.steps],
            }
        if isinstance(s, JoinStep):
            return {"operation": "JOIN", "execution_type": "D", "names": s.names}
        if isinstance(s, WaitStep):
            return {"operation": "WAIT", "execution_type": "D", "condition": s.condition}
        if isinstance(s, CheckpointStep):
            return {"operation": "CHECKPOINT", "execution_type": "D", "name": s.name}
        if isinstance(s, CallStep):
            return {"operation": "CALL", "execution_type": "D", "target": s.target, "args": s.args}
        raise TypeError(type(s).__name__)

    def compile_graph(self, workflows):
        nodes = []
        counter = [0]

        def add(operation, step, deps, branch=None, gate=None):
            counter[0] += 1
            node_id = f"{counter[0]:02d}_{operation.lower()}"
            meta = {"step": step}
            if branch is not None:
                meta["branch"] = branch
            if gate is not None:
                meta["gate"] = gate
            if operation == "RUN":
                meta["agent"] = step.get("name")
            nodes.append({
                "id": node_id,
                "operation": operation,
                "name": str(step.get("name") or step.get("value") or operation),
                "dependencies": list(deps),
                "metadata": meta,
            })
            return node_id

        def walk(steps, deps, branch=None, gate=None):
            current = list(deps)
            for step in steps:
                op = step["operation"]
                if op == "PARALLEL":
                    ends = []
                    for child in step.get("steps", []):
                        ends.extend(walk([child], current, branch=branch, gate=gate))
                    join_step = {"operation": "JOIN", "names": []}
                    current = [add("JOIN", join_step, ends or current, branch=branch, gate=gate)]
                elif op == "IF":
                    gate_id = add("IF", step, current, branch=branch, gate=gate)
                    branch_ends = []
                    then_end = walk(step.get("then", []), [gate_id], branch="then", gate=gate_id)
                    branch_ends.extend(then_end or [gate_id])
                    for idx, else_if in enumerate(step.get("else_if", [])):
                        label = f"else_if_{idx}"
                        # Attach condition onto a synthetic IF branch marker stored in step
                        branch_step = {
                            "operation": "ELSE_IF",
                            "condition": else_if.get("condition"),
                            "steps": else_if.get("steps", []),
                        }
                        # Evaluate else-if as part of IF gate; steps get branch label
                        ends = walk(else_if.get("steps", []), [gate_id], branch=label, gate=gate_id)
                        branch_ends.extend(ends or [gate_id])
                    else_end = walk(step.get("else", []), [gate_id], branch="else", gate=gate_id)
                    branch_ends.extend(else_end or [gate_id])
                    # Barrier after exclusive branches so subsequent steps wait for one path
                    join_step = {"operation": "JOIN", "names": ["if"]}
                    current = [add("JOIN", join_step, branch_ends, branch=branch, gate=gate)]
                elif op == "JOIN":
                    # Explicit JOIN after PARALLEL is optional; if present, chain it
                    current = [add("JOIN", step, current, branch=branch, gate=gate)]
                else:
                    current = [add(op, step, current, branch=branch, gate=gate)]
            return current

        for workflow in workflows:
            walk(workflow["steps"], [])
        return {"nodes": nodes, "version": "0.9"}
