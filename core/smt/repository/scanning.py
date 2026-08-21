"""Turns a live ScanScreen snapshot into a persisted Module + ModuleAttributes (spec §3),
so a screen only needs to be scanned once and can then be referenced by semantic name from
any TestCase — the missing link between the engine (proven to work end-to-end) and a
reusable, authorable test asset.
"""

from __future__ import annotations

import re

from sqlalchemy.orm import Session, sessionmaker

from smt.adapter.generated import uiadapter_pb2 as pb
from smt.adapter.port import UiAgentPort
from smt.repository.models import Module, ModuleAttribute

WND0 = "wnd[0]"
OKCD = f"{WND0}/tbar[0]/okcd"

# Informational only (spec §5 families) — the agent is the source of truth on what an
# op actually supports; an unsupported combination just fails clearly at execution time.
_FAMILY_ACTIONS = {
    pb.FAMILY_TEXT_INPUT: "READ,SET,VERIFY",
    pb.FAMILY_SELECTION: "READ,SELECT",
    pb.FAMILY_ACTION: "PRESS,SET,READ,MENU_SELECT",
    pb.FAMILY_WINDOW: "SEND_VKEY,WINDOW_CLOSE,WINDOW_MAXIMIZE,VERIFY",
    pb.FAMILY_STATUSBAR: "STATUSBAR_READ,STATUSBAR_OPEN_LONG_TEXT",
    pb.FAMILY_ALV_GRID: "GRID_GET_CELL",
    pb.FAMILY_STRUCTURE: "READ,VERIFY,TAB_SELECT",
}


_SESSION_PREFIX = re.compile(r"^.*?/wnd\[")


def _relative_id(full_id: str) -> str:
    """Scanned ids come back as the full `/app/con[x]/ses[y]/wnd[...]` path, tied to one
    specific connection/session index. That breaks reuse across sessions — SAP's FindById
    accepts the short `wnd[0]/...` form just as well (confirmed live), so that's what gets
    persisted; component ids in the repository are portable, not session-pinned."""
    return _SESSION_PREFIX.sub("wnd[", full_id, count=1)


def _semantic_name(node: pb.ComponentNode) -> str:
    raw = node.name or node.id.rsplit("/", 1)[-1]
    slug = re.sub(r"[^a-z0-9]+", "_", raw.lower()).strip("_")
    return slug or "unnamed"


def _walk(node: pb.ComponentNode):
    yield node
    for child in node.children:
        yield from _walk(child)


def scan_module(
    agent: UiAgentPort,
    handle: pb.SessionHandle,
    session_factory: sessionmaker[Session],
    *,
    module_name: str,
    tcode: str,
    root_id: str = WND0,
    navigate: bool = True,
    prefill: dict[str, str] | None = None,
    vkeys_before_scan: list[str] | None = None,
) -> tuple[str, int]:
    """Navigates to `tcode` (unless already there), optionally fills `prefill` fields and
    sends `vkeys_before_scan` (e.g. ["Enter"] to reach a second screen), scans `root_id`,
    and persists it as a Module. Re-scanning an existing module name replaces it.
    Returns (module_id, attribute_count).
    """
    if navigate:
        agent.execute_action(pb.ActionRequest(session_id=handle.session_id, component_id=OKCD, op=pb.SET,
                                               params=pb.ActionParams(text_value=f"/n{tcode}")))
        agent.execute_action(pb.ActionRequest(session_id=handle.session_id, component_id=WND0, op=pb.SEND_VKEY,
                                               params=pb.ActionParams(vkey="Enter")))

    for component_id, value in (prefill or {}).items():
        agent.execute_action(pb.ActionRequest(session_id=handle.session_id, component_id=component_id, op=pb.SET,
                                               params=pb.ActionParams(text_value=value)))
    for vkey in vkeys_before_scan or []:
        agent.execute_action(pb.ActionRequest(session_id=handle.session_id, component_id=WND0, op=pb.SEND_VKEY,
                                               params=pb.ActionParams(vkey=vkey)))

    snapshot = agent.scan_screen(pb.ScanRequest(session_id=handle.session_id, root_id=root_id))

    with session_factory() as db:
        existing = db.query(Module).filter_by(name=module_name).one_or_none()
        if existing:
            db.delete(existing)
            db.flush()

        module = Module(
            name=module_name,
            tcode=tcode,
            screen_number=snapshot.context.screen_number,
            root_id=root_id,
        )
        db.add(module)

        count = 0
        seen_names: set[str] = set()
        for node in _walk(snapshot.root):
            if not node.id:
                continue
            semantic = _semantic_name(node)
            if semantic in seen_names:
                semantic = f"{semantic}_{node.id.split('/')[-1]}"
            seen_names.add(semantic)
            db.add(ModuleAttribute(
                module=module,
                semantic_name=semantic,
                component_id=_relative_id(node.id),
                sap_type=node.type,
                sap_sub_type=node.sub_type,
                label=node.text or node.tooltip,
                supported_action_modes=_FAMILY_ACTIONS.get(node.family, ""),
            ))
            count += 1

        db.commit()
        return module.id, count
