import { Plus, Trash2 } from "lucide-react";
import { useState } from "react";

export type GridRows = Record<string, string>[];

/** A plain editable rows×columns table producing Record<string,string>[] directly for
 * RunTestCaseRequest/ChainStage.rows — lives only in component state, not persisted
 * anywhere (no Test Data library in this MVP). */
export function DataGridEditor({ rows, onChange }: { rows: GridRows; onChange: (rows: GridRows) => void }) {
  const columns = rows.length > 0 ? Object.keys(rows[0]) : [];
  const [newColumnName, setNewColumnName] = useState("");

  const addColumn = () => {
    const name = newColumnName.trim();
    if (!name || columns.includes(name)) return;
    const nextRows = rows.length > 0 ? rows.map((r) => ({ ...r, [name]: "" })) : [{ [name]: "" }];
    onChange(nextRows);
    setNewColumnName("");
  };

  const removeColumn = (name: string) => {
    onChange(rows.map((r) => {
      const { [name]: _removed, ...rest } = r;
      return rest;
    }));
  };

  const addRow = () => {
    const blank = Object.fromEntries(columns.map((c) => [c, ""]));
    onChange([...rows, blank]);
  };

  const removeRow = (index: number) => {
    onChange(rows.filter((_, i) => i !== index));
  };

  const setCell = (index: number, column: string, value: string) => {
    onChange(rows.map((r, i) => (i === index ? { ...r, [column]: value } : r)));
  };

  return (
    <div>
      <div className="table-frame">
        <table className="data-table">
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col}>
                  {col}{" "}
                  <button
                    className="drag-handle"
                    aria-label={`Remove column ${col}`}
                    onClick={() => removeColumn(col)}
                  >
                    <Trash2 size={12} />
                  </button>
                </th>
              ))}
              <th style={{ width: 1 }} />
            </tr>
          </thead>
          <tbody>
            {rows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {columns.map((col) => (
                  <td key={col}>
                    <input
                      type="text"
                      value={row[col] ?? ""}
                      onChange={(e) => setCell(rowIndex, col, e.target.value)}
                      style={{ border: "none", background: "transparent", width: "100%" }}
                    />
                  </td>
                ))}
                <td>
                  <button className="drag-handle" aria-label={`Remove row ${rowIndex + 1}`} onClick={() => removeRow(rowIndex)}>
                    <Trash2 size={14} />
                  </button>
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td className="empty-state">No columns yet — add one below.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="toolbar" style={{ borderBottom: "none", paddingLeft: 0 }}>
        <input
          type="text"
          placeholder="new column name"
          value={newColumnName}
          onChange={(e) => setNewColumnName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && addColumn()}
        />
        <button className="btn" onClick={addColumn}>
          <Plus size={14} /> Add column
        </button>
        <button className="btn" onClick={addRow} disabled={columns.length === 0}>
          <Plus size={14} /> Add row
        </button>
      </div>
    </div>
  );
}
