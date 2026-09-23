"""Tests for setting up, reloading and unloading the Limburg.net integration."""
from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

from aiolimburgnet import CollectionEvent, LimburgNetConnectionError
from freezegun.api import FrozenDateTimeFactory
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.limburg_net.const import (
    CONF_CITY_ID,
    CONF_CITY_NAME,
    CONF_HOUSE_NUMBER,
    CONF_SCAN_INTERVAL_HOURS,
    CONF_STREET_ID,
    CONF_STREET_NAME,
    CONF_SUFFIX,
    DOMAIN,
)

ENTRY_DATA = {
    CONF_CITY_NAME: "Genk",
    CONF_CITY_ID: "71016",
    CONF_STREET_NAME: "Kerkstraat",
    CONF_STREET_ID: "26537",
    CONF_HOUSE_NUMBER: "1",
    CONF_SUFFIX: "",
}


def _client(events: list[CollectionEvent]) -> AsyncMock:
    client = AsyncMock()
    client.get_upcoming_events = AsyncMock(return_value=events)
    return client


async def _setup(
    hass: HomeAssistant, client: AsyncMock, options: dict | None = None
) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN, data=ENTRY_DATA, options=options or {}, title="Kerkstraat 1, Genk"
    )
    entry.add_to_hass(hass)
    with patch("custom_components.limburg_net.LimburgNetClient", return_value=client):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


def _state(hass: HomeAssistant, platform: str, entry: MockConfigEntry, suffix: str):
    entity_id = er.async_get(hass).async_get_entity_id(
        platform, DOMAIN, f"{entry.entry_id}_{suffix}"
    )
    assert entity_id is not None, suffix
    return hass.states.get(entity_id)


async def test_setup_creates_entities_and_unloads(hass: HomeAssistant) -> None:
    client = _client([CollectionEvent(waste_type="Pmd", date=date.today() + timedelta(days=3))])
    entry = await _setup(hass, client)

    assert entry.state is ConfigEntryState.LOADED
    assert _state(hass, "sensor", entry, "today") is not None
    assert _state(hass, "sensor", entry, "tomorrow") is not None
    assert _state(hass, "sensor", entry, "pmd") is not None
    assert _state(hass, "calendar", entry, "calendar") is not None

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_setup_retries_when_api_is_down(hass: HomeAssistant) -> None:
    client = AsyncMock()
    client.get_upcoming_events = AsyncMock(side_effect=LimburgNetConnectionError("down"))
    entry = await _setup(hass, client)

    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_options_change_reloads_with_new_interval(hass: HomeAssistant) -> None:
    client = _client([])
    entry = await _setup(hass, client)

    with patch("custom_components.limburg_net.LimburgNetClient", return_value=client):
        hass.config_entries.async_update_entry(entry, options={CONF_SCAN_INTERVAL_HOURS: 6})
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert entry.runtime_data.update_interval == timedelta(hours=6)


async def test_entities_roll_over_at_midnight_without_refetch(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    await hass.config.async_set_time_zone("Europe/Brussels")
    freezer.move_to("2026-08-20 23:59:00+02:00")
    client = _client([CollectionEvent(waste_type="Pmd", date=date(2026, 8, 21))])
    # 48h polling, so nothing below can come from a coordinator refresh.
    entry = await _setup(hass, client, options={CONF_SCAN_INTERVAL_HOURS: 48})

    assert _state(hass, "sensor", entry, "today").state == "No waste collection"
    assert _state(hass, "sensor", entry, "tomorrow").state == "PMD"
    assert _state(hass, "sensor", entry, "pmd").state == "2026-08-21"

    # Collection day: "today" picks it up right at midnight.
    freezer.move_to("2026-08-21 00:00:01+02:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert _state(hass, "sensor", entry, "today").state == "PMD"
    assert _state(hass, "sensor", entry, "tomorrow").state == "No waste collection"

    # Day after: the per-type sensor no longer shows the passed date.
    freezer.move_to("2026-08-22 00:00:01+02:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert _state(hass, "sensor", entry, "today").state == "No waste collection"
    pmd = _state(hass, "sensor", entry, "pmd")
    assert pmd.state == "unknown"
    assert pmd.attributes["upcoming_dates"] == []

    # All of the above came from the one fetch done at setup.
    assert client.get_upcoming_events.await_count == 1
