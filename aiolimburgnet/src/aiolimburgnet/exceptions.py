"""Exceptions raised by aiolimburgnet."""
from __future__ import annotations


class LimburgNetError(Exception):
    """Base exception for all errors raised by this library."""


class LimburgNetConnectionError(LimburgNetError):
    """Raised when the Limburg.net API cannot be reached or returns a bad response."""


class CityNotFoundError(LimburgNetError):
    """Raised when no city matches the given search query."""

    def __init__(self, query: str) -> None:
        super().__init__(f"No city found matching {query!r}")
        self.query = query


class StreetNotFoundError(LimburgNetError):
    """Raised when no street matches the given search query."""

    def __init__(self, query: str) -> None:
        super().__init__(f"No street found matching {query!r}")
        self.query = query
