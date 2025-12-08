"""Tests for ABC Emergency incident event functionality."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from freezegun.api import FrozenDateTimeFactory
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
from custom_components.abcemergency.coordinator import ABCEmergencyCoordinator

if TYPE_CHECKING:
    from homeassistant.core import Event, HomeAssistant


@pytest.fixture
def event_listener() -> Callable[[], tuple[list[Any], Callable[[Event[Any]], None]]]:
    """Create an event listener factory for testing events.

    Returns a factory that creates (events_list, listener_callback) tuples.
    """

    def create_listener() -> tuple[list[Any], Callable[[Event[Any]], None]]:
        events: list[Any] = []

        def listener(event: Event[Any]) -> None:
            events.append(event)

        return events, listener

    return create_listener


@pytest.fixture
def mock_client() -> MagicMock:
    """Create a mock API client."""
    return MagicMock()


@pytest.fixture
def mock_config_entry_state() -> MockConfigEntry:
    """Create a mock config entry for state mode."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_INSTANCE_TYPE: INSTANCE_TYPE_STATE,
            CONF_STATE: "nsw",
        },
        unique_id="abc_emergency_state_nsw",
        title="NSW Emergencies",
    )


@pytest.fixture
def mock_config_entry_zone() -> MockConfigEntry:
    """Create a mock config entry for zone mode."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE,
            CONF_ZONE_NAME: "Home",
            "latitude": -33.8688,
            "longitude": 151.2093,
            CONF_RADIUS_BUSHFIRE: DEFAULT_RADIUS_BUSHFIRE,
            CONF_RADIUS_EARTHQUAKE: DEFAULT_RADIUS_EARTHQUAKE,
            CONF_RADIUS_STORM: DEFAULT_RADIUS_STORM,
            CONF_RADIUS_FLOOD: DEFAULT_RADIUS_FLOOD,
            CONF_RADIUS_FIRE: DEFAULT_RADIUS_FIRE,
            CONF_RADIUS_HEAT: DEFAULT_RADIUS_HEAT,
            CONF_RADIUS_OTHER: DEFAULT_RADIUS_OTHER,
        },
        unique_id="abc_emergency_zone_home",
        title="Home Zone",
    )


@pytest.fixture
def mock_config_entry_person() -> MockConfigEntry:
    """Create a mock config entry for person mode."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_INSTANCE_TYPE: INSTANCE_TYPE_PERSON,
            CONF_PERSON_ENTITY_ID: "person.john",
            CONF_PERSON_NAME: "John",
            CONF_RADIUS_BUSHFIRE: DEFAULT_RADIUS_BUSHFIRE,
            CONF_RADIUS_EARTHQUAKE: DEFAULT_RADIUS_EARTHQUAKE,
            CONF_RADIUS_STORM: DEFAULT_RADIUS_STORM,
            CONF_RADIUS_FLOOD: DEFAULT_RADIUS_FLOOD,
            CONF_RADIUS_FIRE: DEFAULT_RADIUS_FIRE,
            CONF_RADIUS_HEAT: DEFAULT_RADIUS_HEAT,
            CONF_RADIUS_OTHER: DEFAULT_RADIUS_OTHER,
        },
        unique_id="abc_emergency_person_john",
        title="John's Location",
    )


@pytest.fixture
def sample_api_response_single() -> dict[str, Any]:
    """Provide a sample API response with a single incident."""
    return {
        "emergencies": [
            {
                "id": "AUREMER-bushfire1",
                "headline": "Bushfire at Test Location",
                "to": "/emergency/warning/AUREMER-bushfire1",
                "alertLevelInfoPrepared": {
                    "text": "Emergency",
                    "level": "extreme",
                    "style": "extreme",
                },
                "emergencyTimestampPrepared": {
                    "date": "2025-12-06T05:34:00+00:00",
                    "formattedTime": "4:34:00 pm AEDT",
                    "prefix": "Effective from",
                    "updatedTime": "2025-12-06T05:53:02.97994+00:00",
                },
                "eventLabelPrepared": {
                    "icon": "fire",
                    "labelText": "Bushfire",
                },
                "cardBody": {
                    "type": "Bush Fire",
                    "size": "500 ha",
                    "status": "Out of control",
                    "source": "NSW Rural Fire Service",
                },
                "geometry": {
                    "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
                    "type": "GeometryCollection",
                    "geometries": [
                        {"type": "Point", "coordinates": [151.0, -33.87]},
                    ],
                },
            },
        ],
        "features": [],
        "mapBound": [[140.0, -38.0], [154.0, -28.0]],
        "stateName": "nsw",
        "incidentsNumber": 1,
        "stateCount": 125,
    }


