"""PPL 0.9 graph-driven runtime with durable pause/resume."""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from .ai_gateway import AIGateway, AIRequest, ModelPolicy
from .ai_runtime import CognitiveRuntime
from .execution_graph import (
    Execution,
    ExecutionStatus,
    GraphExecutor,
    GraphNode,
    NodeStatus,
    PauseExecution,
)
from .knowledge import (
    knowledge_for_agent,
    load_knowledge_sources,
    load_memory,
    resolve_memory_key,
)
from .model_policy import resolve_policy
from .production_runtime import InMemoryExecutionStore as ProdStore
from .production_runtime import ProductionExecutor, StreamEvent
from .providers.structured import substitute_policy_defaults
from .store import FileExecutionStore, InMemoryGraphStore
from .expr import evaluate, evaluate_bool
from .fs import resolve_path
from .prompts import prompt_body, render_template
from .provider import apply_program_environment
from .tools import build_tool_registry, resolve_action
from .v03_runtime import HumanApproval


class _AsyncCognitiveAdapter:
    """Adapt sync CognitiveRuntime to the ProductionExecutor async contract."""

    def __init__(self, cognitive: CognitiveRuntime):
        self.cognitive = cognitive

    async def execute(self, request: AIRequest):
        return self.cognitive.execute(request)

    async def stream(self, request: AIRequest):
        response = self.cognitive.execute(request)
        yield StreamEvent("COMPLETE", {"output": response.output})
        return
        yield  # pragma: no cover


class Runtime:
    def __init__(
        self,
        pir: dict[str, Any],
        gateway: AIGateway | None = None,
        store=None,
        program_path: str | Path | None = None,
        worker_id: str | None = None,
        interactive: bool | None = None,
    ):
        self.pir = pir
        apply_program_environment(pir.get("environments"))
        if gateway is None:
            from .provider import build_adapter
            gateway = AIGateway(build_adapter())
        self.gateway = gateway
        self.cognitive = CognitiveRuntime(self.gateway.adapter)
        self._prod_store = ProdStore()
        self.production = ProductionExecutor(_AsyncCognitiveAdapter(self.cognitive), self._prod_store)
        self.program_path = Path(program_path) if program_path else None
        program_dir = self.program_path.parent if self.program_path else Path.cwd()
        self.store = store or FileExecutionStore()
        self.worker_id = worker_id
        self.interactive = sys.stdin.isatty() if interactive is None else interactive
        self.context: dict[str, Any] = {}
        self.trace: list[tuple[str, str, str]] = []
        self.prints: list[str] = []
        self.return_value = None
        self.execution: Execution | None = None
        self.steps_run = 0
        self._loop_guard = int(os.getenv("PPL_MAX_STEPS", "10000") or 10000)
        default_model = os.getenv("PPL_AI_MODEL") or os.getenv("PPL_OPENAI_MODEL")
        self.policies = {
            k: substitute_policy_defaults(
                ModelPolicy(name=k, **{kk: vv for kk, vv in v.items() if kk != "name"}),
                default_model,
            )
            for k, v in pir.get("model_policies", {}).items()
        }
        self.knowledge = load_knowledge_sources(pir.get("knowledge") or [], program_dir)
        self.memory = load_memory(pir.get("memory") or [], pir.get("application") or "app")
        self.tools = build_tool_registry(pir.get("tools"), pir.get("imports"))
        self.human = HumanApproval()

    def run(
        self,
        input_data: dict[str, Any] | None = None,
        execution_id: str | None = None,
        resume: bool = False,
    ) -> Any:
        return asyncio.run(self.run_async(input_data, execution_id=execution_id, resume=resume))

    async def run_async(
        self,
        input_data: dict[str, Any] | None = None,
        execution_id: str | None = None,
        resume: bool = False,
    ) -> Any:
        if resume and execution_id:
            execution = self.store.load(execution_id)
            execution.resume_from_wait()
        elif execution_id and self.store.exists(execution_id):
            execution = self.store.load(execution_id)
            if execution.status is ExecutionStatus.WAITING:
                execution.resume_from_wait()
            elif execution.status is ExecutionStatus.SUCCEEDED:
                self.execution = execution
                self.context = dict(execution.context)
                self.return_value = execution.result
                return execution.result
        else:
            execution = self._new_execution(input_data or {}, execution_id)

        self.execution = execution
        self.context = execution.context
        for guard in self.pir.get("guards", []):
            self.trace.append((f"GUARD {guard['name']}", "D", "ok"))
        for auth in self.pir.get("authorizations", []):
            self.trace.append((f"AUTHORIZATION {auth['name']}", "D", auth.get("requires") or "ok"))

        executor = GraphExecutor(self.store, worker_id=self.worker_id)
        handlers = self._handlers()
        finished = await executor.run(execution, handlers)
        self.execution = finished
        self.context = finished.context
        self.return_value = finished.result
        if finished.status is ExecutionStatus.WAITING:
            return {
                "status": "WAITING",
                "execution_id": finished.execution_id,
                "wait": finished.wait,
            }
        return finished.result if finished.result is not None else finished.context

    def _new_execution(self, input_data: dict[str, Any], execution_id: str | None) -> Execution:
        graph = self.pir.get("graph") or {"nodes": []}
        nodes = {
            item["id"]: GraphNode(
                node_id=item["id"],
                operation=item["operation"],
                dependencies=list(item.get("dependencies") or []),
                metadata=dict(item.get("metadata") or {}),
            )
            for item in graph.get("nodes") or []
        }
        if not nodes:
            raise RuntimeError("Compiled program has no execution graph")
        execution = Execution(
            execution_id=execution_id or str(uuid.uuid4()),
            nodes=nodes,
            context=dict(input_data),
            program_path=str(self.program_path) if self.program_path else None,
            graph_version=str(graph.get("version") or self.pir.get("version") or "0.9"),
        )
        self.store.save(execution)
        return execution

    def _handlers(self) -> dict[str, Any]:
        mapping = {
            "RECEIVE": self._handle_receive,
            "RUN": self._handle_run,
            "IF": self._handle_if,
            "RETURN": self._handle_return,
            "LET": self._handle_let,
            "PRINT": self._handle_print,
            "READ": self._handle_read,
            "WRITE": self._handle_write,
            "FOR": self._handle_for,
            "WHILE": self._handle_while,
            "HUMAN_APPROVAL": self._handle_human,
            "JOIN": self._handle_join,
            "WAIT": self._handle_wait,
            "CHECKPOINT": self._handle_checkpoint,
            "CALL": self._handle_call,
            "PARALLEL": self._handle_noop,
            "ELSE_IF": self._handle_noop,
        }
        return mapping

    def _step(self, node: GraphNode) -> dict[str, Any]:
        return dict((node.metadata or {}).get("step") or {})

    def _budget_guard(self) -> None:
        self.steps_run += 1
        for budget in self.pir.get("budgets", []):
            max_steps = budget.get("max_steps")
            if max_steps is not None and self.steps_run > max_steps:
                raise RuntimeError(f"BUDGET exceeded: max_steps={max_steps}")

    def _handle_noop(self, node: GraphNode, execution: Execution) -> str:
        self._budget_guard()
        self.trace.append((node.operation, "D", "ok"))
        return "ok"

    def _handle_receive(self, node: GraphNode, execution: Execution) -> str:
        self._budget_guard()
        step = self._step(node)
        name = step.get("name", "")
        self.trace.append((f"RECEIVE {name}".strip(), "D", "ok"))
        return name

    def _handle_let(self, node: GraphNode, execution: Execution) -> Any:
        self._budget_guard()
        step = self._step(node)
        name = step.get("name", "")
        value = evaluate(step.get("expr") or step.get("expr_text", ""), execution.context)
        execution.context[name] = value
        self.trace.append((f"LET {name}", "D", str(value)))
        return value

    def _handle_print(self, node: GraphNode, execution: Execution) -> str:
        self._budget_guard()
        step = self._step(node)
        value = evaluate(step.get("expr") or step.get("expr_text", ""), execution.context)
        text = str(value)
        self.prints.append(text)
        print(text)
        self.trace.append(("PRINT", "D", text))
        return text

    def _handle_read(self, node: GraphNode, execution: Execution) -> str:
        self._budget_guard()
        step = self._step(node)
        path = str(self._resolve_arg(step.get("path", ""), execution.context))
        target = resolve_path(path)
        text = target.read_text(encoding="utf-8")
        execution.context[step.get("var", "content")] = text
        self.trace.append((f"READ {target}", "D", f"{len(text)} chars"))
        return text

    def _handle_write(self, node: GraphNode, execution: Execution) -> str:
        self._budget_guard()
        step = self._step(node)
        path = str(self._resolve_arg(step.get("path", ""), execution.context))
        value = evaluate(step.get("expr") or step.get("expr_text", ""), execution.context)
        target = resolve_path(path, create_parents=True)
        if isinstance(value, (dict, list)):
            body = json.dumps(value, indent=2)
        else:
            body = str(value)
        target.write_text(body, encoding="utf-8")
        self.trace.append((f"WRITE {target}", "D", f"{len(body)} chars"))
        return body

    def _handle_for(self, node: GraphNode, execution: Execution) -> str:
        self._budget_guard()
        step = self._step(node)
        item_name = step.get("item", "item")
        source = self._resolve_arg(step.get("source", ""), execution.context)
        if not isinstance(source, list):
            source = list(source) if isinstance(source, (tuple, set)) else [source]
        for item in source:
            execution.context[item_name] = item
            self._execute_steps(step.get("body") or [], execution)
        self.trace.append(("FOR", "D", f"{len(source)} items"))
        return f"{len(source)} items"

    def _handle_while(self, node: GraphNode, execution: Execution) -> str:
        self._budget_guard()
        step = self._step(node)
        iterations = 0
        while evaluate_bool(step.get("condition") or step.get("condition_text", ""), execution.context):
            iterations += 1
            if iterations > self._loop_guard:
                raise RuntimeError(f"WHILE exceeded PPL_MAX_STEPS={self._loop_guard}")
            self._execute_steps(step.get("body") or [], execution)
        self.trace.append(("WHILE", "D", f"{iterations} iterations"))
        return f"{iterations} iterations"

    def _execute_steps(self, steps: list[dict[str, Any]], execution: Execution) -> None:
        for step in steps:
            op = step.get("operation")
            if op == "LET":
                name = step.get("name", "")
                execution.context[name] = evaluate(step.get("expr") or step.get("expr_text", ""), execution.context)
            elif op == "PRINT":
                text = str(evaluate(step.get("expr") or step.get("expr_text", ""), execution.context))
                self.prints.append(text)
                print(text)
            elif op == "READ":
                path = str(self._resolve_arg(step.get("path", ""), execution.context))
                target = resolve_path(path)
                execution.context[step.get("var", "content")] = target.read_text(encoding="utf-8")
            elif op == "WRITE":
                path = str(self._resolve_arg(step.get("path", ""), execution.context))
                value = evaluate(step.get("expr") or step.get("expr_text", ""), execution.context)
                target = resolve_path(path, create_parents=True)
                body = json.dumps(value, indent=2) if isinstance(value, (dict, list)) else str(value)
                target.write_text(body, encoding="utf-8")
            elif op == "IF":
                taken = "else"
                if self._eval_condition(step.get("condition") or {}, execution.context):
                    taken = "then"
                    self._execute_steps(step.get("then") or [], execution)
                else:
                    matched = False
                    for branch in step.get("else_if") or []:
                        if self._eval_condition(branch.get("condition") or {}, execution.context):
                            self._execute_steps(branch.get("steps") or [], execution)
                            matched = True
                            break
                    if not matched:
                        self._execute_steps(step.get("else") or [], execution)
            elif op == "RETURN":
                value = step.get("value") if step.get("literal") else self._return_value(step.get("value"), execution.context)
                execution.result = value
                self.return_value = value
            elif op == "CALL":
                action = resolve_action(step.get("target") or "")
                args = {k: self._resolve_arg(v, execution.context) for k, v in (step.get("args") or {}).items()}
                self.tools.call(action, **args)
            elif op == "FOR":
                self._handle_for(GraphNode("inline", "FOR", [], {"step": step}), execution)
            elif op == "WHILE":
                self._handle_while(GraphNode("inline", "WHILE", [], {"step": step}), execution)
            elif op == "RUN":
                self._run_agent(step.get("name") or "", execution.context)
            else:
                continue

    def _handle_join(self, node: GraphNode, execution: Execution) -> str:
        self._budget_guard()
        step = self._step(node)
        names = " ".join(step.get("names") or []) or "ok"
        self.trace.append(("JOIN", "D", names))
        return names

    def _handle_run(self, node: GraphNode, execution: Execution) -> dict[str, Any]:
        self._budget_guard()
        # Optional sleep for parallel timing tests
        delay = float(os.getenv("PPL_PARALLEL_SLEEP", "0") or 0)
        if delay:
            time.sleep(delay)
        step = self._step(node)
        name = step.get("name") or node.metadata.get("agent")
        if not name:
            raise RuntimeError(f"RUN node {node.node_id} missing agent name")
        result = self._run_agent(name, execution.context)
        return result

    def _handle_if(self, node: GraphNode, execution: Execution) -> str:
        self._budget_guard()
        step = self._step(node)
        condition = step.get("condition") or {}
        taken = "else"
        if self._eval_condition(condition, execution.context):
            taken = "then"
        else:
            for idx, branch in enumerate(step.get("else_if") or []):
                if self._eval_condition(branch.get("condition") or {}, execution.context):
                    taken = f"else_if_{idx}"
                    break
        gates = execution.context.setdefault("_gates", {})
        gates[node.node_id] = taken
        self.trace.append(("IF", "D", taken))
        return taken

    def _handle_return(self, node: GraphNode, execution: Execution) -> Any:
        self._budget_guard()
        step = self._step(node)
        if step.get("literal"):
            value = step.get("value")
        elif step.get("expr"):
            value = evaluate(step.get("value"), execution.context)
        else:
            value = self._return_value(step.get("value"), execution.context)
        execution.result = value
        self.return_value = value
        self.trace.append(("RETURN", "D", str(value)))
        self._persist_memory_outcome(execution.context, value)
        return value

    def _handle_human(self, node: GraphNode, execution: Execution) -> str:
        self._budget_guard()
        step = self._step(node)
        options = step.get("options") or ["APPROVE", "REJECT"]
        question = step.get("question") or "Approve this action?"
        env_choice = os.getenv("PPL_HUMAN_DECISION")
        prior = (execution.wait or {}).get("decision") if execution.wait else None
        context_choice = execution.context.get("human_decision")

        choice = None
        if env_choice and env_choice in options:
            choice = env_choice
        elif context_choice and context_choice in options:
            choice = context_choice
        elif prior and prior in options:
            choice = prior
        elif self.interactive:
            print(f"HUMAN_APPROVAL [{execution.execution_id}]")
            print(f"Question: {question}")
            print(f"Options: {', '.join(options)}")
            raw = input("Decision> ").strip()
            if raw in options:
                choice = raw

        if choice is None:
            wait = {
                "reason": "HUMAN_APPROVAL",
                "node_id": node.node_id,
                "question": question,
                "options": options,
            }
            execution.wait = wait
            node.status = NodeStatus.WAITING
            self.trace.append(("HUMAN_APPROVAL", "H", "WAITING"))
            raise PauseExecution(wait)

        decision = self.human.request(execution.execution_id, question, options)
        resolved = self.human.resolve(decision, choice)
        execution.context["human_decision"] = resolved.decision
        self.trace.append(("HUMAN_APPROVAL", "H", resolved.decision))
        return resolved.decision

    def _handle_wait(self, node: GraphNode, execution: Execution) -> str:
        self._budget_guard()
        step = self._step(node)
        condition = (step.get("condition") or "").strip()
        if self._wait_satisfied(condition, execution.context):
            self.trace.append((f"WAIT {condition}".strip(), "D", "ok"))
            return "ok"
        wait = {
            "reason": "WAIT",
            "node_id": node.node_id,
            "condition": condition,
        }
        execution.wait = wait
        node.status = NodeStatus.WAITING
        self.trace.append((f"WAIT {condition}".strip(), "D", "WAITING"))
        raise PauseExecution(wait)

    def _wait_satisfied(self, condition: str, context: dict[str, Any]) -> bool:
        if not condition:
            return True
        # duration: 1s / 500ms
        m = re.fullmatch(r"(\d+(?:\.\d+)?)(ms|s)", condition)
        if m:
            amount = float(m.group(1))
            seconds = amount / 1000.0 if m.group(2) == "ms" else amount
            # For local tests, treat duration waits as immediately satisfied after first pause resume
            # by storing deadline on context.
            key = f"_wait_deadline:{condition}"
            if key not in context:
                context[key] = time.time() + seconds
                return False
            return time.time() >= float(context[key])
        if condition.startswith("file:"):
            return Path(condition[5:]).exists()
        value = self._resolve(condition, context)
        return bool(value)

    def _handle_checkpoint(self, node: GraphNode, execution: Execution) -> str:
        self._budget_guard()
        step = self._step(node)
        name = step.get("name") or node.node_id
        execution.checkpoint(name)
        node.status = NodeStatus.CHECKPOINTED
        self.trace.append((f"CHECKPOINT {name}".strip(), "D", "saved"))
        self.store.save(execution)
        return name

    def _handle_call(self, node: GraphNode, execution: Execution) -> dict[str, Any]:
        self._budget_guard()
        step = self._step(node)
        target = step.get("target") or ""
        action = resolve_action(target)
        raw_args = dict(step.get("args") or {})
        args = {k: self._resolve_arg(v, execution.context) for k, v in raw_args.items()}
        if action not in self.tools.actions:
            raise KeyError(f"Unknown tool action: {action}")
        result = self.tools.call(action, **args)
        execution.context.setdefault("calls", []).append(result)
        self.trace.append((f"CALL {target}", "D", str(result.get("status", "ok"))))
        return result

    def _resolve_arg(self, value: Any, context: dict[str, Any]) -> Any:
        if isinstance(value, str) and (value in context or "." in value):
            resolved = self._resolve(value, context)
            if resolved != "":
                return resolved
        if isinstance(value, str) and len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            return value[1:-1]
        return value

    def _agent_payload(self, agent: dict[str, Any], local: dict[str, Any]) -> dict[str, Any]:
        name = agent.get("input")
        if name and name in local:
            value = local[name]
            return value if isinstance(value, dict) else {"value": value}
        return local

    def _run_agent(self, name: str, context: dict[str, Any]) -> dict[str, Any]:
        agent = next(a for a in self.pir["agents"] if a["name"] == name)
        local = dict(context)
        self.trace.append((f"RUN {name}", "D", "ok"))
        payload = self._agent_payload(agent, local)

        # Memory read
        for mem_name in agent.get("memory") or []:
            key_expr = None
            for decl in self.pir.get("memory") or []:
                if decl.get("name") == mem_name:
                    key_expr = decl.get("key")
            key = resolve_memory_key(key_expr, local)
            if key is not None:
                prior = self.memory.read(key)
                if prior is not None:
                    local.setdefault("memory", {})[mem_name] = prior

        # Knowledge retrieve
        query_bits = []
        if isinstance(payload, dict):
            query_bits.extend(str(v) for v in payload.values())
        query = " ".join(query_bits) or name
        knowledge_hits = knowledge_for_agent(self.knowledge, agent.get("knowledge") or [], query)
        if knowledge_hits:
            local["knowledge"] = knowledge_hits

        for op in agent["operations"]:
            policy = self.policies.get(agent.get("policy") or "", resolve_policy(agent.get("policy")))
            if op["operation"] == "CLASSIFY":
                source = self._resolve(op["target"], local)
                req = AIRequest(
                    "CLASSIFY",
                    "Classify the input into the allowed categories.",
                    {"input": source, "knowledge": knowledge_hits},
                    op["schema"],
                    op["categories"],
                    policy,
                )
                response = self._cognitive_execute(req)
                local.update(response.output)
                self._trace_ai("CLASSIFY", response)
            elif op["operation"] == "EXTRACT":
                req = AIRequest(
                    "EXTRACT",
                    "Extract the requested fields.",
                    {"payload": payload, "knowledge": knowledge_hits},
                    op["schema"],
                    [],
                    policy,
                )
                response = self._cognitive_execute(req)
                local.update(response.output)
                self._trace_ai("EXTRACT", response)
            elif op["operation"] == "PROMPT":
                template_name = op.get("template", "")
                try:
                    template = prompt_body(template_name, self.pir.get("prompts") or [])
                except KeyError:
                    template = template_name
                bindings = {
                    k: self._resolve_arg(v, local) for k, v in (op.get("bindings") or {}).items()
                }
                instruction = render_template(template, bindings)
                schema = _schema_from_agent_outputs(agent)
                req = AIRequest(
                    "REASON",
                    instruction,
                    {**payload, "context": local, "knowledge": knowledge_hits},
                    schema or {"text": "TEXT", "confidence": "CONFIDENCE"},
                    [],
                    policy,
                )
                response = self._cognitive_execute(req)
                local.update(response.output)
                self._trace_ai("PROMPT", response)
            elif op["operation"] == "REASON":
                req = AIRequest(
                    "REASON",
                    op["instruction"],
                    {**payload, "context": local, "knowledge": knowledge_hits, "memory": local.get("memory")},
                    op["schema"],
                    [],
                    policy,
                )
                response = self._cognitive_execute(req)
                local.update(response.output)
                self._trace_ai("REASON", response)

        context.update(local)
        context[name] = dict(local)
        # Keep agent-scoped view for RETURN Agent.field
        return dict(local)

    def _cognitive_execute(self, req: AIRequest):
        """Execute cognitive ops through ProductionExecutor + CognitiveRuntime."""
        exec_id = f"{(self.execution.execution_id if self.execution else 'local')}-{self.steps_run}-{req.operation}"
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            # Called from a worker thread via to_thread; use a fresh loop.
            return asyncio.run(self.production.execute(req, exec_id, max_retries=req.policy.max_retries))
        return asyncio.run(self.production.execute(req, exec_id, max_retries=req.policy.max_retries))

    def _persist_memory_outcome(self, context: dict[str, Any], result: Any) -> None:
        for decl in self.pir.get("memory") or []:
            key = resolve_memory_key(decl.get("key"), context)
            if key is None:
                continue
            self.memory.write(key, {"result": result, "context_keys": list(context.keys())})

    def _trace_ai(self, operation: str, response: Any) -> None:
        self.trace.append((
            operation,
            "C",
            f"model={response.model} latency={response.latency_ms:.2f}ms tokens={response.input_tokens + response.output_tokens} cost=${response.cost_usd:.4f} attempts={response.attempts}",
        ))

    def _resolve(self, name: Any, local: dict[str, Any]) -> Any:
        if not isinstance(name, str) or not name:
            return name
        cur: Any = local
        for part in name.split("."):
            if isinstance(cur, dict):
                if part not in cur:
                    return ""
                cur = cur[part]
            else:
                return ""
        return cur

    def _return_value(self, value: Any, context: dict[str, Any]) -> Any:
        if isinstance(value, dict) and value.get("kind"):
            return evaluate(value, context)
        if not isinstance(value, str):
            return value
        if "." in value or value in context:
            return self._resolve(value, context)
        try:
            return evaluate(value, context)
        except SyntaxError:
            return value

    def _eval_condition(self, c: dict[str, Any], context: dict[str, Any]) -> bool:
        if not c:
            return False
        if c.get("type") == "expr":
            return evaluate_bool(c.get("expr") or c.get("text", ""), context)
        if "left" in c and "operator" in c:
            left = self._resolve(c.get("left"), context)
            right = c.get("right")
            op = c.get("operator")
            return {
                ">": left > right,
                "<": left < right,
                ">=": left >= right,
                "<=": left <= right,
                "==": left == right,
                "!=": left != right,
            }[op]
        return False

    def _eval(self, c: dict[str, Any], context: dict[str, Any]) -> bool:
        return self._eval_condition(c, context)


def _schema_from_agent_outputs(agent: dict[str, Any]) -> dict[str, str]:
    schema: dict[str, str] = {}
    for item in agent.get("outputs") or []:
        if ":" in item:
            name, type_name = map(str.strip, item.split(":", 1))
            schema[name] = type_name
    return schema


def approve_execution(store, execution_id: str, decision: str) -> Execution:
    execution = store.load(execution_id)
    if not execution.wait or execution.wait.get("reason") != "HUMAN_APPROVAL":
        raise RuntimeError(f"Execution {execution_id} is not waiting for human approval")
    options = execution.wait.get("options") or []
    if decision not in options:
        raise ValueError(f"Invalid decision '{decision}'. Options: {options}")
    execution.context["human_decision"] = decision
    execution.wait["decision"] = decision
    # Clear waiting node so resume re-runs it with decision present
    node_id = execution.wait.get("node_id")
    if node_id and node_id in execution.nodes:
        execution.nodes[node_id].status = NodeStatus.PENDING
    execution.status = ExecutionStatus.RESUMING
    execution.wait = None
    store.save(execution)
    return execution
