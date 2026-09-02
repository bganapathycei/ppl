import { createNode, emptyProgram } from "./model.js";

function cleanLines(text) {
  const lines = [];
  for (const [i, rawLine] of text.split(/\r?\n/).entries()) {
    const stripped = rawLine.split("#", 1)[0].replace(/\s+$/, "");
    if (!stripped.trim()) continue;
    const indent = stripped.length - stripped.trimStart().length;
    lines.push({ number: i + 1, indent, line: stripped.trim() });
  }
  return lines;
}

class Parser {
  constructor(text) {
    this.lines = cleanLines(text);
    this.i = 0;
  }

  error(msg) {
    const n = this.i < this.lines.length ? this.lines[this.i].number : "EOF";
    throw new SyntaxError(`Line ${n}: ${msg}`);
  }

  peek() {
    return this.i < this.lines.length ? this.lines[this.i] : null;
  }

  parse() {
    const program = emptyProgram();
    while (this.peek()) {
      const { indent, line } = this.peek();
      if (indent !== 0) this.error("Top-level declaration must not be indented");
      if (line.startsWith("APP ")) {
        program.children.push(createNode("app", { name: line.slice(4).trim() }));
        this.i += 1;
      } else if (line.startsWith("IMPORT ")) {
        program.children.push(createNode("import", { module: line.slice(7).trim() }));
        this.i += 1;
      } else if (line.startsWith("PROMPT ")) program.children.push(this.parsePrompt());
      else if (line.startsWith("INPUT ")) program.children.push(this.parseInput());
      else if (line.startsWith("MODEL_POLICY ")) program.children.push(this.parsePolicy());
      else if (line.startsWith("GUARD ")) program.children.push(this.parseGuard());
      else if (line.startsWith("AUTHORIZATION ")) program.children.push(this.parseAuthorization());
      else if (line === "BUDGET" || line.startsWith("BUDGET ")) program.children.push(this.parseBudget());
      else if (line.startsWith("ENVIRONMENT ")) program.children.push(this.parseEnvironment());
      else if (line.startsWith("KNOWLEDGE ")) program.children.push(this.parseKnowledge());
      else if (line.startsWith("MEMORY ")) program.children.push(this.parseMemory());
      else if (line.startsWith("TOOL ")) program.children.push(this.parseTool());
      else if (line.startsWith("AGENT ")) program.children.push(this.parseAgent());
      else if (line.startsWith("WORKFLOW ")) program.children.push(this.parseWorkflow());
      else this.error(`Unexpected line: ${line}`);
    }
    return program;
  }

  parsePrompt() {
    const parent = this.peek().indent;
    const name = this.peek().line.slice("PROMPT ".length).trim();
    this.i += 1;
    const children = [];
    while (this.peek() && this.peek().indent > parent) {
      children.push(createNode("rule", { text: this.peek().line }));
      this.i += 1;
    }
    return createNode("prompt", { name, children });
  }

  parseInput() {
    const parent = this.peek().indent;
    const name = this.peek().line.slice(6).trim();
    this.i += 1;
    const children = [];
    while (this.peek() && this.peek().indent > parent) {
      const line = this.peek().line;
      if (!line.includes(":")) this.error(`Expected field declaration, got: ${line}`);
      const [n, t] = splitOnce(line, ":");
      children.push(createNode("field", { name: n, type: t }));
      this.i += 1;
    }
    return createNode("input", { name, children });
  }

  parsePolicy() {
    const parent = this.peek().indent;
    const name = this.peek().line.slice("MODEL_POLICY ".length).trim();
    this.i += 1;
    const vals = {};
    while (this.peek() && this.peek().indent > parent) {
      const line = this.peek().line;
      if (line.includes(":")) {
        const [k, v] = splitOnce(line, ":");
        vals[k.toLowerCase()] = v;
      }
      this.i += 1;
    }
    return createNode("model_policy", {
      name,
      reasoning: vals.reasoning || "reasoning-default",
      classification: vals.classification || "classification-default",
      extraction: vals.extraction || "extraction-default",
      max_retries: vals.max_retries || "1",
      fallback: vals.fallback || "fallback-default",
    });
  }

  parseGuard() {
    const parent = this.peek().indent;
    const name = this.peek().line.slice("GUARD ".length).trim();
    this.i += 1;
    const children = [];
    while (this.peek() && this.peek().indent > parent) {
      children.push(createNode("rule", { text: this.peek().line }));
      this.i += 1;
    }
    return createNode("guard", { name, children });
  }

