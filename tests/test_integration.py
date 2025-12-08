"""Integration tests for ABC Emergency containment detection.

These tests verify the complete flow from API response through coordinator
to entity state and event firing, testing real-world scenarios end-to-end.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant, callback
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.abcemergency.const import (
    CONF_INSTANCE_TYPE,
    CONF_PERSON_ENTITY_ID,
    CONF_PERSON_NAME,
    CONF_RADIUS_BUSHFIRE,
    CONF_RADIUS_EARTHQUAKE,
    CONF_RADIUS_FIRE,
    CONF_RADIUS_FLOOD,
    CONF_RADIUS_HEAT,
    CONF_RADIUS_OTHER,
    CONF_RADIUS_STORM,
    CONF_STATE,
    CONF_ZONE_NAME,
    DEFAULT_RADIUS_BUSHFIRE,
    DEFAULT_RADIUS_EARTHQUAKE,
    DEFAULT_RADIUS_FIRE,
    DEFAULT_RADIUS_FLOOD,
    DEFAULT_RADIUS_HEAT,
    DEFAULT_RADIUS_OTHER,
    DEFAULT_RADIUS_STORM,
    DOMAIN,
    INSTANCE_TYPE_PERSON,
    INSTANCE_TYPE_STATE,
    INSTANCE_TYPE_ZONE,
)


@pytest.fixture
def zone_config_entry() -> MockConfigEntry:
    """Create zone mode config entry for Sydney location."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE,
            CONF_ZONE_NAME: "Home Zone",
            CONF_LATITUDE: -33.8688,
            CONF_LONGITUDE: 151.2093,
            CONF_RADIUS_BUSHFIRE: DEFAULT_RADIUS_BUSHFIRE,
            CONF_RADIUS_EARTHQUAKE: DEFAULT_RADIUS_EARTHQUAKE,
            CONF_RADIUS_STORM: DEFAULT_RADIUS_STORM,
            CONF_RADIUS_FLOOD: DEFAULT_RADIUS_FLOOD,
            CONF_RADIUS_FIRE: DEFAULT_RADIUS_FIRE,
            CONF_RADIUS_HEAT: DEFAULT_RADIUS_HEAT,
            CONF_RADIUS_OTHER: DEFAULT_RADIUS_OTHER,
        },
        unique_id="abc_emergency_zone_home",
        entry_id="integration_test_zone",
        version=3,
    )


@pytest.fixture
def person_config_entry() -> MockConfigEntry:
    """Create person mode config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_INSTANCE_TYPE: INSTANCE_TYPE_PERSON,
            CONF_PERSON_ENTITY_ID: "person.test_user",
            CONF_PERSON_NAME: "Test User",
            CONF_RADIUS_BUSHFIRE: DEFAULT_RADIUS_BUSHFIRE,
            CONF_RADIUS_EARTHQUAKE: DEFAULT_RADIUS_EARTHQUAKE,
            CONF_RADIUS_STORM: DEFAULT_RADIUS_STORM,
            CONF_RADIUS_FLOOD: DEFAULT_RADIUS_FLOOD,
            CONF_RADIUS_FIRE: DEFAULT_RADIUS_FIRE,
            CONF_RADIUS_HEAT: DEFAULT_RADIUS_HEAT,
            CONF_RADIUS_OTHER: DEFAULT_RADIUS_OTHER,
        },
        unique_id="abc_emergency_person_test_user",
        entry_id="integration_test_person",
        version=3,
    )


@pytest.fixture
def state_config_entry() -> MockConfigEntry:
    """Create state mode config entry for NSW."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_INSTANCE_TYPE: INSTANCE_TYPE_STATE,
            CONF_STATE: "nsw",
        },
        unique_id="abc_emergency_state_nsw",
        entry_id="integration_test_state",
        version=3,
    )


@pytest.fixture
def api_response_polygon_containing_sydney() -> dict[str, Any]:
    """API response with polygon that contains Sydney location."""
    return {
        "emergencies": [
            {
                "id": "AUREMER-CONTAIN-SYDNEY",
                "headline": "Test Bushfire Near Sydney",
                "to": "/emergency/warning/AUREMER-CONTAIN-SYDNEY",
                "alertLevelInfoPrepared": {
                    "text": "Emergency",
                    "level": "extreme",
                    "style": "extreme",
                },
                "emergencyTimestampPrepared": {
                    "date": datetime.now(UTC).isoformat(),
                    "formattedTime": "12:00:00 pm AEDT",
                    "prefix": "Effective from",
                    "updatedTime": datetime.now(UTC).isoformat(),
                },
                "eventLabelPrepared": {
                    "icon": "fire",
                    "labelText": "Bushfire",
                },
                "cardBody": {
                    "type": "Bush Fire",
                    "size": "1000 ha",
                    "status": "Out of control",
                    "source": "NSW Rural Fire Service",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [150.0, -34.5],
                            [152.5, -34.5],
                            [152.5, -33.0],
                            [150.0, -33.0],
                            [150.0, -34.5],
                        ]
                    ],
                },
            }
        ],
        "features": [],
        "mapBound": [[150.0, -34.5], [152.5, -33.0]],
        "stateName": "nsw",
        "incidentsNumber": 1,
        "stateCount": 1,
    }


