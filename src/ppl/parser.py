import re
from .ast import *


def clean_lines(text):
    lines = []
    for number, raw in enumerate(text.splitlines(), 1):
        raw = raw.split("#", 1)[0].rstrip()
        if raw.strip():
            lines.append((number, len(raw) - len(raw.lstrip(" ")), raw.strip()))
    return lines


class Parser:
    def __init__(self, text):
        self.lines = clean_lines(text)
        self.i = 0

    def error(self, msg):
        n = self.lines[self.i][0] if self.i < len(self.lines) else "EOF"
        raise SyntaxError(f"Line {n}: {msg}")

    def _body_lines(self, parent):
        lines = []
        while self.i < len(self.lines) and self.lines[self.i][1] > parent:
            lines.append(self.lines[self.i][2])
            self.i += 1
        return lines

    def parse(self):
        p = Program()
        while self.i < len(self.lines):
            _, indent, line = self.lines[self.i]
            if indent != 0:
                self.error("Top-level declaration must not be indented")
            if line.startswith("APP "):
                p.app = AppDecl(line[4:].strip())
                self.i += 1
            elif line.startswith("INPUT "):
                p.inputs.append(self.parse_input())
            elif line.startswith("MODEL_POLICY "):
                p.model_policies.append(self.parse_policy())
            elif line.startswith("GUARD "):
                p.guards.append(self.parse_guard())
            elif line.startswith("AUTHORIZATION "):
                p.authorizations.append(self.parse_authorization())
            elif line == "BUDGET" or line.startswith("BUDGET "):
                p.budgets.append(self.parse_budget())
            elif line.startswith("ENVIRONMENT "):
                p.environments.append(self.parse_environment())
            elif line.startswith("KNOWLEDGE "):
                p.knowledge.append(self.parse_knowledge())
            elif line.startswith("MEMORY "):
                p.memories.append(self.parse_memory())
            elif line.startswith("TOOL "):
                p.tools.append(self.parse_tool())
            elif line.startswith("AGENT "):
                p.agents.append(self.parse_agent())
            elif line.startswith("WORKFLOW "):
                p.workflows.append(self.parse_workflow())
            else:
                self.error(f"Unexpected line: {line}")
        return p

    def parse_input(self):
        _, parent, line = self.lines[self.i]
        name = line[6:].strip()
        self.i += 1
        fields = []
        while self.i < len(self.lines) and self.lines[self.i][1] > parent:
            _, _, line = self.lines[self.i]
            if ":" not in line:
                self.error(f"Expected field declaration, got: {line}")
            n, t = map(str.strip, line.split(":", 1))
            fields.append(InputField(n, t))
            self.i += 1
        return InputDecl(name, fields)

    def parse_policy(self):
        _, parent, line = self.lines[self.i]
        name = line[len("MODEL_POLICY "):].strip()
        self.i += 1
        vals = {}
        while self.i < len(self.lines) and self.lines[self.i][1] > parent:
            _, _, line = self.lines[self.i]
            if ":" in line:
                k, v = map(str.strip, line.split(":", 1))
                vals[k.lower()] = v
            self.i += 1
        return ModelPolicyDecl(
            name,
            vals.get("reasoning", "reasoning-default"),
            vals.get("classification", "classification-default"),
            vals.get("extraction", "extraction-default"),
            int(vals.get("max_retries", "1")),
            vals.get("fallback", "fallback-default"),
        )

    def parse_guard(self):
        _, parent, line = self.lines[self.i]
        name = line[len("GUARD "):].strip()
        self.i += 1
        return GuardDecl(name, self._body_lines(parent))

    def parse_authorization(self):
        _, parent, line = self.lines[self.i]
        name = line[len("AUTHORIZATION "):].strip()
        self.i += 1
        requires = None
        for body in self._body_lines(parent):
            if body.upper().startswith("REQUIRES "):
                requires = body[9:].strip()
        return AuthorizationDecl(name, requires)

    def parse_budget(self):
        _, parent, _ = self.lines[self.i]
        self.i += 1
        vals = {}
        for body in self._body_lines(parent):
            if ":" in body:
                k, v = map(str.strip, body.split(":", 1))
                vals[k.lower()] = v
        cost = float(vals["max_cost"]) if "max_cost" in vals else None
        steps = int(vals["max_steps"]) if "max_steps" in vals else None
        return BudgetDecl(cost, vals.get("max_latency"), steps)

    def parse_environment(self):
        _, parent, line = self.lines[self.i]
        name = line[len("ENVIRONMENT "):].strip()
        self.i += 1
        return EnvironmentDecl(name, self._body_lines(parent))

    def parse_knowledge(self):
        _, parent, line = self.lines[self.i]
        name = line[len("KNOWLEDGE "):].strip()
        self.i += 1
        sources = []
        for body in self._body_lines(parent):
            if body.upper().startswith("SOURCE "):
                sources.append(body[7:].strip())
        return KnowledgeDecl(name, sources)

    def parse_memory(self):
        _, parent, line = self.lines[self.i]
        name = line[len("MEMORY "):].strip()
        self.i += 1
        body = self._body_lines(parent)
        key = None
        for item in body:
            if item.upper().startswith("KEY "):
                key = item[4:].strip()
        return MemoryDecl(name, key, body)

    def parse_tool(self):
        _, parent, line = self.lines[self.i]
        name = line[len("TOOL "):].strip()
        self.i += 1
        body = self._body_lines(parent)
        actions = [item[7:].strip() for item in body if item.upper().startswith("ACTION ")]
        return ToolDecl(name, actions, body)

    def parse_agent(self):
        _, parent, line = self.lines[self.i]
        agent = AgentDecl(line[6:].strip())
        self.i += 1
        while self.i < len(self.lines) and self.lines[self.i][1] > parent:
            _, indent, line = self.lines[self.i]
            if line.startswith("INPUT "):
                agent.input_name = line[6:].strip()
                self.i += 1
            elif line.startswith("POLICY "):
                agent.policy = line[7:].strip()
                self.i += 1
            elif line.upper().startswith("USE KNOWLEDGE "):
                agent.knowledge.append(line[14:].strip())
                self.i += 1
            elif line.upper().startswith("USE MEMORY "):
                agent.memory.append(line[11:].strip())
                self.i += 1
            elif line.startswith("CLASSIFY "):
                agent.operations.append(self.parse_classify(indent))
            elif line == "EXTRACT":
                agent.operations.append(self.parse_extract(indent))
            elif line == "REASON":
                agent.operations.append(self.parse_reason(indent))
            elif line == "OUTPUT":
                agent.outputs = self.parse_output(indent)
            else:
                self.error(f"Unexpected AGENT statement: {line}")
        return agent

    def parse_classify(self, op_indent):
        _, _, line = self.lines[self.i]
        target = line[9:].strip()
        self.i += 1
        cats = []
        while self.i < len(self.lines) and self.lines[self.i][1] > op_indent:
            _, _, line = self.lines[self.i]
            cats.append(line)
            self.i += 1
        return ClassifyOp(target.removesuffix(" AS").strip(), cats)

    def parse_extract(self, op_indent):
        self.i += 1
        fields = []
        schema = {}
        while self.i < len(self.lines) and self.lines[self.i][1] > op_indent:
            _, _, line = self.lines[self.i]
            n, t = self._typed(line)
            fields.append(n)
            schema[n] = t
            self.i += 1
        return ExtractOp(fields, schema)

    def parse_reason(self, op_indent):
        self.i += 1
        instructions = []
        consider = []
        schema = {}
        while self.i < len(self.lines) and self.lines[self.i][1] > op_indent:
            _, indent, line = self.lines[self.i]
            if line.lower() == "consider:":
                self.i += 1
                while self.i < len(self.lines) and self.lines[self.i][1] > indent:
                    _, _, c = self.lines[self.i]
                    consider.append(c)
                    self.i += 1
            elif line.lower() == "output:":
                self.i += 1
                while self.i < len(self.lines) and self.lines[self.i][1] > indent:
                    _, _, o = self.lines[self.i]
                    n, t = self._typed(o)
                    schema[n] = t
                    self.i += 1
            else:
                instructions.append(line)
                self.i += 1
        return ReasonOp(" ".join(instructions).strip(), consider, schema)

    def parse_output(self, op_indent):
        self.i += 1
        fields = []
        while self.i < len(self.lines) and self.lines[self.i][1] > op_indent:
            _, _, line = self.lines[self.i]
            fields.append(line)
            self.i += 1
        return fields

    def _typed(self, line):
        return tuple(map(str.strip, line.split(":", 1))) if ":" in line else (line, "TEXT")

    def parse_workflow(self):
        _, parent, line = self.lines[self.i]
        self.i += 1
        return WorkflowDecl(line[9:].strip(), self.parse_steps(parent))

    def parse_steps(self, parent_indent):
        steps = []
        while self.i < len(self.lines) and self.lines[self.i][1] > parent_indent:
            _, indent, line = self.lines[self.i]
            if line.startswith("RECEIVE "):
                steps.append(ReceiveStep(line[8:].strip()))
                self.i += 1
            elif line.startswith("RUN "):
                steps.append(RunStep(line[4:].strip()))
                self.i += 1
            elif line.startswith("IF "):
                steps.append(self.parse_if(indent))
            elif line.startswith("RETURN "):
                raw = line[7:].strip()
                quoted = len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'"
                steps.append(ReturnStep(self.parse_value(raw), literal=quoted))
                self.i += 1
            elif line == "HUMAN_APPROVAL" or line.startswith("HUMAN_APPROVAL "):
                steps.append(self.parse_human_approval(indent))
            elif line == "PARALLEL":
                steps.append(self.parse_parallel(indent))
            elif line == "JOIN" or line.startswith("JOIN "):
                names = line[4:].strip().split() if line.startswith("JOIN ") else []
                steps.append(JoinStep([n for n in names if n]))
                self.i += 1
            elif line == "WAIT" or line.startswith("WAIT "):
                steps.append(WaitStep(line[4:].strip() if line.startswith("WAIT ") else ""))
                self.i += 1
            elif line == "CHECKPOINT" or line.startswith("CHECKPOINT "):
                steps.append(CheckpointStep(line[11:].strip() if line.startswith("CHECKPOINT ") else ""))
                self.i += 1
            elif line.startswith("CALL "):
                steps.append(self.parse_call(indent))
            else:
                self.error(f"Unexpected WORKFLOW statement: {line}")
        return steps

    def parse_human_approval(self, indent):
        self.i += 1
        question = None
        options = []
        while self.i < len(self.lines) and self.lines[self.i][1] > indent:
            _, nested, line = self.lines[self.i]
            if line.upper().startswith("QUESTION"):
                text = line.split(":", 1)[1].strip() if ":" in line else ""
                self.i += 1
                extras = []
                while self.i < len(self.lines) and self.lines[self.i][1] > nested:
                    extras.append(self.lines[self.i][2])
                    self.i += 1
                question = " ".join(part for part in [text, *extras] if part)
            elif line.upper().startswith("OPTIONS"):
                self.i += 1
                while self.i < len(self.lines) and self.lines[self.i][1] > nested:
                    options.append(self.lines[self.i][2])
                    self.i += 1
            else:
                break
        return HumanApprovalStep(question, options)

    def parse_parallel(self, indent):
        self.i += 1
        return ParallelStep(self.parse_steps(indent))

    def parse_call(self, indent):
        _, _, line = self.lines[self.i]
        target = line[5:].strip()
        self.i += 1
        args = {}
        while self.i < len(self.lines) and self.lines[self.i][1] > indent:
            _, _, body = self.lines[self.i]
            if "=" in body:
                k, v = map(str.strip, body.split("=", 1))
                args[k] = v
            self.i += 1
        return CallStep(target, args)

    def parse_if(self, indent):
        line = self.lines[self.i][2]
        if line.startswith("IF "):
            line = line[3:].strip()
        condition = self.parse_condition(line)
        self.i += 1
        then_steps = self.parse_steps(indent)
        else_if = []
        else_steps = []
        while self.i < len(self.lines) and self.lines[self.i][1] == indent:
            line = self.lines[self.i][2]
            if line.startswith("ELSE IF "):
                c = self.parse_condition(line[8:].strip())
                self.i += 1
                else_if.append((c, self.parse_steps(indent)))
            elif line == "ELSE":
                self.i += 1
                else_steps = self.parse_steps(indent)
                break
            else:
                break
        return IfStep(condition, then_steps, else_if, else_steps)

    def parse_condition(self, text):
        m = re.match(r"(.+?)\s*(>=|<=|==|!=|>|<)\s*(.+)$", text)
        if not m:
            self.error(f"Invalid condition: {text}")
        return Condition(m.group(1).strip(), m.group(2), self.parse_value(m.group(3).strip()))

    def parse_value(self, value):
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            return value[1:-1]
        upper = value.upper()
        if upper == "TRUE":
            return True
        if upper == "FALSE":
            return False
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value


def parse(text):
    return Parser(text).parse()
