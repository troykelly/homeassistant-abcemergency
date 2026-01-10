"""Tests for ABC Emergency coordinator."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.helpers.update_coordinator import UpdateFailed
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
    AlertLevel,
)
from custom_components.abcemergency.coordinator import ABCEmergencyCoordinator
from custom_components.abcemergency.exceptions import (
    ABCEmergencyAPIError,
    ABCEmergencyConnectionError,
)
from custom_components.abcemergency.models import CoordinatorData, EmergencyIncident

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


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
    )


@pytest.fixture
def mock_config_entry_zone() -> MockConfigEntry:
    """Create a mock config entry for zone mode."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE,
            CONF_ZONE_NAME: "Home",
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
    )


def _make_feature(emergency_id: str, state: str) -> dict:
    """Create a minimal feature object for testing state filtering."""
    return {
        "type": "Feature",
        "id": emergency_id,
        "geometry": {"type": "Point", "coordinates": [151.0, -33.87]},
        "properties": {
            "id": emergency_id,
            "state": state,
            "headline": "Test",
        },
    }


@pytest.fixture
def sample_api_response() -> dict:
    """Provide a sample API response with multiple incidents."""
    return {
        "emergencies": [
            {
                "id": "AUREMER-emergency1",
                "headline": "Critical Fire",
                "to": "/emergency/warning/AUREMER-emergency1",
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
                    "crs": {
                        "type": "name",
                        "properties": {"name": "EPSG:4326"},
                    },
                    "type": "GeometryCollection",
                    "geometries": [
                        # About 20km from Sydney CBD
                        {"type": "Point", "coordinates": [151.0, -33.87]},
                    ],
                },
            },
            {
                "id": "AUREMER-warning2",
                "headline": "Watch Fire",
                "to": "/emergency/warning/AUREMER-warning2",
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
                "eventLabelPrepared": {
                    "icon": "fire",
                    "labelText": "Bushfire",
                },
                "cardBody": {
                    "type": "Bush Fire",
                    "size": "100 ha",
                    "status": "Being controlled",
                    "source": "NSW Rural Fire Service",
                },
                "geometry": {
                    "crs": {
                        "type": "name",
                        "properties": {"name": "EPSG:4326"},
                    },
                    "type": "GeometryCollection",
                    "geometries": [
                        # About 100km from Sydney CBD
                        {"type": "Point", "coordinates": [150.5, -33.5]},
                    ],
                },
            },
            {
                "id": "AUREMER-flood3",
                "headline": "Flood Warning",
                "to": "/emergency/warning/AUREMER-flood3",
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
                "eventLabelPrepared": {
                    "icon": "weather",
                    "labelText": "Storm",
                },
                "cardBody": {
                    "type": "Flood/Storm/Tree Down",
                    "size": None,
                    "status": "Active",
                    "source": "New South Wales State Emergency Service",
                },
                "geometry": {
                    "crs": {
                        "type": "name",
                        "properties": {"name": "EPSG:4326"},
                    },
                    "type": "GeometryCollection",
                    "geometries": [
                        # Far away (about 400km)
                        {"type": "Point", "coordinates": [148.0, -35.0]},
                    ],
                },
            },
        ],
        "features": [
            _make_feature("AUREMER-emergency1", "nsw"),
            _make_feature("AUREMER-warning2", "nsw"),
            _make_feature("AUREMER-flood3", "nsw"),
        ],
        "mapBound": [[140.0, -38.0], [154.0, -28.0]],
        "stateName": "nsw",
        "incidentsNumber": 3,
        "stateCount": 125,
    }


@pytest.fixture
def empty_api_response() -> dict:
    """Provide an empty API response."""
    return {
        "emergencies": [],
        "features": [],
        "mapBound": [[140.0, -38.0], [154.0, -28.0]],
        "stateName": "nsw",
        "incidentsNumber": 0,
        "stateCount": 0,
    }


class TestCoordinatorInitState:
    """Test coordinator initialization for state mode."""

    def test_init_stores_state_configuration(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test coordinator stores state configuration correctly."""
        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        assert coordinator._instance_type == INSTANCE_TYPE_STATE
        assert coordinator.instance_type == INSTANCE_TYPE_STATE
        assert coordinator._state == "nsw"
        assert coordinator._latitude is None
        assert coordinator._longitude is None

    def test_init_sets_update_interval(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test coordinator sets correct update interval."""
        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        assert coordinator.update_interval == timedelta(seconds=300)


class TestCoordinatorInitZone:
    """Test coordinator initialization for zone mode."""

    def test_init_stores_zone_configuration(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
    ) -> None:
        """Test coordinator stores zone configuration correctly."""
        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        assert coordinator._instance_type == INSTANCE_TYPE_ZONE
        assert coordinator._latitude == -33.8688
        assert coordinator._longitude == 151.2093
        assert coordinator._state is None


class TestCoordinatorInitPerson:
    """Test coordinator initialization for person mode."""

    def test_init_stores_person_configuration(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_person: MockConfigEntry,
    ) -> None:
        """Test coordinator stores person configuration correctly."""
        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_person,
            instance_type=INSTANCE_TYPE_PERSON,
            person_entity_id="person.john",
        )

        assert coordinator._instance_type == INSTANCE_TYPE_PERSON
        assert coordinator._person_entity_id == "person.john"


class TestCoordinatorUpdateStateMode:
    """Test coordinator update functionality for state mode."""

    async def test_successful_update_state_mode(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
        sample_api_response: dict,
    ) -> None:
        """Test successful data update for state mode."""
        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=sample_api_response)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        data = await coordinator._async_update_data()

        assert isinstance(data, CoordinatorData)
        assert data.total_count == 3
        assert data.instance_type == INSTANCE_TYPE_STATE
        assert data.nearby_count is None  # Not applicable for state mode
        mock_client.async_get_emergencies_by_state.assert_called_once_with("nsw")

    async def test_empty_response_state_mode(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
        empty_api_response: dict,
    ) -> None:
        """Test handling of empty response in state mode."""
        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=empty_api_response)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        data = await coordinator._async_update_data()

        assert data.total_count == 0
        assert data.incidents == []

    async def test_connection_error_raises_update_failed(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test connection error raises UpdateFailed."""
        mock_client.async_get_emergencies_by_state = AsyncMock(
            side_effect=ABCEmergencyConnectionError("Connection failed")
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()

    async def test_api_error_raises_update_failed(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test API error raises UpdateFailed."""
        mock_client.async_get_emergencies_by_state = AsyncMock(
            side_effect=ABCEmergencyAPIError("API error")
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()


class TestCoordinatorUpdateZoneMode:
    """Test coordinator update functionality for zone mode."""

    async def test_successful_update_zone_mode(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
        sample_api_response: dict,
    ) -> None:
        """Test successful data update for zone mode."""
        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=sample_api_response)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        data = await coordinator._async_update_data()

        assert isinstance(data, CoordinatorData)
        assert data.total_count == 3
        assert data.instance_type == INSTANCE_TYPE_ZONE
        assert data.nearby_count is not None

    async def test_incidents_have_calculated_distances(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
        sample_api_response: dict,
    ) -> None:
        """Test incidents have distance from configured location."""
        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=sample_api_response)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        data = await coordinator._async_update_data()

        for incident in data.incidents:
            assert incident.distance_km is not None
            assert incident.distance_km >= 0

    async def test_incidents_have_bearings(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
        sample_api_response: dict,
    ) -> None:
        """Test incidents have bearing calculated."""
        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=sample_api_response)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        data = await coordinator._async_update_data()

        for incident in data.incidents:
            assert incident.bearing is not None
            assert 0 <= incident.bearing < 360
            assert incident.direction is not None
            assert incident.direction in ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

    async def test_incidents_sorted_by_distance(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
    ) -> None:
        """Test incidents are sorted by distance (nearest first)."""
        # Create response with multiple nearby bushfires (within 50km radius)
        nearby_response = {
            "emergencies": [
                {
                    "id": "AUREMER-far",
                    "headline": "Far Fire",
                    "to": "/emergency/warning/AUREMER-far",
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
                        "source": "NSW RFS",
                    },
                    "geometry": {
                        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
                        "type": "GeometryCollection",
                        "geometries": [{"type": "Point", "coordinates": [151.0, -33.87]}],  # ~20km
                    },
                },
                {
                    "id": "AUREMER-near",
                    "headline": "Near Fire",
                    "to": "/emergency/warning/AUREMER-near",
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
                    "eventLabelPrepared": {"icon": "fire", "labelText": "Bushfire"},
                    "cardBody": {
                        "type": "Bush Fire",
                        "size": "100 ha",
                        "status": "Being controlled",
                        "source": "NSW RFS",
                    },
                    "geometry": {
                        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
                        "type": "GeometryCollection",
                        "geometries": [{"type": "Point", "coordinates": [151.25, -33.87]}],  # ~5km
                    },
                },
            ],
            "features": [],
            "mapBound": [[140.0, -38.0], [154.0, -28.0]],
            "stateName": "nsw",
            "incidentsNumber": 2,
            "stateCount": 125,
        }
        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=nearby_response)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        data = await coordinator._async_update_data()

        # Both incidents should be within 50km bushfire radius
        assert len(data.incidents) == 2
        distances = [i.distance_km for i in data.incidents]
        assert distances == sorted(distances)

    async def test_nearest_incident_identified(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
        sample_api_response: dict,
    ) -> None:
        """Test nearest incident is correctly identified."""
        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=sample_api_response)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        data = await coordinator._async_update_data()

        assert data.nearest_incident is not None
        assert data.nearest_incident == data.incidents[0]
        assert data.nearest_distance_km == data.incidents[0].distance_km


class TestCoordinatorUpdatePersonMode:
    """Test coordinator update functionality for person mode."""

    async def test_successful_update_person_mode(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_person: MockConfigEntry,
        sample_api_response: dict,
    ) -> None:
        """Test successful data update for person mode."""
        # Set up person entity with location
        hass.states.async_set(
            "person.john",
            "home",
            {"latitude": -33.8688, "longitude": 151.2093},
        )

        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=sample_api_response)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_person,
            instance_type=INSTANCE_TYPE_PERSON,
            person_entity_id="person.john",
        )

        data = await coordinator._async_update_data()

        assert isinstance(data, CoordinatorData)
        assert data.instance_type == INSTANCE_TYPE_PERSON
        assert data.location_available is True

    async def test_person_no_location_returns_empty(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_person: MockConfigEntry,
    ) -> None:
        """Test person mode with no location returns empty data."""
        # Set up person entity without location
        hass.states.async_set("person.john", "unknown", {})

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_person,
            instance_type=INSTANCE_TYPE_PERSON,
            person_entity_id="person.john",
        )

        data = await coordinator._async_update_data()

        assert data.total_count == 0
        assert data.location_available is False

    async def test_person_entity_not_found_raises_error(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_person: MockConfigEntry,
    ) -> None:
        """Test person entity not found raises UpdateFailed."""
        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_person,
            instance_type=INSTANCE_TYPE_PERSON,
            person_entity_id="person.nonexistent",
        )

        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()


class TestAlertLevelAggregation:
    """Test alert level aggregation."""

    async def test_highest_alert_level_extreme(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
        sample_api_response: dict,
    ) -> None:
        """Test highest alert level is extreme when present in nearby."""
        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=sample_api_response)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        data = await coordinator._async_update_data()

        # The first incident (extreme level) is nearby (~20km)
        assert data.highest_alert_level == AlertLevel.EMERGENCY

    async def test_highest_alert_level_empty_when_no_nearby(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
        sample_api_response: dict,
    ) -> None:
        """Test highest alert level is empty when no nearby incidents."""
        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=sample_api_response)

        # Create entry with very small radius
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE,
                CONF_ZONE_NAME: "Home",
                CONF_LATITUDE: -33.8688,
                CONF_LONGITUDE: 151.2093,
                CONF_RADIUS_BUSHFIRE: 1,  # 1km - too small
                CONF_RADIUS_EARTHQUAKE: 1,
                CONF_RADIUS_STORM: 1,
                CONF_RADIUS_FLOOD: 1,
                CONF_RADIUS_FIRE: 1,
                CONF_RADIUS_HEAT: 1,
                CONF_RADIUS_OTHER: 1,
            },
            unique_id="abc_emergency_zone_test",
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            entry,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        data = await coordinator._async_update_data()

        # With 1km radius, no incidents should be nearby
        assert data.highest_alert_level == ""


class TestIncidentsByType:
    """Test incidents grouped by type."""

    async def test_incidents_by_type_counts(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
        sample_api_response: dict,
    ) -> None:
        """Test incidents are correctly grouped by type."""
        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=sample_api_response)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        data = await coordinator._async_update_data()

        assert "Bushfire" in data.incidents_by_type
        assert data.incidents_by_type["Bushfire"] == 2
        assert "Storm" in data.incidents_by_type
        assert data.incidents_by_type["Storm"] == 1


