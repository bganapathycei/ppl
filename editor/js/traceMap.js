import { walk } from "./model.js";

/** Map runtime trace steps to AST node ids for canvas highlighting. */
export function mapTraceToAstIds(program, trace) {
  const receives = new Map();
  const runs = new Map();

  walk(program, (node) => {
    if (node.kind === "receive" && node.name) receives.set(node.name, node.id);
    if (node.kind === "run" && node.name) runs.set(node.name, node.id);
  });

  const executed = [];
  for (const item of trace || []) {
    const step = String(item.step || "").trim();
    if (step.startsWith("RECEIVE ")) {
      const id = receives.get(step.slice(8).trim());
      if (id) executed.push(id);
    } else if (step.startsWith("RUN ")) {
      const id = runs.get(step.slice(4).trim());
      if (id) executed.push(id);
    }
  }

  return {
    executedIds: new Set(executed),
    lastExecutedId: executed.length ? executed[executed.length - 1] : null,
  };
}
