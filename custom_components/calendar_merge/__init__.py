"""The Calendar merge integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.generated.entity_platforms import EntityPlatforms
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .calendar_handler import CalendarHandler
from .const import DOMAIN, LOGGER
from .hass_util import check_supress_config_update_listener


# ------------------------------------------------------------------
# ------------------------------------------------------------------
@dataclass
class CommonData:
    """Common data."""

    calendar_handler: CalendarHandler
    coordinator: DataUpdateCoordinator


# The type alias needs to be suffixed with 'ConfigEntry'
type CommonConfigEntry = ConfigEntry[CommonData]

sensor_platforms: list[EntityPlatforms] = [
    Platform.SENSOR,
    Platform.CALENDAR,
    Platform.SWITCH,
]


# ------------------------------------------------------------------
async def async_setup_entry(hass: HomeAssistant, entry: CommonConfigEntry) -> bool:
    """Set up State updates from a config entry."""

    calendar_handler: CalendarHandler = CalendarHandler(
        hass,
        entry,
    )

    await calendar_handler.async_init()

    coordinator: DataUpdateCoordinator = DataUpdateCoordinator(
        hass,
        LOGGER,
        name=DOMAIN,
        config_entry=entry,
    )

    entry.runtime_data = CommonData(calendar_handler, coordinator)

    entry.async_on_unload(entry.add_update_listener(config_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, sensor_platforms)

    return True


# ------------------------------------------------------------------
async def async_unload_entry(hass: HomeAssistant, entry: CommonConfigEntry) -> bool:
    """Unload a config entry."""

    return await hass.config_entries.async_unload_platforms(entry, sensor_platforms)


# ------------------------------------------------------------------
async def async_reload_entry(hass: HomeAssistant, entry: CommonConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


# ------------------------------------------------------------------
@check_supress_config_update_listener()
async def config_update_listener(
    hass: HomeAssistant,
    config_entry: CommonConfigEntry,
) -> None:
    """Reload on config entry update."""

    if config_entry.runtime_data.calendar_handler.suppress_update_listener:
        config_entry.runtime_data.calendar_handler.suppress_update_listener = False
        return

    await hass.config_entries.async_reload(config_entry.entry_id)
