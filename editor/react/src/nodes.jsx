import { Handle, Position } from "@xyflow/react";

// A single PPL construct rendered as a React Flow node, color-coded by
// execution class (deterministic / cognitive / human / governance / app).
export function PplNode({ data, selected }) {
  const cls = `ppl-node tone-${data.tone} role-${data.role}${selected ? " selected" : ""}`;
  return (
    <div className={cls}>
      <Handle type="target" position={Position.Top} className="ppl-handle" />
      <div className="ppl-node-kw">{data.keyword}</div>
      {data.title ? <div className="ppl-node-title">{data.title}</div> : null}
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

export const nodeTypes = { ppl: PplNode };
