"""Mines Procure-to-Pay master data (vendors) off the ME21N initial screen, for use as
test data in P2P test cases (ME21N -> MIGO -> MIRO per spec §9).

The vendor field's F4 help is a multi-step flow (a "Restrict Value Range" search dialog
first, then the actual hit list) rather than the single-shot popup f4_miner.mine_simple_f4
handles — confirmed live, so implemented directly here rather than forced into that
generic helper. Purchasing org/purchasing group are NOT mined yet: on this system they
live on ME21N's Org. Data sub-tab as plain fields, not surfaced on the initial view scanned
so far — a gap to close, not a limitation of the approach.

Run: `smt mine-p2p --target localhost:50051 --out core/data/p2p_master_data.json`
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path

from smt.adapter.generated import uiadapter_pb2 as pb
from smt.adapter.port import UiAgentPort
from smt.data.f4_miner import MasterDataEntry, _read_label_grid, _top_window_id

WND0 = "wnd[0]"
OKCD = f"{WND0}/tbar[0]/okcd"
VENDOR_FIELD = (
    f"{WND0}/usr/subSUB0:SAPLMEGUI:0013/subSUB0:SAPLMEGUI:0030"
    "/subSUB1:SAPLMEGUI:1105/ctxtMEPO_TOPLINE-SUPERFIELD"
)


def _navigate(agent: UiAgentPort, handle: pb.SessionHandle, tcode: str) -> pb.SessionInfo:
    agent.execute_action(pb.ActionRequest(session_id=handle.session_id, component_id=OKCD, op=pb.SET,
                                           params=pb.ActionParams(text_value=f"/n{tcode}")))
    agent.execute_action(pb.ActionRequest(session_id=handle.session_id, component_id=WND0, op=pb.SEND_VKEY,
                                           params=pb.ActionParams(vkey="Enter")))
    return agent.get_session_info(handle)


def mine_vendors(agent: UiAgentPort, handle: pb.SessionHandle, max_entries: int = 500) -> list[MasterDataEntry]:
    agent.execute_action(pb.ActionRequest(session_id=handle.session_id, component_id=VENDOR_FIELD, op=pb.SET_FOCUS))
    agent.execute_action(pb.ActionRequest(session_id=handle.session_id, component_id=WND0, op=pb.SEND_VKEY,
                                           params=pb.ActionParams(vkey="F4")))

    search_dialog_id = _top_window_id(agent, handle)
    if search_dialog_id is None:
        return []

    # "Restrict Value Range" dialog: accept whatever MAXRECORDS default is already set
    # and continue straight to the hit list.
    agent.execute_action(pb.ActionRequest(session_id=handle.session_id, component_id=search_dialog_id, op=pb.SEND_VKEY,
                                           params=pb.ActionParams(vkey="Enter")))

    hitlist_id = _top_window_id(agent, handle)
    if hitlist_id is None:
        return []

    rows = _read_label_grid(agent, handle, hitlist_id)
    header_row = min(rows) if rows else None
    # Column layout confirmed live: 1=SearchTerm, 12=Country, 16=PostalCode, 27=City,
    # 53=Name, 79=Vendor (the actual key) — VERIFY-ON-TARGET on other systems/themes.
    # Not using rows_to_entries here: it joins every non-key column into the
    # description, but this table has several unrelated columns (country/postal/city)
    # we don't want mixed in — only the Name column (53) is wanted.
    key_col, name_col = 79, 53

    entries: list[MasterDataEntry] = []
    for row in sorted(rows):
        if row == header_row:
            continue
        cols = rows[row]
        vendor = cols.get(key_col, "").strip()
        if not vendor:
            continue
        entries.append(MasterDataEntry(key=vendor, description=cols.get(name_col, "").strip()))
        if len(entries) >= max_entries:
            break

    try:
        agent.execute_action(pb.ActionRequest(session_id=handle.session_id, component_id=hitlist_id, op=pb.SEND_VKEY,
                                               params=pb.ActionParams(vkey="F12")))
    except Exception:
        pass

    return entries


def mine_p2p_master_data(agent: UiAgentPort, connection_id: str) -> dict:
    handle = agent.open_session(pb.OpenSessionRequest(connection_id=connection_id))
    info = _navigate(agent, handle, "ME21N")
    if info.context.transaction_code != "ME21N":
        raise RuntimeError(f"expected to land on ME21N, got {info.context.transaction_code!r}")

    result = {
        "source_system": info.context.system_id,
        "vendors": [asdict(e) for e in mine_vendors(agent, handle)],
    }
    agent.close_session(handle)
    return result


def main() -> None:
    import argparse

    from smt.adapter.client import UiAgentClient

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default="localhost:50051")
    parser.add_argument("--out", default="core/data/p2p_master_data.json")
    args = parser.parse_args()

    with UiAgentClient(args.target) as agent:
        connection = agent.list_connections().connections[0]
        data = mine_p2p_master_data(agent, connection.connection_id)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"wrote {out_path} ({sum(len(v) for v in data.values() if isinstance(v, list))} entries)")


if __name__ == "__main__":
    main()