@pytest.fixture
def api_response_polygon_not_containing_sydney() -> dict[str, Any]:
    """API response with polygon that does NOT contain Sydney."""
    return {
        "emergencies": [
            {
                "id": "AUREMER-FAR-MELBOURNE",
                "headline": "Test Fire Near Melbourne",
                "to": "/emergency/warning/AUREMER-FAR-MELBOURNE",
                "alertLevelInfoPrepared": {
                    "text": "Watch and Act",
                    "level": "severe",
                    "style": "severe",
                },
                "emergencyTimestampPrepared": {
                    "date": datetime.now(UTC).isoformat(),
                    "formattedTime": "12:00:00 pm AEDT",
                    "prefix": "Effective from",
                    "updatedTime": datetime.now(UTC).isoformat(),
                },
                "eventLabelPrepared": {
                    "icon": "fire",
                    "labelText": "Bushfire",
                },
                "cardBody": {
                    "type": "Bush Fire",
                    "size": "500 ha",
                    "status": "Going",
                    "source": "CFA",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [144.0, -38.0],
                            [146.0, -38.0],
                            [146.0, -36.5],
                            [144.0, -36.5],
                            [144.0, -38.0],
                        ]
                    ],
                },
            }
        ],
        "features": [],
        "mapBound": [[144.0, -38.0], [146.0, -36.5]],
        "stateName": "vic",
        "incidentsNumber": 1,
        "stateCount": 1,
    }


@pytest.fixture
def api_response_empty() -> dict[str, Any]:
    """API response with no incidents."""
    return {
        "emergencies": [],
        "features": [],
        "mapBound": None,
        "stateName": "nsw",
        "incidentsNumber": 0,
        "stateCount": 0,
    }


@pytest.fixture
def api_response_mixed_incidents() -> dict[str, Any]:
    """API response with mix of containing and non-containing incidents."""
    return {
        "emergencies": [
            {
                "id": "AUREMER-INSIDE",
                "headline": "Bushfire Inside Zone",
                "to": "/emergency/warning/AUREMER-INSIDE",
                "alertLevelInfoPrepared": {
                    "text": "Emergency",
                    "level": "extreme",
                    "style": "extreme",
                },
                "emergencyTimestampPrepared": {
                    "date": datetime.now(UTC).isoformat(),
                    "formattedTime": "12:00:00 pm AEDT",
                    "prefix": "Effective from",
                    "updatedTime": datetime.now(UTC).isoformat(),
                },
                "eventLabelPrepared": {
                    "icon": "fire",
                    "labelText": "Bushfire",
                },
                "cardBody": {
                    "type": "Bush Fire",
                    "size": "1000 ha",
                    "status": "Going",
                    "source": "NSW RFS",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [150.0, -34.5],
                            [152.5, -34.5],
                            [152.5, -33.0],
                            [150.0, -33.0],
                            [150.0, -34.5],
                        ]
                    ],
                },
            },
            {
                "id": "AUREMER-OUTSIDE",
                "headline": "Flood Outside Zone",
                "to": "/emergency/warning/AUREMER-OUTSIDE",
                "alertLevelInfoPrepared": {
                    "text": "Advice",
                    "level": "moderate",
                    "style": "moderate",
                },
                "emergencyTimestampPrepared": {
                    "date": datetime.now(UTC).isoformat(),
                    "formattedTime": "12:00:00 pm AEDT",
                    "prefix": "Effective from",
                    "updatedTime": datetime.now(UTC).isoformat(),
                },
                "eventLabelPrepared": {
                    "icon": "weather",
                    "labelText": "Flood",
                },
                "cardBody": {
                    "type": "Flood",
                    "size": None,
                    "status": "Active",
                    "source": "BoM",
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [151.1, -33.9],  # Within 50km radius of Sydney
                },
            },
        ],
        "features": [],
        "mapBound": [[150.0, -34.5], [152.5, -33.0]],
        "stateName": "nsw",
        "incidentsNumber": 2,
        "stateCount": 2,
    }


