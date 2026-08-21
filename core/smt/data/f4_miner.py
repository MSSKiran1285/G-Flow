"""Mines valid master-data values out of SAP GUI's own F4 value-help popups, rather than
guessing test data or requiring a separate master-data extract. Works for any dynpro field
whose F4 help renders as a plain positional grid of GuiLabels (`lbl[col,row]`) — which
covers most simple single-step F4 popups (order type, sales org, distribution channel,
division, ...). Confirmed against a live system; see docs/assumptions.md.

Deliberately does NOT depend on GuiShell/ALV support (not implemented until M2) — SAP
renders these particular popups as plain dynpro labels, which M1 already handles fully.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from smt.adapter.generated import uiadapter_pb2 as pb
from smt.adapter.port import UiAgentPort

_LABEL_CELL = re.compile(r"/lbl\[(\d+),(\d+)\]$")
_WINDOW_PREFIX = re.compile(r"^(.*?wnd\[\d+\])")


@dataclass(frozen=True)
class MasterDataEntry:
    key: str
    description: str


def _top_window_id(agent: UiAgentPort, handle: pb.SessionHandle) -> str | None:
    info = agent.get_session_info(handle)
    if info.context.window_count < 2:
        return None
    return f"wnd[{info.context.window_count - 1}]"


def _read_label_grid(agent: UiAgentPort, handle: pb.SessionHandle, root_id: str) -> dict[int, dict[int, str]]:
    snapshot = agent.scan_screen(pb.ScanRequest(session_id=handle.session_id, root_id=root_id))
    rows: dict[int, dict[int, str]] = {}

    def walk(node: pb.ComponentNode) -> None:
        if node.type == "GuiLabel":
            m = _LABEL_CELL.search(node.id)
            if m:
                col, row = int(m.group(1)), int(m.group(2))
                rows.setdefault(row, {})[col] = node.text
        for child in node.children:
            walk(child)

    walk(snapshot.root)
    return rows


def mine_simple_f4(
    agent: UiAgentPort,
    handle: pb.SessionHandle,
    field_id: str,
    *,
    key_column: int | None = None,
    max_entries: int = 500,
) -> list[MasterDataEntry]:
    """Focus `field_id`, press F4, read the resulting plain-label popup, close it.

    `key_column` picks which grid column is the key; the lowest column present in the
    header row (usually the leftmost) is used when omitted. Returns [] if F4 opened
    nothing recognizable (a real ALV/GuiShell popup, a nested search dialog, or F4 simply
    not being wired for that field) — callers should treat that as "not minable this way"
    rather than as an error.
    """
    agent.execute_action(pb.ActionRequest(session_id=handle.session_id, component_id=field_id, op=pb.SET_FOCUS))
    agent.execute_action(pb.ActionRequest(
        session_id=handle.session_id,
        component_id=_window_of(field_id),
        op=pb.SEND_VKEY,
        params=pb.ActionParams(vkey="F4"),
    ))

    popup_id = _top_window_id(agent, handle)
    if popup_id is None:
        return []

    rows = _read_label_grid(agent, handle, popup_id)
    entries = rows_to_entries(rows, key_column=key_column, max_entries=max_entries)

    # Best-effort close (F12/Cancel) so the underlying screen is left untouched.
    try:
        agent.execute_action(pb.ActionRequest(session_id=handle.session_id, component_id=popup_id, op=pb.SEND_VKEY, params=pb.ActionParams(vkey="F12")))
    except Exception:
        pass

    return entries


def rows_to_entries(
    rows: dict[int, dict[int, str]],
    *,
    key_column: int | None = None,
    max_entries: int = 500,
) -> list[MasterDataEntry]:
    """Pure parsing step, split out from mine_simple_f4 so it's testable without a live
    agent: turns a {row: {col: text}} grid (as read off a plain-label F4 popup) into
    entries, skipping the header row and any row missing the key column."""
    entries: list[MasterDataEntry] = []
    header_row = min(rows) if rows else None
    key_col = key_column if key_column is not None else (
        min(rows[header_row]) if header_row is not None and rows[header_row] else None
    )

    for row in sorted(rows):
        if row == header_row:
            continue
        cols = rows[row]
        if not cols or key_col not in cols or not cols[key_col]:
            continue
        desc = " ".join(v for c, v in sorted(cols.items()) if c != key_col and v).strip()
        entries.append(MasterDataEntry(key=cols[key_col], description=desc))
        if len(entries) >= max_entries:
            break

    return entries


def _window_of(field_id: str) -> str:
    """The wnd[N] segment a field id lives under — SEND_VKEY targets the window, since
    SAP resolves it against whatever currently has focus, not an arbitrary component."""
    match = _WINDOW_PREFIX.search(field_id)
    if not match:
        raise ValueError(f"not a component id under a wnd[..]: {field_id!r}")
    return match.group(1)
