import { Copy, Pencil, Plus, Trash2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { api, ApiError } from "../../api";
import { BINDING_CONSUMING_ACTIONS, type RowResultOut, type StepSpec, type TestCaseDetail } from "../../types";
import { blankRow, dataColumnsOf } from "../../utils";
import { DataGridEditor, type GridRows } from "../Data/DataGridEditor";
import { RunResultsPanel } from "../Runs/RunResultsPanel";
import { StepEditorDialog } from "./StepEditorDialog";

let nextKey = 0;
function newKey() {
  nextKey += 1;
  return `step-${nextKey}`;
}

interface KeyedStep {
  key: string;
  step: StepSpec;
}

function stepFromOut(detail: TestCaseDetail): KeyedStep[] {
  return detail.steps.map((s) => ({
    key: newKey(),
    step: {
      module: s.module_name || null,
      attribute: s.attribute_semantic_name || null,
      component_id: s.raw_component_id || null,
      action: s.action_mode,
      binding: { type: s.binding_type, value: s.binding_value },
      row_binding: { type: s.row_binding_type, value: s.row_binding_value },
      optional: s.optional,
      capture: s.capture_buffer_key
        ? { buffer: s.capture_buffer_key, from: s.capture_from, pattern: s.capture_pattern || null }
        : null,
    },
  }));
}

function summarizeTarget(step: StepSpec): string {
  if (step.component_id) return step.component_id;
  if (step.module && step.attribute) return `${step.module}.${step.attribute}`;
  return "(not set)";
}

export function TestCaseEditor({ name, onClose }: { name: string | null; onClose: () => void }) {
  const [caseName, setCaseName] = useState(name ?? "");
  const [description, setDescription] = useState("");
  const [steps, setSteps] = useState<KeyedStep[]>([]);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [dialogFor, setDialogFor] = useState<{ key: string | null } | null>(null); // null = closed, key null = adding
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [announcement, setAnnouncement] = useState("");

  const [gridRows, setGridRows] = useState<GridRows>([]);
  const [results, setResults] = useState<RowResultOut[]>([]);
  const [running, setRunning] = useState(false);

  const dragIndex = useRef<number | null>(null);
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null);

  useEffect(() => {
    if (!name) return;
    api.getTestCase(name).then((detail) => {
      setCaseName(detail.name);
      setDescription(detail.description);
      setSteps(stepFromOut(detail));
      const columns = dataColumnsOf(detail);
      if (columns.length) setGridRows([blankRow(columns)]);
    }).catch(() => undefined);
  }, [name]);

  const reorder = (from: number, to: number) => {
    if (to < 0 || to >= steps.length) return;
    setSteps((prev) => {
      const next = [...prev];
      const [moved] = next.splice(from, 1);
      next.splice(to, 0, moved);
      return next;
    });
    setAnnouncement(`Moved step ${from + 1} to position ${to + 1}`);
  };

  const selectedIndex = steps.findIndex((s) => s.key === selectedKey);

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      await api.defineTestCase({ name: caseName, description, steps: steps.map((s) => s.step) });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const run = async () => {
    setRunning(true);
    setError(null);
    try {
      const response = await api.runTestCase(caseName, gridRows);
      setResults(response.results);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Run failed");
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>{name ? "Edit script" : "New script"}</h2>
        <div className="toolbar" style={{ border: "none", padding: 0 }}>
          <button className="btn" onClick={onClose}>
            Back
          </button>
          <button className="btn btn-primary" disabled={!caseName || saving} onClick={save}>
            {saving ? "Saving…" : "Save script"}
          </button>
        </div>
      </div>
      <div className="panel-body">
        {error && <div className="error-banner">{error}</div>}

        <div className="field">
          <label htmlFor="case-name">Name</label>
          <input id="case-name" type="text" value={caseName} onChange={(e) => setCaseName(e.target.value)} disabled={Boolean(name)} />
        </div>
        <div className="field">
          <label htmlFor="case-description">Description</label>
          <input id="case-description" type="text" value={description} onChange={(e) => setDescription(e.target.value)} />
        </div>

        <span role="status" aria-live="polite" className="sr-only">
          {announcement}
        </span>

        <div className="toolbar">
          <button
            className="btn"
            disabled={selectedIndex < 0}
            onClick={() => selectedIndex >= 0 && setDialogFor({ key: steps[selectedIndex].key })}
          >
            <Pencil size={14} /> Edit
          </button>
          <button
            className="btn"
            disabled={selectedIndex < 0}
            onClick={() => {
              if (selectedIndex < 0) return;
              const copy: KeyedStep = { key: newKey(), step: { ...steps[selectedIndex].step } };
              setSteps((prev) => {
                const next = [...prev];
                next.splice(selectedIndex + 1, 0, copy);
                return next;
              });
            }}
          >
            <Copy size={14} /> Duplicate
          </button>
          <button
            className="btn btn-danger"
            disabled={selectedIndex < 0}
            onClick={() => {
              setSteps((prev) => prev.filter((_, i) => i !== selectedIndex));
              setSelectedKey(null);
            }}
          >
            <Trash2 size={14} /> Remove
          </button>
          <button className="btn btn-primary" onClick={() => setDialogFor({ key: null })}>
            <Plus size={14} /> Add step
          </button>
        </div>

        <div className="table-frame">
          <table className="data-table">
            <thead>
              <tr>
                <th />
                <th />
                <th>#</th>
                <th>Target</th>
                <th>Action</th>
                <th>Data</th>
              </tr>
            </thead>
            <tbody>
              {steps.map(({ key, step }, index) => (
                <tr
                  key={key}
                  className={[selectedKey === key ? "selected" : "", dragOverIndex === index ? "drag-over" : ""].join(" ").trim()}
                  draggable
                  onClick={() => setSelectedKey(key)}
                  onDragStart={() => {
                    dragIndex.current = index;
                  }}
                  onDragOver={(e) => {
                    e.preventDefault();
                    setDragOverIndex(index);
                  }}
                  onDragLeave={() => setDragOverIndex(null)}
                  onDrop={(e) => {
                    e.preventDefault();
                    if (dragIndex.current !== null) reorder(dragIndex.current, index);
                    dragIndex.current = null;
                    setDragOverIndex(null);
                  }}
                  onDragEnd={() => {
                    dragIndex.current = null;
                    setDragOverIndex(null);
                  }}
                >
                  <td>
                    <button
                      className="drag-handle"
                      aria-label={`Reorder step ${index + 1}`}
                      onKeyDown={(e) => {
                        if (e.key === "ArrowUp") {
                          e.preventDefault();
                          reorder(index, index - 1);
                        } else if (e.key === "ArrowDown") {
                          e.preventDefault();
                          reorder(index, index + 1);
                        }
                      }}
                    >
                      ⠿
                    </button>
                  </td>
                  <td>
                    <input type="radio" checked={selectedKey === key} onChange={() => setSelectedKey(key)} aria-label={`Select step ${index + 1}`} />
                  </td>
                  <td>{index + 1}</td>
                  <td style={{ font: "var(--text-code)" }}>{summarizeTarget(step)}</td>
                  <td>{step.action}</td>
                  <td>
                    <div style={{ display: "flex", flexDirection: "column", gap: 4, alignItems: "flex-start" }}>
                      {(BINDING_CONSUMING_ACTIONS as readonly string[]).includes(step.action) && (
                        <span className={`chip chip-${step.binding.type}`}>
                          Input: {step.binding.type}
                          {step.binding.value ? `:${step.binding.value}` : ""}
                        </span>
                      )}
                      {step.capture && (
                        <span className="chip chip-buffer">
                          Output: buffer:{step.capture.buffer || "…"}
                          {step.capture.from === "statusbar" && step.capture.pattern
                            ? ` (${step.capture.pattern})`
                            : ""}
                        </span>
                      )}
                      {!(BINDING_CONSUMING_ACTIONS as readonly string[]).includes(step.action) && !step.capture && (
                        <span className="breadcrumb">—</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {steps.length === 0 && (
                <tr>
                  <td className="empty-state" colSpan={6}>No steps yet — add one above.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <h3 style={{ marginTop: 32 }}>Run</h3>
        <DataGridEditor rows={gridRows} onChange={setGridRows} />
        <div className="toolbar" style={{ border: "none", paddingLeft: 0 }}>
          <button className="btn btn-primary" disabled={!caseName || running || gridRows.length === 0} onClick={run}>
            {running ? "Running…" : "Run script"}
          </button>
        </div>
        <RunResultsPanel results={results} />
      </div>

      {dialogFor && (
        <StepEditorDialog
          initial={dialogFor.key ? steps.find((s) => s.key === dialogFor.key)?.step ?? null : null}
          onClose={() => setDialogFor(null)}
          onSave={(step) => {
            if (dialogFor.key) {
              setSteps((prev) => prev.map((s) => (s.key === dialogFor.key ? { ...s, step } : s)));
            } else {
              setSteps((prev) => [...prev, { key: newKey(), step }]);
            }
            setDialogFor(null);
          }}
        />
      )}
    </div>
  );
}
