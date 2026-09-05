"""Turns a live ScanScreen snapshot into a persisted Module + ModuleAttributes (spec §3),
so a screen only needs to be scanned once and can then be referenced by semantic name from
any TestCase — the missing link between the engine (proven to work end-to-end) and a
reusable, authorable test asset.

A full screen scan can easily surface hundreds of components (menu items, every toolbar
button, ...) that nobody wants as a permanent Module attribute. `scan_screen_preview`
does the live navigate+scan and returns the full candidate list *without* touching the
repository at all; `save_module` persists exactly the (possibly renamed, possibly
filtered) attributes the caller chooses. `scan_module` is kept as the original
all-in-one behavior (preview then save everything) for backward compatibility with the
CLI's `scan-module` command and any batch/quick-scan use — the script-builder UI drives
the two halves separately so a tester can pick and choose.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

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
_WINDOW_PREFIX = re.compile(r"^(wnd\[\d+\])")


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


def _window_of(relative_id: str) -> str:
    match = _WINDOW_PREFIX.match(relative_id)
    return match.group(1) if match else relative_id


def _walk(node: pb.ComponentNode):
    yield node
    for child in node.children:
        yield from _walk(child)


@dataclass
class ScannedComponent:
    """One candidate component from a live preview scan — nothing persisted yet."""

    component_id: str
    window: str
    semantic_name: str
    sap_type: str
    sap_sub_type: str
    label: str
    supported_action_modes: list[str] = field(default_factory=list)


def scan_screen_preview(
    agent: UiAgentPort,
    handle: pb.SessionHandle,
    *,
    tcode: str,
    root_id: str = WND0,
    navigate: bool = True,
    prefill: dict[str, str] | None = None,
    vkeys_before_scan: list[str] | None = None,
) -> tuple[str, list[ScannedComponent]]:
    """Navigates to `tcode` (unless already there), optionally fills `prefill` fields and
    sends `vkeys_before_scan` (e.g. ["Enter"] to reach a second screen), scans `root_id`,
    and returns every candidate component found — read-only, nothing persisted. Returns
    (screen_number, components)."""
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

    components: list[ScannedComponent] = []
    seen_names: set[str] = set()
    for node in _walk(snapshot.root):
        if not node.id:
            continue
        semantic = _semantic_name(node)
        if semantic in seen_names:
            semantic = f"{semantic}_{node.id.split('/')[-1]}"
        seen_names.add(semantic)
        relative_id = _relative_id(node.id)
        components.append(ScannedComponent(
            component_id=relative_id,
            window=_window_of(relative_id),
            semantic_name=semantic,
            sap_type=node.type,
            sap_sub_type=node.sub_type,
            label=node.text or node.tooltip,
            supported_action_modes=[m for m in _FAMILY_ACTIONS.get(node.family, "").split(",") if m],
        ))

    return snapshot.context.screen_number, components


def _as_dict(attr: "ScannedComponent | dict") -> dict:
    if isinstance(attr, dict):
        return attr
    return {
        "semantic_name": attr.semantic_name, "component_id": attr.component_id,
        "sap_type": attr.sap_type, "sap_sub_type": attr.sap_sub_type, "label": attr.label,
        "supported_action_modes": attr.supported_action_modes,
    }


def save_module(
    session_factory: sessionmaker[Session],
    *,
    module_name: str,
    tcode: str,
    root_id: str,
    screen_number: str = "",
    attributes: list[ScannedComponent] | list[dict],
) -> tuple[str, int]:
    """Persists a Module with exactly the given attributes — the curated (possibly
    filtered, possibly renamed) subset of a scan_screen_preview result. Re-saving an
    existing module name replaces it. Returns (module_id, attribute_count)."""
    with session_factory() as db:
        existing = db.query(Module).filter_by(name=module_name).one_or_none()
        if existing:
            db.delete(existing)
            db.flush()

        module = Module(name=module_name, tcode=tcode, screen_number=screen_number, root_id=root_id)
        db.add(module)

        count = 0
        for raw in attributes:
            attr = _as_dict(raw)
            modes = attr.get("supported_action_modes") or []
            db.add(ModuleAttribute(
                module=module,
                semantic_name=attr["semantic_name"],
                component_id=attr["component_id"],
                sap_type=attr.get("sap_type", ""),
                sap_sub_type=attr.get("sap_sub_type", ""),
                label=attr.get("label", ""),
                supported_action_modes=",".join(modes) if isinstance(modes, list) else (modes or ""),
            ))
            count += 1

        db.commit()
        return module.id, count


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
    """All-in-one scan + persist-everything, kept for the CLI's `scan-module` command
    and any batch/quick-scan use. The script-builder UI instead drives
    scan_screen_preview + save_module separately so a tester can pick and choose which
    fields/buttons actually become Module attributes, rather than persisting the entire
    screen. Returns (module_id, attribute_count)."""
    screen_number, components = scan_screen_preview(
        agent, handle, tcode=tcode, root_id=root_id, navigate=navigate,
        prefill=prefill, vkeys_before_scan=vkeys_before_scan,
    )
    return save_module(
        session_factory, module_name=module_name, tcode=tcode, root_id=root_id,
        screen_number=screen_number, attributes=components,
    )
