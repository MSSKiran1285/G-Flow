import { Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../../api";
import type { TestCaseSummary } from "../../types";
import { TestCaseEditor } from "./TestCaseEditor";

export function ScriptsPanel() {
  const [scripts, setScripts] = useState<TestCaseSummary[]>([]);
  const [editing, setEditing] = useState<string | null | undefined>(undefined); // undefined = list view

  const reload = () => {
    api.listTestCases().then(setScripts).catch(() => setScripts([]));
  };

  useEffect(reload, []);

  if (editing !== undefined) {
    return (
      <TestCaseEditor
        name={editing}
        onClose={() => {
          setEditing(undefined);
          reload();
        }}
      />
    );
  }

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Scripts</h2>
      </div>
      <div className="toolbar">
        <button className="btn btn-primary" onClick={() => setEditing(null)}>
          <Plus size={14} /> New script
        </button>
      </div>
      <div className="table-frame">
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Description</th>
              <th>Steps</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {scripts.map((s) => (
              <tr key={s.id}>
                <td style={{ cursor: "pointer" }} onClick={() => setEditing(s.name)}>
                  {s.name}
                </td>
                <td>{s.description}</td>
                <td>{s.step_count}</td>
                <td>
                  <button
                    className="drag-handle"
                    aria-label={`Delete ${s.name}`}
                    onClick={async () => {
                      await api.deleteTestCase(s.name);
                      reload();
                    }}
                  >
                    <Trash2 size={14} />
                  </button>
                </td>
              </tr>
            ))}
            {scripts.length === 0 && (
              <tr>
                <td className="empty-state">No scripts yet — create one above.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
