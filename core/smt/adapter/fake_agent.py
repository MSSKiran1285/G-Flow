"""In-process fake of `UiAgentPort` that replays recorded fixtures instead of talking
to a real agent over gRPC. Lets the entire Python core be developed and tested without
SAP GUI or Windows (spec §2).

Fixture format: one JSON file, shaped like
{
  "connections": {...ConnectionList...},
  "open_session": {...SessionHandle...},
  "session_info": {...SessionInfo...},
  "scans": {"<root_id>": {...ScreenSnapshot...}},
  "actions": {"<component_id>|<ActionOp name>": {...ActionResult...}},
  "events": [{...UiEvent...}, ...]
}
using protobuf's canonical JSON mapping (enums as their string names).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

from google.protobuf import json_format

from smt.adapter.generated import uiadapter_pb2 as pb


class FixtureLookupError(KeyError):
    """Raised when a fixture has no recording for the requested call."""


class FakeUiAgent:
    """Implements `UiAgentPort` by replaying a fixture loaded from disk."""

    def __init__(self, fixture_path: str | Path) -> None:
        self._path = Path(fixture_path)
        self._data: dict[str, Any] = json.loads(self._path.read_text(encoding="utf-8"))
        self.events_sent: list[pb.ActionRequest] = []

    def _parse(self, message_cls: type, data: dict[str, Any]):
        return json_format.ParseDict(data, message_cls())

    def list_connections(self) -> pb.ConnectionList:
        return self._parse(pb.ConnectionList, self._data.get("connections", {}))

    def open_session(self, request: pb.OpenSessionRequest) -> pb.SessionHandle:
        if "open_session" not in self._data:
            raise FixtureLookupError(f"{self._path}: no 'open_session' recorded")
        return self._parse(pb.SessionHandle, self._data["open_session"])

    def close_session(self, handle: pb.SessionHandle) -> pb.Ack:
        return pb.Ack(contract_version=handle.contract_version, success=True)

    def get_session_info(self, handle: pb.SessionHandle) -> pb.SessionInfo:
        if "session_info" not in self._data:
            raise FixtureLookupError(f"{self._path}: no 'session_info' recorded")
        return self._parse(pb.SessionInfo, self._data["session_info"])

    def scan_screen(self, request: pb.ScanRequest) -> pb.ScreenSnapshot:
        scans = self._data.get("scans", {})
        key = request.root_id or "wnd[0]"
        if key not in scans:
            raise FixtureLookupError(f"{self._path}: no scan recorded for root_id={key!r}")
        return self._parse(pb.ScreenSnapshot, scans[key])

    def execute_action(self, request: pb.ActionRequest) -> pb.ActionResult:
        actions = self._data.get("actions", {})
        op_name = pb.ActionOp.Name(request.op)
        key = f"{request.component_id}|{op_name}"
        if key not in actions:
            raise FixtureLookupError(f"{self._path}: no action recorded for {key!r}")
        return self._parse(pb.ActionResult, actions[key])

    def execute_batch(self, batch: pb.ActionBatch) -> Iterator[pb.ActionResult]:
        for step in batch.steps:
            result = self.execute_action(step)
            yield result
            if batch.fail_fast and not result.success:
                return

    def resolve_locator(self, request: pb.LocatorRequest) -> pb.LocatorCandidates:
        return self._parse(pb.LocatorCandidates, self._data.get("locator_candidates", {}))

    def subscribe(self, handle: pb.SessionHandle) -> Iterator[pb.UiEvent]:
        for event in self._data.get("events", []):
            yield self._parse(pb.UiEvent, event)

    def capture_screenshot(self, request: pb.CaptureRequest) -> pb.ImageBlob:
        return self._parse(pb.ImageBlob, self._data.get("screenshot", {}))

    def get_ok_code_history(self, handle: pb.SessionHandle) -> pb.OkCodeHistory:
        return self._parse(pb.OkCodeHistory, self._data.get("ok_code_history", {}))
