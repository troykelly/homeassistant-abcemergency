"""Tests for ABC Emergency base entity."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from homeassistant.helpers.device_registry import DeviceEntryType

from custom_components.abcemergency.const import (
    CONF_INSTANCE_TYPE,
    CONF_PERSON_NAME,
    CONF_STATE,
    CONF_ZONE_NAME,
    DOMAIN,
    INSTANCE_TYPE_PERSON,
    INSTANCE_TYPE_STATE,
    INSTANCE_TYPE_ZONE,
)
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
        instance_type=INSTANCE_TYPE_STATE,
    )
    return coordinator


@pytest.fixture
def mock_config_entry_state() -> MagicMock:
    """Create a mock config entry for state mode."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id_12345"
    entry.data = {
        CONF_INSTANCE_TYPE: INSTANCE_TYPE_STATE,
        CONF_STATE: "nsw",
    }
    return entry


@pytest.fixture
def mock_config_entry_zone() -> MagicMock:
    """Create a mock config entry for zone mode."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id_zone"
    entry.data = {
        CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE,
        CONF_ZONE_NAME: "Home",
    }
    return entry


@pytest.fixture
def mock_config_entry_person() -> MagicMock:
    """Create a mock config entry for person mode."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id_person"
    entry.data = {
        CONF_INSTANCE_TYPE: INSTANCE_TYPE_PERSON,
        CONF_PERSON_NAME: "John",
    }
    return entry


class TestABCEmergencyEntity:
    """Test ABCEmergencyEntity base class."""

    def test_has_entity_name_enabled(
        self,
        mock_coordinator: MagicMock,
        mock_config_entry_state: MagicMock,
    ) -> None:
        """Test _attr_has_entity_name is True."""
        entity = ABCEmergencyEntity(mock_coordinator, mock_config_entry_state)
        assert entity._attr_has_entity_name is True

    def test_device_info_identifiers(
        self,
        mock_coordinator: MagicMock,
        mock_config_entry_state: MagicMock,
    ) -> None:
        """Test device info identifiers are correctly set."""
        entity = ABCEmergencyEntity(mock_coordinator, mock_config_entry_state)

        assert entity._attr_device_info is not None
        identifiers = entity._attr_device_info.get("identifiers")
        assert identifiers is not None
        assert (DOMAIN, "test_entry_id_12345") in identifiers

    def test_device_info_name_state_mode(
        self,
        mock_coordinator: MagicMock,
        mock_config_entry_state: MagicMock,
    ) -> None:
        """Test device info name for state mode."""
        entity = ABCEmergencyEntity(mock_coordinator, mock_config_entry_state)

        assert entity._attr_device_info is not None
        assert entity._attr_device_info.get("name") == "ABC Emergency (New South Wales)"

    def test_device_info_name_zone_mode(
        self,
        mock_coordinator: MagicMock,
        mock_config_entry_zone: MagicMock,
    ) -> None:
        """Test device info name for zone mode."""
        entity = ABCEmergencyEntity(mock_coordinator, mock_config_entry_zone)

        assert entity._attr_device_info is not None
        assert entity._attr_device_info.get("name") == "ABC Emergency (Home)"

    def test_device_info_name_person_mode(
        self,
        mock_coordinator: MagicMock,
        mock_config_entry_person: MagicMock,
    ) -> None:
        """Test device info name for person mode."""
        entity = ABCEmergencyEntity(mock_coordinator, mock_config_entry_person)

        assert entity._attr_device_info is not None
        assert entity._attr_device_info.get("name") == "ABC Emergency (John)"

    def test_device_info_name_different_states(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test device name with different states."""
        for state_code, expected_name in [
            ("vic", "ABC Emergency (Victoria)"),
            ("qld", "ABC Emergency (Queensland)"),
            ("sa", "ABC Emergency (South Australia)"),
            ("wa", "ABC Emergency (Western Australia)"),
            ("tas", "ABC Emergency (Tasmania)"),
            ("nt", "ABC Emergency (Northern Territory)"),
            ("act", "ABC Emergency (Australian Capital Territory)"),
        ]:
            entry = MagicMock()
            entry.entry_id = "test_id"
            entry.data = {
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_STATE,
                CONF_STATE: state_code,
            }

            entity = ABCEmergencyEntity(mock_coordinator, entry)

            assert entity._attr_device_info is not None
            assert entity._attr_device_info.get("name") == expected_name

    def test_device_info_manufacturer(
        self,
        mock_coordinator: MagicMock,
        mock_config_entry_state: MagicMock,
    ) -> None:
        """Test device info manufacturer is ABC."""
        entity = ABCEmergencyEntity(mock_coordinator, mock_config_entry_state)

        assert entity._attr_device_info is not None
        assert entity._attr_device_info.get("manufacturer") == "Australian Broadcasting Corporation"

    def test_device_info_model(
        self,
        mock_coordinator: MagicMock,
        mock_config_entry_state: MagicMock,
    ) -> None:
        """Test device info model."""
        entity = ABCEmergencyEntity(mock_coordinator, mock_config_entry_state)

        assert entity._attr_device_info is not None
        assert entity._attr_device_info.get("model") == "Emergency Data Feed"

    def test_device_info_entry_type(
        self,
        mock_coordinator: MagicMock,
        mock_config_entry_state: MagicMock,
    ) -> None:
        """Test device info entry type is SERVICE."""
        entity = ABCEmergencyEntity(mock_coordinator, mock_config_entry_state)

        assert entity._attr_device_info is not None
        assert entity._attr_device_info.get("entry_type") == DeviceEntryType.SERVICE

    def test_device_info_configuration_url(
        self,
        mock_coordinator: MagicMock,
        mock_config_entry_state: MagicMock,
    ) -> None:
        """Test device info has configuration URL."""
        entity = ABCEmergencyEntity(mock_coordinator, mock_config_entry_state)

        assert entity._attr_device_info is not None
        assert (
            entity._attr_device_info.get("configuration_url") == "https://www.abc.net.au/emergency"
        )

    def test_data_property(
        self,
        mock_coordinator: MagicMock,
        mock_config_entry_state: MagicMock,
    ) -> None:
        """Test data property returns coordinator data."""
        entity = ABCEmergencyEntity(mock_coordinator, mock_config_entry_state)

        assert entity.data == mock_coordinator.data
        assert isinstance(entity.data, CoordinatorData)

    def test_data_property_reflects_updates(
        self,
        mock_coordinator: MagicMock,
        mock_config_entry_state: MagicMock,
    ) -> None:
        """Test data property reflects coordinator updates."""
        entity = ABCEmergencyEntity(mock_coordinator, mock_config_entry_state)

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
            instance_type=INSTANCE_TYPE_STATE,
        )
        mock_coordinator.data = new_data

        # Should reflect new data
        assert entity.data.total_count == 5
        assert entity.data.nearby_count == 2

    def test_inherits_from_coordinator_entity(
        self,
        mock_coordinator: MagicMock,
        mock_config_entry_state: MagicMock,
    ) -> None:
        """Test entity inherits from CoordinatorEntity."""
        from homeassistant.helpers.update_coordinator import CoordinatorEntity

        entity = ABCEmergencyEntity(mock_coordinator, mock_config_entry_state)

        assert isinstance(entity, CoordinatorEntity)
