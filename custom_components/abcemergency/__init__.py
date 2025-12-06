"""ABC Emergency integration for Home Assistant.

This integration provides real-time Australian emergency incident data
from ABC Emergency (abc.net.au/emergency), enabling location-based alerting
for bushfires, floods, storms, cyclones, and other emergencies.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_RADIUS,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ABCEmergencyClient
from .const import CONF_STATE, DEFAULT_RADIUS_KM, DOMAIN
from .coordinator import ABCEmergencyCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.GEO_LOCATION,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ABC Emergency from a config entry.

    Args:
        hass: Home Assistant instance.
        entry: Config entry being set up.

    Returns:
        True if setup was successful.
    """
    hass.data.setdefault(DOMAIN, {})

    session = async_get_clientsession(hass)
    client = ABCEmergencyClient(session)

    # Get radius from options first, then data, then default
    radius = entry.options.get(
        CONF_RADIUS,
        entry.data.get(CONF_RADIUS, DEFAULT_RADIUS_KM),
    )

    coordinator = ABCEmergencyCoordinator(
        hass,
        client,
        state=entry.data[CONF_STATE],
        latitude=entry.data[CONF_LATITUDE],
        longitude=entry.data[CONF_LONGITUDE],
        radius_km=radius,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for options
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.

    Args:
        hass: Home Assistant instance.
        entry: Config entry being unloaded.

    Returns:
        True if unload was successful.
    """
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update.

    Args:
        hass: Home Assistant instance.
        entry: Config entry with updated options.
    """
    await hass.config_entries.async_reload(entry.entry_id)
