"""In-memory relay between a live StartElementPicker gRPC stream and REST polling from
the browser (which can't consume a gRPC stream directly). A background thread drains
the agent's streaming call into a per-capture-session buffer; the browser polls it on
an interval — the same "poll every few seconds" pattern already used for the
connection-status pill, chosen over WebSocket/SSE to keep this MVP's transport surface
small. One process-wide registry (constructed once in the FastAPI app's lifespan,
mirroring session_factory/agent) tracks capture sessions by a random capture_id.
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field

import grpc

from smt.adapter.generated import uiadapter_pb2 as pb
from smt.adapter.port import UiAgentPort
from smt.repository.scanning import ScannedComponent, scanned_component_from_picked

WND0 = "wnd[0]"
OKCD = f"{WND0}/tbar[0]/okcd"


@dataclass
class CaptureSession:
    capture_id: str
    agent: UiAgentPort
    handle: pb.SessionHandle
    call: object  # the raw grpc streaming call — supports .cancel(), same object returned by iterating
    thread: threading.Thread
    lock: threading.Lock = field(default_factory=threading.Lock)
    picked: list[ScannedComponent] = field(default_factory=list)
    seen_ids: set[str] = field(default_factory=set)
    active: bool = True
    error: str | None = None


class ElementCaptureRegistry:
    def __init__(self) -> None:
        self._sessions: dict[str, CaptureSession] = {}

    def start(
        self,
        agent: UiAgentPort,
        *,
        connection_id: str,
        tcode: str,
        navigate: bool,
        prefill: dict[str, str],
        vkeys_before_scan: list[str],
    ) -> str:
        handle = agent.open_session(pb.OpenSessionRequest(connection_id=connection_id))

        if navigate:
            agent.execute_action(pb.ActionRequest(session_id=handle.session_id, component_id=OKCD, op=pb.SET,
                                                   params=pb.ActionParams(text_value=f"/n{tcode}")))
            agent.execute_action(pb.ActionRequest(session_id=handle.session_id, component_id=WND0, op=pb.SEND_VKEY,
                                                   params=pb.ActionParams(vkey="Enter")))
        for component_id, value in prefill.items():
            agent.execute_action(pb.ActionRequest(session_id=handle.session_id, component_id=component_id, op=pb.SET,
                                                   params=pb.ActionParams(text_value=value)))
        for vkey in vkeys_before_scan:
            agent.execute_action(pb.ActionRequest(session_id=handle.session_id, component_id=WND0, op=pb.SEND_VKEY,
                                                   params=pb.ActionParams(vkey=vkey)))

        call = agent.start_element_picker(handle)
        capture_id = str(uuid.uuid4())
        session = CaptureSession(capture_id=capture_id, agent=agent, handle=handle, call=call, thread=None)  # type: ignore[arg-type]
        thread = threading.Thread(target=self._relay, args=(session,), daemon=True)
        session.thread = thread
        self._sessions[capture_id] = session
        thread.start()
        return capture_id

    def _relay(self, session: CaptureSession) -> None:
        try:
            for raw in session.call:  # type: ignore[attr-defined]
                component = scanned_component_from_picked(raw)
                with session.lock:
                    if component.component_id not in session.seen_ids:
                        session.seen_ids.add(component.component_id)
                        session.picked.append(component)
        except grpc.RpcError:
            pass  # expected: stop() cancels the call, which surfaces here as CANCELLED
        except Exception as exc:  # noqa: BLE001 - surface anything unexpected to the poller instead of losing it
            with session.lock:
                session.error = str(exc)
        finally:
            with session.lock:
                session.active = False

    def poll(self, capture_id: str) -> tuple[list[ScannedComponent], bool, str | None]:
        session = self._require(capture_id)
        with session.lock:
            drained, session.picked = session.picked, []
            return drained, session.active, session.error

    def highlight(self, capture_id: str, component_id: str) -> None:
        """Draws a colored border around `component_id` on the real, live SAP GUI
        screen (GuiVComponent.Visualize(true), see HIGHLIGHT in uiadapter.proto) — lets
        a tester confirm which on-screen control a captured row actually points to.
        Reuses the capture session's own handle rather than opening a new one."""
        session = self._require(capture_id)
        result = session.agent.execute_action(pb.ActionRequest(
            session_id=session.handle.session_id, component_id=component_id, op=pb.HIGHLIGHT,
        ))
        if not result.success:
            raise ValueError(result.error_message or "highlight failed")

    def stop(self, capture_id: str) -> list[ScannedComponent]:
        session = self._sessions.pop(capture_id, None)
        if session is None:
            raise KeyError(capture_id)
        try:
            session.call.cancel()  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001 - best-effort; the session/thread cleanup below still happens
            pass
        session.thread.join(timeout=2)
        try:
            session.agent.close_session(session.handle)
        except Exception:  # noqa: BLE001 - agent may already be gone; don't block returning captured results
            pass
        with session.lock:
            return list(session.picked)

    def _require(self, capture_id: str) -> CaptureSession:
        session = self._sessions.get(capture_id)
        if session is None:
            raise KeyError(capture_id)
        return session
