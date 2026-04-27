"""Serialization: encoders, sort, multi-values, type coercion."""

from __future__ import annotations

import pytest

from querystring import parse, serialize


def test_dict_serialized_with_plus_encoder_by_default() -> None:
    assert serialize({"q": "hello world"}) == "q=hello+world"


def test_percent_encoder_uses_pct20_for_space() -> None:
    assert serialize({"q": "hello world"}, quote_via="percent") == "q=hello%20world"


def test_callable_quote_via() -> None:
    upper = lambda s: s.upper().replace(" ", "_")
    assert serialize({"q": "hello"}, quote_via=upper) == "Q=HELLO"


def test_invalid_quote_via_string_raises() -> None:
    with pytest.raises(ValueError):
        serialize({"q": "x"}, quote_via="urlsafe")


def test_invalid_quote_via_type_raises() -> None:
    with pytest.raises(ValueError):
        serialize({"q": "x"}, quote_via=123)  # type: ignore[arg-type]


def test_iterable_of_pairs_round_trip() -> None:
    pairs = [("a", "1"), ("b", "2"), ("a", "3")]
    assert serialize(pairs) == "a=1&b=2&a=3"


def test_list_value_expands_to_repeated_keys() -> None:
    assert serialize({"a": ["1", "2"]}) == "a=1&a=2"


def test_tuple_value_expands_to_repeated_keys() -> None:
    assert serialize({"a": ("1", "2")}) == "a=1&a=2"


def test_int_value_coerced_to_str() -> None:
    assert serialize({"n": 42}) == "n=42"


def test_float_value_coerced_to_str() -> None:
    assert serialize({"x": 3.5}) == "x=3.5"


def test_bool_value_lowercase() -> None:
    assert serialize({"on": True, "off": False}) == "on=true&off=false"


def test_none_value_becomes_empty_string() -> None:
    assert serialize({"a": None}) == "a="


def test_none_value_dropped_when_blank_values_false() -> None:
    assert serialize({"a": None, "b": "x"}, blank_values=False) == "b=x"


def test_blank_string_dropped_when_blank_values_false() -> None:
    assert serialize({"a": "", "b": "x"}, blank_values=False) == "b=x"


def test_sort_key_alphabetical() -> None:
    assert serialize({"b": "1", "a": "2", "c": "3"}, sort=True) == "a=2&b=1&c=3"


def test_custom_separator() -> None:
    assert serialize({"a": "1", "b": "2"}, sep=";") == "a=1;b=2"


def test_unicode_value_percent_encoded() -> None:
    assert serialize({"name": "café"}, quote_via="percent") == "name=caf%C3%A9"


def test_special_chars_in_key_are_encoded() -> None:
    assert serialize({"k&v": "x"}) == "k%26v=x"


def test_value_with_ampersand_encoded() -> None:
    assert serialize({"a": "x&y"}) == "a=x%26y"


def test_serialize_rejects_str_input() -> None:
    with pytest.raises(TypeError):
        serialize("a=1")  # type: ignore[arg-type]


def test_serialize_rejects_non_pair_iterable() -> None:
    with pytest.raises(TypeError):
        serialize([("a", "1"), "bad"])  # type: ignore[list-item]


def test_serialize_rejects_three_element_pair() -> None:
    with pytest.raises(TypeError):
        serialize([("a", "1", "extra")])  # type: ignore[list-item]


def test_serialize_rejects_unsupported_value_type() -> None:
    with pytest.raises(TypeError):
        serialize({"a": object()})


def test_serialize_rejects_unsupported_key_type() -> None:
    with pytest.raises(TypeError):
        serialize({(1, 2): "x"})  # type: ignore[dict-item]


def test_serialize_rejects_none_key() -> None:
    with pytest.raises(TypeError):
        serialize([(None, "x")])  # type: ignore[list-item]


def test_serialize_accepts_int_key() -> None:
    assert serialize({1: "a"}) == "1=a"


def test_serialize_accepts_float_key() -> None:
    assert serialize({1.5: "a"}) == "1.5=a"


def test_serialize_accepts_bool_key() -> None:
    assert serialize({True: "a"}) == "true=a"


def test_round_trip_parse_then_serialize() -> None:
    text = "a=1&b=hello+world&c=caf%C3%A9"
    pairs = sum(([(k, v) for v in vs] for k, vs in parse(text).items()), [])
    out = serialize(pairs, quote_via="percent")
    # Pretty-printing differs, but re-parsing must equal original
    assert parse(out) == parse(text)


def test_empty_input_yields_empty_string() -> None:
    assert serialize({}) == ""
    assert serialize([]) == ""
