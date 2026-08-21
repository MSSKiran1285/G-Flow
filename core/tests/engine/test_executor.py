from pathlib import Path

import pytest

from smt.adapter.generated import uiadapter_pb2 as pb
from smt.engine.executor import define_test_case, run_test_case
from smt.repository.db import init_db, make_engine, make_session_factory
from smt.repository.models import Module, ModuleAttribute


class FakeAgent:
    """Minimal in-process double for UiAgentPort: records every SET it receives and
    fails a chosen (component_id, op) combination on demand, without needing gRPC,
    COM, or a fixture file."""

    def __init__(self, fail_on: tuple[str, int] | None = None):
        self.fail_on = fail_on
        self.sets: list[tuple[str, str]] = []
        self.sessions_opened = 0
        self.sessions_closed = 0

    def open_session(self, request):
        self.sessions_opened += 1
        return pb.SessionHandle(session_id=f"ses{self.sessions_opened}")

    def close_session(self, handle):
        self.sessions_closed += 1
        return pb.Ack(success=True)

    def execute_action(self, request):
        if self.fail_on == (request.component_id, request.op):
            return pb.ActionResult(success=False, error_message="boom")
        if request.op == pb.SET:
            self.sets.append((request.component_id, request.params.text_value))
            return pb.ActionResult(success=True, actual_value=request.params.text_value)
        if request.op == pb.STATUSBAR_READ:
            result = pb.ActionResult(success=True)
            result.statusbar_deltas.add(type="S", text="Standard Order 999 has been saved")
            return result
        return pb.ActionResult(success=True)


@pytest.fixture
def session_factory():
    engine = make_engine(":memory:")
    init_db(engine)
    factory = make_session_factory(engine)
    with factory() as db:
        module = Module(name="VA01_InitialScreen", tcode="VA01", root_id="wnd[0]")
        module.attributes.append(ModuleAttribute(
            semantic_name="vbak_auart", component_id="wnd[0]/usr/ctxtVBAK-AUART", sap_type="GuiCTextField",
        ))
        module.attributes.append(ModuleAttribute(
            semantic_name="vbak_vkorg", component_id="wnd[0]/usr/ctxtVBAK-VKORG", sap_type="GuiCTextField",
        ))
        db.add(module)
        db.commit()
    return factory


@pytest.fixture
def testcase_yaml(tmp_path: Path) -> Path:
    path = tmp_path / "va01.yaml"
    path.write_text(
        """
name: VA01_CreateOrder
description: test
steps:
  - module: VA01_InitialScreen
    attribute: vbak_auart
    action: SET
    bind: "column:order_type"
  - module: VA01_InitialScreen
    attribute: vbak_vkorg
    action: SET
    bind: "column:sales_org"
""",
        encoding="utf-8",
    )
    return path


@pytest.fixture
def sheet_csv(tmp_path: Path) -> Path:
    path = tmp_path / "data.csv"
    path.write_text("order_type,sales_org\nOR,GP01\nZOR,GP02\n", encoding="utf-8")
    return path


def test_define_test_case_persists_steps_in_yaml_order(session_factory, testcase_yaml):
    from smt.repository.models import TestCase

    define_test_case(session_factory, testcase_yaml)

    with session_factory() as db:
        loaded = db.query(TestCase).filter_by(name="VA01_CreateOrder").one()
        assert [s.attribute_semantic_name for s in loaded.steps] == ["vbak_auart", "vbak_vkorg"]
        assert loaded.steps[0].binding_type == "column"
        assert loaded.steps[0].binding_value == "order_type"


def test_run_test_case_executes_one_session_per_row_with_resolved_bindings(session_factory, testcase_yaml, sheet_csv):
    define_test_case(session_factory, testcase_yaml)
    agent = FakeAgent()

    results = run_test_case(agent, session_factory, "VA01_CreateOrder", sheet_csv, connection_id="conn1")

    assert [r.success for r in results] == [True, True]
    assert agent.sessions_opened == 2
    assert agent.sessions_closed == 2
    assert agent.sets == [
        ("wnd[0]/usr/ctxtVBAK-AUART", "OR"),
        ("wnd[0]/usr/ctxtVBAK-VKORG", "GP01"),
        ("wnd[0]/usr/ctxtVBAK-AUART", "ZOR"),
        ("wnd[0]/usr/ctxtVBAK-VKORG", "GP02"),
    ]
    assert "has been saved" in results[0].message


def test_run_test_case_reports_which_step_failed(session_factory, testcase_yaml, sheet_csv):
    define_test_case(session_factory, testcase_yaml)
    agent = FakeAgent(fail_on=("wnd[0]/usr/ctxtVBAK-VKORG", pb.SET))

    results = run_test_case(agent, session_factory, "VA01_CreateOrder", sheet_csv, connection_id="conn1")

    assert results[0].success is False
    assert results[0].failed_at_step == 1
    assert results[0].message == "boom"
