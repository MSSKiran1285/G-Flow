"""Deterministic interpreter for a persisted TestCase (spec §6 MVP slice): resolves each
TestStep's Module-attribute reference to a component id, resolves its binding (literal /
TestSheet column / buffer) and executes it. AI has no part in this — it's plain, boring,
auditable execution.

Buffers (spec §6 `Buffer` ActionMode) let a step capture a value — typically a document
number parsed from the statusbar via smt.engine.message_patterns — for later steps to
bind to, either within one TestCase or across a chain of them (`run_chain`), which is what
lets a real business process (VA01 -> VL01N -> VF01) be tested end to end instead of one
document at a time.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from sqlalchemy.orm import Session, sessionmaker

from smt.adapter.generated import uiadapter_pb2 as pb
from smt.adapter.port import UiAgentPort
from smt.engine import message_patterns
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
            capture = step.get("capture") or {}
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
                capture_buffer_key=capture.get("buffer", ""),
                capture_from="statusbar" if capture.get("pattern") else "actual_value",
                capture_pattern=capture.get("pattern", ""),
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


def _resolve_binding(step: TestStep, row: dict[str, str], buffer: dict[str, str]) -> str:
    if step.binding_type == "column":
        return row.get(step.binding_value, "")
    if step.binding_type == "buffer":
        if step.binding_value not in buffer:
            raise ValueError(
                f"step {step.sequence_order} needs buffer '{step.binding_value}', "
                f"but nothing has captured it yet (have: {', '.join(sorted(buffer)) or 'nothing'})"
            )
        return buffer[step.binding_value]
    return step.binding_value


@dataclass
class RowResult:
    row_index: int
    success: bool
    failed_at_step: int | None
    message: str
    values: dict[str, str]
    test_case_name: str = ""
    buffer: dict[str, str] = field(default_factory=dict)


def _run_one_row(
    agent: UiAgentPort,
    resolved: list[tuple[TestStep, str]],
    row: dict[str, str],
    connection_id: str,
    buffer: dict[str, str],
    test_case_name: str,
) -> RowResult:
    handle = agent.open_session(pb.OpenSessionRequest(connection_id=connection_id))
    failed_at: int | None = None
    message = ""

    for step, component_id in resolved:
        try:
            value = _resolve_binding(step, row, buffer)
        except ValueError as exc:
            failed_at, message = step.sequence_order, str(exc)
            break

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

        if step.capture_buffer_key and result.success:
            if step.capture_from == "statusbar":
                status = agent.execute_action(pb.ActionRequest(session_id=handle.session_id, component_id=SBAR, op=pb.STATUSBAR_READ))
                text = status.statusbar_deltas[0].text if status.statusbar_deltas else ""
                captured = message_patterns.extract(step.capture_pattern, text)
                if captured is None:
                    failed_at = step.sequence_order
                    message = f"capture pattern '{step.capture_pattern}' did not match statusbar text: {text!r}"
                    break
                buffer[step.capture_buffer_key] = captured
            else:
                buffer[step.capture_buffer_key] = result.actual_value

    if failed_at is None:
        status = agent.execute_action(pb.ActionRequest(session_id=handle.session_id, component_id=SBAR, op=pb.STATUSBAR_READ))
        message = status.statusbar_deltas[0].text if status.statusbar_deltas else ""

    agent.close_session(handle)
    return RowResult(
        row_index=-1,  # filled in by the caller, which knows the row index
        success=failed_at is None,
        failed_at_step=failed_at,
        message=message,
        values=row,
        test_case_name=test_case_name,
        buffer=dict(buffer),
    )


def _resolve_steps(db: Session, test_case_name: str) -> list[tuple[TestStep, str]]:
    test_case = db.query(TestCase).filter_by(name=test_case_name).one()
    return [(step, _resolve_component_id(db, step)) for step in test_case.steps]


def _read_rows(sheet_path: Path | str) -> list[dict[str, str]]:
    with open(sheet_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def run_test_case(
    agent: UiAgentPort,
    session_factory: sessionmaker[Session],
    test_case_name: str,
    sheet_path: Path | str,
    connection_id: str,
) -> list[RowResult]:
    with session_factory() as db:
        resolved = _resolve_steps(db, test_case_name)

    results: list[RowResult] = []
    for row_index, row in enumerate(_read_rows(sheet_path)):
        result = _run_one_row(agent, resolved, row, connection_id, buffer={}, test_case_name=test_case_name)
        result.row_index = row_index
        results.append(result)

    return results


def run_chain(
    agent: UiAgentPort,
    session_factory: sessionmaker[Session],
    chain: list[tuple[str, Path | str]],
    connection_id: str,
) -> list[list[RowResult]]:
    """Runs several TestCases in sequence per data row, sharing one buffer per row across
    all of them — e.g. [(VA01_CreateStandardOrder, orders.csv), (VL01N_CreateDelivery,
    deliveries.csv), (VF01_CreateBilling, billing.csv)] lets the order number VA01 creates
    feed VL01N, and the delivery number VL01N creates feed VF01. Row i of every sheet is
    assumed to belong to the same logical chain run; sheets must have equal row counts.
    Stops a row's chain at the first failing TestCase — later ones in the chain would just
    be missing the buffer value they need anyway.
    """
    with session_factory() as db:
        resolved_by_case = [(name, _resolve_steps(db, name)) for name, _ in chain]

    rows_by_case = [_read_rows(sheet) for _, sheet in chain]
    row_counts = {len(rows) for rows in rows_by_case}
    if len(row_counts) > 1:
        raise ValueError(f"chain sheets have mismatched row counts: {row_counts} — every sheet needs one row per chain run")
    num_rows = row_counts.pop() if row_counts else 0

    all_results: list[list[RowResult]] = []
    for row_index in range(num_rows):
        buffer: dict[str, str] = {}
        row_results: list[RowResult] = []
        for (test_case_name, resolved), rows in zip(resolved_by_case, rows_by_case):
            result = _run_one_row(agent, resolved, rows[row_index], connection_id, buffer, test_case_name)
            result.row_index = row_index
            row_results.append(result)
            if not result.success:
                break
        all_results.append(row_results)

    return all_results
