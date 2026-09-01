import { renderPalette } from "./palette.js";
import { bindCanvas, renderCanvas } from "./canvas.js";
import { generatePpl, appName } from "./codegen.js";
import { parsePpl } from "./parse.js";
import { compileProgram, fallbackGraph } from "./compile.js";
import { renderGraph } from "./graph.js";
import { validate } from "./validate.js";
import { helloWorldDocument } from "./model.js";
import { loadExampleSource } from "./templates.js";
import { formatResult, runProgram } from "./run.js";
import { renderTrace } from "./results.js";
import { initAssistant } from "./assistant.js";

const STORAGE_KEY = "ppl-editor-v1";
const INPUT_KEY = "ppl-editor-input-v1";

const els = {
  palette: document.getElementById("palette"),
  canvas: document.getElementById("canvas"),
  source: document.getElementById("source"),
  graph: document.getElementById("graph"),
  graphMeta: document.getElementById("graph-meta"),
  status: document.getElementById("status"),
  issues: document.getElementById("issues"),
  openFile: document.getElementById("open-file"),
  example: document.getElementById("example-select"),
  runInput: document.getElementById("run-input"),
  runResult: document.getElementById("run-result"),
  runTrace: document.getElementById("run-trace"),
  runActions: document.getElementById("run-actions"),
  runHuman: document.getElementById("run-human"),
  assistant: document.getElementById("assistant"),
};

let program = loadStored() || helloWorldDocument();
let compileTimer = 0;
let lastDefaultInput = null;
let inputDirty = Boolean(loadInputText());
let lastExecutionId = null;
let lastWaitOptions = [];

function loadStored() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const doc = JSON.parse(raw);
    if (doc?.kind === "program" && Array.isArray(doc.children)) return doc;
  } catch {
    return null;
  }
  return null;
}

function loadInputText() {
  try {
    return localStorage.getItem(INPUT_KEY) || "";
  } catch {
    return "";
  }
}

function persist() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(program));
  } catch {
    // quota / private mode
  }
}

function persistInput() {
  try {
    localStorage.setItem(INPUT_KEY, els.runInput.value);
  } catch {
    // quota / private mode
  }
}

function setStatus(text, level = "") {
  els.status.textContent = text;
  els.status.className = "status" + (level ? ` ${level}` : "");
}

