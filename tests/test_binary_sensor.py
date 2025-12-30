"""Tests for ABC Emergency binary sensor platform."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.abcemergency.binary_sensor import (
    BINARY_SENSOR_DESCRIPTIONS,
    ABCEmergencyBinarySensor,
    _get_emergency_attrs,
    async_setup_entry,
)
from custom_components.abcemergency.const import (
    CONF_INSTANCE_TYPE,
    CONF_STATE,
    CONF_ZONE_NAME,
    DOMAIN,
    INSTANCE_TYPE_STATE,
    INSTANCE_TYPE_ZONE,
    AlertLevel,
)
from custom_components.abcemergency.models import (
    CoordinatorData,
    EmergencyIncident,
)

if TYPE_CHECKING:
    pass


class TestBinarySensorDescriptions:
    """Test binary sensor entity descriptions."""

    def test_binary_sensor_descriptions_exist(self) -> None:
        """Test that binary sensor descriptions are defined."""
        assert len(BINARY_SENSOR_DESCRIPTIONS) == 4

    def test_binary_sensor_descriptions_have_required_fields(self) -> None:
        """Test that binary sensor descriptions have required fields."""
        for desc in BINARY_SENSOR_DESCRIPTIONS:
            assert desc.key
            assert desc.translation_key
            assert desc.is_on_fn is not None
            assert desc.device_class == BinarySensorDeviceClass.SAFETY

    def test_active_alert_description(self) -> None:
        """Test active_alert binary sensor description."""
        desc = next(d for d in BINARY_SENSOR_DESCRIPTIONS if d.key == "active_alert")
        assert desc.translation_key == "active_alert"

    def test_emergency_warning_description(self) -> None:
        """Test emergency_warning binary sensor description."""
        desc = next(d for d in BINARY_SENSOR_DESCRIPTIONS if d.key == "emergency_warning")
        assert desc.translation_key == "emergency_warning"
        assert desc.attr_fn is not None

    def test_watch_and_act_description(self) -> None:
        """Test watch_and_act binary sensor description."""
        desc = next(d for d in BINARY_SENSOR_DESCRIPTIONS if d.key == "watch_and_act")
        assert desc.translation_key == "watch_and_act"
        assert desc.attr_fn is not None

    def test_advice_description(self) -> None:
        """Test advice binary sensor description."""
        desc = next(d for d in BINARY_SENSOR_DESCRIPTIONS if d.key == "advice")
        assert desc.translation_key == "advice"


class TestGetEmergencyAttrs:
    """Test the _get_emergency_attrs helper function."""

    def test_returns_empty_when_no_matching(
        self,
        mock_coordinator_data_empty: CoordinatorData,
    ) -> None:
        """Test returns empty dict when no matching incidents."""
        result = _get_emergency_attrs(mock_coordinator_data_empty, AlertLevel.EMERGENCY)
        assert result == {}

    def test_returns_attrs_for_single_level(
        self,
        mock_coordinator_data: CoordinatorData,
    ) -> None:
        """Test returns attributes for single alert level."""
        result = _get_emergency_attrs(mock_coordinator_data, AlertLevel.EMERGENCY)
        assert result["count"] == 1
        assert result["nearest_headline"] == "Bushfire at Test Location"
        assert result["nearest_distance_km"] == 10.5
        assert result["nearest_direction"] == "S"

    def test_returns_attrs_for_multiple_levels(
        self,
        mock_coordinator_data: CoordinatorData,
    ) -> None:
        """Test returns attributes for multiple alert levels."""
        result = _get_emergency_attrs(
            mock_coordinator_data,
            (AlertLevel.EMERGENCY, AlertLevel.WATCH_AND_ACT),
        )
        assert result["count"] == 2
        # Should return nearest (bushfire at 10.5 km)
        assert result["nearest_headline"] == "Bushfire at Test Location"
        assert result["nearest_distance_km"] == 10.5

    def test_handles_string_level(
        self,
        mock_coordinator_data: CoordinatorData,
    ) -> None:
        """Test handles single string level (converted to tuple)."""
        result = _get_emergency_attrs(mock_coordinator_data, AlertLevel.WATCH_AND_ACT)
        assert result["count"] == 1
        assert result["nearest_headline"] == "Flood Warning at River Area"

    def test_returns_state_format_for_state_instance(
        self,
        mock_coordinator_data_state: CoordinatorData,
    ) -> None:
        """Test returns state instance format (no distance info)."""
        result = _get_emergency_attrs(mock_coordinator_data_state, AlertLevel.EMERGENCY)
        assert result["count"] == 1
        assert "headline" in result
        # State format uses "headline" not "nearest_headline"
        assert "nearest_distance_km" not in result


class TestBinarySensorIsOnFunctions:
    """Test is_on functions in binary sensor descriptions."""

    def test_active_alert_is_on_when_nearby(
        self,
        mock_coordinator_data: CoordinatorData,
    ) -> None:
        """Test active_alert is on when nearby_count > 0."""
        desc = next(d for d in BINARY_SENSOR_DESCRIPTIONS if d.key == "active_alert")
        assert desc.is_on_fn(mock_coordinator_data) is True

    def test_active_alert_is_off_when_no_nearby(
        self,
        mock_coordinator_data_empty: CoordinatorData,
    ) -> None:
        """Test active_alert is off when nearby_count == 0."""
        desc = next(d for d in BINARY_SENSOR_DESCRIPTIONS if d.key == "active_alert")
        assert desc.is_on_fn(mock_coordinator_data_empty) is False

    def test_active_alert_is_on_for_state_with_incidents(
        self,
        mock_coordinator_data_state: CoordinatorData,
    ) -> None:
        """Test active_alert is on for state instance with incidents."""
        desc = next(d for d in BINARY_SENSOR_DESCRIPTIONS if d.key == "active_alert")
        assert desc.is_on_fn(mock_coordinator_data_state) is True

    def test_emergency_warning_is_on_when_extreme(
        self,
        mock_coordinator_data: CoordinatorData,
    ) -> None:
        """Test emergency_warning is on when alert level is extreme."""
        desc = next(d for d in BINARY_SENSOR_DESCRIPTIONS if d.key == "emergency_warning")
        assert desc.is_on_fn(mock_coordinator_data) is True

    def test_emergency_warning_is_off_when_not_extreme(
        self,
        mock_coordinator_data_empty: CoordinatorData,
    ) -> None:
        """Test emergency_warning is off when no extreme alert."""
        desc = next(d for d in BINARY_SENSOR_DESCRIPTIONS if d.key == "emergency_warning")
        assert desc.is_on_fn(mock_coordinator_data_empty) is False

    def test_watch_and_act_is_on_when_severe_or_extreme(
        self,
        mock_coordinator_data: CoordinatorData,
    ) -> None:
        """Test watch_and_act is on when alert level is severe or extreme."""
        desc = next(d for d in BINARY_SENSOR_DESCRIPTIONS if d.key == "watch_and_act")
        assert desc.is_on_fn(mock_coordinator_data) is True

    def test_watch_and_act_is_on_for_severe_only(
        self,
        mock_incident_flood: EmergencyIncident,
    ) -> None:
        """Test watch_and_act is on for severe level only."""
        desc = next(d for d in BINARY_SENSOR_DESCRIPTIONS if d.key == "watch_and_act")
        data = CoordinatorData(
            incidents=[mock_incident_flood],
            total_count=1,
            nearby_count=1,
            highest_alert_level=AlertLevel.WATCH_AND_ACT,
            instance_type=INSTANCE_TYPE_ZONE,
        )
        assert desc.is_on_fn(data) is True

    def test_advice_is_on_when_any_alert(
        self,
        mock_coordinator_data: CoordinatorData,
    ) -> None:
        """Test advice is on when any alert level is present."""
        desc = next(d for d in BINARY_SENSOR_DESCRIPTIONS if d.key == "advice")
        assert desc.is_on_fn(mock_coordinator_data) is True

    def test_advice_is_on_for_moderate_only(
        self,
        mock_incident_storm: EmergencyIncident,
    ) -> None:
        """Test advice is on for moderate level only."""
        desc = next(d for d in BINARY_SENSOR_DESCRIPTIONS if d.key == "advice")
        data = CoordinatorData(
            incidents=[mock_incident_storm],
            total_count=1,
            nearby_count=1,
            highest_alert_level=AlertLevel.ADVICE,
            instance_type=INSTANCE_TYPE_ZONE,
        )
        assert desc.is_on_fn(data) is True

    def test_advice_is_off_when_no_alerts(
        self,
        mock_coordinator_data_empty: CoordinatorData,
    ) -> None:
        """Test advice is off when no alerts."""
        desc = next(d for d in BINARY_SENSOR_DESCRIPTIONS if d.key == "advice")
        assert desc.is_on_fn(mock_coordinator_data_empty) is False


class TestABCEmergencyBinarySensor:
    """Test ABCEmergencyBinarySensor entity."""

    def test_sensor_unique_id(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test binary sensor unique ID is correctly generated."""
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
        desc = BINARY_SENSOR_DESCRIPTIONS[0]

        sensor = ABCEmergencyBinarySensor(mock_coordinator, entry, desc)

        assert sensor.unique_id == f"{entry.entry_id}_{desc.key}"

    def test_sensor_is_on(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test binary sensor returns correct is_on value."""
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
        desc = next(d for d in BINARY_SENSOR_DESCRIPTIONS if d.key == "active_alert")

        sensor = ABCEmergencyBinarySensor(mock_coordinator, entry, desc)

        assert sensor.is_on is True

    def test_sensor_extra_state_attributes_with_fn(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test binary sensor returns extra state attributes when fn is defined."""
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
        desc = next(d for d in BINARY_SENSOR_DESCRIPTIONS if d.key == "emergency_warning")

        sensor = ABCEmergencyBinarySensor(mock_coordinator, entry, desc)

        attrs = sensor.extra_state_attributes
        assert attrs is not None
        assert attrs["count"] == 1
        assert attrs["nearest_headline"] == "Bushfire at Test Location"

    def test_sensor_extra_state_attributes_without_fn(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test binary sensor returns None for attributes when fn is not defined."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_STATE,
                CONF_STATE: "nsw",
            },
            unique_id="abc_emergency_state_nsw",
        )
        desc = next(d for d in BINARY_SENSOR_DESCRIPTIONS if d.key == "active_alert")

        sensor = ABCEmergencyBinarySensor(mock_coordinator, entry, desc)

        assert sensor.extra_state_attributes is None


