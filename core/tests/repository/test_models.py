import pytest

from smt.repository.db import init_db, make_engine, make_session_factory
from smt.repository.models import Module, ModuleAttribute, TestCase, TestStep


@pytest.fixture
def session_factory():
    engine = make_engine(":memory:")
    init_db(engine)
    return make_session_factory(engine)


def test_module_and_attributes_round_trip(session_factory):
    with session_factory() as db:
        module = Module(name="VA01_InitialScreen", tcode="VA01", screen_number="4001", root_id="wnd[0]")
        module.attributes.append(ModuleAttribute(
            semantic_name="vbak_auart", component_id="wnd[0]/usr/ctxtVBAK-AUART",
            sap_type="GuiCTextField", supported_action_modes="READ,SET,VERIFY",
        ))
        db.add(module)
        db.commit()

    with session_factory() as db:
        loaded = db.query(Module).filter_by(name="VA01_InitialScreen").one()
        assert loaded.tcode == "VA01"
        assert len(loaded.attributes) == 1
        assert loaded.attributes[0].semantic_name == "vbak_auart"


def test_test_case_steps_preserve_sequence_order(session_factory):
    with session_factory() as db:
        test_case = TestCase(name="VA01_CreateOrder")
        test_case.steps.append(TestStep(sequence_order=1, module_name="M", attribute_semantic_name="b", action_mode="SET"))
        test_case.steps.append(TestStep(sequence_order=0, module_name="M", attribute_semantic_name="a", action_mode="SET"))
        db.add(test_case)
        db.commit()

    with session_factory() as db:
        loaded = db.query(TestCase).filter_by(name="VA01_CreateOrder").one()
        assert [s.attribute_semantic_name for s in loaded.steps] == ["a", "b"]