@pytest.fixture
def sample_api_response_multiple() -> dict[str, Any]:
    """Provide a sample API response with multiple incidents."""
    return {
        "emergencies": [
            {
                "id": "AUREMER-bushfire1",
                "headline": "Bushfire at Location A",
                "to": "/emergency/warning/AUREMER-bushfire1",
                "alertLevelInfoPrepared": {
                    "text": "Emergency",
                    "level": "extreme",
                    "style": "extreme",
                },
                "emergencyTimestampPrepared": {
                    "date": "2025-12-06T05:34:00+00:00",
                    "formattedTime": "4:34:00 pm AEDT",
                    "prefix": "Effective from",
                    "updatedTime": "2025-12-06T05:53:02.97994+00:00",
                },
                "eventLabelPrepared": {"icon": "fire", "labelText": "Bushfire"},
                "cardBody": {
                    "type": "Bush Fire",
                    "size": "500 ha",
                    "status": "Out of control",
                    "source": "NSW Rural Fire Service",
                },
                "geometry": {
                    "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
                    "type": "GeometryCollection",
                    "geometries": [{"type": "Point", "coordinates": [151.0, -33.87]}],
                },
            },
            {
                "id": "AUREMER-flood1",
                "headline": "Flood Warning at River",
                "to": "/emergency/warning/AUREMER-flood1",
                "alertLevelInfoPrepared": {
                    "text": "Watch and Act",
                    "level": "severe",
                    "style": "severe",
                },
                "emergencyTimestampPrepared": {
                    "date": "2025-12-06T04:00:00+00:00",
                    "formattedTime": "3:00:00 pm AEDT",
                    "prefix": "Effective from",
                    "updatedTime": "2025-12-06T04:30:00.00+00:00",
                },
                "eventLabelPrepared": {"icon": "weather", "labelText": "Flood"},
                "cardBody": {
                    "type": "Flood",
                    "size": None,
                    "status": "Developing",
                    "source": "Bureau of Meteorology",
                },
                "geometry": {
                    "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
                    "type": "GeometryCollection",
                    "geometries": [{"type": "Point", "coordinates": [151.1, -33.85]}],
                },
            },
            {
                "id": "AUREMER-storm1",
                "headline": "Severe Storm Warning",
                "to": "/emergency/warning/AUREMER-storm1",
                "alertLevelInfoPrepared": {
                    "text": "Advice",
                    "level": "moderate",
                    "style": "moderate",
                },
                "emergencyTimestampPrepared": {
                    "date": "2025-12-06T03:00:00+00:00",
                    "formattedTime": "2:00:00 pm AEDT",
                    "prefix": "Effective from",
                    "updatedTime": "2025-12-06T03:30:00.00+00:00",
                },
                "eventLabelPrepared": {"icon": "weather", "labelText": "Storm"},
                "cardBody": {
                    "type": "Storm",
                    "size": None,
                    "status": "Active",
                    "source": "Bureau of Meteorology",
                },
                "geometry": {
                    "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
                    "type": "GeometryCollection",
                    "geometries": [{"type": "Point", "coordinates": [151.2, -33.88]}],
                },
            },
        ],
        "features": [],
        "mapBound": [[140.0, -38.0], [154.0, -28.0]],
        "stateName": "nsw",
        "incidentsNumber": 3,
        "stateCount": 125,
    }


@pytest.fixture
def empty_api_response() -> dict[str, Any]:
    """Provide an empty API response."""
    return {
        "emergencies": [],
        "features": [],
        "mapBound": [[140.0, -38.0], [154.0, -28.0]],
        "stateName": "nsw",
        "incidentsNumber": 0,
        "stateCount": 0,
    }


