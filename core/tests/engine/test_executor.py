from pathlib import Path

import pytest

from smt.adapter.generated import uiadapter_pb2 as pb
from smt.engine.executor import _parse_table_cell_id, define_test_case, run_chain, run_test_case
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


@pytest.fixture
def capture_yaml(tmp_path: Path, session_factory) -> Path:
    with session_factory() as db:
        module = db.query(Module).filter_by(name="VA01_InitialScreen").one()
        module.attributes.append(ModuleAttribute(
            semantic_name="btn_save", component_id="wnd[0]/tbar[0]/btn[11]", sap_type="GuiButton",
        ))
        db.commit()

    path = tmp_path / "va01_save.yaml"
    path.write_text(
        """
name: VA01_CreateAndCapture
steps:
  - module: VA01_InitialScreen
    attribute: vbak_auart
    action: SET
    bind: "column:order_type"
  - module: VA01_InitialScreen
    attribute: btn_save
    action: PRESS
    bind: "literal:"
    capture:
      buffer: order_number
      pattern: order_saved
""",
        encoding="utf-8",
    )
    return path


def test_capture_from_statusbar_populates_the_row_buffer(session_factory, capture_yaml, sheet_csv):
    define_test_case(session_factory, capture_yaml)
    agent = FakeAgent(statusbar_texts=["Standard Order 1976 has been saved"])

    results = run_test_case(agent, session_factory, "VA01_CreateAndCapture", sheet_csv, connection_id="conn1")

    assert results[0].success is True
    assert results[0].buffer == {"order_number": "1976"}


def test_capture_pattern_mismatch_fails_the_row_with_a_clear_message(session_factory, capture_yaml, sheet_csv):
    define_test_case(session_factory, capture_yaml)
    agent = FakeAgent(statusbar_texts=["Please enter a value"])

    results = run_test_case(agent, session_factory, "VA01_CreateAndCapture", sheet_csv, connection_id="conn1")

    assert results[0].success is False
    assert "did not match" in results[0].message


@pytest.fixture
def chain_setup(tmp_path: Path, session_factory):
    with session_factory() as db:
        module = db.query(Module).filter_by(name="VA01_InitialScreen").one()
        module.attributes.append(ModuleAttribute(
            semantic_name="btn_save", component_id="wnd[0]/tbar[0]/btn[11]", sap_type="GuiButton",
        ))
        db.commit()

    order_yaml = tmp_path / "order.yaml"
    order_yaml.write_text(
        """
name: OrderCase
steps:
  - module: VA01_InitialScreen
    attribute: vbak_auart
    action: SET
    bind: "column:order_type"
  - module: VA01_InitialScreen
    attribute: btn_save
    action: PRESS
    bind: "literal:"
    capture: {buffer: order_number, pattern: order_saved}
""",
        encoding="utf-8",
    )
    delivery_yaml = tmp_path / "delivery.yaml"
    delivery_yaml.write_text(
        """
name: DeliveryCase
steps:
  - module: VA01_InitialScreen
    attribute: vbak_vkorg
    action: SET
    bind: "buffer:order_number"
  - module: VA01_InitialScreen
    attribute: btn_save
    action: PRESS
    bind: "literal:"
    capture: {buffer: delivery_number, pattern: delivery_saved}
""",
        encoding="utf-8",
    )
    define_test_case(session_factory, order_yaml)
    define_test_case(session_factory, delivery_yaml)

    orders_csv = tmp_path / "orders.csv"
    orders_csv.write_text("order_type\nOR\n", encoding="utf-8")
    deliveries_csv = tmp_path / "deliveries.csv"
    deliveries_csv.write_text("unused\nx\n", encoding="utf-8")
    return orders_csv, deliveries_csv


