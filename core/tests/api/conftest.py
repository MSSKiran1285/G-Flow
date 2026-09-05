import pytest
from fastapi.testclient import TestClient

from smt.api.app import create_app
from smt.repository.db import init_db, make_engine, make_session_factory
from smt.repository.models import Module, ModuleAttribute
from tests.support.fake_agent import FakeAgent


@pytest.fixture
def session_factory():
    """Same seed shape as tests/engine/test_executor.py's fixture: one Module with two
    settable attributes plus a save button, enough for a real TestCase to be defined
    and run against."""
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
        module.attributes.append(ModuleAttribute(
            semantic_name="btn_save", component_id="wnd[0]/tbar[0]/btn[11]", sap_type="GuiButton",
        ))
        db.add(module)
        db.commit()
    return factory


@pytest.fixture
def client(session_factory):
    agent = FakeAgent()
    app = create_app(agent=agent, session_factory=session_factory)
    with TestClient(app) as c:
        yield c, agent
