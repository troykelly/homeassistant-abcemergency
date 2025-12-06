"""Data models for ABC Emergency integration.

This module defines dataclasses for representing emergency incidents
and coordinator data in a type-safe manner.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Coordinate:
    """Geographic coordinate.

    Represents a point on Earth using latitude and longitude.

    Attributes:
        latitude: Latitude in degrees (-90 to 90).
        longitude: Longitude in degrees (-180 to 180).
    """

    latitude: float
    longitude: float


@dataclass
class EmergencyIncident:
    """Processed emergency incident.

    Represents a single emergency incident with all relevant details
    for display and alerting purposes.

    Attributes:
        id: Unique identifier for the incident (e.g., "AUREMER-...").
        headline: Brief headline describing the incident location.
        alert_level: Australian Warning System level (extreme, severe, moderate, minor).
        alert_text: Human-readable alert text (Emergency, Watch and Act, Advice, "").
        event_type: Type of incident (e.g., Bushfire, Flood, Storm).
        event_icon: Icon category (fire, weather, heat, other).
        status: Current status of the incident (e.g., "Being controlled").
        size: Affected area size (e.g., "100 ha").
        source: Reporting agency (e.g., "NSW Rural Fire Service").
        location: Geographic coordinates of the incident.
        updated: Last update timestamp.
        distance_km: Distance from monitored location in kilometers.
        bearing: Bearing from monitored location in degrees (0-360).
        direction: Compass direction from monitored location (N, NE, E, etc.).
    """

    id: str
    headline: str
    alert_level: str
    alert_text: str
    event_type: str
    event_icon: str
    status: str | None
    size: str | None
    source: str
    location: Coordinate
    updated: datetime
    distance_km: float | None = None
    bearing: float | None = None
    direction: str | None = None


@dataclass
class CoordinatorData:
    """Data returned by the coordinator.

    Contains all processed emergency data for consumption by entities.

    Attributes:
        incidents: List of all processed emergency incidents.
        total_count: Total number of incidents in the state.
        nearby_count: Number of incidents within the configured radius.
        nearest_distance_km: Distance to the nearest incident in kilometers.
        nearest_incident: Reference to the nearest incident, if any.
        highest_alert_level: Highest alert level among nearby incidents.
        incidents_by_type: Count of incidents grouped by event type.
    """

    incidents: list[EmergencyIncident] = field(default_factory=list)
    total_count: int = 0
    nearby_count: int = 0
    nearest_distance_km: float | None = None
    nearest_incident: EmergencyIncident | None = None
    highest_alert_level: str = ""
    incidents_by_type: dict[str, int] = field(default_factory=dict)
