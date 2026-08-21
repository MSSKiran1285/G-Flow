"""Real gRPC client for talking to a running SapGuiAgent (or any future UiAgent
implementation, e.g. the Playwright/Fiori agent) over the uiadapter.proto contract.
"""

from __future__ import annotations

from typing import Iterator

import grpc

from smt.adapter.contract import CONTRACT_VERSION
from smt.adapter.generated import uiadapter_pb2 as pb
from smt.adapter.generated import uiadapter_pb2_grpc as pb_grpc


class ContractVersionMismatch(RuntimeError):
    def __init__(self, expected: str, actual: str) -> None:
        super().__init__(f"agent contract_version {actual!r} != core {expected!r}")
        self.expected = expected
        self.actual = actual


class UiAgentClient:
    """Implements `UiAgentPort` against a real SapGuiAgent gRPC endpoint."""

    def __init__(self, target: str, *, secure: bool = False) -> None:
        self._channel = (
            grpc.secure_channel(target, grpc.ssl_channel_credentials())
            if secure
            else grpc.insecure_channel(target)
        )
        self._stub = pb_grpc.UiAgentStub(self._channel)

    def close(self) -> None:
        self._channel.close()

    def __enter__(self) -> "UiAgentClient":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def list_connections(self) -> pb.ConnectionList:
        return self._stub.ListConnections(
            pb.ListConnectionsRequest(contract_version=CONTRACT_VERSION)
        )

    def open_session(self, request: pb.OpenSessionRequest) -> pb.SessionHandle:
        request.contract_version = CONTRACT_VERSION
        return self._stub.OpenSession(request)

    def close_session(self, handle: pb.SessionHandle) -> pb.Ack:
        handle.contract_version = CONTRACT_VERSION
        return self._stub.CloseSession(handle)

    def get_session_info(self, handle: pb.SessionHandle) -> pb.SessionInfo:
        handle.contract_version = CONTRACT_VERSION
        return self._stub.GetSessionInfo(handle)

    def scan_screen(self, request: pb.ScanRequest) -> pb.ScreenSnapshot:
        request.contract_version = CONTRACT_VERSION
        return self._stub.ScanScreen(request)

    def execute_action(self, request: pb.ActionRequest) -> pb.ActionResult:
        request.contract_version = CONTRACT_VERSION
        return self._stub.ExecuteAction(request)

    def execute_batch(self, batch: pb.ActionBatch) -> Iterator[pb.ActionResult]:
        batch.contract_version = CONTRACT_VERSION
        yield from self._stub.ExecuteBatch(batch)

    def resolve_locator(self, request: pb.LocatorRequest) -> pb.LocatorCandidates:
        request.contract_version = CONTRACT_VERSION
        return self._stub.ResolveLocator(request)

    def subscribe(self, handle: pb.SessionHandle) -> Iterator[pb.UiEvent]:
        handle.contract_version = CONTRACT_VERSION
        yield from self._stub.Subscribe(handle)

    def capture_screenshot(self, request: pb.CaptureRequest) -> pb.ImageBlob:
        request.contract_version = CONTRACT_VERSION
        return self._stub.CaptureScreenshot(request)

    def get_ok_code_history(self, handle: pb.SessionHandle) -> pb.OkCodeHistory:
        handle.contract_version = CONTRACT_VERSION
        return self._stub.GetOkCodeHistory(handle)
