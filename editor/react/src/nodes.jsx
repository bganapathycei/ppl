import { useState, useRef, useEffect } from "react";
import { Handle, Position } from "@xyflow/react";

function InlineRename({ value, onCommit, className, onCancel }) {
  const [draft, setDraft] = useState(value);
  const ref = useRef(null);

  useEffect(() => {
    ref.current?.focus();
    ref.current?.select();
  }, []);

  return (
    <input
      ref={ref}
      className={className}
      value={draft}
      onChange={(e) => setDraft(e.target.value)}
      onBlur={() => onCommit(draft.trim() || value)}
      onKeyDown={(e) => {
        if (e.key === "Enter") onCommit(draft.trim() || value);
        if (e.key === "Escape") onCancel?.();
      }}
      onClick={(e) => e.stopPropagation()}
      onDoubleClick={(e) => e.stopPropagation()}
    />
  );
}

function IssueBadge({ level, tip }) {
  return (
    <span className={`ppl-issue ppl-issue-${level}`} title={tip}>
      !
    </span>
  );
}

// APP container frame — wraps declarations and workflows inside one application boundary.
export function AppContainerNode({ data, selected }) {
  const [editing, setEditing] = useState(false);
  const cls = `app-container${selected ? " selected" : ""}`;

  return (
    <div className={cls} style={{ width: "100%", height: "100%" }}>
      <div className="app-container-header">
        <span className="app-container-kw">APP</span>
        {editing ? (
          <InlineRename
            className="app-container-rename"
            value={data.name || "MyApplication"}
            onCommit={(v) => {
              data.onRename?.(v);
              setEditing(false);
            }}
            onCancel={() => setEditing(false)}
          />
        ) : (
          <span
            className="app-container-name"
            onDoubleClick={(e) => {
              e.stopPropagation();
              if (data.onRename) setEditing(true);
            }}
          >
            {data.name || "MyApplication"}
          </span>
        )}
      </div>
      {data.hasDeclarations ? (
        <button
          type="button"
          className={`app-container-section-toggle${data.declCollapsed ? " collapsed" : ""}`}
          style={{ top: data.declLabelY }}
          onClick={(e) => {
            e.stopPropagation();
            data.onToggleDecl?.();
          }}
        >
          {data.declCollapsed ? "▸" : "▾"} Declarations{data.declCount ? ` (${data.declCount})` : ""}
        </button>
      ) : null}
      {data.hasWorkflows ? (
        <button
          type="button"
          className={`app-container-section-toggle${data.wfCollapsed ? " collapsed" : ""}`}
          style={{ top: data.workflowLabelY }}
          onClick={(e) => {
            e.stopPropagation();
            data.onToggleWf?.();
          }}
        >
          {data.wfCollapsed ? "▸" : "▾"} Workflows{data.wfCount ? ` (${data.wfCount})` : ""}
        </button>
      ) : null}
    </div>
  );
}

// A single PPL construct rendered as a React Flow node, color-coded by
// execution class (deterministic / cognitive / human / governance / app).
export function PplNode({ data, selected }) {
  const [editing, setEditing] = useState(false);
  const cls = [
    "ppl-node",
    `tone-${data.tone}`,
    `role-${data.role}`,
    selected ? "selected" : "",
    data.issueLevel ? `has-issue issue-${data.issueLevel}` : "",
    data.traceStatus ? `trace-${data.traceStatus}` : "",
    data.refHighlight ? "ref-highlight" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={cls}>
      <Handle type="target" position={Position.Top} className="ppl-handle" />
      {data.issues?.length ? <IssueBadge level={data.issueLevel} tip={data.issueTip} /> : null}
      <div className="ppl-node-kw">{data.keyword}</div>
      {data.title ? (
        editing && data.renamable ? (
          <InlineRename
            className="ppl-node-rename"
            value={data.title}
            onCommit={(v) => {
              data.onRename?.(v);
              setEditing(false);
            }}
            onCancel={() => setEditing(false)}
          />
        ) : (
          <div
            className="ppl-node-title"
            onDoubleClick={(e) => {
              e.stopPropagation();
              if (data.renamable && data.onRename) setEditing(true);
            }}
          >
            {data.title}
          </div>
        )
      ) : null}
      {data.lines?.length ? (
        <div className="ppl-node-lines">
          {data.lines.map((line, i) => (
            <span key={i}>{line}</span>
          ))}
        </div>
      ) : null}
      <Handle type="source" position={Position.Bottom} className="ppl-handle" />
    </div>
  );
}

export const nodeTypes = { ppl: PplNode, appContainer: AppContainerNode };
