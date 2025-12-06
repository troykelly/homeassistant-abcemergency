"""Fixtures for ABC Emergency integration tests."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_RADIUS

from custom_components.abcemergency.const import (
    CONF_STATE,
    CONF_USE_HOME_LOCATION,
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
) -> Generator[None, None, None]:
    """Enable custom integrations for all tests."""
    yield


@pytest.fixture
def mock_config_entry_data() -> dict[str, Any]:
    """Return mock config entry data."""
    return {
        CONF_STATE: "nsw",
        CONF_LATITUDE: -33.8688,
        CONF_LONGITUDE: 151.2093,
        CONF_RADIUS: 50,
        CONF_USE_HOME_LOCATION: True,
    }


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
    """Create mock coordinator data with multiple incidents."""
    return CoordinatorData(
        incidents=[mock_incident_bushfire, mock_incident_flood, mock_incident_storm],
        total_count=3,
        nearby_count=3,
        nearest_distance_km=10.5,
        nearest_incident=mock_incident_bushfire,
        highest_alert_level=AlertLevel.EMERGENCY,
        incidents_by_type={"Bushfire": 1, "Flood": 1, "Storm": 1},
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
    )


@pytest.fixture
def mock_coordinator(
    mock_coordinator_data: CoordinatorData,
) -> MagicMock:
    """Create a mock coordinator."""
    coordinator = MagicMock()
    coordinator.data = mock_coordinator_data
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
