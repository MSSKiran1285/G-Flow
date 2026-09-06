"""Shared in-process UiAgentPort test double — no gRPC, COM, or fixture file needed.
Originally lived inline in tests/engine/test_executor.py; promoted here so
tests/api/* can exercise the exact same double instead of redefining one with
possibly-drifting behavior.
"""

from __future__ import annotations

from smt.adapter.generated import uiadapter_pb2 as pb


class FakePickerCall:
    """Minimal stand-in for the real grpc streaming-call object StartElementPicker
    returns: iterable, and supports .cancel() the way capture.py's stop() expects."""

    def __init__(self, items: list[pb.PickedComponent]):
        self._items = list(items)
        self.cancelled = False

    def __iter__(self):
        for item in self._items:
            if self.cancelled:
                return
            yield item

    def cancel(self) -> None:
        self.cancelled = True


class FakeAgent:
    """Records every SET it receives, fails a chosen (component_id, op) combination on
    demand, serves scripted statusbar text (one entry per STATUSBAR_READ call, repeating
    the last once exhausted), and answers list_connections/scan_screen from canned
    responses when provided (both default to "nothing configured" behavior that's safe
    for tests that don't need them)."""

    def __init__(
        self,
        fail_on: tuple[str, int] | None = None,
        statusbar_texts: list[str] | None = None,
        connections: pb.ConnectionList | None = None,
        scan_result: pb.ScreenSnapshot | None = None,
        picked_components: list[pb.PickedComponent] | None = None,
    ):
        self.fail_on = fail_on
        self.statusbar_texts = list(statusbar_texts) if statusbar_texts else ["Standard Order 999 has been saved"]
        self.connections = connections if connections is not None else pb.ConnectionList()
        self.scan_result = scan_result if scan_result is not None else pb.ScreenSnapshot()
        self.picked_components = list(picked_components) if picked_components else []
        self.last_picker_call: FakePickerCall | None = None
        self.sets: list[tuple[str, str]] = []
        self.table_calls: list[tuple[str, int, str, str]] = []  # (component_id, row, column_id, op_name)
        self.sessions_opened = 0
        self.sessions_closed = 0

    def list_connections(self) -> pb.ConnectionList:
        return self.connections

    def open_session(self, request):
        self.sessions_opened += 1
        return pb.SessionHandle(session_id=f"ses{self.sessions_opened}")

    def close_session(self, handle):
        self.sessions_closed += 1
        return pb.Ack(success=True)

    def scan_screen(self, request):
        return self.scan_result

    def start_element_picker(self, handle):
        self.last_picker_call = FakePickerCall(self.picked_components)
        return self.last_picker_call

    def execute_action(self, request):
        if self.fail_on == (request.component_id, request.op):
            return pb.ActionResult(success=False, error_message="boom")
        if request.op == pb.SET:
            self.sets.append((request.component_id, request.params.text_value))
            return pb.ActionResult(success=True, actual_value=request.params.text_value)
        if request.op == pb.STATUSBAR_READ:
            text = self.statusbar_texts.pop(0) if len(self.statusbar_texts) > 1 else self.statusbar_texts[0]
            result = pb.ActionResult(success=True)
            result.statusbar_deltas.add(type="S", text=text)
            return result
        if request.op in (pb.TABLE_SET_CELL, pb.TABLE_GET_CELL):
            op_name = "TABLE_SET_CELL" if request.op == pb.TABLE_SET_CELL else "TABLE_GET_CELL"
            self.table_calls.append((request.component_id, request.params.row, request.params.column_id, op_name))
            return pb.ActionResult(success=True, actual_value=request.params.text_value)
        return pb.ActionResult(success=True)
