"""Tests for ABC Emergency base entity."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from homeassistant.helpers.device_registry import DeviceEntryType

from custom_components.abcemergency.const import DOMAIN
from custom_components.abcemergency.entity import ABCEmergencyEntity
from custom_components.abcemergency.models import CoordinatorData

if TYPE_CHECKING:
    pass


@pytest.fixture
def mock_coordinator() -> MagicMock:
    """Create a mock coordinator."""
    coordinator = MagicMock()
    coordinator.data = CoordinatorData(
        incidents=[],
        total_count=0,
        nearby_count=0,
        nearest_distance_km=None,
        nearest_incident=None,
        highest_alert_level="",
        incidents_by_type={},
    )
    return coordinator


@pytest.fixture
def mock_config_entry() -> MagicMock:
    """Create a mock config entry."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id_12345"
    entry.data = {"state": "nsw"}
    return entry


class TestABCEmergencyEntity:
    """Test ABCEmergencyEntity base class."""

    def test_has_entity_name_enabled(
        self,
        mock_coordinator: MagicMock,
        mock_config_entry: MagicMock,
    ) -> None:
        """Test _attr_has_entity_name is True."""
        entity = ABCEmergencyEntity(mock_coordinator, mock_config_entry)
        assert entity._attr_has_entity_name is True

    def test_device_info_identifiers(
        self,
        mock_coordinator: MagicMock,
        mock_config_entry: MagicMock,
    ) -> None:
        """Test device info identifiers are correctly set."""
        entity = ABCEmergencyEntity(mock_coordinator, mock_config_entry)

        assert entity._attr_device_info is not None
        identifiers = entity._attr_device_info.get("identifiers")
        assert identifiers is not None
        assert (DOMAIN, "test_entry_id_12345") in identifiers

    def test_device_info_name(
        self,
        mock_coordinator: MagicMock,
        mock_config_entry: MagicMock,
    ) -> None:
        """Test device info name includes state."""
        entity = ABCEmergencyEntity(mock_coordinator, mock_config_entry)

        assert entity._attr_device_info is not None
        assert entity._attr_device_info.get("name") == "ABC Emergency (NSW)"

    def test_device_info_name_different_state(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test device name with different states."""
        for state_code, expected_name in [
            ("vic", "ABC Emergency (VIC)"),
            ("qld", "ABC Emergency (QLD)"),
            ("sa", "ABC Emergency (SA)"),
            ("wa", "ABC Emergency (WA)"),
            ("tas", "ABC Emergency (TAS)"),
            ("nt", "ABC Emergency (NT)"),
            ("act", "ABC Emergency (ACT)"),
        ]:
            entry = MagicMock()
            entry.entry_id = "test_id"
            entry.data = {"state": state_code}

            entity = ABCEmergencyEntity(mock_coordinator, entry)

            assert entity._attr_device_info is not None
            assert entity._attr_device_info.get("name") == expected_name

    def test_device_info_manufacturer(
        self,
        mock_coordinator: MagicMock,
        mock_config_entry: MagicMock,
    ) -> None:
        """Test device info manufacturer is ABC."""
        entity = ABCEmergencyEntity(mock_coordinator, mock_config_entry)

        assert entity._attr_device_info is not None
        assert entity._attr_device_info.get("manufacturer") == "Australian Broadcasting Corporation"

    def test_device_info_model(
        self,
        mock_coordinator: MagicMock,
        mock_config_entry: MagicMock,
    ) -> None:
        """Test device info model."""
        entity = ABCEmergencyEntity(mock_coordinator, mock_config_entry)

        assert entity._attr_device_info is not None
        assert entity._attr_device_info.get("model") == "Emergency Data Feed"

    def test_device_info_entry_type(
        self,
        mock_coordinator: MagicMock,
        mock_config_entry: MagicMock,
    ) -> None:
        """Test device info entry type is SERVICE."""
        entity = ABCEmergencyEntity(mock_coordinator, mock_config_entry)

        assert entity._attr_device_info is not None
        assert entity._attr_device_info.get("entry_type") == DeviceEntryType.SERVICE

    def test_device_info_configuration_url(
        self,
        mock_coordinator: MagicMock,
        mock_config_entry: MagicMock,
    ) -> None:
        """Test device info has configuration URL."""
        entity = ABCEmergencyEntity(mock_coordinator, mock_config_entry)

        assert entity._attr_device_info is not None
        assert (
            entity._attr_device_info.get("configuration_url") == "https://www.abc.net.au/emergency"
        )

    def test_data_property(
        self,
        mock_coordinator: MagicMock,
        mock_config_entry: MagicMock,
    ) -> None:
        """Test data property returns coordinator data."""
        entity = ABCEmergencyEntity(mock_coordinator, mock_config_entry)

        assert entity.data == mock_coordinator.data
        assert isinstance(entity.data, CoordinatorData)

    def test_data_property_reflects_updates(
        self,
        mock_coordinator: MagicMock,
        mock_config_entry: MagicMock,
    ) -> None:
        """Test data property reflects coordinator updates."""
        entity = ABCEmergencyEntity(mock_coordinator, mock_config_entry)

        # Initial data
        assert entity.data.total_count == 0

        # Simulate coordinator update
        new_data = CoordinatorData(
            incidents=[],
            total_count=5,
            nearby_count=2,
            nearest_distance_km=10.0,
            nearest_incident=None,
            highest_alert_level="moderate",
            incidents_by_type={"Bushfire": 3, "Flood": 2},
        )
        mock_coordinator.data = new_data

        # Should reflect new data
        assert entity.data.total_count == 5
        assert entity.data.nearby_count == 2

    def test_inherits_from_coordinator_entity(
        self,
        mock_coordinator: MagicMock,
        mock_config_entry: MagicMock,
    ) -> None:
        """Test entity inherits from CoordinatorEntity."""
        from homeassistant.helpers.update_coordinator import CoordinatorEntity

        entity = ABCEmergencyEntity(mock_coordinator, mock_config_entry)

        assert isinstance(entity, CoordinatorEntity)
