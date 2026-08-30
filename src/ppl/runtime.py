class CognitiveEngine:
    """Local deterministic stand-in for the future AI gateway."""

    def classify(self, text, categories):
        t = str(text).lower()
        scores = {c: 0 for c in categories}
        keywords = {
            "ACCESS": ["login","password","permission","access","authentication"],
            "NETWORK": ["network","dns","latency","timeout"],
            "DATABASE": ["database","db","sql","query","connection pool","deadlock"],
            "APPLICATION": ["application","app","crash","exception"],
            "INFRASTRUCTURE": ["server","cpu","memory","disk","host"],
        }
        for c, words in keywords.items():
            scores[c] = sum(1 for w in words if w in t)
        best = max(scores, key=scores.get)
        confidence = 0.55 if scores[best] == 0 else min(0.96, 0.70 + 0.08 * scores[best])
        return {"category": best, "confidence": round(confidence, 2)}

    def extract(self, incident, fields):
        text = str(incident.get("description", "")).lower()
        out = {}
        if "root_cause" in fields:
            out["root_cause"] = (
                "Database connection pool exhaustion" if "connection pool" in text else
                "Authentication or access issue" if ("login" in text or "password" in text) else
                "Service timeout or network connectivity issue" if "timeout" in text else
                "Requires further investigation"
            )
        if "resolution" in fields:
            out["resolution"] = (
                "Restart or recycle the connection pool and validate database capacity" if "connection pool" in text else
                "Validate credentials and access permissions" if ("login" in text or "password" in text) else
                "Check network path and service availability" if "timeout" in text else
                "Follow operational runbook"
            )
        return out

    def reason(self, instruction, incident, context):
        text = (str(incident) + " " + str(context)).lower()
        if "repetitive" in instruction.lower():
            repetitive = any(x in text for x in ["repeated", "recurring", "again", "multiple", "historical"])
            return {"repetitive": repetitive, "confidence": 0.88 if repetitive else 0.72}
        if "automation" in instruction.lower() or "candidate" in instruction.lower():
            repetitive = bool(context.get("repetitive", False))
            return {
                "score": 86 if repetitive else 42,
                "rationale": "Repetitive and relatively deterministic remediation." if repetitive else "Insufficient evidence of a repeatable remediation pattern.",
                "confidence": 0.89 if repetitive else 0.76
            }
        return {"result": "REASONED", "confidence": 0.70}

class Runtime:
    def __init__(self, pir):
        self.pir = pir
        self.ai = CognitiveEngine()
        self.context = {}
        self.trace = []
        self.return_value = None

    def run(self, input_data):
        self.context.update(input_data)
        if not self.pir["workflows"]:
            raise RuntimeError("No workflow defined")
        workflow = next((w for w in self.pir["workflows"] if w["name"] == "Main"), self.pir["workflows"][0])
        self._steps(workflow["steps"])
        return self.return_value if self.return_value is not None else self.context

    def _steps(self, steps):
        for s in steps:
            op = s["operation"]
            if op == "RECEIVE":
                self.trace.append(("RECEIVE", "D", "✓"))
            elif op == "RUN":
                self._run_agent(s["name"])
            elif op == "IF":
                self._run_condition(s)
            elif op == "RETURN":
                self.return_value = s["value"]
                self.trace.append(("RETURN", "D", str(s["value"])))
                return

    def _run_agent(self, name):
        agent = next(a for a in self.pir["agents"] if a["name"] == name)
        local = dict(self.context)
        self.trace.append((f"RUN {name}", "D", "✓"))
        for op in agent["operations"]:
            if op["operation"] == "CLASSIFY":
                source = self._resolve(op["target"], local)
                out = self.ai.classify(source, op["categories"])
                local.update(out)
                self.trace.append(("CLASSIFY", "C", f'{out["category"]} ({out["confidence"]:.2f})'))
            elif op["operation"] == "EXTRACT":
                out = self.ai.extract(local.get("incident", {}), op["fields"])
                local.update(out)
                self.trace.append(("EXTRACT", "C", str(out)))
            elif op["operation"] == "REASON":
                out = self.ai.reason(op["instruction"], local.get("incident", {}), local)
                local.update(out)
                self.trace.append(("REASON", "C", str(out)))
        self.context.update(local)
        self.context[name] = dict(local)

    def _run_condition(self, s):
        if self._eval(s["condition"]):
            self._steps(s["then"]); return
        for branch in s["else_if"]:
            if self._eval(branch["condition"]):
                self._steps(branch["steps"]); return
        self._steps(s["else"])

    def _resolve(self, name, local):
        cur = local
        for part in name.split("."):
            if isinstance(cur, dict): cur = cur.get(part, "")
            else: return ""
        return cur

    def _eval(self, c):
        left = self._resolve(c["left"], self.context)
        right = c["right"]
        if isinstance(right, str) and "." in right:
            right = self._resolve(right, self.context)
        return {">":left>right, "<":left<right, ">=":left>=right, "<=":left<=right, "==":left==right, "!=":left!=right}[c["operator"]]
