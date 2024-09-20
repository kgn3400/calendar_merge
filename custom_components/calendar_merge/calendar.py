"""Calendars merge."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

# from homeassistant.util import dt as dt_util
from .calendar_handler import CalendarHandler
from .const import DOMAIN


# ------------------------------------------------------
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up calendar items based on a config entry."""

    async_add_entities([EventsCalendar(hass, config_entry)])


# ------------------------------------------------------
# ------------------------------------------------------
class EventsCalendar(CalendarEntity):
    """Define a events calendar."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
    ) -> None:
        """Initialize a Calendar events."""

        self.hass: HomeAssistant = hass
        self.entry: ConfigEntry = entry
        self._event: CalendarEvent | None = None
        # self.tmp_calendar_event: list = []

        self.coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
            "coordinator"
        ]
        self.calendar_handler: CalendarHandler = hass.data[DOMAIN][entry.entry_id][
            "calendar_handler"
        ]

    # ------------------------------------------------------
    @property
    def name(self) -> str:
        """Name.

        Returns:
            str: Name

        """

        return self.entry.title

    # ------------------------------------------------------
    @property
    def unique_id(self) -> str:
        """Unique id.

        Returns:
            str: Unique  id

        """
        return self.entry.entry_id + "calendar"

    # ------------------------------------------------------
    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""

        if len(self.calendar_handler.events) == 0:
            self._event = None
            return None

        event = self.calendar_handler.events[0]

        self._event = CalendarEvent(
            start=event.start,
            end=event.end,
            summary=event.summary,
            description=event.description,
            location=event.location,
        )

        return self._event

    # ------------------------------------------------------
    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return calendar events within a datetime range."""

        events: list[CalendarEvent] = []

        for tmp_event in self.calendar_handler.events:
            check_start: datetime = tmp_event.start_datetime_local

            check_end: datetime = tmp_event.end_datetime_local

            if (
                start_date <= check_start < end_date
                or start_date < check_end <= end_date
                or check_start <= start_date < check_end
                or check_start < end_date <= check_end
            ):
                events.append(
                    CalendarEvent(
                        start=tmp_event.start,
                        end=tmp_event.end,
                        summary=tmp_event.summary,
                        description=tmp_event.description,
                        location=tmp_event.location,
                    )
                )
        return events

    # ------------------------------------------------------
    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )
