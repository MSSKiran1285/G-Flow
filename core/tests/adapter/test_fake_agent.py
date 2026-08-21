from pathlib import Path

import pytest

from smt.adapter.fake_agent import FakeUiAgent, FixtureLookupError
from smt.adapter.generated import uiadapter_pb2 as pb

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "va01_minimal.json"


@pytest.fixture
def agent() -> FakeUiAgent:
    return FakeUiAgent(FIXTURE)


def test_list_connections(agent: FakeUiAgent) -> None:
    result = agent.list_connections()
    assert [c.connection_id for c in result.connections] == ["conn1"]


def test_open_session_returns_recorded_handle(agent: FakeUiAgent) -> None:
    handle = agent.open_session(pb.OpenSessionRequest(connection_id="conn1"))
    assert handle.session_id == "ses1"


def test_scan_screen_round_trips_component_tree(agent: FakeUiAgent) -> None:
    snapshot = agent.scan_screen(pb.ScanRequest(session_id="ses1", root_id="wnd[0]"))
    assert snapshot.context.transaction_code == "VA01"
    assert [c.id for c in snapshot.root.children] == [
        "wnd[0]/usr/ctxtVBAK-AUART",
        "wnd[0]/tbar[0]/btn[11]",
    ]
    assert snapshot.root.children[0].family == pb.FAMILY_TEXT_INPUT


def test_execute_action_set_then_press(agent: FakeUiAgent) -> None:
    set_result = agent.execute_action(
        pb.ActionRequest(
            component_id="wnd[0]/usr/ctxtVBAK-AUART",
            op=pb.SET,
            params=pb.ActionParams(text_value="OR"),
        )
    )
    assert set_result.success
    assert set_result.actual_value == "OR"

    press_result = agent.execute_action(
        pb.ActionRequest(component_id="wnd[0]/tbar[0]/btn[11]", op=pb.PRESS)
    )
    assert press_result.success
    assert press_result.statusbar_deltas[0].text == "Standard Order 1234567 has been saved"


def test_execute_batch_stops_on_failure_with_fail_fast(agent: FakeUiAgent) -> None:
    batch = pb.ActionBatch(
        steps=[
            pb.ActionRequest(component_id="wnd[0]/usr/ctxtVBAK-AUART", op=pb.SET,
                              params=pb.ActionParams(text_value="OR")),
            pb.ActionRequest(component_id="wnd[0]/tbar[0]/btn[11]", op=pb.PRESS),
        ],
        fail_fast=True,
    )
    results = list(agent.execute_batch(batch))
    assert len(results) == 2
    assert all(r.success for r in results)


def test_unrecorded_action_raises_lookup_error(agent: FakeUiAgent) -> None:
    with pytest.raises(FixtureLookupError):
        agent.execute_action(pb.ActionRequest(component_id="wnd[0]/does/not/exist", op=pb.READ))
