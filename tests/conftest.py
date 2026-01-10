"""Fixtures for ABC Emergency integration tests."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE

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
    INSTANCE_TYPE_PERSON,
    INSTANCE_TYPE_STATE,
    INSTANCE_TYPE_ZONE,
    AlertLevel,
)
from custom_components.abcemergency.models import (
    Coordinate,
    CoordinatorData,
    EmergencyIncident,
)

pytest_plugins = ["pytest_homeassistant_custom_component"]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(
    enable_custom_integrations: None,
) -> Generator[None]:
    """Enable custom integrations for all tests."""
    yield


@pytest.fixture
def mock_config_entry_data_state() -> dict[str, Any]:
    """Return mock config entry data for state instance."""
    return {
        CONF_INSTANCE_TYPE: INSTANCE_TYPE_STATE,
        CONF_STATE: "nsw",
    }


@pytest.fixture
def mock_config_entry_data_zone() -> dict[str, Any]:
    """Return mock config entry data for zone instance."""
    return {
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
    }


@pytest.fixture
def mock_config_entry_data_person() -> dict[str, Any]:
    """Return mock config entry data for person instance."""
    return {
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
    }


# Keep the old fixture name for backward compatibility
@pytest.fixture
def mock_config_entry_data(mock_config_entry_data_state: dict[str, Any]) -> dict[str, Any]:
    """Return mock config entry data (alias for state)."""
    return mock_config_entry_data_state


@pytest.fixture
def mock_incident_bushfire() -> EmergencyIncident:
    """Create a mock bushfire incident."""
    return EmergencyIncident(
        id="AUREMER-12345",
        headline="Bushfire at Test Location",
        alert_level=AlertLevel.EMERGENCY,
        alert_text="Emergency",
        event_type="Bushfire",
        event_icon="fire",
        status="Out of control",
        size="500 ha",
        source="NSW Rural Fire Service",
        location=Coordinate(latitude=-33.9, longitude=151.2),
        updated=datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC),
        distance_km=10.5,
        bearing=180.0,
        direction="S",
    )


@pytest.fixture
def mock_incident_flood() -> EmergencyIncident:
    """Create a mock flood incident."""
    return EmergencyIncident(
        id="AUREMER-12346",
        headline="Flood Warning at River Area",
        alert_level=AlertLevel.WATCH_AND_ACT,
        alert_text="Watch and Act",
        event_type="Flood",
        event_icon="weather",
        status="Developing",
        size=None,
        source="Bureau of Meteorology",
        location=Coordinate(latitude=-33.7, longitude=151.0),
        updated=datetime(2025, 1, 15, 9, 0, 0, tzinfo=UTC),
        distance_km=25.3,
        bearing=315.0,
        direction="NW",
    )


@pytest.fixture
def mock_incident_storm() -> EmergencyIncident:
    """Create a mock storm incident."""
    return EmergencyIncident(
        id="AUREMER-12347",
        headline="Severe Thunderstorm",
        alert_level=AlertLevel.ADVICE,
        alert_text="Advice",
        event_type="Storm",
        event_icon="weather",
        status="Active",
        size=None,
        source="Bureau of Meteorology",
        location=Coordinate(latitude=-34.0, longitude=151.5),
        updated=datetime(2025, 1, 15, 8, 0, 0, tzinfo=UTC),
        distance_km=45.0,
        bearing=135.0,
        direction="SE",
    )


@pytest.fixture
def mock_coordinator_data(
    mock_incident_bushfire: EmergencyIncident,
    mock_incident_flood: EmergencyIncident,
    mock_incident_storm: EmergencyIncident,
) -> CoordinatorData:
    """Create mock coordinator data with multiple incidents (zone/person mode)."""
    return CoordinatorData(
        incidents=[mock_incident_bushfire, mock_incident_flood, mock_incident_storm],
        total_count=3,
        nearby_count=3,
        nearest_distance_km=10.5,
        nearest_incident=mock_incident_bushfire,
        highest_alert_level=AlertLevel.EMERGENCY,
        incidents_by_type={"Bushfire": 1, "Flood": 1, "Storm": 1},
        instance_type=INSTANCE_TYPE_ZONE,
        location_available=True,
        current_latitude=-33.8688,
        current_longitude=151.2093,
    )


@pytest.fixture
def mock_coordinator_data_state(
    mock_incident_bushfire: EmergencyIncident,
    mock_incident_flood: EmergencyIncident,
    mock_incident_storm: EmergencyIncident,
) -> CoordinatorData:
    """Create mock coordinator data for state mode."""
    # Create incidents without distance info for state mode
    bushfire = EmergencyIncident(
        id=mock_incident_bushfire.id,
        headline=mock_incident_bushfire.headline,
        alert_level=mock_incident_bushfire.alert_level,
        alert_text=mock_incident_bushfire.alert_text,
        event_type=mock_incident_bushfire.event_type,
        event_icon=mock_incident_bushfire.event_icon,
        status=mock_incident_bushfire.status,
        size=mock_incident_bushfire.size,
        source=mock_incident_bushfire.source,
        location=mock_incident_bushfire.location,
        updated=mock_incident_bushfire.updated,
        distance_km=None,
        bearing=None,
        direction=None,
    )
    flood = EmergencyIncident(
        id=mock_incident_flood.id,
        headline=mock_incident_flood.headline,
        alert_level=mock_incident_flood.alert_level,
        alert_text=mock_incident_flood.alert_text,
        event_type=mock_incident_flood.event_type,
        event_icon=mock_incident_flood.event_icon,
        status=mock_incident_flood.status,
        size=mock_incident_flood.size,
        source=mock_incident_flood.source,
        location=mock_incident_flood.location,
        updated=mock_incident_flood.updated,
        distance_km=None,
        bearing=None,
        direction=None,
    )
    storm = EmergencyIncident(
        id=mock_incident_storm.id,
        headline=mock_incident_storm.headline,
        alert_level=mock_incident_storm.alert_level,
        alert_text=mock_incident_storm.alert_text,
        event_type=mock_incident_storm.event_type,
        event_icon=mock_incident_storm.event_icon,
        status=mock_incident_storm.status,
        size=mock_incident_storm.size,
        source=mock_incident_storm.source,
        location=mock_incident_storm.location,
        updated=mock_incident_storm.updated,
        distance_km=None,
        bearing=None,
        direction=None,
    )

    return CoordinatorData(
        incidents=[bushfire, flood, storm],
        total_count=3,
        nearby_count=None,  # Not applicable for state mode
        nearest_distance_km=None,
        nearest_incident=None,
        highest_alert_level=AlertLevel.EMERGENCY,
        incidents_by_type={"Bushfire": 1, "Flood": 1, "Storm": 1},
        instance_type=INSTANCE_TYPE_STATE,
        location_available=True,
    )


@pytest.fixture
def mock_coordinator_data_empty() -> CoordinatorData:
    """Create empty coordinator data."""
    return CoordinatorData(
        incidents=[],
        total_count=0,
        nearby_count=0,
        nearest_distance_km=None,
        nearest_incident=None,
        highest_alert_level="",
        incidents_by_type={},
        instance_type=INSTANCE_TYPE_ZONE,
        location_available=True,
    )


@pytest.fixture
def mock_coordinator(
    mock_coordinator_data: CoordinatorData,
) -> MagicMock:
    """Create a mock coordinator (zone mode)."""
    coordinator = MagicMock()
    coordinator.data = mock_coordinator_data
    coordinator.last_update_success = True
    return coordinator


@pytest.fixture
def mock_coordinator_state(
    mock_coordinator_data_state: CoordinatorData,
) -> MagicMock:
    """Create a mock coordinator (state mode)."""
    coordinator = MagicMock()
    coordinator.data = mock_coordinator_data_state
    coordinator.last_update_success = True
    return coordinator


@pytest.fixture
def mock_coordinator_empty(
    mock_coordinator_data_empty: CoordinatorData,
) -> MagicMock:
    """Create a mock coordinator with no data."""
    coordinator = MagicMock()
    coordinator.data = mock_coordinator_data_empty
    coordinator.last_update_success = True
    return coordinator


@pytest.fixture
def mock_coordinator_data_with_containment() -> CoordinatorData:
    """Create mock coordinator data with containment information."""
    # Create incidents with containment data
    containing_incident = EmergencyIncident(
        id="AUREMER-CONTAIN-1",
        headline="Bushfire Inside Zone",
        alert_level=AlertLevel.EMERGENCY,
        alert_text="Emergency",
        event_type="Bushfire",
        event_icon="fire",
        status="Going",
        size="Large",
        source="NSW RFS",
        location=Coordinate(latitude=-33.88, longitude=151.19),
        updated=datetime(2025, 1, 15, 10, 0, 0, tzinfo=UTC),
        distance_km=5.5,
        bearing=180.0,
        direction="S",
        has_polygon=True,
        contains_point=True,
    )

    nearby_no_contain = EmergencyIncident(
        id="AUREMER-NEARBY-1",
        headline="Storm Nearby",
        alert_level=AlertLevel.WATCH_AND_ACT,
        alert_text="Watch and Act",
        event_type="Storm",
        event_icon="weather",
        status="Active",
        size=None,
        source="BoM",
        location=Coordinate(latitude=-33.9, longitude=151.3),
        updated=datetime(2025, 1, 15, 9, 0, 0, tzinfo=UTC),
        distance_km=15.0,
        bearing=90.0,
        direction="E",
        has_polygon=True,
        contains_point=False,
    )

    point_only_incident = EmergencyIncident(
        id="AUREMER-POINT-1",
        headline="Traffic Hazard",
        alert_level=AlertLevel.ADVICE,
        alert_text="Advice",
        event_type="Traffic",
        event_icon="other",
        status="Active",
        size=None,
        source="NSW Police",
        location=Coordinate(latitude=-33.85, longitude=151.21),
        updated=datetime(2025, 1, 15, 8, 0, 0, tzinfo=UTC),
        distance_km=3.0,
        bearing=45.0,
        direction="NE",
        has_polygon=False,
        contains_point=False,
    )

    return CoordinatorData(
        incidents=[containing_incident, nearby_no_contain, point_only_incident],
        total_count=3,
        nearby_count=3,
        nearest_distance_km=3.0,
        nearest_incident=point_only_incident,
        highest_alert_level=AlertLevel.EMERGENCY,
        incidents_by_type={"Bushfire": 1, "Storm": 1, "Traffic": 1},
        instance_type=INSTANCE_TYPE_ZONE,
        location_available=True,
        current_latitude=-33.8688,
        current_longitude=151.2093,
        containing_incidents=[containing_incident],
        inside_polygon=True,
        inside_emergency_warning=True,
        inside_watch_and_act=True,
        inside_advice=True,
        highest_containing_alert_level=AlertLevel.EMERGENCY,
    )


@pytest.fixture
def mock_coordinator_with_containment(
    mock_coordinator_data_with_containment: CoordinatorData,
) -> MagicMock:
    """Create a mock coordinator with containment data."""
    coordinator = MagicMock()
    coordinator.data = mock_coordinator_data_with_containment
    coordinator.last_update_success = True
    return coordinator


@pytest.fixture
def mock_incident_with_single_polygon() -> EmergencyIncident:
    """Create a mock incident with a single polygon geometry."""
    return EmergencyIncident(
        id="AUREMER-POLY-1",
        headline="Bushfire with Polygon Boundary",
        alert_level=AlertLevel.EMERGENCY,
        alert_text="Emergency",
        event_type="Bushfire",
        event_icon="fire",
        status="Out of control",
        size="1000 ha",
        source="NSW Rural Fire Service",
        location=Coordinate(latitude=-33.85, longitude=151.25),
        updated=datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC),
        distance_km=15.0,
        bearing=90.0,
        direction="E",
        geometry_type="Polygon",
        has_polygon=True,
        polygons=[
            {
                "outer_ring": [
                    [151.2, -33.8],
                    [151.3, -33.8],
                    [151.3, -33.9],
                    [151.2, -33.9],
                    [151.2, -33.8],
                ],
                "inner_rings": None,
            }
        ],
    )


@pytest.fixture
def mock_incident_with_polygon_and_hole() -> EmergencyIncident:
    """Create a mock incident with a polygon containing a hole (inner ring)."""
    return EmergencyIncident(
        id="AUREMER-POLY-HOLE-1",
        headline="Flood Warning with Exclusion Zone",
        alert_level=AlertLevel.WATCH_AND_ACT,
        alert_text="Watch and Act",
        event_type="Flood",
        event_icon="weather",
        status="Active",
        size=None,
        source="Bureau of Meteorology",
        location=Coordinate(latitude=-33.85, longitude=151.25),
        updated=datetime(2025, 1, 15, 11, 0, 0, tzinfo=UTC),
        distance_km=20.0,
        bearing=45.0,
        direction="NE",
        geometry_type="Polygon",
        has_polygon=True,
        polygons=[
            {
                "outer_ring": [
                    [151.0, -33.7],
                    [151.4, -33.7],
                    [151.4, -34.0],
                    [151.0, -34.0],
                    [151.0, -33.7],
                ],
                "inner_rings": [
                    [
                        [151.15, -33.8],
                        [151.25, -33.8],
                        [151.25, -33.9],
                        [151.15, -33.9],
                        [151.15, -33.8],
                    ]
                ],
            }
        ],
    )


@pytest.fixture
def mock_incident_with_multipolygon() -> EmergencyIncident:
    """Create a mock incident with multiple polygons (MultiPolygon)."""
    return EmergencyIncident(
        id="AUREMER-MULTI-1",
        headline="Storm Warning Multiple Areas",
        alert_level=AlertLevel.ADVICE,
        alert_text="Advice",
        event_type="Storm",
        event_icon="weather",
        status="Developing",
        size=None,
        source="Bureau of Meteorology",
        location=Coordinate(latitude=-33.9, longitude=151.3),
        updated=datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC),
        distance_km=30.0,
        bearing=135.0,
        direction="SE",
        geometry_type="MultiPolygon",
        has_polygon=True,
        polygons=[
            {
                "outer_ring": [
                    [151.2, -33.8],
                    [151.3, -33.8],
                    [151.3, -33.9],
                    [151.2, -33.9],
                    [151.2, -33.8],
                ],
                "inner_rings": None,
            },
            {
                "outer_ring": [
                    [151.4, -33.7],
                    [151.5, -33.7],
                    [151.5, -33.8],
                    [151.4, -33.8],
                    [151.4, -33.7],
                ],
                "inner_rings": None,
            },
        ],
    )


@pytest.fixture
def mock_incident_point_only() -> EmergencyIncident:
    """Create a mock incident with only a point (no polygon)."""
    return EmergencyIncident(
        id="AUREMER-POINT-ONLY-1",
        headline="Traffic Incident",
        alert_level=AlertLevel.ADVICE,
        alert_text="Advice",
        event_type="Traffic",
        event_icon="other",
        status="Active",
        size=None,
        source="NSW Police",
        location=Coordinate(latitude=-33.88, longitude=151.21),
        updated=datetime(2025, 1, 15, 13, 0, 0, tzinfo=UTC),
        distance_km=5.0,
        bearing=0.0,
        direction="N",
        geometry_type="Point",
        has_polygon=False,
        polygons=None,
    )


@pytest.fixture
def mock_incident_with_multipolygon_and_holes() -> EmergencyIncident:
    """Create a mock incident with multiple polygons including holes."""
    return EmergencyIncident(
        id="AUREMER-MULTI-HOLES-1",
        headline="Flood Warning with Multiple Areas and Exclusions",
        alert_level=AlertLevel.WATCH_AND_ACT,
        alert_text="Watch and Act",
        event_type="Flood",
        event_icon="weather",
        status="Active",
        size=None,
        source="Bureau of Meteorology",
        location=Coordinate(latitude=-33.9, longitude=151.3),
        updated=datetime(2025, 1, 15, 14, 0, 0, tzinfo=UTC),
        distance_km=35.0,
        bearing=120.0,
        direction="ESE",
        geometry_type="MultiPolygon",
        has_polygon=True,
        polygons=[
            {
                "outer_ring": [
                    [151.2, -33.8],
                    [151.3, -33.8],
                    [151.3, -33.9],
                    [151.2, -33.9],
                    [151.2, -33.8],
                ],
                "inner_rings": [
                    [
                        [151.22, -33.82],
                        [151.28, -33.82],
                        [151.28, -33.88],
                        [151.22, -33.88],
                        [151.22, -33.82],
                    ]
                ],
            },
            {
                "outer_ring": [
                    [151.4, -33.7],
                    [151.5, -33.7],
                    [151.5, -33.8],
                    [151.4, -33.8],
                    [151.4, -33.7],
                ],
                "inner_rings": None,
            },
        ],
    )


@pytest.fixture
def mock_incident_has_polygon_but_empty_list() -> EmergencyIncident:
    """Create a mock incident with has_polygon=True but empty polygons list."""
    return EmergencyIncident(
        id="AUREMER-EMPTY-POLY-1",
        headline="Incident with empty polygon list",
        alert_level=AlertLevel.ADVICE,
        alert_text="Advice",
        event_type="Fire",
        event_icon="fire",
        status="Active",
        size=None,
        source="NSW RFS",
        location=Coordinate(latitude=-33.88, longitude=151.21),
        updated=datetime(2025, 1, 15, 15, 0, 0, tzinfo=UTC),
        distance_km=5.0,
        bearing=0.0,
        direction="N",
        geometry_type="Polygon",
        has_polygon=True,
        polygons=[],
    )


def make_feature_for_emergency(emergency_id: str, state: str = "nsw") -> dict[str, Any]:
    """Create a minimal feature object matching an emergency for state filtering.

    The ABC Emergency API returns features with a 1:1 mapping to emergencies.
    Each feature has a `properties.state` field that indicates which state
    the emergency belongs to. This function creates a minimal feature object
    for testing purposes.

    Args:
        emergency_id: The ID of the emergency (must match emergency["id"]).
        state: The state code (e.g., "nsw", "vic", "qld").

    Returns:
        A minimal feature dict suitable for API response mocking.
    """
    return {
        "type": "Feature",
        "id": emergency_id,
        "geometry": {"type": "Point", "coordinates": [151.0, -33.87]},
        "properties": {
            "id": emergency_id,
            "state": state,
            "headline": "Test Feature",
        },
    }


def add_features_to_response(
    response: dict[str, Any],
    state: str = "nsw",
) -> dict[str, Any]:
    """Add features array to an API response based on emergencies.

    This function takes an API response dict and populates the features array
    with corresponding feature objects for each emergency. This is needed
    because the coordinator filters emergencies by state using the features array.

    Args:
        response: The API response dict containing "emergencies" and "features".
        state: The state code to assign to all features (default "nsw").

    Returns:
        The modified response with populated features array.
    """
    emergencies = response.get("emergencies", [])
    features = [make_feature_for_emergency(e["id"], state) for e in emergencies]
    response["features"] = features
    return response
