"""Tests for the Limburg.net per-waste-type and today/tomorrow sensors."""
from __future__ import annotations

from datetime import date, datetime
from types import SimpleNamespace

import pytest
from homeassistant.util import dt as dt_util

from custom_components.limburg_net.const import get_waste_type_icon
from custom_components.limburg_net.sensor import (
    LimburgNetDaySensor,
    LimburgNetSensor,
    async_setup_entry,
)


class _FakeCoordinator:
    """Minimal stand-in exposing only what the sensors read."""

    def __init__(self, data):
        self.data = data
        self._listeners = []

    def async_add_listener(self, callback):
        self._listeners.append(callback)
        return lambda: self._listeners.remove(callback)

    def notify(self):
        for callback in list(self._listeners):
            callback()


def _entry(coordinator=None):
    entry = SimpleNamespace(entry_id="entry123", title="Test Street 1")
    if coordinator is not None:
        entry.runtime_data = coordinator
        entry.async_on_unload = lambda unsub: None
    return entry


def _day_sensor(data, day_offset, translation_key="today", unique_suffix="today", language="en"):
    sensor = LimburgNetDaySensor(
        _FakeCoordinator(data), _entry(), day_offset, translation_key, unique_suffix
    )
    sensor.hass = SimpleNamespace(config=SimpleNamespace(language=language))
    return sensor


# --- LimburgNetSensor -------------------------------------------------------


def test_sensor_native_value_returns_earliest_date():
    coordinator = _FakeCoordinator({"PMD": [date(2026, 8, 20), date(2026, 8, 27)]})
    sensor = LimburgNetSensor(coordinator, _entry(), "PMD")

    assert sensor.native_value == date(2026, 8, 20)


def test_sensor_native_value_none_when_no_dates():
    sensor = LimburgNetSensor(_FakeCoordinator({}), _entry(), "PMD")

    assert sensor.native_value is None


def test_sensor_extra_state_attributes_lists_iso_dates():
    coordinator = _FakeCoordinator({"PMD": [date(2026, 8, 20), date(2026, 8, 27)]})
    sensor = LimburgNetSensor(coordinator, _entry(), "PMD")

    assert sensor.extra_state_attributes == {
        "upcoming_dates": ["2026-08-20", "2026-08-27"]
    }


def test_sensor_uses_translation_key_for_known_waste_type():
    sensor = LimburgNetSensor(_FakeCoordinator({}), _entry(), "Restafval")

    assert sensor._attr_translation_key == "residual_waste"
    assert getattr(sensor, "_attr_name", None) is None


def test_sensor_falls_back_to_raw_name_for_unknown_waste_type():
    sensor = LimburgNetSensor(_FakeCoordinator({}), _entry(), "Iets Onbekends")

    assert getattr(sensor, "_attr_translation_key", None) is None
    assert sensor._attr_name == "Iets Onbekends"


# --- LimburgNetDaySensor -----------------------------------------------------


def test_day_sensor_lists_types_for_target_date(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(dt_util, "now", lambda: datetime(2026, 8, 20))
    sensor = _day_sensor(
        {"PMD": [date(2026, 8, 20)], "Huisvuil": [date(2026, 8, 20)]}, day_offset=0
    )

    assert sensor.native_value == "Residual waste, PMD (plastic, metal & drink cartons)"


def test_day_sensor_lists_types_in_dutch_when_hass_language_is_dutch(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(dt_util, "now", lambda: datetime(2026, 8, 20))
    sensor = _day_sensor(
        {"PMD": [date(2026, 8, 20)], "Huisvuil": [date(2026, 8, 20)]},
        day_offset=0,
        language="nl-BE",
    )

    assert sensor.native_value == "Huisvuil, PMD"


def test_day_sensor_uses_day_offset_for_tomorrow(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(dt_util, "now", lambda: datetime(2026, 8, 20))
    sensor = _day_sensor({"PMD": [date(2026, 8, 21)]}, day_offset=1)

    assert sensor.native_value == "PMD (plastic, metal & drink cartons)"


def test_day_sensor_shows_english_placeholder_when_no_collection(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(dt_util, "now", lambda: datetime(2026, 8, 20))
    sensor = _day_sensor({"PMD": [date(2026, 8, 27)]}, day_offset=0)
    sensor.hass = SimpleNamespace(config=SimpleNamespace(language="en"))

    assert sensor.native_value == "No waste collection"


def test_day_sensor_shows_dutch_placeholder_when_no_collection(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(dt_util, "now", lambda: datetime(2026, 8, 20))
    sensor = _day_sensor({"PMD": [date(2026, 8, 27)]}, day_offset=0)
    sensor.hass = SimpleNamespace(config=SimpleNamespace(language="nl-BE"))

    assert sensor.native_value == "Geen afvalophaling"


def test_day_sensor_icon_no_collection():
    sensor = _day_sensor({}, day_offset=0)

    assert sensor.icon == "mdi:calendar-remove-outline"


def test_day_sensor_icon_single_type(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(dt_util, "now", lambda: datetime(2026, 8, 20))
    sensor = _day_sensor({"PMD": [date(2026, 8, 20)]}, day_offset=0)

    assert sensor.icon == get_waste_type_icon("PMD")


def test_day_sensor_icon_multiple_types(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(dt_util, "now", lambda: datetime(2026, 8, 20))
    sensor = _day_sensor(
        {"PMD": [date(2026, 8, 20)], "Huisvuil": [date(2026, 8, 20)]}, day_offset=0
    )

    assert sensor.icon == "mdi:trash-can"


def test_day_sensor_extra_state_attributes(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(dt_util, "now", lambda: datetime(2026, 8, 20))
    sensor = _day_sensor(
        {"PMD": [date(2026, 8, 20)], "Huisvuil": [date(2026, 8, 20)]}, day_offset=0
    )

    assert sensor.extra_state_attributes == {
        "waste_types": ["Residual waste", "PMD (plastic, metal & drink cartons)"]
    }


# --- async_setup_entry --------------------------------------------------------


async def test_async_setup_entry_adds_today_tomorrow_and_known_waste_types():
    coordinator = _FakeCoordinator({"PMD": [date(2026, 8, 20)]})
    entry = _entry(coordinator)
    added: list = []

    await async_setup_entry(hass=None, entry=entry, async_add_entities=added.extend)

    assert len(added) == 3
    assert sum(isinstance(e, LimburgNetDaySensor) for e in added) == 2
    assert sum(isinstance(e, LimburgNetSensor) for e in added) == 1


async def test_async_setup_entry_adds_new_waste_type_on_coordinator_update():
    coordinator = _FakeCoordinator({"PMD": [date(2026, 8, 20)]})
    entry = _entry(coordinator)
    added: list = []

    await async_setup_entry(hass=None, entry=entry, async_add_entities=added.extend)
    assert len(added) == 3

    coordinator.data["Huisvuil"] = [date(2026, 8, 21)]
    coordinator.notify()

    assert len(added) == 4
    assert any(
        isinstance(e, LimburgNetSensor) and e._waste_type == "Huisvuil" for e in added
    )

    # A further notification with no new waste types must not add duplicates.
    coordinator.notify()
    assert len(added) == 4
