"""Tests for ABC Emergency sensor platform."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, UnitOfLength
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.abcemergency.const import (
    CONF_INSTANCE_TYPE,
    CONF_STATE,
    CONF_ZONE_NAME,
    DOMAIN,
    INSTANCE_TYPE_STATE,
    INSTANCE_TYPE_ZONE,
    AlertLevel,
)
from custom_components.abcemergency.models import CoordinatorData
from custom_components.abcemergency.sensor import (
    COMMON_SENSOR_DESCRIPTIONS,
    LOCATION_SENSOR_DESCRIPTIONS,
    ABCEmergencySensor,
    _get_incidents_list_attrs,
    _get_incidents_list_by_type_attrs,
    _get_nearest_incident_attrs,
    async_setup_entry,
)

if TYPE_CHECKING:
    pass


class TestSensorDescriptions:
    """Test sensor entity descriptions."""

    def test_common_sensor_descriptions_exist(self) -> None:
        """Test that common sensor descriptions are defined."""
        assert len(COMMON_SENSOR_DESCRIPTIONS) == 5

    def test_location_sensor_descriptions_exist(self) -> None:
        """Test that location sensor descriptions are defined."""
        assert len(LOCATION_SENSOR_DESCRIPTIONS) == 2

    def test_sensor_descriptions_have_required_fields(self) -> None:
        """Test that sensor descriptions have required fields."""
        all_descriptions = list(COMMON_SENSOR_DESCRIPTIONS) + list(LOCATION_SENSOR_DESCRIPTIONS)
        for desc in all_descriptions:
            assert desc.key
            assert desc.translation_key
            assert desc.value_fn is not None

    def test_incidents_total_description(self) -> None:
        """Test incidents_total sensor description."""
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "incidents_total")
        assert desc.translation_key == "incidents_total"

    def test_incidents_nearby_description(self) -> None:
        """Test incidents_nearby sensor description."""
        desc = next(d for d in LOCATION_SENSOR_DESCRIPTIONS if d.key == "incidents_nearby")
        assert desc.translation_key == "incidents_nearby"
        assert desc.location_only is True

    def test_nearest_incident_description(self) -> None:
        """Test nearest_incident sensor description."""
        desc = next(d for d in LOCATION_SENSOR_DESCRIPTIONS if d.key == "nearest_incident")
        assert desc.native_unit_of_measurement == UnitOfLength.KILOMETERS
        assert desc.attr_fn is not None
        assert desc.location_only is True

    def test_highest_alert_level_description(self) -> None:
        """Test highest_alert_level sensor description."""
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "highest_alert_level")
        assert desc.translation_key == "highest_alert_level"

    def test_bushfires_description(self) -> None:
        """Test bushfires sensor description."""
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "bushfires")
        assert desc.translation_key == "bushfires"
        assert desc.attr_fn is not None  # Should have incidents list attr_fn

    def test_floods_description(self) -> None:
        """Test floods sensor description."""
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "floods")
        assert desc.translation_key == "floods"
        assert desc.attr_fn is not None  # Should have incidents list attr_fn

    def test_storms_description(self) -> None:
        """Test storms sensor description."""
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "storms")
        assert desc.translation_key == "storms"
        assert desc.attr_fn is not None  # Should have incidents list attr_fn

    def test_incidents_total_has_attr_fn(self) -> None:
        """Test incidents_total sensor has attr_fn for incidents list."""
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "incidents_total")
        assert desc.attr_fn is not None

    def test_incidents_nearby_has_attr_fn(self) -> None:
        """Test incidents_nearby sensor has attr_fn for incidents list."""
        desc = next(d for d in LOCATION_SENSOR_DESCRIPTIONS if d.key == "incidents_nearby")
        assert desc.attr_fn is not None


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


class TestGetIncidentsListAttrs:
    """Test the _get_incidents_list_attrs helper function."""

    def test_returns_empty_list_when_no_incidents(
        self,
        mock_coordinator_data_empty: CoordinatorData,
    ) -> None:
        """Test returns empty incidents list when no incidents."""
        result = _get_incidents_list_attrs(mock_coordinator_data_empty)
        assert result == {"incidents": []}

    def test_returns_all_incidents_with_standard_fields(
        self,
        mock_coordinator_data: CoordinatorData,
    ) -> None:
        """Test returns all incidents with standard key fields."""
        result = _get_incidents_list_attrs(mock_coordinator_data)
        assert "incidents" in result
        assert len(result["incidents"]) == 3

        # Check first incident (bushfire - nearest)
        first = result["incidents"][0]
        assert first["headline"] == "Bushfire at Test Location"
        assert first["alert_level"] == AlertLevel.EMERGENCY
        assert first["event_type"] == "Bushfire"
        assert first["distance_km"] == 10.5
        assert first["direction"] == "S"

        # Check second incident (flood)
        second = result["incidents"][1]
        assert second["headline"] == "Flood Warning at River Area"
        assert second["alert_level"] == AlertLevel.WATCH_AND_ACT
        assert second["event_type"] == "Flood"
        assert second["distance_km"] == 25.3
        assert second["direction"] == "NW"

    def test_returns_null_distance_for_state_mode(
        self,
        mock_coordinator_data_state: CoordinatorData,
    ) -> None:
        """Test returns null distance/direction for state mode incidents."""
        result = _get_incidents_list_attrs(mock_coordinator_data_state)
        assert "incidents" in result
        assert len(result["incidents"]) == 3

        # All should have null distance and direction
        for incident in result["incidents"]:
            assert incident["distance_km"] is None
            assert incident["direction"] is None

    def test_returns_incident_id_in_attributes(
        self,
        mock_coordinator_data: CoordinatorData,
    ) -> None:
        """Test returns incident ID in attributes."""
        result = _get_incidents_list_attrs(mock_coordinator_data)
        assert "incidents" in result

        # Check all incidents have ID field
        for incident in result["incidents"]:
            assert "id" in incident
            assert incident["id"] is not None


class TestGetIncidentsListByTypeAttrs:
    """Test the _get_incidents_list_by_type_attrs helper function."""

    def test_returns_empty_list_for_missing_type(
        self,
        mock_coordinator_data: CoordinatorData,
    ) -> None:
        """Test returns empty list when event type not present."""
        result = _get_incidents_list_by_type_attrs(mock_coordinator_data, "Cyclone")
        assert result == {"incidents": []}

    def test_returns_only_matching_type(
        self,
        mock_coordinator_data: CoordinatorData,
    ) -> None:
        """Test returns only incidents matching the specified type."""
        result = _get_incidents_list_by_type_attrs(mock_coordinator_data, "Bushfire")
        assert "incidents" in result
        assert len(result["incidents"]) == 1

        incident = result["incidents"][0]
        assert incident["headline"] == "Bushfire at Test Location"
        assert incident["event_type"] == "Bushfire"
        assert incident["distance_km"] == 10.5

    def test_returns_floods_only(
        self,
        mock_coordinator_data: CoordinatorData,
    ) -> None:
        """Test filtering for floods."""
        result = _get_incidents_list_by_type_attrs(mock_coordinator_data, "Flood")
        assert len(result["incidents"]) == 1
        assert result["incidents"][0]["event_type"] == "Flood"

    def test_returns_storms_only(
        self,
        mock_coordinator_data: CoordinatorData,
    ) -> None:
        """Test filtering for storms."""
        result = _get_incidents_list_by_type_attrs(mock_coordinator_data, "Storm")
        assert len(result["incidents"]) == 1
        assert result["incidents"][0]["event_type"] == "Storm"

    def test_returns_empty_when_no_incidents(
        self,
        mock_coordinator_data_empty: CoordinatorData,
    ) -> None:
        """Test returns empty list when no incidents at all."""
        result = _get_incidents_list_by_type_attrs(mock_coordinator_data_empty, "Bushfire")
        assert result == {"incidents": []}


class TestSensorValueFunctions:
    """Test sensor value functions in descriptions."""

    def test_incidents_total_value(
        self,
        mock_coordinator_data: CoordinatorData,
    ) -> None:
        """Test incidents_total returns correct value."""
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "incidents_total")
        assert desc.value_fn(mock_coordinator_data) == 3

    def test_incidents_nearby_value(
        self,
        mock_coordinator_data: CoordinatorData,
    ) -> None:
        """Test incidents_nearby returns correct value."""
        desc = next(d for d in LOCATION_SENSOR_DESCRIPTIONS if d.key == "incidents_nearby")
        assert desc.value_fn(mock_coordinator_data) == 3

    def test_nearest_incident_value(
        self,
        mock_coordinator_data: CoordinatorData,
    ) -> None:
        """Test nearest_incident returns distance."""
        desc = next(d for d in LOCATION_SENSOR_DESCRIPTIONS if d.key == "nearest_incident")
        assert desc.value_fn(mock_coordinator_data) == 10.5

    def test_nearest_incident_value_none(
        self,
        mock_coordinator_data_empty: CoordinatorData,
    ) -> None:
        """Test nearest_incident returns None when no incidents."""
        desc = next(d for d in LOCATION_SENSOR_DESCRIPTIONS if d.key == "nearest_incident")
        assert desc.value_fn(mock_coordinator_data_empty) is None

    def test_highest_alert_level_value(
        self,
        mock_coordinator_data: CoordinatorData,
    ) -> None:
        """Test highest_alert_level returns correct value."""
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "highest_alert_level")
        assert desc.value_fn(mock_coordinator_data) == AlertLevel.EMERGENCY

    def test_highest_alert_level_value_none(
        self,
        mock_coordinator_data_empty: CoordinatorData,
    ) -> None:
        """Test highest_alert_level returns 'none' when no alerts."""
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "highest_alert_level")
        assert desc.value_fn(mock_coordinator_data_empty) == "none"

    def test_bushfires_value(
        self,
        mock_coordinator_data: CoordinatorData,
    ) -> None:
        """Test bushfires returns correct count."""
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "bushfires")
        assert desc.value_fn(mock_coordinator_data) == 1

    def test_bushfires_value_zero(
        self,
        mock_coordinator_data_empty: CoordinatorData,
    ) -> None:
        """Test bushfires returns 0 when no bushfires."""
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "bushfires")
        assert desc.value_fn(mock_coordinator_data_empty) == 0

    def test_floods_value(
        self,
        mock_coordinator_data: CoordinatorData,
    ) -> None:
        """Test floods returns correct count."""
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "floods")
        assert desc.value_fn(mock_coordinator_data) == 1

    def test_storms_value(
        self,
        mock_coordinator_data: CoordinatorData,
    ) -> None:
        """Test storms returns correct count."""
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "storms")
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
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_STATE,
                CONF_STATE: "nsw",
            },
            unique_id="abc_emergency_state_nsw",
        )
        desc = COMMON_SENSOR_DESCRIPTIONS[0]

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
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_STATE,
                CONF_STATE: "nsw",
            },
            unique_id="abc_emergency_state_nsw",
        )
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "incidents_total")

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
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE,
                CONF_ZONE_NAME: "Home",
                CONF_LATITUDE: -33.8688,
                CONF_LONGITUDE: 151.2093,
            },
            unique_id="abc_emergency_zone_home",
        )
        desc = next(d for d in LOCATION_SENSOR_DESCRIPTIONS if d.key == "nearest_incident")

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
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_STATE,
                CONF_STATE: "nsw",
            },
            unique_id="abc_emergency_state_nsw",
        )
        # highest_alert_level is the only sensor without an attr_fn now
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "highest_alert_level")

        sensor = ABCEmergencySensor(mock_coordinator, entry, desc)

        assert sensor.extra_state_attributes is None

    def test_sensor_extra_state_attributes_incidents_total(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test incidents_total sensor returns incidents list attribute."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE,
                CONF_ZONE_NAME: "Home",
                CONF_LATITUDE: -33.8688,
                CONF_LONGITUDE: 151.2093,
            },
            unique_id="abc_emergency_zone_home",
        )
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "incidents_total")

        sensor = ABCEmergencySensor(mock_coordinator, entry, desc)

        attrs = sensor.extra_state_attributes
        assert attrs is not None
        assert "incidents" in attrs
        assert len(attrs["incidents"]) == 3

    def test_sensor_extra_state_attributes_bushfires(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test bushfires sensor returns only bushfire incidents in attributes."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE,
                CONF_ZONE_NAME: "Home",
                CONF_LATITUDE: -33.8688,
                CONF_LONGITUDE: 151.2093,
            },
            unique_id="abc_emergency_zone_home",
        )
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "bushfires")

        sensor = ABCEmergencySensor(mock_coordinator, entry, desc)

        attrs = sensor.extra_state_attributes
        assert attrs is not None
        assert "incidents" in attrs
        assert len(attrs["incidents"]) == 1
        assert attrs["incidents"][0]["event_type"] == "Bushfire"

    def test_sensor_extra_state_attributes_floods(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test floods sensor returns only flood incidents in attributes."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE,
                CONF_ZONE_NAME: "Home",
                CONF_LATITUDE: -33.8688,
                CONF_LONGITUDE: 151.2093,
            },
            unique_id="abc_emergency_zone_home",
        )
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "floods")

        sensor = ABCEmergencySensor(mock_coordinator, entry, desc)

        attrs = sensor.extra_state_attributes
        assert attrs is not None
        assert "incidents" in attrs
        assert len(attrs["incidents"]) == 1
        assert attrs["incidents"][0]["event_type"] == "Flood"

    def test_sensor_extra_state_attributes_storms(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test storms sensor returns only storm incidents in attributes."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE,
                CONF_ZONE_NAME: "Home",
                CONF_LATITUDE: -33.8688,
                CONF_LONGITUDE: 151.2093,
            },
            unique_id="abc_emergency_zone_home",
        )
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "storms")

        sensor = ABCEmergencySensor(mock_coordinator, entry, desc)

        attrs = sensor.extra_state_attributes
        assert attrs is not None
        assert "incidents" in attrs
        assert len(attrs["incidents"]) == 1
        assert attrs["incidents"][0]["event_type"] == "Storm"


class TestAsyncSetupEntry:
    """Test async_setup_entry for sensor platform."""

    async def test_setup_creates_sensors_for_state_instance(
        self,
        hass: HomeAssistant,
        mock_coordinator_state: MagicMock,
    ) -> None:
        """Test that setup creates common sensors for state instance."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_STATE,
                CONF_STATE: "nsw",
            },
            unique_id="abc_emergency_state_nsw",
        )
        entry.add_to_hass(hass)

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = mock_coordinator_state

        entities_added: list = []

        def mock_add_entities(entities: list) -> None:
            entities_added.extend(entities)

        await async_setup_entry(hass, entry, mock_add_entities)

        # State instances only get common sensors (5)
        assert len(entities_added) == 5
        assert all(isinstance(e, ABCEmergencySensor) for e in entities_added)

    async def test_setup_creates_all_sensors_for_zone_instance(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test that setup creates all sensors for zone instance."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE,
                CONF_ZONE_NAME: "Home",
                CONF_LATITUDE: -33.8688,
                CONF_LONGITUDE: 151.2093,
            },
            unique_id="abc_emergency_zone_home",
        )
        entry.add_to_hass(hass)

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = mock_coordinator

        entities_added: list = []

        def mock_add_entities(entities: list) -> None:
            entities_added.extend(entities)

        await async_setup_entry(hass, entry, mock_add_entities)

        # Zone instances get common (5) + location (2) = 7 sensors
        assert len(entities_added) == 7
        assert all(isinstance(e, ABCEmergencySensor) for e in entities_added)