class TestAsyncSetupEntry:
    """Test async_setup_entry for binary sensor platform."""

    async def test_setup_creates_all_binary_sensors(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test that setup creates all binary sensor entities."""
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
        hass.data[DOMAIN][entry.entry_id] = mock_coordinator

        entities_added: list = []

        def mock_add_entities(entities: list) -> None:
            entities_added.extend(entities)

        await async_setup_entry(hass, entry, mock_add_entities)

        assert len(entities_added) == 4
        assert all(isinstance(e, ABCEmergencyBinarySensor) for e in entities_added)

    async def test_setup_creates_containment_sensors_for_zone_instance(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test that setup creates containment sensors for zone instance."""
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

        # Update coordinator instance type for zone mode
        mock_coordinator.instance_type = INSTANCE_TYPE_ZONE

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = mock_coordinator

        entities_added: list = []

        def mock_add_entities(entities: list) -> None:
            entities_added.extend(entities)

        await async_setup_entry(hass, entry, mock_add_entities)

        # Should have 4 base sensors + 4 containment sensors = 8 total
        assert len(entities_added) == 8

        # Verify containment sensor keys are present
        keys = [e.entity_description.key for e in entities_added]
        assert "inside_polygon" in keys
        assert "inside_emergency_warning" in keys
        assert "inside_watch_and_act" in keys
        assert "inside_advice" in keys

    async def test_setup_does_not_create_containment_sensors_for_state_instance(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test that setup does not create containment sensors for state instance."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_STATE,
                CONF_STATE: "nsw",
            },
            unique_id="abc_emergency_state_nsw",
        )
        entry.add_to_hass(hass)

        # Ensure coordinator is state mode
        mock_coordinator.instance_type = INSTANCE_TYPE_STATE

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = mock_coordinator

        entities_added: list = []

        def mock_add_entities(entities: list) -> None:
            entities_added.extend(entities)

        await async_setup_entry(hass, entry, mock_add_entities)

        # Should have only 4 base sensors (no containment sensors)
        assert len(entities_added) == 4

        # Verify NO containment sensor keys
        keys = [e.entity_description.key for e in entities_added]
        assert "inside_polygon" not in keys


