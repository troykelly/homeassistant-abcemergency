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
