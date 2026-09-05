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
_PREFIX_SUFFIX = re.compile(r"^([a-z]+)([A-Za-z0-9_].*)$")
_TABLE_CELL_BRACKET = re.compile(r"\[(\d+),(\d+)\]$")

# Controls whose own .text (or .tooltip, for icon-only buttons) already IS the descriptive
# English label — mirrors ComponentHitTester.SelfCaptionedTypes on the agent side.
_SELF_CAPTIONED_TYPES = {"GuiButton", "GuiTab", "GuiRadioButton", "GuiCheckBox", "GuiMenu"}


def _relative_id(full_id: str) -> str:
    """Scanned ids come back as the full `/app/con[x]/ses[y]/wnd[...]` path, tied to one
    specific connection/session index. That breaks reuse across sessions — SAP's FindById
    accepts the short `wnd[0]/...` form just as well (confirmed live), so that's what gets
    persisted; component ids in the repository are portable, not session-pinned."""
    return _SESSION_PREFIX.sub("wnd[", full_id, count=1)


def _semantic_name_from(name: str, id_: str) -> str:
    raw = name or id_.rsplit("/", 1)[-1]
    slug = re.sub(r"[^a-z0-9]+", "_", raw.lower()).strip("_")
    return slug or "unnamed"


def _semantic_name(node: pb.ComponentNode) -> str:
    return _semantic_name_from(node.name, node.id)


def _window_of(relative_id: str) -> str:
    match = _WINDOW_PREFIX.match(relative_id)
    return match.group(1) if match else relative_id


def _walk(node: pb.ComponentNode):
    yield node
    for child in node.children:
        yield from _walk(child)


def _caption_by_id(relative_id: str, sap_type: str, label_index: dict[str, str]) -> str:
    """Finds the descriptive caption SAP conventionally renders as a sibling GuiLabel
    next to a value-bearing control — same id suffix, "lbl" prefix instead of the
    control's own (e.g. ctxtVBAK-AUART's caption is lblVBAK-AUART's text; confirmed
    against dozens of real screens this project has scanned). Mirrors
    ComponentHitTester.FindCaptionById on the agent side. Skips table-control cells
    (ids with a "[row,col]" suffix), where this convention doesn't reliably hold."""
    if sap_type == "GuiLabel":
        return ""
    last_slash = relative_id.rfind("/")
    parent_path = relative_id[:last_slash] if last_slash >= 0 else ""
    last_segment = relative_id[last_slash + 1:] if last_slash >= 0 else relative_id
    if "[" in last_segment:
        return ""
    match = _PREFIX_SUFFIX.match(last_segment)
    if not match:
        return ""
    candidate_id = f"{parent_path}/lbl{match.group(2)}"
    return label_index.get(candidate_id, "")


def _caption_by_column(root: pb.ComponentNode, target: pb.ComponentNode) -> str:
    """A classic GuiTableControl cell's id ends "...[col,row]" (confirmed live on VA01's
    item overview table: ctxtRV45A-MABNR[1,3] is column 1, row 3) — column headers sit
    above every data row, not aligned with any one of them, so neither the id nor the
    positional heuristic below finds them. Column index doubles as the lookup key into
    the containing table's table_detail.columns, populated at scan time by the agent's
    TableControlHandler from GuiTableControl.Columns (same left-to-right display order —
    no separate technical-name matching needed). Mirrors
    ComponentHitTester.FindCaptionByColumn."""
    match = _TABLE_CELL_BRACKET.search(target.id)
    if not match:
        return ""
    column_index = int(match.group(1))

    def find_table(node: pb.ComponentNode, nearest_table: pb.ComponentNode | None) -> pb.ComponentNode | None:
        this_table = node if node.type == "GuiTableControl" else nearest_table
        if node is target:
            return this_table
        for child in node.children:
            found = find_table(child, this_table)
            if found is not None:
                return found
        return None

    table = find_table(root, None)
    if table is None:
        return ""
    columns = table.table_detail.columns
    if column_index < 0 or column_index >= len(columns):
        return ""
    return columns[column_index].title


def _is_caption_like(node: pb.ComponentNode) -> bool:
    return node.type == "GuiLabel" or (node.type == "GuiTextField" and not node.changeable)


