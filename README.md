# querystring

A small, predictable round-trip layer for **`application/x-www-form-
urlencoded`** query strings. One module, ~140 lines, 107 tests, 100%
line coverage, zero PyPI dependencies.

## Why

Python ships `urllib.parse` for percent-encoding, but the convenience
layer for "give me back a multi-value dict, then serialize me a stable,
sorted query string" is split across `parse_qs`, `parse_qsl`, and
`urlencode` — each with its own quirks (silent invalid-percent
acceptance, no merge/pick/omit, no callable encoder injection,
inconsistent multi-value behaviour).

`querystring` is the small, friendly layer:

- `parse` returns `{key: list[str]}` — multi-values are first-class.
- `parse_pairs` returns `[(key, value), ...]` — keeps insertion order.
- `serialize` accepts dicts, lists of pairs, or iterables; coerces
  bools/ints/floats; expands list values into repeated keys.
- `merge`, `pick`, `omit` operate directly on the wire format.
- Strict mode (default) rejects invalid percent-encoding;
  lax mode keeps malformed input literal.
- Encoder is injectable: `quote_via="plus"` (default), `"percent"`, or
  any callable.

## Install

Python 3.10+.

```bash
pip install querystring
```

## Quick start

```python
from querystring import parse, serialize, merge, pick, omit

parse("?a=1&b=hello+world&a=2")
# {'a': ['1', '2'], 'b': ['hello world']}

serialize({"q": "café au lait"}, quote_via="percent")
# 'q=caf%C3%A9%20au%20lait'

merge("?a=1&b=2", "?b=99&c=3")
# 'a=1&b=99&c=3'   (later inputs replace overlapping keys)

pick("?a=1&b=2&c=3", "a", "c")
# 'a=1&c=3'

omit("?a=1&b=2&c=3", "b")
# 'a=1&c=3'
```

## Parsing

```python
from querystring import parse, parse_pairs

parse("?a=1&a=2&b=3")
# {'a': ['1', '2'], 'b': ['3']}

parse_pairs("?a=1&a=2&b=3")
# [('a', '1'), ('a', '2'), ('b', '3')]
```

Options:

| Argument | Default | Behaviour |
|---|---|---|
| `sep` | `"&"` | Pair separator; pass `";"` for legacy `<form>` payloads. |
| `strict` | `True` | Raise `EncodingError` for `%XX` with bad hex or invalid UTF-8 sequences. |
| `blank_values` | `True` | Keep `key=` pairs (empty value). Set False to drop them. |
| `max_pairs` | `None` | Optional ceiling — useful for hardening against query-string DoS. |

A leading `?` is stripped automatically. Consecutive separators are
collapsed (no empty pair). A bare `key` (no `=`) decodes to `(key, "")`.

### Strict vs lax decoding

```python
parse("a=%2")               # raises EncodingError (dangling %)
parse("a=%2", strict=False) # {'a': ['%2']}

parse("a=%C3%28")               # raises EncodingError (invalid UTF-8)
parse("a=%C3%28", strict=False) # decoded with U+FFFD replacement
```

## Serializing

```python
from querystring import serialize

serialize({"q": "hello world"})
# 'q=hello+world'

serialize({"q": "hello world"}, quote_via="percent")
# 'q=hello%20world'

serialize({"a": [1, 2, 3]})
# 'a=1&a=2&a=3'

serialize({"on": True, "n": 42, "x": None})
# 'on=true&n=42&x='

serialize({"b": 2, "a": 1, "c": 3}, sort=True)
# 'a=1&b=2&c=3'

serialize({"q": "x"}, quote_via=lambda s: s.upper())
# 'Q=X'
```

Inputs accepted: any `Mapping`, or any iterable of `(key, value)` pairs.
List/tuple values expand into repeated keys. Scalar value types
supported: `str`, `int`, `float`, `bool`, `None`.

`bool` serializes as `"true"` / `"false"` (lowercase). Pass a callable
`quote_via` if you need different escaping (for example, an
identity function for already-encoded segments).

## merge / pick / omit

```python
from querystring import merge, pick, omit

merge("a=1&a=2&b=3", "a=99")
# 'a=99&b=3'   — later inputs replace the entire value list of overlapping keys.

merge("a=1", {"b": 2}, [("c", "3")])
# 'a=1&b=2&c=3' — accepts strings, mappings, or iterables.

pick("?a=1&b=2&c=3", "a", "c")        # 'a=1&c=3'
omit("?a=1&b=2&c=3", "b")             # 'a=1&c=3'
```

`merge` is order-preserving: keys appear in the order they first show
up across the inputs.

## Public API

| Symbol | Description |
|---|---|
| `parse(query, *, sep, strict, blank_values, max_pairs) -> dict[str, list[str]]` | Multi-value dict. |
| `parse_pairs(query, *, sep, strict, blank_values, max_pairs) -> list[tuple[str, str]]` | Insertion-order pairs. |
| `serialize(data, *, sep, quote_via, sort, blank_values) -> str` | Encode mapping/iterable. |
| `merge(*queries, sep, quote_via) -> str` | Merge with later-wins semantics. |
| `pick(query, *keys, sep, quote_via) -> str` | Keep only listed keys. |
| `omit(query, *keys, sep, quote_via) -> str` | Drop listed keys. |
| `QueryStringError` | Base exception. |
| `EncodingError(QueryStringError)` | Invalid `%XX` sequence in strict mode. |

## Running tests

```bash
git clone https://github.com/nripankadas07/querystring
cd querystring
pip install -e .[dev]
pytest -q
```

The tests are split across `tests/test_parse.py`,
`tests/test_serialize.py`, `tests/test_combinators.py`, and
`tests/test_round_trip.py` (parametrized property checks).

## License

MIT.
