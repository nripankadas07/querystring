"""Parsing: ordering, multi-values, separators, decoding, edge cases."""

from __future__ import annotations

import pytest

from querystring import EncodingError, parse, parse_pairs


def test_empty_query_returns_empty_dict() -> None:
    assert parse("") == {}


def test_empty_query_pairs_returns_empty_list() -> None:
    assert parse_pairs("") == []


def test_single_pair() -> None:
    assert parse("a=1") == {"a": ["1"]}


def test_multiple_keys_preserve_order_in_pairs() -> None:
    assert parse_pairs("a=1&b=2&c=3") == [("a", "1"), ("b", "2"), ("c", "3")]


def test_multi_value_keys_collected_into_list() -> None:
    assert parse("a=1&a=2&a=3") == {"a": ["1", "2", "3"]}


def test_leading_question_mark_stripped() -> None:
    assert parse("?a=1") == {"a": ["1"]}


def test_lone_key_decodes_to_empty_value() -> None:
    assert parse("a") == {"a": [""]}
    assert parse_pairs("a") == [("a", "")]


def test_trailing_separator_skipped() -> None:
    assert parse("a=1&") == {"a": ["1"]}


def test_consecutive_separators_skipped() -> None:
    assert parse("a=1&&b=2") == {"a": ["1"], "b": ["2"]}


def test_plus_decodes_to_space() -> None:
    assert parse("q=hello+world") == {"q": ["hello world"]}


def test_percent_decoding_basic() -> None:
    assert parse("q=hello%20world") == {"q": ["hello world"]}


def test_percent_decoding_utf8_multibyte() -> None:
    assert parse("name=caf%C3%A9") == {"name": ["café"]}


def test_emoji_round_trip_via_percent_encoding() -> None:
    assert parse("emoji=%F0%9F%98%80") == {"emoji": ["😀"]}


def test_blank_values_kept_by_default() -> None:
    assert parse("a=&b=value") == {"a": [""], "b": ["value"]}


def test_blank_values_dropped_when_disabled() -> None:
    assert parse("a=&b=value", blank_values=False) == {"b": ["value"]}


def test_custom_separator_semicolon() -> None:
    assert parse("a=1;b=2", sep=";") == {"a": ["1"], "b": ["2"]}


def test_strict_mode_rejects_dangling_percent() -> None:
    with pytest.raises(EncodingError):
        parse("a=%2")


def test_strict_mode_rejects_invalid_hex() -> None:
    with pytest.raises(EncodingError):
        parse("a=%ZZ")


def test_strict_mode_rejects_invalid_utf8() -> None:
    with pytest.raises(EncodingError):
        parse("a=%C3%28")


def test_lax_mode_keeps_dangling_percent_literal() -> None:
    assert parse("a=%2", strict=False) == {"a": ["%2"]}


def test_lax_mode_replaces_invalid_utf8() -> None:
    out = parse("a=%C3%28", strict=False)
    assert "a" in out
    assert len(out["a"]) == 1
    assert out["a"][0] != "%C3%28"


def test_max_pairs_enforced() -> None:
    from querystring import QueryStringError

    with pytest.raises(QueryStringError):
        parse("a=1&b=2&c=3", max_pairs=2)


def test_max_pairs_zero_means_no_pairs_allowed() -> None:
    from querystring import QueryStringError

    with pytest.raises(QueryStringError):
        parse("a=1", max_pairs=0)


def test_parse_rejects_non_string_query() -> None:
    with pytest.raises(TypeError):
        parse(123)  # type: ignore[arg-type]


def test_parse_rejects_empty_separator() -> None:
    with pytest.raises(ValueError):
        parse("a=1", sep="")


def test_parse_rejects_negative_max_pairs() -> None:
    with pytest.raises(ValueError):
        parse("a=1", max_pairs=-1)


def test_parse_rejects_non_int_max_pairs() -> None:
    with pytest.raises(ValueError):
        parse("a=1", max_pairs="three")  # type: ignore[arg-type]


def test_parse_rejects_bool_max_pairs() -> None:
    with pytest.raises(ValueError):
        parse("a=1", max_pairs=True)  # type: ignore[arg-type]


def test_keys_with_special_chars_decoded() -> None:
    assert parse("k%20with%20spaces=1") == {"k with spaces": ["1"]}


def test_value_with_equals_keeps_extra_equals_in_value() -> None:
    assert parse("a=1=2") == {"a": ["1=2"]}


def test_pairs_preserve_insertion_order_for_duplicates() -> None:
    assert parse_pairs("b=2&a=1&b=3") == [
        ("b", "2"),
        ("a", "1"),
        ("b", "3"),
    ]
