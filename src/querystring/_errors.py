"""Exception hierarchy for querystring."""

from __future__ import annotations


class QueryStringError(Exception):
    """Base exception for all querystring failures."""


class EncodingError(QueryStringError):
    """Raised when input contains invalid percent-encoding (strict mode)."""
