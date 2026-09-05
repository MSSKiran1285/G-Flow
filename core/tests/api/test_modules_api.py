from smt.adapter.generated import uiadapter_pb2 as pb


def test_list_modules_returns_the_seeded_module(client):
    c, _agent = client
    r = c.get("/api/modules")
    assert r.status_code == 200
    names = [m["name"] for m in r.json()]
    assert "VA01_InitialScreen" in names


def test_get_module_returns_its_attributes(client):
    c, _agent = client
    r = c.get("/api/modules/VA01_InitialScreen")
    assert r.status_code == 200
    body = r.json()
    assert body["tcode"] == "VA01"
    semantic_names = {a["semantic_name"] for a in body["attributes"]}
    assert semantic_names == {"vbak_auart", "vbak_vkorg", "btn_save"}


def test_get_unknown_module_returns_404(client):
    c, _agent = client
    r = c.get("/api/modules/DoesNotExist")
    assert r.status_code == 404


def test_scan_preview_returns_candidates_without_persisting_anything(client):
    c, agent = client

    snapshot = pb.ScreenSnapshot()
    snapshot.root.id = "/app/con[0]/ses[0]/wnd[0]"
    snapshot.root.type = "GuiMainWindow"
    field = snapshot.root.children.add()
    field.id = "/app/con[0]/ses[0]/wnd[0]/usr/ctxtVBAK-VTWEG"
    field.type = "GuiCTextField"
    field.name = "VBAK-VTWEG"
    button = snapshot.root.children.add()
    button.id = "/app/con[0]/ses[0]/wnd[0]/tbar[0]/btn[11]"
    button.type = "GuiButton"
    button.name = "btn[11]"
    agent.scan_result = snapshot

    r = c.post("/api/modules/scan-preview", json={"tcode": "VA01", "connection_id": "conn1"})
    assert r.status_code == 200
    body = r.json()
    assert body["tcode"] == "VA01"
    component_ids = {comp["component_id"] for comp in body["components"]}
    assert "wnd[0]/usr/ctxtVBAK-VTWEG" in component_ids
    assert "wnd[0]/tbar[0]/btn[11]" in component_ids
    assert all(comp["window"] == "wnd[0]" for comp in body["components"])

    # nothing persisted by the preview alone — only the fixture-seeded module exists
    assert [m["name"] for m in c.get("/api/modules").json()] == ["VA01_InitialScreen"]


def test_save_module_persists_only_the_curated_selection(client):
    c, _agent = client

    r = c.post("/api/modules", json={
        "module_name": "VA01_Curated",
        "tcode": "VA01",
        "root_id": "wnd[0]",
        "attributes": [
            {
                "semantic_name": "distribution_channel",
                "component_id": "wnd[0]/usr/ctxtVBAK-VTWEG",
                "sap_type": "GuiCTextField",
                "supported_action_modes": ["SET", "READ"],
            },
        ],
    })
    assert r.status_code == 200
    assert r.json()["attribute_count"] == 1

    detail = c.get("/api/modules/VA01_Curated").json()
    assert [a["semantic_name"] for a in detail["attributes"]] == ["distribution_channel"]
    assert detail["attributes"][0]["supported_action_modes"] == ["SET", "READ"]


def test_scan_module_persists_a_new_module(client):
    c, agent = client

    snapshot = pb.ScreenSnapshot()
    snapshot.root.id = "/app/con[0]/ses[0]/wnd[0]"
    snapshot.root.type = "GuiMainWindow"
    field = snapshot.root.children.add()
    field.id = "/app/con[0]/ses[0]/wnd[0]/usr/ctxtVBAK-VTWEG"
    field.type = "GuiCTextField"
    field.name = "VBAK-VTWEG"
    agent.scan_result = snapshot

    r = c.post("/api/modules/scan", json={
        "module_name": "VA01_Extra",
        "tcode": "VA01",
        "connection_id": "conn1",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["module_name"] == "VA01_Extra"
    assert body["attribute_count"] == 2  # root wnd[0] + the one child field

    detail = c.get("/api/modules/VA01_Extra").json()
    assert any(a["component_id"] == "wnd[0]/usr/ctxtVBAK-VTWEG" for a in detail["attributes"])