  parseAuthorization() {
    const parent = this.peek().indent;
    const name = this.peek().line.slice("AUTHORIZATION ".length).trim();
    this.i += 1;
    let requires = "";
    while (this.peek() && this.peek().indent > parent) {
      const line = this.peek().line;
      if (line.toUpperCase().startsWith("REQUIRES ")) requires = line.slice(9).trim();
      this.i += 1;
    }
    return createNode("authorization", { name, requires });
  }

  parseBudget() {
    const parent = this.peek().indent;
    this.i += 1;
    const vals = {};
    while (this.peek() && this.peek().indent > parent) {
      const line = this.peek().line;
      if (line.includes(":")) {
        const [k, v] = splitOnce(line, ":");
        vals[k.toLowerCase()] = v;
      }
      this.i += 1;
    }
    return createNode("budget", {
      max_cost: vals.max_cost || "",
      max_latency: vals.max_latency || "",
      max_steps: vals.max_steps || "",
    });
  }

  parseEnvironment() {
    const parent = this.peek().indent;
    const name = this.peek().line.slice("ENVIRONMENT ".length).trim();
    this.i += 1;
    const children = [];
    while (this.peek() && this.peek().indent > parent) {
      children.push(createNode("rule", { text: this.peek().line }));
      this.i += 1;
    }
    return createNode("environment", { name, children });
  }

  parseKnowledge() {
    const parent = this.peek().indent;
    const name = this.peek().line.slice("KNOWLEDGE ".length).trim();
    this.i += 1;
    const children = [];
    while (this.peek() && this.peek().indent > parent) {
      const line = this.peek().line;
      if (line.toUpperCase().startsWith("SOURCE ")) {
        children.push(createNode("source", { name: line.slice(7).trim() }));
      }
      this.i += 1;
    }
    return createNode("knowledge", { name, children });
  }

  parseMemory() {
    const parent = this.peek().indent;
    const name = this.peek().line.slice("MEMORY ".length).trim();
    this.i += 1;
    let key = "";
    const children = [];
    while (this.peek() && this.peek().indent > parent) {
      const line = this.peek().line;
      if (line.toUpperCase().startsWith("KEY ")) key = line.slice(4).trim();
      else children.push(createNode("memory_clause", { text: line }));
      this.i += 1;
    }
    return createNode("memory", { name, key, children });
  }

  parseTool() {
    const parent = this.peek().indent;
    const name = this.peek().line.slice("TOOL ".length).trim();
    this.i += 1;
    const children = [];
    while (this.peek() && this.peek().indent > parent) {
      const { indent, line } = this.peek();
      if (line.toUpperCase().startsWith("ACTION ")) {
        children.push(createNode("action", { name: line.slice(7).trim() }));
        this.i += 1;
      } else if (line === "INPUT" || line.startsWith("INPUT ")) {
        this.i += 1;
        const fields = [];
        while (this.peek() && this.peek().indent > indent) {
          const [n, t] = typed(this.peek().line);
          fields.push(createNode("field", { name: n, type: t }));
          this.i += 1;
        }
        children.push(createNode("tool_input", { children: fields }));
      } else if (line === "OUTPUT" || line.startsWith("OUTPUT ")) {
        this.i += 1;
        const fields = [];
        while (this.peek() && this.peek().indent > indent) {
          const [n, t] = typed(this.peek().line);
          fields.push(createNode("field", { name: n, type: t }));
          this.i += 1;
        }
        children.push(createNode("tool_output", { children: fields }));
      } else {
        this.i += 1;
      }
    }
    return createNode("tool", { name, children });
  }

  parseAgent() {
    const parent = this.peek().indent;
    const agent = createNode("agent", { name: this.peek().line.slice(6).trim(), children: [] });
    this.i += 1;
    while (this.peek() && this.peek().indent > parent) {
      const { indent, line } = this.peek();
      if (line.startsWith("INPUT ")) {
        agent.children.push(createNode("agent_input", { name: line.slice(6).trim() }));
        this.i += 1;
      } else if (line.startsWith("POLICY ")) {
        agent.children.push(createNode("policy_ref", { name: line.slice(7).trim() }));
        this.i += 1;
      } else if (line.toUpperCase().startsWith("USE KNOWLEDGE ")) {
        agent.children.push(createNode("use_knowledge", { name: line.slice(14).trim() }));
        this.i += 1;
      } else if (line.toUpperCase().startsWith("USE MEMORY ")) {
        agent.children.push(createNode("use_memory", { name: line.slice(11).trim() }));
        this.i += 1;
      } else if (line.startsWith("CLASSIFY ")) agent.children.push(this.parseClassify(indent));
      else if (line === "EXTRACT") agent.children.push(this.parseExtract(indent));
      else if (line === "REASON") agent.children.push(this.parseReason(indent));
      else if (line === "OUTPUT") agent.children.push(this.parseOutput(indent));
      else this.error(`Unexpected AGENT statement: ${line}`);
    }
    return agent;
  }