class TestContainmentBinarySensorDescriptions:
    """Test containment binary sensor descriptions."""

    def test_containment_descriptions_exist(self) -> None:
        """Test that containment sensor descriptions are defined."""
        from custom_components.abcemergency.binary_sensor import (
            CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS,
        )

        assert len(CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS) == 4

    def test_containment_descriptions_have_required_fields(self) -> None:
        """Test that containment sensor descriptions have required fields."""
        from custom_components.abcemergency.binary_sensor import (
            CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS,
        )

        for desc in CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS:
            assert desc.key
            assert desc.translation_key
            assert desc.is_on_fn is not None
            assert desc.device_class == BinarySensorDeviceClass.SAFETY
            assert desc.attr_fn is not None  # Containment sensors all have attributes

    def test_inside_polygon_description(self) -> None:
        """Test inside_polygon binary sensor description."""
        from custom_components.abcemergency.binary_sensor import (
            CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS,
        )

        desc = next(d for d in CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS if d.key == "inside_polygon")
        assert desc.translation_key == "inside_polygon"

    def test_inside_emergency_warning_description(self) -> None:
        """Test inside_emergency_warning binary sensor description."""
        from custom_components.abcemergency.binary_sensor import (
            CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS,
        )

        desc = next(
            d for d in CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS if d.key == "inside_emergency_warning"
        )
        assert desc.translation_key == "inside_emergency_warning"

    def test_inside_watch_and_act_description(self) -> None:
        """Test inside_watch_and_act binary sensor description."""
        from custom_components.abcemergency.binary_sensor import (
            CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS,
        )

        desc = next(
            d for d in CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS if d.key == "inside_watch_and_act"
        )
        assert desc.translation_key == "inside_watch_and_act"

    def test_inside_advice_description(self) -> None:
        """Test inside_advice binary sensor description."""
        from custom_components.abcemergency.binary_sensor import (
            CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS,
        )

        desc = next(d for d in CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS if d.key == "inside_advice")
        assert desc.translation_key == "inside_advice"


