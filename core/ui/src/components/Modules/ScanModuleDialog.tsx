import { Plus, Trash2, X } from "lucide-react";
import { useMemo, useState } from "react";
import { api, ApiError } from "../../api";
import type { ScannedComponentOut } from "../../types";

interface PrefillPair {
  componentId: string;
  value: string;
}

type Step = "configure" | "select";

export function ScanModuleDialog({ onClose, onScanned }: { onClose: () => void; onScanned: () => void }) {
  const [step, setStep] = useState<Step>("configure");

  // --- configure step state ---
  const [moduleName, setModuleName] = useState("");
  const [tcode, setTcode] = useState("");
  const [rootId, setRootId] = useState("wnd[0]");
  const [navigate, setNavigate] = useState(true);
  const [prefill, setPrefill] = useState<PrefillPair[]>([]);
  const [vkeys, setVkeys] = useState<string[]>([]);

  // --- select step state ---
  const [screenNumber, setScreenNumber] = useState("");
  const [components, setComponents] = useState<ScannedComponentOut[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [names, setNames] = useState<Record<string, string>>({});
  const [filter, setFilter] = useState("");

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const scan = async () => {
    setBusy(true);
    setError(null);
    try {
      const result = await api.scanPreview({
        tcode,
        root_id: rootId,
        navigate,
        prefill: Object.fromEntries(prefill.filter((p) => p.componentId).map((p) => [p.componentId, p.value])),
        vkeys_before_scan: vkeys.filter(Boolean),
      });
      setComponents(result.components);
      setScreenNumber(result.screen_number);
      setNames(Object.fromEntries(result.components.map((c) => [c.component_id, c.semantic_name])));
      setSelected(new Set());
      setStep("select");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Scan failed");
    } finally {
      setBusy(false);
    }
  };

  const groups = useMemo(() => {
    const byWindow = new Map<string, ScannedComponentOut[]>();
    for (const c of components) {
      if (!byWindow.has(c.window)) byWindow.set(c.window, []);
      byWindow.get(c.window)!.push(c);
    }
    return [...byWindow.entries()].sort(([a], [b]) => a.localeCompare(b));
  }, [components]);

  const visible = (list: ScannedComponentOut[]) =>
    !filter
      ? list
      : list.filter((c) => {
          const needle = filter.toLowerCase();
          return (
            c.semantic_name.toLowerCase().includes(needle) ||
            c.label.toLowerCase().includes(needle) ||
            c.component_id.toLowerCase().includes(needle)
          );
        });

  const toggle = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleGroup = (list: ScannedComponentOut[], checked: boolean) => {
    setSelected((prev) => {
      const next = new Set(prev);
      for (const c of list) {
        if (checked) next.add(c.component_id);
        else next.delete(c.component_id);
      }
      return next;
    });
  };

  const save = async () => {
    setBusy(true);
    setError(null);
    try {
      const byId = new Map(components.map((c) => [c.component_id, c]));
      const attributes = [...selected].map((id) => {
        const c = byId.get(id)!;
        return {
          semantic_name: names[id] || c.semantic_name,
          component_id: c.component_id,
          sap_type: c.sap_type,
          sap_sub_type: c.sap_sub_type,
          label: c.label,
          supported_action_modes: c.supported_action_modes,
        };
      });
      await api.saveModule({ module_name: moduleName, tcode, root_id: rootId, screen_number: screenNumber, attributes });
      onScanned();
      onClose();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Save failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="dialog-backdrop" onClick={onClose}>
      <div
        className="dialog"
        style={step === "select" ? { width: "min(920px, 96vw)" } : undefined}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="scan-title"
      >
        <div className="dialog-header">
          <h3 id="scan-title">{step === "configure" ? "Scan a screen" : `Pick fields for "${moduleName}"`}</h3>
          <button className="btn" aria-label="Close" onClick={onClose}>
            <X size={16} />
          </button>
        </div>
        <div className="dialog-body">
          {error && <div className="error-banner">{error}</div>}

          {step === "configure" && (
            <>
              <div className="field">
                <label htmlFor="module-name">Module name</label>
                <input id="module-name" type="text" value={moduleName} onChange={(e) => setModuleName(e.target.value)} placeholder="e.g. ME21N_InitialScreen" />
              </div>
              <div className="field">
                <label htmlFor="tcode">Transaction code</label>
                <input id="tcode" type="text" value={tcode} onChange={(e) => setTcode(e.target.value.toUpperCase())} placeholder="e.g. ME21N" />
              </div>
              <details className="details-advanced">
                <summary>Advanced (root id, prefill, navigation)</summary>
                <div className="field" style={{ marginTop: 12 }}>
                  <label htmlFor="root-id">Root component id</label>
                  <input id="root-id" type="text" value={rootId} onChange={(e) => setRootId(e.target.value)} />
                </div>
                <div className="field">
                  <label>
                    <input type="checkbox" checked={navigate} onChange={(e) => setNavigate(e.target.checked)} /> Navigate to the tcode before scanning
                  </label>
                </div>
                <div className="field">
                  <label>Prefill fields (set before scanning)</label>
                  {prefill.map((pair, i) => (
                    <div key={i} style={{ display: "flex", gap: 8, marginBottom: 4 }}>
                      <input
                        type="text" placeholder="component id" value={pair.componentId}
                        onChange={(e) => setPrefill(prefill.map((p, j) => (j === i ? { ...p, componentId: e.target.value } : p)))}
                      />
                      <input
                        type="text" placeholder="value" value={pair.value}
                        onChange={(e) => setPrefill(prefill.map((p, j) => (j === i ? { ...p, value: e.target.value } : p)))}
                      />
                      <button className="drag-handle" aria-label="Remove prefill" onClick={() => setPrefill(prefill.filter((_, j) => j !== i))}>
                        <Trash2 size={14} />
                      </button>
                    </div>
                  ))}
                  <button className="btn" onClick={() => setPrefill([...prefill, { componentId: "", value: "" }])}>
                    <Plus size={14} /> Add prefill field
                  </button>
                </div>
                <div className="field">
                  <label>VKeys to send before scanning (in order)</label>
                  {vkeys.map((v, i) => (
                    <div key={i} style={{ display: "flex", gap: 8, marginBottom: 4 }}>
                      <input type="text" value={v} onChange={(e) => setVkeys(vkeys.map((x, j) => (j === i ? e.target.value : x)))} />
                      <button className="drag-handle" aria-label="Remove vkey" onClick={() => setVkeys(vkeys.filter((_, j) => j !== i))}>
                        <Trash2 size={14} />
                      </button>
                    </div>
                  ))}
                  <button className="btn" onClick={() => setVkeys([...vkeys, "Enter"])}>
                    <Plus size={14} /> Add vkey
                  </button>
                </div>
              </details>
            </>
          )}

          {step === "select" && (
            <>
              <input
                type="search"
                placeholder="Filter by name, label, or component id…"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                style={{ width: "100%", marginBottom: 12 }}
              />
              <div className="breadcrumb" style={{ marginBottom: 12 }}>
                {selected.size} of {components.length} selected
              </div>
              {groups.map(([window, list]) => {
                const shown = visible(list);
                if (shown.length === 0) return null;
                const allChecked = shown.every((c) => selected.has(c.component_id));
                return (
                  <div key={window} style={{ marginBottom: 16 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                      <input
                        type="checkbox"
                        checked={allChecked}
                        onChange={(e) => toggleGroup(shown, e.target.checked)}
                        aria-label={`Select all fields in ${window}`}
                      />
                      <strong style={{ font: "var(--text-code)" }}>{window}</strong>
                      <span className="breadcrumb">({shown.length})</span>
                    </div>
                    <div className="table-frame">
                      <table className="data-table">
                        <tbody>
                          {shown.map((c) => (
                            <tr key={c.component_id}>
                              <td style={{ width: 1 }}>
                                <input
                                  type="checkbox"
                                  checked={selected.has(c.component_id)}
                                  onChange={() => toggle(c.component_id)}
                                  aria-label={`Select ${c.component_id}`}
                                />
                              </td>
                              <td>
                                <input
                                  type="text"
                                  value={names[c.component_id] ?? c.semantic_name}
                                  onChange={(e) => setNames({ ...names, [c.component_id]: e.target.value })}
                                  style={{ border: "none", background: "transparent", font: "var(--text-code)", width: "100%" }}
                                />
                              </td>
                              <td>{c.label}</td>
                              <td className="breadcrumb">{c.sap_type}</td>
                              <td style={{ font: "var(--text-code)" }}>{c.component_id}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                );
              })}
            </>
          )}
        </div>
        <div className="dialog-footer">
          {step === "select" && (
            <button className="btn" onClick={() => setStep("configure")} disabled={busy}>
              Back
            </button>
          )}
          <button className="btn" onClick={onClose}>
            Cancel
          </button>
          {step === "configure" ? (
            <button className="btn btn-primary" disabled={!moduleName || !tcode || busy} onClick={scan}>
              {busy ? "Scanning…" : "Scan screen"}
            </button>
          ) : (
            <button className="btn btn-primary" disabled={selected.size === 0 || busy} onClick={save}>
              {busy ? "Saving…" : `Save ${selected.size} selected as Module`}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