  parseClassify(opIndent) {
    let target = this.peek().line.slice(9).trim();
    if (target.endsWith(" AS")) target = target.slice(0, -3).trim();
    this.i += 1;
    const children = [];
    while (this.peek() && this.peek().indent > opIndent) {
      children.push(createNode("category", { name: this.peek().line }));
      this.i += 1;
    }
    return createNode("classify", { target, children });
  }

  parseExtract(opIndent) {
    this.i += 1;
    const children = [];
    while (this.peek() && this.peek().indent > opIndent) {
      const [n, t] = typed(this.peek().line);
      children.push(createNode("field", { name: n, type: t }));
      this.i += 1;
    }
    return createNode("extract", { children });
  }

  parseReason(opIndent) {
    this.i += 1;
    const instructions = [];
    const considers = [];
    const outputFields = [];
    while (this.peek() && this.peek().indent > opIndent) {
      const { indent, line } = this.peek();
      if (line.toLowerCase() === "consider:") {
        this.i += 1;
        while (this.peek() && this.peek().indent > indent) {
          considers.push(createNode("consider", { text: this.peek().line }));
          this.i += 1;
        }
      } else if (line.toLowerCase() === "output:") {
        this.i += 1;
        while (this.peek() && this.peek().indent > indent) {
          const [n, t] = typed(this.peek().line);
          outputFields.push(createNode("field", { name: n, type: t }));
          this.i += 1;
        }
      } else {
        instructions.push(line);
        this.i += 1;
      }
    }
    return createNode("reason", {
      instruction: instructions.join(" ").trim(),
      children: considers,
      outputFields,
    });
  }

  parseOutput(opIndent) {
    this.i += 1;
    const children = [];
    while (this.peek() && this.peek().indent > opIndent) {
      const [n, t] = this.peek().line.includes(":")
        ? typed(this.peek().line)
        : [this.peek().line, ""];
      children.push(createNode("field", { name: n, type: t }));
      this.i += 1;
    }
    return createNode("output", { children });
  }

  parseWorkflow() {
    const parent = this.peek().indent;
    const name = this.peek().line.slice(9).trim();
    this.i += 1;
    return createNode("workflow", { name, children: this.parseSteps(parent) });
  }

  parseSteps(parentIndent) {
    const steps = [];
    while (this.peek() && this.peek().indent > parentIndent) {
      const { indent, line } = this.peek();
      if (line.startsWith("LET ")) {
        const rest = line.slice(4).trim();
        const [name, expr] = splitOnce(rest, "=");
        steps.push(createNode("let", { name: name.trim(), expr: (expr || "").trim() }));
        this.i += 1;
      } else if (line.startsWith("PRINT ")) {
        steps.push(createNode("print", { expr: line.slice(6).trim() }));
        this.i += 1;
      } else if (line.startsWith("READ ")) {
        const m = line.slice(5).trim().match(/^(.+?)\s+INTO\s+(.+)$/i);
        if (!m) this.error(`READ requires path INTO var: ${line}`);
        steps.push(createNode("read", { path: m[1].trim(), var: m[2].trim() }));
        this.i += 1;
      } else if (line.startsWith("WRITE ")) {
        const m = line.slice(6).trim().match(/^(.+?)\s+FROM\s+(.+)$/i);
        if (!m) this.error(`WRITE requires path FROM expr: ${line}`);
        steps.push(createNode("write", { path: m[1].trim(), expr: m[2].trim() }));
        this.i += 1;
      } else if (line.startsWith("FOR ")) {
        const m = line.slice(4).trim().match(/^(.+?)\s+IN\s+(.+?)\s+DO$/i);
        if (!m) this.error(`FOR requires item IN source DO: ${line}`);
        this.i += 1;
        steps.push(createNode("for", { item: m[1].trim(), source: m[2].trim(), children: this.parseSteps(indent) }));
      } else if (line.startsWith("WHILE ")) {
        const rest = line.slice(6).trim();
        if (!rest.toUpperCase().endsWith(" DO")) this.error(`WHILE requires trailing DO: ${line}`);
        this.i += 1;
        steps.push(createNode("while", { condition: rest.slice(0, -2).trim(), children: this.parseSteps(indent) }));
      } else if (line.startsWith("RECEIVE ")) {
        steps.push(createNode("receive", { name: line.slice(8).trim() }));
        this.i += 1;
      } else if (line.startsWith("RUN ")) {
        steps.push(createNode("run", { name: line.slice(4).trim() }));
        this.i += 1;
      } else if (line.startsWith("IF ")) steps.push(this.parseIf(indent));
      else if (line.startsWith("RETURN ")) {
        const raw = line.slice(7).trim();
        const quoted = raw.length >= 2 && raw[0] === raw[raw.length - 1] && (raw[0] === '"' || raw[0] === "'");
        steps.push(createNode("return", { value: quoted ? raw.slice(1, -1) : raw, literal: quoted }));
        this.i += 1;
      } else if (line === "HUMAN_APPROVAL" || line.startsWith("HUMAN_APPROVAL ")) {
        steps.push(this.parseHumanApproval(indent));
      } else if (line === "PARALLEL") steps.push(this.parseParallel(indent));
      else if (line === "JOIN" || line.startsWith("JOIN ")) {
        const names = line.startsWith("JOIN ") ? line.slice(4).trim() : "";
        steps.push(createNode("join", { names }));
        this.i += 1;
      } else if (line === "WAIT" || line.startsWith("WAIT ")) {
        steps.push(createNode("wait", { condition: line.startsWith("WAIT ") ? line.slice(5).trim() : "" }));
        this.i += 1;
      } else if (line === "CHECKPOINT" || line.startsWith("CHECKPOINT ")) {
        steps.push(
          createNode("checkpoint", {
            name: line.startsWith("CHECKPOINT ") ? line.slice(11).trim() : "",
          }),
        );
        this.i += 1;
      } else if (line.startsWith("CALL ")) steps.push(this.parseCall(indent));
      else this.error(`Unexpected WORKFLOW statement: ${line}`);
    }
    return steps;
  }

