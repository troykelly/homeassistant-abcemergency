"""Sensor platform for ABC Emergency integration.

This module provides sensor entities that expose emergency incident data
such as counts, distances, and aggregate information.

Sensors created depend on instance type:
- State: Total incidents, highest alert level, incidents by type
- Zone/Person: Above plus nearby count, nearest incident distance
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfLength
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_INSTANCE_TYPE,
    DOMAIN,
    INSTANCE_TYPE_STATE,
)
from .coordinator import ABCEmergencyCoordinator
from .entity import ABCEmergencyEntity
from .models import CoordinatorData, EmergencyIncident

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry


@dataclass(frozen=True, kw_only=True)
class ABCEmergencySensorEntityDescription(SensorEntityDescription):
    """Entity description for ABC Emergency sensors."""

    value_fn: Callable[[CoordinatorData], int | float | str | None]
    attr_fn: Callable[[CoordinatorData], dict[str, Any]] | None = None
    location_only: bool = False  # Only for zone/person instances


def _get_nearest_incident_attrs(data: CoordinatorData) -> dict[str, Any]:
    """Get attributes for nearest incident sensor."""
    if not data.nearest_incident:
        return {}
    return {
        "headline": data.nearest_incident.headline,
        "alert_level": data.nearest_incident.alert_level,
        "event_type": data.nearest_incident.event_type,
        "direction": data.nearest_incident.direction,
        "contains_point": data.nearest_incident.contains_point,
        "has_polygon": data.nearest_incident.has_polygon,
    }


def _incident_to_dict(incident: EmergencyIncident) -> dict[str, Any]:
    """Convert an EmergencyIncident to a dictionary with standard key fields.

    Args:
        incident: The emergency incident to convert.

    Returns:
        Dictionary containing id, headline, alert_level, event_type, distance_km,
        direction, contains_point, and has_polygon.
    """
    return {
        "id": incident.id,
        "headline": incident.headline,
        "alert_level": incident.alert_level,
        "event_type": incident.event_type,
        "distance_km": incident.distance_km,
        "direction": incident.direction,
        "contains_point": incident.contains_point,
        "has_polygon": incident.has_polygon,
    }


def _get_incidents_list_attrs(data: CoordinatorData) -> dict[str, Any]:
    """Get incidents list attribute for count sensors.

    Args:
        data: Coordinator data containing incidents.

    Returns:
        Dictionary with 'incidents' key containing list of incident details,
        plus containment summary fields for zone/person modes.
    """
    result: dict[str, Any] = {
        "incidents": [_incident_to_dict(i) for i in data.incidents] if data.incidents else []
    }

    # Add containment summary for zone/person modes (not state mode)
    if data.instance_type != INSTANCE_TYPE_STATE:
        result["containing_count"] = len(data.containing_incidents)
        result["inside_polygon"] = data.inside_polygon
        result["highest_containing_level"] = data.highest_containing_alert_level or None
    else:
        # State mode has no containment info
        result["containing_count"] = None
        result["inside_polygon"] = None
        result["highest_containing_level"] = None

    return result


def _get_incidents_list_by_type_attrs(data: CoordinatorData, event_type: str) -> dict[str, Any]:
    """Get incidents list attribute filtered by event type.

    Args:
        data: Coordinator data containing incidents.
        event_type: The event type to filter by (e.g., "Bushfire", "Flood", "Storm").

    Returns:
        Dictionary with 'incidents' key containing list of matching incident details,
        plus containing_count for zone/person modes.
    """
    matching = [i for i in data.incidents if i.event_type == event_type] if data.incidents else []
    containing = [i for i in matching if i.contains_point]

    result: dict[str, Any] = {"incidents": [_incident_to_dict(i) for i in matching]}

    # Add containing_count for zone/person modes
    if data.instance_type != INSTANCE_TYPE_STATE:
        result["containing_count"] = len(containing)
    else:
        result["containing_count"] = None

    return result


# Sensors for all instance types
COMMON_SENSOR_DESCRIPTIONS: tuple[ABCEmergencySensorEntityDescription, ...] = (
    ABCEmergencySensorEntityDescription(
        key="incidents_total",
        translation_key="incidents_total",
        native_unit_of_measurement=None,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.total_count,
        attr_fn=_get_incidents_list_attrs,
    ),
    ABCEmergencySensorEntityDescription(
        key="highest_alert_level",
        translation_key="highest_alert_level",
        value_fn=lambda data: data.highest_alert_level or "none",
    ),
    ABCEmergencySensorEntityDescription(
        key="bushfires",
        translation_key="bushfires",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.incidents_by_type.get("Bushfire", 0),
        attr_fn=lambda data: _get_incidents_list_by_type_attrs(data, "Bushfire"),
    ),
    ABCEmergencySensorEntityDescription(
        key="floods",
        translation_key="floods",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.incidents_by_type.get("Flood", 0),
        attr_fn=lambda data: _get_incidents_list_by_type_attrs(data, "Flood"),
    ),
    ABCEmergencySensorEntityDescription(
        key="storms",
        translation_key="storms",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.incidents_by_type.get("Storm", 0),
        attr_fn=lambda data: _get_incidents_list_by_type_attrs(data, "Storm"),
    ),
)

# Sensors only for zone/person instances (require location)
LOCATION_SENSOR_DESCRIPTIONS: tuple[ABCEmergencySensorEntityDescription, ...] = (
    ABCEmergencySensorEntityDescription(
        key="incidents_nearby",
        translation_key="incidents_nearby",
        native_unit_of_measurement=None,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.nearby_count if data.nearby_count is not None else 0,
        attr_fn=_get_incidents_list_attrs,
        location_only=True,
    ),
    ABCEmergencySensorEntityDescription(
        key="nearest_incident",
        translation_key="nearest_incident",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: (
            round(data.nearest_distance_km, 1) if data.nearest_distance_km else None
        ),
        attr_fn=_get_nearest_incident_attrs,
        location_only=True,
    ),
)


class ABCEmergencySensor(ABCEmergencyEntity, SensorEntity):
    """Sensor entity for ABC Emergency."""

    entity_description: ABCEmergencySensorEntityDescription

    def __init__(
        self,
        coordinator: ABCEmergencyCoordinator,
        config_entry: ConfigEntry,
        description: ABCEmergencySensorEntityDescription,
    ) -> None:
        """Initialize the sensor.

        Args:
            coordinator: The data update coordinator.
            config_entry: The config entry for this integration.
            description: The entity description.
        """
        super().__init__(coordinator, config_entry)
        self.entity_description = description
        self._attr_unique_id = f"{config_entry.entry_id}_{description.key}"

    @property
    def native_value(self) -> int | float | str | None:
        """Return the sensor value."""
        return self.entity_description.value_fn(self.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        if self.entity_description.attr_fn:
            return self.entity_description.attr_fn(self.data)
        return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ABC Emergency sensors.

    Args:
        hass: Home Assistant instance.
        entry: Config entry being set up.
        async_add_entities: Callback to add entities.
    """
    coordinator: ABCEmergencyCoordinator = hass.data[DOMAIN][entry.entry_id]
    instance_type = entry.data.get(CONF_INSTANCE_TYPE, INSTANCE_TYPE_STATE)

    # Determine which sensors to create
    descriptions = list(COMMON_SENSOR_DESCRIPTIONS)

    # Add location-specific sensors for zone/person instances
    if instance_type != INSTANCE_TYPE_STATE:
        descriptions.extend(LOCATION_SENSOR_DESCRIPTIONS)

    async_add_entities(
        ABCEmergencySensor(coordinator, entry, description) for description in descriptions
    )
