from smt.repository.scanning import _relative_id, _semantic_name
from smt.adapter.generated import uiadapter_pb2 as pb


def test_relative_id_strips_the_connection_session_prefix():
    full = "/app/con[0]/ses[1]/wnd[0]/usr/ctxtVBAK-AUART"
    assert _relative_id(full) == "wnd[0]/usr/ctxtVBAK-AUART"


def test_relative_id_leaves_an_already_short_id_alone():
    assert _relative_id("wnd[0]/usr/ctxtVBAK-AUART") == "wnd[0]/usr/ctxtVBAK-AUART"


def test_semantic_name_prefers_the_sap_name_property():
    node = pb.ComponentNode(id="wnd[0]/usr/ctxtVBAK-AUART", name="VBAK-AUART")
    assert _semantic_name(node) == "vbak_auart"


def test_semantic_name_falls_back_to_the_id_tail_when_name_is_empty():
    node = pb.ComponentNode(id="wnd[0]/tbar[0]/btn[11]", name="")
    assert _semantic_name(node) == "btn_11"
