import { Plus, Trash2, X } from "lucide-react";
import { useState } from "react";
import { api, ApiError } from "../../api";

interface PrefillPair {
  componentId: string;
  value: string;
}

export function ScanModuleDialog({ onClose, onScanned }: { onClose: () => void; onScanned: () => void }) {
  const [moduleName, setModuleName] = useState("");
  const [tcode, setTcode] = useState("");
  const [rootId, setRootId] = useState("wnd[0]");
  const [navigate, setNavigate] = useState(true);
  const [prefill, setPrefill] = useState<PrefillPair[]>([]);
  const [vkeys, setVkeys] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resultText, setResultText] = useState<string | null>(null);

  const submit = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const result = await api.scanModule({
        module_name: moduleName,
        tcode,
        root_id: rootId,
        navigate,
        prefill: Object.fromEntries(prefill.filter((p) => p.componentId).map((p) => [p.componentId, p.value])),
        vkeys_before_scan: vkeys.filter(Boolean),
      });
      setResultText(`Scanned ${result.attribute_count} attributes into "${result.module_name}".`);
      onScanned();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Scan failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="dialog-backdrop" onClick={onClose}>
      <div className="dialog" onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true" aria-labelledby="scan-title">
        <div className="dialog-header">
          <h3 id="scan-title">Scan a new Module</h3>
          <button className="btn" aria-label="Close" onClick={onClose}>
            <X size={16} />
          </button>
        </div>
        <div className="dialog-body">
          {error && <div className="error-banner">{error}</div>}
          {resultText && <div className="panel panel-body" style={{ marginBottom: 12 }}>{resultText}</div>}
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
        </div>
        <div className="dialog-footer">
          <button className="btn" onClick={onClose}>Close</button>
          <button className="btn btn-primary" disabled={!moduleName || !tcode || submitting} onClick={submit}>
            {submitting ? "Scanning…" : "Scan"}
          </button>
        </div>
      </div>
    </div>
  );
}
