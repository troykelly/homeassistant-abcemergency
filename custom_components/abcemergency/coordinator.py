"""DataUpdateCoordinator for ABC Emergency.

This module provides the coordinator that manages polling the ABC Emergency API
and distributing data to all entities. It handles distance calculations, data
transformation, and aggregation of emergency incident information.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, cast

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import ABCEmergencyClient
from .const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    AlertLevel,
    Emergency,
    Geometry,
    GeometryCollectionGeometry,
    PolygonGeometry,
    TopLevelMultiPolygonGeometry,
    TopLevelPointGeometry,
    TopLevelPolygonGeometry,
)
from .exceptions import ABCEmergencyAPIError, ABCEmergencyConnectionError
from .helpers import bearing_to_direction, calculate_distance, get_bearing
from .models import Coordinate, CoordinatorData, EmergencyIncident

if TYPE_CHECKING:
    pass

_LOGGER = logging.getLogger(__name__)

# Priority order for alert levels (highest to lowest)
ALERT_LEVEL_PRIORITY: dict[str, int] = {
    AlertLevel.EMERGENCY: 4,
    AlertLevel.WATCH_AND_ACT: 3,
    AlertLevel.ADVICE: 2,
    AlertLevel.INFORMATION: 1,
    "": 0,
}


class ABCEmergencyCoordinator(DataUpdateCoordinator[CoordinatorData]):
    """Coordinator for ABC Emergency data.

    This coordinator polls the ABC Emergency API at regular intervals and
    processes the data for consumption by entities. It calculates distances
    and bearings from the configured location and aggregates data for quick
    access by sensors.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        client: ABCEmergencyClient,
        *,
        state: str,
        latitude: float,
        longitude: float,
        radius_km: float,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance.
            client: ABC Emergency API client.
            state: Australian state/territory code (e.g., "nsw").
            latitude: Latitude of the monitored location.
            longitude: Longitude of the monitored location.
            radius_km: Radius in kilometers for "nearby" alerts.
        """
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

        self._client = client
        self._state = state
        self._latitude = latitude
        self._longitude = longitude
        self._radius_km = radius_km

    async def _async_update_data(self) -> CoordinatorData:
        """Fetch and process emergency data.

        Returns:
            Processed coordinator data with all emergency information.

        Raises:
            UpdateFailed: If fetching or processing data fails.
        """
        try:
            _LOGGER.debug("Fetching emergency data for state: %s", self._state)
            response = await self._client.async_get_emergencies_by_state(self._state)

        except ABCEmergencyConnectionError as err:
            raise UpdateFailed(f"Connection error: {err}") from err
        except ABCEmergencyAPIError as err:
            raise UpdateFailed(f"API error: {err}") from err

        return self._process_emergencies(response["emergencies"])

    def _process_emergencies(
        self,
        emergencies: list[Emergency],
    ) -> CoordinatorData:
        """Process raw API data into coordinator data.

        Args:
            emergencies: List of emergency objects from the API.

        Returns:
            Processed coordinator data.
        """
        incidents: list[EmergencyIncident] = []

        for emergency in emergencies:
            incident = self._create_incident(emergency)
            if incident:
                incidents.append(incident)

        # Sort by distance (nearest first)
        incidents.sort(key=lambda i: i.distance_km if i.distance_km is not None else float("inf"))

        # Calculate nearby incidents
        nearby_incidents = [
            i for i in incidents if i.distance_km is not None and i.distance_km <= self._radius_km
        ]

        # Find nearest incident
        nearest_incident: EmergencyIncident | None = None
        nearest_distance: float | None = None
        if incidents:
            nearest_incident = incidents[0]
            nearest_distance = nearest_incident.distance_km

        # Determine highest alert level in nearby area
        highest_alert_level = self._get_highest_alert_level(nearby_incidents)

        # Count incidents by type
        incidents_by_type: dict[str, int] = {}
        for incident in incidents:
            event_type = incident.event_type
            incidents_by_type[event_type] = incidents_by_type.get(event_type, 0) + 1

        return CoordinatorData(
            incidents=incidents,
            total_count=len(incidents),
            nearby_count=len(nearby_incidents),
            nearest_distance_km=nearest_distance,
            nearest_incident=nearest_incident,
            highest_alert_level=highest_alert_level,
            incidents_by_type=incidents_by_type,
        )

    def _create_incident(self, emergency: Emergency) -> EmergencyIncident | None:
        """Create an EmergencyIncident from raw API data.

        Args:
            emergency: Emergency object from the API.

        Returns:
            Processed EmergencyIncident or None if coordinates can't be extracted.
        """
        # Extract coordinates from geometry
        location = self._extract_location(emergency["geometry"])
        if location is None:
            _LOGGER.warning(
                "Could not extract location for emergency: %s",
                emergency["id"],
            )
            return None

        # Calculate distance and bearing from configured location
        distance = calculate_distance(
            self._latitude,
            self._longitude,
            location.latitude,
            location.longitude,
        )
        bearing = get_bearing(
            self._latitude,
            self._longitude,
            location.latitude,
            location.longitude,
        )
        direction = bearing_to_direction(bearing)

        # Parse timestamp
        try:
            updated = datetime.fromisoformat(emergency["emergencyTimestampPrepared"]["updatedTime"])
        except (ValueError, KeyError):
            updated = datetime.now()

        return EmergencyIncident(
            id=emergency["id"],
            headline=emergency["headline"],
            alert_level=emergency["alertLevelInfoPrepared"]["level"],
            alert_text=emergency["alertLevelInfoPrepared"]["text"],
            event_type=emergency["eventLabelPrepared"]["labelText"],
            event_icon=emergency["eventLabelPrepared"]["icon"],
            status=emergency["cardBody"]["status"],
            size=emergency["cardBody"]["size"],
            source=emergency["cardBody"]["source"],
            location=location,
            updated=updated,
            distance_km=distance,
            bearing=bearing,
            direction=direction,
        )

    def _extract_location(self, geometry: Geometry) -> Coordinate | None:
        """Extract location coordinates from geometry.

        Handles various geometry types:
        - GeometryCollection: Uses first Point geometry
        - Point: Uses coordinates directly
        - Polygon/MultiPolygon: Calculates centroid

        Args:
            geometry: Geometry object from the API.

        Returns:
            Coordinate with latitude and longitude, or None if extraction fails.
        """
        geom_type = geometry["type"]

        if geom_type == "GeometryCollection":
            collection = cast(GeometryCollectionGeometry, geometry)
            geometries = collection["geometries"]
            for geom in geometries:
                if geom["type"] == "Point":
                    # Type is automatically narrowed to PointGeometry
                    coords = geom["coordinates"]
                    if len(coords) >= 2:
                        # GeoJSON uses [longitude, latitude]
                        return Coordinate(latitude=coords[1], longitude=coords[0])
            # If no point found, try to get centroid of first polygon
            for geom in geometries:
                if geom["type"] == "Polygon":
                    # Type is automatically narrowed to PolygonGeometry
                    return self._calculate_polygon_centroid_from_polygon(geom)

        elif geom_type == "Point":
            point = cast(TopLevelPointGeometry, geometry)
            coords = point["coordinates"]
            if len(coords) >= 2:
                return Coordinate(latitude=coords[1], longitude=coords[0])

        elif geom_type == "Polygon":
            return self._calculate_polygon_centroid(cast(TopLevelPolygonGeometry, geometry))

        elif geom_type == "MultiPolygon":
            return self._calculate_multipolygon_centroid(
                cast(TopLevelMultiPolygonGeometry, geometry)
            )

        return None

    def _calculate_polygon_centroid(self, geometry: TopLevelPolygonGeometry) -> Coordinate | None:
        """Calculate the centroid of a top-level polygon.

        This is a simple average of all coordinates, which gives an
        approximate center point for the polygon.

        Args:
            geometry: TopLevelPolygonGeometry object.

        Returns:
            Coordinate representing the centroid, or None if calculation fails.
        """
        coords = geometry["coordinates"]
        if not coords:
            return None

        all_points: list[tuple[float, float]] = []

        # Polygon: [[[lon, lat], ...]]
        if len(coords) > 0:
            ring = coords[0]  # Outer ring
            for point in ring:
                if len(point) >= 2:
                    all_points.append((point[0], point[1]))

        if not all_points:
            return None

        # Calculate average
        avg_lon = sum(p[0] for p in all_points) / len(all_points)
        avg_lat = sum(p[1] for p in all_points) / len(all_points)

        return Coordinate(latitude=avg_lat, longitude=avg_lon)

    def _calculate_multipolygon_centroid(
        self, geometry: TopLevelMultiPolygonGeometry
    ) -> Coordinate | None:
        """Calculate the centroid of a multipolygon.

        This is a simple average of all coordinates, which gives an
        approximate center point for the multipolygon.

        Args:
            geometry: TopLevelMultiPolygonGeometry object.

        Returns:
            Coordinate representing the centroid, or None if calculation fails.
        """
        coords = geometry["coordinates"]
        if not coords:
            return None

        all_points: list[tuple[float, float]] = []

        # MultiPolygon: [[[[lon, lat], ...]]]
        for polygon in coords:
            if polygon and len(polygon) > 0:
                ring = polygon[0]  # Outer ring
                for point in ring:
                    if len(point) >= 2:
                        all_points.append((point[0], point[1]))

        if not all_points:
            return None

        # Calculate average
        avg_lon = sum(p[0] for p in all_points) / len(all_points)
        avg_lat = sum(p[1] for p in all_points) / len(all_points)

        return Coordinate(latitude=avg_lat, longitude=avg_lon)

    def _calculate_polygon_centroid_from_polygon(
        self, geometry: PolygonGeometry
    ) -> Coordinate | None:
        """Calculate the centroid of a nested polygon geometry.

        This is a simple average of all coordinates, which gives an
        approximate center point for the polygon.

        Args:
            geometry: PolygonGeometry object (nested, no CRS).

        Returns:
            Coordinate representing the centroid, or None if calculation fails.
        """
        coords = geometry["coordinates"]
        if not coords:
            return None

        all_points: list[tuple[float, float]] = []

        # Polygon: [[[lon, lat], ...]]
        if len(coords) > 0:
            ring = coords[0]  # Outer ring
            for point in ring:
                if len(point) >= 2:
                    all_points.append((point[0], point[1]))

        if not all_points:
            return None

        # Calculate average
        avg_lon = sum(p[0] for p in all_points) / len(all_points)
        avg_lat = sum(p[1] for p in all_points) / len(all_points)

        return Coordinate(latitude=avg_lat, longitude=avg_lon)

    def _get_highest_alert_level(
        self,
        incidents: list[EmergencyIncident],
    ) -> str:
        """Get the highest alert level among incidents.

        Args:
            incidents: List of emergency incidents.

        Returns:
            The highest alert level string, or empty string if no incidents.
        """
        if not incidents:
            return ""

        highest_priority = 0
        highest_level = ""

        for incident in incidents:
            level = incident.alert_level
            priority = ALERT_LEVEL_PRIORITY.get(level, 0)
            if priority > highest_priority:
                highest_priority = priority
                highest_level = level

        return highest_level
