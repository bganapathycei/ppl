import { useCallback, useEffect, useMemo, useReducer, useRef, useState } from "react";

import {

  ReactFlow,

  ReactFlowProvider,

  Background,

  Controls,

  MiniMap,

  MarkerType,

  useNodesState,

  useEdgesState,

  useReactFlow,

} from "@xyflow/react";

import "@xyflow/react/dist/style.css";



import { nodeTypes } from "./nodes.jsx";

import { buildFlow } from "./astToFlow.js";

import Palette from "./Palette.jsx";

import PropertiesPanel from "./PropertiesPanel.jsx";

import { generatePpl } from "../../js/codegen.js";

import { parsePpl } from "../../js/parse.js";

import { helloWorldDocument, createNode, getNode, getSlot, insertNode, removeNode, setProp } from "../../js/model.js";

import { insertPaletteBlock } from "../../js/paletteInsert.js";

import { WORKFLOW_STEPS, BLOCKS } from "../../js/schema.js";

import { validate } from "../../js/validate.js";

import { mapTraceToAstIds } from "../../js/traceMap.js";
import { refLinkedIds } from "../../js/refLinks.js";

const EXAMPLES = ["hello_world", "incident", "governed_change", "enterprise_automation"];

const EDGE_DEFAULTS = {
  markerEnd: { type: MarkerType.ArrowClosed, color: "#5b6378", width: 18, height: 18 },
  style: { stroke: "#5b6378", strokeWidth: 1.6 },
};