class TestIncidentIDTracking:
    """Test incident ID tracking (Issue #38)."""

    def test_coordinator_initializes_with_empty_seen_ids(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test that _seen_incident_ids is empty on initialization."""
        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        assert hasattr(coordinator, "_seen_incident_ids")
        assert coordinator._seen_incident_ids == set()

    def test_coordinator_initializes_with_first_refresh_true(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test that _first_refresh is True on initialization."""
        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        assert hasattr(coordinator, "_first_refresh")
        assert coordinator._first_refresh is True

    async def test_seen_ids_updated_after_refresh(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
        sample_api_response_single: dict[str, Any],
    ) -> None:
        """Test that IDs are tracked after first update."""
        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=sample_api_response_single
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        await coordinator._async_update_data()

        assert "AUREMER-bushfire1" in coordinator._seen_incident_ids

    async def test_first_refresh_becomes_false_after_update(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
        sample_api_response_single: dict[str, Any],
    ) -> None:
        """Test that _first_refresh becomes False after first update."""
        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=sample_api_response_single
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        assert coordinator._first_refresh is True
        await coordinator._async_update_data()
        assert coordinator._first_refresh is False


class TestNewIncidentDetection:
    """Test new incident detection logic (Issue #39)."""

    async def test_new_incident_detected_when_count_increases(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
        sample_api_response_single: dict[str, Any],
        sample_api_response_multiple: dict[str, Any],
        event_listener: Callable[[], tuple[list[Any], Callable[[Any], None]]],
    ) -> None:
        """Test new incident detection when incident count increases."""
        # Start with single incident
        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=sample_api_response_single
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        # First refresh - no events should fire
        await coordinator._async_update_data()
        assert len(coordinator._seen_incident_ids) == 1

        # Set up event listener before second update
        events, listener = event_listener()
        hass.bus.async_listen("abc_emergency_new_incident", listener)

        # Now update with multiple incidents
        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=sample_api_response_multiple
        )

        await coordinator._async_update_data()
        await hass.async_block_till_done()

        # Should have detected 2 new incidents (flood and storm)
        assert len(events) == 2
        # All 3 IDs should now be tracked
        assert len(coordinator._seen_incident_ids) == 3

    async def test_new_incident_detected_when_count_same_but_ids_change(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
        sample_api_response_single: dict[str, Any],
        event_listener: Callable[[], tuple[list[Any], Callable[[Any], None]]],
    ) -> None:
        """Test new incident detection when count stays same but IDs change."""
        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=sample_api_response_single
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        # First refresh
        await coordinator._async_update_data()
        assert "AUREMER-bushfire1" in coordinator._seen_incident_ids

        # Create response with different incident (same count)
        different_response = {
            "emergencies": [
                {
                    "id": "AUREMER-bushfire2",  # Different ID
                    "headline": "Bushfire at Different Location",
                    "to": "/emergency/warning/AUREMER-bushfire2",
                    "alertLevelInfoPrepared": {
                        "text": "Emergency",
                        "level": "extreme",
                        "style": "extreme",
                    },
                    "emergencyTimestampPrepared": {
                        "date": "2025-12-06T06:00:00+00:00",
                        "formattedTime": "5:00:00 pm AEDT",
                        "prefix": "Effective from",
                        "updatedTime": "2025-12-06T06:30:00.00+00:00",
                    },
                    "eventLabelPrepared": {"icon": "fire", "labelText": "Bushfire"},
                    "cardBody": {
                        "type": "Bush Fire",
                        "size": "200 ha",
                        "status": "Being controlled",
                        "source": "NSW Rural Fire Service",
                    },
                    "geometry": {
                        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
                        "type": "GeometryCollection",
                        "geometries": [{"type": "Point", "coordinates": [151.5, -33.9]}],
                    },
                },
            ],
            "features": [],
            "mapBound": [[140.0, -38.0], [154.0, -28.0]],
            "stateName": "nsw",
            "incidentsNumber": 1,
            "stateCount": 125,
        }

        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=different_response)

        # Set up event listener
        events, listener = event_listener()
        hass.bus.async_listen("abc_emergency_new_incident", listener)

        await coordinator._async_update_data()
        await hass.async_block_till_done()

        # Should have detected 1 new incident
        assert len(events) >= 1
        # New ID should be in tracking set, old one should be removed
        assert "AUREMER-bushfire2" in coordinator._seen_incident_ids
        assert "AUREMER-bushfire1" not in coordinator._seen_incident_ids

    async def test_no_events_on_first_refresh(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
        sample_api_response_multiple: dict[str, Any],
        event_listener: Callable[[], tuple[list[Any], Callable[[Any], None]]],
    ) -> None:
        """Test that first refresh does not fire events."""
        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=sample_api_response_multiple
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        # Set up event listener before first update
        events, listener = event_listener()
        hass.bus.async_listen("abc_emergency_new_incident", listener)

        await coordinator._async_update_data()
        await hass.async_block_till_done()

        # No events should fire on first refresh
        assert len(events) == 0

    async def test_removed_incidents_not_in_tracking_set(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
        sample_api_response_multiple: dict[str, Any],
        sample_api_response_single: dict[str, Any],
    ) -> None:
        """Test that removed incidents don't stay in tracking set."""
        # Start with multiple incidents
        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=sample_api_response_multiple
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        await coordinator._async_update_data()
        assert len(coordinator._seen_incident_ids) == 3

        # Now update with single incident (2 removed)
        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=sample_api_response_single
        )

        await coordinator._async_update_data()
        # Only 1 incident should remain in tracking set
        assert len(coordinator._seen_incident_ids) == 1
        assert "AUREMER-bushfire1" in coordinator._seen_incident_ids

    async def test_detection_works_in_zone_mode(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
        sample_api_response_single: dict[str, Any],
        sample_api_response_multiple: dict[str, Any],
        event_listener: Callable[[], tuple[list[Any], Callable[[Any], None]]],
    ) -> None:
        """Test detection works in zone mode."""
        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=sample_api_response_single
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        await coordinator._async_update_data()
        assert coordinator._first_refresh is False

        # Set up event listener
        events, listener = event_listener()
        hass.bus.async_listen("abc_emergency_new_incident", listener)

        # Update with more incidents
        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=sample_api_response_multiple
        )

        await coordinator._async_update_data()
        await hass.async_block_till_done()

        # Should detect new incidents
        assert len(events) >= 2

    async def test_detection_works_in_person_mode(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_person: MockConfigEntry,
        sample_api_response_single: dict[str, Any],
        sample_api_response_multiple: dict[str, Any],
        event_listener: Callable[[], tuple[list[Any], Callable[[Any], None]]],
    ) -> None:
        """Test detection works in person mode."""
        # Set up person entity
        hass.states.async_set(
            "person.john",
            "home",
            {"latitude": -33.8688, "longitude": 151.2093},
        )

        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=sample_api_response_single
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_person,
            instance_type=INSTANCE_TYPE_PERSON,
            person_entity_id="person.john",
        )

        await coordinator._async_update_data()
        assert coordinator._first_refresh is False

        # Set up event listener
        events, listener = event_listener()
        hass.bus.async_listen("abc_emergency_new_incident", listener)

        # Update with more incidents
        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=sample_api_response_multiple
        )

        await coordinator._async_update_data()
        await hass.async_block_till_done()

        # Should detect new incidents
        assert len(events) >= 2


