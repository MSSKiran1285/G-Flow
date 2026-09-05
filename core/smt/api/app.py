"""FastAPI app factory for the script-builder backend.

`create_app` takes optional `agent`/`session_factory` overrides specifically so tests
can inject a FakeUiAgent + in-memory SQLite (see core/tests/api/) without a live
SapGuiAgent or SAP GUI session — the same seam smt.adapter.port.UiAgentPort already
gives every other subsystem in this project.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm.exc import NoResultFound

from smt.adapter.client import UiAgentClient
from smt.adapter.port import UiAgentPort
from smt.api.capture import ElementCaptureRegistry
from smt.api.deps import ConnectionUnavailableError
from smt.api.routers import connections, meta, modules, runs, test_cases
from smt.repository.db import DEFAULT_DB_PATH, init_db, make_engine, make_session_factory


def _build_session_factory(db_path: Path | str) -> sessionmaker[Session]:
    engine = make_engine(db_path)
    init_db(engine)
    return make_session_factory(engine)


def create_app(
    *,
    target: str = "localhost:50051",
    db_path: Path | str = DEFAULT_DB_PATH,
    agent: UiAgentPort | None = None,
    session_factory: sessionmaker[Session] | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.session_factory = session_factory or _build_session_factory(db_path)
        app.state.agent = agent or UiAgentClient(target)
        app.state.owns_agent = agent is None
        app.state.captures = ElementCaptureRegistry()
        yield
        if app.state.owns_agent and hasattr(app.state.agent, "close"):
            app.state.agent.close()

    app = FastAPI(title="SapModelTest API", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(ValueError)
    async def _value_error(request, exc: ValueError):  # noqa: ANN001, ARG001
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(ConnectionUnavailableError)
    async def _connection_unavailable(request, exc: ConnectionUnavailableError):  # noqa: ANN001, ARG001
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.exception_handler(NoResultFound)
    async def _not_found(request, exc: NoResultFound):  # noqa: ANN001, ARG001
        return JSONResponse(status_code=404, content={"detail": str(exc) or "not found"})

    app.include_router(connections.router, prefix="/api")
    app.include_router(meta.router, prefix="/api")
    app.include_router(modules.router, prefix="/api")
    app.include_router(test_cases.router, prefix="/api")
    app.include_router(runs.router, prefix="/api")

    return app
