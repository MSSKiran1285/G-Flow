import { useEffect, useState } from "react";
import { api } from "../../api";
import type { CaptureFrom, CaptureSpec } from "../../types";

export function CaptureFields({
  value,
  onChange,
  defaultOpen = false,
}: {
  value: CaptureSpec | null;
  onChange: (v: CaptureSpec | null) => void;
  /** Expand the section even before a capture is configured — used for an "output"
   * attribute (e.g. a Save button), where capturing a result is the expected next
   * step rather than an edge case worth hiding behind a details toggle. */
  defaultOpen?: boolean;
}) {
  const [patterns, setPatterns] = useState<string[]>([]);
  const enabled = value !== null;

  useEffect(() => {
    api.listMessagePatterns().then(setPatterns).catch(() => setPatterns([]));
  }, []);

  const set = (patch: Partial<CaptureSpec>) => {
    if (!value) return;
    onChange({ ...value, ...patch });
  };

  return (
    <details className="details-advanced" open={enabled || defaultOpen}>
      <summary>Capture (optional) {enabled && `· buffer "${value.buffer || "…"}"`}</summary>
      <div style={{ marginTop: 12 }}>
        <label>
          <input
            type="checkbox"
            checked={enabled}
            onChange={(e) => onChange(e.target.checked ? { buffer: "", from: "actual_value", pattern: null } : null)}
          />{" "}
          Capture this step's outcome into a named buffer
        </label>

        {value && (
          <>
            <div className="field" style={{ marginTop: 8 }}>
              <label htmlFor="capture-buffer">Buffer key</label>
              <input
                id="capture-buffer"
                type="text"
                value={value.buffer}
                onChange={(e) => set({ buffer: e.target.value })}
                placeholder="e.g. order_number"
              />
            </div>
            <div className="radio-row">
              {(["actual_value", "statusbar"] as CaptureFrom[]).map((from) => (
                <label key={from}>
                  <input type="radio" name="capture-from" checked={value.from === from} onChange={() => set({ from })} />
                  {from === "actual_value" ? "This step's own result" : "Statusbar message"}
                </label>
              ))}
            </div>
            {value.from === "statusbar" && (
              <div className="field" style={{ marginTop: 8 }}>
                <label htmlFor="capture-pattern">Message pattern</label>
                <select id="capture-pattern" value={value.pattern ?? ""} onChange={(e) => set({ pattern: e.target.value })}>
                  <option value="" disabled>
                    choose a pattern…
                  </option>
                  {patterns.map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </>
        )}
      </div>
    </details>
  );
}
