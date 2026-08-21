"""Reads rows straight out of any SAP table via SE16N — the general-purpose way to mine
*proven-valid* master-data combinations from real historical documents (VBAK/VBAP for
sales orders, LIKP/LIPS for deliveries, VBRK/VBRP for invoices, EKKO/EKPO for purchase
orders, ...) instead of guessing values that satisfy unknown customizing rules.

Confirmed live: SE16N's result list is a GuiShell/GridView (ALV grid) — the M2 family
this framework didn't support until now. `AlvGridHandler` (agent-side) covers exactly the
read path this needs: RowCount/columns on scan, GRID_GET_CELL for cell reads.
"""

from __future__ import annotations

from smt.adapter.generated import uiadapter_pb2 as pb
from smt.adapter.port import UiAgentPort

WND0 = "wnd[0]"
OKCD = f"{WND0}/tbar[0]/okcd"
USR = f"{WND0}/usr"
GRID = f"{USR}/cntlRESULT_LIST/shellcont/shell"


def _action(agent: UiAgentPort, handle: pb.SessionHandle, component_id: str, op, **params) -> pb.ActionResult:
    return agent.execute_action(pb.ActionRequest(
        session_id=handle.session_id, component_id=component_id, op=op,
        params=pb.ActionParams(**params) if params else None,
    ))


def read_table(
    agent: UiAgentPort,
    handle: pb.SessionHandle,
    table_name: str,
    columns: list[str],
    max_rows: int = 100,
) -> list[dict[str, str]]:
    """Opens SE16N for `table_name`, runs the default selection (F8 — whatever variant/
    selection criteria are already defaulted), and reads `columns` for up to `max_rows`
    of the result grid. Returns [] if the table doesn't exist / has no ALV result (e.g.
    an authorization error) rather than raising — callers should treat that as "nothing
    minable here", the same convention as f4_miner.
    """
    _action(agent, handle, OKCD, pb.SET, text_value="/nSE16N")
    _action(agent, handle, WND0, pb.SEND_VKEY, vkey="Enter")
    _action(agent, handle, f"{USR}/ctxtGD-TAB", pb.SET, text_value=table_name)
    _action(agent, handle, WND0, pb.SEND_VKEY, vkey="Enter")
    _action(agent, handle, WND0, pb.SEND_VKEY, vkey="F8")

    info = agent.get_session_info(handle)
    if info.context.transaction_code != "SE16N" or "Display of Entries Found" not in info.context.window_title:
        return []

    rows: list[dict[str, str]] = []
    for row in range(max_rows):
        values: dict[str, str] = {}
        ok = True
        for column in columns:
            result = _action(agent, handle, GRID, pb.GRID_GET_CELL, row=row, column_id=column)
            if not result.success:
                ok = False
                break
            values[column] = result.actual_value
        if not ok:
            break
        rows.append(values)
    return rows


def main() -> None:
    import argparse
    import json

    from smt.adapter.client import UiAgentClient

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("table", help="e.g. VBAK, VBAP, LIKP, LIPS, VBRK, VBRP, EKKO, EKPO")
    parser.add_argument("columns", nargs="+", help="technical field names, e.g. VBELN AUART VKORG")
    parser.add_argument("--target", default="localhost:50051")
    parser.add_argument("--max-rows", type=int, default=20)
    args = parser.parse_args()

    with UiAgentClient(args.target) as agent:
        connection = agent.list_connections().connections[0]
        handle = agent.open_session(pb.OpenSessionRequest(connection_id=connection.connection_id))
        rows = read_table(agent, handle, args.table, args.columns, max_rows=args.max_rows)
        agent.close_session(handle)

    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
