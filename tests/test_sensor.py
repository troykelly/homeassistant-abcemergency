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
        # 5 original + 3 alert-level sensors = 8 total
        assert len(COMMON_SENSOR_DESCRIPTIONS) == 8

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
        assert result["incidents"] == []
        # Zone/person modes have containment summary fields
        assert "containing_count" in result
        assert "inside_polygon" in result
        assert "highest_containing_level" in result

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
        assert result["incidents"] == []
        # Zone/person modes have containing_count field
        assert "containing_count" in result
        assert result["containing_count"] == 0

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
        assert result["incidents"] == []
        # Zone/person modes have containing_count field
        assert "containing_count" in result

    def test_state_mode_containing_count_null(
        self,
        mock_coordinator_data_state: CoordinatorData,
    ) -> None:
        """Test state mode has null containing_count for type filter."""
        result = _get_incidents_list_by_type_attrs(mock_coordinator_data_state, "Bushfire")
        assert result["containing_count"] is None


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

        # State instances only get common sensors (8 including 3 alert-level sensors)
        assert len(entities_added) == 8
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

        # Zone instances get common (8) + location (2) = 10 sensors
        assert len(entities_added) == 10
        assert all(isinstance(e, ABCEmergencySensor) for e in entities_added)


class TestContainmentAttributes:
    """Test containment attributes in sensor entities."""

    def test_incident_to_dict_includes_contains_point(
        self,
        mock_coordinator_data_with_containment: CoordinatorData,
    ) -> None:
        """Test incident dict includes contains_point field."""
        result = _get_incidents_list_attrs(mock_coordinator_data_with_containment)
        assert "incidents" in result
        for incident in result["incidents"]:
            assert "contains_point" in incident

    def test_incident_to_dict_includes_has_polygon(
        self,
        mock_coordinator_data_with_containment: CoordinatorData,
    ) -> None:
        """Test incident dict includes has_polygon field."""
        result = _get_incidents_list_attrs(mock_coordinator_data_with_containment)
        assert "incidents" in result
        for incident in result["incidents"]:
            assert "has_polygon" in incident

    def test_contains_point_true_for_containing_incident(
        self,
        mock_coordinator_data_with_containment: CoordinatorData,
    ) -> None:
        """Test contains_point is True for incidents containing the point."""
        result = _get_incidents_list_attrs(mock_coordinator_data_with_containment)
        containing_incident = next(i for i in result["incidents"] if i["id"] == "AUREMER-CONTAIN-1")
        assert containing_incident["contains_point"] is True

    def test_contains_point_false_for_non_containing_incident(
        self,
        mock_coordinator_data_with_containment: CoordinatorData,
    ) -> None:
        """Test contains_point is False for incidents not containing the point."""
        result = _get_incidents_list_attrs(mock_coordinator_data_with_containment)
        nearby_incident = next(i for i in result["incidents"] if i["id"] == "AUREMER-NEARBY-1")
        assert nearby_incident["contains_point"] is False

    def test_has_polygon_true_for_polygon_incidents(
        self,
        mock_coordinator_data_with_containment: CoordinatorData,
    ) -> None:
        """Test has_polygon is True for incidents with polygon data."""
        result = _get_incidents_list_attrs(mock_coordinator_data_with_containment)
        polygon_incident = next(i for i in result["incidents"] if i["id"] == "AUREMER-CONTAIN-1")
        assert polygon_incident["has_polygon"] is True

    def test_has_polygon_false_for_point_only_incidents(
        self,
        mock_coordinator_data_with_containment: CoordinatorData,
    ) -> None:
        """Test has_polygon is False for point-only incidents."""
        result = _get_incidents_list_attrs(mock_coordinator_data_with_containment)
        point_incident = next(i for i in result["incidents"] if i["id"] == "AUREMER-POINT-1")
        assert point_incident["has_polygon"] is False

    def test_incidents_list_has_containing_count(
        self,
        mock_coordinator_data_with_containment: CoordinatorData,
    ) -> None:
        """Test incidents list has containing_count attribute."""
        result = _get_incidents_list_attrs(mock_coordinator_data_with_containment)
        assert "containing_count" in result
        assert result["containing_count"] == 1

    def test_incidents_list_has_inside_polygon(
        self,
        mock_coordinator_data_with_containment: CoordinatorData,
    ) -> None:
        """Test incidents list has inside_polygon attribute."""
        result = _get_incidents_list_attrs(mock_coordinator_data_with_containment)
        assert "inside_polygon" in result
        assert result["inside_polygon"] is True

    def test_incidents_list_has_highest_containing_level(
        self,
        mock_coordinator_data_with_containment: CoordinatorData,
    ) -> None:
        """Test incidents list has highest_containing_level attribute."""
        result = _get_incidents_list_attrs(mock_coordinator_data_with_containment)
        assert "highest_containing_level" in result
        assert result["highest_containing_level"] == AlertLevel.EMERGENCY

    def test_state_mode_containment_attributes_null(
        self,
        mock_coordinator_data_state: CoordinatorData,
    ) -> None:
        """Test state mode has null containment summary attributes."""
        result = _get_incidents_list_attrs(mock_coordinator_data_state)
        # State mode should have None for containment summaries
        assert result.get("containing_count") is None
        assert result.get("inside_polygon") is None
        assert result.get("highest_containing_level") is None

    def test_nearest_incident_includes_contains_point(
        self,
        mock_coordinator_data_with_containment: CoordinatorData,
    ) -> None:
        """Test nearest incident attributes includes contains_point."""
        result = _get_nearest_incident_attrs(mock_coordinator_data_with_containment)
        assert "contains_point" in result

    def test_nearest_incident_includes_has_polygon(
        self,
        mock_coordinator_data_with_containment: CoordinatorData,
    ) -> None:
        """Test nearest incident attributes includes has_polygon."""
        result = _get_nearest_incident_attrs(mock_coordinator_data_with_containment)
        assert "has_polygon" in result

    def test_type_filter_includes_containment_info(
        self,
        mock_coordinator_data_with_containment: CoordinatorData,
    ) -> None:
        """Test type-filtered incidents list includes containment info."""
        result = _get_incidents_list_by_type_attrs(
            mock_coordinator_data_with_containment, "Bushfire"
        )
        assert len(result["incidents"]) == 1
        bushfire = result["incidents"][0]
        assert "contains_point" in bushfire
        assert "has_polygon" in bushfire
        assert bushfire["contains_point"] is True
        assert bushfire["has_polygon"] is True

    def test_type_filter_includes_containing_count(
        self,
        mock_coordinator_data_with_containment: CoordinatorData,
    ) -> None:
        """Test type-filtered incidents list includes containing_count."""
        result = _get_incidents_list_by_type_attrs(
            mock_coordinator_data_with_containment, "Bushfire"
        )
        assert "containing_count" in result
        assert result["containing_count"] == 1  # One containing bushfire


