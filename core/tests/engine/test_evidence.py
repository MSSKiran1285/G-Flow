import pytest

from smt.engine.evidence import capture_chain_evidence, capture_test_case_evidence
from smt.engine.executor import define_test_case_from_spec
from smt.repository.db import init_db, make_engine, make_session_factory
from smt.repository.models import Module, ModuleAttribute
from tests.support.fake_agent import FakeAgent


@pytest.fixture
def session_factory():
    engine = make_engine(":memory:")
    init_db(engine)
    factory = make_session_factory(engine)
    with factory() as db:
        module = Module(name="VA01_InitialScreen", tcode="VA01", root_id="wnd[0]")
        module.attributes.append(ModuleAttribute(
            semantic_name="vbak_auart", component_id="wnd[0]/usr/ctxtVBAK-AUART",
            sap_type="GuiCTextField", caption="Order Type",
        ))
        module.attributes.append(ModuleAttribute(
            semantic_name="btn_save", component_id="wnd[0]/tbar[0]/btn[11]",
            sap_type="GuiButton", caption="Save",
        ))
        db.add(module)
        db.commit()
        define_test_case_from_spec(factory, {
            "name": "VA01_CreateOrder",
            "description": "test",
            "steps": [
                {"module": "VA01_InitialScreen", "attribute": "vbak_auart", "action": "SET", "bind": "column:order_type"},
                {
                    "module": "VA01_InitialScreen", "attribute": "btn_save", "action": "PRESS", "bind": "literal:",
                    "capture": {"buffer": "order_number", "pattern": "order_saved"},
                },
            ],
        })
    return factory


def test_capture_test_case_evidence_records_timing_and_screenshots(session_factory):
    agent = FakeAgent(statusbar_texts=["Standard Order 1976 has been saved"])

    report = capture_test_case_evidence(
        agent, session_factory, "VA01_CreateOrder", {"order_type": "OR"}, connection_id="conn1",
    )

    assert report.success is True
    assert len(report.scenarios) == 1
    steps = report.scenarios[0].steps
    assert len(steps) == 2
    assert steps[0].description == "Entered Order Type = 'OR'"
    assert steps[0].value_entered == "OR"
    assert steps[0].duration_ms >= 0
    assert steps[0].screenshot_png == b"fake-png-bytes"
    assert steps[1].description == "Clicked Save"
    assert steps[1].captured == "order_number = 1976"
    assert report.final_buffer == {"order_number": "1976"}
    assert agent.screenshots_captured == 2
    # real, derived hashes — not fabricated placeholders
    assert len(report.plan_hash) == 64
    assert len(report.data_hash) == 64
    assert report.run_id != report.execution_id


def test_capture_test_case_evidence_stops_and_flags_failure(session_factory):
    from smt.adapter.generated import uiadapter_pb2 as pb

    agent = FakeAgent(fail_on=("wnd[0]/usr/ctxtVBAK-AUART", pb.SET))

    report = capture_test_case_evidence(
        agent, session_factory, "VA01_CreateOrder", {"order_type": "OR"}, connection_id="conn1",
    )

    assert report.success is False
    steps = report.scenarios[0].steps
    assert len(steps) == 1  # stopped after the failing step, never reached Save
    assert steps[0].success is False
    assert steps[0].error == "boom"


def test_capture_chain_evidence_shares_buffer_across_stages(session_factory):
    with session_factory() as db:
        module = db.query(Module).filter_by(name="VA01_InitialScreen").one()
        module.attributes.append(ModuleAttribute(
            semantic_name="vbak_vkorg", component_id="wnd[0]/usr/ctxtVBAK-VKORG",
            sap_type="GuiCTextField", caption="Sales Org",
        ))
        db.commit()
    define_test_case_from_spec(session_factory, {
        "name": "VL01N_CreateDelivery",
        "steps": [
            {"module": "VA01_InitialScreen", "attribute": "vbak_vkorg", "action": "SET", "bind": "buffer:order_number"},
        ],
    })

    agent = FakeAgent(statusbar_texts=["Standard Order 1976 has been saved"])

    report = capture_chain_evidence(
        agent, session_factory,
        chain=[("VA01_CreateOrder", {"order_type": "OR"}), ("VL01N_CreateDelivery", {})],
        connection_id="conn1",
    )

    assert report.execution_mode == "Chain (2 stages)"
    assert len(report.scenarios) == 2
    assert report.scenarios[1].steps[0].value_entered == "1976"
    assert ("wnd[0]/usr/ctxtVBAK-VKORG", "1976") in agent.sets