def _caption_by_position(target: pb.ComponentNode, candidates: list[pb.ComponentNode]) -> str:
    """Fallback for screens where the caption isn't a lbl-prefixed id sibling but an
    unrelated, positionally-adjacent control (confirmed live: VA01's "Order Type"
    caption for VBAK-AUART is actually the read-only GuiTextField RV45A-TXT_AUART, no
    naming relationship at all). Mirrors ComponentHitTester.FindCaptionByPosition:
    nearest caption-like (GuiLabel or non-changeable GuiTextField) node on the same
    row, strictly to the left, preferring the one closest (largest screen_left)."""
    if target.width <= 0 or target.height <= 0:
        return ""
    target_center_y = target.screen_top + target.height / 2.0
    tolerance = target.height / 2.0 + 4

    best: pb.ComponentNode | None = None
    best_left = -1
    for node in candidates:
        if node is target or not _is_caption_like(node) or node.width <= 0 or node.height <= 0:
            continue
        node_center_y = node.screen_top + node.height / 2.0
        if (abs(node_center_y - target_center_y) <= tolerance
                and node.screen_left + node.width <= target.screen_left
                and node.screen_left > best_left):
            best_left = node.screen_left
            best = node
    return best.text if best is not None else ""


@dataclass
class ScannedComponent:
    """One candidate component from a live preview scan — nothing persisted yet."""

    component_id: str
    window: str
    semantic_name: str
    sap_type: str
    sap_sub_type: str
    label: str
    caption: str = ""
    window_title: str = ""
    supported_action_modes: list[str] = field(default_factory=list)


def scanned_component_from_picked(picked: pb.PickedComponent) -> ScannedComponent:
    """Converts one live-picker result (StartElementPicker) into the same shape a full
    scan_screen_preview candidate has, so the UI's picker table can render both the
    same way. Shares _relative_id/_semantic_name_from/_FAMILY_ACTIONS with the
    whole-screen path rather than re-deriving any of it. `caption`/`window_title` were
    already resolved agent-side (it had the live tree in hand at hit-test time) —
    passed through as-is."""
    relative_id = _relative_id(picked.component_id)
    return ScannedComponent(
        component_id=relative_id,
        window=_window_of(relative_id),
        semantic_name=_semantic_name_from(picked.name, relative_id),
        sap_type=picked.type,
        sap_sub_type=picked.sub_type,
        label=picked.text or picked.tooltip,
        caption=picked.caption,
        window_title=picked.window_title,
        supported_action_modes=[m for m in _FAMILY_ACTIONS.get(picked.family, "").split(",") if m],
    )


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

    nodes = [node for node in _walk(snapshot.root) if node.id]
    label_index = {
        _relative_id(node.id): node.text
        for node in nodes
        if node.type == "GuiLabel"
    }
    # A window's own node has a relative id that IS exactly its window id (e.g. "wnd[0]",
    # or "wnd[1]" for a modal when root_id="*") — its .text is that window's real title
    # (e.g. "Create Sales Order: Initial Screen"), letting the UI group captured fields by
    # originating screen/dialog instead of one flat list.
    window_title_index = {
        _relative_id(node.id): node.text
        for node in nodes
        if _relative_id(node.id) == _window_of(_relative_id(node.id))
    }

    components: list[ScannedComponent] = []
    seen_names: set[str] = set()
    for node in nodes:
        semantic = _semantic_name(node)
        if semantic in seen_names:
            semantic = f"{semantic}_{node.id.split('/')[-1]}"
        seen_names.add(semantic)
        relative_id = _relative_id(node.id)
        if node.type == "GuiLabel":
            caption = ""
        elif node.type in _SELF_CAPTIONED_TYPES:
            caption = node.text or node.tooltip
        else:
            caption = _caption_by_id(relative_id, node.type, label_index)
            if not caption:
                caption = _caption_by_column(snapshot.root, node)
            if not caption:
                caption = _caption_by_position(node, nodes)
        components.append(ScannedComponent(
            component_id=relative_id,
            window=_window_of(relative_id),
            semantic_name=semantic,
            sap_type=node.type,
            sap_sub_type=node.sub_type,
            label=node.text or node.tooltip,
            caption=caption,
            window_title=window_title_index.get(_window_of(relative_id), ""),
            supported_action_modes=[m for m in _FAMILY_ACTIONS.get(node.family, "").split(",") if m],
        ))

    return snapshot.context.screen_number, components


def _as_dict(attr: "ScannedComponent | dict") -> dict:
    if isinstance(attr, dict):
        return attr
    return {
        "semantic_name": attr.semantic_name, "component_id": attr.component_id,
        "sap_type": attr.sap_type, "sap_sub_type": attr.sap_sub_type, "label": attr.label,
        "caption": attr.caption, "window_title": attr.window_title,
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
                caption=attr.get("caption", ""),
                window_title=attr.get("window_title", ""),
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
