"""Tests for the const.py helper functions."""
from __future__ import annotations

import pytest

from custom_components.limburg_net.const import get_no_collection_text


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
