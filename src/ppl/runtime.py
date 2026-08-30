import os
from .ai_gateway import AIGateway, AIRequest, ModelPolicy
from .ai_runtime import CognitiveRuntime
from .model_policy import resolve_policy
from .v03_runtime import HumanApproval, KnowledgeSource, MemoryStore, ToolRegistry


class Runtime:
    def __init__(self, pir, gateway=None):
        self.pir = pir
        self.gateway = gateway or AIGateway()
        self.cognitive = CognitiveRuntime(self.gateway.adapter)
        self.context = {}
        self.trace = []
        self.return_value = None
        self.steps_run = 0
        self.policies = {
            k: ModelPolicy(name=k, **{kk: vv for kk, vv in v.items() if kk != "name"})
            for k, v in pir.get("model_policies", {}).items()
        }
        self.knowledge = [
            KnowledgeSource(item["name"], {source: source for source in item.get("sources", [])})
            for item in pir.get("knowledge", [])
        ]
        self.memory = MemoryStore(pir["memory"][0]["name"]) if pir.get("memory") else MemoryStore("default")
        self.tools = ToolRegistry()
        for tool in pir.get("tools", []):
            for action in tool.get("actions", []):
                self.tools.register(
                    action,
                    lambda registered=action, **kwargs: {"tool": registered, "args": kwargs, "status": "ok"},
                )
        self.human = HumanApproval()

    def run(self, input_data):
        self.context.update(input_data)
        for guard in self.pir.get("guards", []):
            self.trace.append((f"GUARD {guard['name']}", "D", "ok"))
        for auth in self.pir.get("authorizations", []):
            self.trace.append((f"AUTHORIZATION {auth['name']}", "D", auth.get("requires") or "ok"))
        if not self.pir["workflows"]:
            raise RuntimeError("No workflow defined")
        wf = next((w for w in self.pir["workflows"] if w["name"] == "Main"), self.pir["workflows"][0])
        self._steps(wf["steps"])
        return self.return_value if self.return_value is not None else self.context

    def _budget_guard(self):
        self.steps_run += 1
        for budget in self.pir.get("budgets", []):
            max_steps = budget.get("max_steps")
            if max_steps is not None and self.steps_run > max_steps:
                raise RuntimeError(f"BUDGET exceeded: max_steps={max_steps}")

    def _steps(self, steps):
        for s in steps:
            if self.return_value is not None:
                return
            self._budget_guard()
            op = s["operation"]
            if op == "RECEIVE":
                self.trace.append((f"RECEIVE {s.get('name', '')}".strip(), "D", "ok"))
            elif op == "RUN":
                self._run_agent(s["name"])
            elif op == "IF":
                self._condition(s)
            elif op == "RETURN":
                value = s["value"] if s.get("literal") else self._return_value(s["value"])
                self.return_value = value
                self.trace.append(("RETURN", "D", str(value)))
                return
            elif op == "HUMAN_APPROVAL":
                self._human_approval(s)
            elif op == "PARALLEL":
                self.trace.append(("PARALLEL", "D", f"{len(s.get('steps', []))} branches"))
                self._steps(s.get("steps", []))
            elif op == "JOIN":
                self.trace.append(("JOIN", "D", " ".join(s.get("names") or []) or "ok"))
            elif op == "WAIT":
                self.trace.append((f"WAIT {s.get('condition', '')}".strip(), "D", "WAITING"))
            elif op == "CHECKPOINT":
                self.trace.append((f"CHECKPOINT {s.get('name', '')}".strip(), "D", "saved"))
            elif op == "CALL":
                result = {"tool": s.get("target"), "args": s.get("args", {}), "status": "ok"}
                try:
                    action = (s.get("target") or "").split(".")[-1]
                    result = self.tools.call(action) if action in self.tools.actions else result
                except Exception:
                    pass
                self.context.setdefault("calls", []).append(result)
                self.trace.append((f"CALL {s.get('target')}", "D", str(result.get("status", "ok"))))

    def _human_approval(self, step):
        options = step.get("options") or ["APPROVE", "REJECT"]
        question = step.get("question") or "Approve this action?"
        decision = self.human.request("local", question, options)
        choice = os.getenv("PPL_HUMAN_DECISION", options[0])
        resolved = self.human.resolve(decision, choice if choice in options else options[0])
        self.context["human_decision"] = resolved.decision
        self.trace.append(("HUMAN_APPROVAL", "H", resolved.decision))

    def _agent_payload(self, agent, local):
        name = agent.get("input")
        if name and name in local:
            value = local[name]
            return value if isinstance(value, dict) else {"value": value}
        return local

    def _run_agent(self, name):
        agent = next(a for a in self.pir["agents"] if a["name"] == name)
        local = dict(self.context)
        self.trace.append((f"RUN {name}", "D", "ok"))
        payload = self._agent_payload(agent, local)
        for op in agent["operations"]:
            policy = self.policies.get(agent.get("policy") or "", resolve_policy(agent.get("policy")))
            if op["operation"] == "CLASSIFY":
                source = self._resolve(op["target"], local)
                req = AIRequest("CLASSIFY", "Classify the input into the allowed categories.", source, op["schema"], op["categories"], policy)
                response = self.cognitive.execute(req)
                local.update(response.output)
                self._trace_ai("CLASSIFY", response)
            elif op["operation"] == "EXTRACT":
                req = AIRequest("EXTRACT", "Extract the requested fields.", payload, op["schema"], [], policy)
                response = self.cognitive.execute(req)
                local.update(response.output)
                self._trace_ai("EXTRACT", response)
            elif op["operation"] == "REASON":
                req = AIRequest("REASON", op["instruction"], {**payload, "context": local}, op["schema"], [], policy)
                response = self.cognitive.execute(req)
                local.update(response.output)
                self._trace_ai("REASON", response)
        self.context.update(local)
        self.context[name] = dict(local)

    def _trace_ai(self, operation, response):
        self.trace.append((
            operation,
            "C",
            f"model={response.model} latency={response.latency_ms:.2f}ms tokens={response.input_tokens + response.output_tokens} cost=${response.cost_usd:.4f} attempts={response.attempts}",
        ))

    def _condition(self, s):
        if self._eval(s["condition"]):
            self._steps(s["then"])
            return
        for branch in s["else_if"]:
            if self._eval(branch["condition"]):
                self._steps(branch["steps"])
                return
        self._steps(s["else"])

    def _resolve(self, name, local):
        if not isinstance(name, str) or not name:
            return name
        cur = local
        for part in name.split("."):
            if isinstance(cur, dict):
                if part not in cur:
                    return ""
                cur = cur[part]
            else:
                return ""
        return cur

    def _return_value(self, value):
        if not isinstance(value, str):
            return value
        if "." in value or value in self.context:
            resolved = self._resolve(value, self.context)
            return resolved
        return value

    def _eval(self, c):
        left = self._resolve(c["left"], self.context)
        right = c["right"]
        return {">": left > right, "<": left < right, ">=": left >= right, "<=": left <= right, "==": left == right, "!=": left != right}[c["operator"]]
