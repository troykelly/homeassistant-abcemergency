"""Binary sensor platform for ABC Emergency integration.

This module provides binary sensor entities that indicate active alert states,
ideal for automations and notifications.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, AlertLevel
from .coordinator import ABCEmergencyCoordinator
from .entity import ABCEmergencyEntity
from .models import CoordinatorData

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry


@dataclass(frozen=True, kw_only=True)
class ABCEmergencyBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Entity description for ABC Emergency binary sensors."""

    is_on_fn: Callable[[CoordinatorData], bool]
    attr_fn: Callable[[CoordinatorData], dict[str, Any]] | None = None


def _get_emergency_attrs(
    data: CoordinatorData,
    levels: str | tuple[str, ...],
) -> dict[str, Any]:
    """Get attributes for emergency level binary sensors.

    Args:
        data: Coordinator data.
        levels: Alert level(s) to filter by.

    Returns:
        Dictionary of attributes for the nearest matching incident.
    """
    if isinstance(levels, str):
        levels = (levels,)

    matching = [i for i in data.incidents if i.alert_level in levels and i.distance_km is not None]

    if not matching:
        return {}

    nearest = min(matching, key=lambda i: i.distance_km or float("inf"))
    return {
        "count": len(matching),
        "nearest_headline": nearest.headline,
        "nearest_distance_km": round(nearest.distance_km, 1) if nearest.distance_km else None,
        "nearest_direction": nearest.direction,
    }


BINARY_SENSOR_DESCRIPTIONS: tuple[ABCEmergencyBinarySensorEntityDescription, ...] = (
    ABCEmergencyBinarySensorEntityDescription(
        key="active_alert",
        translation_key="active_alert",
        device_class=BinarySensorDeviceClass.SAFETY,
        is_on_fn=lambda data: data.nearby_count > 0,
    ),
    ABCEmergencyBinarySensorEntityDescription(
        key="emergency_warning",
        translation_key="emergency_warning",
        device_class=BinarySensorDeviceClass.SAFETY,
        is_on_fn=lambda data: data.highest_alert_level == AlertLevel.EMERGENCY,
        attr_fn=lambda data: _get_emergency_attrs(data, AlertLevel.EMERGENCY),
    ),
    ABCEmergencyBinarySensorEntityDescription(
        key="watch_and_act",
        translation_key="watch_and_act",
        device_class=BinarySensorDeviceClass.SAFETY,
        is_on_fn=lambda data: data.highest_alert_level
        in (
            AlertLevel.EMERGENCY,
            AlertLevel.WATCH_AND_ACT,
        ),
        attr_fn=lambda data: _get_emergency_attrs(
            data, (AlertLevel.EMERGENCY, AlertLevel.WATCH_AND_ACT)
        ),
    ),
    ABCEmergencyBinarySensorEntityDescription(
        key="advice",
        translation_key="advice",
        device_class=BinarySensorDeviceClass.SAFETY,
        is_on_fn=lambda data: data.highest_alert_level
        in (
            AlertLevel.EMERGENCY,
            AlertLevel.WATCH_AND_ACT,
            AlertLevel.ADVICE,
        ),
    ),
)


class ABCEmergencyBinarySensor(ABCEmergencyEntity, BinarySensorEntity):
    """Binary sensor entity for ABC Emergency."""

    entity_description: ABCEmergencyBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: ABCEmergencyCoordinator,
        config_entry: ConfigEntry,
        description: ABCEmergencyBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor.

        Args:
            coordinator: The data update coordinator.
            config_entry: The config entry for this integration.
            description: The entity description.
        """
        super().__init__(coordinator, config_entry)
        self.entity_description = description
        self._attr_unique_id = f"{config_entry.entry_id}_{description.key}"

    @property
    def is_on(self) -> bool:
        """Return true if there is an active alert."""
        return self.entity_description.is_on_fn(self.data)

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
    """Set up ABC Emergency binary sensors.

    Args:
        hass: Home Assistant instance.
        entry: Config entry being set up.
        async_add_entities: Callback to add entities.
    """
    coordinator: ABCEmergencyCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        ABCEmergencyBinarySensor(coordinator, entry, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
    )