  parseHumanApproval(indent) {
    this.i += 1;
    let question = "";
    const children = [];
    while (this.peek() && this.peek().indent > indent) {
      const nested = this.peek().indent;
      const line = this.peek().line;
      if (line.toUpperCase().startsWith("QUESTION")) {
        let text = line.includes(":") ? line.split(":").slice(1).join(":").trim() : "";
        this.i += 1;
        const extras = [];
        while (this.peek() && this.peek().indent > nested) {
          extras.push(this.peek().line);
          this.i += 1;
        }
        question = [text, ...extras].filter(Boolean).join(" ");
      } else if (line.toUpperCase().startsWith("OPTIONS")) {
        this.i += 1;
        while (this.peek() && this.peek().indent > nested) {
          children.push(createNode("option", { name: this.peek().line }));
          this.i += 1;
        }
      } else break;
    }
    return createNode("human_approval", { question, children });
  }

  parseParallel(indent) {
    this.i += 1;
    return createNode("parallel", { children: this.parseSteps(indent) });
  }

  parseCall(indent) {
    const target = this.peek().line.slice(5).trim();
    this.i += 1;
    const children = [];
    while (this.peek() && this.peek().indent > indent) {
      const body = this.peek().line;
      if (body.includes("=")) {
        const [name, value] = splitOnce(body, "=");
        children.push(createNode("arg", { name, value }));
      }
      this.i += 1;
    }
    return createNode("call", { target, children });
  }

  parseIf(indent) {
    let line = this.peek().line;
    if (line.startsWith("IF ")) line = line.slice(3).trim();
    const condition = parseCondition(line, (msg) => this.error(msg));
    this.i += 1;
    const node = createNode("if", {
      ...condition,
      children: this.parseSteps(indent),
      elseIf: [],
      elseChildren: [],
    });
    while (this.peek() && this.peek().indent === indent) {
      const next = this.peek().line;
      if (next.startsWith("ELSE IF ")) {
        const cond = parseCondition(next.slice(8).trim(), (msg) => this.error(msg));
        this.i += 1;
        node.elseIf.push(createNode("else_if", { ...cond, children: this.parseSteps(indent) }));
      } else if (next === "ELSE") {
        this.i += 1;
        node.elseChildren = this.parseSteps(indent);
        break;
      } else break;
    }
    return node;
  }
}

function splitOnce(text, sep) {
  const i = text.indexOf(sep);
  return [text.slice(0, i).trim(), text.slice(i + sep.length).trim()];
}

function typed(line) {
  return line.includes(":") ? splitOnce(line, ":") : [line, "TEXT"];
}

function parseCondition(text, error) {
  const m = text.match(/^(.+?)\s*(>=|<=|==|!=|>|<)\s*(.+)$/);
  if (!m) error(`Invalid condition: ${text}`);
  return { left: m[1].trim(), operator: m[2], right: m[3].trim() };
}

export function parsePpl(text) {
  return new Parser(text).parse();
}
