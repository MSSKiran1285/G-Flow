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


def test_scan_preview_resolves_the_caption_from_a_sibling_label(client):
    c, agent = client

    snapshot = pb.ScreenSnapshot()
    snapshot.root.id = "/app/con[0]/ses[0]/wnd[0]"
    snapshot.root.type = "GuiMainWindow"
    label = snapshot.root.children.add()
    label.id = "/app/con[0]/ses[0]/wnd[0]/usr/lblVBAK-VTWEG"
    label.type = "GuiLabel"
    label.text = "Distribution Channel"
    field = snapshot.root.children.add()
    field.id = "/app/con[0]/ses[0]/wnd[0]/usr/ctxtVBAK-VTWEG"
    field.type = "GuiCTextField"
    field.name = "VBAK-VTWEG"
    field.text = "G1"
    agent.scan_result = snapshot

    r = c.post("/api/modules/scan-preview", json={"tcode": "VA01", "connection_id": "conn1"})
    assert r.status_code == 200
    by_id = {comp["component_id"]: comp for comp in r.json()["components"]}
    assert by_id["wnd[0]/usr/ctxtVBAK-VTWEG"]["caption"] == "Distribution Channel"
    assert by_id["wnd[0]/usr/ctxtVBAK-VTWEG"]["label"] == "G1"  # the current value, not the caption
    assert by_id["wnd[0]/usr/lblVBAK-VTWEG"]["caption"] == ""  # a label has no caption of its own


def test_scan_preview_falls_back_to_a_positionally_adjacent_caption(client):
    c, agent = client

    # Mirrors the real VA01 screen: VBAK-AUART's caption is rendered by an unrelated
    # read-only GuiTextField (RV45A-TXT_AUART), not a lbl-prefixed id sibling.
    snapshot = pb.ScreenSnapshot()
    snapshot.root.id = "/app/con[0]/ses[0]/wnd[0]"
    snapshot.root.type = "GuiMainWindow"
    snapshot.root.width = 800
    snapshot.root.height = 600
    caption = snapshot.root.children.add()
    caption.id = "/app/con[0]/ses[0]/wnd[0]/usr/txtRV45A-TXT_AUART"
    caption.type = "GuiTextField"
    caption.text = "Order Type"
    caption.changeable = False
    caption.screen_left, caption.screen_top, caption.width, caption.height = 10, 100, 80, 20
    field = snapshot.root.children.add()
    field.id = "/app/con[0]/ses[0]/wnd[0]/usr/ctxtVBAK-AUART"
    field.type = "GuiCTextField"
    field.name = "VBAK-AUART"
    field.text = "OR"
    field.changeable = True
    field.screen_left, field.screen_top, field.width, field.height = 100, 100, 50, 20
    agent.scan_result = snapshot

    r = c.post("/api/modules/scan-preview", json={"tcode": "VA01", "connection_id": "conn1"})
    assert r.status_code == 200
    by_id = {comp["component_id"]: comp for comp in r.json()["components"]}
    assert by_id["wnd[0]/usr/ctxtVBAK-AUART"]["caption"] == "Order Type"


def test_scan_preview_uses_the_button_s_own_text_as_its_caption(client):
    c, agent = client

    snapshot = pb.ScreenSnapshot()
    snapshot.root.id = "/app/con[0]/ses[0]/wnd[0]"
    snapshot.root.type = "GuiMainWindow"
    button = snapshot.root.children.add()
    button.id = "/app/con[0]/ses[0]/wnd[0]/tbar[1]/btn[11]"
    button.type = "GuiButton"
    button.text = "Save"
    agent.scan_result = snapshot

    r = c.post("/api/modules/scan-preview", json={"tcode": "VA01", "connection_id": "conn1"})
    assert r.status_code == 200
    by_id = {comp["component_id"]: comp for comp in r.json()["components"]}
    assert by_id["wnd[0]/tbar[1]/btn[11]"]["caption"] == "Save"


