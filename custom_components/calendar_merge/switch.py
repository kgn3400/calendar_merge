"""Calendar merge show time as time to."""

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import CommonConfigEntry
from .calendar_handler import CalendarHandler
from .const import (
    CONF_SHOW_EVENT_AS_TIME_TO,
    DOMAIN,
    TRANSLATION_KEY_SWITCH_SHOW_AS_TIME_TO,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up calendar merge show time as time to platform."""

    async_add_entities([ShowAsTimeTo(hass, entry)])


# ------------------------------------------------------
# ------------------------------------------------------
class ShowAsTimeTo(SwitchEntity):
    """Implement the show as time to switch entity."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: CommonConfigEntry,
    ) -> None:
        """Initialize the show as tine to switch entity."""

        self.hass: HomeAssistant = hass
        self.entry: ConfigEntry = entry
        self.calendar_handler: CalendarHandler = entry.runtime_data.calendar_handler
        self.coordinator: DataUpdateCoordinator = entry.runtime_data.coordinator

        self.translation_key = TRANSLATION_KEY_SWITCH_SHOW_AS_TIME_TO
        self.has_entity_name = True
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.entry.title)},
            name=self.entry.title,
        )

    @property
    # ------------------------------------------------------
    def is_on(self) -> bool:
        """Return True if entity is on."""
        return self.calendar_handler.show_event_as_time_to

    # ------------------------------------------------------
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""

        self.calendar_handler.show_event_as_time_to = True

        tmp_entry_options: dict[str, Any] = self.entry.options.copy()
        tmp_entry_options[CONF_SHOW_EVENT_AS_TIME_TO] = (
            self.calendar_handler.show_event_as_time_to
        )
        self.calendar_handler.update_settings(tmp_entry_options)

        await self.coordinator.async_refresh()

    # ------------------------------------------------------
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        self.calendar_handler.show_event_as_time_to = False

        tmp_entry_options: dict[str, Any] = self.entry.options.copy()
        tmp_entry_options[CONF_SHOW_EVENT_AS_TIME_TO] = (
            self.calendar_handler.show_event_as_time_to
        )
        self.calendar_handler.update_settings(tmp_entry_options)

        await self.coordinator.async_refresh()

    # ------------------------------------------------------
    # @property
    # def name(self) -> str:
    #     """Name.

    #     Returns:
    #         str: Name of sensor

    #     """
    #     return f"{self.entry.title}_{TRANSLATION_KEY_SWITCH_SHOW_AS_TIME_TO}"
    #     # return self.entry.title + " Show as time to"

    # ------------------------------------------------------
    @property
    def unique_id(self) -> str:
        """Unique id.

        Returns:
            str: Unique id

        """
        return f"{self.entry.entry_id}_{TRANSLATION_KEY_SWITCH_SHOW_AS_TIME_TO}"

        # return f"{self.entry.entry_id}_{TRANSLATION_KEY_SWITCH_SHOW_AS_TIME_TO}"
