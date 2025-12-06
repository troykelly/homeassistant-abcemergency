"""Tests for ABC Emergency coordinator."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.abcemergency.const import AlertLevel
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


class TestCoordinatorInit:
    """Test coordinator initialization."""

    def test_init_stores_configuration(self, hass: HomeAssistant, mock_client: MagicMock) -> None:
        """Test coordinator stores configuration correctly."""
        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            state="nsw",
            latitude=-33.8688,
            longitude=151.2093,
            radius_km=50,
        )

        assert coordinator._state == "nsw"
        assert coordinator._latitude == -33.8688
        assert coordinator._longitude == 151.2093
        assert coordinator._radius_km == 50

    def test_init_sets_update_interval(self, hass: HomeAssistant, mock_client: MagicMock) -> None:
        """Test coordinator sets correct update interval."""
        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            state="nsw",
            latitude=-33.8688,
            longitude=151.2093,
            radius_km=50,
        )

        assert coordinator.update_interval == timedelta(seconds=300)


class TestCoordinatorUpdate:
    """Test coordinator update functionality."""

    async def test_successful_update(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        sample_api_response: dict,
    ) -> None:
        """Test successful data update."""
        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=sample_api_response)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            state="nsw",
            latitude=-33.8688,
            longitude=151.2093,
            radius_km=50,
        )

        data = await coordinator._async_update_data()

        assert isinstance(data, CoordinatorData)
        assert data.total_count == 3
        mock_client.async_get_emergencies_by_state.assert_called_once_with("nsw")

    async def test_empty_response(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        empty_api_response: dict,
    ) -> None:
        """Test handling of empty response."""
        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=empty_api_response)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            state="nsw",
            latitude=-33.8688,
            longitude=151.2093,
            radius_km=50,
        )

        data = await coordinator._async_update_data()

        assert data.total_count == 0
        assert data.incidents == []
        assert data.nearby_count == 0
        assert data.nearest_incident is None

    async def test_connection_error_raises_update_failed(
        self, hass: HomeAssistant, mock_client: MagicMock
    ) -> None:
        """Test connection error raises UpdateFailed."""
        mock_client.async_get_emergencies_by_state = AsyncMock(
            side_effect=ABCEmergencyConnectionError("Connection failed")
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            state="nsw",
            latitude=-33.8688,
            longitude=151.2093,
            radius_km=50,
        )

        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()

    async def test_api_error_raises_update_failed(
        self, hass: HomeAssistant, mock_client: MagicMock
    ) -> None:
        """Test API error raises UpdateFailed."""
        mock_client.async_get_emergencies_by_state = AsyncMock(
            side_effect=ABCEmergencyAPIError("API error")
        )

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            state="nsw",
            latitude=-33.8688,
            longitude=151.2093,
            radius_km=50,
        )

        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()


class TestIncidentProcessing:
    """Test incident data processing."""

    async def test_incidents_have_calculated_distances(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        sample_api_response: dict,
    ) -> None:
        """Test incidents have distance from configured location."""
        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=sample_api_response)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            state="nsw",
            latitude=-33.8688,
            longitude=151.2093,
            radius_km=50,
        )

        data = await coordinator._async_update_data()

        for incident in data.incidents:
            assert incident.distance_km is not None
            assert incident.distance_km >= 0

    async def test_incidents_have_bearings(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        sample_api_response: dict,
    ) -> None:
        """Test incidents have bearing calculated."""
        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=sample_api_response)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            state="nsw",
            latitude=-33.8688,
            longitude=151.2093,
            radius_km=50,
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
        sample_api_response: dict,
    ) -> None:
        """Test incidents are sorted by distance (nearest first)."""
        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=sample_api_response)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            state="nsw",
            latitude=-33.8688,
            longitude=151.2093,
            radius_km=50,
        )

        data = await coordinator._async_update_data()

        assert len(data.incidents) >= 2
        distances = [i.distance_km for i in data.incidents]
        assert distances == sorted(distances)

    async def test_nearest_incident_identified(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        sample_api_response: dict,
    ) -> None:
        """Test nearest incident is correctly identified."""
        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=sample_api_response)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            state="nsw",
            latitude=-33.8688,
            longitude=151.2093,
            radius_km=500,  # Large radius to include all
        )

        data = await coordinator._async_update_data()

        assert data.nearest_incident is not None
        assert data.nearest_incident == data.incidents[0]
        assert data.nearest_distance_km == data.incidents[0].distance_km


class TestNearbyFiltering:
    """Test nearby incident filtering."""

    async def test_nearby_count_correct(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        sample_api_response: dict,
    ) -> None:
        """Test nearby count reflects incidents within radius."""
        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=sample_api_response)

        # First incident is ~20km away, second is ~100km, third is ~400km
        # With 50km radius, only first should be nearby
        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            state="nsw",
            latitude=-33.8688,
            longitude=151.2093,
            radius_km=50,
        )

        data = await coordinator._async_update_data()

        assert data.nearby_count == 1

    async def test_large_radius_includes_all(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        sample_api_response: dict,
    ) -> None:
        """Test large radius includes all incidents."""
        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=sample_api_response)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            state="nsw",
            latitude=-33.8688,
            longitude=151.2093,
            radius_km=500,  # Large enough for all
        )

        data = await coordinator._async_update_data()

        assert data.nearby_count == 3


class TestAlertLevelAggregation:
    """Test alert level aggregation."""

    async def test_highest_alert_level_extreme(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        sample_api_response: dict,
    ) -> None:
        """Test highest alert level is extreme when present in nearby."""
        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=sample_api_response)

        # Use radius that includes the extreme-level incident
        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            state="nsw",
            latitude=-33.8688,
            longitude=151.2093,
            radius_km=50,
        )

        data = await coordinator._async_update_data()

        assert data.highest_alert_level == AlertLevel.EMERGENCY

    async def test_highest_alert_level_empty_when_no_nearby(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        sample_api_response: dict,
    ) -> None:
        """Test highest alert level is empty when no nearby incidents."""
        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=sample_api_response)

        # Very small radius - no incidents nearby
        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            state="nsw",
            latitude=-33.8688,
            longitude=151.2093,
            radius_km=1,
        )

        data = await coordinator._async_update_data()

        assert data.highest_alert_level == ""


class TestIncidentsByType:
    """Test incidents grouped by type."""

    async def test_incidents_by_type_counts(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        sample_api_response: dict,
    ) -> None:
        """Test incidents are correctly grouped by type."""
        mock_client.async_get_emergencies_by_state = AsyncMock(return_value=sample_api_response)

        coordinator = ABCEmergencyCoordinator(
            hass,
            mock_client,
            state="nsw",
            latitude=-33.8688,
            longitude=151.2093,
            radius_km=500,  # Include all
        )

        data = await coordinator._async_update_data()

        assert "Bushfire" in data.incidents_by_type
        assert data.incidents_by_type["Bushfire"] == 2
        assert "Storm" in data.incidents_by_type
        assert data.incidents_by_type["Storm"] == 1


class TestBOMWarningsWithMultiPolygon:
    """Test handling of BOM warnings with MultiPolygon geometry."""

    async def test_multipolygon_geometry_extracts_centroid(
        self, hass: HomeAssistant, mock_client: MagicMock
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
            state="nsw",
            latitude=-33.5,
            longitude=150.5,
            radius_km=100,
        )

        data = await coordinator._async_update_data()

        assert len(data.incidents) == 1
        incident = data.incidents[0]
        # Centroid of the polygon vertices (average of 5 points including repeat)
        # The polygon has vertices: (-33, 150), (-33, 151), (-34, 151), (-34, 150), (-33, 150)
        # Average lat = (-33 -33 -34 -34 -33) / 5 = -33.4
        # Average lon = (150 + 151 + 151 + 150 + 150) / 5 = 150.4
        assert incident.location.latitude == pytest.approx(-33.4, abs=0.1)
        assert incident.location.longitude == pytest.approx(150.4, abs=0.1)


class TestGeometryExtraction:
    """Test geometry extraction edge cases."""

    async def test_geometry_collection_with_polygon_no_point(
        self, hass: HomeAssistant, mock_client: MagicMock
    ) -> None:
        """Test GeometryCollection with polygon but no point uses polygon centroid."""
        response = {
            "emergencies": [
                {
                    "id": "AUREMER-polygon-only",
                    "headline": "Area Warning",
                    "to": "/emergency/warning/AUREMER-polygon-only",
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
                        "type": "GeometryCollection",
                        "geometries": [
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
            hass, mock_client, state="nsw", latitude=-33.5, longitude=150.5, radius_km=100
        )

        data = await coordinator._async_update_data()

        assert len(data.incidents) == 1
        incident = data.incidents[0]
        assert incident.location.latitude == pytest.approx(-33.4, abs=0.1)

    async def test_direct_point_geometry(self, hass: HomeAssistant, mock_client: MagicMock) -> None:
        """Test direct Point geometry type (not in GeometryCollection)."""
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
            hass, mock_client, state="nsw", latitude=-33.5, longitude=150.5, radius_km=100
        )

        data = await coordinator._async_update_data()

        assert len(data.incidents) == 1
        incident = data.incidents[0]
        assert incident.location.latitude == -33.5
        assert incident.location.longitude == 151.0

    async def test_direct_polygon_geometry(
        self, hass: HomeAssistant, mock_client: MagicMock
    ) -> None:
        """Test direct Polygon geometry type (not in GeometryCollection)."""
        response = {
            "emergencies": [
                {
                    "id": "AUREMER-direct-polygon",
                    "headline": "Polygon Warning",
                    "to": "/emergency/warning/AUREMER-direct-polygon",
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
            hass, mock_client, state="nsw", latitude=-33.5, longitude=150.5, radius_km=100
        )

        data = await coordinator._async_update_data()

        assert len(data.incidents) == 1
        incident = data.incidents[0]
        assert incident.location.latitude == pytest.approx(-33.4, abs=0.1)

    async def test_unknown_geometry_type_skipped(
        self, hass: HomeAssistant, mock_client: MagicMock
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
            hass, mock_client, state="nsw", latitude=-33.5, longitude=150.5, radius_km=100
        )

        data = await coordinator._async_update_data()

        # Incident should be skipped due to unknown geometry
        assert len(data.incidents) == 0

    async def test_polygon_with_empty_coordinates(
        self, hass: HomeAssistant, mock_client: MagicMock
    ) -> None:
        """Test Polygon with empty coordinates is skipped."""
        response = {
            "emergencies": [
                {
                    "id": "AUREMER-empty-poly",
                    "headline": "Empty Polygon",
                    "to": "/emergency/warning/AUREMER-empty-poly",
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
                        "type": "Polygon",
                        "coordinates": [],  # Empty coordinates
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
            hass, mock_client, state="nsw", latitude=-33.5, longitude=150.5, radius_km=100
        )

        data = await coordinator._async_update_data()

        # Incident should be skipped due to empty coordinates
        assert len(data.incidents) == 0

    async def test_invalid_timestamp_uses_now(
        self, hass: HomeAssistant, mock_client: MagicMock
    ) -> None:
        """Test invalid timestamp falls back to current time."""
        response = {
            "emergencies": [
                {
                    "id": "AUREMER-bad-time",
                    "headline": "Bad Timestamp",
                    "to": "/emergency/warning/AUREMER-bad-time",
                    "alertLevelInfoPrepared": {
                        "text": "",
                        "level": "moderate",
                        "style": "moderate",
                    },
                    "emergencyTimestampPrepared": {
                        "date": "2025-12-06T03:00:00+00:00",
                        "formattedTime": "2:00:00 pm AEDT",
                        "prefix": "Effective from",
                        "updatedTime": "not-a-valid-timestamp",  # Invalid
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
            hass, mock_client, state="nsw", latitude=-33.5, longitude=150.5, radius_km=100
        )

        before = datetime.now()
        data = await coordinator._async_update_data()
        after = datetime.now()

        assert len(data.incidents) == 1
        # The updated timestamp should be approximately now
        assert before <= data.incidents[0].updated <= after

    async def test_missing_timestamp_key_uses_now(
        self, hass: HomeAssistant, mock_client: MagicMock
    ) -> None:
        """Test missing timestamp key falls back to current time."""
        response = {
            "emergencies": [
                {
                    "id": "AUREMER-no-time",
                    "headline": "No Timestamp",
                    "to": "/emergency/warning/AUREMER-no-time",
                    "alertLevelInfoPrepared": {
                        "text": "",
                        "level": "moderate",
                        "style": "moderate",
                    },
                    "emergencyTimestampPrepared": {
                        "date": "2025-12-06T03:00:00+00:00",
                        "formattedTime": "2:00:00 pm AEDT",
                        "prefix": "Effective from",
                        # "updatedTime" key is missing
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
            hass, mock_client, state="nsw", latitude=-33.5, longitude=150.5, radius_km=100
        )

        before = datetime.now()
        data = await coordinator._async_update_data()
        after = datetime.now()

        assert len(data.incidents) == 1
        assert before <= data.incidents[0].updated <= after

    async def test_polygon_ring_with_invalid_points(
        self, hass: HomeAssistant, mock_client: MagicMock
    ) -> None:
        """Test Polygon with some invalid points only uses valid ones."""
        response = {
            "emergencies": [
                {
                    "id": "AUREMER-partial-points",
                    "headline": "Partial Points",
                    "to": "/emergency/warning/AUREMER-partial-points",
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
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [150.0, -33.0],
                                [151.0],
                                [151.0, -34.0],
                                [],
                                [150.0, -34.0],
                                [150.0, -33.0],
                            ]  # Some invalid points
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
            hass, mock_client, state="nsw", latitude=-33.5, longitude=150.5, radius_km=100
        )

        data = await coordinator._async_update_data()

        assert len(data.incidents) == 1
        # Should still calculate centroid from valid points

    async def test_polygon_with_empty_ring(
        self, hass: HomeAssistant, mock_client: MagicMock
    ) -> None:
        """Test Polygon with empty ring array is skipped."""
        response = {
            "emergencies": [
                {
                    "id": "AUREMER-empty-ring",
                    "headline": "Empty Ring",
                    "to": "/emergency/warning/AUREMER-empty-ring",
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
                        "type": "Polygon",
                        "coordinates": [[]],  # Empty ring
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
            hass, mock_client, state="nsw", latitude=-33.5, longitude=150.5, radius_km=100
        )

        data = await coordinator._async_update_data()

        # Incident should be skipped due to empty ring
        assert len(data.incidents) == 0


class TestModels:
    """Test model classes."""

    def test_coordinator_data_defaults(self) -> None:
        """Test CoordinatorData has correct defaults."""
        data = CoordinatorData()

        assert data.incidents == []
        assert data.total_count == 0
        assert data.nearby_count == 0
        assert data.nearest_distance_km is None
        assert data.nearest_incident is None
        assert data.highest_alert_level == ""
        assert data.incidents_by_type == {}

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
