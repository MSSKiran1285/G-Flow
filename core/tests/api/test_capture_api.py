import time

from smt.adapter.generated import uiadapter_pb2 as pb


def _wait_until(predicate, timeout=2.0, interval=0.02):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return predicate()


def test_start_then_poll_returns_picked_components(client):
    c, agent = client
    agent.picked_components = [
        pb.PickedComponent(component_id="/app/con[0]/ses[0]/wnd[0]/usr/ctxtVBAK-AUART", type="GuiCTextField", name="VBAK-AUART"),
        pb.PickedComponent(component_id="/app/con[0]/ses[0]/wnd[0]/usr/ctxtVBAK-VKORG", type="GuiCTextField", name="VBAK-VKORG"),
    ]

    r = c.post("/api/modules/capture/start", json={"tcode": "VA01", "connection_id": "conn1"})
    assert r.status_code == 200
    capture_id = r.json()["capture_id"]

    def got_both():
        poll = c.get(f"/api/modules/capture/{capture_id}/poll").json()
        got_both.seen.extend(poll["components"])
        return len(got_both.seen) >= 2

    got_both.seen = []
    assert _wait_until(got_both)
    ids = {comp["component_id"] for comp in got_both.seen}
    assert ids == {"wnd[0]/usr/ctxtVBAK-AUART", "wnd[0]/usr/ctxtVBAK-VKORG"}

    stopped = c.post(f"/api/modules/capture/{capture_id}/stop")
    assert stopped.status_code == 200
    assert agent.last_picker_call.cancelled is True


def test_poll_passes_through_the_agent_resolved_caption(client):
    c, agent = client
    agent.picked_components = [
        pb.PickedComponent(
            component_id="/app/con[0]/ses[0]/wnd[0]/usr/ctxtVBAK-AUART",
            type="GuiCTextField", name="VBAK-AUART", text="OR", caption="Order Type",
        ),
    ]

    capture_id = c.post("/api/modules/capture/start", json={"tcode": "VA01", "connection_id": "conn1"}).json()["capture_id"]

    def got_one():
        poll = c.get(f"/api/modules/capture/{capture_id}/poll").json()
        got_one.seen.extend(poll["components"])
        return len(got_one.seen) >= 1

    got_one.seen = []
    assert _wait_until(got_one)
    assert got_one.seen[0]["caption"] == "Order Type"
    assert got_one.seen[0]["label"] == "OR"

    c.post(f"/api/modules/capture/{capture_id}/stop")


def test_poll_does_not_duplicate_the_same_component_clicked_twice(client):
    c, agent = client
    same = pb.PickedComponent(component_id="/app/con[0]/ses[0]/wnd[0]/usr/ctxtVBAK-AUART", type="GuiCTextField", name="VBAK-AUART")
    agent.picked_components = [same, same]

    r = c.post("/api/modules/capture/start", json={"tcode": "VA01", "connection_id": "conn1"})
    capture_id = r.json()["capture_id"]

    # drain until the fake stream (2 identical items) has been fully consumed
    collected = []
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline:
        poll = c.get(f"/api/modules/capture/{capture_id}/poll").json()
        collected.extend(poll["components"])
        if not poll["active"]:
            break
        time.sleep(0.02)

    assert len(collected) == 1
    assert collected[0]["component_id"] == "wnd[0]/usr/ctxtVBAK-AUART"

    c.post(f"/api/modules/capture/{capture_id}/stop")


def test_poll_unknown_capture_id_returns_404(client):
    c, _agent = client
    assert c.get("/api/modules/capture/does-not-exist/poll").status_code == 404


def test_stop_unknown_capture_id_returns_404(client):
    c, _agent = client
    assert c.post("/api/modules/capture/does-not-exist/stop").status_code == 404


def test_stop_twice_returns_404_the_second_time(client):
    c, agent = client
    agent.picked_components = []

    capture_id = c.post("/api/modules/capture/start", json={"tcode": "VA01", "connection_id": "conn1"}).json()["capture_id"]
    assert c.post(f"/api/modules/capture/{capture_id}/stop").status_code == 200
    assert c.post(f"/api/modules/capture/{capture_id}/stop").status_code == 404
