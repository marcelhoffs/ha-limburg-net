"""Exceptions raised by aiolimburgnet."""
from __future__ import annotations


class LimburgNetError(Exception):
    """Base exception for all errors raised by this library."""


class LimburgNetConnectionError(LimburgNetError):
    """Raised when the Limburg.net API cannot be reached or returns a bad response."""


class CityNotFoundError(LimburgNetError):
    """Raised when no single city matches the given search query.

    `candidates` lists the names the API returned when the query was
    ambiguous (several prefix matches, none exact); empty when nothing matched.
    """

    def __init__(self, query: str, candidates: list[str] | None = None) -> None:
        super().__init__(f"No city found matching {query!r}")
        self.query = query
        self.candidates = candidates or []


class StreetNotFoundError(LimburgNetError):
    """Raised when no single street matches the given search query.

    `candidates` works as for CityNotFoundError.
    """

    def __init__(self, query: str, candidates: list[str] | None = None) -> None:
        super().__init__(f"No street found matching {query!r}")
        self.query = query
        self.candidates = candidates or []