class TestGeometryExtraction:
    """Test geometry extraction edge cases."""

    async def test_multipolygon_geometry_extracts_centroid(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test MultiPolygon geometry uses centroid for location."""
        bom_response = {
            "emergencies": [
                {
                    "id": "AUREMER-bom-warning",
                    "headline": "Severe Heatwave Warning",
                    "to": "/emergency/warning/AUREMER-bom-warning",
                    "alertLevelInfoPrepared": {
                        "text": "",
                        "level": "severe",
                        "style": "minor",
                    },
                    "emergencyTimestampPrepared": {
                        "date": "2025-12-06T03:00:00+00:00",
                        "formattedTime": "2:00:00 pm AEDT",
                        "prefix": "Effective from",
                        "updatedTime": "2025-12-06T03:30:00.00+00:00",
                    },
                    "eventLabelPrepared": {
                        "icon": "heat",
                        "labelText": "Heatwave",
                    },
                    "cardBody": {
                        "type": None,
                        "size": None,
                        "status": "Active",
                        "source": "Australian Government Bureau of Meteorology",
                    },
                    "geometry": {
                        "crs": {
                            "type": "name",
                            "properties": {"name": "EPSG:4326"},
                        },
                        "type": "MultiPolygon",
                        "coordinates": [
                            [
                                [
                                    [150.0, -33.0],
                                    [151.0, -33.0],
                                    [151.0, -34.0],
                                    [150.0, -34.0],
                                    [150.0, -33.0],
                                ]
                            ]
                        ],
                    },
                }
            ],
            "features": [],
            "mapBound": [[149.0, -35.0], [152.0, -32.0]],
            "stateName": "nsw",
            "incidentsNumber": 1,
            "stateCount": 1,
        }

        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=bom_response)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        data = await coordinator._async_update_data()

        assert len(data.incidents) == 1
        incident = data.incidents[0]
        # Centroid of the polygon
        assert incident.location.latitude == pytest.approx(-33.4, abs=0.1)
        assert incident.location.longitude == pytest.approx(150.4, abs=0.1)

    async def test_direct_point_geometry(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test direct Point geometry type."""
        response = {
            "emergencies": [
                {
                    "id": "AUREMER-point",
                    "headline": "Point Warning",
                    "to": "/emergency/warning/AUREMER-point",
                    "alertLevelInfoPrepared": {
                        "text": "",
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
                    "cardBody": {"type": None, "size": None, "status": "Active", "source": "BOM"},
                    "geometry": {
                        "type": "Point",
                        "coordinates": [151.0, -33.5],
                    },
                }
            ],
            "features": [],
            "mapBound": [[149.0, -35.0], [152.0, -32.0]],
            "stateName": "nsw",
            "incidentsNumber": 1,
            "stateCount": 1,
        }

        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=response)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        data = await coordinator._async_update_data()

        assert len(data.incidents) == 1
        incident = data.incidents[0]
        assert incident.location.latitude == -33.5
        assert incident.location.longitude == 151.0

    async def test_unknown_geometry_type_skipped(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test unknown geometry type results in skipped incident."""
        response = {
            "emergencies": [
                {
                    "id": "AUREMER-unknown",
                    "headline": "Unknown Geometry",
                    "to": "/emergency/warning/AUREMER-unknown",
                    "alertLevelInfoPrepared": {
                        "text": "",
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
                    "cardBody": {"type": None, "size": None, "status": "Active", "source": "BOM"},
                    "geometry": {
                        "type": "LineString",  # Unknown/unsupported type
                        "coordinates": [[150.0, -33.0], [151.0, -34.0]],
                    },
                }
            ],
            "features": [],
            "mapBound": [[149.0, -35.0], [152.0, -32.0]],
            "stateName": "nsw",
            "incidentsNumber": 1,
            "stateCount": 0,
        }

        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=response)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        data = await coordinator._async_update_data()

        # Incident should be skipped due to unknown geometry
        assert len(data.incidents) == 0


class TestModels:
    """Test model classes."""

    def test_coordinator_data_defaults(self) -> None:
        """Test CoordinatorData has correct defaults."""
        data = CoordinatorData()

        assert data.incidents == []
        assert data.total_count == 0
        assert data.nearby_count is None  # Changed from 0 to None
        assert data.nearest_distance_km is None
        assert data.nearest_incident is None
        assert data.highest_alert_level == ""
        assert data.incidents_by_type == {}
        assert data.instance_type == "state"

    def test_emergency_incident_optional_fields(self) -> None:
        """Test EmergencyIncident optional fields."""
        from custom_components.abcemergency.models import Coordinate

        incident = EmergencyIncident(
            id="test",
            headline="Test",
            alert_level="minor",
            alert_text="",
            event_type="Test",
            event_icon="other",
            status=None,
            size=None,
            source="Test",
            location=Coordinate(latitude=-33.0, longitude=151.0),
            updated=datetime.now(),
        )

        assert incident.distance_km is None
        assert incident.bearing is None
        assert incident.direction is None

    def test_emergency_incident_geometry_fields_defaults(self) -> None:
        """Test EmergencyIncident new geometry fields have correct defaults."""
        from custom_components.abcemergency.models import Coordinate

        incident = EmergencyIncident(
            id="test",
            headline="Test",
            alert_level="minor",
            alert_text="",
            event_type="Test",
            event_icon="other",
            status=None,
            size=None,
            source="Test",
            location=Coordinate(latitude=-33.0, longitude=151.0),
            updated=datetime.now(),
        )

        # New geometry fields should default to None/False
        assert incident.geometry_type is None
        assert incident.polygons is None
        assert incident.has_polygon is False

    def test_emergency_incident_with_polygon_data(self) -> None:
        """Test EmergencyIncident can store polygon geometry data."""
        from custom_components.abcemergency.models import Coordinate

        polygon_data = [
            {
                "outer_ring": [
                    [151.0, -33.0],
                    [152.0, -33.0],
                    [152.0, -34.0],
                    [151.0, -34.0],
                    [151.0, -33.0],
                ],
                "inner_rings": None,
            }
        ]

        incident = EmergencyIncident(
            id="test-polygon",
            headline="Test With Polygon",
            alert_level="severe",
            alert_text="Watch and Act",
            event_type="Bushfire",
            event_icon="fire",
            status="Out of control",
            size="100 ha",
            source="NSW Rural Fire Service",
            location=Coordinate(latitude=-33.5, longitude=151.5),
            updated=datetime.now(),
            geometry_type="Polygon",
            polygons=polygon_data,
            has_polygon=True,
        )

        assert incident.geometry_type == "Polygon"
        assert incident.polygons is not None
        assert len(incident.polygons) == 1
        assert incident.has_polygon is True


class TestCoordinatorEdgeCases:
    """Test edge cases and error handling in coordinator."""

    async def test_unknown_instance_type_raises_error(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
    ) -> None:
        """Test unknown instance type raises UpdateFailed."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: "unknown",
            },
            unique_id="abc_emergency_unknown",
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            entry,
            instance_type="unknown",  # type: ignore[arg-type]
        )

        with pytest.raises(UpdateFailed, match="Unknown instance type"):
            await coordinator._async_update_data()

    async def test_state_mode_no_state_configured_raises_error(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
    ) -> None:
        """Test state mode with no state configured raises UpdateFailed."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_STATE,
            },
            unique_id="abc_emergency_state_empty",
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            entry,
            instance_type=INSTANCE_TYPE_STATE,
            state=None,
        )

        with pytest.raises(UpdateFailed, match="No state configured"):
            await coordinator._async_update_data()

    async def test_zone_mode_no_location_raises_error(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
    ) -> None:
        """Test zone mode with no location raises UpdateFailed."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE,
                CONF_ZONE_NAME: "Test",
            },
            unique_id="abc_emergency_zone_test",
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            entry,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=None,
            longitude=None,
        )

        with pytest.raises(UpdateFailed, match="No location configured"):
            await coordinator._async_update_data()

    async def test_zone_mode_outside_australia_raises_error(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
    ) -> None:
        """Test zone mode with coordinates outside Australia raises UpdateFailed."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE,
                CONF_ZONE_NAME: "London",
                CONF_LATITUDE: 51.5074,  # London
                CONF_LONGITUDE: -0.1278,
            },
            unique_id="abc_emergency_zone_london",
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            entry,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=51.5074,
            longitude=-0.1278,
        )

        with pytest.raises(UpdateFailed, match="Could not determine state"):
            await coordinator._async_update_data()

    async def test_zone_mode_connection_error(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
    ) -> None:
        """Test zone mode connection error raises UpdateFailed."""
        mock_client.async_get_emergencies_by_state = AsyncMock(
            side_effect=ABCEmergencyConnectionError("Connection failed")
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        with pytest.raises(UpdateFailed, match="Connection error"):
            await coordinator._async_update_data()

    async def test_zone_mode_api_error(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
    ) -> None:
        """Test zone mode API error raises UpdateFailed."""
        mock_client.async_get_emergencies_by_state = AsyncMock(
            side_effect=ABCEmergencyAPIError("API error")
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        with pytest.raises(UpdateFailed, match="API error"):
            await coordinator._async_update_data()

    async def test_person_mode_no_entity_configured_raises_error(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
    ) -> None:
        """Test person mode with no entity configured raises UpdateFailed."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_PERSON,
            },
            unique_id="abc_emergency_person_empty",
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            entry,
            instance_type=INSTANCE_TYPE_PERSON,
            person_entity_id=None,
        )

        with pytest.raises(UpdateFailed, match="No person entity configured"):
            await coordinator._async_update_data()

    async def test_person_mode_outside_australia_returns_empty(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_person: MockConfigEntry,
    ) -> None:
        """Test person mode outside Australia returns empty data with location."""
        # Set up person entity in London
        hass.states.async_set(
            "person.john",
            "away",
            {"latitude": 51.5074, "longitude": -0.1278},  # London
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_person,
            instance_type=INSTANCE_TYPE_PERSON,
            person_entity_id="person.john",
        )

        data = await coordinator._async_update_data()

        assert data.total_count == 0
        assert data.location_available is True
        assert data.current_latitude == 51.5074
        assert data.current_longitude == -0.1278

    async def test_person_mode_connection_error(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_person: MockConfigEntry,
    ) -> None:
        """Test person mode connection error raises UpdateFailed."""
        hass.states.async_set(
            "person.john",
            "home",
            {"latitude": -33.8688, "longitude": 151.2093},
        )

        mock_client.async_get_emergencies_by_state = AsyncMock(
            side_effect=ABCEmergencyConnectionError("Connection failed")
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_person,
            instance_type=INSTANCE_TYPE_PERSON,
            person_entity_id="person.john",
        )

        with pytest.raises(UpdateFailed, match="Connection error"):
            await coordinator._async_update_data()

    async def test_person_mode_api_error(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_person: MockConfigEntry,
    ) -> None:
        """Test person mode API error raises UpdateFailed."""
        hass.states.async_set(
            "person.john",
            "home",
            {"latitude": -33.8688, "longitude": 151.2093},
        )

        mock_client.async_get_emergencies_by_state = AsyncMock(
            side_effect=ABCEmergencyAPIError("API error")
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_person,
            instance_type=INSTANCE_TYPE_PERSON,
            person_entity_id="person.john",
        )

        with pytest.raises(UpdateFailed, match="API error"):
            await coordinator._async_update_data()

    async def test_timestamp_parsing_error_uses_now(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test timestamp parsing error uses current time."""
        response = {
            "emergencies": [
                {
                    "id": "AUREMER-test",
                    "headline": "Test Warning",
                    "to": "/emergency/warning/AUREMER-test",
                    "alertLevelInfoPrepared": {
                        "text": "",
                        "level": "moderate",
                        "style": "moderate",
                    },
                    "emergencyTimestampPrepared": {
                        "date": "invalid-date",
                        "formattedTime": "invalid",
                        "prefix": "Effective from",
                        "updatedTime": "not-a-valid-timestamp",  # Invalid
                    },
                    "eventLabelPrepared": {"icon": "weather", "labelText": "Storm"},
                    "cardBody": {"type": None, "size": None, "status": "Active", "source": "BOM"},
                    "geometry": {
                        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
                        "type": "GeometryCollection",
                        "geometries": [{"type": "Point", "coordinates": [151.0, -33.5]}],
                    },
                }
            ],
            "features": [],
            "mapBound": [[149.0, -35.0], [152.0, -32.0]],
            "stateName": "nsw",
            "incidentsNumber": 1,
            "stateCount": 1,
        }

        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=response)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        data = await coordinator._async_update_data()

        assert len(data.incidents) == 1
        # Should have used current time
        assert data.incidents[0].updated is not None


class TestPolygonCentroidCalculation:
    """Test polygon centroid calculation methods."""

    async def test_polygon_centroid_empty_coords(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test polygon with empty coordinates returns None."""
        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        result = coordinator._calculate_polygon_centroid(
            {
                "type": "Polygon",
                "coordinates": [],
                "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
            }
        )
        assert result is None

    async def test_multipolygon_centroid_empty_coords(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test multipolygon with empty coordinates returns None."""
        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        result = coordinator._calculate_multipolygon_centroid(
            {
                "type": "MultiPolygon",
                "coordinates": [],
                "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
            }
        )
        assert result is None

    async def test_polygon_from_polygon_empty_coords(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test nested polygon with empty coordinates returns None."""
        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        result = coordinator._calculate_polygon_centroid_from_polygon(
            {"type": "Polygon", "coordinates": []}
        )
        assert result is None

    async def test_polygon_centroid_no_valid_points(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test polygon with no valid points returns None."""
        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        result = coordinator._calculate_polygon_centroid(
            {
                "type": "Polygon",
                "coordinates": [[]],
                "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
            }
        )
        assert result is None

    async def test_multipolygon_centroid_no_valid_points(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test multipolygon with no valid points returns None."""
        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        result = coordinator._calculate_multipolygon_centroid(
            {
                "type": "MultiPolygon",
                "coordinates": [[[]]],
                "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
            }
        )
        assert result is None

    async def test_polygon_from_polygon_no_valid_points(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test nested polygon with no valid points returns None."""
        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        result = coordinator._calculate_polygon_centroid_from_polygon(
            {"type": "Polygon", "coordinates": [[]]}
        )
        assert result is None

    async def test_multipolygon_centroid_valid(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test multipolygon with valid coordinates returns centroid."""
        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        result = coordinator._calculate_multipolygon_centroid(
            {
                "type": "MultiPolygon",
                "coordinates": [
                    [
                        [
                            [150.0, -33.0],
                            [151.0, -33.0],
                            [151.0, -34.0],
                            [150.0, -34.0],
                            [150.0, -33.0],
                        ]
                    ]
                ],
                "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
            }
        )
        assert result is not None
        assert result.latitude == pytest.approx(-33.4, abs=0.1)
        assert result.longitude == pytest.approx(150.4, abs=0.1)

    async def test_nested_polygon_centroid_valid(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test nested polygon geometry with valid coordinates returns centroid."""
        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        result = coordinator._calculate_polygon_centroid_from_polygon(
            {
                "type": "Polygon",
                "coordinates": [
                    [[150.0, -33.0], [151.0, -33.0], [151.0, -34.0], [150.0, -34.0], [150.0, -33.0]]
                ],
            }
        )
        assert result is not None
        assert result.latitude == pytest.approx(-33.4, abs=0.1)
        assert result.longitude == pytest.approx(150.4, abs=0.1)

    async def test_polygon_centroid_valid(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test top-level polygon with valid coordinates returns centroid."""
        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        result = coordinator._calculate_polygon_centroid(
            {
                "type": "Polygon",
                "coordinates": [
                    [[150.0, -33.0], [151.0, -33.0], [151.0, -34.0], [150.0, -34.0], [150.0, -33.0]]
                ],
                "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
            }
        )
        assert result is not None
        assert result.latitude == pytest.approx(-33.4, abs=0.1)
        assert result.longitude == pytest.approx(150.4, abs=0.1)


class TestGeometryCoordinateExtraction:
    """Test coordinate extraction from different geometry types."""

    async def test_extract_location_from_polygon(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test location extraction from top-level Polygon geometry."""
        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        geometry = {
            "type": "Polygon",
            "coordinates": [
                [[150.0, -33.0], [151.0, -33.0], [151.0, -34.0], [150.0, -34.0], [150.0, -33.0]]
            ],
            "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        }

        location, geom_type, polygons = coordinator._extract_location_and_geometry(geometry)
        assert location is not None
        assert location.latitude == pytest.approx(-33.4, abs=0.1)
        assert location.longitude == pytest.approx(150.4, abs=0.1)
        assert geom_type == "Polygon"
        assert polygons is not None

    async def test_extract_location_from_geometry_collection_polygon_fallback(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test location extraction from GeometryCollection falls back to polygon."""
        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        geometry = {
            "type": "GeometryCollection",
            "geometries": [
                # No Point geometry, should fall back to Polygon
                {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [150.0, -33.0],
                            [151.0, -33.0],
                            [151.0, -34.0],
                            [150.0, -34.0],
                            [150.0, -33.0],
                        ]
                    ],
                }
            ],
            "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        }

        location, geom_type, polygons = coordinator._extract_location_and_geometry(geometry)
        assert location is not None
        assert location.latitude == pytest.approx(-33.4, abs=0.1)
        assert location.longitude == pytest.approx(150.4, abs=0.1)
        assert geom_type == "GeometryCollection"
        assert polygons is not None


class TestPolygonGeometryStorage:
    """Test storing polygon geometry in EmergencyIncident."""

    async def test_polygon_geometry_stored_in_incident(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test that polygon geometry is stored when processing incidents."""
        response = {
            "emergencies": [
                {
                    "id": "AUREMER-polygon-test",
                    "headline": "Test Bushfire With Polygon",
                    "to": "/emergency/warning/AUREMER-polygon-test",
                    "alertLevelInfoPrepared": {
                        "text": "Watch and Act",
                        "level": "severe",
                        "style": "severe",
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
                        "crs": {
                            "type": "name",
                            "properties": {"name": "EPSG:4326"},
                        },
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [150.0, -33.0],
                                [151.0, -33.0],
                                [151.0, -34.0],
                                [150.0, -34.0],
                                [150.0, -33.0],
                            ]
                        ],
                    },
                }
            ],
            "features": [],
            "mapBound": [[149.0, -35.0], [152.0, -32.0]],
            "stateName": "nsw",
            "incidentsNumber": 1,
            "stateCount": 1,
        }

        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=response)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        data = await coordinator._async_update_data()

        assert len(data.incidents) == 1
        incident = data.incidents[0]
        assert incident.geometry_type == "Polygon"
        assert incident.has_polygon is True
        assert incident.polygons is not None
        assert len(incident.polygons) == 1
        assert len(incident.polygons[0]["outer_ring"]) == 5
        assert incident.polygons[0]["inner_rings"] is None

    async def test_point_geometry_has_no_polygon(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test that Point geometry results in has_polygon=False."""
        response = {
            "emergencies": [
                {
                    "id": "AUREMER-point-test",
                    "headline": "Test Fire Point",
                    "to": "/emergency/warning/AUREMER-point-test",
                    "alertLevelInfoPrepared": {
                        "text": "Advice",
                        "level": "moderate",
                        "style": "moderate",
                    },
                    "emergencyTimestampPrepared": {
                        "date": "2025-12-06T05:34:00+00:00",
                        "formattedTime": "4:34:00 pm AEDT",
                        "prefix": "Effective from",
                        "updatedTime": "2025-12-06T05:53:02.97994+00:00",
                    },
                    "eventLabelPrepared": {
                        "icon": "fire",
                        "labelText": "Fire",
                    },
                    "cardBody": {
                        "type": "Structure Fire",
                        "size": None,
                        "status": "Under control",
                        "source": "Fire and Rescue NSW",
                    },
                    "geometry": {
                        "crs": {
                            "type": "name",
                            "properties": {"name": "EPSG:4326"},
                        },
                        "type": "Point",
                        "coordinates": [151.2, -33.9],
                    },
                }
            ],
            "features": [],
            "mapBound": [[149.0, -35.0], [152.0, -32.0]],
            "stateName": "nsw",
            "incidentsNumber": 1,
            "stateCount": 1,
        }

        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=response)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        data = await coordinator._async_update_data()

        assert len(data.incidents) == 1
        incident = data.incidents[0]
        assert incident.geometry_type == "Point"
        assert incident.has_polygon is False
        assert incident.polygons is None

    async def test_multipolygon_geometry_stores_all_polygons(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test that MultiPolygon geometry stores all polygons."""
        response = {
            "emergencies": [
                {
                    "id": "AUREMER-multi-test",
                    "headline": "Severe Heatwave Warning",
                    "to": "/emergency/warning/AUREMER-multi-test",
                    "alertLevelInfoPrepared": {
                        "text": "",
                        "level": "severe",
                        "style": "minor",
                    },
                    "emergencyTimestampPrepared": {
                        "date": "2025-12-06T03:00:00+00:00",
                        "formattedTime": "2:00:00 pm AEDT",
                        "prefix": "Effective from",
                        "updatedTime": "2025-12-06T03:30:00.00+00:00",
                    },
                    "eventLabelPrepared": {
                        "icon": "heat",
                        "labelText": "Heatwave",
                    },
                    "cardBody": {
                        "type": None,
                        "size": None,
                        "status": "Active",
                        "source": "Australian Government Bureau of Meteorology",
                    },
                    "geometry": {
                        "crs": {
                            "type": "name",
                            "properties": {"name": "EPSG:4326"},
                        },
                        "type": "MultiPolygon",
                        "coordinates": [
                            [
                                [
                                    [150.0, -33.0],
                                    [151.0, -33.0],
                                    [151.0, -34.0],
                                    [150.0, -34.0],
                                    [150.0, -33.0],
                                ]
                            ],
                            [
                                [
                                    [152.0, -35.0],
                                    [153.0, -35.0],
                                    [153.0, -36.0],
                                    [152.0, -36.0],
                                    [152.0, -35.0],
                                ]
                            ],
                        ],
                    },
                }
            ],
            "features": [],
            "mapBound": [[149.0, -37.0], [154.0, -32.0]],
            "stateName": "nsw",
            "incidentsNumber": 1,
            "stateCount": 1,
        }

        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=response)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        data = await coordinator._async_update_data()

        assert len(data.incidents) == 1
        incident = data.incidents[0]
        assert incident.geometry_type == "MultiPolygon"
        assert incident.has_polygon is True
        assert incident.polygons is not None
        assert len(incident.polygons) == 2

    async def test_geometry_collection_stores_polygon(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test that GeometryCollection extracts and stores the polygon."""
        response = {
            "emergencies": [
                {
                    "id": "AUREMER-collection-test",
                    "headline": "Test With Point and Polygon",
                    "to": "/emergency/warning/AUREMER-collection-test",
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
                        "size": "1000 ha",
                        "status": "Out of control",
                        "source": "NSW Rural Fire Service",
                    },
                    "geometry": {
                        "crs": {
                            "type": "name",
                            "properties": {"name": "EPSG:4326"},
                        },
                        "type": "GeometryCollection",
                        "geometries": [
                            {"type": "Point", "coordinates": [150.5, -33.5]},
                            {
                                "type": "Polygon",
                                "coordinates": [
                                    [
                                        [150.0, -33.0],
                                        [151.0, -33.0],
                                        [151.0, -34.0],
                                        [150.0, -34.0],
                                        [150.0, -33.0],
                                    ]
                                ],
                            },
                        ],
                    },
                }
            ],
            "features": [],
            "mapBound": [[149.0, -35.0], [152.0, -32.0]],
            "stateName": "nsw",
            "incidentsNumber": 1,
            "stateCount": 1,
        }

        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=response)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        data = await coordinator._async_update_data()

        assert len(data.incidents) == 1
        incident = data.incidents[0]
        # GeometryCollection with Point + Polygon
        assert incident.geometry_type == "GeometryCollection"
        assert incident.has_polygon is True
        assert incident.polygons is not None
        assert len(incident.polygons) == 1
        # Location should come from Point
        assert incident.location.latitude == pytest.approx(-33.5, abs=0.01)
        assert incident.location.longitude == pytest.approx(150.5, abs=0.01)

    async def test_geometry_collection_polygon_only_uses_centroid(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test GeometryCollection with only Polygon (no Point) uses centroid for location."""
        response = {
            "emergencies": [
                {
                    "id": "AUREMER-polygon-only-collection",
                    "headline": "Test With Polygon Only",
                    "to": "/emergency/warning/AUREMER-polygon-only-collection",
                    "alertLevelInfoPrepared": {
                        "text": "Watch and Act",
                        "level": "severe",
                        "style": "severe",
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
                        "size": "200 ha",
                        "status": "Under control",
                        "source": "NSW Rural Fire Service",
                    },
                    "geometry": {
                        "crs": {
                            "type": "name",
                            "properties": {"name": "EPSG:4326"},
                        },
                        "type": "GeometryCollection",
                        "geometries": [
                            # No Point - only Polygon
                            {
                                "type": "Polygon",
                                "coordinates": [
                                    [
                                        [150.0, -33.0],
                                        [151.0, -33.0],
                                        [151.0, -34.0],
                                        [150.0, -34.0],
                                        [150.0, -33.0],
                                    ]
                                ],
                            },
                        ],
                    },
                }
            ],
            "features": [],
            "mapBound": [[149.0, -35.0], [152.0, -32.0]],
            "stateName": "nsw",
            "incidentsNumber": 1,
            "stateCount": 1,
        }

        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=response)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        data = await coordinator._async_update_data()

        assert len(data.incidents) == 1
        incident = data.incidents[0]
        assert incident.geometry_type == "GeometryCollection"
        assert incident.has_polygon is True
        assert incident.polygons is not None
        # Location should be calculated from polygon centroid
        # Centroid of polygon [150, 151] x [-33, -34] - using abs=0.1 tolerance
        # because centroid calculation uses triangulation, not simple average
        assert incident.location.latitude == pytest.approx(-33.4, abs=0.1)
        assert incident.location.longitude == pytest.approx(150.4, abs=0.1)


class TestContainmentDetection:
    """Test point-in-polygon containment detection in coordinator."""

    @pytest.fixture
    def api_response_with_containing_polygon(self) -> dict:
        """API response with a polygon that contains the monitored point."""
        # Polygon encompasses Sydney CBD (-33.8688, 151.2093)
        return {
            "emergencies": [
                {
                    "id": "AUREMER-containing",
                    "headline": "Bushfire Containing Sydney",
                    "to": "/emergency/warning/AUREMER-containing",
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
                        "size": "5000 ha",
                        "status": "Out of control",
                        "source": "NSW Rural Fire Service",
                    },
                    "geometry": {
                        "crs": {
                            "type": "name",
                            "properties": {"name": "EPSG:4326"},
                        },
                        "type": "Polygon",
                        "coordinates": [
                            [
                                # Large polygon around Sydney
                                [150.0, -33.0],
                                [152.0, -33.0],
                                [152.0, -35.0],
                                [150.0, -35.0],
                                [150.0, -33.0],
                            ]
                        ],
                    },
                }
            ],
            "features": [],
            "mapBound": [[149.0, -36.0], [153.0, -32.0]],
            "stateName": "nsw",
            "incidentsNumber": 1,
            "stateCount": 1,
        }

    @pytest.fixture
    def api_response_with_far_centroid_but_containing_polygon(self) -> dict:
        """API response where centroid is far but polygon still contains point.

        This tests the critical requirement from issue #73: containment must be
        checked for ALL incidents BEFORE radius filtering, because a polygon
        centroid may be far away but the polygon itself may still contain the
        monitored point.
        """
        # Large irregular polygon: centroid would be ~100km from Sydney
        # but the polygon extends to include Sydney
        return {
            "emergencies": [
                {
                    "id": "AUREMER-far-centroid",
                    "headline": "Large Bushfire Far Centroid",
                    "to": "/emergency/warning/AUREMER-far-centroid",
                    "alertLevelInfoPrepared": {
                        "text": "Watch and Act",
                        "level": "severe",
                        "style": "severe",
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
                        "size": "50000 ha",
                        "status": "Out of control",
                        "source": "NSW Rural Fire Service",
                    },
                    "geometry": {
                        "crs": {
                            "type": "name",
                            "properties": {"name": "EPSG:4326"},
                        },
                        "type": "Polygon",
                        "coordinates": [
                            [
                                # Polygon extends west and south far from Sydney
                                # but includes Sydney at the east edge
                                [148.0, -32.0],  # Far west-north
                                [152.0, -32.0],  # East-north (past Sydney longitude)
                                [152.0, -35.0],  # East-south (past Sydney latitude)
                                [148.0, -36.0],  # Far west-south
                                [148.0, -32.0],
                            ]
                        ],
                    },
                }
            ],
            "features": [],
            "mapBound": [[147.0, -37.0], [153.0, -31.0]],
            "stateName": "nsw",
            "incidentsNumber": 1,
            "stateCount": 1,
        }

    async def test_incident_contains_point_field_true_when_inside(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
        api_response_with_containing_polygon: dict,
    ) -> None:
        """Test incident.contains_point is True when monitored point is inside polygon."""
        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=api_response_with_containing_polygon
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,  # Sydney CBD
            longitude=151.2093,
        )

        data = await coordinator._async_update_data()

        assert len(data.incidents) == 1
        assert data.incidents[0].contains_point is True

    async def test_incident_contains_point_field_false_when_outside(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
    ) -> None:
        """Test incident.contains_point is False when monitored point is outside polygon.

        Note: The polygon is positioned close enough to be within radius filtering
        so the incident appears in data.incidents.
        """
        response = {
            "emergencies": [
                {
                    "id": "AUREMER-not-containing",
                    "headline": "Bushfire Near But Not Containing Sydney",
                    "to": "/emergency/warning/AUREMER-not-containing",
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
                        "type": "Polygon",
                        "coordinates": [
                            [
                                # Polygon near Sydney but NOT containing Sydney CBD
                                # This polygon is west of Sydney (~20km away)
                                [150.9, -33.7],
                                [151.1, -33.7],
                                [151.1, -34.0],
                                [150.9, -34.0],
                                [150.9, -33.7],
                            ]
                        ],
                    },
                }
            ],
            "features": [],
            "mapBound": [[150.8, -34.1], [151.2, -33.6]],
            "stateName": "nsw",
            "incidentsNumber": 1,
            "stateCount": 1,
        }
        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=response)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,  # Sydney CBD - outside the polygon
            longitude=151.2093,
        )

        data = await coordinator._async_update_data()

        assert len(data.incidents) == 1
        assert data.incidents[0].contains_point is False
        # Verify the containment summary is correct
        assert data.inside_polygon is False
        assert len(data.containing_incidents) == 0

    async def test_coordinator_data_inside_polygon_true_when_contained(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
        api_response_with_containing_polygon: dict,
    ) -> None:
        """Test CoordinatorData.inside_polygon is True when point is inside any polygon."""
        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=api_response_with_containing_polygon
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        data = await coordinator._async_update_data()

        assert data.inside_polygon is True

    async def test_coordinator_data_containing_incidents_list(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
        api_response_with_containing_polygon: dict,
    ) -> None:
        """Test CoordinatorData.containing_incidents contains incidents whose polygons contain point."""
        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=api_response_with_containing_polygon
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        data = await coordinator._async_update_data()

        assert data.containing_incidents is not None
        assert len(data.containing_incidents) == 1
        assert data.containing_incidents[0].id == "AUREMER-containing"

    async def test_inside_emergency_warning_true_when_inside_extreme(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
        api_response_with_containing_polygon: dict,
    ) -> None:
        """Test inside_emergency_warning is True when inside extreme alert polygon."""
        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=api_response_with_containing_polygon
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        data = await coordinator._async_update_data()

        assert data.inside_emergency_warning is True

    async def test_inside_watch_and_act_true_when_inside_severe(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
        api_response_with_far_centroid_but_containing_polygon: dict,
    ) -> None:
        """Test inside_watch_and_act is True when inside severe alert polygon."""
        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=api_response_with_far_centroid_but_containing_polygon
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        data = await coordinator._async_update_data()

        assert data.inside_watch_and_act is True

    async def test_inside_advice_true_when_inside_moderate(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
    ) -> None:
        """Test inside_advice is True when inside moderate alert polygon."""
        response = {
            "emergencies": [
                {
                    "id": "AUREMER-advice",
                    "headline": "Advisory Zone",
                    "to": "/emergency/warning/AUREMER-advice",
                    "alertLevelInfoPrepared": {
                        "text": "Advice",
                        "level": "moderate",
                        "style": "moderate",
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
                        "size": "100 ha",
                        "status": "Being controlled",
                        "source": "NSW RFS",
                    },
                    "geometry": {
                        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [150.0, -33.0],
                                [152.0, -33.0],
                                [152.0, -35.0],
                                [150.0, -35.0],
                                [150.0, -33.0],
                            ]
                        ],
                    },
                }
            ],
            "features": [],
            "mapBound": [[149.0, -36.0], [153.0, -32.0]],
            "stateName": "nsw",
            "incidentsNumber": 1,
            "stateCount": 1,
        }
        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=response)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        data = await coordinator._async_update_data()

        assert data.inside_advice is True

    async def test_highest_containing_alert_level(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
    ) -> None:
        """Test highest_containing_alert_level returns highest alert level among containing incidents."""
        response = {
            "emergencies": [
                {
                    "id": "AUREMER-moderate-containing",
                    "headline": "Advice Zone",
                    "to": "/emergency/warning/AUREMER-moderate-containing",
                    "alertLevelInfoPrepared": {
                        "text": "Advice",
                        "level": "moderate",
                        "style": "moderate",
                    },
                    "emergencyTimestampPrepared": {
                        "date": "2025-12-06T05:34:00+00:00",
                        "formattedTime": "4:34:00 pm AEDT",
                        "prefix": "Effective from",
                        "updatedTime": "2025-12-06T05:53:02.97994+00:00",
                    },
                    "eventLabelPrepared": {"icon": "weather", "labelText": "Storm"},
                    "cardBody": {
                        "type": "Storm",
                        "size": None,
                        "status": "Active",
                        "source": "BOM",
                    },
                    "geometry": {
                        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [150.0, -33.0],
                                [152.0, -33.0],
                                [152.0, -35.0],
                                [150.0, -35.0],
                                [150.0, -33.0],
                            ]
                        ],
                    },
                },
                {
                    "id": "AUREMER-severe-containing",
                    "headline": "Watch and Act Zone",
                    "to": "/emergency/warning/AUREMER-severe-containing",
                    "alertLevelInfoPrepared": {
                        "text": "Watch and Act",
                        "level": "severe",
                        "style": "severe",
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
                        "source": "NSW RFS",
                    },
                    "geometry": {
                        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [150.0, -33.0],
                                [152.0, -33.0],
                                [152.0, -35.0],
                                [150.0, -35.0],
                                [150.0, -33.0],
                            ]
                        ],
                    },
                },
            ],
            "features": [],
            "mapBound": [[149.0, -36.0], [153.0, -32.0]],
            "stateName": "nsw",
            "incidentsNumber": 2,
            "stateCount": 2,
        }
        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=response)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        data = await coordinator._async_update_data()

        assert data.highest_containing_alert_level == AlertLevel.WATCH_AND_ACT

    async def test_containment_checked_before_radius_filtering(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        api_response_with_far_centroid_but_containing_polygon: dict,
    ) -> None:
        """Test containment is checked for ALL incidents before radius filtering.

        CRITICAL TEST: This validates issue #73 requirement that containment
        must be checked before radius filtering. The polygon's centroid is far
        (~100km) but the polygon still contains the monitored point.
        """
        # Use small radius that would exclude based on centroid distance
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE,
                CONF_ZONE_NAME: "Home",
                CONF_LATITUDE: -33.8688,
                CONF_LONGITUDE: 151.2093,
                CONF_RADIUS_BUSHFIRE: 10,  # 10km - centroid is ~100km away
                CONF_RADIUS_EARTHQUAKE: 10,
                CONF_RADIUS_STORM: 10,
                CONF_RADIUS_FLOOD: 10,
                CONF_RADIUS_FIRE: 10,
                CONF_RADIUS_HEAT: 10,
                CONF_RADIUS_OTHER: 10,
            },
            unique_id="abc_emergency_zone_small_radius",
        )

        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=api_response_with_far_centroid_but_containing_polygon
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            entry,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        data = await coordinator._async_update_data()

        # Even with small radius, containment should be detected
        # because containment checks ALL incidents before radius filtering
        assert data.inside_polygon is True
        assert data.inside_watch_and_act is True
        assert len(data.containing_incidents) == 1

    async def test_state_mode_no_containment_fields(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test state mode has no containment detection (no monitored point)."""
        response = {
            "emergencies": [
                {
                    "id": "AUREMER-state-incident",
                    "headline": "Some Bushfire",
                    "to": "/emergency/warning/AUREMER-state-incident",
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
                        "size": "1000 ha",
                        "status": "Out of control",
                        "source": "NSW RFS",
                    },
                    "geometry": {
                        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [150.0, -33.0],
                                [152.0, -33.0],
                                [152.0, -35.0],
                                [150.0, -35.0],
                                [150.0, -33.0],
                            ]
                        ],
                    },
                }
            ],
            "features": [],
            "mapBound": [[149.0, -36.0], [153.0, -32.0]],
            "stateName": "nsw",
            "incidentsNumber": 1,
            "stateCount": 1,
        }
        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=response)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        data = await coordinator._async_update_data()

        # State mode has no monitored point, so containment fields should be empty/False
        assert data.inside_polygon is False
        assert data.inside_emergency_warning is False
        assert data.inside_watch_and_act is False
        assert data.inside_advice is False
        assert data.containing_incidents == []
        assert data.highest_containing_alert_level == ""
        # Incidents in state mode should have contains_point as None (not applicable)
        assert data.incidents[0].contains_point is None

    async def test_person_mode_containment_detection(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_person: MockConfigEntry,
        api_response_with_containing_polygon: dict,
    ) -> None:
        """Test person mode has containment detection based on person location."""
        # Set up person entity in Sydney
        hass.states.async_set(
            "person.john",
            "home",
            {"latitude": -33.8688, "longitude": 151.2093},
        )

        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=api_response_with_containing_polygon
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_person,
            instance_type=INSTANCE_TYPE_PERSON,
            person_entity_id="person.john",
        )

        data = await coordinator._async_update_data()

        assert data.inside_polygon is True
        assert data.inside_emergency_warning is True
        assert len(data.containing_incidents) == 1

    async def test_point_geometry_no_containment(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
    ) -> None:
        """Test Point geometry (no polygon) cannot contain the monitored point."""
        response = {
            "emergencies": [
                {
                    "id": "AUREMER-point-only",
                    "headline": "Point Fire",
                    "to": "/emergency/warning/AUREMER-point-only",
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
                    "eventLabelPrepared": {"icon": "fire", "labelText": "Fire"},
                    "cardBody": {
                        "type": "Structure Fire",
                        "size": None,
                        "status": "Under control",
                        "source": "FRNSW",
                    },
                    "geometry": {
                        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
                        "type": "Point",
                        "coordinates": [151.2093, -33.8688],  # At the monitored location
                    },
                }
            ],
            "features": [],
            "mapBound": [[150.0, -35.0], [152.0, -32.0]],
            "stateName": "nsw",
            "incidentsNumber": 1,
            "stateCount": 1,
        }
        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=response)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        data = await coordinator._async_update_data()

        # Point geometry has no polygon, so contains_point should be False
        assert data.incidents[0].contains_point is False
        assert data.incidents[0].has_polygon is False
        assert data.inside_polygon is False

    async def test_containment_with_no_incidents(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
        empty_api_response: dict,
    ) -> None:
        """Test containment fields are properly initialized with no incidents."""
        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=empty_api_response)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        data = await coordinator._async_update_data()

        assert data.inside_polygon is False
        assert data.inside_emergency_warning is False
        assert data.inside_watch_and_act is False
        assert data.inside_advice is False
        assert data.containing_incidents == []
        assert data.highest_containing_alert_level == ""


