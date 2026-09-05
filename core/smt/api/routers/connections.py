"""Live SAP connection status — powers the UI's connection pill. Deliberately never
raises: an unreachable agent is a normal, expected state (SapGuiAgent not started, no SAP
GUI session open yet), not a server error."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from smt.api.deps import get_agent
from smt.api.schemas import ConnectionOut, ConnectionsResponse
from smt.adapter.port import UiAgentPort

router = APIRouter(tags=["connections"])


@router.get("/connections", response_model=ConnectionsResponse)
def list_connections(agent: UiAgentPort = Depends(get_agent)) -> ConnectionsResponse:
    try:
        result = agent.list_connections()
    except Exception as exc:  # noqa: BLE001 - any transport failure means "not reachable"
        return ConnectionsResponse(reachable=False, error=str(exc))

    return ConnectionsResponse(
        reachable=True,
        connections=[
            ConnectionOut(connection_id=c.connection_id, description=c.description, session_ids=list(c.session_ids))
            for c in result.connections
        ],
    )
