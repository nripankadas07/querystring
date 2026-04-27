"""querystring — stable, encoder-configurable form-encoding round-trip.

Public API::

    from querystring import parse, parse_pairs, serialize
    from querystring import merge, pick, omit
    from querystring import QueryStringError, EncodingError

See the README for usage.
"""

from __future__ import annotations

from ._core import merge, omit, parse, parse_pairs, pick, serialize
from ._errors import EncodingError, QueryStringError

__all__ = [
    "EncodingError",
    "QueryStringError",
    "merge",
    "omit",
    "parse",
    "parse_pairs",
    "pick",
    "serialize",
]

__version__ = "0.1.0"
