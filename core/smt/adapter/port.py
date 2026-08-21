"""The seam between the Python core and any UI-technology agent.

`UiAgentClient` (real gRPC, talking to SapGuiAgent) and `FakeUiAgent` (in-process,
replays recorded fixtures) both implement this `Protocol`. Every other subsystem
(scanner, engine, healing) depends only on this interface, never on gRPC or COM
directly, so the whole core is testable without SAP or Windows.
"""

from __future__ import annotations

from typing import Iterator, Protocol

from smt.adapter.generated import uiadapter_pb2 as pb


class UiAgentPort(Protocol):
    def list_connections(self) -> pb.ConnectionList: ...

    def open_session(self, request: pb.OpenSessionRequest) -> pb.SessionHandle: ...

    def close_session(self, handle: pb.SessionHandle) -> pb.Ack: ...

    def get_session_info(self, handle: pb.SessionHandle) -> pb.SessionInfo: ...

    def scan_screen(self, request: pb.ScanRequest) -> pb.ScreenSnapshot: ...

    def execute_action(self, request: pb.ActionRequest) -> pb.ActionResult: ...

    def execute_batch(self, batch: pb.ActionBatch) -> Iterator[pb.ActionResult]: ...

    def resolve_locator(self, request: pb.LocatorRequest) -> pb.LocatorCandidates: ...

    def subscribe(self, handle: pb.SessionHandle) -> Iterator[pb.UiEvent]: ...

    def capture_screenshot(self, request: pb.CaptureRequest) -> pb.ImageBlob: ...

    def get_ok_code_history(self, handle: pb.SessionHandle) -> pb.OkCodeHistory: ...
