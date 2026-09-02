import { useState } from "react";
import { BLOCKS, PALETTE_GROUPS } from "../../js/schema.js";

export default function Palette({ onAdd, statusMsg }) {
  const [selected, setSelected] = useState(null);

  const handleClick = (kind) => {
    if (selected === kind) {
      const added = onAdd(kind);
      if (added) setSelected(null);
    } else {
      setSelected(kind);
    }
  };

  return (
    <aside className="palette-pane" aria-label="PPL constructs">
      <h2>Blocks</h2>
      <p className="palette-hint">
        {selected ? "Click again to add, or pick another block." : "Click a block to select, then click again to add."}
      </p>
      {PALETTE_GROUPS.map((group) => (
        <div key={group.id} className="palette-group">
          <h3>{group.title}</h3>
          <div className="palette-items">
            {group.kinds.map((kind) => {
              const def = BLOCKS[kind];
              if (!def) return null;
              return (
                <button
                  key={kind}
                  type="button"
                  className={`palette-item tone-${def.tone}${selected === kind ? " selected" : ""}`}
                  title={def.keyword}
                  onClick={() => handleClick(kind)}
                >
                  <span className={`palette-swatch tone-${def.tone}`} />
                  {def.keyword}
                </button>
              );
            })}
          </div>
        </div>
      ))}
      {statusMsg ? <p className="palette-status">{statusMsg}</p> : null}
    </aside>
  );
}