class TestEventFiring:
    """Test event firing method (Issue #40)."""

    async def test_event_fired_with_correct_type(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
        sample_api_response_single: dict[str, Any],
        event_listener: Callable[[], tuple[list[Any], Callable[[Any], None]]],
    ) -> None:
        """Test event is fired with correct event type."""
        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value={
                "emergencies": [],
                "features": [],
                "mapBound": [],
                "stateName": "nsw",
                "incidentsNumber": 0,
                "stateCount": 0,
            }
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        # First refresh with empty data
        await coordinator._async_update_data()

        # Set up event listener
        events, listener = event_listener()
        hass.bus.async_listen("abc_emergency_new_incident", listener)

        # Now add an incident
        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=sample_api_response_single
        )

        await coordinator._async_update_data()
        await hass.async_block_till_done()

        # Should fire the generic event
        assert len(events) == 1
        assert events[0].event_type == "abc_emergency_new_incident"

    async def test_event_payload_contains_all_fields(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
        sample_api_response_single: dict[str, Any],
        event_listener: Callable[[], tuple[list[Any], Callable[[Any], None]]],
    ) -> None:
        """Test event payload contains all required fields."""
        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value={
                "emergencies": [],
                "features": [],
                "mapBound": [],
                "stateName": "nsw",
                "incidentsNumber": 0,
                "stateCount": 0,
            }
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        await coordinator._async_update_data()

        # Set up event listener
        events, listener = event_listener()
        hass.bus.async_listen("abc_emergency_new_incident", listener)

        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=sample_api_response_single
        )

        await coordinator._async_update_data()
        await hass.async_block_till_done()

        # Check we got an event
        assert len(events) == 1
        event_data = events[0].data

        # Check required fields
        assert "config_entry_id" in event_data
        assert "instance_name" in event_data
        assert "instance_type" in event_data
        assert "incident_id" in event_data
        assert "headline" in event_data
        assert "event_type" in event_data
        assert "event_icon" in event_data
        assert "alert_level" in event_data
        assert "alert_text" in event_data
        assert "latitude" in event_data
        assert "longitude" in event_data
        assert "status" in event_data
        assert "source" in event_data
        assert "updated" in event_data
        # Zone mode fields
        assert "distance_km" in event_data
        assert "direction" in event_data
        assert "bearing" in event_data

    async def test_multiple_incidents_fire_multiple_events(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
        sample_api_response_multiple: dict[str, Any],
        event_listener: Callable[[], tuple[list[Any], Callable[[Any], None]]],
    ) -> None:
        """Test multiple incidents fire multiple events."""
        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value={
                "emergencies": [],
                "features": [],
                "mapBound": [],
                "stateName": "nsw",
                "incidentsNumber": 0,
                "stateCount": 0,
            }
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        await coordinator._async_update_data()

        # Set up event listener
        events, listener = event_listener()
        hass.bus.async_listen("abc_emergency_new_incident", listener)

        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=sample_api_response_multiple
        )

        await coordinator._async_update_data()
        await hass.async_block_till_done()

        # Count generic events
        assert len(events) == 3

    async def test_nullable_fields_handled_correctly(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
        event_listener: Callable[[], tuple[list[Any], Callable[[Any], None]]],
    ) -> None:
        """Test nullable fields are handled correctly."""
        # Response with missing cardBody fields
        response_with_nulls = {
            "emergencies": [
                {
                    "id": "AUREMER-test1",
                    "headline": "Test Warning",
                    "to": "/emergency/warning/AUREMER-test1",
                    "alertLevelInfoPrepared": {
                        "text": "",
                        "level": "minor",
                        "style": "minor",
                    },
                    "emergencyTimestampPrepared": {
                        "date": "2025-12-06T05:34:00+00:00",
                        "formattedTime": "4:34:00 pm AEDT",
                        "prefix": "Effective from",
                        "updatedTime": "2025-12-06T05:53:02.97994+00:00",
                    },
                    "eventLabelPrepared": {"icon": "other", "labelText": "Other"},
                    "cardBody": {},  # Empty cardBody
                    "geometry": {
                        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
                        "type": "GeometryCollection",
                        "geometries": [{"type": "Point", "coordinates": [151.0, -33.87]}],
                    },
                },
            ],
            "features": [],
            "mapBound": [[140.0, -38.0], [154.0, -28.0]],
            "stateName": "nsw",
            "incidentsNumber": 1,
            "stateCount": 1,
        }

        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value={
                "emergencies": [],
                "features": [],
                "mapBound": [],
                "stateName": "nsw",
                "incidentsNumber": 0,
                "stateCount": 0,
            }
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        await coordinator._async_update_data()

        # Set up event listener
        events, listener = event_listener()
        hass.bus.async_listen("abc_emergency_new_incident", listener)

        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=response_with_nulls)

        await coordinator._async_update_data()
        await hass.async_block_till_done()

        assert len(events) == 1
        event_data = events[0].data
        # These fields should be None, not cause errors
        assert event_data["status"] is None
        assert event_data["size"] is None


