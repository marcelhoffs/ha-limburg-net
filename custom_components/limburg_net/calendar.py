"""Calendar platform for the Limburg.net Afvalkalender integration."""
from __future__ import annotations

import datetime as dt

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import get_waste_type_name
from .coordinator import LimburgNetConfigEntry, LimburgNetCoordinator
from .entity import device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LimburgNetConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Limburg.net calendar entity."""
    async_add_entities([LimburgNetCalendar(entry.runtime_data, entry)])


class LimburgNetCalendar(CoordinatorEntity[LimburgNetCoordinator], CalendarEntity):
    """Calendar listing every upcoming waste collection as an all-day event."""

    _attr_has_entity_name = True
    _attr_translation_key = "collections"

    def __init__(
        self, coordinator: LimburgNetCoordinator, entry: LimburgNetConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_calendar"
        self._attr_device_info = device_info(entry)

    def _events(self) -> list[CalendarEvent]:
        language = self.hass.config.language
        events = [
            CalendarEvent(
                start=collection_date,
                end=collection_date + dt.timedelta(days=1),
                summary=get_waste_type_name(waste_type, language),
            )
            for waste_type, dates in self.coordinator.data.items()
            for collection_date in dates
        ]
        events.sort(key=lambda event: event.start)
        return events

    @property
    def event(self) -> CalendarEvent | None:
        today = dt_util.now().date()
        for event in self._events():
            if event.start >= today:
                return event
        return None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: dt.datetime, end_date: dt.datetime
    ) -> list[CalendarEvent]:
        # Overlap test on local datetimes: an all-day event spans its whole
        # day, so any window touching that day (e.g. 23:55-00:10) includes it.
        start = dt_util.as_local(start_date)
        end = dt_util.as_local(end_date)
        return [
            event
            for event in self._events()
            if event.start_datetime_local < end and event.end_datetime_local > start
        ]
