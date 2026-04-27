"""Parser, serializer, merge / pick / omit helpers for querystring.

The implementation thinly wraps :mod:`urllib.parse` so percent-decoding
is correct for arbitrary UTF-8 sequences, but adds:

* multi-value first-class support (``a=1&a=2`` → ``{'a': ['1', '2']}``);
* configurable separator (``&`` or ``;``);
* configurable encoder (``plus``, ``percent``, or callable);
* deterministic, sorted serialization on demand;
* ``merge`` / ``pick`` / ``omit`` operating on the wire format directly.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Iterable, Mapping
from urllib.parse import quote, quote_plus, unquote

from ._errors import EncodingError, QueryStringError

__all__ = [
    "merge",
    "omit",
    "parse",
    "parse_pairs",
    "pick",
    "serialize",
]


_BAD_PERCENT = re.compile(r"%(?![0-9A-Fa-f]{2})")
_QuoteFn = Callable[[str], str]
_Pair = tuple[str, str]


def parse_pairs(
    query: str,
    *,
    sep: str = "&",
    strict: bool = True,
    blank_values: bool = True,
    max_pairs: int | None = None,
) -> list[_Pair]:
    """Parse a query string into an ordered list of ``(key, value)`` pairs.

    A leading ``?`` is stripped if present. Empty pairs (consecutive
    separators) are skipped. Keys without ``=`` decode to ``(key, "")``.
    Pass ``strict=False`` to leave malformed percent-encoding literal
    instead of raising :class:`EncodingError`.
    """
    _check_parse_args(query, sep, max_pairs)
    if not query:
        return []
    text = query[1:] if query.startswith("?") else query
    raw_pairs = text.split(sep)
    if max_pairs is not None and len(raw_pairs) > max_pairs:
        raise QueryStringError(
            f"too many pairs: {len(raw_pairs)} > {max_pairs}"
        )
    pairs: list[_Pair] = []
    for chunk in raw_pairs:
        if chunk == "":
            continue
        key_raw, _eq, value_raw = chunk.partition("=")
        key = _decode(key_raw, strict=strict)
        value = _decode(value_raw, strict=strict)
        if not blank_values and value == "":
            continue
        pairs.append((key, value))
    return pairs


def parse(
    query: str,
    *,
    sep: str = "&",
    strict: bool = True,
    blank_values: bool = True,
    max_pairs: int | None = None,
) -> dict[str, list[str]]:
    """Parse a query string into ``{key: [value, ...]}``.

    Multi-valued keys (``?a=1&a=2``) are returned with values in the
    order they appeared. Other arguments are forwarded to
    :func:`parse_pairs`.
    """
    pairs = parse_pairs(
        query,
        sep=sep,
        strict=strict,
        blank_values=blank_values,
        max_pairs=max_pairs,
    )
    out: dict[str, list[str]] = {}
    for key, value in pairs:
        out.setdefault(key, []).append(value)
    return out


def serialize(
    data: Mapping[str, Any] | Iterable[tuple[str, Any]],
    *,
    sep: str = "&",
    quote_via: str | _QuoteFn = "plus",
    sort: bool = False,
    blank_values: bool = True,
) -> str:
    """Encode ``data`` as ``application/x-www-form-urlencoded`` text.

    ``data`` may be a mapping (dict-like) or an iterable of pairs. List
    or tuple values produce repeated keys. Values are coerced to
    strings: ``True``/``False`` become ``"true"``/``"false"``, ``None``
    becomes ``""`` (or is dropped if ``blank_values=False``), and
    int/float use ``str()``.

    ``quote_via`` selects the encoder: ``"plus"`` (form encoding,
    spaces as ``+``), ``"percent"`` (RFC 3986 percent-encoding), or any
    callable accepting a string.
    """
    pairs = _normalize_data(data)
    if sort:
        pairs = sorted(pairs, key=lambda pair: pair[0])
    quote_fn = _resolve_quote(quote_via)
    parts: list[str] = []
    for key, value in pairs:
        if value == "" and not blank_values:
            continue
        parts.append(f"{quote_fn(key)}={quote_fn(value)}")
    return sep.join(parts)


def merge(
    *queries: str | Mapping[str, Any] | Iterable[tuple[str, Any]],
    sep: str = "&",
    quote_via: str | _QuoteFn = "plus",
) -> str:
    """Merge multiple queries; later queries replace earlier keys.

    Each input may be a query string, a mapping, or an iterable of
    pairs. When a key reappears in a later input, its entire value
    *list* is replaced by the later input's values (so multi-value
    keys remain intact). Insertion order is preserved.
    """
    accumulated: dict[str, list[str]] = {}
    order: list[str] = []
    for source in queries:
        new_pairs = _coerce_pairs(source, sep=sep)
        grouped: dict[str, list[str]] = {}
        for key, value in new_pairs:
            grouped.setdefault(key, []).append(value)
        for key, values in grouped.items():
            if key not in accumulated:
                order.append(key)
            accumulated[key] = values
    flat = [(key, value) for key in order for value in accumulated[key]]
    return serialize(flat, sep=sep, quote_via=quote_via)


def pick(
    query: str,
    *keys: str,
    sep: str = "&",
    quote_via: str | _QuoteFn = "plus",
) -> str:
    """Return a query containing only pairs whose key appears in ``keys``."""
    targets = set(keys)
    pairs = parse_pairs(query, sep=sep, strict=False)
    return serialize(
        [pair for pair in pairs if pair[0] in targets],
        sep=sep,
        quote_via=quote_via,
    )


def omit(
    query: str,
    *keys: str,
    sep: str = "&",
    quote_via: str | _QuoteFn = "plus",
) -> str:
    """Return a query with pairs whose key appears in ``keys`` removed."""
    targets = set(keys)
    pairs = parse_pairs(query, sep=sep, strict=False)
    return serialize(
        [pair for pair in pairs if pair[0] not in targets],
        sep=sep,
        quote_via=quote_via,
    )


# -- internals ---------------------------------------------------------


def _check_parse_args(
    query: object, sep: object, max_pairs: object
) -> None:
    if not isinstance(query, str):
        raise TypeError(
            f"query must be str, got {type(query).__name__}"
        )
    if not isinstance(sep, str) or sep == "":
        raise ValueError("sep must be a non-empty str")
    if max_pairs is not None and (
        not isinstance(max_pairs, int)
        or isinstance(max_pairs, bool)
        or max_pairs < 0
    ):
        raise ValueError("max_pairs must be a non-negative int or None")


def _decode(text: str, *, strict: bool) -> str:
    if strict and _BAD_PERCENT.search(text):
        raise EncodingError(
            f"invalid percent-encoding in {text!r}"
        )
    text = text.replace("+", " ")
    if strict:
        try:
            return unquote(text, errors="strict")
        except UnicodeDecodeError as exc:
            raise EncodingError(
                f"invalid UTF-8 in percent-encoded sequence: {exc}"
            ) from exc
    return unquote(text, errors="replace")


def _normalize_data(
    data: Mapping[str, Any] | Iterable[tuple[str, Any]],
) -> list[_Pair]:
    if isinstance(data, str):
        raise TypeError(
            "serialize() does not accept a query string — call parse() first"
        )
    if isinstance(data, Mapping):
        items: Iterable[Any] = data.items()
    else:
        items = data
    pairs: list[_Pair] = []
    for entry in items:
        key, value = _split_entry(entry)
        encoded_key = _stringify_scalar(key, role="key")
        if isinstance(value, (list, tuple)):
            for sub in value:
                pairs.append((encoded_key, _stringify_scalar(sub, role="value")))
        else:
            pairs.append((encoded_key, _stringify_scalar(value, role="value")))
    return pairs


def _split_entry(entry: Any) -> tuple[Any, Any]:
    if not isinstance(entry, (tuple, list)) or len(entry) != 2:
        raise TypeError(
            f"each entry must be a (key, value) pair; got {entry!r}"
        )
    return entry[0], entry[1]


def _stringify_scalar(value: Any, *, role: str) -> str:
    if value is None:
        if role == "key":
            raise TypeError("key must not be None")
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float, str)):
        return str(value)
    raise TypeError(
        f"{role} must be str/int/float/bool/None, got {type(value).__name__}"
    )


def _resolve_quote(quote_via: str | _QuoteFn) -> _QuoteFn:
    if callable(quote_via):
        return quote_via
    if quote_via == "plus":
        return _quote_plus_safe
    if quote_via == "percent":
        return _quote_percent_safe
    raise ValueError(
        f"quote_via must be 'plus', 'percent', or callable; got {quote_via!r}"
    )


def _quote_plus_safe(text: str) -> str:
    return quote_plus(text, safe="")


def _quote_percent_safe(text: str) -> str:
    return quote(text, safe="")


def _coerce_pairs(
    source: str | Mapping[str, Any] | Iterable[tuple[str, Any]],
    *,
    sep: str,
) -> list[_Pair]:
    if isinstance(source, str):
        return parse_pairs(source, sep=sep, strict=False)
    return _normalize_data(source)
