"""Tests for ABC Emergency sensor platform."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_RADIUS, UnitOfLength
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.abcemergency.const import (
    CONF_STATE,
    CONF_USE_HOME_LOCATION,
    DOMAIN,
    AlertLevel,
)
from custom_components.abcemergency.models import CoordinatorData
from custom_components.abcemergency.sensor import (
    SENSOR_DESCRIPTIONS,
    ABCEmergencySensor,
    _get_nearest_incident_attrs,
    async_setup_entry,
)

if TYPE_CHECKING:
    pass


class TestSensorDescriptions:
    """Test sensor entity descriptions."""

    def test_sensor_descriptions_exist(self) -> None:
        """Test that sensor descriptions are defined."""
        assert len(SENSOR_DESCRIPTIONS) == 7

    def test_sensor_descriptions_have_required_fields(self) -> None:
        """Test that sensor descriptions have required fields."""
        for desc in SENSOR_DESCRIPTIONS:
            assert desc.key
            assert desc.translation_key
            assert desc.value_fn is not None

    def test_incidents_total_description(self) -> None:
        """Test incidents_total sensor description."""
        desc = next(d for d in SENSOR_DESCRIPTIONS if d.key == "incidents_total")
        assert desc.translation_key == "incidents_total"

    def test_incidents_nearby_description(self) -> None:
        """Test incidents_nearby sensor description."""
        desc = next(d for d in SENSOR_DESCRIPTIONS if d.key == "incidents_nearby")
        assert desc.translation_key == "incidents_nearby"

    def test_nearest_incident_description(self) -> None:
        """Test nearest_incident sensor description."""
        desc = next(d for d in SENSOR_DESCRIPTIONS if d.key == "nearest_incident")
        assert desc.native_unit_of_measurement == UnitOfLength.KILOMETERS
        assert desc.attr_fn is not None

    def test_highest_alert_level_description(self) -> None:
        """Test highest_alert_level sensor description."""
        desc = next(d for d in SENSOR_DESCRIPTIONS if d.key == "highest_alert_level")
        assert desc.translation_key == "highest_alert_level"

    def test_bushfires_description(self) -> None:
        """Test bushfires sensor description."""
        desc = next(d for d in SENSOR_DESCRIPTIONS if d.key == "bushfires")
        assert desc.translation_key == "bushfires"

    def test_floods_description(self) -> None:
        """Test floods sensor description."""
        desc = next(d for d in SENSOR_DESCRIPTIONS if d.key == "floods")
        assert desc.translation_key == "floods"

    def test_storms_description(self) -> None:
        """Test storms sensor description."""
        desc = next(d for d in SENSOR_DESCRIPTIONS if d.key == "storms")
        assert desc.translation_key == "storms"


class TestGetNearestIncidentAttrs:
    """Test the _get_nearest_incident_attrs helper function."""

    def test_returns_empty_when_no_nearest(
        self,
        mock_coordinator_data_empty: CoordinatorData,
    ) -> None:
        """Test returns empty dict when no nearest incident."""
        result = _get_nearest_incident_attrs(mock_coordinator_data_empty)
        assert result == {}

    def test_returns_attrs_when_nearest_exists(
        self,
        mock_coordinator_data: CoordinatorData,
    ) -> None:
        """Test returns attributes when nearest incident exists."""
        result = _get_nearest_incident_attrs(mock_coordinator_data)
        assert result["headline"] == "Bushfire at Test Location"
        assert result["alert_level"] == AlertLevel.EMERGENCY
        assert result["event_type"] == "Bushfire"
        assert result["direction"] == "S"


class TestSensorValueFunctions:
    """Test sensor value functions in descriptions."""

    def test_incidents_total_value(
        self,
        mock_coordinator_data: CoordinatorData,
    ) -> None:
        """Test incidents_total returns correct value."""
        desc = next(d for d in SENSOR_DESCRIPTIONS if d.key == "incidents_total")
        assert desc.value_fn(mock_coordinator_data) == 3

    def test_incidents_nearby_value(
        self,
        mock_coordinator_data: CoordinatorData,
    ) -> None:
        """Test incidents_nearby returns correct value."""
        desc = next(d for d in SENSOR_DESCRIPTIONS if d.key == "incidents_nearby")
        assert desc.value_fn(mock_coordinator_data) == 3

    def test_nearest_incident_value(
        self,
        mock_coordinator_data: CoordinatorData,
    ) -> None:
        """Test nearest_incident returns distance."""
        desc = next(d for d in SENSOR_DESCRIPTIONS if d.key == "nearest_incident")
        assert desc.value_fn(mock_coordinator_data) == 10.5

    def test_nearest_incident_value_none(
        self,
        mock_coordinator_data_empty: CoordinatorData,
    ) -> None:
        """Test nearest_incident returns None when no incidents."""
        desc = next(d for d in SENSOR_DESCRIPTIONS if d.key == "nearest_incident")
        assert desc.value_fn(mock_coordinator_data_empty) is None

    def test_highest_alert_level_value(
        self,
        mock_coordinator_data: CoordinatorData,
    ) -> None:
        """Test highest_alert_level returns correct value."""
        desc = next(d for d in SENSOR_DESCRIPTIONS if d.key == "highest_alert_level")
        assert desc.value_fn(mock_coordinator_data) == AlertLevel.EMERGENCY

    def test_highest_alert_level_value_none(
        self,
        mock_coordinator_data_empty: CoordinatorData,
    ) -> None:
        """Test highest_alert_level returns 'none' when no alerts."""
        desc = next(d for d in SENSOR_DESCRIPTIONS if d.key == "highest_alert_level")
        assert desc.value_fn(mock_coordinator_data_empty) == "none"

    def test_bushfires_value(
        self,
        mock_coordinator_data: CoordinatorData,
    ) -> None:
        """Test bushfires returns correct count."""
        desc = next(d for d in SENSOR_DESCRIPTIONS if d.key == "bushfires")
        assert desc.value_fn(mock_coordinator_data) == 1

    def test_bushfires_value_zero(
        self,
        mock_coordinator_data_empty: CoordinatorData,
    ) -> None:
        """Test bushfires returns 0 when no bushfires."""
        desc = next(d for d in SENSOR_DESCRIPTIONS if d.key == "bushfires")
        assert desc.value_fn(mock_coordinator_data_empty) == 0

    def test_floods_value(
        self,
        mock_coordinator_data: CoordinatorData,
    ) -> None:
        """Test floods returns correct count."""
        desc = next(d for d in SENSOR_DESCRIPTIONS if d.key == "floods")
        assert desc.value_fn(mock_coordinator_data) == 1

    def test_storms_value(
        self,
        mock_coordinator_data: CoordinatorData,
    ) -> None:
        """Test storms returns correct count."""
        desc = next(d for d in SENSOR_DESCRIPTIONS if d.key == "storms")
        assert desc.value_fn(mock_coordinator_data) == 1


class TestABCEmergencySensor:
    """Test ABCEmergencySensor entity."""

    def test_sensor_unique_id(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test sensor unique ID is correctly generated."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_STATE: "nsw",
                CONF_LATITUDE: -33.8688,
                CONF_LONGITUDE: 151.2093,
                CONF_RADIUS: 50,
                CONF_USE_HOME_LOCATION: True,
            },
            unique_id="abc_emergency_nsw",
        )
        desc = SENSOR_DESCRIPTIONS[0]

        sensor = ABCEmergencySensor(mock_coordinator, entry, desc)

        assert sensor.unique_id == f"{entry.entry_id}_{desc.key}"

    def test_sensor_native_value(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test sensor returns correct native value."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_STATE: "nsw",
                CONF_LATITUDE: -33.8688,
                CONF_LONGITUDE: 151.2093,
                CONF_RADIUS: 50,
                CONF_USE_HOME_LOCATION: True,
            },
            unique_id="abc_emergency_nsw",
        )
        desc = next(d for d in SENSOR_DESCRIPTIONS if d.key == "incidents_total")

        sensor = ABCEmergencySensor(mock_coordinator, entry, desc)

        assert sensor.native_value == 3

    def test_sensor_extra_state_attributes_with_fn(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test sensor returns extra state attributes when fn is defined."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_STATE: "nsw",
                CONF_LATITUDE: -33.8688,
                CONF_LONGITUDE: 151.2093,
                CONF_RADIUS: 50,
                CONF_USE_HOME_LOCATION: True,
            },
            unique_id="abc_emergency_nsw",
        )
        desc = next(d for d in SENSOR_DESCRIPTIONS if d.key == "nearest_incident")

        sensor = ABCEmergencySensor(mock_coordinator, entry, desc)

        attrs = sensor.extra_state_attributes
        assert attrs is not None
        assert attrs["headline"] == "Bushfire at Test Location"

    def test_sensor_extra_state_attributes_without_fn(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test sensor returns None for attributes when fn is not defined."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_STATE: "nsw",
                CONF_LATITUDE: -33.8688,
                CONF_LONGITUDE: 151.2093,
                CONF_RADIUS: 50,
                CONF_USE_HOME_LOCATION: True,
            },
            unique_id="abc_emergency_nsw",
        )
        desc = next(d for d in SENSOR_DESCRIPTIONS if d.key == "incidents_total")

        sensor = ABCEmergencySensor(mock_coordinator, entry, desc)

        assert sensor.extra_state_attributes is None


class TestAsyncSetupEntry:
    """Test async_setup_entry for sensor platform."""

    async def test_setup_creates_all_sensors(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test that setup creates all sensor entities."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_STATE: "nsw",
                CONF_LATITUDE: -33.8688,
                CONF_LONGITUDE: 151.2093,
                CONF_RADIUS: 50,
                CONF_USE_HOME_LOCATION: True,
            },
            unique_id="abc_emergency_nsw",
        )
        entry.add_to_hass(hass)

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = mock_coordinator

        entities_added: list = []

        def mock_add_entities(entities: list) -> None:
            entities_added.extend(entities)

        await async_setup_entry(hass, entry, mock_add_entities)

        assert len(entities_added) == 7
        assert all(isinstance(e, ABCEmergencySensor) for e in entities_added)
