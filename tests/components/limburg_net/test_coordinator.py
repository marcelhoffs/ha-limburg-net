"""Tests for the Limburg.net data update coordinator."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from aiolimburgnet import CollectionEvent, LimburgNetConnectionError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util import dt as dt_util

from custom_components.limburg_net.const import (
    CONF_CITY_ID,
    CONF_CITY_NAME,
    CONF_HOUSE_NUMBER,
    CONF_STREET_ID,
    CONF_STREET_NAME,
    CONF_SUFFIX,
    DOMAIN,
)
from custom_components.limburg_net.coordinator import LimburgNetCoordinator

ENTRY_DATA = {
    CONF_CITY_NAME: "Genk",
    CONF_CITY_ID: "71034",
    CONF_STREET_NAME: "Stationsstraat",
    CONF_STREET_ID: "12345",
    CONF_HOUSE_NUMBER: "12",
    CONF_SUFFIX: "",
}


def _coordinator(hass: HomeAssistant, client: AsyncMock) -> LimburgNetCoordinator:
    entry = MockConfigEntry(domain=DOMAIN, data=ENTRY_DATA)
    entry.add_to_hass(hass)
    return LimburgNetCoordinator(hass, entry, client, timedelta(hours=12))


async def test_async_update_data_filters_sorts_and_dedupes(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Past events are dropped, duplicates collapse, and dates end up sorted."""
    monkeypatch.setattr(dt_util, "now", lambda: datetime(2026, 8, 20))
    client = AsyncMock()
    client.get_upcoming_events = AsyncMock(
        return_value=[
            CollectionEvent(waste_type="PMD", date=date(2026, 8, 19)),  # past, dropped
            CollectionEvent(waste_type="PMD", date=date(2026, 8, 27)),
            CollectionEvent(waste_type="PMD", date=date(2026, 8, 20)),  # today, out of order
            CollectionEvent(waste_type="PMD", date=date(2026, 8, 20)),  # duplicate
            CollectionEvent(waste_type="Huisvuil", date=date(2026, 8, 24)),
        ]
    )
    coordinator = _coordinator(hass, client)

    data = await coordinator._async_update_data()

    assert data == {
        "PMD": [date(2026, 8, 20), date(2026, 8, 27)],
        "Huisvuil": [date(2026, 8, 24)],
    }


async def test_async_update_data_wraps_client_errors(hass: HomeAssistant) -> None:
    """A client-side error is surfaced as UpdateFailed so the coordinator retries."""
    client = AsyncMock()
    client.get_upcoming_events = AsyncMock(
        side_effect=LimburgNetConnectionError("boom")
    )
    coordinator = _coordinator(hass, client)

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
