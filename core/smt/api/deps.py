"""FastAPI dependency helpers — thin accessors over what app.state holds (constructed
once in app.py's lifespan), plus the "which SAP connection do we run against" resolution
every scan/run endpoint needs.
"""

from __future__ import annotations

from fastapi import Request
from sqlalchemy.orm import Session, sessionmaker

from smt.adapter.port import UiAgentPort


class ConnectionUnavailableError(RuntimeError):
    """Raised when no live SAP GUI connection is reachable through the agent."""


def get_session_factory(request: Request) -> sessionmaker[Session]:
    return request.app.state.session_factory


def get_agent(request: Request) -> UiAgentPort:
    return request.app.state.agent


def resolve_connection_id(agent: UiAgentPort, connection_id: str | None) -> str:
    if connection_id:
        return connection_id
    connections = agent.list_connections().connections
    if not connections:
        raise ConnectionUnavailableError("no live SAP GUI connection reported by the agent")
    return connections[0].connection_id