class TestTypeSpecificEvents:
    """Test type-specific events (Issue #42)."""

    async def test_slugify_simple_type(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
        sample_api_response_single: dict[str, Any],
        event_listener: Callable[[], tuple[list[Any], Callable[[Any], None]]],
    ) -> None:
        """Test slugification of simple event types."""
        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value={
                "emergencies": [],
                "features": [],
                "mapBound": [],
                "stateName": "nsw",
                "incidentsNumber": 0,
                "stateCount": 0,
            }
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        await coordinator._async_update_data()

        # Set up event listener for type-specific event
        events, listener = event_listener()
        hass.bus.async_listen("abc_emergency_new_bushfire", listener)

        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=sample_api_response_single
        )

        await coordinator._async_update_data()
        await hass.async_block_till_done()

        assert len(events) == 1
        assert events[0].event_type == "abc_emergency_new_bushfire"

    async def test_slugify_type_with_spaces(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
        event_listener: Callable[[], tuple[list[Any], Callable[[Any], None]]],
    ) -> None:
        """Test slugification of event types with spaces."""
        response = {
            "emergencies": [
                {
                    "id": "AUREMER-heat1",
                    "headline": "Extreme Heat Warning",
                    "to": "/emergency/warning/AUREMER-heat1",
                    "alertLevelInfoPrepared": {
                        "text": "Warning",
                        "level": "severe",
                        "style": "severe",
                    },
                    "emergencyTimestampPrepared": {
                        "date": "2025-12-06T05:34:00+00:00",
                        "formattedTime": "4:34:00 pm AEDT",
                        "prefix": "Effective from",
                        "updatedTime": "2025-12-06T05:53:02.97994+00:00",
                    },
                    "eventLabelPrepared": {"icon": "heat", "labelText": "Extreme Heat"},
                    "cardBody": {
                        "type": "Heat Wave",
                        "size": None,
                        "status": "Active",
                        "source": "Bureau of Meteorology",
                    },
                    "geometry": {
                        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
                        "type": "GeometryCollection",
                        "geometries": [{"type": "Point", "coordinates": [151.0, -33.87]}],
                    },
                },
            ],
            "features": [],
            "mapBound": [[140.0, -38.0], [154.0, -28.0]],
            "stateName": "nsw",
            "incidentsNumber": 1,
            "stateCount": 1,
        }

        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value={
                "emergencies": [],
                "features": [],
                "mapBound": [],
                "stateName": "nsw",
                "incidentsNumber": 0,
                "stateCount": 0,
            }
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        await coordinator._async_update_data()

        # Set up event listener for type-specific event
        events, listener = event_listener()
        hass.bus.async_listen("abc_emergency_new_extreme_heat", listener)

        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=response)

        await coordinator._async_update_data()
        await hass.async_block_till_done()

        assert len(events) == 1
        assert events[0].event_type == "abc_emergency_new_extreme_heat"

    async def test_generic_and_type_specific_events_fired(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
        sample_api_response_single: dict[str, Any],
        event_listener: Callable[[], tuple[list[Any], Callable[[Any], None]]],
    ) -> None:
        """Test both generic and type-specific events are fired."""
        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value={
                "emergencies": [],
                "features": [],
                "mapBound": [],
                "stateName": "nsw",
                "incidentsNumber": 0,
                "stateCount": 0,
            }
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        await coordinator._async_update_data()

        # Set up event listeners for both event types
        generic_events, generic_listener = event_listener()
        specific_events, specific_listener = event_listener()
        hass.bus.async_listen("abc_emergency_new_incident", generic_listener)
        hass.bus.async_listen("abc_emergency_new_bushfire", specific_listener)

        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=sample_api_response_single
        )

        await coordinator._async_update_data()
        await hass.async_block_till_done()

        assert len(generic_events) == 1
        assert len(specific_events) == 1

    async def test_event_payloads_identical(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
        sample_api_response_single: dict[str, Any],
        event_listener: Callable[[], tuple[list[Any], Callable[[Any], None]]],
    ) -> None:
        """Test event payloads are identical for generic and type-specific events."""
        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value={
                "emergencies": [],
                "features": [],
                "mapBound": [],
                "stateName": "nsw",
                "incidentsNumber": 0,
                "stateCount": 0,
            }
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        await coordinator._async_update_data()

        # Set up event listeners for both event types
        generic_events, generic_listener = event_listener()
        specific_events, specific_listener = event_listener()
        hass.bus.async_listen("abc_emergency_new_incident", generic_listener)
        hass.bus.async_listen("abc_emergency_new_bushfire", specific_listener)

        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=sample_api_response_single
        )

        await coordinator._async_update_data()
        await hass.async_block_till_done()

        assert len(generic_events) == 1
        assert len(specific_events) == 1

        generic_payload = generic_events[0].data
        specific_payload = specific_events[0].data

        assert generic_payload == specific_payload


