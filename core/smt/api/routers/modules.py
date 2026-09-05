"""Browse scanned Modules, and trigger a live scan of a new one."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, sessionmaker

from smt.adapter.generated import uiadapter_pb2 as pb
from smt.adapter.port import UiAgentPort
from smt.api.capture import ElementCaptureRegistry
from smt.api.deps import get_agent, get_capture_registry, get_session_factory, resolve_connection_id
from smt.api.schemas import (
    HighlightComponentRequest,
    HighlightRequest,
    HighlightResponse,
    ModuleAttributeOut,
    ModuleDetail,
    ModuleSummary,
    PollCaptureResponse,
    ScannedComponentOut,
    ScanModuleRequest,
    ScanModuleResponse,
    ScanPreviewRequest,
    ScanPreviewResponse,
    SaveModuleRequest,
    StartCaptureRequest,
    StartCaptureResponse,
    StopCaptureResponse,
)
from smt.repository.models import Module
from smt.repository.scanning import ScannedComponent, save_module, scan_module, scan_screen_preview

router = APIRouter(tags=["modules"])


def _to_out(c: ScannedComponent) -> ScannedComponentOut:
    return ScannedComponentOut(
        component_id=c.component_id, window=c.window, semantic_name=c.semantic_name,
        sap_type=c.sap_type, sap_sub_type=c.sap_sub_type, label=c.label, caption=c.caption,
        window_title=c.window_title, supported_action_modes=c.supported_action_modes,
    )


def _to_summary(module: Module) -> ModuleSummary:
    return ModuleSummary(
        id=module.id, name=module.name, tcode=module.tcode, screen_number=module.screen_number,
        scanned_at=module.scanned_at, attribute_count=len(module.attributes),
    )


@router.get("/modules", response_model=list[ModuleSummary])
def list_modules(session_factory: sessionmaker[Session] = Depends(get_session_factory)) -> list[ModuleSummary]:
    with session_factory() as db:
        return [_to_summary(m) for m in db.query(Module).order_by(Module.name).all()]


@router.get("/modules/{name}", response_model=ModuleDetail)
def get_module(name: str, session_factory: sessionmaker[Session] = Depends(get_session_factory)) -> ModuleDetail:
    with session_factory() as db:
        module = db.query(Module).filter_by(name=name).one_or_none()
        if module is None:
            raise HTTPException(status_code=404, detail=f"no Module named {name!r}")
        return ModuleDetail(
            **_to_summary(module).model_dump(),
            root_id=module.root_id,
            attributes=[
                ModuleAttributeOut(
                    id=a.id, semantic_name=a.semantic_name, component_id=a.component_id,
                    sap_type=a.sap_type, sap_sub_type=a.sap_sub_type, label=a.label, caption=a.caption,
                    window_title=a.window_title,
                    supported_action_modes=[m for m in a.supported_action_modes.split(",") if m],
                )
                for a in module.attributes
            ],
        )


@router.post("/modules/scan", response_model=ScanModuleResponse)
def scan_module_endpoint(
    body: ScanModuleRequest,
    agent: UiAgentPort = Depends(get_agent),
    session_factory: sessionmaker[Session] = Depends(get_session_factory),
) -> ScanModuleResponse:
    """All-in-one scan + persist-everything. Kept for parity with the CLI's
    `scan-module` command / quick full scans; the script-builder UI uses
    /modules/scan-preview + POST /modules instead so a tester can pick and choose
    which fields/buttons actually become Module attributes."""
    connection_id = resolve_connection_id(agent, body.connection_id)
    handle = agent.open_session(pb.OpenSessionRequest(connection_id=connection_id))
    try:
        module_id, attribute_count = scan_module(
            agent, handle, session_factory,
            module_name=body.module_name, tcode=body.tcode, root_id=body.root_id,
            navigate=body.navigate, prefill=body.prefill, vkeys_before_scan=body.vkeys_before_scan,
        )
    finally:
        agent.close_session(handle)

    return ScanModuleResponse(module_id=module_id, module_name=body.module_name, attribute_count=attribute_count)


@router.post("/modules/scan-preview", response_model=ScanPreviewResponse)
def scan_preview_endpoint(
    body: ScanPreviewRequest,
    agent: UiAgentPort = Depends(get_agent),
) -> ScanPreviewResponse:
    """Live navigate+scan without persisting anything — returns every candidate
    field/button/label found so the UI can let a tester pick and choose which ones to
    keep, and rename them, before POST /modules actually saves a Module."""
    connection_id = resolve_connection_id(agent, body.connection_id)
    handle = agent.open_session(pb.OpenSessionRequest(connection_id=connection_id))
    try:
        screen_number, components = scan_screen_preview(
            agent, handle, tcode=body.tcode, root_id=body.root_id,
            navigate=body.navigate, prefill=body.prefill, vkeys_before_scan=body.vkeys_before_scan,
        )
    finally:
        agent.close_session(handle)

    return ScanPreviewResponse(
        tcode=body.tcode, screen_number=screen_number, root_id=body.root_id,
        components=[_to_out(c) for c in components],
    )


@router.post("/modules", response_model=ScanModuleResponse)
def save_module_endpoint(
    body: SaveModuleRequest,
    session_factory: sessionmaker[Session] = Depends(get_session_factory),
) -> ScanModuleResponse:
    """Persists a Module from an already-curated attribute list (the selection a
    tester made from a prior /modules/scan-preview) — no live agent call needed here."""
    module_id, count = save_module(
        session_factory, module_name=body.module_name, tcode=body.tcode, root_id=body.root_id,
        screen_number=body.screen_number, attributes=[a.model_dump() for a in body.attributes],
    )
    return ScanModuleResponse(module_id=module_id, module_name=body.module_name, attribute_count=count)


@router.post("/modules/highlight", response_model=HighlightResponse)
def highlight_component_endpoint(
    body: HighlightComponentRequest,
    agent: UiAgentPort = Depends(get_agent),
) -> HighlightResponse:
    """Draws a colored border around `component_id` on the real, live SAP GUI screen —
    for a saved Module's attribute (ModuleDetailView) or a field still in the review
    step, neither of which has an active capture session to reuse a handle from (see
    /modules/capture/{id}/highlight for that case). Opens a short-lived session just
    for this one action and closes it when done — safe now that close_session no
    longer touches the real window (see CloseSessionAsync)."""
    connection_id = resolve_connection_id(agent, body.connection_id)
    handle = agent.open_session(pb.OpenSessionRequest(connection_id=connection_id))
    try:
        result = agent.execute_action(pb.ActionRequest(
            session_id=handle.session_id, component_id=body.component_id, op=pb.HIGHLIGHT,
        ))
    finally:
        agent.close_session(handle)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error_message or "highlight failed")
    return HighlightResponse()


@router.post("/modules/capture/start", response_model=StartCaptureResponse)
def start_capture_endpoint(
    body: StartCaptureRequest,
    agent: UiAgentPort = Depends(get_agent),
    captures: ElementCaptureRegistry = Depends(get_capture_registry),
) -> StartCaptureResponse:
    """Launches the transaction (if `navigate`) and starts watching for Ctrl+Click on
    the live SAP GUI window — each click identifies and adds one field/button, until
    /modules/capture/{id}/stop is called. Poll /modules/capture/{id}/poll to see
    newly-picked components as they arrive."""
    connection_id = resolve_connection_id(agent, body.connection_id)
    capture_id = captures.start(
        agent, connection_id=connection_id, tcode=body.tcode, navigate=body.navigate,
        prefill=body.prefill, vkeys_before_scan=body.vkeys_before_scan,
    )
    return StartCaptureResponse(capture_id=capture_id)


@router.get("/modules/capture/{capture_id}/poll", response_model=PollCaptureResponse)
def poll_capture_endpoint(
    capture_id: str,
    captures: ElementCaptureRegistry = Depends(get_capture_registry),
) -> PollCaptureResponse:
    try:
        components, active, error = captures.poll(capture_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"no capture session {capture_id!r} (already stopped?)")
    return PollCaptureResponse(components=[_to_out(c) for c in components], active=active, error=error)


@router.post("/modules/capture/{capture_id}/highlight", response_model=HighlightResponse)
def highlight_capture_endpoint(
    capture_id: str,
    body: HighlightRequest,
    captures: ElementCaptureRegistry = Depends(get_capture_registry),
) -> HighlightResponse:
    """Draws a colored border around `component_id` on the real, live SAP GUI screen
    (reusing the capture session's own live handle) — lets a tester confirm which
    on-screen control a just-captured row actually points to."""
    try:
        captures.highlight(capture_id, body.component_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"no capture session {capture_id!r} (already stopped?)")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return HighlightResponse()


@router.post("/modules/capture/{capture_id}/stop", response_model=StopCaptureResponse)
def stop_capture_endpoint(
    capture_id: str,
    captures: ElementCaptureRegistry = Depends(get_capture_registry),
) -> StopCaptureResponse:
    try:
        components = captures.stop(capture_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"no capture session {capture_id!r} (already stopped?)")
    return StopCaptureResponse(components=[_to_out(c) for c in components])
