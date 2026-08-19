"""Data models returned by the Limburg.net API client."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class City:
    """A city (gemeente) as known by Limburg.net."""

    nis_code: str
    name: str


@dataclass(frozen=True, slots=True)
class Street:
    """A street within a city, as known by Limburg.net."""

    id: str
    name: str


@dataclass(frozen=True, slots=True)
class CollectionEvent:
    """A single waste collection event for one address."""

    waste_type: str
    date: date
