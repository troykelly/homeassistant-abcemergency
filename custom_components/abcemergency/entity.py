"""Base entity for ABC Emergency integration.

This module provides the base entity class that all ABC Emergency entity
platforms inherit from. It handles common functionality like device info
and coordinator data access.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ABCEmergencyCoordinator
from .models import CoordinatorData

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry


class ABCEmergencyEntity(CoordinatorEntity[ABCEmergencyCoordinator]):
    """Base entity for ABC Emergency.

    This class provides common functionality for all ABC Emergency entities,
    including device registration and coordinator data access.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ABCEmergencyCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the entity.

        Args:
            coordinator: The data update coordinator.
            config_entry: The config entry for this integration instance.
        """
        super().__init__(coordinator)

        state_upper = config_entry.data["state"].upper()

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=f"ABC Emergency ({state_upper})",
            manufacturer="Australian Broadcasting Corporation",
            model="Emergency Data Feed",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://www.abc.net.au/emergency",
        )

    @property
    def data(self) -> CoordinatorData:
        """Return coordinator data.

        This is a convenience property that returns the coordinator's data
        with proper typing for easy access in entity subclasses.

        Returns:
            The current coordinator data.
        """
        return self.coordinator.data
