"""Sensor platform for the Limburg.net Afvalkalender integration."""
from __future__ import annotations

from datetime import date, timedelta

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util
from homeassistant.util import slugify

from .const import (
    get_no_collection_text,
    get_waste_type_icon,
    get_waste_type_name,
    get_waste_type_translation_key,
)
from .coordinator import LimburgNetConfigEntry, LimburgNetCoordinator
from .entity import device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LimburgNetConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Limburg.net sensors, adding new ones as new waste types appear."""
    coordinator = entry.runtime_data
    known_waste_types: set[str] = set()

    async_add_entities(
        [
            LimburgNetDaySensor(
                coordinator, entry, day_offset=0, translation_key="today", unique_suffix="today"
            ),
            LimburgNetDaySensor(
                coordinator, entry, day_offset=1, translation_key="tomorrow", unique_suffix="tomorrow"
            ),
        ]
    )

    @callback
    def _add_new_entities() -> None:
        new_types = set(coordinator.data) - known_waste_types
        if not new_types:
            return
        known_waste_types.update(new_types)
        async_add_entities(
            LimburgNetSensor(coordinator, entry, waste_type) for waste_type in new_types
        )

    _add_new_entities()
    entry.async_on_unload(coordinator.async_add_listener(_add_new_entities))


class LimburgNetSensor(CoordinatorEntity[LimburgNetCoordinator], SensorEntity):
    """Represents the next pickup date for a single waste type."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.DATE

    def __init__(
        self,
        coordinator: LimburgNetCoordinator,
        entry: LimburgNetConfigEntry,
        waste_type: str,
    ) -> None:
        super().__init__(coordinator)
        self._waste_type = waste_type
        translation_key = get_waste_type_translation_key(waste_type)
        if translation_key:
            self._attr_translation_key = translation_key
        else:
            self._attr_name = waste_type
        self._attr_unique_id = f"{entry.entry_id}_{slugify(waste_type)}"
        self._attr_icon = get_waste_type_icon(waste_type)
        self._attr_device_info = device_info(entry)

    @property
    def native_value(self) -> date | None:
        dates = self.coordinator.data.get(self._waste_type)
        return dates[0] if dates else None

    @property
    def extra_state_attributes(self) -> dict[str, list[str]]:
        dates = self.coordinator.data.get(self._waste_type, [])
        return {"upcoming_dates": [d.isoformat() for d in dates]}


class LimburgNetDaySensor(CoordinatorEntity[LimburgNetCoordinator], SensorEntity):
    """Lists which waste type(s), if any, are collected on a given day."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: LimburgNetCoordinator,
        entry: LimburgNetConfigEntry,
        day_offset: int,
        translation_key: str,
        unique_suffix: str,
    ) -> None:
        super().__init__(coordinator)
        self._day_offset = day_offset
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{entry.entry_id}_{unique_suffix}"
        self._attr_device_info = device_info(entry)

    @property
    def _target_date(self) -> date:
        return dt_util.now().date() + timedelta(days=self._day_offset)

    @property
    def _collected_types(self) -> list[str]:
        target = self._target_date
        return sorted(
            waste_type
            for waste_type, dates in self.coordinator.data.items()
            if target in dates
        )

    @property
    def native_value(self) -> str:
        types = self._collected_types
        if not types:
            return get_no_collection_text(self.hass.config.language)
        language = self.hass.config.language
        return ", ".join(get_waste_type_name(t, language) for t in types)

    @property
    def icon(self) -> str:
        types = self._collected_types
        if not types:
            return "mdi:calendar-remove-outline"
        if len(types) == 1:
            return get_waste_type_icon(types[0])
        return "mdi:trash-can"

    @property
    def extra_state_attributes(self) -> dict[str, list[str]]:
        language = self.hass.config.language
        return {
            "waste_types": [get_waste_type_name(t, language) for t in self._collected_types]
        }
