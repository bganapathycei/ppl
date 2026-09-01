# PPL Flow Editor (React Flow)

A polished node-canvas editor for PPL programs, built with [React Flow](https://reactflow.dev/)
(`@xyflow/react`) and [dagre](https://github.com/dagrejs/dagre) auto-layout. It is an
alternative front end to the classic editor in [`../`](../) and talks to the same
`serve.py` HTTP API (`/api/compile`, `/api/run`, `/templates/*`).

The PPL document (AST) stays the single source of truth. This app reuses the shared,
framework-free modules in [`../js/`](../js/) (`parse.js`, `codegen.js`, `model.js`,
`schema.js`, `flow_layout.js`) so `.ppl` generation and round-tripping stay identical to
the classic editor; the canvas is a control-flow projection:

- workflow steps chain top-to-bottom;
- `IF` / `PARALLEL` fan out into labeled branches that merge (`RETURN` paths terminate and
  do not merge onward);
- declarations and agents are placed as reference cards in a left column;
- selecting a node opens a schema-driven **Properties** panel that edits the AST.

## Develop

Requires Node.js 18+. Start the Python API first (from the repo root):

```bash
python editor/serve.py           # API + classic editor on :8765
```

Then run the Vite dev server (proxies `/api` and `/templates` to `:8765`):

```bash
npm --prefix editor/react install
npm --prefix editor/react run dev      # http://127.0.0.1:5173/flow/
```

## Build (served by the Python server)

```bash
npm --prefix editor/react install
npm --prefix editor/react run build
```

This emits `editor/react/dist/`, which `serve.py` serves at
[http://127.0.0.1:8765/flow/](http://127.0.0.1:8765/flow/). Until it is built, that route
shows build instructions; the classic editor at `/` always works.

## Test

```bash
npm --prefix editor/react test    # graph-builder assertions (astToFlow)
```

## Layout

```text
editor/react/
├── index.html            # Vite entry
├── vite.config.js        # base "/flow/", dev proxy to :8765
├── src/
│   ├── main.jsx
│   ├── App.jsx           # toolbar, canvas, properties, run
│   ├── astToFlow.js      # AST → React Flow nodes/edges + dagre layout
│   ├── nodes.jsx         # custom PPL node (color-coded by execution class)
│   ├── PropertiesPanel.jsx
│   └── styles.css
└── tests/ast_to_flow.test.mjs
```
