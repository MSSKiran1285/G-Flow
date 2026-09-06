def _spec(name="VA01_CreateOrder"):
    return {
        "name": name,
        "description": "test",
        "steps": [
            {
                "module": "VA01_InitialScreen", "attribute": "vbak_auart",
                "action": "SET", "binding": {"type": "column", "value": "order_type"},
            },
            {
                "module": "VA01_InitialScreen", "attribute": "vbak_vkorg",
                "action": "SET", "binding": {"type": "column", "value": "sales_org"},
            },
            {
                "module": "VA01_InitialScreen", "attribute": "btn_save",
                "action": "PRESS", "binding": {"type": "literal", "value": ""},
                "capture": {"buffer": "order_number", "from": "statusbar", "pattern": "order_saved"},
            },
        ],
    }


def test_define_then_get_round_trips_steps_in_order(client):
    c, _agent = client

    r = c.post("/api/test-cases", json=_spec())
    assert r.status_code == 200
    assert r.json()["name"] == "VA01_CreateOrder"

    detail = c.get("/api/test-cases/VA01_CreateOrder").json()
    steps = detail["steps"]
    assert [s["attribute_semantic_name"] for s in steps] == ["vbak_auart", "vbak_vkorg", "btn_save"]
    assert steps[0]["binding_type"] == "column"
    assert steps[0]["binding_value"] == "order_type"
    assert steps[2]["capture_buffer_key"] == "order_number"
    assert steps[2]["capture_from"] == "statusbar"
    assert steps[2]["capture_pattern"] == "order_saved"


def test_redefining_the_same_name_replaces_it(client):
    c, _agent = client
    c.post("/api/test-cases", json=_spec())

    smaller = _spec()
    smaller["steps"] = smaller["steps"][:1]
    c.post("/api/test-cases", json=smaller)

    detail = c.get("/api/test-cases/VA01_CreateOrder").json()
    assert len(detail["steps"]) == 1


def test_list_test_cases_reports_step_count(client):
    c, _agent = client
    c.post("/api/test-cases", json=_spec())

    r = c.get("/api/test-cases")
    assert r.status_code == 200
    row = next(tc for tc in r.json() if tc["name"] == "VA01_CreateOrder")
    assert row["step_count"] == 3


def test_delete_test_case(client):
    c, _agent = client
    c.post("/api/test-cases", json=_spec())

    r = c.delete("/api/test-cases/VA01_CreateOrder")
    assert r.status_code == 204
    assert c.get("/api/test-cases/VA01_CreateOrder").status_code == 404


def test_get_unknown_test_case_returns_404(client):
    c, _agent = client
    assert c.get("/api/test-cases/DoesNotExist").status_code == 404


def test_unknown_action_name_returns_422(client):
    c, _agent = client
    bad = _spec()
    bad["steps"][0]["action"] = "NOT_A_REAL_ACTION"
    r = c.post("/api/test-cases", json=bad)
    assert r.status_code == 422


def test_step_needs_either_raw_component_id_or_module_and_attribute(client):
    c, _agent = client
    bad = _spec()
    bad["steps"][0] = {"action": "SET", "binding": {"type": "literal", "value": "x"}}
    r = c.post("/api/test-cases", json=bad)
    assert r.status_code == 422


def test_row_binding_round_trips_for_a_table_step(client):
    c, _agent = client
    spec = _spec()
    spec["steps"].append({
        "module": "VA01_InitialScreen", "attribute": "item_qty",
        "action": "TABLE_SET_CELL", "binding": {"type": "column", "value": "quantity"},
        "row_binding": {"type": "column", "value": "item_row"},
    })

    r = c.post("/api/test-cases", json=spec)
    assert r.status_code == 200

    detail = c.get("/api/test-cases/VA01_CreateOrder").json()
    table_step = next(s for s in detail["steps"] if s["action_mode"] == "TABLE_SET_CELL")
    assert table_step["row_binding_type"] == "column"
    assert table_step["row_binding_value"] == "item_row"


def test_row_binding_defaults_to_literal_zero_when_omitted(client):
    c, _agent = client
    r = c.post("/api/test-cases", json=_spec())
    assert r.status_code == 200

    detail = c.get("/api/test-cases/VA01_CreateOrder").json()
    assert all(s["row_binding_type"] == "literal" for s in detail["steps"])
    assert all(s["row_binding_value"] == "" for s in detail["steps"])