def test_scan_preview_resolves_a_table_cell_s_caption_from_its_column_title(client):
    c, agent = client

    # Mirrors VA01's item overview table: a classic GuiTableControl (not an ALV grid),
    # whose column titles come from GuiTableControl.Columns, not any GuiLabel sibling.
    snapshot = pb.ScreenSnapshot()
    snapshot.root.id = "/app/con[0]/ses[0]/wnd[0]"
    snapshot.root.type = "GuiMainWindow"
    table = snapshot.root.children.add()
    table.id = "/app/con[0]/ses[0]/wnd[0]/usr/tblSAPMV45ATCTRL_UEBERSICHT"
    table.type = "GuiTableControl"
    table.table_detail.columns.add(title="Item")
    table.table_detail.columns.add(title="Material")
    table.table_detail.columns.add(title="Order Quantity")
    cell = table.children.add()
    cell.id = "/app/con[0]/ses[0]/wnd[0]/usr/tblSAPMV45ATCTRL_UEBERSICHT/ctxtRV45A-MABNR[1,3]"
    cell.type = "GuiCTextField"
    cell.name = "RV45A-MABNR"
    agent.scan_result = snapshot

    r = c.post("/api/modules/scan-preview", json={"tcode": "VA01", "connection_id": "conn1"})
    assert r.status_code == 200
    by_id = {comp["component_id"]: comp for comp in r.json()["components"]}
    assert by_id["wnd[0]/usr/tblSAPMV45ATCTRL_UEBERSICHT/ctxtRV45A-MABNR[1,3]"]["caption"] == "Material"


def test_scan_preview_resolves_the_window_title_for_every_component(client):
    c, agent = client

    snapshot = pb.ScreenSnapshot()
    snapshot.root.id = "/app/con[0]/ses[0]/wnd[0]"
    snapshot.root.type = "GuiMainWindow"
    snapshot.root.text = "Create Sales Order: Initial Screen"
    field = snapshot.root.children.add()
    field.id = "/app/con[0]/ses[0]/wnd[0]/usr/ctxtVBAK-AUART"
    field.type = "GuiCTextField"
    field.name = "VBAK-AUART"
    agent.scan_result = snapshot

    r = c.post("/api/modules/scan-preview", json={"tcode": "VA01", "connection_id": "conn1"})
    assert r.status_code == 200
    by_id = {comp["component_id"]: comp for comp in r.json()["components"]}
    assert by_id["wnd[0]/usr/ctxtVBAK-AUART"]["window_title"] == "Create Sales Order: Initial Screen"
    assert by_id["wnd[0]"]["window_title"] == "Create Sales Order: Initial Screen"


def test_save_module_persists_the_window_title(client):
    c, _agent = client

    r = c.post("/api/modules", json={
        "module_name": "VA01_WithWindowTitle",
        "tcode": "VA01",
        "attributes": [
            {
                "semantic_name": "order_type",
                "component_id": "wnd[0]/usr/ctxtVBAK-AUART",
                "sap_type": "GuiCTextField",
                "window_title": "Create Sales Order: Initial Screen",
            },
        ],
    })
    assert r.status_code == 200

    detail = c.get("/api/modules/VA01_WithWindowTitle").json()
    assert detail["attributes"][0]["window_title"] == "Create Sales Order: Initial Screen"


def test_save_module_persists_the_caption(client):
    c, _agent = client

    r = c.post("/api/modules", json={
        "module_name": "VA01_WithCaption",
        "tcode": "VA01",
        "attributes": [
            {
                "semantic_name": "distribution_channel",
                "component_id": "wnd[0]/usr/ctxtVBAK-VTWEG",
                "sap_type": "GuiCTextField",
                "caption": "Distribution Channel",
            },
        ],
    })
    assert r.status_code == 200

    detail = c.get("/api/modules/VA01_WithCaption").json()
    assert detail["attributes"][0]["caption"] == "Distribution Channel"


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
