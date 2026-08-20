"""Tests for the Limburg.net calendar entity."""
from __future__ import annotations

from datetime import date, datetime
from types import SimpleNamespace

import pytest
from homeassistant.util import dt as dt_util

from custom_components.limburg_net.calendar import LimburgNetCalendar


class _FakeCoordinator:
    """Minimal stand-in exposing only what LimburgNetCalendar reads."""

    def __init__(self, data):
        self.data = data


def _entry():
    return SimpleNamespace(entry_id="entry123", title="Test Street 1")


def _calendar(data):
    return LimburgNetCalendar(_FakeCoordinator(data), _entry())


def test_event_returns_earliest_upcoming(monkeypatch):
    monkeypatch.setattr(dt_util, "now", lambda: datetime(2026, 8, 20))
    calendar = _calendar(
        {
            "PMD": [date(2026, 8, 27), date(2026, 9, 10)],
            "Huisvuil": [date(2026, 8, 24)],
        }
    )

    event = calendar.event

    assert event is not None
    assert event.start == date(2026, 8, 24)
    assert event.end == date(2026, 8, 25)
    assert event.summary == "Huisvuil"
    assert event.all_day is True


def test_event_ignores_past_dates(monkeypatch):
    monkeypatch.setattr(dt_util, "now", lambda: datetime(2026, 8, 26))
    calendar = _calendar({"Huisvuil": [date(2026, 8, 24)]})

    assert calendar.event is None


@pytest.mark.asyncio
async def test_async_get_events_filters_by_range():
    calendar = _calendar(
        {
            "PMD": [date(2026, 8, 27), date(2026, 9, 10)],
            "Huisvuil": [date(2026, 8, 24)],
        }
    )

    events = await calendar.async_get_events(
        hass=None,
        start_date=datetime(2026, 8, 25),
        end_date=datetime(2026, 9, 1),
    )

    assert [(e.start, e.summary) for e in events] == [(date(2026, 8, 27), "PMD")]
