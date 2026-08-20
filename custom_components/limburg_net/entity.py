"""Shared entity helpers for the Limburg.net Afvalkalender integration."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN
from .coordinator import LimburgNetConfigEntry


def device_info(entry: LimburgNetConfigEntry) -> DeviceInfo:
    """Return the shared device info for this config entry's address."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        manufacturer="Limburg.net",
        entry_type=DeviceEntryType.SERVICE,
    )
