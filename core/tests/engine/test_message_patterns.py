import pytest

from smt.engine.message_patterns import extract


def test_extract_order_saved():
    assert extract("order_saved", "Standard Order 1976 has been saved") == "1976"


def test_extract_returns_none_when_the_text_does_not_match():
    assert extract("order_saved", "Please enter a value") is None


def test_extract_raises_on_an_unknown_pattern_name():
    with pytest.raises(ValueError, match="unknown message pattern"):
        extract("not_a_real_pattern", "anything")
