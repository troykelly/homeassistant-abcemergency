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
        "features": [],
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
        sample_api_response: dict,
    ) -> None:
        """Test incidents are sorted by distance (nearest first)."""
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

        assert len(data.incidents) >= 2
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

        result = coordinator._extract_location(geometry)
        assert result is not None
        assert result.latitude == pytest.approx(-33.4, abs=0.1)
        assert result.longitude == pytest.approx(150.4, abs=0.1)

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
        }

        result = coordinator._extract_location(geometry)
        assert result is not None
        assert result.latitude == pytest.approx(-33.4, abs=0.1)
        assert result.longitude == pytest.approx(150.4, abs=0.1)
