import { ArrowDown, ArrowUp, Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { api, ApiError } from "../../api";
import type { RowResultOut, TestCaseSummary } from "../../types";
import { type BufferFlow, blankRow, bufferFlowOf, dataColumnsOf } from "../../utils";
import { DataGridEditor, type GridRows } from "../Data/DataGridEditor";
import { RunResultsPanel } from "../Runs/RunResultsPanel";

interface Stage {
  key: string;
  testCaseName: string;
  rows: GridRows;
  bufferFlow: BufferFlow;
}

let nextKey = 0;
function newKey() {
  nextKey += 1;
  return `stage-${nextKey}`;
}

export function ChainBuilder() {
  const [scripts, setScripts] = useState<TestCaseSummary[]>([]);
  const [stages, setStages] = useState<Stage[]>([]);
  const [results, setResults] = useState<RowResultOut[][]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listTestCases().then(setScripts).catch(() => setScripts([]));
  }, []);

  const addStage = () => {
    setStages((prev) => [...prev, { key: newKey(), testCaseName: "", rows: [], bufferFlow: { consumes: [], produces: [] } }]);
  };

  const removeStage = (key: string) => setStages((prev) => prev.filter((s) => s.key !== key));

  const selectScript = async (key: string, testCaseName: string) => {
    setStages((prev) => prev.map((s) => (s.key === key ? { ...s, testCaseName } : s)));
    if (!testCaseName) return;
    try {
      const detail = await api.getTestCase(testCaseName);
      const columns = dataColumnsOf(detail);
      const bufferFlow = bufferFlowOf(detail);
      setStages((prev) =>
        prev.map((s) => (s.key === key ? { ...s, rows: columns.length ? [blankRow(columns)] : [], bufferFlow } : s))
      );
    } catch {
      // script has no known data columns (or fetch failed) — leave the grid empty,
      // the tester can still add columns by hand
    }
  };

  const move = (index: number, delta: number) => {
    setStages((prev) => {
      const to = index + delta;
      if (to < 0 || to >= prev.length) return prev;
      const next = [...prev];
      const [moved] = next.splice(index, 1);
      next.splice(to, 0, moved);
      return next;
    });
  };

  const run = async () => {
    setRunning(true);
    setError(null);
    try {
      const response = await api.runChain(stages.map((s) => ({ test_case_name: s.testCaseName, rows: s.rows })));
      setResults(response.results);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Chain run failed");
    } finally {
      setRunning(false);
    }
  };

  // Every stage runs the same row_index in lockstep (see run_chain_with_rows) — a
  // mismatched row count between stages is always a real authoring mistake, not
  // something the backend can sensibly guess how to reconcile, so it's worth
  // catching here rather than only as a run-time ValueError after clicking Run.
  const rowCountMismatch = stages.length > 1 && new Set(stages.map((s) => s.rows.length)).size > 1;
  const canRun = stages.length > 0 && !rowCountMismatch && stages.every((s) => s.testCaseName && s.rows.length > 0);

  /** Buffers produced by every stage strictly before `index` — what's actually
   * available for that stage to consume, given chain stages run in listed order. */
  const producedBefore = (index: number): Set<string> => {
    const produced = new Set<string>();
    for (let i = 0; i < index; i++) {
      for (const key of stages[i].bufferFlow.produces) produced.add(key);
    }
    return produced;
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Chain builder</h2>
        <span className="breadcrumb">Runs several scripts in order, sharing one buffer per row — mirrors run_chain</span>
      </div>
      <div className="panel-body">
        {error && <div className="error-banner">{error}</div>}
        {rowCountMismatch && (
          <div className="error-banner">
            Stages have different row counts ({stages.map((s, i) => `Stage ${i + 1}: ${s.rows.length}`).join(", ")}) — every
            stage runs the same row index together, so they all need the same number of rows. Add or remove rows until
            they match.
          </div>
        )}

        {stages.map((stage, index) => (
          <div key={stage.key} className="panel" style={{ marginBottom: 16 }}>
            <div className="panel-header">
              <span>Stage {index + 1}</span>
              <div className="toolbar" style={{ border: "none", padding: 0 }}>
                <button className="drag-handle" aria-label="Move up" disabled={index === 0} onClick={() => move(index, -1)}>
                  <ArrowUp size={14} />
                </button>
                <button className="drag-handle" aria-label="Move down" disabled={index === stages.length - 1} onClick={() => move(index, 1)}>
                  <ArrowDown size={14} />
                </button>
                <button className="drag-handle" aria-label="Remove stage" onClick={() => removeStage(stage.key)}>
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
            <div className="panel-body">
              <div className="field">
                <label>Script</label>
                <select
                  value={stage.testCaseName}
                  onChange={(e) => selectScript(stage.key, e.target.value)}
                >
                  <option value="" disabled>
                    choose a script…
                  </option>
                  {scripts.map((s) => (
                    <option key={s.id} value={s.name}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </div>
              {(stage.bufferFlow.consumes.length > 0 || stage.bufferFlow.produces.length > 0) && (
                <div className="field">
                  <label>Buffer data flow</label>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                    {stage.bufferFlow.consumes.map((key) => {
                      const available = producedBefore(index).has(key);
                      return (
                        <span
                          key={`consumes-${key}`}
                          className={`chip ${available ? "chip-buffer" : "status-fail"}`}
                          title={
                            available
                              ? `Filled in automatically from an earlier stage's captured "${key}" — no data column needed`
                              : `No earlier stage produces "${key}" yet — this step will fail at run time. Add a stage before this one whose script captures it, or reorder stages.`
                          }
                        >
                          uses buffer: {key}
                          {!available && " ⚠"}
                        </span>
                      );
                    })}
                    {stage.bufferFlow.produces.map((key) => (
                      <span
                        key={`produces-${key}`}
                        className="chip chip-column"
                        title={`Captured by this script — available to every stage after this one as buffer:${key}`}
                      >
                        produces buffer: {key}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              <DataGridEditor
                rows={stage.rows}
                onChange={(rows) => setStages((prev) => prev.map((s) => (s.key === stage.key ? { ...s, rows } : s)))}
              />
            </div>
          </div>
        ))}

        <div className="toolbar" style={{ border: "none", paddingLeft: 0 }}>
          <button className="btn" onClick={addStage}>
            <Plus size={14} /> Add stage
          </button>
          <button className="btn btn-primary" disabled={!canRun || running} onClick={run}>
            {running ? "Running…" : "Run chain"}
          </button>
        </div>

        <RunResultsPanel results={results} />
      </div>
    </div>
  );
}
