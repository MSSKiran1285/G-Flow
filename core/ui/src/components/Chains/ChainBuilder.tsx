import { ArrowDown, ArrowUp, Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { api, ApiError } from "../../api";
import type { RowResultOut, TestCaseSummary } from "../../types";
import { DataGridEditor, type GridRows } from "../Data/DataGridEditor";
import { RunResultsPanel } from "../Runs/RunResultsPanel";

interface Stage {
  key: string;
  testCaseName: string;
  rows: GridRows;
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
    setStages((prev) => [...prev, { key: newKey(), testCaseName: "", rows: [] }]);
  };

  const removeStage = (key: string) => setStages((prev) => prev.filter((s) => s.key !== key));

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

  const canRun = stages.length > 0 && stages.every((s) => s.testCaseName && s.rows.length > 0);

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Chain builder</h2>
        <span className="breadcrumb">Runs several scripts in order, sharing one buffer per row — mirrors run_chain</span>
      </div>
      <div className="panel-body">
        {error && <div className="error-banner">{error}</div>}

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
                  onChange={(e) =>
                    setStages((prev) => prev.map((s) => (s.key === stage.key ? { ...s, testCaseName: e.target.value } : s)))
                  }
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
