from smt.adapter.generated import uiadapter_pb2 as pb


def _order_spec(name="OrderCase"):
    return {
        "name": name,
        "steps": [
            {
                "module": "VA01_InitialScreen", "attribute": "vbak_auart",
                "action": "SET", "binding": {"type": "column", "value": "order_type"},
            },
            {
                "module": "VA01_InitialScreen", "attribute": "btn_save",
                "action": "PRESS", "binding": {"type": "literal", "value": ""},
                "capture": {"buffer": "order_number", "from": "statusbar", "pattern": "order_saved"},
            },
        ],
    }


def _delivery_spec(name="DeliveryCase"):
    return {
        "name": name,
        "steps": [
            {
                "module": "VA01_InitialScreen", "attribute": "vbak_vkorg",
                "action": "SET", "binding": {"type": "buffer", "value": "order_number"},
            },
            {
                "module": "VA01_InitialScreen", "attribute": "btn_save",
                "action": "PRESS", "binding": {"type": "literal", "value": ""},
                "capture": {"buffer": "delivery_number", "from": "statusbar", "pattern": "delivery_saved"},
            },
        ],
    }


def test_run_test_case_endpoint_returns_row_results(client):
    c, agent = client
    c.post("/api/test-cases", json=_order_spec())
    agent.statusbar_texts = ["Standard Order 1976 has been saved"]

    r = c.post("/api/runs/test-case", json={
        "test_case_name": "OrderCase",
        "rows": [{"order_type": "OR"}],
        "connection_id": "conn1",
    })

    assert r.status_code == 200
    results = r.json()["results"]
    assert len(results) == 1
    assert results[0]["success"] is True
    assert results[0]["buffer"] == {"order_number": "1976"}
    assert ("wnd[0]/usr/ctxtVBAK-AUART", "OR") in agent.sets


def test_run_test_case_reports_which_step_failed(client):
    c, agent = client
    c.post("/api/test-cases", json=_order_spec())
    agent.fail_on = ("wnd[0]/tbar[0]/btn[11]", pb.PRESS)

    r = c.post("/api/runs/test-case", json={
        "test_case_name": "OrderCase",
        "rows": [{"order_type": "OR"}],
        "connection_id": "conn1",
    })

    result = r.json()["results"][0]
    assert result["success"] is False
    assert result["failed_at_step"] == 1
    assert result["message"] == "boom"


def test_run_unknown_test_case_returns_404(client):
    c, _agent = client
    r = c.post("/api/runs/test-case", json={
        "test_case_name": "NopeCase", "rows": [{}], "connection_id": "conn1",
    })
    assert r.status_code == 404


def test_run_chain_shares_a_buffer_across_stages(client):
    c, agent = client
    c.post("/api/test-cases", json=_order_spec())
    c.post("/api/test-cases", json=_delivery_spec())
    agent.statusbar_texts = [
        "Standard Order 1976 has been saved", "Standard Order 1976 has been saved",
        "Delivery 80001234 has been saved", "Delivery 80001234 has been saved",
    ]

    r = c.post("/api/runs/chain", json={
        "stages": [
            {"test_case_name": "OrderCase", "rows": [{"order_type": "OR"}]},
            {"test_case_name": "DeliveryCase", "rows": [{"unused": "x"}]},
        ],
        "connection_id": "conn1",
    })

    assert r.status_code == 200
    row = r.json()["results"][0]
    assert [stage["success"] for stage in row] == [True, True]
    assert row[1]["buffer"] == {"order_number": "1976", "delivery_number": "80001234"}
    assert ("wnd[0]/usr/ctxtVBAK-VKORG", "1976") in agent.sets


def test_run_chain_mismatched_row_counts_returns_400(client):
    c, _agent = client
    c.post("/api/test-cases", json=_order_spec())
    c.post("/api/test-cases", json=_delivery_spec())

    r = c.post("/api/runs/chain", json={
        "stages": [
            {"test_case_name": "OrderCase", "rows": [{"order_type": "OR"}, {"order_type": "ZOR"}]},
            {"test_case_name": "DeliveryCase", "rows": [{"unused": "x"}]},
        ],
        "connection_id": "conn1",
    })
    assert r.status_code == 400


def test_connections_endpoint_reports_unreachable_without_raising(client):
    c, agent = client

    def _boom():
        raise RuntimeError("agent down")

    agent.list_connections = _boom  # type: ignore[method-assign]

    r = c.get("/api/connections")
    assert r.status_code == 200
    body = r.json()
    assert body["reachable"] is False
    assert "agent down" in body["error"]
