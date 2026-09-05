import { useEffect, useState } from "react";
import { api } from "../../api";
import type { ModuleDetail } from "../../types";

export function ModuleDetailView({ name }: { name: string }) {
  const [detail, setDetail] = useState<ModuleDetail | null>(null);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    setDetail(null);
    api.getModule(name).then(setDetail).catch(() => setDetail(null));
  }, [name]);

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
                <th>Semantic name</th>
                <th>English name</th>
                <th>Value</th>
                <th>Type</th>
                <th>Component id</th>
              </tr>
            </thead>
            <tbody>
              {attributes.map((a) => (
                <tr key={a.id}>
                  <td>{a.semantic_name}</td>
                  <td>{a.caption || <span className="breadcrumb">—</span>}</td>
                  <td>{a.label}</td>
                  <td>{a.sap_type}</td>
                  <td style={{ font: "var(--text-code)" }}>{a.component_id}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
