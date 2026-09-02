import { walk } from "./model.js";

export function validate(program) {
  const issues = [];
  const children = program.children || [];
  const apps = children.filter((child) => child.kind === "app");
  if (!apps.length) issues.push({ level: "error", message: "Program must define APP" });
  if (apps.length > 1) issues.push({ level: "error", message: "Only one APP is allowed" });

  const inputs = new Set(children.filter((child) => child.kind === "input").map((child) => child.name));
  const agents = new Set(children.filter((child) => child.kind === "agent").map((child) => child.name));
  const workflows = children.filter((child) => child.kind === "workflow");
  if (!workflows.length) issues.push({ level: "warning", message: "No WORKFLOW defined" });

  function checkSteps(steps, where) {
    for (const step of steps || []) {
      if (step.kind === "run" && step.name && !agents.has(step.name)) {
        issues.push({
          level: "error",
          message: `${where}: RUN ${step.name} — unknown agent`,
          nodeId: step.id,
        });
      }
      if (step.kind === "receive" && step.name && !inputs.has(step.name)) {
        issues.push({
          level: "warning",
          message: `${where}: RECEIVE ${step.name} — unknown input`,
          nodeId: step.id,
        });
      }
      if (step.kind === "if") {
        checkSteps(step.children, where);
        for (const branch of step.elseIf || []) checkSteps(branch.children, where);
        checkSteps(step.elseChildren, where);
      }
      if (step.kind === "parallel") checkSteps(step.children, where);
    }
  }

  for (const workflow of workflows) {
    if (!(workflow.children || []).length) {
      issues.push({
        level: "warning",
        message: `WORKFLOW ${workflow.name} is empty`,
        nodeId: workflow.id,
      });
    }
    checkSteps(workflow.children, `WORKFLOW ${workflow.name}`);
  }
  return issues;
}

/** Group validation issues by AST node id for canvas badges. */
export function issuesByNodeId(program) {
  const map = new Map();
  for (const issue of validate(program)) {
    if (!issue.nodeId) continue;
    const list = map.get(issue.nodeId) || [];
    list.push(issue);
    map.set(issue.nodeId, list);
  }
  return map;
}