class TestIntegrationFullFlow:
    """Integration tests for complete API → Coordinator → Entity flow."""

    async def test_zone_mode_inside_polygon_full_flow(
        self,
        hass: HomeAssistant,
        zone_config_entry: MockConfigEntry,
        api_response_polygon_containing_sydney: dict[str, Any],
    ) -> None:
        """Test complete flow: API returns containing polygon → binary sensor ON."""
        zone_config_entry.add_to_hass(hass)

        with patch("custom_components.abcemergency.ABCEmergencyClient") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.async_get_emergencies_by_state = AsyncMock(
                return_value=api_response_polygon_containing_sydney
            )

            await hass.config_entries.async_setup(zone_config_entry.entry_id)
            await hass.async_block_till_done()

        # Verify binary sensor is ON for inside_polygon (entity_id uses "safety" from device_class)
        state = hass.states.get("binary_sensor.abc_emergency_home_zone_safety")
        assert state is not None
        assert state.state == "on"
        assert state.attributes["containing_count"] == 1

        # Verify inside_emergency_warning is ON (extreme = emergency warning)
        # Entity_id uses "safety_2" (collision avoidance with inside_polygon)
        state = hass.states.get("binary_sensor.abc_emergency_home_zone_safety_2")
        assert state is not None
        assert state.state == "on"

    async def test_zone_mode_outside_polygon_full_flow(
        self,
        hass: HomeAssistant,
        zone_config_entry: MockConfigEntry,
        api_response_polygon_not_containing_sydney: dict[str, Any],
    ) -> None:
        """Test complete flow: API returns non-containing polygon → binary sensor OFF."""
        zone_config_entry.add_to_hass(hass)

        with patch("custom_components.abcemergency.ABCEmergencyClient") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.async_get_emergencies_by_state = AsyncMock(
                return_value=api_response_polygon_not_containing_sydney
            )

            await hass.config_entries.async_setup(zone_config_entry.entry_id)
            await hass.async_block_till_done()

        # Verify binary sensor is OFF for inside_polygon (entity_id uses "safety")
        state = hass.states.get("binary_sensor.abc_emergency_home_zone_safety")
        assert state is not None
        assert state.state == "off"

    async def test_sensor_attributes_include_containment_fields(
        self,
        hass: HomeAssistant,
        zone_config_entry: MockConfigEntry,
        api_response_mixed_incidents: dict[str, Any],
    ) -> None:
        """Test sensor attributes include containment fields for each incident."""
        zone_config_entry.add_to_hass(hass)

        with patch("custom_components.abcemergency.ABCEmergencyClient") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.async_get_emergencies_by_state = AsyncMock(
                return_value=api_response_mixed_incidents
            )

            await hass.config_entries.async_setup(zone_config_entry.entry_id)
            await hass.async_block_till_done()

        # Check total incidents sensor has containment attributes
        state = hass.states.get("sensor.abc_emergency_home_zone_total_incidents")
        assert state is not None

        incidents = state.attributes.get("incidents", [])
        assert len(incidents) == 2

        # Each incident should have containment fields
        for incident in incidents:
            assert "contains_point" in incident
            assert "has_polygon" in incident

        # Verify containing_count attribute
        assert "containing_count" in state.attributes
        assert state.attributes["containing_count"] == 1

        # Verify inside_polygon attribute
        assert "inside_polygon" in state.attributes
        assert state.attributes["inside_polygon"] is True