class TestPersistence:
    """Test persistence for seen incident IDs (Issue #41)."""

    async def test_storage_file_created_and_loaded(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
        sample_api_response_single: dict[str, Any],
    ) -> None:
        """Test IDs are persisted and loaded from storage."""
        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=sample_api_response_single
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        # Load should work even with no existing storage
        await coordinator.async_load_seen_incidents()

        # First refresh
        await coordinator._async_update_data()

        # Verify ID is tracked
        assert "AUREMER-bushfire1" in coordinator._seen_incident_ids

    async def test_first_refresh_false_when_loading_existing_data(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test _first_refresh is False when loading existing storage data."""
        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        # Simulate loading existing data (v1 format triggers migration)
        with patch.object(coordinator, "_store") as mock_store:
            mock_store.async_load = AsyncMock(
                return_value={"seen_ids": ["AUREMER-existing1", "AUREMER-existing2"]}
            )
            mock_store.async_save = AsyncMock()  # For v1->v2 migration
            await coordinator.async_load_seen_incidents()

            assert coordinator._first_refresh is False
            assert "AUREMER-existing1" in coordinator._seen_incident_ids
            assert "AUREMER-existing2" in coordinator._seen_incident_ids

    async def test_graceful_handling_of_missing_storage(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test graceful handling when storage file doesn't exist."""
        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        with patch.object(coordinator, "_store") as mock_store:
            mock_store.async_load = AsyncMock(return_value=None)
            await coordinator.async_load_seen_incidents()

            # Should still be first refresh
            assert coordinator._first_refresh is True
            assert coordinator._seen_incident_ids == set()

    async def test_graceful_handling_of_corrupt_storage(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test graceful handling of corrupt storage data."""
        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        with patch.object(coordinator, "_store") as mock_store:
            # Return data without 'seen_ids' key
            mock_store.async_load = AsyncMock(return_value={"invalid": "data"})
            await coordinator.async_load_seen_incidents()

            # Should still be first refresh
            assert coordinator._first_refresh is True
            assert coordinator._seen_incident_ids == set()


class TestEventLogging:
    """Test event logging."""

    async def test_event_logged_at_info_level(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
        sample_api_response_single: dict[str, Any],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test events are logged at INFO level."""
        import logging

        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value={
                "emergencies": [],
                "features": [],
                "mapBound": [],
                "stateName": "nsw",
                "incidentsNumber": 0,
                "stateCount": 0,
            }
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        await coordinator._async_update_data()

        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=sample_api_response_single
        )

        with caplog.at_level(logging.INFO):
            await coordinator._async_update_data()

            # Check for log message about new incident
            assert any(
                "New" in record.message and "incident" in record.message.lower()
                for record in caplog.records
            )


class TestStorageCleanup:
    """Test storage cleanup functionality."""

    async def test_async_remove_storage_clears_storage(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test async_remove_storage clears the storage."""
        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        # Call remove storage - should not raise
        await coordinator.async_remove_storage()

    async def test_cleanup_removes_old_incidents(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
        freezer: FrozenDateTimeFactory,
    ) -> None:
        """Test cleanup removes incidents older than 30 days."""
        from datetime import timedelta

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        # Set up old storage data with timestamps (v2 format)
        now = datetime.now(UTC)
        old_date = (now - timedelta(days=31)).isoformat()
        recent_date = (now - timedelta(days=5)).isoformat()

        with patch.object(coordinator, "_store") as mock_store:
            mock_store.async_load = AsyncMock(
                return_value={
                    "seen_incidents": {
                        "AUREMER-old1": old_date,
                        "AUREMER-old2": old_date,
                        "AUREMER-recent1": recent_date,
                    }
                }
            )
            mock_store.async_save = AsyncMock()
            await coordinator.async_load_seen_incidents()

        # Old incidents should be cleaned up, recent ones kept
        assert "AUREMER-old1" not in coordinator._seen_incident_ids
        assert "AUREMER-old2" not in coordinator._seen_incident_ids
        assert "AUREMER-recent1" in coordinator._seen_incident_ids

    async def test_cleanup_handles_timezone_naive_timestamps(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test cleanup properly handles timezone-naive timestamps."""
        from datetime import timedelta

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        # Set up storage with timezone-naive timestamp (simulating legacy data)
        now = datetime.now(UTC)
        # Create timezone-naive ISO string (no +00:00 suffix)
        naive_old = (now - timedelta(days=31)).replace(tzinfo=None).isoformat()
        naive_recent = (now - timedelta(days=5)).replace(tzinfo=None).isoformat()

        with patch.object(coordinator, "_store") as mock_store:
            mock_store.async_load = AsyncMock(
                return_value={
                    "seen_incidents": {
                        "AUREMER-naive-old": naive_old,
                        "AUREMER-naive-recent": naive_recent,
                    }
                }
            )
            mock_store.async_save = AsyncMock()
            await coordinator.async_load_seen_incidents()

        # Old (naive timezone) should be cleaned up, recent kept
        assert "AUREMER-naive-old" not in coordinator._seen_incident_ids
        assert "AUREMER-naive-recent" in coordinator._seen_incident_ids

    async def test_migrate_v1_to_v2_format(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test migrating from v1 (list) to v2 (dict with timestamps) format."""
        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        with patch.object(coordinator, "_store") as mock_store:
            # v1 format: list of IDs
            mock_store.async_load = AsyncMock(
                return_value={"seen_ids": ["AUREMER-existing1", "AUREMER-existing2"]}
            )
            mock_store.async_save = AsyncMock()
            await coordinator.async_load_seen_incidents()

        # IDs should be loaded and tracked
        assert "AUREMER-existing1" in coordinator._seen_incident_ids
        assert "AUREMER-existing2" in coordinator._seen_incident_ids

    async def test_v2_format_saves_with_timestamps(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
        sample_api_response_single: dict[str, Any],
    ) -> None:
        """Test that saving uses v2 format with timestamps."""
        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=sample_api_response_single
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        with patch.object(coordinator, "_store") as mock_store:
            mock_store.async_load = AsyncMock(return_value=None)
            mock_store.async_save = AsyncMock()

            await coordinator._async_update_data()

            # Check that save was called with v2 format
            mock_store.async_save.assert_called()
            saved_data = mock_store.async_save.call_args[0][0]
            assert "seen_incidents" in saved_data
            assert isinstance(saved_data["seen_incidents"], dict)
            # Each entry should have an ISO timestamp
            for _incident_id, timestamp in saved_data["seen_incidents"].items():
                assert isinstance(timestamp, str)
                # Should parse as ISO format
                datetime.fromisoformat(timestamp)

    async def test_cleanup_threshold_configurable(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test that cleanup uses SEEN_INCIDENT_RETENTION_DAYS constant."""
        from custom_components.abcemergency.coordinator import (
            SEEN_INCIDENT_RETENTION_DAYS,
        )

        # Verify constant exists and is reasonable
        assert isinstance(SEEN_INCIDENT_RETENTION_DAYS, int)
        assert SEEN_INCIDENT_RETENTION_DAYS >= 7  # At least a week
        assert SEEN_INCIDENT_RETENTION_DAYS <= 365  # At most a year

    async def test_cleanup_handles_invalid_timestamps(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test cleanup handles invalid timestamp formats gracefully."""
        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        now = datetime.now(UTC)
        recent_date = now.isoformat()

        with patch.object(coordinator, "_store") as mock_store:
            mock_store.async_load = AsyncMock(
                return_value={
                    "seen_incidents": {
                        "AUREMER-valid": recent_date,
                        "AUREMER-invalid": "not-a-date",
                    }
                }
            )
            mock_store.async_save = AsyncMock()
            await coordinator.async_load_seen_incidents()

        # Valid one should be kept, invalid one should be removed
        assert "AUREMER-valid" in coordinator._seen_incident_ids
        assert "AUREMER-invalid" not in coordinator._seen_incident_ids

    async def test_update_refreshes_timestamp_for_existing_incidents(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
        sample_api_response_single: dict[str, Any],
        freezer: FrozenDateTimeFactory,
    ) -> None:
        """Test that refreshing updates timestamps for existing incidents."""
        from datetime import timedelta

        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=sample_api_response_single
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        # Load with old timestamp
        old_time = datetime.now(UTC) - timedelta(days=20)
        incident_id = sample_api_response_single["emergencies"][0]["id"]

        with patch.object(coordinator, "_store") as mock_store:
            mock_store.async_load = AsyncMock(
                return_value={
                    "seen_incidents": {
                        incident_id: old_time.isoformat(),
                    }
                }
            )
            mock_store.async_save = AsyncMock()
            await coordinator.async_load_seen_incidents()

            # Do an update - this should refresh the timestamp
            await coordinator._async_update_data()

            # Check that save was called with updated timestamp
            mock_store.async_save.assert_called()
            saved_data = mock_store.async_save.call_args[0][0]
            new_timestamp = datetime.fromisoformat(saved_data["seen_incidents"][incident_id])
            # New timestamp should be more recent than old one
            assert new_timestamp > old_time
