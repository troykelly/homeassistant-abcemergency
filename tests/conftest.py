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
