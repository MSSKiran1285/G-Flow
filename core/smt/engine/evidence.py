"""On-demand evidence capture (spec-inspired by G-Stride's own evidence PDFs): re-runs a
TestCase or chain exactly like executor.py's plain run_*, but additionally times every
step, captures a real screenshot (with the target field highlighted) after each one, and
records enough detail to render a full audit/training document — see
smt.reporting.evidence_pdf for the renderer.

Deliberately a separate code path from executor.py's run_test_case/run_chain rather than
a flag threaded through them: evidence capture is meaningfully slower (a screenshot round
trip per step) and produces a much richer result shape, so keeping it separate avoids
complicating the hot path every plain run already goes through. Steps' business
descriptions are derived from real captured data (the attribute's own caption, action
mode, resolved value) — nothing here is invented; a step with no caption just falls back
to its semantic/technical name.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from getpass import getuser

from sqlalchemy.orm import Session, sessionmaker

from smt.adapter.generated import uiadapter_pb2 as pb
from smt.adapter.port import UiAgentPort
from smt.engine import message_patterns
from smt.engine.executor import (
    SBAR,
    TABLE_OPS,
    _build_params,
    _parse_table_cell_id,
    _resolve_binding,
    _resolve_row_index,
)
from smt.repository.models import Module, ModuleAttribute, TestCase, TestStep

# Actions whose ActionParams actually carry binding.value through to the agent (mirrors
# executor._build_params) — only these show a "Value Entered" in the step table.
_BINDING_CONSUMING = {"SET", "SEND_VKEY", "SELECT", "TABLE_SET_CELL"}

_ACTION_VERB = {
    "SET": "Entered",
    "SEND_VKEY": "Sent key",
    "SELECT": "Selected",
    "PRESS": "Clicked",
    "TABLE_SET_CELL": "Set",
    "TABLE_GET_CELL": "Read",
    "READ": "Read",
    "VERIFY": "Verified",
}


@dataclass
class EvidenceStep:
    sequence_order: int
    description: str
    value_entered: str
    action_mode: str
    component_id: str
    success: bool
    duration_ms: float
    error: str
    screenshot_png: bytes | None
    captured: str = ""  # "buffer_key = value" when this step captured something


@dataclass
class EvidenceScenario:
    test_case_name: str
    description: str
    steps: list[EvidenceStep]
    success: bool
    started_at: datetime
    finished_at: datetime
    final_statusbar: str


@dataclass
class EvidenceReport:
    run_id: str
    execution_id: str
    plan_hash: str
    data_hash: str
    execution_mode: str
    started_at: datetime
    finished_at: datetime
    executed_by: str
    environment: str
    scenarios: list[EvidenceScenario]
    row: dict[str, str]
    final_buffer: dict[str, str] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return all(s.success for s in self.scenarios)


def _resolve_steps_with_captions(db: Session, test_case_name: str) -> list[tuple[TestStep, str, str]]:
    """Same resolution as executor._resolve_steps, plus each attribute's own caption
    (falls back to "" for a raw component_id step) — the only extra data evidence
    capture needs to write a business-readable step description."""
    test_case = db.query(TestCase).filter_by(name=test_case_name).one()
    resolved = []
    for step in test_case.steps:
        if step.raw_component_id:
            resolved.append((step, step.raw_component_id, ""))
            continue
        attribute = (
            db.query(ModuleAttribute)
            .join(Module)
            .filter(Module.name == step.module_name, ModuleAttribute.semantic_name == step.attribute_semantic_name)
            .one_or_none()
        )
        if attribute is None:
            raise ValueError(f"unknown module attribute '{step.module_name}.{step.attribute_semantic_name}'")
        resolved.append((step, attribute.component_id, attribute.caption))
    return resolved


def _describe_step(step: TestStep, caption: str, value: str) -> str:
    label = caption or step.attribute_semantic_name or step.raw_component_id or "component"
    verb = _ACTION_VERB.get(step.action_mode, step.action_mode.replace("_", " ").title())
    if step.action_mode in _BINDING_CONSUMING and value:
        return f"{verb} {label} = {value!r}"
    return f"{verb} {label}"


def _hash_json(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _plan_hash(steps: list[TestStep]) -> str:
    return _hash_json([
        {
            "module": s.module_name, "attribute": s.attribute_semantic_name, "raw": s.raw_component_id,
            "action": s.action_mode, "binding": [s.binding_type, s.binding_value],
            "row_binding": [s.row_binding_type, s.row_binding_value], "optional": s.optional,
            "capture": [s.capture_buffer_key, s.capture_from, s.capture_pattern],
        }
        for s in steps
    ])


def _capture_step_screenshot(agent: UiAgentPort, session_id: str, component_id: str) -> bytes | None:
    """Best-effort: highlights the just-touched field, then grabs a full-window
    screenshot. Never allowed to fail the actual test step — a missing screenshot just
    shows as "not available" in the rendered document."""
    try:
        agent.execute_action(pb.ActionRequest(session_id=session_id, component_id=component_id, op=pb.HIGHLIGHT))
    except Exception:
        pass
    try:
        blob = agent.capture_screenshot(pb.CaptureRequest(session_id=session_id, component_id=""))
        return blob.data or None
    except Exception:
        return None


def _run_one_row_with_evidence(
    agent: UiAgentPort,
    resolved: list[tuple[TestStep, str, str]],
    row: dict[str, str],
    connection_id: str,
    buffer: dict[str, str],
    test_case_name: str,
    test_case_description: str,
    capture_screenshots: bool,
) -> EvidenceScenario:
    handle = agent.open_session(pb.OpenSessionRequest(connection_id=connection_id))
    started_at = datetime.now(timezone.utc)
    steps: list[EvidenceStep] = []
    scenario_failed = False

    for step, component_id, caption in resolved:
        step_start = time.perf_counter()
        target_id = component_id
        table_row: int | None = None
        table_column_id = ""
        error = ""
        value = ""
        success = True

        try:
            value = _resolve_binding(step, row, buffer)
            if step.action_mode in TABLE_OPS:
                target_id, table_column_id = _parse_table_cell_id(component_id)
                table_row = _resolve_row_index(step, row, buffer)
        except ValueError as exc:
            success = False
            error = str(exc)

        actual_value = ""
        if success:
            result = agent.execute_action(pb.ActionRequest(
                session_id=handle.session_id, component_id=target_id,
                op=getattr(pb, step.action_mode),
                params=_build_params(step.action_mode, value, table_row, table_column_id),
            ))
            actual_value = result.actual_value
            if not result.success and not step.optional:
                success = False
                error = result.error_message or result.unsupported_reason

        captured_note = ""
        if success and step.capture_buffer_key:
            if step.capture_from == "statusbar":
                status = agent.execute_action(pb.ActionRequest(session_id=handle.session_id, component_id=SBAR, op=pb.STATUSBAR_READ))
                text = status.statusbar_deltas[0].text if status.statusbar_deltas else ""
                captured_value = message_patterns.extract(step.capture_pattern, text)
                if captured_value is None:
                    success = False
                    error = f"capture pattern '{step.capture_pattern}' did not match statusbar text: {text!r}"
                else:
                    buffer[step.capture_buffer_key] = captured_value
                    captured_note = f"{step.capture_buffer_key} = {captured_value}"
            else:
                buffer[step.capture_buffer_key] = actual_value
                captured_note = f"{step.capture_buffer_key} = {actual_value}"

        duration_ms = (time.perf_counter() - step_start) * 1000
        screenshot = _capture_step_screenshot(agent, handle.session_id, target_id) if capture_screenshots else None

        steps.append(EvidenceStep(
            sequence_order=step.sequence_order,
            description=_describe_step(step, caption, value),
            value_entered=value if step.action_mode in _BINDING_CONSUMING else "",
            action_mode=step.action_mode,
            component_id=target_id,
            success=success,
            duration_ms=duration_ms,
            error=error,
            screenshot_png=screenshot,
            captured=captured_note,
        ))

        if not success:
            scenario_failed = True
            break

    final_statusbar = ""
    if not scenario_failed:
        status = agent.execute_action(pb.ActionRequest(session_id=handle.session_id, component_id=SBAR, op=pb.STATUSBAR_READ))
        final_statusbar = status.statusbar_deltas[0].text if status.statusbar_deltas else ""

    agent.close_session(handle)
    finished_at = datetime.now(timezone.utc)
    return EvidenceScenario(
        test_case_name=test_case_name, description=test_case_description, steps=steps,
        success=not scenario_failed, started_at=started_at, finished_at=finished_at,
        final_statusbar=final_statusbar,
    )


def _environment_of(agent: UiAgentPort, connection_id: str) -> str:
    for conn in agent.list_connections().connections:
        if conn.connection_id == connection_id:
            return conn.description or connection_id
    return connection_id


def capture_test_case_evidence(
    agent: UiAgentPort,
    session_factory: sessionmaker[Session],
    test_case_name: str,
    row: dict[str, str],
    connection_id: str,
    capture_screenshots: bool = True,
) -> EvidenceReport:
    with session_factory() as db:
        resolved = _resolve_steps_with_captions(db, test_case_name)
        test_case = db.query(TestCase).filter_by(name=test_case_name).one()
        plan_hash = _plan_hash([s for s, _, _ in resolved])
        description = test_case.description

    started_at = datetime.now(timezone.utc)
    buffer: dict[str, str] = {}
    scenario = _run_one_row_with_evidence(
        agent, resolved, row, connection_id, buffer, test_case_name, description, capture_screenshots,
    )
    finished_at = datetime.now(timezone.utc)

    return EvidenceReport(
        run_id=str(uuid.uuid4()), execution_id=str(uuid.uuid4()), plan_hash=plan_hash,
        data_hash=_hash_json(row), execution_mode="Single script", started_at=started_at,
        finished_at=finished_at, executed_by=getuser(), environment=_environment_of(agent, connection_id),
        scenarios=[scenario], row=row, final_buffer=buffer,
    )


def capture_chain_evidence(
    agent: UiAgentPort,
    session_factory: sessionmaker[Session],
    chain: list[tuple[str, dict[str, str]]],
    connection_id: str,
    capture_screenshots: bool = True,
) -> EvidenceReport:
    """chain: [(test_case_name, row), ...] — one row per stage, sharing one buffer
    across the whole chain, same semantics as executor.run_chain."""
    with session_factory() as db:
        resolved_by_case = []
        plan_hashes = []
        descriptions = {}
        for name, _ in chain:
            resolved = _resolve_steps_with_captions(db, name)
            resolved_by_case.append((name, resolved))
            plan_hashes.append(_plan_hash([s for s, _, _ in resolved]))
            descriptions[name] = db.query(TestCase).filter_by(name=name).one().description
    plan_hash = _hash_json(plan_hashes)

    started_at = datetime.now(timezone.utc)
    buffer: dict[str, str] = {}
    scenarios: list[EvidenceScenario] = []
    for name, resolved in resolved_by_case:
        row = next(r for n, r in chain if n == name)
        scenario = _run_one_row_with_evidence(
            agent, resolved, row, connection_id, buffer, name, descriptions[name], capture_screenshots,
        )
        scenarios.append(scenario)
        if not scenario.success:
            break
    finished_at = datetime.now(timezone.utc)

    return EvidenceReport(
        run_id=str(uuid.uuid4()), execution_id=str(uuid.uuid4()), plan_hash=plan_hash,
        data_hash=_hash_json([r for _, r in chain]), execution_mode=f"Chain ({len(chain)} stages)",
        started_at=started_at, finished_at=finished_at, executed_by=getuser(),
        environment=_environment_of(agent, connection_id), scenarios=scenarios,
        row={}, final_buffer=buffer,
    )