function Editor() {
  const programRef = useRef(helloWorldDocument());

  const [version, bump] = useReducer((x) => x + 1, 0);

  const [selectedId, setSelectedId] = useState(null);

  const [nodes, setNodes, onNodesChange] = useNodesState([]);

  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const [status, setStatus] = useState("Ready");

  const [statusLevel, setStatusLevel] = useState("");

  const [paletteMsg, setPaletteMsg] = useState("");

  const [result, setResult] = useState("Run the program to see output here.");

  const [trace, setTrace] = useState([]);

  const [traceState, setTraceState] = useState({ executedIds: new Set(), lastExecutedId: null });

  const [inputText, setInputText] = useState("");

  const [addKind, setAddKind] = useState("run");

  const [showSource, setShowSource] = useState(false);

  const [collapsed, setCollapsed] = useState({ declarations: false, workflows: false });

  const [hoverAstId, setHoverAstId] = useState(null);

  const inputDirty = useRef(false);

  const rf = useReactFlow();



  const source = useMemo(() => generatePpl(programRef.current), [version]);

  const issues = useMemo(() => validate(programRef.current), [version]);

  const issuesByNode = useMemo(() => {

    const map = new Map();

    for (const issue of issues) {

      if (!issue.nodeId) continue;

      const list = map.get(issue.nodeId) || [];

      list.push(issue);

      map.set(issue.nodeId, list);

    }

    return map;

  }, [issues]);



  const handleRename = useCallback((astId, name) => {

    const node = getNode(programRef.current, astId);

    if (!node || !name) return;

    setProp(node, "name", name);

    bump();

  }, []);



  // Rebuild the flow graph whenever the document structure/props change.

  useEffect(() => {

    const refLinked = refLinkedIds(programRef.current, hoverAstId);

    const flow = buildFlow(programRef.current, {

      collapsed,

      issuesByNode,

      traceState,

      hoverAstId,

      refLinked,

    });



    for (const node of flow.nodes) {

      node.selected = node.data.astId === selectedId;

      if (node.data.astId) {

        node.data.onRename = (name) => handleRename(node.data.astId, name);

      }

      if (node.type === "appContainer") {

        node.data.onToggleDecl = () => setCollapsed((c) => ({ ...c, declarations: !c.declarations }));

        node.data.onToggleWf = () => setCollapsed((c) => ({ ...c, workflows: !c.workflows }));

      }

    }



    for (const edge of flow.edges) {

      edge.className = `edge-${edge.data?.kind || "flow"}`;

      if (edge.data?.kind === "branch") edge.labelBgPadding = [5, 2];

      if (edge.data?.kind === "ref") {

        const sourceNode = flow.nodes.find((n) => n.id === edge.source);

        const targetNode = flow.nodes.find((n) => n.id === edge.target);

        const active =

          hoverAstId &&

          (refLinked.has(sourceNode?.data.astId) || refLinked.has(targetNode?.data.astId));

        edge.style = {

          stroke: active ? "#8d93a6" : "#5b6378",

          strokeDasharray: "6 4",

          opacity: active ? 1 : 0.75,

          strokeWidth: active ? 2.4 : 1.6,

        };

        edge.markerEnd = undefined;

        edge.className = active ? "edge-ref edge-ref-active" : "edge-ref";

      }

    }



    setNodes(flow.nodes);

    setEdges(flow.edges);

    // eslint-disable-next-line react-hooks/exhaustive-deps

  }, [version, collapsed, issuesByNode, traceState, hoverAstId, selectedId, handleRename]);



  // Reflect selection highlight without a full relayout when only selection changes.

  useEffect(() => {

    setNodes((cur) => cur.map((n) => ({ ...n, selected: n.data.astId === selectedId })));

    // eslint-disable-next-line react-hooks/exhaustive-deps

  }, [selectedId]);



  useEffect(() => {

    const errors = issues.filter((i) => i.level === "error");

    if (errors.length) setStatusMsg(errors[0].message, "err");

    else if (issues.length) setStatusMsg(issues[0].message, "warn");

    else setStatusMsg("Program looks complete", "ok");

  }, [issues]);



  const refit = useCallback(() => {

    requestAnimationFrame(() => rf.fitView({ padding: 0.15, duration: 250 }));

  }, [rf]);



  const setStatusMsg = useCallback((text, level = "") => {

    setStatus(text);

    setStatusLevel(level);

  }, []);



  useEffect(() => {

    let cancelled = false;

    (async () => {

      try {

        const res = await fetch("/api/compile", {

          method: "POST",

          headers: { "Content-Type": "application/json" },

          body: JSON.stringify({ source }),

        });

        const data = await res.json();

        if (cancelled) return;

        if (data.ok && !issues.some((i) => i.level === "error")) {

          setStatusMsg(`Compiled ${data.application || "program"}`, "ok");

        } else if (data.error) setStatusMsg(data.error, "err");

        if (!inputDirty.current && data.default_input) {

          setInputText(JSON.stringify(data.default_input, null, 2));

        }

      } catch {

        /* server not running; canvas still works */

      }

    })();

    return () => {

      cancelled = true;

    };

  }, [source, issues, setStatusMsg]);



  const loadDocument = useCallback(

    (doc) => {

      programRef.current = doc;

      setSelectedId(null);

      setTrace([]);

      setTraceState({ executedIds: new Set(), lastExecutedId: null });

      inputDirty.current = false;

      setResult("Run the program to see output here.");

      bump();

      refit();

    },

    [refit],

  );



  const loadExample = useCallback(

    async (name) => {

      if (!name) return;

      try {

        const res = await fetch(`/templates/${name}.ppl`);

        loadDocument(parsePpl(await res.text()));

      } catch (err) {

        setStatusMsg(`Could not load ${name}: ${err.message}`, "err");

      }

    },

    [loadDocument, setStatusMsg],

  );



  const onNodeClick = useCallback((_e, node) => {

    setSelectedId(node.data?.astId || null);

  }, []);



  const onNodeMouseEnter = useCallback((_e, node) => {

    if (node.data?.astId) setHoverAstId(node.data.astId);

  }, []);



  const onNodeMouseLeave = useCallback(() => {

    setHoverAstId(null);

  }, []);



  const addFromPalette = useCallback(

    (kind) => {

      const node = insertPaletteBlock(programRef.current, kind, selectedId);

      if (!node) {

        setPaletteMsg(`Can't add ${BLOCKS[kind]?.keyword || kind} here.`);

        return null;

      }

      setPaletteMsg("");

      setSelectedId(node.id);

      bump();

      refit();

      return node;

    },

    [selectedId, refit],

  );



  const addStep = useCallback(() => {

    const wf = (programRef.current.children || []).find((c) => c.kind === "workflow");

    if (!wf) {

      setStatusMsg("Add a WORKFLOW first.", "warn");

      return;

    }

    const list = getSlot(wf, "children") || [];

    const node = createNode(addKind);

    insertNode(wf, "children", list.length, node);

    setSelectedId(node.id);

    bump();

    refit();

  }, [addKind, refit, setStatusMsg]);



  const onDelete = useCallback(

    (id) => {

      removeNode(programRef.current, id);

      if (selectedId === id) setSelectedId(null);

      bump();

    },

    [selectedId],

  );



  const run = useCallback(

    async (humanDecision) => {

      setResult("Running…");

      setTrace([]);

      setTraceState({ executedIds: new Set(), lastExecutedId: null });

      let input;

      try {

        input = inputText.trim() ? JSON.parse(inputText) : {};

      } catch (err) {

        setStatusMsg(`Invalid input JSON: ${err.message}`, "err");

        setResult(`Invalid input JSON: ${err.message}`);

        return;

      }

      try {

        const res = await fetch("/api/run", {

          method: "POST",

          headers: { "Content-Type": "application/json" },

          body: JSON.stringify({ source, input, trace: true, human_decision: humanDecision }),

        });

        const data = await res.json();

        if (!data.ok) {

          setStatusMsg(data.error || "Run failed", "err");

          setResult(data.error || "Run failed");

          setTrace(data.trace || []);

          setTraceState(mapTraceToAstIds(programRef.current, data.trace || []));

          return;

        }

        setResult(typeof data.result === "string" ? JSON.stringify(data.result) : JSON.stringify(data.result, null, 2));

        setTrace(data.trace || []);

        setTraceState(mapTraceToAstIds(programRef.current, data.trace || []));

        if (data.waiting) setStatusMsg(`Waiting — ${data.wait?.reason || "paused"}`, "warn");

        else setStatusMsg(`Finished — ${typeof data.result === "string" ? data.result : "done"}`, "ok");

      } catch (err) {

        setStatusMsg(`Run requires the server: ${err.message}`, "err");

        setResult("Start the PPL server (python editor/serve.py) to run programs.");

      }

    },

    [inputText, source, setStatusMsg],

  );



  const stepKinds = WORKFLOW_STEPS.filter((k) => BLOCKS[k]);



  return (

    <div className="app">

      <header className="topbar">

        <div className="brand">

          <span className="brand-mark">PPL</span>

          <span className="brand-name">Flow Editor</span>

          <span className="brand-tag">React Flow</span>

        </div>

        <label className="tb-select">

          Example

          <select defaultValue="" onChange={(e) => loadExample(e.target.value)}>

            <option value="">Load…</option>

            {EXAMPLES.map((name) => (

              <option key={name} value={name}>

                {name}

              </option>

            ))}

          </select>

        </label>

        <label className="tb-select">

          Add step

          <select value={addKind} onChange={(e) => setAddKind(e.target.value)}>

            {stepKinds.map((k) => (

              <option key={k} value={k}>

                {BLOCKS[k].keyword}

              </option>

            ))}

          </select>

        </label>

        <button type="button" onClick={addStep}>

          Add step

        </button>

        <button type="button" onClick={() => setShowSource((s) => !s)}>

          {showSource ? "Hide source" : "Source"}

        </button>

        <button type="button" className="primary" onClick={() => run()}>

          Run

        </button>

        <span className={`status ${statusLevel}`}>{status}</span>

      </header>



      <div className="workspace workspace-palette">

        <Palette onAdd={addFromPalette} statusMsg={paletteMsg} />



        <div className="canvas">

          <ReactFlow

            nodes={nodes}

            edges={edges}

            onNodesChange={onNodesChange}

            onEdgesChange={onEdgesChange}

            nodeTypes={nodeTypes}

            defaultEdgeOptions={EDGE_DEFAULTS}

            onNodeClick={onNodeClick}

            onNodeMouseEnter={onNodeMouseEnter}

            onNodeMouseLeave={onNodeMouseLeave}

            onPaneClick={() => setSelectedId(null)}

            fitView

            minZoom={0.2}

            maxZoom={2.2}

            proOptions={{ hideAttribution: true }}

          >

            <Background color="#252a38" gap={18} />

            <Controls />

            <MiniMap pannable zoomable className="mini" nodeColor={() => "#2a2f3e"} />

          </ReactFlow>

          {showSource ? (

            <pre className="source-overlay">{source || "// empty program"}</pre>

          ) : null}

        </div>



        <aside className="sidebar">

          <section className="pane">

            <h2>Properties</h2>

            <PropertiesPanel

              program={programRef.current}

              selectedId={selectedId}

              issues={issues}

              onEdit={bump}

              onStructure={() => {

                bump();

              }}

              onDelete={onDelete}

            />

          </section>

          <section className="pane run-pane">

            <h2>Run</h2>

            <label className="run-label">Input JSON</label>

            <textarea

              className="run-input"

              value={inputText}

              spellCheck={false}

              onChange={(e) => {

                inputDirty.current = true;

                setInputText(e.target.value);

              }}

            />

            <h3>Result</h3>

            <pre className="run-result">{result}</pre>

            {trace.length ? (

              <>

                <h3>Trace</h3>

                <ul className="trace">

                  {trace.map((t, i) => (

                    <li key={i}>

                      <span className={`t-${(t.type || "d").toLowerCase()}`}>{t.type || "D"}</span> {t.step}

                    </li>

                  ))}

                </ul>

              </>

            ) : null}

          </section>

        </aside>

      </div>

    </div>

  );

}



export default function App() {

  return (

    <ReactFlowProvider>

      <Editor />

    </ReactFlowProvider>

  );

}


