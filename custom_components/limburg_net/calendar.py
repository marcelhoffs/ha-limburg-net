"""Calendar platform for the Limburg.net Afvalkalender integration."""
from __future__ import annotations

import datetime as dt

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .coordinator import LimburgNetConfigEntry, LimburgNetCoordinator
from .entity import device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LimburgNetConfigEntry,
    async_add_entities: AddEntitiesCallback,
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
        events = [
            CalendarEvent(
                start=collection_date,
                end=collection_date + dt.timedelta(days=1),
                summary=waste_type,
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
        start = dt_util.as_local(start_date).date()
        end = dt_util.as_local(end_date).date()
        return [event for event in self._events() if start <= event.start < end]
