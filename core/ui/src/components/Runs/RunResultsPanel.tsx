import type { RowResultOut } from "../../types";

function StatusBadge({ success }: { success: boolean }) {
  return (
    <span className={`status-badge ${success ? "status-pass" : "status-fail"}`}>
      {success ? "PASS" : "FAIL"}
    </span>
  );
}

function BufferTable({ buffer }: { buffer: Record<string, string> }) {
  const entries = Object.entries(buffer);
  if (entries.length === 0) return null;
  return (
    <table className="data-table" style={{ marginTop: 8 }}>
      <thead>
        <tr>
          <th>captured key</th>
          <th>value</th>
        </tr>
      </thead>
      <tbody>
        {entries.map(([key, value]) => (
          <tr key={key}>
            <td>{key}</td>
            <td>{value}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function RowResultCard({ result }: { result: RowResultOut }) {
  return (
    <div className="panel" style={{ marginBottom: 12 }}>
      <div className="panel-header">
        <span>
          {result.test_case_name} — row {result.row_index + 1}
          {result.failed_at_step !== null && !result.success && (
            <span style={{ color: "var(--status-fail-text)" }}> (failed at step {result.failed_at_step + 1})</span>
          )}
        </span>
        <StatusBadge success={result.success} />
      </div>
      <div className="panel-body">
        <div style={{ font: "var(--text-code)" }}>{result.message || <em>(no statusbar message)</em>}</div>
        <BufferTable buffer={result.buffer} />
      </div>
    </div>
  );
}

/** Renders either a single TestCase run (RowResultOut[]) or a Chain run
 * (RowResultOut[][], one array per data row, each containing one entry per stage) —
 * the direct visual proof that e.g. a PO number fed into MIGO, a material document
 * fed into MIRO. */
export function RunResultsPanel({ results }: { results: RowResultOut[] | RowResultOut[][] }) {
  if (results.length === 0) {
    return <p className="empty-state">No results yet — run the script to see output here.</p>;
  }

  const isChain = Array.isArray(results[0]);

  if (!isChain) {
    return (
      <div>
        {(results as RowResultOut[]).map((r) => (
          <RowResultCard key={`${r.test_case_name}-${r.row_index}`} result={r} />
        ))}
      </div>
    );
  }

  return (
    <div>
      {(results as RowResultOut[][]).map((row, rowIndex) => (
        <div key={rowIndex} style={{ marginBottom: 20 }}>
          <div className="breadcrumb" style={{ marginBottom: 8 }}>Chain run — row {rowIndex + 1}</div>
          {row.map((stage) => (
            <RowResultCard key={`${stage.test_case_name}-${stage.row_index}`} result={stage} />
          ))}
        </div>
      ))}
    </div>
  );
}