def test_run_chain_shares_a_buffer_across_test_cases(session_factory, chain_setup):
    orders_csv, deliveries_csv = chain_setup
    agent = FakeAgent(statusbar_texts=[
        "Standard Order 1976 has been saved", "Standard Order 1976 has been saved",
        "Delivery 80001234 has been saved", "Delivery 80001234 has been saved",
    ])

    results = run_chain(
        agent, session_factory,
        chain=[("OrderCase", orders_csv), ("DeliveryCase", deliveries_csv)],
        connection_id="conn1",
    )

    assert len(results) == 1  # one row
    row = results[0]
    assert [r.success for r in row] == [True, True]
    assert row[1].buffer == {"order_number": "1976", "delivery_number": "80001234"}
    assert ("wnd[0]/usr/ctxtVBAK-VKORG", "1976") in agent.sets  # DeliveryCase bound the captured order number


def test_parse_table_cell_id_splits_table_and_column():
    table_id, column = _parse_table_cell_id(
        "wnd[0]/usr/tblSAPMV45ATC_TC_ITEM_OVERVIEW/ctxtRV45A-MABNR[1,3]"
    )
    assert table_id == "wnd[0]/usr/tblSAPMV45ATC_TC_ITEM_OVERVIEW"
    assert column == "1"


def test_parse_table_cell_id_rejects_a_non_table_component_id():
    with pytest.raises(ValueError, match="captured table-cell attribute"):
        _parse_table_cell_id("wnd[0]/usr/ctxtVBAK-AUART")


@pytest.fixture
def table_row_yaml(tmp_path: Path, session_factory) -> Path:
    with session_factory() as db:
        module = db.query(Module).filter_by(name="VA01_InitialScreen").one()
        module.attributes.append(ModuleAttribute(
            semantic_name="item_qty",
            component_id="wnd[0]/usr/tblSAPMV45ATC_TC_ITEM_OVERVIEW/ctxtRV45A-KWMENG[3,0]",
            sap_type="GuiCTextField",
        ))
        db.commit()

    path = tmp_path / "va01_item.yaml"
    path.write_text(
        """
name: VA01_SetItemQuantity
steps:
  - module: VA01_InitialScreen
    attribute: item_qty
    action: TABLE_SET_CELL
    bind: "column:quantity"
    row_bind: "column:item_row"
""",
        encoding="utf-8",
    )
    return path


def test_table_set_cell_targets_the_table_with_a_data_driven_row(session_factory, table_row_yaml, tmp_path):
    define_test_case(session_factory, table_row_yaml)
    sheet = tmp_path / "items.csv"
    sheet.write_text("quantity,item_row\n5,0\n12,1\n", encoding="utf-8")
    agent = FakeAgent()

    results = run_test_case(agent, session_factory, "VA01_SetItemQuantity", sheet, connection_id="conn1")

    assert [r.success for r in results] == [True, True]
    assert agent.table_calls == [
        ("wnd[0]/usr/tblSAPMV45ATC_TC_ITEM_OVERVIEW", 0, "3", "TABLE_SET_CELL"),
        ("wnd[0]/usr/tblSAPMV45ATC_TC_ITEM_OVERVIEW", 1, "3", "TABLE_SET_CELL"),
    ]


def test_table_row_binding_reports_a_clear_error_for_a_non_numeric_row(session_factory, table_row_yaml, tmp_path):
    define_test_case(session_factory, table_row_yaml)
    sheet = tmp_path / "items.csv"
    sheet.write_text("quantity,item_row\n5,not-a-number\n", encoding="utf-8")
    agent = FakeAgent()

    results = run_test_case(agent, session_factory, "VA01_SetItemQuantity", sheet, connection_id="conn1")

    assert results[0].success is False
    assert "numeric table row" in results[0].message


def test_run_chain_stops_a_row_at_the_first_failing_test_case(session_factory, chain_setup):
    orders_csv, deliveries_csv = chain_setup
    agent = FakeAgent(fail_on=("wnd[0]/tbar[0]/btn[11]", pb.PRESS))

    results = run_chain(
        agent, session_factory,
        chain=[("OrderCase", orders_csv), ("DeliveryCase", deliveries_csv)],
        connection_id="conn1",
    )

    assert len(results[0]) == 1  # DeliveryCase never ran
    assert results[0][0].success is False
    assert agent.sessions_opened == 1
