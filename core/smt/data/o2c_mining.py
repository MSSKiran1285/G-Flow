"""Mines Order-to-Cash master data (order types, sales org / distribution channel /
division) off the VA01 initial screen using F4 value help, for use as test data in O2C
test cases (VA01 -> VL01N -> VF01 per spec §9).

Run: `smt mine-o2c --target localhost:50051 --out core/data/o2c_master_data.json`
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from smt.adapter.generated import uiadapter_pb2 as pb
from smt.adapter.port import UiAgentPort
from smt.data.f4_miner import mine_simple_f4

WND0 = "wnd[0]"
OKCD = f"{WND0}/tbar[0]/okcd"
USR = f"{WND0}/usr"


def _navigate(agent: UiAgentPort, handle: pb.SessionHandle, tcode: str) -> pb.SessionInfo:
    agent.execute_action(pb.ActionRequest(session_id=handle.session_id, component_id=OKCD, op=pb.SET,
                                           params=pb.ActionParams(text_value=f"/n{tcode}")))
    agent.execute_action(pb.ActionRequest(session_id=handle.session_id, component_id=WND0, op=pb.SEND_VKEY,
                                           params=pb.ActionParams(vkey="Enter")))
    return agent.get_session_info(handle)


def mine_o2c_master_data(agent: UiAgentPort, connection_id: str) -> dict:
    handle = agent.open_session(pb.OpenSessionRequest(connection_id=connection_id))
    info = _navigate(agent, handle, "VA01")
    if info.context.transaction_code != "VA01":
        raise RuntimeError(f"expected to land on VA01, got {info.context.transaction_code!r}")

    result = {
        "source_system": info.context.system_id,
        "order_types": [asdict(e) for e in mine_simple_f4(agent, handle, f"{USR}/ctxtVBAK-AUART")],
        "sales_organizations": [asdict(e) for e in mine_simple_f4(agent, handle, f"{USR}/ctxtVBAK-VKORG")],
        "distribution_channels": [asdict(e) for e in mine_simple_f4(agent, handle, f"{USR}/ctxtVBAK-VTWEG")],
        "divisions": [asdict(e) for e in mine_simple_f4(agent, handle, f"{USR}/ctxtVBAK-SPART")],
    }
    agent.close_session(handle)
    return result


def main() -> None:
    import argparse

    from smt.adapter.client import UiAgentClient

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default="localhost:50051")
    parser.add_argument("--out", default="core/data/o2c_master_data.json")
    args = parser.parse_args()

    with UiAgentClient(args.target) as agent:
        connection = agent.list_connections().connections[0]
        data = mine_o2c_master_data(agent, connection.connection_id)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"wrote {out_path} ({sum(len(v) for v in data.values() if isinstance(v, list))} entries)")


if __name__ == "__main__":
    main()
