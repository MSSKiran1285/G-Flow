"""Deterministic interpreter for a persisted TestCase (spec §6 MVP slice): resolves each
TestStep's Module-attribute reference to a component id, resolves its binding against a
TestSheet (CSV) row, and executes it. AI has no part in this — it's plain, boring,
auditable execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import yaml
from sqlalchemy.orm import Session, sessionmaker

from smt.adapter.generated import uiadapter_pb2 as pb
from smt.adapter.port import UiAgentPort
from smt.repository.models import Module, ModuleAttribute, TestCase, TestStep

SBAR = "wnd[0]/sbar"


@dataclass
class DefinedTestCase:
    id: str
    name: str


def define_test_case(session_factory: sessionmaker[Session], yaml_path: Path | str) -> DefinedTestCase:
    """Imports a YAML test-case definition into the repository. Re-importing a name
    already present replaces it — the YAML is the human-editable source, the DB row is
    the actual persisted asset (what a future UI would read/write directly)."""
    spec = yaml.safe_load(Path(yaml_path).read_text(encoding="utf-8"))
    with session_factory() as db:
        existing = db.query(TestCase).filter_by(name=spec["name"]).one_or_none()
        if existing:
            db.delete(existing)
            db.flush()

        test_case = TestCase(name=spec["name"], description=spec.get("description", ""))
        db.add(test_case)

        for order, step in enumerate(spec["steps"]):
            binding_type, _, binding_value = step.get("bind", "literal:").partition(":")
            db.add(TestStep(
                test_case=test_case,
                sequence_order=order,
                module_name=step.get("module", ""),
                attribute_semantic_name=step.get("attribute", ""),
                raw_component_id=step.get("component_id", ""),
                action_mode=step["action"],
                binding_type=binding_type or "literal",
                binding_value=binding_value,
                optional=bool(step.get("optional", False)),
            ))

        db.commit()
        return DefinedTestCase(id=test_case.id, name=test_case.name)


def _resolve_component_id(db: Session, step: TestStep) -> str:
    if step.raw_component_id:
        return step.raw_component_id
    attribute = (
        db.query(ModuleAttribute)
        .join(Module)
        .filter(Module.name == step.module_name, ModuleAttribute.semantic_name == step.attribute_semantic_name)
        .one_or_none()
    )
    if attribute is None:
        raise ValueError(f"unknown module attribute '{step.module_name}.{step.attribute_semantic_name}'")
    return attribute.component_id


def _build_params(action_mode: str, value: str) -> pb.ActionParams:
    if action_mode == "SET":
        return pb.ActionParams(text_value=value)
    if action_mode == "SEND_VKEY":
        return pb.ActionParams(vkey=value)
    if action_mode == "SELECT":
        return pb.ActionParams(key_value=value)
    return pb.ActionParams()


@dataclass
class RowResult:
    row_index: int
    success: bool
    failed_at_step: int | None
    message: str
    values: dict[str, str]


def run_test_case(
    agent: UiAgentPort,
    session_factory: sessionmaker[Session],
    test_case_name: str,
    sheet_path: Path | str,
    connection_id: str,
) -> list[RowResult]:
    with session_factory() as db:
        test_case = db.query(TestCase).filter_by(name=test_case_name).one()
        resolved = [(step, _resolve_component_id(db, step)) for step in test_case.steps]

    with open(sheet_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    results: list[RowResult] = []
    for row_index, row in enumerate(rows):
        handle = agent.open_session(pb.OpenSessionRequest(connection_id=connection_id))
        failed_at: int | None = None
        message = ""

        for step, component_id in resolved:
            value = row.get(step.binding_value, "") if step.binding_type == "column" else step.binding_value
            result = agent.execute_action(pb.ActionRequest(
                session_id=handle.session_id,
                component_id=component_id,
                op=getattr(pb, step.action_mode),
                params=_build_params(step.action_mode, value),
            ))
            if not result.success and not step.optional:
                failed_at = step.sequence_order
                message = result.error_message or result.unsupported_reason
                break

        if failed_at is None:
            status = agent.execute_action(pb.ActionRequest(session_id=handle.session_id, component_id=SBAR, op=pb.STATUSBAR_READ))
            message = status.statusbar_deltas[0].text if status.statusbar_deltas else ""

        agent.close_session(handle)
        results.append(RowResult(row_index=row_index, success=failed_at is None, failed_at_step=failed_at, message=message, values=row))

    return results
