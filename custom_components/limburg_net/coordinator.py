"""Data update coordinator for the Limburg.net integration."""
from __future__ import annotations

import logging
from datetime import date

from aiolimburgnet import City, LimburgNetClient, LimburgNetError, Street

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CONF_CITY_ID,
    CONF_CITY_NAME,
    CONF_HOUSE_NUMBER,
    CONF_STREET_ID,
    CONF_STREET_NAME,
    CONF_SUFFIX,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

# waste type title -> sorted list of upcoming collection dates
LimburgNetData = dict[str, list[date]]


class LimburgNetCoordinator(DataUpdateCoordinator[LimburgNetData]):
    """Fetches and caches upcoming waste collection dates."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: LimburgNetClient,
        update_interval,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self._client = client
        self._city = City(nis_code=entry.data[CONF_CITY_ID], name=entry.data[CONF_CITY_NAME])
        self._street = Street(id=entry.data[CONF_STREET_ID], name=entry.data[CONF_STREET_NAME])
        self._house_number = entry.data[CONF_HOUSE_NUMBER]
        self._suffix = entry.data.get(CONF_SUFFIX, "")

    async def _async_update_data(self) -> LimburgNetData:
        try:
            events = await self._client.get_upcoming_events(
                self._city, self._street, self._house_number, self._suffix
            )
        except LimburgNetError as err:
            raise UpdateFailed(f"Error communicating with Limburg.net: {err}") from err

        today = dt_util.now().date()
        result: LimburgNetData = {}

        for event in events:
            if event.date < today:
                continue
            dates = result.setdefault(event.waste_type, [])
            if event.date not in dates:
                dates.append(event.date)

        for dates in result.values():
            dates.sort()

        return result
