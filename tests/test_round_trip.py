"""Property-style round-trip checks across encoder choices."""

from __future__ import annotations

import pytest

from querystring import parse, serialize


@pytest.mark.parametrize(
    "data",
    [
        {"a": "1"},
        {"a": "1", "b": "2"},
        {"a": ["1", "2"]},
        {"q": "hello world"},
        {"name": "café"},
        {"emoji": "😀"},
        {"a": "x&y", "b": "x=y"},
        {"path": "/a/b/c"},
        {"chars": "+%#?@!*"},
        {"empty": ""},
    ],
)
@pytest.mark.parametrize("quote_via", ["plus", "percent"])
def test_round_trip_preserves_data(data: dict, quote_via: str) -> None:
    encoded = serialize(data, quote_via=quote_via)
    decoded = parse(encoded)
    expected = {key: value if isinstance(value, list) else [value] for key, value in data.items()}
    assert decoded == expected


def test_sorted_serialize_is_deterministic() -> None:
    data = {"b": "2", "a": "1", "c": "3"}
    assert serialize(data, sort=True) == serialize(data, sort=True)


def test_round_trip_mixed_types_via_pairs() -> None:
    data = [("n", 42), ("f", 3.5), ("b", True), ("s", "x")]
    out = serialize(data)
    parsed = parse(out)
    assert parsed == {"n": ["42"], "f": ["3.5"], "b": ["true"], "s": ["x"]}


def test_parse_pairs_round_trips_through_serialize() -> None:
    text = "a=1&b=2&a=3&c=hello+world"
    pairs = parse(text)
    flat = [(key, value) for key, values in pairs.items() for value in values]
    assert parse(serialize(flat)) == pairs