class TestIntegrationEventFlow:
    """Integration tests for enter/exit polygon events."""

    async def test_entered_polygon_event_fires_on_transition(
        self,
        hass: HomeAssistant,
        zone_config_entry: MockConfigEntry,
        api_response_polygon_not_containing_sydney: dict[str, Any],
        api_response_polygon_containing_sydney: dict[str, Any],
    ) -> None:
        """Test entered_polygon event fires when transitioning to inside."""
        zone_config_entry.add_to_hass(hass)
        entered_events: list = []

        @callback
        def capture_entered(event: Any) -> None:
            entered_events.append(event)

        hass.bus.async_listen("abc_emergency_entered_polygon", capture_entered)

        with patch("custom_components.abcemergency.ABCEmergencyClient") as mock_client_class:
            mock_client = mock_client_class.return_value
            # Start outside
            mock_client.async_get_emergencies_by_state = AsyncMock(
                return_value=api_response_polygon_not_containing_sydney
            )

            await hass.config_entries.async_setup(zone_config_entry.entry_id)
            await hass.async_block_till_done()

            # No entered events yet (outside polygon)
            assert len(entered_events) == 0

            # Now change to be inside
            mock_client.async_get_emergencies_by_state = AsyncMock(
                return_value=api_response_polygon_containing_sydney
            )

            # Trigger coordinator refresh
            coordinator = hass.data[DOMAIN][zone_config_entry.entry_id]
            await coordinator.async_refresh()
            await hass.async_block_till_done()

        # Event should have fired
        assert len(entered_events) == 1
        assert entered_events[0].data["headline"] == "Test Bushfire Near Sydney"
        assert entered_events[0].data["alert_level"] == "extreme"

    async def test_exited_polygon_event_fires_on_transition(
        self,
        hass: HomeAssistant,
        zone_config_entry: MockConfigEntry,
        api_response_polygon_containing_sydney: dict[str, Any],
        api_response_polygon_not_containing_sydney: dict[str, Any],
    ) -> None:
        """Test exited_polygon event fires when transitioning to outside."""
        zone_config_entry.add_to_hass(hass)
        exited_events: list = []

        @callback
        def capture_exited(event: Any) -> None:
            exited_events.append(event)

        hass.bus.async_listen("abc_emergency_exited_polygon", capture_exited)

        with patch("custom_components.abcemergency.ABCEmergencyClient") as mock_client_class:
            mock_client = mock_client_class.return_value
            # Start inside
            mock_client.async_get_emergencies_by_state = AsyncMock(
                return_value=api_response_polygon_containing_sydney
            )

            await hass.config_entries.async_setup(zone_config_entry.entry_id)
            await hass.async_block_till_done()

            # No exit events yet (first load doesn't fire exit)
            exited_events.clear()

            # Now change to be outside
            mock_client.async_get_emergencies_by_state = AsyncMock(
                return_value=api_response_polygon_not_containing_sydney
            )

            # Trigger coordinator refresh
            coordinator = hass.data[DOMAIN][zone_config_entry.entry_id]
            await coordinator.async_refresh()
            await hass.async_block_till_done()

        # Exit event should have fired
        assert len(exited_events) == 1
        assert exited_events[0].data["incident_id"] == "AUREMER-CONTAIN-SYDNEY"


class TestIntegrationPersonMode:
    """Integration tests for person mode dynamic location."""

    async def test_person_mode_detects_containment_at_person_location(
        self,
        hass: HomeAssistant,
        person_config_entry: MockConfigEntry,
        api_response_polygon_containing_sydney: dict[str, Any],
    ) -> None:
        """Test person mode detects containment at person's location."""
        # Set up person entity at Sydney (inside polygon)
        hass.states.async_set(
            "person.test_user",
            "home",
            {"latitude": -33.8688, "longitude": 151.2093},
        )

        person_config_entry.add_to_hass(hass)

        with patch("custom_components.abcemergency.ABCEmergencyClient") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.async_get_emergencies_by_state = AsyncMock(
                return_value=api_response_polygon_containing_sydney
            )

            await hass.config_entries.async_setup(person_config_entry.entry_id)
            await hass.async_block_till_done()

        # Verify person is inside polygon (entity_id uses "safety" from device_class)
        state = hass.states.get("binary_sensor.abc_emergency_test_user_safety")
        assert state is not None
        assert state.state == "on"

    async def test_person_mode_enters_polygon_when_moving(
        self,
        hass: HomeAssistant,
        person_config_entry: MockConfigEntry,
        api_response_polygon_containing_sydney: dict[str, Any],
    ) -> None:
        """Test person entering polygon as they move."""
        entered_events: list = []

        @callback
        def capture_entered(event: Any) -> None:
            entered_events.append(event)

        hass.bus.async_listen("abc_emergency_entered_polygon", capture_entered)

        # Person starts outside polygon (Melbourne)
        hass.states.async_set(
            "person.test_user",
            "home",
            {"latitude": -37.8136, "longitude": 144.9631},
        )

        person_config_entry.add_to_hass(hass)

        with patch("custom_components.abcemergency.ABCEmergencyClient") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.async_get_emergencies_by_state = AsyncMock(
                return_value=api_response_polygon_containing_sydney
            )

            await hass.config_entries.async_setup(person_config_entry.entry_id)
            await hass.async_block_till_done()

            # Verify outside polygon initially (entity_id uses "safety")
            state = hass.states.get("binary_sensor.abc_emergency_test_user_safety")
            assert state is not None
            assert state.state == "off"
            assert len(entered_events) == 0

            # Person moves to Sydney (inside polygon)
            hass.states.async_set(
                "person.test_user",
                "away",
                {"latitude": -33.8688, "longitude": 151.2093},
            )

            # Trigger coordinator refresh
            coordinator = hass.data[DOMAIN][person_config_entry.entry_id]
            await coordinator.async_refresh()
            await hass.async_block_till_done()

        # Now inside polygon
        state = hass.states.get("binary_sensor.abc_emergency_test_user_safety")
        assert state.state == "on"

        # Entered event should have fired
        assert len(entered_events) == 1


