import { Crosshair } from "lucide-react";
import { Fragment, useEffect, useState } from "react";
import { api, ApiError } from "../../api";
import type { ModuleAttributeOut, ModuleDetail } from "../../types";

function windowIdOf(componentId: string): string {
  return componentId.match(/^(wnd\[\d+\])/)?.[1] ?? "";
}

/** Groups a Module's attributes by the real window/dialog they were captured from (e.g.
 * "Create Sales Order: Initial Screen"), falling back to the technical window id or
 * "Other" — same grouping ScanModuleDialog's capture/review tables use. */
function groupByWindow(attributes: ModuleAttributeOut[]): [string, ModuleAttributeOut[]][] {
  const order: string[] = [];
  const groups = new Map<string, ModuleAttributeOut[]>();
  for (const a of attributes) {
    const key = a.window_title || windowIdOf(a.component_id) || "Other";
    if (!groups.has(key)) {
      groups.set(key, []);
      order.push(key);
    }
    groups.get(key)!.push(a);
  }
  return order.map((key) => [key, groups.get(key)!]);
}

export function ModuleDetailView({ name }: { name: string }) {
  const [detail, setDetail] = useState<ModuleDetail | null>(null);
  const [filter, setFilter] = useState("");
  const [highlighting, setHighlighting] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setDetail(null);
    api.getModule(name).then(setDetail).catch(() => setDetail(null));
  }, [name]);

  const highlight = async (componentId: string) => {
    setHighlighting(componentId);
    setError(null);
    try {
      await api.highlightComponent(componentId);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not highlight that field");
    } finally {
      setHighlighting(null);
    }
  };

  if (!detail) return <p className="empty-state">Loading…</p>;

  const attributes = detail.attributes.filter((a) => {
    if (!filter) return true;
    const needle = filter.toLowerCase();
    return (
      a.semantic_name.toLowerCase().includes(needle) ||
      a.label.toLowerCase().includes(needle) ||
      a.caption.toLowerCase().includes(needle)
    );
  });

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>{detail.name}</h2>
        <span className="breadcrumb">{detail.tcode} · {detail.attribute_count} attributes</span>
      </div>
      <div className="panel-body">
        {error && <div className="error-banner">{error}</div>}
        <input
          type="search"
          placeholder="Filter attributes by name, English name, or value…"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          style={{ marginBottom: 12, width: "100%" }}
        />
        <div className="table-frame">
          <table className="data-table">
            <thead>
              <tr>
                <th />
                <th>Semantic name</th>
                <th>English name</th>
                <th>Value</th>
                <th>Type</th>
                <th>Component id</th>
              </tr>
            </thead>
            <tbody>
              {groupByWindow(attributes).map(([windowTitle, rows]) => (
                <Fragment key={windowTitle}>
                  <tr className="table-group-row">
                    <td colSpan={6}>{windowTitle}</td>
                  </tr>
                  {rows.map((a) => (
                    <tr key={a.id}>
                      <td style={{ width: 1 }}>
                        <button
                          className="drag-handle"
                          aria-label={`Highlight ${a.component_id} on screen`}
                          title="Highlight this field on the live SAP screen"
                          disabled={highlighting === a.component_id}
                          onClick={() => highlight(a.component_id)}
                        >
                          <Crosshair size={14} />
                        </button>
                      </td>
                      <td>{a.semantic_name}</td>
                      <td>{a.caption || <span className="breadcrumb">—</span>}</td>
                      <td>{a.label}</td>
                      <td>{a.sap_type}</td>
                      <td style={{ font: "var(--text-code)" }}>{a.component_id}</td>
                    </tr>
                  ))}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