class TestContainmentBinarySensorIsOnFunctions:
    """Test is_on functions for containment binary sensors."""

    def test_inside_polygon_is_on_when_contained(self) -> None:
        """Test inside_polygon is on when inside any polygon."""
        from custom_components.abcemergency.binary_sensor import (
            CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS,
        )

        data = CoordinatorData(
            incidents=[],
            total_count=0,
            nearby_count=0,
            inside_polygon=True,
            containing_incidents=[],
            instance_type=INSTANCE_TYPE_ZONE,
        )
        desc = next(d for d in CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS if d.key == "inside_polygon")
        assert desc.is_on_fn(data) is True

    def test_inside_polygon_is_off_when_not_contained(self) -> None:
        """Test inside_polygon is off when not inside any polygon."""
        from custom_components.abcemergency.binary_sensor import (
            CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS,
        )

        data = CoordinatorData(
            incidents=[],
            total_count=0,
            nearby_count=0,
            inside_polygon=False,
            containing_incidents=[],
            instance_type=INSTANCE_TYPE_ZONE,
        )
        desc = next(d for d in CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS if d.key == "inside_polygon")
        assert desc.is_on_fn(data) is False

    def test_inside_emergency_warning_is_on_when_inside_extreme(
        self,
        mock_incident_bushfire: EmergencyIncident,
    ) -> None:
        """Test inside_emergency_warning is on when inside extreme alert polygon."""
        from custom_components.abcemergency.binary_sensor import (
            CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS,
        )

        data = CoordinatorData(
            incidents=[],
            total_count=0,
            nearby_count=0,
            inside_polygon=True,
            inside_emergency_warning=True,
            containing_incidents=[mock_incident_bushfire],
            instance_type=INSTANCE_TYPE_ZONE,
        )
        desc = next(
            d for d in CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS if d.key == "inside_emergency_warning"
        )
        assert desc.is_on_fn(data) is True

    def test_inside_emergency_warning_is_off_when_only_severe(
        self,
        mock_incident_flood: EmergencyIncident,
    ) -> None:
        """Test inside_emergency_warning is off when inside severe-only polygon."""
        from custom_components.abcemergency.binary_sensor import (
            CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS,
        )

        data = CoordinatorData(
            incidents=[],
            total_count=0,
            nearby_count=0,
            inside_polygon=True,
            inside_emergency_warning=False,
            inside_watch_and_act=True,
            containing_incidents=[mock_incident_flood],
            instance_type=INSTANCE_TYPE_ZONE,
        )
        desc = next(
            d for d in CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS if d.key == "inside_emergency_warning"
        )
        assert desc.is_on_fn(data) is False

    def test_inside_watch_and_act_is_on_when_inside_severe(
        self,
        mock_incident_flood: EmergencyIncident,
    ) -> None:
        """Test inside_watch_and_act is on when inside severe or extreme polygon."""
        from custom_components.abcemergency.binary_sensor import (
            CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS,
        )

        data = CoordinatorData(
            incidents=[],
            total_count=0,
            nearby_count=0,
            inside_polygon=True,
            inside_watch_and_act=True,
            containing_incidents=[mock_incident_flood],
            instance_type=INSTANCE_TYPE_ZONE,
        )
        desc = next(
            d for d in CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS if d.key == "inside_watch_and_act"
        )
        assert desc.is_on_fn(data) is True

    def test_inside_advice_is_on_when_inside_moderate(
        self,
        mock_incident_storm: EmergencyIncident,
    ) -> None:
        """Test inside_advice is on when inside moderate or higher polygon."""
        from custom_components.abcemergency.binary_sensor import (
            CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS,
        )

        data = CoordinatorData(
            incidents=[],
            total_count=0,
            nearby_count=0,
            inside_polygon=True,
            inside_advice=True,
            containing_incidents=[mock_incident_storm],
            instance_type=INSTANCE_TYPE_ZONE,
        )
        desc = next(d for d in CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS if d.key == "inside_advice")
        assert desc.is_on_fn(data) is True

    def test_inside_advice_is_off_when_not_contained(self) -> None:
        """Test inside_advice is off when not inside any polygon."""
        from custom_components.abcemergency.binary_sensor import (
            CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS,
        )

        data = CoordinatorData(
            incidents=[],
            total_count=0,
            nearby_count=0,
            inside_polygon=False,
            inside_advice=False,
            containing_incidents=[],
            instance_type=INSTANCE_TYPE_ZONE,
        )
        desc = next(d for d in CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS if d.key == "inside_advice")
        assert desc.is_on_fn(data) is False


