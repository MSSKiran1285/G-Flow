import pytest

from smt.engine.message_patterns import extract


def test_extract_order_saved():
    assert extract("order_saved", "Standard Order 1976 has been saved") == "1976"


def test_extract_delivery_saved_matches_the_real_outbound_delivery_wording():
    # Confirmed live: VL01N's real statusbar text is "Outbound Delivery N has been
    # saved", not just "Delivery N has been saved" as originally guessed.
    assert extract("delivery_saved", "Outbound Delivery 80001138 has been saved") == "80001138"


def test_extract_billing_saved_matches_the_real_document_wording():
    # Confirmed live: VF01's real statusbar text is "Document N has been saved", not
    # "Billing document N has been saved" as originally guessed.
    assert extract("billing_saved", "Document 90001005 has been saved") == "90001005"


def test_extract_returns_none_when_the_text_does_not_match():
    assert extract("order_saved", "Please enter a value") is None


def test_extract_raises_on_an_unknown_pattern_name():
    with pytest.raises(ValueError, match="unknown message pattern"):
        extract("not_a_real_pattern", "anything")
