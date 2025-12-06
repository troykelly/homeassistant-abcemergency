"""Geo location platform for ABC Emergency integration.

This module provides geo location entities that display emergency incidents
as markers on the Home Assistant map.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.geo_location import GeolocationEvent
from homeassistant.const import UnitOfLength
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SOURCE
from .coordinator import ABCEmergencyCoordinator
from .models import EmergencyIncident

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)


class ABCEmergencyGeolocationEvent(
    CoordinatorEntity[ABCEmergencyCoordinator],
    GeolocationEvent,
):
    """Geo location event for an emergency incident."""

    _attr_should_poll = False
    _attr_unit_of_measurement = UnitOfLength.KILOMETERS

    def __init__(
        self,
        coordinator: ABCEmergencyCoordinator,
        incident: EmergencyIncident,
    ) -> None:
        """Initialize the geo location event.

        Args:
            coordinator: The data update coordinator.
            incident: The emergency incident data.
        """
        super().__init__(coordinator)
        self._incident = incident
        self._attr_unique_id = f"{SOURCE}_{incident.id}"
        self._attr_name = incident.headline

    @property
    def source(self) -> str:
        """Return source of the event."""
        return SOURCE

    @property
    def latitude(self) -> float | None:
        """Return latitude of the event."""
        return self._incident.location.latitude

    @property
    def longitude(self) -> float | None:
        """Return longitude of the event."""
        return self._incident.location.longitude

    @property
    def distance(self) -> float | None:
        """Return distance from home in km."""
        return self._incident.distance_km

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs: dict[str, Any] = {
            "alert_level": self._incident.alert_level,
            "alert_text": self._incident.alert_text,
            "event_type": self._incident.event_type,
            "event_icon": self._incident.event_icon,
            "status": self._incident.status,
            "source": self._incident.source,
            "direction": self._incident.direction,
            "updated": self._incident.updated.isoformat(),
        }
        if self._incident.size:
            attrs["size"] = self._incident.size
        return attrs

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # Find this incident in the updated data
        for incident in self.coordinator.data.incidents:
            if incident.id == self._incident.id:
                self._incident = incident
                self._attr_name = incident.headline
                self.async_write_ha_state()
                return
        # Incident no longer exists - it will be removed by the manager


class ABCEmergencyGeoLocationManager:
    """Manager for geo location entities.

    This class manages the lifecycle of geo location entities, adding new
    entities when incidents appear and tracking existing ones.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: ABCEmergencyCoordinator,
        async_add_entities: AddEntitiesCallback,
    ) -> None:
        """Initialize the manager.

        Args:
            hass: Home Assistant instance.
            coordinator: The data update coordinator.
            async_add_entities: Callback to add entities.
        """
        self._hass = hass
        self._coordinator = coordinator
        self._async_add_entities = async_add_entities
        self._entities: dict[str, ABCEmergencyGeolocationEvent] = {}

    @callback
    def async_update(self) -> None:
        """Update geo location entities based on current data."""
        if self._coordinator.data is None:
            return

        current_ids = {i.id for i in self._coordinator.data.incidents}
        existing_ids = set(self._entities.keys())

        # Add new incidents
        new_ids = current_ids - existing_ids
        if new_ids:
            new_incidents = [i for i in self._coordinator.data.incidents if i.id in new_ids]
            new_entities = [
                ABCEmergencyGeolocationEvent(self._coordinator, incident)
                for incident in new_incidents
            ]
            self._async_add_entities(new_entities)
            for entity in new_entities:
                self._entities[entity._incident.id] = entity

        # Remove old incidents
        removed_ids = existing_ids - current_ids
        for incident_id in removed_ids:
            entity = self._entities.pop(incident_id, None)
            if entity:
                self._hass.async_create_task(entity.async_remove(force_remove=True))


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ABC Emergency geo location platform.

    Args:
        hass: Home Assistant instance.
        entry: Config entry being set up.
        async_add_entities: Callback to add entities.
    """
    coordinator: ABCEmergencyCoordinator = hass.data[DOMAIN][entry.entry_id]

    manager = ABCEmergencyGeoLocationManager(hass, coordinator, async_add_entities)

    # Initial population
    manager.async_update()

    # Subscribe to updates
    entry.async_on_unload(coordinator.async_add_listener(manager.async_update))
