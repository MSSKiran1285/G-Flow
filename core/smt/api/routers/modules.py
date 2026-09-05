"""Browse scanned Modules, and trigger a live scan of a new one."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, sessionmaker

from smt.adapter.generated import uiadapter_pb2 as pb
from smt.adapter.port import UiAgentPort
from smt.api.deps import get_agent, get_session_factory, resolve_connection_id
from smt.api.schemas import (
    ModuleAttributeOut,
    ModuleDetail,
    ModuleSummary,
    ScanModuleRequest,
    ScanModuleResponse,
)
from smt.repository.models import Module
from smt.repository.scanning import scan_module

router = APIRouter(tags=["modules"])


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
                    sap_type=a.sap_type, sap_sub_type=a.sap_sub_type, label=a.label,
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
