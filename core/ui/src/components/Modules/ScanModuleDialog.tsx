import { MousePointerClick, Plus, Trash2, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { api, ApiError } from "../../api";
import type { ScannedComponentOut } from "../../types";

interface PrefillPair {
  componentId: string;
  value: string;
}

type Step = "configure" | "capturing" | "review";

export function ScanModuleDialog({ onClose, onScanned }: { onClose: () => void; onScanned: () => void }) {
  const [step, setStep] = useState<Step>("configure");

  // --- configure step state ---
  const [moduleName, setModuleName] = useState("");
  const [tcode, setTcode] = useState("");
  const [rootId, setRootId] = useState("wnd[0]");
  const [navigate, setNavigate] = useState(true);
  const [prefill, setPrefill] = useState<PrefillPair[]>([]);
  const [vkeys, setVkeys] = useState<string[]>([]);

  // --- capturing / review state ---
  const [captureId, setCaptureId] = useState<string | null>(null);
  const [picked, setPicked] = useState<ScannedComponentOut[]>([]);
  const [names, setNames] = useState<Record<string, string>>({});
  const pollTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mergeNew = (incoming: ScannedComponentOut[]) => {
    if (incoming.length === 0) return;
    setPicked((prev) => {
      const known = new Set(prev.map((c) => c.component_id));
      const fresh = incoming.filter((c) => !known.has(c.component_id));
      return fresh.length ? [...prev, ...fresh] : prev;
    });
    setNames((prev) => {
      const next = { ...prev };
      for (const c of incoming) if (!(c.component_id in next)) next[c.component_id] = c.semantic_name;
      return next;
    });
  };

  useEffect(() => () => {
    if (pollTimer.current) clearInterval(pollTimer.current);
  }, []);

  const startCapture = async () => {
    setBusy(true);
    setError(null);
    try {
      const result = await api.startCapture({
        tcode,
        navigate,
        prefill: Object.fromEntries(prefill.filter((p) => p.componentId).map((p) => [p.componentId, p.value])),
        vkeys_before_scan: vkeys.filter(Boolean),
      });
      setCaptureId(result.capture_id);
      setPicked([]);
      setNames({});
      setStep("capturing");
      pollTimer.current = setInterval(async () => {
        try {
          const poll = await api.pollCapture(result.capture_id);
          mergeNew(poll.components);
          if (poll.error) setError(poll.error);
        } catch {
          // transient poll failure — keep trying until the user stops
        }
      }, 500);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not start capture");
    } finally {
      setBusy(false);
    }
  };

  const stopCapture = async () => {
    if (!captureId) return;
    setBusy(true);
    setError(null);
    if (pollTimer.current) {
      clearInterval(pollTimer.current);
      pollTimer.current = null;
    }
    try {
      const result = await api.stopCapture(captureId);
      mergeNew(result.components);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not stop capture");
    } finally {
      setBusy(false);
      setStep("review");
    }
  };

  const removePicked = (componentId: string) => {
    setPicked((prev) => prev.filter((c) => c.component_id !== componentId));
  };

  const save = async () => {
    setBusy(true);
    setError(null);
    try {
      const attributes = picked.map((c) => ({
        semantic_name: names[c.component_id] || c.semantic_name,
        component_id: c.component_id,
        sap_type: c.sap_type,
        sap_sub_type: c.sap_sub_type,
        label: c.label,
        supported_action_modes: c.supported_action_modes,
      }));
      await api.saveModule({ module_name: moduleName, tcode, root_id: rootId, attributes });
      onScanned();
      onClose();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Save failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="dialog-backdrop" onClick={step === "capturing" ? undefined : onClose}>
      <div
        className="dialog"
        style={step !== "configure" ? { width: "min(760px, 96vw)" } : undefined}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="scan-title"
      >
        <div className="dialog-header">
          <h3 id="scan-title">
            {step === "configure" && "Pick fields from a screen"}
            {step === "capturing" && "Capturing… Ctrl+Click fields in SAP"}
            {step === "review" && `Review ${picked.length} captured field${picked.length === 1 ? "" : "s"}`}
          </h3>
          {step !== "capturing" && (
            <button className="btn" aria-label="Close" onClick={onClose}>
              <X size={16} />
            </button>
          )}
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
                    <input type="checkbox" checked={navigate} onChange={(e) => setNavigate(e.target.checked)} /> Launch the transaction before capturing
                  </label>
                </div>
                <div className="field">
                  <label>Prefill fields (set before launching)</label>
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
                  <label>VKeys to send before capturing (in order)</label>
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

          {step === "capturing" && (
            <>
              <div className="panel panel-body" style={{ marginBottom: 16, display: "flex", gap: 12, alignItems: "center" }}>
                <MousePointerClick size={28} aria-hidden="true" />
                <div>
                  <strong>Switch to your SAP window</strong> and hold <kbd>Ctrl</kbd> while clicking each field,
                  button, or control you want — it appears in the list below the moment you click it. Come back
                  here and press "Stop scanning" when you're done.
                </div>
              </div>
              <div className="breadcrumb" style={{ marginBottom: 8 }}>{picked.length} captured so far</div>
              <div className="table-frame">
                <table className="data-table">
                  <tbody>
                    {picked.map((c) => (
                      <tr key={c.component_id}>
                        <td style={{ font: "var(--text-code)" }}>{names[c.component_id] ?? c.semantic_name}</td>
                        <td>{c.label}</td>
                        <td className="breadcrumb">{c.sap_type}</td>
                        <td style={{ font: "var(--text-code)" }}>{c.component_id}</td>
                      </tr>
                    ))}
                    {picked.length === 0 && (
                      <tr>
                        <td className="empty-state">Waiting for your first Ctrl+Click…</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </>
          )}

          {step === "review" && (
            <div className="table-frame">
              <table className="data-table">
                <tbody>
                  {picked.map((c) => (
                    <tr key={c.component_id}>
                      <td style={{ width: 1 }}>
                        <button className="drag-handle" aria-label={`Remove ${c.component_id}`} onClick={() => removePicked(c.component_id)}>
                          <Trash2 size={14} />
                        </button>
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
                  {picked.length === 0 && (
                    <tr>
                      <td className="empty-state">Nothing captured — go back and try again.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
        <div className="dialog-footer">
          {step === "review" && (
            <button className="btn" onClick={() => setStep("capturing")} disabled={busy}>
              Back to capturing
            </button>
          )}
          {step !== "capturing" && (
            <button className="btn" onClick={onClose}>
              Cancel
            </button>
          )}
          {step === "configure" && (
            <button className="btn btn-primary" disabled={!moduleName || !tcode || busy} onClick={startCapture}>
              {busy ? "Launching…" : "Launch & start picking"}
            </button>
          )}
          {step === "capturing" && (
            <button className="btn btn-danger" disabled={busy} onClick={stopCapture}>
              Stop scanning
            </button>
          )}
          {step === "review" && (
            <button className="btn btn-primary" disabled={picked.length === 0 || busy} onClick={save}>
              {busy ? "Saving…" : `Save ${picked.length} field${picked.length === 1 ? "" : "s"} as Module`}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
