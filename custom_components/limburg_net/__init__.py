"""The Limburg.net Afvalkalender integration."""
from __future__ import annotations

from datetime import timedelta

from aiolimburgnet import LimburgNetClient

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_SCAN_INTERVAL_HOURS, DEFAULT_SCAN_INTERVAL_HOURS
from .coordinator import LimburgNetConfigEntry, LimburgNetCoordinator

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: LimburgNetConfigEntry) -> bool:
    """Set up Limburg.net from a config entry."""
    session = async_get_clientsession(hass)
    client = LimburgNetClient(session)

    scan_interval_hours = entry.options.get(
        CONF_SCAN_INTERVAL_HOURS, DEFAULT_SCAN_INTERVAL_HOURS
    )
    coordinator = LimburgNetCoordinator(
        hass, entry, client, timedelta(hours=scan_interval_hours)
    )
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: LimburgNetConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(hass: HomeAssistant, entry: LimburgNetConfigEntry) -> None:
    """Reload the entry when its options (e.g. polling interval) change."""
    await hass.config_entries.async_reload(entry.entry_id)