class TestIntegrationStateMode:
    """Integration tests for state mode (no containment)."""

    async def test_state_mode_no_containment_sensors_created(
        self,
        hass: HomeAssistant,
        state_config_entry: MockConfigEntry,
        api_response_polygon_containing_sydney: dict[str, Any],
    ) -> None:
        """Test state mode does NOT create containment binary sensors."""
        state_config_entry.add_to_hass(hass)

        with patch("custom_components.abcemergency.ABCEmergencyClient") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.async_get_emergencies_by_state = AsyncMock(
                return_value=api_response_polygon_containing_sydney
            )

            await hass.config_entries.async_setup(state_config_entry.entry_id)
            await hass.async_block_till_done()

        # Verify containment sensors don't exist for state mode
        # Containment sensors would use "safety*" entity_ids if they existed
        assert hass.states.get("binary_sensor.abc_emergency_nsw_safety") is None
        assert hass.states.get("binary_sensor.abc_emergency_nsw_safety_2") is None
        assert hass.states.get("binary_sensor.abc_emergency_nsw_safety_3") is None
        assert hass.states.get("binary_sensor.abc_emergency_nsw_safety_4") is None

    async def test_state_mode_sensor_containment_attributes_null(
        self,
        hass: HomeAssistant,
        state_config_entry: MockConfigEntry,
        api_response_polygon_containing_sydney: dict[str, Any],
    ) -> None:
        """Test state mode sensors have null containment attributes."""
        state_config_entry.add_to_hass(hass)

        with patch("custom_components.abcemergency.ABCEmergencyClient") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.async_get_emergencies_by_state = AsyncMock(
                return_value=api_response_polygon_containing_sydney
            )

            await hass.config_entries.async_setup(state_config_entry.entry_id)
            await hass.async_block_till_done()

        # Check total incidents sensor has null containment attributes
        # State name "nsw" expands to "New South Wales" in entity_id
        state = hass.states.get("sensor.abc_emergency_new_south_wales_total_incidents")
        assert state is not None

        # State mode should have null containment attributes
        assert state.attributes.get("containing_count") is None
        assert state.attributes.get("inside_polygon") is None
        assert state.attributes.get("highest_containing_level") is None

    async def test_state_mode_no_containment_events_fired(
        self,
        hass: HomeAssistant,
        state_config_entry: MockConfigEntry,
        api_response_polygon_containing_sydney: dict[str, Any],
    ) -> None:
        """Test state mode does NOT fire containment events."""
        state_config_entry.add_to_hass(hass)
        events: list = []

        @callback
        def capture_event(event: Any) -> None:
            events.append(event)

        hass.bus.async_listen("abc_emergency_entered_polygon", capture_event)
        hass.bus.async_listen("abc_emergency_exited_polygon", capture_event)
        hass.bus.async_listen("abc_emergency_inside_polygon", capture_event)

        with patch("custom_components.abcemergency.ABCEmergencyClient") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.async_get_emergencies_by_state = AsyncMock(
                return_value=api_response_polygon_containing_sydney
            )

            await hass.config_entries.async_setup(state_config_entry.entry_id)
            await hass.async_block_till_done()

            # Multiple refreshes
            coordinator = hass.data[DOMAIN][state_config_entry.entry_id]
            await coordinator.async_refresh()
            await hass.async_block_till_done()

        # No containment events should fire for state mode
        assert len(events) == 0


class TestIntegrationEmptyData:
    """Integration tests for edge cases with empty data."""

    async def test_zone_mode_no_incidents(
        self,
        hass: HomeAssistant,
        zone_config_entry: MockConfigEntry,
        api_response_empty: dict[str, Any],
    ) -> None:
        """Test zone mode handles no incidents gracefully."""
        zone_config_entry.add_to_hass(hass)

        with patch("custom_components.abcemergency.ABCEmergencyClient") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.async_get_emergencies_by_state = AsyncMock(return_value=api_response_empty)

            await hass.config_entries.async_setup(zone_config_entry.entry_id)
            await hass.async_block_till_done()

        # Containment sensors should be OFF (entity_id uses "safety")
        state = hass.states.get("binary_sensor.abc_emergency_home_zone_safety")
        assert state is not None
        assert state.state == "off"

        # Total incidents should be 0
        state = hass.states.get("sensor.abc_emergency_home_zone_total_incidents")
        assert state is not None
        assert int(state.state) == 0
