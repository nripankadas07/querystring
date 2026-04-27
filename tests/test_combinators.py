"""merge, pick, omit operating on the wire format."""

from __future__ import annotations

import pytest

from querystring import merge, omit, parse, pick


def test_merge_two_disjoint_strings_concatenates() -> None:
    assert parse(merge("a=1", "b=2")) == {"a": ["1"], "b": ["2"]}


def test_merge_overrides_overlapping_keys() -> None:
    assert parse(merge("a=1&b=2", "b=99")) == {"a": ["1"], "b": ["99"]}


def test_merge_replaces_entire_value_list() -> None:
    out = merge("a=1&a=2&b=3", "a=99")
    parsed = parse(out)
    assert parsed["a"] == ["99"]
    assert parsed["b"] == ["3"]


def test_merge_preserves_insertion_order_of_keys() -> None:
    out = merge("c=3&a=1", "b=2")
    assert out.split("&") == ["c=3", "a=1", "b=2"]


def test_merge_accepts_mixed_strings_and_dicts() -> None:
    out = merge("a=1", {"b": "2"}, [("c", "3")])
    assert parse(out) == {"a": ["1"], "b": ["2"], "c": ["3"]}


def test_merge_with_no_inputs_returns_empty() -> None:
    assert merge() == ""


def test_merge_uses_lax_decoding_for_strings() -> None:
    # Bad percent encoding should not raise here (lax mode).
    out = merge("a=%2", "b=2")
    assert "b=2" in out


def test_merge_custom_separator() -> None:
    out = merge("a=1;b=2", "c=3", sep=";")
    assert out.split(";") == ["a=1", "b=2", "c=3"]


def test_merge_uses_percent_encoder_when_requested() -> None:
    out = merge({"q": "hello world"}, quote_via="percent")
    assert out == "q=hello%20world"


def test_pick_keeps_only_named_keys() -> None:
    assert pick("a=1&b=2&c=3", "a", "c") == "a=1&c=3"


def test_pick_preserves_multi_value_for_named_keys() -> None:
    assert pick("a=1&b=2&a=3", "a") == "a=1&a=3"


def test_pick_returns_empty_when_no_keys_match() -> None:
    assert pick("a=1&b=2", "x") == ""


def test_pick_with_no_keys_returns_empty() -> None:
    assert pick("a=1&b=2") == ""


def test_pick_preserves_separator() -> None:
    assert pick("a=1;b=2;c=3", "a", "c", sep=";") == "a=1;c=3"


def test_omit_drops_named_keys() -> None:
    assert omit("a=1&b=2&c=3", "b") == "a=1&c=3"


def test_omit_drops_all_values_for_multi_value_key() -> None:
    assert omit("a=1&b=2&a=3", "a") == "b=2"


def test_omit_no_keys_returns_serialized_input() -> None:
    out = omit("a=1&b=2")
    assert parse(out) == {"a": ["1"], "b": ["2"]}


def test_omit_preserves_separator() -> None:
    assert omit("a=1;b=2;c=3", "b", sep=";") == "a=1;c=3"


def test_omit_unknown_key_is_a_noop() -> None:
    assert omit("a=1&b=2", "x", "y") == "a=1&b=2"


def test_pick_returns_unicode_when_input_is_unicode() -> None:
    assert pick("name=caf%C3%A9&other=1", "name", quote_via="percent") == "name=caf%C3%A9"


def test_merge_three_layers_last_wins() -> None:
    out = merge("a=1", "a=2", "a=3")
    assert out == "a=3"


def test_pick_rejects_non_string_query() -> None:
    with pytest.raises(TypeError):
        pick(123, "a")  # type: ignore[arg-type]


def test_omit_rejects_non_string_query() -> None:
    with pytest.raises(TypeError):
        omit(123, "a")  # type: ignore[arg-type]