function showIssues(issues) {
  if (!issues.length) {
    els.issues.hidden = true;
    els.issues.innerHTML = "";
    return;
  }
  els.issues.hidden = false;
  els.issues.innerHTML = `<strong>Validation</strong><ul>${issues
    .map((issue) => `<li>${issue.level}: ${escapeHtml(issue.message)}</li>`)
    .join("")}</ul>`;
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function refreshCanvas() {
  renderCanvas(els.canvas, program);
}

function maybeFillDefaultInput(defaultInput) {
  lastDefaultInput = defaultInput;
  if (inputDirty || !defaultInput) return;
  els.runInput.value = JSON.stringify(defaultInput, null, 2);
  persistInput();
}

async function refreshSourceAndGraph() {
  persist();
  const source = generatePpl(program);
  els.source.textContent = source || "// empty program";
  const issues = validate(program);
  showIssues(issues);
  const errors = issues.filter((issue) => issue.level === "error");
  if (errors.length) setStatus(errors[0].message, "err");
  else if (issues.length) setStatus(issues[0].message, "warn");
  else setStatus("Program looks complete", "ok");
  scheduleCompile(source);
}

function scheduleCompile(source) {
  clearTimeout(compileTimer);
  compileTimer = setTimeout(() => updateGraph(source), 280);
}

async function updateGraph(source) {
  const compiled = await compileProgram(source);
  if (compiled) {
    maybeFillDefaultInput(compiled.default_input);
    els.graphMeta.textContent = compiled.fromCompiler
      ? compiled.ok
        ? `Compiled ${compiled.application || ""}`
        : "Compiler error"
      : "";
    renderGraph(els.graph, compiled.graph, compiled.error);
    if (compiled.error) setStatus(compiled.error, "err");
    else if (compiled.ok) setStatus(`Compiled ${compiled.application || "program"}`, "ok");
    return;
  }
  els.graphMeta.textContent = "Start python editor/serve.py to compile, run, and preview graphs";
  renderGraph(els.graph, fallbackGraph(program), null);
}

function loadDocument(next) {
  program = next;
  inputDirty = false;
  lastExecutionId = null;
  lastWaitOptions = [];
  hideHumanActions();
  persist();
  refreshCanvas();
  refreshSourceAndGraph();
}

function download() {
  const source = generatePpl(program);
  const blob = new Blob([source], { type: "text/plain;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `${appName(program)}.ppl`;
  link.click();
  URL.revokeObjectURL(link.href);
}

async function openText(text) {
  loadDocument(parsePpl(text));
}

function parseRunInput() {
  const raw = els.runInput.value.trim();
  if (!raw) return {};
  return JSON.parse(raw);
}

function hideHumanActions() {
  els.runActions.hidden = true;
  els.runHuman.innerHTML = "";
}

function showHumanActions(options) {
  els.runActions.hidden = false;
  els.runHuman.innerHTML = "";
  for (const option of options) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = option;
    button.addEventListener("click", () => executeRun({ humanDecision: option }));
    els.runHuman.appendChild(button);
  }
}

async function executeRun(options = {}) {
  const source = generatePpl(program);
  hideHumanActions();
  els.runResult.textContent = "Running…";
  renderTrace(els.runTrace, [], [], false, null);

  let input;
  try {
    input = parseRunInput();
  } catch (err) {
    setStatus(`Invalid input JSON: ${err.message}`, "err");
    els.runResult.textContent = `Invalid input JSON: ${err.message}`;
    return;
  }

  const run = await runProgram(source, {
    input,
    executionId: options.executionId || lastExecutionId,
    humanDecision: options.humanDecision,
  });

  if (!run.fromServer) {
    setStatus("Run requires python editor/serve.py", "err");
    els.runResult.textContent = run.error || "Server unavailable";
    return;
  }

  if (!run.ok) {
    setStatus(run.error || "Run failed", "err");
    els.runResult.textContent = run.error || "Run failed";
    renderTrace(els.runTrace, run.trace || [], run.node_status || [], false, null);
    return;
  }

  lastExecutionId = run.execution_id || null;
  els.runResult.textContent = formatResult(run.result);

  if (run.waiting) {
    setStatus(`Waiting — ${run.wait?.reason || "paused"}`, "warn");
    lastWaitOptions = run.wait?.options || [];
    if (lastWaitOptions.length) showHumanActions(lastWaitOptions);
    renderTrace(els.runTrace, run.trace || [], run.node_status || [], true, run.wait);
    return;
  }

  lastWaitOptions = [];
  lastExecutionId = null;
  const label = typeof run.result === "string" ? run.result : JSON.stringify(run.result);
  setStatus(`Finished — ${label}`, "ok");
  renderTrace(els.runTrace, run.trace || [], run.node_status || [], false, null);
}

document.getElementById("btn-new").addEventListener("click", () => {
  if (!confirm("Replace the current program with hello world?")) return;
  loadDocument(helloWorldDocument());
});

document.getElementById("btn-open").addEventListener("click", () => els.openFile.click());
els.openFile.addEventListener("change", async () => {
  const file = els.openFile.files?.[0];
  els.openFile.value = "";
  if (!file) return;
  try {
    await openText(await file.text());
  } catch (err) {
    setStatus(String(err.message || err), "err");
  }
});

document.getElementById("btn-download").addEventListener("click", download);

document.getElementById("btn-validate").addEventListener("click", async () => {
  const source = generatePpl(program);
  const compiled = await compileProgram(source);
  if (!compiled) {
    const issues = validate(program);
    setStatus(issues[0]?.message || "No compiler (run python editor/serve.py)", issues.length ? "warn" : "ok");
    return;
  }
  if (compiled.ok) setStatus(`Valid — ${compiled.application}`, "ok");
  else setStatus(compiled.error || "Invalid", "err");
  renderGraph(els.graph, compiled.graph, compiled.error);
});

document.getElementById("btn-run").addEventListener("click", () => executeRun());

els.runInput.addEventListener("input", () => {
  inputDirty = true;
  persistInput();
});

els.example.addEventListener("change", async () => {
  const name = els.example.value;
  els.example.value = "";
  if (!name) return;
  try {
    await openText(await loadExampleSource(name));
  } catch (err) {
    setStatus(String(err.message || err), "err");
  }
});

if (loadInputText()) {
  els.runInput.value = loadInputText();
}

renderPalette(els.palette);
bindCanvas(els.canvas, () => program, {
  onEdit: refreshSourceAndGraph,
  onStructure: () => {
    refreshCanvas();
    refreshSourceAndGraph();
  },
});
initAssistant(els.assistant, {
  getSource: () => generatePpl(program),
  applySource: (text) => openText(text),
  onStatus: setStatus,
});

refreshCanvas();
refreshSourceAndGraph();
