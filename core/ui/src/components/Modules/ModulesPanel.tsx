import { ChevronDown, ChevronRight, Folder, Plus } from "lucide-react";
import { Fragment, useEffect, useMemo, useState } from "react";
import { api } from "../../api";
import type { ModuleSummary } from "../../types";
import { ModuleDetailView } from "./ModuleDetailView";
import { ScanModuleDialog } from "./ScanModuleDialog";

const UNTAGGED = "Untagged";

/** Groups modules by folder (falling back to "Untagged"), sorted so named folders
 * come before the fallback bucket, each internally sorted by module name. */
function groupByFolder(modules: ModuleSummary[]): [string, ModuleSummary[]][] {
  const groups = new Map<string, ModuleSummary[]>();
  for (const m of modules) {
    const key = m.folder || UNTAGGED;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(m);
  }
  for (const list of groups.values()) list.sort((a, b) => a.name.localeCompare(b.name));
  return [...groups.entries()].sort(([a], [b]) => {
    if (a === UNTAGGED) return 1;
    if (b === UNTAGGED) return -1;
    return a.localeCompare(b);
  });
}

export function ModulesPanel() {
  const [modules, setModules] = useState<ModuleSummary[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [showScan, setShowScan] = useState(false);
  const [editing, setEditing] = useState<ModuleSummary | null>(null);
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());

  const reload = () => {
    api.listModules().then(setModules).catch(() => setModules([]));
  };

  useEffect(reload, []);

  const groups = useMemo(() => groupByFolder(modules), [modules]);

  const toggleFolder = (folder: string) => {
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(folder)) next.delete(folder);
      else next.add(folder);
      return next;
    });
  };

  const deleteSelected = async () => {
    if (!selected) return;
    if (!window.confirm(`Delete module "${selected}"? This can't be undone — any script that references its attributes will start failing at run time.`)) {
      return;
    }
    await api.deleteModule(selected);
    setSelected(null);
    reload();
  };

  const rootCollapsed = collapsed.has("__root__");

  return (
    <div style={{ display: "grid", gridTemplateColumns: "320px 1fr", gap: 20, alignItems: "start" }}>
      <div className="panel">
        <div className="panel-header">
          <h2>Object Library</h2>
          <button className="icon-btn" aria-label="Scan new module" title="Scan new module" onClick={() => setShowScan(true)}>
            <Plus size={16} />
          </button>
        </div>
        <div className="table-frame">
          <table className="data-table">
            <tbody>
              <tr className="table-group-row" style={{ cursor: "pointer" }} onClick={() => toggleFolder("__root__")}>
                <td style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", fontWeight: 600 }}>
                  {rootCollapsed ? <ChevronRight size={14} /> : <ChevronDown size={14} />}
                  <Folder size={14} />
                  Repositories
                  <span className="chip chip-literal">{groups.length}</span>
                </td>
              </tr>
              {!rootCollapsed &&
                groups.map(([folder, items]) => (
                  <Fragment key={folder}>
                    <tr className="table-group-row" style={{ cursor: "pointer" }} onClick={() => toggleFolder(folder)}>
                      <td style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", paddingLeft: "var(--space-5)" }}>
                        {collapsed.has(folder) ? <ChevronRight size={14} /> : <ChevronDown size={14} />}
                        <Folder size={14} />
                        {folder}
                        <span className="chip chip-literal">{items.length}</span>
                      </td>
                    </tr>
                    {!collapsed.has(folder) &&
                      items.map((m) => (
                        <tr
                          key={m.id}
                          className={selected === m.name ? "selected" : undefined}
                          onClick={() => setSelected(m.name)}
                          style={{ cursor: "pointer" }}
                        >
                          <td style={{ paddingLeft: "var(--space-6)" }}>
                            <div>{m.name}</div>
                            <div className="breadcrumb">{m.tcode} · {m.attribute_count} attrs</div>
                          </td>
                        </tr>
                      ))}
                  </Fragment>
                ))}
              {modules.length === 0 && (
                <tr>
                  <td className="empty-state">No modules scanned yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <div className="toolbar" style={{ borderTop: "none" }}>
          <button className="btn btn-primary" style={{ width: "100%", justifyContent: "center" }} onClick={() => setShowScan(true)}>
            <Plus size={14} /> Scan new module
          </button>
        </div>
        <p className="breadcrumb" style={{ textAlign: "center", padding: "0 var(--space-3) var(--space-3)" }}>
          {groups.length} folder{groups.length === 1 ? "" : "s"} · {modules.length} module{modules.length === 1 ? "" : "s"}
        </p>
      </div>

      {selected ? (
        <ModuleDetailView
          name={selected}
          onEdit={() => {
            const m = modules.find((x) => x.name === selected);
            if (m) setEditing(m);
          }}
          onDelete={deleteSelected}
        />
      ) : (
        <p className="empty-state">Select a module to see its attributes.</p>
      )}

      {showScan && (
        <ScanModuleDialog
          onClose={() => setShowScan(false)}
          onScanned={() => {
            reload();
          }}
        />
      )}

      {editing && (
        <ScanModuleDialog
          initial={{ moduleName: editing.name, tcode: editing.tcode, folder: editing.folder }}
          onClose={() => setEditing(null)}
          onScanned={() => {
            reload();
          }}
        />
      )}
    </div>
  );
}
