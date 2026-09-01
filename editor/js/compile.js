function add(nodes, operation, name, deps) {
  const id = `${String(nodes.length + 1).padStart(2, "0")}_${operation.toLowerCase()}`;
  nodes.push({
    id,
    operation,
    name: name || operation,
    dependencies: [...deps],
    metadata: {},
  });
  return [id];
}

function stepName(step) {
  if (step.kind === "return") return String(step.value ?? "RETURN");
  if (step.kind === "if") return "IF";
  if (step.kind === "call") return step.target || "CALL";
  if (step.kind === "human_approval") return "HUMAN_APPROVAL";
  return step.name || step.condition || step.kind.toUpperCase();
}

function stepOp(step) {
  if (step.kind === "human_approval") return "HUMAN_APPROVAL";
  return step.kind.toUpperCase();
}

function walk(steps, deps, nodes) {
  let current = [...deps];
  for (const step of steps || []) {
    if (step.kind === "parallel") {
      const ends = [];
      for (const child of step.children || []) ends.push(...walk([child], current, nodes));
      current = add(nodes, "JOIN", "JOIN", ends.length ? ends : current);
    } else if (step.kind === "if") {
      const gate = add(nodes, "IF", "IF", current);
      const ends = [];
      ends.push(...walk(step.children, gate, nodes));
      for (const branch of step.elseIf || []) ends.push(...walk(branch.children, gate, nodes));
      ends.push(...walk(step.elseChildren, gate, nodes));
      current = add(nodes, "JOIN", "JOIN", ends.length ? ends : gate);
    } else {
      current = add(nodes, stepOp(step), stepName(step), current);
    }
  }
  return current;
}

export function fallbackGraph(program) {
  const nodes = [];
  for (const child of program.children || []) {
    if (child.kind === "workflow") walk(child.children, [], nodes);
  }
  return { nodes, version: "0.9" };
}

export async function compileProgram(source) {
  try {
    const response = await fetch("/api/compile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source }),
    });
    if (response.ok) {
      const data = await response.json();
      if (data && typeof data === "object" && ("ok" in data || data.graph)) {
        return {
          ok: Boolean(data.ok),
          fromCompiler: true,
          application: data.application || null,
          graph: data.graph || { nodes: [] },
          default_input: data.default_input || null,
          inputs: data.inputs || [],
          error: data.error || null,
        };
      }
    }
  } catch {
    // file:// or missing server — use the client-side walk
  }
  return null;
}