class TestEntityIdsAttribute:
    """Test entity_ids attribute for map card integration (Issue #101)."""

    def test_incidents_total_has_entity_ids_attribute(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test incidents_total sensor includes entity_ids in attributes."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE,
                CONF_ZONE_NAME: "Home",
                CONF_LATITUDE: -33.8688,
                CONF_LONGITUDE: 151.2093,
            },
            unique_id="abc_emergency_zone_home",
            title="ABC Emergency (Home)",
        )
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "incidents_total")

        sensor = ABCEmergencySensor(mock_coordinator, entry, desc)

        attrs = sensor.extra_state_attributes
        assert attrs is not None
        assert "entity_ids" in attrs
        assert isinstance(attrs["entity_ids"], list)
        assert len(attrs["entity_ids"]) == 3  # 3 incidents in mock data

    def test_entity_ids_format_uses_slugify(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test entity_ids are correctly formatted using slugify."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE,
                CONF_ZONE_NAME: "Home",
                CONF_LATITUDE: -33.8688,
                CONF_LONGITUDE: 151.2093,
            },
            unique_id="abc_emergency_zone_home",
            title="ABC Emergency (Home)",
        )
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "incidents_total")

        sensor = ABCEmergencySensor(mock_coordinator, entry, desc)

        attrs = sensor.extra_state_attributes
        assert attrs is not None
        entity_ids = attrs["entity_ids"]

        # Entity IDs should be slugified: geo_location.abc_emergency_home_auremer_12345
        # Instance source "ABC Emergency (Home)" + incident ID "AUREMER-12345"
        # Slugified: abc_emergency_home_auremer_12345
        assert "geo_location.abc_emergency_home_auremer_12345" in entity_ids

    def test_entity_ids_match_incident_count(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test entity_ids count matches incidents count."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE,
                CONF_ZONE_NAME: "Home",
                CONF_LATITUDE: -33.8688,
                CONF_LONGITUDE: 151.2093,
            },
            unique_id="abc_emergency_zone_home",
            title="ABC Emergency (Home)",
        )
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "incidents_total")

        sensor = ABCEmergencySensor(mock_coordinator, entry, desc)

        attrs = sensor.extra_state_attributes
        assert attrs is not None
        assert len(attrs["entity_ids"]) == len(attrs["incidents"])

    def test_bushfires_sensor_has_entity_ids(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test bushfires sensor includes entity_ids for matching incidents."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE,
                CONF_ZONE_NAME: "Home",
                CONF_LATITUDE: -33.8688,
                CONF_LONGITUDE: 151.2093,
            },
            unique_id="abc_emergency_zone_home",
            title="ABC Emergency (Home)",
        )
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "bushfires")

        sensor = ABCEmergencySensor(mock_coordinator, entry, desc)

        attrs = sensor.extra_state_attributes
        assert attrs is not None
        assert "entity_ids" in attrs
        assert len(attrs["entity_ids"]) == 1  # Only 1 bushfire in mock data
        assert "geo_location.abc_emergency_home_auremer_12345" in attrs["entity_ids"]

    def test_floods_sensor_has_entity_ids(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test floods sensor includes entity_ids for matching incidents."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE,
                CONF_ZONE_NAME: "Home",
                CONF_LATITUDE: -33.8688,
                CONF_LONGITUDE: 151.2093,
            },
            unique_id="abc_emergency_zone_home",
            title="ABC Emergency (Home)",
        )
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "floods")

        sensor = ABCEmergencySensor(mock_coordinator, entry, desc)

        attrs = sensor.extra_state_attributes
        assert attrs is not None
        assert "entity_ids" in attrs
        assert len(attrs["entity_ids"]) == 1  # Only 1 flood in mock data
        assert "geo_location.abc_emergency_home_auremer_12346" in attrs["entity_ids"]

    def test_storms_sensor_has_entity_ids(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test storms sensor includes entity_ids for matching incidents."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE,
                CONF_ZONE_NAME: "Home",
                CONF_LATITUDE: -33.8688,
                CONF_LONGITUDE: 151.2093,
            },
            unique_id="abc_emergency_zone_home",
            title="ABC Emergency (Home)",
        )
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "storms")

        sensor = ABCEmergencySensor(mock_coordinator, entry, desc)

        attrs = sensor.extra_state_attributes
        assert attrs is not None
        assert "entity_ids" in attrs
        assert len(attrs["entity_ids"]) == 1  # Only 1 storm in mock data
        assert "geo_location.abc_emergency_home_auremer_12347" in attrs["entity_ids"]

    def test_incidents_nearby_has_entity_ids(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test incidents_nearby sensor includes entity_ids."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE,
                CONF_ZONE_NAME: "Home",
                CONF_LATITUDE: -33.8688,
                CONF_LONGITUDE: 151.2093,
            },
            unique_id="abc_emergency_zone_home",
            title="ABC Emergency (Home)",
        )
        desc = next(d for d in LOCATION_SENSOR_DESCRIPTIONS if d.key == "incidents_nearby")

        sensor = ABCEmergencySensor(mock_coordinator, entry, desc)

        attrs = sensor.extra_state_attributes
        assert attrs is not None
        assert "entity_ids" in attrs
        assert len(attrs["entity_ids"]) == 3  # All incidents are nearby in mock data

    def test_entity_ids_empty_when_no_incidents(
        self,
        mock_coordinator_empty: MagicMock,
    ) -> None:
        """Test entity_ids is empty list when no incidents."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE,
                CONF_ZONE_NAME: "Home",
                CONF_LATITUDE: -33.8688,
                CONF_LONGITUDE: 151.2093,
            },
            unique_id="abc_emergency_zone_home",
            title="ABC Emergency (Home)",
        )
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "incidents_total")

        sensor = ABCEmergencySensor(mock_coordinator_empty, entry, desc)

        attrs = sensor.extra_state_attributes
        assert attrs is not None
        assert "entity_ids" in attrs
        assert attrs["entity_ids"] == []

    def test_entity_ids_uses_default_source_when_no_title(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test entity_ids uses 'ABC Emergency' when entry has no title."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE,
                CONF_ZONE_NAME: "Home",
                CONF_LATITUDE: -33.8688,
                CONF_LONGITUDE: 151.2093,
            },
            unique_id="abc_emergency_zone_home",
            title="",  # Empty title
        )
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "bushfires")

        sensor = ABCEmergencySensor(mock_coordinator, entry, desc)

        attrs = sensor.extra_state_attributes
        assert attrs is not None
        assert "entity_ids" in attrs
        # With empty title, uses "ABC Emergency" as source
        assert "geo_location.abc_emergency_auremer_12345" in attrs["entity_ids"]

    def test_sensor_stores_instance_source(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test sensor stores _instance_source from config entry title."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE,
                CONF_ZONE_NAME: "Home",
                CONF_LATITUDE: -33.8688,
                CONF_LONGITUDE: 151.2093,
            },
            unique_id="abc_emergency_zone_home",
            title="ABC Emergency (Home)",
        )
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "incidents_total")

        sensor = ABCEmergencySensor(mock_coordinator, entry, desc)

        assert hasattr(sensor, "_instance_source")
        assert sensor._instance_source == "ABC Emergency (Home)"


class TestAlertLevelSensors:
    """Test new alert-level sensors for map card integration (Issue #101)."""

    def test_emergency_warnings_sensor_exists(self) -> None:
        """Test emergency_warnings sensor description exists."""
        desc = next(
            (d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "emergency_warnings"),
            None,
        )
        assert desc is not None
        assert desc.translation_key == "emergency_warnings"

    def test_watch_and_acts_sensor_exists(self) -> None:
        """Test watch_and_acts sensor description exists."""
        desc = next(
            (d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "watch_and_acts"),
            None,
        )
        assert desc is not None
        assert desc.translation_key == "watch_and_acts"

    def test_advices_sensor_exists(self) -> None:
        """Test advices sensor description exists."""
        desc = next(
            (d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "advices"),
            None,
        )
        assert desc is not None
        assert desc.translation_key == "advices"

    def test_emergency_warnings_counts_extreme_level(
        self,
        mock_coordinator_data: CoordinatorData,
    ) -> None:
        """Test emergency_warnings counts only extreme (emergency) level incidents."""
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "emergency_warnings")
        # Mock data has 1 bushfire with extreme alert level
        assert desc.value_fn(mock_coordinator_data) == 1

    def test_watch_and_acts_counts_severe_level(
        self,
        mock_coordinator_data: CoordinatorData,
    ) -> None:
        """Test watch_and_acts counts only severe (watch and act) level incidents."""
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "watch_and_acts")
        # Mock data has 1 flood with severe alert level
        assert desc.value_fn(mock_coordinator_data) == 1

    def test_advices_counts_moderate_level(
        self,
        mock_coordinator_data: CoordinatorData,
    ) -> None:
        """Test advices counts only moderate (advice) level incidents."""
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "advices")
        # Mock data has 1 storm with moderate alert level
        assert desc.value_fn(mock_coordinator_data) == 1

    def test_emergency_warnings_zero_when_no_extreme(
        self,
        mock_coordinator_data_empty: CoordinatorData,
    ) -> None:
        """Test emergency_warnings returns 0 when no extreme alerts."""
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "emergency_warnings")
        assert desc.value_fn(mock_coordinator_data_empty) == 0

    def test_emergency_warnings_has_entity_ids(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test emergency_warnings sensor includes entity_ids."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE,
                CONF_ZONE_NAME: "Home",
                CONF_LATITUDE: -33.8688,
                CONF_LONGITUDE: 151.2093,
            },
            unique_id="abc_emergency_zone_home",
            title="ABC Emergency (Home)",
        )
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "emergency_warnings")

        sensor = ABCEmergencySensor(mock_coordinator, entry, desc)

        attrs = sensor.extra_state_attributes
        assert attrs is not None
        assert "entity_ids" in attrs
        assert len(attrs["entity_ids"]) == 1  # Only bushfire is extreme
        assert "geo_location.abc_emergency_home_auremer_12345" in attrs["entity_ids"]

    def test_watch_and_acts_has_entity_ids(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test watch_and_acts sensor includes entity_ids."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE,
                CONF_ZONE_NAME: "Home",
                CONF_LATITUDE: -33.8688,
                CONF_LONGITUDE: 151.2093,
            },
            unique_id="abc_emergency_zone_home",
            title="ABC Emergency (Home)",
        )
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "watch_and_acts")

        sensor = ABCEmergencySensor(mock_coordinator, entry, desc)

        attrs = sensor.extra_state_attributes
        assert attrs is not None
        assert "entity_ids" in attrs
        assert len(attrs["entity_ids"]) == 1  # Only flood is severe
        assert "geo_location.abc_emergency_home_auremer_12346" in attrs["entity_ids"]

    def test_advices_has_entity_ids(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test advices sensor includes entity_ids."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE,
                CONF_ZONE_NAME: "Home",
                CONF_LATITUDE: -33.8688,
                CONF_LONGITUDE: 151.2093,
            },
            unique_id="abc_emergency_zone_home",
            title="ABC Emergency (Home)",
        )
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "advices")

        sensor = ABCEmergencySensor(mock_coordinator, entry, desc)

        attrs = sensor.extra_state_attributes
        assert attrs is not None
        assert "entity_ids" in attrs
        assert len(attrs["entity_ids"]) == 1  # Only storm is moderate
        assert "geo_location.abc_emergency_home_auremer_12347" in attrs["entity_ids"]

    def test_alert_level_sensors_have_incidents_list(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test alert-level sensors include incidents list in attributes."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE,
                CONF_ZONE_NAME: "Home",
                CONF_LATITUDE: -33.8688,
                CONF_LONGITUDE: 151.2093,
            },
            unique_id="abc_emergency_zone_home",
            title="ABC Emergency (Home)",
        )
        desc = next(d for d in COMMON_SENSOR_DESCRIPTIONS if d.key == "emergency_warnings")

        sensor = ABCEmergencySensor(mock_coordinator, entry, desc)

        attrs = sensor.extra_state_attributes
        assert attrs is not None
        assert "incidents" in attrs
        assert len(attrs["incidents"]) == 1
        assert attrs["incidents"][0]["alert_level"] == AlertLevel.EMERGENCY
