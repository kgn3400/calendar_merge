"""The Calendar merge integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .calendar_handler import CalendarHandler
from .const import DOMAIN, LOGGER


# ------------------------------------------------------------------
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up State updates from a config entry."""

    calendar_handler: CalendarHandler = CalendarHandler(
        hass,
        entry,
    )

    coordinator: DataUpdateCoordinator = DataUpdateCoordinator(
        hass,
        LOGGER,
        name=DOMAIN,
    )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "calendar_handler": calendar_handler,
        "coordinator": coordinator,
    }

    entry.async_on_unload(entry.add_update_listener(update_listener))

    await hass.config_entries.async_forward_entry_setups(
        entry, [Platform.SENSOR, Platform.CALENDAR]
    )

    return True


# ------------------------------------------------------------------
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    return await hass.config_entries.async_unload_platforms(
        entry, [Platform.SENSOR, Platform.CALENDAR]
    )


# ------------------------------------------------------------------
async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


# ------------------------------------------------------------------
async def update_listener(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> None:
    """Reload on config entry update."""

    calendar_handler: CalendarHandler = hass.data[DOMAIN][config_entry.entry_id][
        "calendar_handler"
    ]

    if calendar_handler.supress_update_listener:
        calendar_handler.supress_update_listener = False
        return

    await hass.config_entries.async_reload(config_entry.entry_id)