class TestContainmentBinarySensorAttributes:
    """Test attribute functions for containment binary sensors."""

    def test_inside_polygon_attributes(
        self,
        mock_incident_bushfire: EmergencyIncident,
        mock_incident_flood: EmergencyIncident,
    ) -> None:
        """Test inside_polygon returns correct attributes."""
        from custom_components.abcemergency.binary_sensor import (
            CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS,
        )

        data = CoordinatorData(
            incidents=[],
            total_count=0,
            nearby_count=0,
            inside_polygon=True,
            highest_containing_alert_level=AlertLevel.EMERGENCY,
            containing_incidents=[mock_incident_bushfire, mock_incident_flood],
            instance_type=INSTANCE_TYPE_ZONE,
        )
        desc = next(d for d in CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS if d.key == "inside_polygon")
        attrs = desc.attr_fn(data)

        assert attrs["containing_count"] == 2
        assert attrs["highest_alert_level"] == AlertLevel.EMERGENCY
        assert len(attrs["incidents"]) == 2
        # Verify incident structure
        assert attrs["incidents"][0]["id"] == mock_incident_bushfire.id
        assert attrs["incidents"][0]["headline"] == mock_incident_bushfire.headline
        assert attrs["incidents"][0]["alert_level"] == mock_incident_bushfire.alert_level
        assert attrs["incidents"][0]["event_type"] == mock_incident_bushfire.event_type

    def test_inside_emergency_warning_attributes_filters_by_level(
        self,
        mock_incident_bushfire: EmergencyIncident,
        mock_incident_flood: EmergencyIncident,
    ) -> None:
        """Test inside_emergency_warning attributes only include extreme level."""
        from custom_components.abcemergency.binary_sensor import (
            CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS,
        )

        # Bushfire is extreme, flood is severe
        data = CoordinatorData(
            incidents=[],
            total_count=0,
            nearby_count=0,
            inside_polygon=True,
            inside_emergency_warning=True,
            containing_incidents=[mock_incident_bushfire, mock_incident_flood],
            instance_type=INSTANCE_TYPE_ZONE,
        )
        desc = next(
            d for d in CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS if d.key == "inside_emergency_warning"
        )
        attrs = desc.attr_fn(data)

        assert attrs["count"] == 1  # Only the extreme-level incident
        assert len(attrs["incidents"]) == 1
        assert attrs["incidents"][0]["id"] == mock_incident_bushfire.id

    def test_inside_watch_and_act_attributes_filters_severe_and_above(
        self,
        mock_incident_bushfire: EmergencyIncident,
        mock_incident_flood: EmergencyIncident,
        mock_incident_storm: EmergencyIncident,
    ) -> None:
        """Test inside_watch_and_act attributes include severe and extreme."""
        from custom_components.abcemergency.binary_sensor import (
            CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS,
        )

        # Bushfire is extreme, flood is severe, storm is moderate
        data = CoordinatorData(
            incidents=[],
            total_count=0,
            nearby_count=0,
            inside_polygon=True,
            inside_watch_and_act=True,
            containing_incidents=[
                mock_incident_bushfire,
                mock_incident_flood,
                mock_incident_storm,
            ],
            instance_type=INSTANCE_TYPE_ZONE,
        )
        desc = next(
            d for d in CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS if d.key == "inside_watch_and_act"
        )
        attrs = desc.attr_fn(data)

        assert attrs["count"] == 2  # Extreme + severe, not moderate
        assert len(attrs["incidents"]) == 2

    def test_inside_advice_attributes_filters_moderate_and_above(
        self,
        mock_incident_bushfire: EmergencyIncident,
        mock_incident_storm: EmergencyIncident,
    ) -> None:
        """Test inside_advice attributes include moderate, severe, and extreme."""
        from custom_components.abcemergency.binary_sensor import (
            CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS,
        )

        data = CoordinatorData(
            incidents=[],
            total_count=0,
            nearby_count=0,
            inside_polygon=True,
            inside_advice=True,
            containing_incidents=[mock_incident_bushfire, mock_incident_storm],
            instance_type=INSTANCE_TYPE_ZONE,
        )
        desc = next(d for d in CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS if d.key == "inside_advice")
        attrs = desc.attr_fn(data)

        assert attrs["count"] == 2  # Both extreme and moderate
        assert len(attrs["incidents"]) == 2


