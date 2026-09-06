import { useEffect, useState } from "react";
import { api } from "../../api";
import type { ConnectionsResponse } from "../../types";

export function SapConnectionPill() {
  const [status, setStatus] = useState<ConnectionsResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    const poll = async () => {
      try {
        const result = await api.listConnections();
        if (!cancelled) setStatus(result);
      } catch {
        if (!cancelled) setStatus({ reachable: false, connections: [], error: "API unreachable" });
      }
    };
    poll();
    const id = setInterval(poll, 5000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  if (!status) {
    return <span className="status-badge status-pending">checking…</span>;
  }

  if (!status.reachable || status.connections.length === 0) {
    return (
      <span className="status-badge status-fail" title={status.error ?? "no live SAP connection"}>
        SAP: not connected
      </span>
    );
  }

  const first = status.connections[0];
  return (
    <span className="status-badge status-pass" title={first.connection_id}>
      SAP · {first.description || "connected"}
    </span>
  );
}
