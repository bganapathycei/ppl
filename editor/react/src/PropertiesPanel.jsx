// Schema-driven properties form for the selected node. Reads field definitions
// from the shared schema and writes edits back into the AST via model.js.
import { BLOCKS, TYPES, OPERATORS } from "../../js/schema.js";
import { getNode, getSlot, setProp, createNode, insertNode, removeNode } from "../../js/model.js";

const SIMPLE_KINDS = new Set(["field", "category", "option", "source", "rule", "memory_clause", "consider", "arg"]);

function Field({ node, field, onEdit }) {
  const value = node[field.prop];
  const common = {
    value: field.kind === "check" ? undefined : value ?? "",
    onChange: (e) => {
      const v = field.kind === "check" ? e.target.checked : e.target.value;
      setProp(node, field.prop, v);
      onEdit();
    },
  };
  if (field.kind === "textarea") {
    return (
      <label className="pf-row">
        <span>{field.prop.replace(/_/g, " ")}</span>
        <textarea rows={3} placeholder={field.placeholder} {...common} />
      </label>
    );
  }
  if (field.kind === "type" || field.kind === "operator") {
    const options = field.kind === "type" ? TYPES : OPERATORS;
    return (
      <label className="pf-row">
        <span>{field.prop.replace(/_/g, " ")}</span>
        <select {...common}>
          {options.map((o) => (
            <option key={o} value={o}>
              {o || "—"}
            </option>
          ))}
        </select>
      </label>
    );
  }
  if (field.kind === "check") {
    return (
      <label className="pf-check">
        <input type="checkbox" checked={Boolean(value)} onChange={common.onChange} /> {field.label || field.prop}
      </label>
    );
  }
  return (
    <label className="pf-row">
      <span>{field.prop.replace(/_/g, " ")}</span>
      <input placeholder={field.placeholder} {...common} />
    </label>
  );
}

function InlineSlot({ node, spec, onEdit, onStructure }) {
  const list = getSlot(node, spec.name) || [];
  const childKind = spec.accept[0];
  const childDef = BLOCKS[childKind] || {};
  return (
    <div className="pf-slot">
      <div className="pf-slot-head">
        <span>{spec.label || spec.name}</span>
        <button
          type="button"
          onClick={() => {
            insertNode(node, spec.name, list.length, createNode(childKind));
            onStructure();
          }}
        >
          + {childDef.keyword || childKind}
        </button>
      </div>
      {!list.length ? <p className="pf-empty">none</p> : null}
      {list.map((item) => (
        <div className="pf-item" key={item.id}>
          {(childDef.fields || []).map((field) => (
            <Field key={field.prop} node={item} field={field} onEdit={onEdit} />
          ))}
          <button
            type="button"
            className="pf-del"
            title="Remove"
            onClick={() => {
              removeNode(node, item.id);
              onStructure();
            }}
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  );
}

export default function PropertiesPanel({ program, selectedId, onEdit, onStructure, onDelete }) {
  const node = selectedId ? getNode(program, selectedId) : null;
  if (!node) {
    return <p className="pf-hint">Select a node on the canvas to edit its properties.</p>;
  }
  const def = BLOCKS[node.kind] || {};
  const inlineSlots = (def.slots || []).filter((s) => (s.accept || []).every((k) => SIMPLE_KINDS.has(k)));
  const complex = (def.slots || []).filter((s) => !(s.accept || []).every((k) => SIMPLE_KINDS.has(k)));
  return (
    <div className="pf">
      <div className="pf-title">
        <span className={`pf-kw tone-${def.tone || "det"}`}>{def.keyword || node.kind}</span>
        {node.kind !== "app" && node.kind !== "program" ? (
          <button type="button" className="pf-remove" onClick={() => onDelete(node.id)}>
            Delete
          </button>
        ) : null}
      </div>
      {(def.fields || []).map((field) => (
        <Field key={field.prop} node={node} field={field} onEdit={onEdit} />
      ))}
      {inlineSlots.map((spec) => (
        <InlineSlot key={spec.name} node={node} spec={spec} onEdit={onEdit} onStructure={onStructure} />
      ))}
      {complex.length ? (
        <p className="pf-hint">
          Add {complex.map((s) => (s.label || s.name).toLowerCase()).join(", ")} from the toolbar “Add step”.
        </p>
      ) : null}
    </div>
  );
}