class TestContainingEntityIdsAttribute:
    """Test containing_entity_ids attribute for map card integration (Issue #101)."""

    def test_inside_polygon_has_containing_entity_ids(
        self,
        mock_coordinator_data_with_containment: CoordinatorData,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test inside_polygon sensor includes containing_entity_ids."""
        from custom_components.abcemergency.binary_sensor import (
            CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS,
        )

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

        # Use coordinator with containment data
        mock_coordinator.data = mock_coordinator_data_with_containment

        desc = next(d for d in CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS if d.key == "inside_polygon")

        sensor = ABCEmergencyBinarySensor(mock_coordinator, entry, desc)

        attrs = sensor.extra_state_attributes
        assert attrs is not None
        assert "containing_entity_ids" in attrs
        assert isinstance(attrs["containing_entity_ids"], list)

    def test_containing_entity_ids_format_uses_slugify(
        self,
        mock_incident_bushfire: EmergencyIncident,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test containing_entity_ids are correctly formatted using slugify."""
        from custom_components.abcemergency.binary_sensor import (
            CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS,
        )

        # Create containment data with known incident
        containment_data = CoordinatorData(
            incidents=[mock_incident_bushfire],
            total_count=1,
            nearby_count=1,
            inside_polygon=True,
            highest_containing_alert_level=AlertLevel.EMERGENCY,
            containing_incidents=[mock_incident_bushfire],
            instance_type=INSTANCE_TYPE_ZONE,
        )
        mock_coordinator.data = containment_data

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

        desc = next(d for d in CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS if d.key == "inside_polygon")

        sensor = ABCEmergencyBinarySensor(mock_coordinator, entry, desc)

        attrs = sensor.extra_state_attributes
        assert attrs is not None
        entity_ids = attrs["containing_entity_ids"]

        # Entity IDs should be slugified
        assert "geo_location.abc_emergency_home_auremer_12345" in entity_ids

    def test_containing_entity_ids_match_incidents_count(
        self,
        mock_incident_bushfire: EmergencyIncident,
        mock_incident_flood: EmergencyIncident,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test containing_entity_ids count matches incidents count."""
        from custom_components.abcemergency.binary_sensor import (
            CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS,
        )

        containment_data = CoordinatorData(
            incidents=[mock_incident_bushfire, mock_incident_flood],
            total_count=2,
            nearby_count=2,
            inside_polygon=True,
            highest_containing_alert_level=AlertLevel.EMERGENCY,
            containing_incidents=[mock_incident_bushfire, mock_incident_flood],
            instance_type=INSTANCE_TYPE_ZONE,
        )
        mock_coordinator.data = containment_data

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

        desc = next(d for d in CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS if d.key == "inside_polygon")

        sensor = ABCEmergencyBinarySensor(mock_coordinator, entry, desc)

        attrs = sensor.extra_state_attributes
        assert attrs is not None
        assert len(attrs["containing_entity_ids"]) == len(attrs["incidents"])

    def test_inside_emergency_warning_has_containing_entity_ids(
        self,
        mock_incident_bushfire: EmergencyIncident,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test inside_emergency_warning sensor includes containing_entity_ids."""
        from custom_components.abcemergency.binary_sensor import (
            CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS,
        )

        containment_data = CoordinatorData(
            incidents=[mock_incident_bushfire],
            total_count=1,
            nearby_count=1,
            inside_polygon=True,
            inside_emergency_warning=True,
            highest_containing_alert_level=AlertLevel.EMERGENCY,
            containing_incidents=[mock_incident_bushfire],
            instance_type=INSTANCE_TYPE_ZONE,
        )
        mock_coordinator.data = containment_data

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

        desc = next(
            d for d in CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS if d.key == "inside_emergency_warning"
        )

        sensor = ABCEmergencyBinarySensor(mock_coordinator, entry, desc)

        attrs = sensor.extra_state_attributes
        assert attrs is not None
        assert "containing_entity_ids" in attrs
        assert len(attrs["containing_entity_ids"]) == 1
        assert "geo_location.abc_emergency_home_auremer_12345" in attrs["containing_entity_ids"]

    def test_containing_entity_ids_empty_when_no_containment(
        self,
        mock_coordinator_empty: MagicMock,
    ) -> None:
        """Test containing_entity_ids is empty when no containment."""
        from custom_components.abcemergency.binary_sensor import (
            CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS,
        )

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

        desc = next(d for d in CONTAINMENT_BINARY_SENSOR_DESCRIPTIONS if d.key == "inside_polygon")

        sensor = ABCEmergencyBinarySensor(mock_coordinator_empty, entry, desc)

        attrs = sensor.extra_state_attributes
        assert attrs is not None
        assert "containing_entity_ids" in attrs
        assert attrs["containing_entity_ids"] == []

    def test_binary_sensor_stores_instance_source(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test binary sensor stores _instance_source from config entry title."""
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
        desc = BINARY_SENSOR_DESCRIPTIONS[0]

        sensor = ABCEmergencyBinarySensor(mock_coordinator, entry, desc)

        assert hasattr(sensor, "_instance_source")
        assert sensor._instance_source == "ABC Emergency (Home)"