class TestCoordinatorDataContainmentFields:
    """Test CoordinatorData containment field defaults and types."""

    def test_coordinator_data_containment_defaults(self) -> None:
        """Test CoordinatorData has correct containment field defaults."""
        data = CoordinatorData()

        # New containment fields should have proper defaults
        assert data.containing_incidents == []
        assert data.inside_polygon is False
        assert data.inside_emergency_warning is False
        assert data.inside_watch_and_act is False
        assert data.inside_advice is False
        assert data.highest_containing_alert_level == ""


class TestEmergencyIncidentContainsPointField:
    """Test EmergencyIncident contains_point field."""

    def test_emergency_incident_contains_point_default(self) -> None:
        """Test EmergencyIncident.contains_point defaults to None."""
        from custom_components.abcemergency.models import Coordinate

        incident = EmergencyIncident(
            id="test",
            headline="Test",
            alert_level="minor",
            alert_text="",
            event_type="Test",
            event_icon="other",
            status=None,
            size=None,
            source="Test",
            location=Coordinate(latitude=-33.0, longitude=151.0),
            updated=datetime.now(),
        )

        # Default should be None (not yet checked)
        assert incident.contains_point is None

    def test_emergency_incident_contains_point_can_be_set(self) -> None:
        """Test EmergencyIncident.contains_point can be set to True/False."""
        from custom_components.abcemergency.models import Coordinate

        incident = EmergencyIncident(
            id="test",
            headline="Test",
            alert_level="minor",
            alert_text="",
            event_type="Test",
            event_icon="other",
            status=None,
            size=None,
            source="Test",
            location=Coordinate(latitude=-33.0, longitude=151.0),
            updated=datetime.now(),
            contains_point=True,
        )

        assert incident.contains_point is True


