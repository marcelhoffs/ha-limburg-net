"""Tests for the const.py helper functions."""
from __future__ import annotations

import pytest

import json
from pathlib import Path

from custom_components.limburg_net.const import WASTE_TYPE_NAMES, get_no_collection_text

TRANSLATIONS = Path(__file__).parents[3] / "custom_components" / "limburg_net" / "translations"


@pytest.mark.parametrize(
    ("language", "expected"),
    [
        ("nl", "Geen afvalophaling"),
        ("nl-BE", "Geen afvalophaling"),
        ("NL", "Geen afvalophaling"),
        ("en", "No waste collection"),
        ("fr", "No waste collection"),
    ],
)
def test_get_no_collection_text(language: str, expected: str) -> None:
    assert get_no_collection_text(language) == expected


@pytest.mark.parametrize("language", ["en", "nl"])
def test_waste_type_names_match_entity_translations(language: str) -> None:
    """WASTE_TYPE_NAMES (calendar/day sensors) must not drift from the entity names."""
    sensors = json.loads((TRANSLATIONS / f"{language}.json").read_text())["entity"]["sensor"]

    for key, names in WASTE_TYPE_NAMES.items():
        assert names[language] == sensors[key]["name"], key
