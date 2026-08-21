"""SQLite by default (spec §3 MVP); swap DEFAULT_URL for a Postgres DSN later --
nothing else in this module needs to change."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from smt.repository.models import Base

DEFAULT_DB_PATH = Path("core/data/repository.db")


def make_engine(db_path: Path | str = DEFAULT_DB_PATH):
    if str(db_path) == ":memory:":
        # Every SQLite in-memory connection is its own separate empty database unless
        # forced onto one shared connection via StaticPool — otherwise each new Session
        # would see a blank DB instead of what a previous Session just committed.
        return create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{path}")


def init_db(engine) -> None:
    Base.metadata.create_all(engine)


def make_session_factory(engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine)
