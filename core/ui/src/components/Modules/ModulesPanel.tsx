import { Plus } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../../api";
import type { ModuleSummary } from "../../types";
import { ModuleDetailView } from "./ModuleDetailView";
import { ScanModuleDialog } from "./ScanModuleDialog";

export function ModulesPanel() {
  const [modules, setModules] = useState<ModuleSummary[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [showScan, setShowScan] = useState(false);

  const reload = () => {
    api.listModules().then(setModules).catch(() => setModules([]));
  };

  useEffect(reload, []);

  return (
    <div style={{ display: "grid", gridTemplateColumns: "320px 1fr", gap: 20, alignItems: "start" }}>
      <div className="panel">
        <div className="panel-header">
          <h2>Modules</h2>
        </div>
        <div className="toolbar">
          <button className="btn btn-primary" onClick={() => setShowScan(true)}>
            <Plus size={14} /> Scan new module
          </button>
        </div>
        <div className="table-frame">
          <table className="data-table">
            <tbody>
              {modules.map((m) => (
                <tr
                  key={m.id}
                  className={selected === m.name ? "selected" : undefined}
                  onClick={() => setSelected(m.name)}
                  style={{ cursor: "pointer" }}
                >
                  <td>
                    <div>{m.name}</div>
                    <div className="breadcrumb">{m.tcode} · {m.attribute_count} attrs</div>
                  </td>
                </tr>
              ))}
              {modules.length === 0 && (
                <tr>
                  <td className="empty-state">No modules scanned yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {selected ? <ModuleDetailView name={selected} /> : <p className="empty-state">Select a module to see its attributes.</p>}

      {showScan && (
        <ScanModuleDialog
          onClose={() => setShowScan(false)}
          onScanned={() => {
            reload();
          }}
        />
      )}
    </div>
  );
}
