"""Execute a TestCase or a Chain of TestCases against the live SAP agent."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, sessionmaker

from smt.adapter.port import UiAgentPort
from smt.api.deps import get_agent, get_session_factory, resolve_connection_id
from smt.api.schemas import (
    RowResultOut,
    RunChainRequest,
    RunChainResponse,
    RunTestCaseRequest,
    RunTestCaseResponse,
)
from smt.engine.executor import RowResult, run_chain_with_rows, run_test_case_with_rows

router = APIRouter(tags=["runs"])


def _to_out(result: RowResult) -> RowResultOut:
    return RowResultOut(
        row_index=result.row_index, success=result.success, failed_at_step=result.failed_at_step,
        message=result.message, values=result.values, test_case_name=result.test_case_name,
        buffer=result.buffer,
    )


@router.post("/runs/test-case", response_model=RunTestCaseResponse)
def run_test_case_endpoint(
    body: RunTestCaseRequest,
    agent: UiAgentPort = Depends(get_agent),
    session_factory: sessionmaker[Session] = Depends(get_session_factory),
) -> RunTestCaseResponse:
    connection_id = resolve_connection_id(agent, body.connection_id)
    results = run_test_case_with_rows(agent, session_factory, body.test_case_name, body.rows, connection_id)
    return RunTestCaseResponse(results=[_to_out(r) for r in results])


@router.post("/runs/chain", response_model=RunChainResponse)
def run_chain_endpoint(
    body: RunChainRequest,
    agent: UiAgentPort = Depends(get_agent),
    session_factory: sessionmaker[Session] = Depends(get_session_factory),
) -> RunChainResponse:
    connection_id = resolve_connection_id(agent, body.connection_id)
    chain = [(stage.test_case_name, stage.rows) for stage in body.stages]
    results = run_chain_with_rows(agent, session_factory, chain, connection_id)
    return RunChainResponse(results=[[_to_out(r) for r in row] for row in results])
