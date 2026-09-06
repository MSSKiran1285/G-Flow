import { Crosshair, Pencil, Trash2 } from "lucide-react";
import { Fragment, useEffect, useState } from "react";
import { api, ApiError } from "../../api";
import type { ModuleAttributeOut, ModuleDetail } from "../../types";

function windowIdOf(componentId: string): string {
  return componentId.match(/^(wnd\[\d+\])/)?.[1] ?? "";
}

/** Friendly labels for the ActionOp names a Module attribute was captured as
 * supporting — shown so a reader doesn't have to already know the raw op names. */
const ACTION_LABELS: Record<string, string> = {
  SET: "Set",
  PRESS: "Click",
  SEND_VKEY: "Send key",
  SELECT: "Select",
  READ: "Read",
  VERIFY: "Verify",
  TABLE_GET_CELL: "Read cell",
  TABLE_SET_CELL: "Set cell",
  GRID_GET_CELL: "Read cell",
  GRID_SET_CELL: "Set cell",
  GRID_SELECT_ROWS: "Select rows",
  GRID_DOUBLE_CLICK_CELL: "Double-click cell",
  SET_FOCUS: "Focus",
  WINDOW_CLOSE: "Close window",
  HIGHLIGHT: "Highlight",
};

function describeActions(modes: string[]): string {
  return modes.map((m) => ACTION_LABELS[m] ?? m).join(", ");
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

export function ModuleDetailView({
  name,
  onEdit,
  onDelete,
}: {
  name: string;
  onEdit?: () => void;
  onDelete?: () => void;
}) {
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

  const inputCount = detail.attributes.filter((a) => a.direction === "input").length;
  const outputCount = detail.attributes.length - inputCount;

  return (
    <div className="panel">
      <div className="panel-header">
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
          <h2 style={{ margin: 0 }}>{detail.name}</h2>
          <span className="chip chip-literal">{detail.tcode}</span>
          <span className="chip chip-literal">{detail.attribute_count} attributes</span>
          <span className="chip chip-column">{inputCount} input</span>
          <span className="chip chip-buffer">{outputCount} output</span>
          {detail.folder && <span className="chip chip-literal">{detail.folder}</span>}
        </div>
      </div>
      <div className="toolbar">
        <button className="btn" onClick={onEdit} disabled={!onEdit}>
          <Pencil size={14} /> Edit
        </button>
        <button className="btn btn-danger" onClick={onDelete} disabled={!onDelete}>
          <Trash2 size={14} /> Delete
        </button>
      </div>
      <div className="panel-body">
        {error && <div className="error-banner">{error}</div>}
        <input
          type="search"
          placeholder="Filter attributes by name, caption, or value…"
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
                <th>Caption</th>
                <th>Value</th>
                <th>Type</th>
                <th>Action</th>
                <th>Direction</th>
                <th>Component id</th>
              </tr>
            </thead>
            <tbody>
              {groupByWindow(attributes).map(([windowTitle, rows]) => (
                <Fragment key={windowTitle}>
                  <tr className="table-group-row">
                    <td colSpan={8}>{windowTitle}</td>
                  </tr>
                  {rows.map((a) => (
                    <tr key={a.id}>
                      <td style={{ width: 1 }}>
                        <button
                          className="icon-btn"
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
                      <td>
                        {a.supported_action_modes.length ? (
                          describeActions(a.supported_action_modes)
                        ) : (
                          <span className="breadcrumb">—</span>
                        )}
                      </td>
                      <td>
                        <span className={`chip chip-${a.direction === "input" ? "column" : "buffer"}`}>
                          {a.direction === "input" ? "Input" : "Output"}
                        </span>
                      </td>
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