class TestContainmentEvents:
    """Test containment event firing for enter/exit/inside polygon."""

    @pytest.fixture
    def polygon_near_sydney(self) -> list[list[list[float]]]:
        """Create a small polygon near Sydney that contains the test point."""
        # Sydney coords: -33.8688, 151.2093
        # Create a box around Sydney
        return [
            [
                [151.15, -33.92],  # SW
                [151.25, -33.92],  # SE
                [151.25, -33.82],  # NE
                [151.15, -33.82],  # NW
                [151.15, -33.92],  # Close the ring
            ]
        ]

    @pytest.fixture
    def polygon_away_from_sydney(self) -> list[list[list[float]]]:
        """Create a polygon that doesn't contain the test point."""
        # Far away from Sydney
        return [
            [
                [150.0, -34.5],
                [150.1, -34.5],
                [150.1, -34.4],
                [150.0, -34.4],
                [150.0, -34.5],
            ]
        ]

    @pytest.fixture
    def api_response_with_containing_polygon(
        self, polygon_near_sydney: list[list[list[float]]]
    ) -> dict:
        """Create API response with an incident polygon containing the monitored point."""
        return {
            "emergencies": [
                {
                    "id": "incident-inside",
                    "headline": "Bushfire Inside Zone",
                    "to": "/emergency/warning/incident-inside",
                    "alertLevelInfoPrepared": {
                        "text": "Watch and Act",
                        "level": "severe",
                        "style": "severe",
                    },
                    "emergencyTimestampPrepared": {
                        "date": "2024-01-15T01:00:00+00:00",
                        "formattedTime": "12:00:00 pm AEDT",
                        "prefix": "Effective from",
                        "updatedTime": "2024-01-15T01:00:00+00:00",
                    },
                    "eventLabelPrepared": {"icon": "fire", "labelText": "Bushfire"},
                    "cardBody": {
                        "type": "Bush Fire",
                        "size": "Large",
                        "status": "Going",
                        "source": "NSW RFS",
                    },
                    "geometry": {
                        "crs": {
                            "type": "name",
                            "properties": {"name": "EPSG:4326"},
                        },
                        "type": "Polygon",
                        "coordinates": polygon_near_sydney,
                    },
                }
            ],
            "features": [],
        }

    @pytest.fixture
    def api_response_with_non_containing_polygon(
        self, polygon_away_from_sydney: list[list[list[float]]]
    ) -> dict:
        """Create API response with an incident polygon NOT containing the monitored point."""
        return {
            "emergencies": [
                {
                    "id": "incident-outside",
                    "headline": "Bushfire Outside Zone",
                    "to": "/emergency/warning/incident-outside",
                    "alertLevelInfoPrepared": {
                        "text": "Watch and Act",
                        "level": "severe",
                        "style": "severe",
                    },
                    "emergencyTimestampPrepared": {
                        "date": "2024-01-15T01:00:00+00:00",
                        "formattedTime": "12:00:00 pm AEDT",
                        "prefix": "Effective from",
                        "updatedTime": "2024-01-15T01:00:00+00:00",
                    },
                    "eventLabelPrepared": {"icon": "fire", "labelText": "Bushfire"},
                    "cardBody": {
                        "type": "Bush Fire",
                        "size": "Large",
                        "status": "Going",
                        "source": "NSW RFS",
                    },
                    "geometry": {
                        "crs": {
                            "type": "name",
                            "properties": {"name": "EPSG:4326"},
                        },
                        "type": "Polygon",
                        "coordinates": polygon_away_from_sydney,
                    },
                }
            ],
            "features": [],
        }

    async def test_entered_polygon_event_fired_when_entering(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
        api_response_with_non_containing_polygon: dict,
        api_response_with_containing_polygon: dict,
    ) -> None:
        """Test abc_emergency_entered_polygon event fires when entering polygon."""
        # Set up to start outside, then move inside
        mock_client.async_get_emergencies_by_state = AsyncMock(
            side_effect=[
                api_response_with_non_containing_polygon,  # First refresh - outside
                api_response_with_containing_polygon,  # Second refresh - inside
            ]
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        # Track fired events
        entered_events: list = []

        def capture_entered_event(event) -> None:
            entered_events.append(event)

        hass.bus.async_listen("abc_emergency_entered_polygon", capture_entered_event)

        # First refresh - outside polygon
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        assert len(entered_events) == 0  # No enter event on first refresh

        # Second refresh - now inside polygon
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        assert len(entered_events) == 1

        # Verify event data
        event_data = entered_events[0].data
        assert event_data["incident_id"] == "incident-inside"
        assert event_data["headline"] == "Bushfire Inside Zone"
        assert event_data["alert_level"] == "severe"
        assert event_data["instance_type"] == "zone"

    async def test_exited_polygon_event_fired_when_exiting(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
        api_response_with_containing_polygon: dict,
        api_response_with_non_containing_polygon: dict,
    ) -> None:
        """Test abc_emergency_exited_polygon event fires when exiting polygon."""
        # Set up to start inside, then move outside
        mock_client.async_get_emergencies_by_state = AsyncMock(
            side_effect=[
                api_response_with_containing_polygon,  # First refresh - inside
                api_response_with_non_containing_polygon,  # Second refresh - outside
            ]
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        # Track fired events
        exited_events: list = []

        def capture_exited_event(event) -> None:
            exited_events.append(event)

        hass.bus.async_listen("abc_emergency_exited_polygon", capture_exited_event)

        # First refresh - inside polygon
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        assert len(exited_events) == 0  # No exit event on first refresh

        # Second refresh - now outside polygon
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        assert len(exited_events) == 1

        # Verify event data
        event_data = exited_events[0].data
        assert event_data["incident_id"] == "incident-inside"
        assert event_data["headline"] == "Bushfire Inside Zone"

    async def test_inside_polygon_event_fired_each_update(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
        api_response_with_containing_polygon: dict,
    ) -> None:
        """Test abc_emergency_inside_polygon event fires on each update while inside."""
        # Always inside
        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=api_response_with_containing_polygon
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        # Track fired events
        inside_events: list = []

        def capture_inside_event(event) -> None:
            inside_events.append(event)

        hass.bus.async_listen("abc_emergency_inside_polygon", capture_inside_event)

        # First refresh - inside but shouldn't fire yet (first load)
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        assert len(inside_events) == 0

        # Second refresh - should fire inside event
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        assert len(inside_events) == 1

        # Third refresh - should fire again
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        assert len(inside_events) == 2

    async def test_no_containment_events_on_first_load(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
        api_response_with_containing_polygon: dict,
    ) -> None:
        """Test that no containment events fire on first data load."""
        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=api_response_with_containing_polygon
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        # Track all containment events
        entered_events: list = []
        inside_events: list = []

        hass.bus.async_listen("abc_emergency_entered_polygon", lambda e: entered_events.append(e))
        hass.bus.async_listen("abc_emergency_inside_polygon", lambda e: inside_events.append(e))

        # First refresh - no events should fire
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        assert len(entered_events) == 0
        assert len(inside_events) == 0

    async def test_state_mode_no_containment_events(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
        api_response_with_containing_polygon: dict,
    ) -> None:
        """Test that state mode does not fire containment events."""
        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=api_response_with_containing_polygon
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        # Track all containment events
        all_events: list = []

        hass.bus.async_listen("abc_emergency_entered_polygon", lambda e: all_events.append(e))
        hass.bus.async_listen("abc_emergency_inside_polygon", lambda e: all_events.append(e))
        hass.bus.async_listen("abc_emergency_exited_polygon", lambda e: all_events.append(e))

        # Multiple refreshes - no containment events for state mode
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        assert len(all_events) == 0

    async def test_entered_event_includes_monitored_location(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
        api_response_with_non_containing_polygon: dict,
        api_response_with_containing_polygon: dict,
    ) -> None:
        """Test entered event includes monitored location coordinates."""
        mock_client.async_get_emergencies_by_state = AsyncMock(
            side_effect=[
                api_response_with_non_containing_polygon,
                api_response_with_containing_polygon,
            ]
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        entered_events: list = []
        hass.bus.async_listen("abc_emergency_entered_polygon", lambda e: entered_events.append(e))

        await coordinator.async_refresh()  # Outside
        await hass.async_block_till_done()
        await coordinator.async_refresh()  # Inside
        await hass.async_block_till_done()

        assert len(entered_events) == 1
        event_data = entered_events[0].data
        assert event_data["monitored_latitude"] == -33.8688
        assert event_data["monitored_longitude"] == 151.2093

    async def test_exited_event_works_when_incident_cleared(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
        api_response_with_containing_polygon: dict,
    ) -> None:
        """Test exit event fires with incident details even when incident is cleared."""
        # First inside, then incident disappears completely
        empty_response = {"emergencies": [], "features": []}
        mock_client.async_get_emergencies_by_state = AsyncMock(
            side_effect=[
                api_response_with_containing_polygon,  # First refresh - inside
                empty_response,  # Second refresh - incident gone
            ]
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        exited_events: list = []
        hass.bus.async_listen("abc_emergency_exited_polygon", lambda e: exited_events.append(e))

        await coordinator.async_refresh()  # Inside
        await hass.async_block_till_done()
        await coordinator.async_refresh()  # Incident gone
        await hass.async_block_till_done()

        assert len(exited_events) == 1
        # Event should still have incident details from cache
        event_data = exited_events[0].data
        assert event_data["incident_id"] == "incident-inside"
        assert event_data["headline"] == "Bushfire Inside Zone"

    async def test_entered_event_data_structure(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
        api_response_with_non_containing_polygon: dict,
        api_response_with_containing_polygon: dict,
    ) -> None:
        """Test that entered event has all expected data fields."""
        mock_client.async_get_emergencies_by_state = AsyncMock(
            side_effect=[
                api_response_with_non_containing_polygon,
                api_response_with_containing_polygon,
            ]
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        entered_events: list = []
        hass.bus.async_listen("abc_emergency_entered_polygon", lambda e: entered_events.append(e))

        await coordinator.async_refresh()
        await hass.async_block_till_done()
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        assert len(entered_events) == 1
        event_data = entered_events[0].data

        # Verify all expected fields are present
        expected_fields = [
            "config_entry_id",
            "instance_name",
            "instance_type",
            "incident_id",
            "headline",
            "event_type",
            "event_icon",
            "alert_level",
            "alert_text",
            "latitude",
            "longitude",
            "monitored_latitude",
            "monitored_longitude",
            "status",
            "source",
            "updated",
        ]

        for field in expected_fields:
            assert field in event_data, f"Missing field: {field}"


class TestContainmentEventsPersonMode:
    """Test containment events in person mode."""

    @pytest.fixture
    def polygon_near_sydney(self) -> list[list[list[float]]]:
        """Create a small polygon near Sydney."""
        return [
            [
                [151.15, -33.92],
                [151.25, -33.92],
                [151.25, -33.82],
                [151.15, -33.82],
                [151.15, -33.92],
            ]
        ]

    @pytest.fixture
    def api_response_with_containing_polygon(
        self, polygon_near_sydney: list[list[list[float]]]
    ) -> dict:
        """Create API response with containing polygon."""
        return {
            "emergencies": [
                {
                    "id": "incident-person-inside",
                    "headline": "Flood Near Person",
                    "to": "/emergency/warning/incident-person-inside",
                    "alertLevelInfoPrepared": {
                        "text": "Emergency Warning",
                        "level": "extreme",
                        "style": "extreme",
                    },
                    "emergencyTimestampPrepared": {
                        "date": "2024-01-15T03:00:00+00:00",
                        "formattedTime": "2:00:00 pm AEDT",
                        "prefix": "Effective from",
                        "updatedTime": "2024-01-15T03:00:00+00:00",
                    },
                    "eventLabelPrepared": {"icon": "weather", "labelText": "Flood"},
                    "cardBody": {
                        "type": "Flood",
                        "size": None,
                        "status": "Active",
                        "source": "NSW SES",
                    },
                    "geometry": {
                        "crs": {
                            "type": "name",
                            "properties": {"name": "EPSG:4326"},
                        },
                        "type": "Polygon",
                        "coordinates": polygon_near_sydney,
                    },
                }
            ],
            "features": [],
        }

    async def test_person_mode_entered_event_when_person_moves_into_polygon(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_person: MockConfigEntry,
        api_response_with_containing_polygon: dict,
    ) -> None:
        """Test person mode fires entered event when person moves into polygon."""
        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=api_response_with_containing_polygon
        )

        # Create person entity states
        hass.states.async_set(
            "person.troy",
            "home",
            {
                "latitude": -34.0,  # Outside polygon
                "longitude": 151.0,
            },
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_person,
            instance_type=INSTANCE_TYPE_PERSON,
            person_entity_id="person.troy",
        )

        entered_events: list = []
        hass.bus.async_listen("abc_emergency_entered_polygon", lambda e: entered_events.append(e))

        # First refresh - outside
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        assert len(entered_events) == 0

        # Move person into polygon
        hass.states.async_set(
            "person.troy",
            "home",
            {
                "latitude": -33.87,  # Inside polygon
                "longitude": 151.2,
            },
        )

        # Second refresh - now inside
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        assert len(entered_events) == 1
        assert entered_events[0].data["instance_type"] == "person"

    async def test_person_mode_no_exit_when_location_unknown(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_person: MockConfigEntry,
        api_response_with_containing_polygon: dict,
    ) -> None:
        """Test no exit event fires when person location becomes unknown."""
        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=api_response_with_containing_polygon
        )

        # Start with known location inside polygon
        hass.states.async_set(
            "person.troy",
            "home",
            {
                "latitude": -33.87,
                "longitude": 151.2,
            },
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_person,
            instance_type=INSTANCE_TYPE_PERSON,
            person_entity_id="person.troy",
        )

        exited_events: list = []
        hass.bus.async_listen("abc_emergency_exited_polygon", lambda e: exited_events.append(e))

        # First refresh - inside
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        # Make location unknown
        hass.states.async_set("person.troy", "unknown", {})

        # Second refresh - location unknown
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        # Should NOT fire exit event when location becomes unknown
        assert len(exited_events) == 0


class TestContainmentEventEdgeCases:
    """Test containment event edge cases including polygon changes and severity changes.

    These tests verify the refactored containment tracking that tracks actual
    containment state rather than just incident IDs. This enables detection of:
    - Polygon expansion (incident existed but wasn't containing, now is)
    - Polygon contraction (incident was containing, still exists but isn't)
    - Severity changes (alert level changed while inside polygon)
    """

    @pytest.fixture
    def polygon_containing_sydney(self) -> list[list[list[float]]]:
        """Create a polygon that contains Sydney coordinates (-33.8688, 151.2093)."""
        return [
            [
                [151.15, -33.92],
                [151.25, -33.92],
                [151.25, -33.82],
                [151.15, -33.82],
                [151.15, -33.92],
            ]
        ]

    @pytest.fixture
    def polygon_not_containing_sydney(self) -> list[list[list[float]]]:
        """Create a polygon that does NOT contain Sydney coordinates."""
        return [
            [
                [150.00, -34.50],
                [150.10, -34.50],
                [150.10, -34.40],
                [150.00, -34.40],
                [150.00, -34.50],
            ]
        ]

    def _create_api_response(
        self,
        incident_id: str,
        polygon: list[list[list[float]]],
        alert_level: str = "severe",
        alert_text: str = "Watch and Act",
    ) -> dict:
        """Create API response with specified polygon and alert level."""
        return {
            "emergencies": [
                {
                    "id": incident_id,
                    "headline": f"Test Incident {incident_id}",
                    "to": f"/emergency/warning/{incident_id}",
                    "alertLevelInfoPrepared": {
                        "text": alert_text,
                        "level": alert_level,
                        "style": alert_level,
                    },
                    "emergencyTimestampPrepared": {
                        "date": "2024-01-15T01:00:00+00:00",
                        "formattedTime": "12:00:00 pm AEDT",
                        "prefix": "Effective from",
                        "updatedTime": "2024-01-15T01:00:00+00:00",
                    },
                    "eventLabelPrepared": {"icon": "fire", "labelText": "Bushfire"},
                    "cardBody": {
                        "type": "Bush Fire",
                        "size": "Large",
                        "status": "Going",
                        "source": "NSW RFS",
                    },
                    "geometry": {
                        "crs": {
                            "type": "name",
                            "properties": {"name": "EPSG:4326"},
                        },
                        "type": "Polygon",
                        "coordinates": polygon,
                    },
                }
            ],
            "features": [],
        }

    async def test_entered_event_fires_when_polygon_expands(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
        polygon_not_containing_sydney: list[list[list[float]]],
        polygon_containing_sydney: list[list[list[float]]],
    ) -> None:
        """Test entered event fires when existing incident polygon expands to contain point.

        This tests the key fix for Issue #91: when an incident's polygon changes
        from not containing to containing, the entered event should fire even
        though the incident ID already existed.
        """
        # Same incident ID, but polygon changes from not containing to containing
        response_not_containing = self._create_api_response(
            "incident-123", polygon_not_containing_sydney
        )
        response_containing = self._create_api_response("incident-123", polygon_containing_sydney)

        mock_client.async_get_emergencies_by_state = AsyncMock(
            side_effect=[
                response_not_containing,  # First: incident exists but doesn't contain
                response_containing,  # Second: same incident now contains (polygon expanded)
            ]
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        entered_events: list = []
        hass.bus.async_listen("abc_emergency_entered_polygon", lambda e: entered_events.append(e))

        # First refresh - incident exists but doesn't contain point
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        assert len(entered_events) == 0

        # Second refresh - same incident now contains point (polygon expanded)
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        # Should fire entered event because containment state changed
        assert len(entered_events) == 1
        assert entered_events[0].data["incident_id"] == "incident-123"

    async def test_exited_event_fires_when_polygon_contracts(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
        polygon_containing_sydney: list[list[list[float]]],
        polygon_not_containing_sydney: list[list[list[float]]],
    ) -> None:
        """Test exited event fires when existing incident polygon shrinks to not contain point.

        This tests the key fix for Issue #91: when an incident's polygon changes
        from containing to not containing, the exited event should fire even
        though the incident ID still exists.
        """
        # Same incident ID, but polygon changes from containing to not containing
        response_containing = self._create_api_response("incident-456", polygon_containing_sydney)
        response_not_containing = self._create_api_response(
            "incident-456", polygon_not_containing_sydney
        )

        mock_client.async_get_emergencies_by_state = AsyncMock(
            side_effect=[
                response_containing,  # First: incident contains point
                response_not_containing,  # Second: same incident no longer contains
            ]
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        exited_events: list = []
        hass.bus.async_listen("abc_emergency_exited_polygon", lambda e: exited_events.append(e))

        # First refresh - inside polygon (baseline)
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        assert len(exited_events) == 0

        # Second refresh - same incident but polygon no longer contains
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        # Should fire exited event because containment state changed
        assert len(exited_events) == 1
        assert exited_events[0].data["incident_id"] == "incident-456"

    async def test_severity_changed_event_fires_on_escalation(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
        polygon_containing_sydney: list[list[list[float]]],
    ) -> None:
        """Test severity changed event fires when alert level escalates while inside.

        This tests Issue #92: when the severity of an incident changes from
        Advice to Emergency Warning while the point is inside, a severity
        changed event should fire.
        """
        response_advice = self._create_api_response(
            "incident-escalate",
            polygon_containing_sydney,
            alert_level="moderate",
            alert_text="Advice",
        )
        response_emergency = self._create_api_response(
            "incident-escalate",
            polygon_containing_sydney,
            alert_level="extreme",
            alert_text="Emergency Warning",
        )

        mock_client.async_get_emergencies_by_state = AsyncMock(
            side_effect=[
                response_advice,  # First: Advice level
                response_emergency,  # Second: Escalated to Emergency Warning
            ]
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        severity_events: list = []
        hass.bus.async_listen(
            "abc_emergency_containment_severity_changed", lambda e: severity_events.append(e)
        )

        # First refresh - inside at Advice level
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        assert len(severity_events) == 0

        # Second refresh - escalated to Emergency Warning
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        assert len(severity_events) == 1
        event_data = severity_events[0].data
        assert event_data["incident_id"] == "incident-escalate"
        assert event_data["previous_alert_level"] == "moderate"
        assert event_data["previous_alert_text"] == "Advice"
        assert event_data["new_alert_level"] == "extreme"
        assert event_data["new_alert_text"] == "Emergency Warning"
        assert event_data["escalated"] is True

    async def test_severity_changed_event_fires_on_deescalation(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
        polygon_containing_sydney: list[list[list[float]]],
    ) -> None:
        """Test severity changed event fires when alert level de-escalates while inside.

        This tests Issue #92: when the severity decreases (e.g., Emergency Warning
        to Advice), a severity changed event should fire with escalated=False.
        """
        response_emergency = self._create_api_response(
            "incident-deescalate",
            polygon_containing_sydney,
            alert_level="extreme",
            alert_text="Emergency Warning",
        )
        response_advice = self._create_api_response(
            "incident-deescalate",
            polygon_containing_sydney,
            alert_level="moderate",
            alert_text="Advice",
        )

        mock_client.async_get_emergencies_by_state = AsyncMock(
            side_effect=[
                response_emergency,  # First: Emergency Warning
                response_advice,  # Second: De-escalated to Advice
            ]
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        severity_events: list = []
        hass.bus.async_listen(
            "abc_emergency_containment_severity_changed", lambda e: severity_events.append(e)
        )

        await coordinator.async_refresh()
        await hass.async_block_till_done()
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        assert len(severity_events) == 1
        event_data = severity_events[0].data
        assert event_data["previous_alert_level"] == "extreme"
        assert event_data["new_alert_level"] == "moderate"
        assert event_data["escalated"] is False

    async def test_no_severity_event_when_level_unchanged(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
        polygon_containing_sydney: list[list[list[float]]],
    ) -> None:
        """Test no severity changed event when alert level is unchanged."""
        response = self._create_api_response(
            "incident-unchanged",
            polygon_containing_sydney,
            alert_level="severe",
            alert_text="Watch and Act",
        )

        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=response)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        severity_events: list = []
        hass.bus.async_listen(
            "abc_emergency_containment_severity_changed", lambda e: severity_events.append(e)
        )

        # Multiple refreshes with same alert level
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        # No severity changed events
        assert len(severity_events) == 0

    async def test_no_severity_event_when_not_containing(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
        polygon_not_containing_sydney: list[list[list[float]]],
    ) -> None:
        """Test no severity changed event for incidents not containing the point."""
        response_advice = self._create_api_response(
            "incident-outside",
            polygon_not_containing_sydney,
            alert_level="moderate",
            alert_text="Advice",
        )
        response_emergency = self._create_api_response(
            "incident-outside",
            polygon_not_containing_sydney,
            alert_level="extreme",
            alert_text="Emergency Warning",
        )

        mock_client.async_get_emergencies_by_state = AsyncMock(
            side_effect=[response_advice, response_emergency]
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        severity_events: list = []
        hass.bus.async_listen(
            "abc_emergency_containment_severity_changed", lambda e: severity_events.append(e)
        )

        await coordinator.async_refresh()
        await hass.async_block_till_done()
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        # No events since point was never inside polygon
        assert len(severity_events) == 0

    async def test_polygon_expansion_and_severity_change_combined(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
        polygon_not_containing_sydney: list[list[list[float]]],
        polygon_containing_sydney: list[list[list[float]]],
    ) -> None:
        """Test when polygon expands AND severity changes in same update.

        When polygon expands to contain point, only entered event should fire,
        not severity changed (since there's no previous containing state).
        """
        response_outside_advice = self._create_api_response(
            "incident-combo",
            polygon_not_containing_sydney,
            alert_level="moderate",
            alert_text="Advice",
        )
        response_inside_emergency = self._create_api_response(
            "incident-combo",
            polygon_containing_sydney,
            alert_level="extreme",
            alert_text="Emergency Warning",
        )

        mock_client.async_get_emergencies_by_state = AsyncMock(
            side_effect=[response_outside_advice, response_inside_emergency]
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        entered_events: list = []
        severity_events: list = []
        hass.bus.async_listen("abc_emergency_entered_polygon", lambda e: entered_events.append(e))
        hass.bus.async_listen(
            "abc_emergency_containment_severity_changed", lambda e: severity_events.append(e)
        )

        await coordinator.async_refresh()
        await hass.async_block_till_done()
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        # Should fire entered event (polygon expanded to contain)
        assert len(entered_events) == 1
        # Should NOT fire severity event (no previous containing state to compare)
        assert len(severity_events) == 0

    async def test_no_event_when_still_inside_unchanged(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
        polygon_containing_sydney: list[list[list[float]]],
    ) -> None:
        """Test no entered/exited event when containment state unchanged.

        When point was inside and remains inside with same alert level,
        only inside_polygon event should fire, not entered or severity_changed.
        """
        response = self._create_api_response("incident-stable", polygon_containing_sydney)

        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=response)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        entered_events: list = []
        exited_events: list = []
        inside_events: list = []
        severity_events: list = []

        hass.bus.async_listen("abc_emergency_entered_polygon", lambda e: entered_events.append(e))
        hass.bus.async_listen("abc_emergency_exited_polygon", lambda e: exited_events.append(e))
        hass.bus.async_listen("abc_emergency_inside_polygon", lambda e: inside_events.append(e))
        hass.bus.async_listen(
            "abc_emergency_containment_severity_changed", lambda e: severity_events.append(e)
        )

        # First refresh - baseline (no events on first load)
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        # Second refresh - still inside, unchanged
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        # Third refresh - still inside, unchanged
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        # Only inside_polygon events should fire (one per refresh after first)
        assert len(entered_events) == 0  # No re-entry
        assert len(exited_events) == 0  # No exit
        assert len(inside_events) == 2  # Two inside events (second and third refresh)
        assert len(severity_events) == 0  # No severity change

    async def test_severity_changed_event_data_structure(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
        polygon_containing_sydney: list[list[list[float]]],
    ) -> None:
        """Test that severity changed event has all expected data fields."""
        response_watch = self._create_api_response(
            "incident-data-test",
            polygon_containing_sydney,
            alert_level="severe",
            alert_text="Watch and Act",
        )
        response_emergency = self._create_api_response(
            "incident-data-test",
            polygon_containing_sydney,
            alert_level="extreme",
            alert_text="Emergency Warning",
        )

        mock_client.async_get_emergencies_by_state = AsyncMock(
            side_effect=[response_watch, response_emergency]
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        severity_events: list = []
        hass.bus.async_listen(
            "abc_emergency_containment_severity_changed", lambda e: severity_events.append(e)
        )

        await coordinator.async_refresh()
        await hass.async_block_till_done()
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        assert len(severity_events) == 1
        event_data = severity_events[0].data

        # Verify all standard containment event fields
        expected_standard_fields = [
            "config_entry_id",
            "instance_name",
            "instance_type",
            "incident_id",
            "headline",
            "event_type",
            "event_icon",
            "alert_level",
            "alert_text",
            "latitude",
            "longitude",
            "monitored_latitude",
            "monitored_longitude",
            "status",
            "source",
            "updated",
        ]
        for field in expected_standard_fields:
            assert field in event_data, f"Missing standard field: {field}"

        # Verify severity-specific fields
        severity_specific_fields = [
            "previous_alert_level",
            "previous_alert_text",
            "new_alert_level",
            "new_alert_text",
            "escalated",
        ]
        for field in severity_specific_fields:
            assert field in event_data, f"Missing severity field: {field}"

    async def test_severity_watch_and_act_to_advice(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
        polygon_containing_sydney: list[list[list[float]]],
    ) -> None:
        """Test severity change from Watch and Act to Advice (de-escalation)."""
        response_watch = self._create_api_response(
            "incident-waa",
            polygon_containing_sydney,
            alert_level="severe",
            alert_text="Watch and Act",
        )
        response_advice = self._create_api_response(
            "incident-waa",
            polygon_containing_sydney,
            alert_level="moderate",
            alert_text="Advice",
        )

        mock_client.async_get_emergencies_by_state = AsyncMock(
            side_effect=[response_watch, response_advice]
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        severity_events: list = []
        hass.bus.async_listen(
            "abc_emergency_containment_severity_changed", lambda e: severity_events.append(e)
        )

        await coordinator.async_refresh()
        await hass.async_block_till_done()
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        assert len(severity_events) == 1
        event_data = severity_events[0].data
        assert event_data["previous_alert_level"] == "severe"
        assert event_data["new_alert_level"] == "moderate"
        assert event_data["escalated"] is False

    async def test_severity_advice_to_watch_and_act(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
        polygon_containing_sydney: list[list[list[float]]],
    ) -> None:
        """Test severity change from Advice to Watch and Act (escalation)."""
        response_advice = self._create_api_response(
            "incident-atw",
            polygon_containing_sydney,
            alert_level="moderate",
            alert_text="Advice",
        )
        response_watch = self._create_api_response(
            "incident-atw",
            polygon_containing_sydney,
            alert_level="severe",
            alert_text="Watch and Act",
        )

        mock_client.async_get_emergencies_by_state = AsyncMock(
            side_effect=[response_advice, response_watch]
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        severity_events: list = []
        hass.bus.async_listen(
            "abc_emergency_containment_severity_changed", lambda e: severity_events.append(e)
        )

        await coordinator.async_refresh()
        await hass.async_block_till_done()
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        assert len(severity_events) == 1
        event_data = severity_events[0].data
        assert event_data["previous_alert_level"] == "moderate"
        assert event_data["new_alert_level"] == "severe"
        assert event_data["escalated"] is True

    async def test_containment_tracking_handles_incident_not_containing_in_previous_state(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
        polygon_containing_sydney: list[list[list[float]]],
        polygon_not_containing_sydney: list[list[list[float]]],
    ) -> None:
        """Test that previous containment state with was_containing=False is handled.

        This covers line 1007 - the continue statement when iterating previous
        state and finding an incident that wasn't containing. We need to:
        1. First refresh with some incident (populates first_containment_check)
        2. Second refresh with a non-containing incident (stores was_containing=False)
        3. Third refresh removes it (iterates previous state, should skip exit event)
        """
        # First have one containing incident, then add another non-containing, then remove it
        response_containing_only = self._create_api_response(
            "incident-inside", polygon_containing_sydney
        )
        # Two incidents: one containing, one not
        response_both = {
            "emergencies": [
                {
                    "id": "incident-inside",
                    "headline": "Test Inside",
                    "to": "/emergency/warning/incident-inside",
                    "alertLevelInfoPrepared": {
                        "text": "Watch and Act",
                        "level": "severe",
                        "style": "severe",
                    },
                    "emergencyTimestampPrepared": {
                        "date": "2024-01-15T01:00:00+00:00",
                        "formattedTime": "12:00:00 pm AEDT",
                        "prefix": "Effective from",
                        "updatedTime": "2024-01-15T01:00:00+00:00",
                    },
                    "eventLabelPrepared": {"icon": "fire", "labelText": "Bushfire"},
                    "cardBody": {
                        "type": "Bush Fire",
                        "size": "Large",
                        "status": "Going",
                        "source": "NSW RFS",
                    },
                    "geometry": {
                        "crs": {
                            "type": "name",
                            "properties": {"name": "EPSG:4326"},
                        },
                        "type": "Polygon",
                        "coordinates": polygon_containing_sydney,
                    },
                },
                {
                    "id": "incident-outside",
                    "headline": "Test Outside",
                    "to": "/emergency/warning/incident-outside",
                    "alertLevelInfoPrepared": {
                        "text": "Watch and Act",
                        "level": "severe",
                        "style": "severe",
                    },
                    "emergencyTimestampPrepared": {
                        "date": "2024-01-15T01:00:00+00:00",
                        "formattedTime": "12:00:00 pm AEDT",
                        "prefix": "Effective from",
                        "updatedTime": "2024-01-15T01:00:00+00:00",
                    },
                    "eventLabelPrepared": {"icon": "fire", "labelText": "Bushfire"},
                    "cardBody": {
                        "type": "Bush Fire",
                        "size": "Large",
                        "status": "Going",
                        "source": "NSW RFS",
                    },
                    "geometry": {
                        "crs": {
                            "type": "name",
                            "properties": {"name": "EPSG:4326"},
                        },
                        "type": "Polygon",
                        "coordinates": polygon_not_containing_sydney,
                    },
                },
            ],
            "features": [],
        }

        mock_client.async_get_emergencies_by_state = AsyncMock(
            side_effect=[
                response_containing_only,  # First: one containing (populates first check)
                response_both,  # Second: add non-containing incident (was_containing=False stored)
                response_containing_only,  # Third: remove non-containing (should NOT fire exit)
            ]
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,
            longitude=151.2093,
        )

        exited_events: list = []
        hass.bus.async_listen("abc_emergency_exited_polygon", lambda e: exited_events.append(e))

        # First refresh - baseline with one containing incident
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        # Second refresh - add non-containing incident
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        # Third refresh - remove non-containing incident
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        # Should NOT fire exited event for the outside incident because it was never containing
        # Only inside_polygon events should have fired for incident-inside
        assert len(exited_events) == 0


class TestStateFiltering:
    """Test filtering emergencies by state (Issue #117).

    The ABC Emergency API returns incidents from neighboring states when querying
    for a specific state. These tests verify that the coordinator correctly filters
    emergencies to only include those from the requested state.
    """

    async def test_filters_out_incidents_from_other_states(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test that incidents from other states are filtered out."""
        # Create response with incidents from NSW (target) and VIC (should be filtered)
        response_with_mixed_states = {
            "emergencies": [
                {
                    "id": "AUREMER-nsw-incident",
                    "headline": "NSW Bushfire",
                    "to": "/emergency/warning/AUREMER-nsw-incident",
                    "alertLevelInfoPrepared": {
                        "text": "Emergency",
                        "level": "extreme",
                        "style": "extreme",
                    },
                    "emergencyTimestampPrepared": {
                        "date": "2025-12-06T05:00:00+00:00",
                        "formattedTime": "4:00:00 pm AEDT",
                        "prefix": "Effective from",
                        "updatedTime": "2025-12-06T05:00:00+00:00",
                    },
                    "eventLabelPrepared": {"icon": "fire", "labelText": "Bushfire"},
                    "cardBody": {
                        "type": "Bushfire",
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
                    "id": "AUREMER-vic-incident",
                    "headline": "VIC Bushfire",
                    "to": "/emergency/warning/AUREMER-vic-incident",
                    "alertLevelInfoPrepared": {
                        "text": "Watch and Act",
                        "level": "severe",
                        "style": "severe",
                    },
                    "emergencyTimestampPrepared": {
                        "date": "2025-12-06T04:00:00+00:00",
                        "formattedTime": "3:00:00 pm AEDT",
                        "prefix": "Effective from",
                        "updatedTime": "2025-12-06T04:00:00+00:00",
                    },
                    "eventLabelPrepared": {"icon": "fire", "labelText": "Bushfire"},
                    "cardBody": {
                        "type": "Bushfire",
                        "size": "200 ha",
                        "status": "Going",
                        "source": "CFA Victoria",
                    },
                    "geometry": {
                        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
                        "type": "GeometryCollection",
                        "geometries": [{"type": "Point", "coordinates": [145.0, -37.5]}],
                    },
                },
            ],
            "features": [
                _make_feature("AUREMER-nsw-incident", "nsw"),
                _make_feature("AUREMER-vic-incident", "vic"),
            ],
            "mapBound": [[140.0, -38.0], [154.0, -28.0]],
            "stateName": "nsw",
            "incidentsNumber": 2,
            "stateCount": 125,
        }

        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=response_with_mixed_states
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        data = await coordinator._async_update_data()

        # Should only have 1 incident (NSW), not 2
        assert data.total_count == 1
        assert len(data.incidents) == 1
        assert data.incidents[0].id == "AUREMER-nsw-incident"

    async def test_filters_multiple_other_states(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test filtering when API returns incidents from multiple other states."""
        response_with_multiple_states = {
            "emergencies": [
                {
                    "id": "AUREMER-nsw-1",
                    "headline": "NSW Fire",
                    "to": "/emergency/warning/AUREMER-nsw-1",
                    "alertLevelInfoPrepared": {
                        "text": "Advice",
                        "level": "moderate",
                        "style": "moderate",
                    },
                    "emergencyTimestampPrepared": {
                        "date": "2025-12-06T05:00:00+00:00",
                        "formattedTime": "4:00:00 pm AEDT",
                        "prefix": "Effective from",
                        "updatedTime": "2025-12-06T05:00:00+00:00",
                    },
                    "eventLabelPrepared": {"icon": "fire", "labelText": "Bushfire"},
                    "cardBody": {
                        "type": "Bushfire",
                        "size": "100 ha",
                        "status": "Going",
                        "source": "NSW RFS",
                    },
                    "geometry": {
                        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
                        "type": "GeometryCollection",
                        "geometries": [{"type": "Point", "coordinates": [151.0, -33.87]}],
                    },
                },
                {
                    "id": "AUREMER-vic-1",
                    "headline": "VIC Fire",
                    "to": "/emergency/warning/AUREMER-vic-1",
                    "alertLevelInfoPrepared": {
                        "text": "Watch and Act",
                        "level": "severe",
                        "style": "severe",
                    },
                    "emergencyTimestampPrepared": {
                        "date": "2025-12-06T04:00:00+00:00",
                        "formattedTime": "3:00:00 pm AEDT",
                        "prefix": "Effective from",
                        "updatedTime": "2025-12-06T04:00:00+00:00",
                    },
                    "eventLabelPrepared": {"icon": "fire", "labelText": "Bushfire"},
                    "cardBody": {
                        "type": "Bushfire",
                        "size": "200 ha",
                        "status": "Going",
                        "source": "CFA",
                    },
                    "geometry": {
                        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
                        "type": "GeometryCollection",
                        "geometries": [{"type": "Point", "coordinates": [145.0, -37.5]}],
                    },
                },
                {
                    "id": "AUREMER-qld-1",
                    "headline": "QLD Storm",
                    "to": "/emergency/warning/AUREMER-qld-1",
                    "alertLevelInfoPrepared": {
                        "text": "Advice",
                        "level": "moderate",
                        "style": "moderate",
                    },
                    "emergencyTimestampPrepared": {
                        "date": "2025-12-06T03:00:00+00:00",
                        "formattedTime": "2:00:00 pm AEDT",
                        "prefix": "Effective from",
                        "updatedTime": "2025-12-06T03:00:00+00:00",
                    },
                    "eventLabelPrepared": {"icon": "weather", "labelText": "Storm"},
                    "cardBody": {
                        "type": "Storm",
                        "size": None,
                        "status": "Active",
                        "source": "QLD Fire",
                    },
                    "geometry": {
                        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
                        "type": "GeometryCollection",
                        "geometries": [{"type": "Point", "coordinates": [153.0, -27.5]}],
                    },
                },
                {
                    "id": "AUREMER-sa-1",
                    "headline": "SA Fire",
                    "to": "/emergency/warning/AUREMER-sa-1",
                    "alertLevelInfoPrepared": {
                        "text": "Emergency",
                        "level": "extreme",
                        "style": "extreme",
                    },
                    "emergencyTimestampPrepared": {
                        "date": "2025-12-06T02:00:00+00:00",
                        "formattedTime": "1:00:00 pm AEDT",
                        "prefix": "Effective from",
                        "updatedTime": "2025-12-06T02:00:00+00:00",
                    },
                    "eventLabelPrepared": {"icon": "fire", "labelText": "Bushfire"},
                    "cardBody": {
                        "type": "Bushfire",
                        "size": "1000 ha",
                        "status": "Going",
                        "source": "CFS SA",
                    },
                    "geometry": {
                        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
                        "type": "GeometryCollection",
                        "geometries": [{"type": "Point", "coordinates": [138.0, -34.9]}],
                    },
                },
            ],
            "features": [
                _make_feature("AUREMER-nsw-1", "nsw"),
                _make_feature("AUREMER-vic-1", "vic"),
                _make_feature("AUREMER-qld-1", "qld"),
                _make_feature("AUREMER-sa-1", "sa"),
            ],
            "mapBound": [[113.0, -44.0], [154.0, -10.0]],
            "stateName": "nsw",
            "incidentsNumber": 4,
            "stateCount": 500,
        }

        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=response_with_multiple_states
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        data = await coordinator._async_update_data()

        # Should only have 1 incident (NSW), filtering out VIC, QLD, SA
        assert data.total_count == 1
        assert len(data.incidents) == 1
        assert data.incidents[0].id == "AUREMER-nsw-1"

    async def test_state_filtering_case_insensitive(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test that state filtering is case insensitive."""
        response_with_mixed_case = {
            "emergencies": [
                {
                    "id": "AUREMER-nsw-upper",
                    "headline": "NSW Fire",
                    "to": "/emergency/warning/AUREMER-nsw-upper",
                    "alertLevelInfoPrepared": {
                        "text": "Advice",
                        "level": "moderate",
                        "style": "moderate",
                    },
                    "emergencyTimestampPrepared": {
                        "date": "2025-12-06T05:00:00+00:00",
                        "formattedTime": "4:00:00 pm AEDT",
                        "prefix": "Effective from",
                        "updatedTime": "2025-12-06T05:00:00+00:00",
                    },
                    "eventLabelPrepared": {"icon": "fire", "labelText": "Bushfire"},
                    "cardBody": {
                        "type": "Bushfire",
                        "size": "100 ha",
                        "status": "Going",
                        "source": "NSW RFS",
                    },
                    "geometry": {
                        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
                        "type": "GeometryCollection",
                        "geometries": [{"type": "Point", "coordinates": [151.0, -33.87]}],
                    },
                },
            ],
            "features": [
                {
                    "type": "Feature",
                    "id": "AUREMER-nsw-upper",
                    "geometry": {"type": "Point", "coordinates": [151.0, -33.87]},
                    "properties": {
                        "id": "AUREMER-nsw-upper",
                        "state": "NSW",  # Upper case
                        "headline": "Test",
                    },
                },
            ],
            "mapBound": [[140.0, -38.0], [154.0, -28.0]],
            "stateName": "nsw",
            "incidentsNumber": 1,
            "stateCount": 125,
        }

        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=response_with_mixed_case
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",  # Lower case in config
        )

        data = await coordinator._async_update_data()

        # Should match despite case difference
        assert data.total_count == 1

    async def test_zone_mode_filters_by_determined_state(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_zone: MockConfigEntry,
    ) -> None:
        """Test that zone mode also filters by state."""
        # Location is in NSW (Sydney area)
        response_with_mixed_states = {
            "emergencies": [
                {
                    "id": "AUREMER-nsw-zone",
                    "headline": "NSW Fire Near Zone",
                    "to": "/emergency/warning/AUREMER-nsw-zone",
                    "alertLevelInfoPrepared": {
                        "text": "Emergency",
                        "level": "extreme",
                        "style": "extreme",
                    },
                    "emergencyTimestampPrepared": {
                        "date": "2025-12-06T05:00:00+00:00",
                        "formattedTime": "4:00:00 pm AEDT",
                        "prefix": "Effective from",
                        "updatedTime": "2025-12-06T05:00:00+00:00",
                    },
                    "eventLabelPrepared": {"icon": "fire", "labelText": "Bushfire"},
                    "cardBody": {
                        "type": "Bushfire",
                        "size": "500 ha",
                        "status": "Out of control",
                        "source": "NSW RFS",
                    },
                    "geometry": {
                        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
                        "type": "GeometryCollection",
                        "geometries": [{"type": "Point", "coordinates": [151.22, -33.87]}],
                    },
                },
                {
                    "id": "AUREMER-vic-zone",
                    "headline": "VIC Fire (Should be filtered)",
                    "to": "/emergency/warning/AUREMER-vic-zone",
                    "alertLevelInfoPrepared": {
                        "text": "Emergency",
                        "level": "extreme",
                        "style": "extreme",
                    },
                    "emergencyTimestampPrepared": {
                        "date": "2025-12-06T04:00:00+00:00",
                        "formattedTime": "3:00:00 pm AEDT",
                        "prefix": "Effective from",
                        "updatedTime": "2025-12-06T04:00:00+00:00",
                    },
                    "eventLabelPrepared": {"icon": "fire", "labelText": "Bushfire"},
                    "cardBody": {
                        "type": "Bushfire",
                        "size": "1000 ha",
                        "status": "Out of control",
                        "source": "CFA Victoria",
                    },
                    "geometry": {
                        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
                        "type": "GeometryCollection",
                        "geometries": [{"type": "Point", "coordinates": [145.0, -37.5]}],
                    },
                },
            ],
            "features": [
                _make_feature("AUREMER-nsw-zone", "nsw"),
                _make_feature("AUREMER-vic-zone", "vic"),
            ],
            "mapBound": [[140.0, -38.0], [154.0, -28.0]],
            "stateName": "nsw",
            "incidentsNumber": 2,
            "stateCount": 125,
        }

        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=response_with_mixed_states
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_zone,
            instance_type=INSTANCE_TYPE_ZONE,
            latitude=-33.8688,  # Sydney
            longitude=151.2093,
        )

        data = await coordinator._async_update_data()

        # Should only have NSW incident (zone is in NSW)
        assert data.total_count == 1
        assert len(data.incidents) == 1
        assert data.incidents[0].id == "AUREMER-nsw-zone"

    async def test_no_filtering_when_features_empty(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_state: MockConfigEntry,
    ) -> None:
        """Test that no filtering occurs when features array is empty."""
        # This handles edge cases where API might not return features
        response_no_features = {
            "emergencies": [
                {
                    "id": "AUREMER-unknown-1",
                    "headline": "Unknown State Fire",
                    "to": "/emergency/warning/AUREMER-unknown-1",
                    "alertLevelInfoPrepared": {
                        "text": "Advice",
                        "level": "moderate",
                        "style": "moderate",
                    },
                    "emergencyTimestampPrepared": {
                        "date": "2025-12-06T05:00:00+00:00",
                        "formattedTime": "4:00:00 pm AEDT",
                        "prefix": "Effective from",
                        "updatedTime": "2025-12-06T05:00:00+00:00",
                    },
                    "eventLabelPrepared": {"icon": "fire", "labelText": "Bushfire"},
                    "cardBody": {
                        "type": "Bushfire",
                        "size": "100 ha",
                        "status": "Going",
                        "source": "Unknown Service",
                    },
                    "geometry": {
                        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
                        "type": "GeometryCollection",
                        "geometries": [{"type": "Point", "coordinates": [151.0, -33.87]}],
                    },
                },
            ],
            "features": [],  # Empty features array
            "mapBound": [[140.0, -38.0], [154.0, -28.0]],
            "stateName": "nsw",
            "incidentsNumber": 1,
            "stateCount": 125,
        }

        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=response_no_features)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_state,
            instance_type=INSTANCE_TYPE_STATE,
            state="nsw",
        )

        data = await coordinator._async_update_data()

        # Should return all emergencies when features is empty (fallback behavior)
        assert data.total_count == 1

    async def test_person_mode_filters_by_state(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry_person: MockConfigEntry,
    ) -> None:
        """Test that person mode also filters by state."""
        # Person is in Sydney (NSW)
        hass.states.async_set(
            "person.john",
            "home",
            {"latitude": -33.8688, "longitude": 151.2093},
        )

        response_with_mixed_states = {
            "emergencies": [
                {
                    "id": "AUREMER-nsw-person",
                    "headline": "NSW Fire",
                    "to": "/emergency/warning/AUREMER-nsw-person",
                    "alertLevelInfoPrepared": {
                        "text": "Emergency",
                        "level": "extreme",
                        "style": "extreme",
                    },
                    "emergencyTimestampPrepared": {
                        "date": "2025-12-06T05:00:00+00:00",
                        "formattedTime": "4:00:00 pm AEDT",
                        "prefix": "Effective from",
                        "updatedTime": "2025-12-06T05:00:00+00:00",
                    },
                    "eventLabelPrepared": {"icon": "fire", "labelText": "Bushfire"},
                    "cardBody": {
                        "type": "Bushfire",
                        "size": "500 ha",
                        "status": "Out of control",
                        "source": "NSW RFS",
                    },
                    "geometry": {
                        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
                        "type": "GeometryCollection",
                        "geometries": [{"type": "Point", "coordinates": [151.22, -33.87]}],
                    },
                },
                {
                    "id": "AUREMER-vic-person",
                    "headline": "VIC Fire",
                    "to": "/emergency/warning/AUREMER-vic-person",
                    "alertLevelInfoPrepared": {
                        "text": "Emergency",
                        "level": "extreme",
                        "style": "extreme",
                    },
                    "emergencyTimestampPrepared": {
                        "date": "2025-12-06T04:00:00+00:00",
                        "formattedTime": "3:00:00 pm AEDT",
                        "prefix": "Effective from",
                        "updatedTime": "2025-12-06T04:00:00+00:00",
                    },
                    "eventLabelPrepared": {"icon": "fire", "labelText": "Bushfire"},
                    "cardBody": {
                        "type": "Bushfire",
                        "size": "1000 ha",
                        "status": "Out of control",
                        "source": "CFA Victoria",
                    },
                    "geometry": {
                        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
                        "type": "GeometryCollection",
                        "geometries": [{"type": "Point", "coordinates": [145.0, -37.5]}],
                    },
                },
            ],
            "features": [
                _make_feature("AUREMER-nsw-person", "nsw"),
                _make_feature("AUREMER-vic-person", "vic"),
            ],
            "mapBound": [[140.0, -38.0], [154.0, -28.0]],
            "stateName": "nsw",
            "incidentsNumber": 2,
            "stateCount": 125,
        }

        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value=response_with_mixed_states
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            mock_config_entry_person,
            instance_type=INSTANCE_TYPE_PERSON,
            person_entity_id="person.john",
        )

        data = await coordinator._async_update_data()

        # Should only have NSW incident (person is in NSW)
        assert data.total_count == 1
        assert len(data.incidents) == 1
        assert data.incidents[0].id == "AUREMER-nsw-person"
