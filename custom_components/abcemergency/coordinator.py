"""DataUpdateCoordinator for ABC Emergency.

This module provides the coordinator that manages polling the ABC Emergency API
and distributing data to all entities. It handles distance calculations, data
transformation, and aggregation of emergency incident information.

The coordinator supports three instance types:
- State: Monitors all incidents in a selected state
- Zone: Monitors incidents near a fixed location
- Person: Monitors incidents near a person's dynamic location
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Literal, cast

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import ABCEmergencyClient
from .const import (
    CONF_RADIUS_BUSHFIRE,
    CONF_RADIUS_EARTHQUAKE,
    CONF_RADIUS_FIRE,
    CONF_RADIUS_FLOOD,
    CONF_RADIUS_HEAT,
    CONF_RADIUS_OTHER,
    CONF_RADIUS_STORM,
    DEFAULT_RADIUS_BUSHFIRE,
    DEFAULT_RADIUS_EARTHQUAKE,
    DEFAULT_RADIUS_FIRE,
    DEFAULT_RADIUS_FLOOD,
    DEFAULT_RADIUS_HEAT,
    DEFAULT_RADIUS_OTHER,
    DEFAULT_RADIUS_STORM,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    INCIDENT_TYPE_TO_RADIUS_CATEGORY,
    INSTANCE_TYPE_PERSON,
    INSTANCE_TYPE_STATE,
    INSTANCE_TYPE_ZONE,
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
from .helpers import (
    bearing_to_direction,
    calculate_distance,
    get_bearing,
    get_state_from_coordinates,
)
from .models import Coordinate, CoordinatorData, EmergencyIncident

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

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
    processes the data for consumption by entities. It supports three modes:
    - State mode: Fetches all incidents for a state
    - Zone mode: Fetches incidents and filters by distance from a fixed location
    - Person mode: Fetches incidents and filters by distance from a person's location
    """

    def __init__(
        self,
        hass: HomeAssistant,
        client: ABCEmergencyClient,
        entry: ConfigEntry,
        *,
        instance_type: Literal["state", "zone", "person"],
        state: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        person_entity_id: str | None = None,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance.
            client: ABC Emergency API client.
            entry: Config entry for this coordinator.
            instance_type: Type of instance (state, zone, person).
            state: Australian state/territory code (for state mode).
            latitude: Latitude of the monitored location (for zone mode).
            longitude: Longitude of the monitored location (for zone mode).
            person_entity_id: Person entity ID (for person mode).
        """
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

        self._client = client
        self._entry = entry
        self._instance_type = instance_type
        self._state = state
        self._latitude = latitude
        self._longitude = longitude
        self._person_entity_id = person_entity_id

        # Radii configuration (for zone/person modes)
        self._radii: dict[str, int] = self._load_radii()

    def _load_radii(self) -> dict[str, int]:
        """Load radius configuration from entry data/options."""

        def get_radius(key: str, default: int) -> int:
            value = self._entry.options.get(key, self._entry.data.get(key, default))
            return int(value) if value is not None else default

        return {
            "bushfire": get_radius(CONF_RADIUS_BUSHFIRE, DEFAULT_RADIUS_BUSHFIRE),
            "earthquake": get_radius(CONF_RADIUS_EARTHQUAKE, DEFAULT_RADIUS_EARTHQUAKE),
            "storm": get_radius(CONF_RADIUS_STORM, DEFAULT_RADIUS_STORM),
            "flood": get_radius(CONF_RADIUS_FLOOD, DEFAULT_RADIUS_FLOOD),
            "fire": get_radius(CONF_RADIUS_FIRE, DEFAULT_RADIUS_FIRE),
            "heat": get_radius(CONF_RADIUS_HEAT, DEFAULT_RADIUS_HEAT),
            "other": get_radius(CONF_RADIUS_OTHER, DEFAULT_RADIUS_OTHER),
        }

    def _get_radius_for_incident(self, event_type: str) -> int:
        """Get the configured radius for an incident type."""
        category = INCIDENT_TYPE_TO_RADIUS_CATEGORY.get(event_type, "other")
        return self._radii.get(category, self._radii["other"])

    async def _async_update_data(self) -> CoordinatorData:
        """Fetch and process emergency data.

        Returns:
            Processed coordinator data with all emergency information.

        Raises:
            UpdateFailed: If fetching or processing data fails.
        """
        if self._instance_type == INSTANCE_TYPE_STATE:
            return await self._update_state_mode()
        if self._instance_type == INSTANCE_TYPE_ZONE:
            return await self._update_zone_mode()
        if self._instance_type == INSTANCE_TYPE_PERSON:
            return await self._update_person_mode()

        raise UpdateFailed(f"Unknown instance type: {self._instance_type}")

    async def _update_state_mode(self) -> CoordinatorData:
        """Fetch data for state mode (all incidents in a state)."""
        if not self._state:
            raise UpdateFailed("No state configured")

        try:
            _LOGGER.debug("Fetching emergency data for state: %s", self._state)
            response = await self._client.async_get_emergencies_by_state(self._state)
        except ABCEmergencyConnectionError as err:
            raise UpdateFailed(f"Connection error: {err}") from err
        except ABCEmergencyAPIError as err:
            raise UpdateFailed(f"API error: {err}") from err

        return self._process_state_emergencies(response["emergencies"])

    async def _update_zone_mode(self) -> CoordinatorData:
        """Fetch data for zone mode (incidents near a fixed location)."""
        if self._latitude is None or self._longitude is None:
            raise UpdateFailed("No location configured")

        # Determine which state to query based on coordinates
        state = get_state_from_coordinates(self._latitude, self._longitude)
        if not state:
            raise UpdateFailed("Could not determine state from coordinates")

        try:
            _LOGGER.debug(
                "Fetching emergency data for zone at %s, %s", self._latitude, self._longitude
            )
            response = await self._client.async_get_emergencies_by_state(state)
        except ABCEmergencyConnectionError as err:
            raise UpdateFailed(f"Connection error: {err}") from err
        except ABCEmergencyAPIError as err:
            raise UpdateFailed(f"API error: {err}") from err

        return self._process_location_emergencies(
            response["emergencies"],
            self._latitude,
            self._longitude,
            INSTANCE_TYPE_ZONE,
        )

    async def _update_person_mode(self) -> CoordinatorData:
        """Fetch data for person mode (incidents near a person's location)."""
        if not self._person_entity_id:
            raise UpdateFailed("No person entity configured")

        # Get person's current location
        person_state = self.hass.states.get(self._person_entity_id)
        if person_state is None:
            raise UpdateFailed(f"Person entity {self._person_entity_id} not found")

        latitude = person_state.attributes.get("latitude")
        longitude = person_state.attributes.get("longitude")

        if latitude is None or longitude is None:
            # Person location is unknown - return empty data
            _LOGGER.debug("Person %s has no location data", self._person_entity_id)
            return CoordinatorData(
                incidents=[],
                total_count=0,
                nearby_count=0,
                instance_type=INSTANCE_TYPE_PERSON,
                location_available=False,
            )

        # Determine which state to query based on coordinates
        state = get_state_from_coordinates(latitude, longitude)
        if not state:
            # Person might be outside Australia
            _LOGGER.debug("Person %s is outside tracked area", self._person_entity_id)
            return CoordinatorData(
                incidents=[],
                total_count=0,
                nearby_count=0,
                instance_type=INSTANCE_TYPE_PERSON,
                location_available=True,
                current_latitude=latitude,
                current_longitude=longitude,
            )

        try:
            _LOGGER.debug("Fetching emergency data for person at %s, %s", latitude, longitude)
            response = await self._client.async_get_emergencies_by_state(state)
        except ABCEmergencyConnectionError as err:
            raise UpdateFailed(f"Connection error: {err}") from err
        except ABCEmergencyAPIError as err:
            raise UpdateFailed(f"API error: {err}") from err

        return self._process_location_emergencies(
            response["emergencies"],
            latitude,
            longitude,
            INSTANCE_TYPE_PERSON,
        )

    def _process_state_emergencies(
        self,
        emergencies: list[Emergency],
    ) -> CoordinatorData:
        """Process emergencies for state mode (no distance filtering).

        Args:
            emergencies: List of emergency objects from the API.

        Returns:
            Processed coordinator data.
        """
        incidents: list[EmergencyIncident] = []

        for emergency in emergencies:
            incident = self._create_incident(emergency, latitude=None, longitude=None)
            if incident:
                incidents.append(incident)

        # Determine highest alert level in state
        highest_alert_level = self._get_highest_alert_level(incidents)

        # Count incidents by type
        incidents_by_type: dict[str, int] = {}
        for incident in incidents:
            event_type = incident.event_type
            incidents_by_type[event_type] = incidents_by_type.get(event_type, 0) + 1

        return CoordinatorData(
            incidents=incidents,
            total_count=len(incidents),
            nearby_count=None,  # Not applicable for state mode
            nearest_distance_km=None,  # Not applicable for state mode
            nearest_incident=None,  # Not applicable for state mode
            highest_alert_level=highest_alert_level,
            incidents_by_type=incidents_by_type,
            instance_type=INSTANCE_TYPE_STATE,
            location_available=True,
        )

    def _process_location_emergencies(
        self,
        emergencies: list[Emergency],
        latitude: float,
        longitude: float,
        instance_type: Literal["zone", "person"],
    ) -> CoordinatorData:
        """Process emergencies for zone/person mode (with distance filtering).

        Args:
            emergencies: List of emergency objects from the API.
            latitude: Reference latitude.
            longitude: Reference longitude.
            instance_type: Type of instance (zone or person).

        Returns:
            Processed coordinator data.
        """
        incidents: list[EmergencyIncident] = []

        for emergency in emergencies:
            incident = self._create_incident(emergency, latitude=latitude, longitude=longitude)
            if incident:
                incidents.append(incident)

        # Sort by distance (nearest first)
        incidents.sort(key=lambda i: i.distance_km if i.distance_km is not None else float("inf"))

        # Calculate nearby incidents based on per-type radii
        nearby_incidents = [
            i
            for i in incidents
            if i.distance_km is not None
            and i.distance_km <= self._get_radius_for_incident(i.event_type)
        ]

        # Find nearest incident
        nearest_incident: EmergencyIncident | None = None
        nearest_distance: float | None = None
        if incidents:
            nearest_incident = incidents[0]
            nearest_distance = nearest_incident.distance_km

        # Determine highest alert level in nearby area
        highest_alert_level = self._get_highest_alert_level(nearby_incidents)

        # Count incidents by type (for nearby incidents)
        incidents_by_type: dict[str, int] = {}
        for incident in nearby_incidents:
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
            instance_type=instance_type,
            location_available=True,
            current_latitude=latitude,
            current_longitude=longitude,
        )

    def _create_incident(
        self,
        emergency: Emergency,
        *,
        latitude: float | None,
        longitude: float | None,
    ) -> EmergencyIncident | None:
        """Create an EmergencyIncident from raw API data.

        Args:
            emergency: Emergency object from the API.
            latitude: Reference latitude for distance calculation (None for state mode).
            longitude: Reference longitude for distance calculation (None for state mode).

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

        # Calculate distance and bearing if reference location provided
        distance: float | None = None
        bearing: float | None = None
        direction: str | None = None

        if latitude is not None and longitude is not None:
            distance = calculate_distance(
                latitude,
                longitude,
                location.latitude,
                location.longitude,
            )
            bearing = get_bearing(
                latitude,
                longitude,
                location.latitude,
                location.longitude,
            )
            direction = bearing_to_direction(bearing)

        # Parse timestamp
        try:
            updated = datetime.fromisoformat(emergency["emergencyTimestampPrepared"]["updatedTime"])
        except (ValueError, KeyError):
            updated = datetime.now()

        # cardBody fields may be missing in some incidents
        card_body = emergency.get("cardBody", {})

        return EmergencyIncident(
            id=emergency["id"],
            headline=emergency["headline"],
            alert_level=emergency["alertLevelInfoPrepared"]["level"],
            alert_text=emergency["alertLevelInfoPrepared"]["text"],
            event_type=emergency["eventLabelPrepared"]["labelText"],
            event_icon=emergency["eventLabelPrepared"]["icon"],
            status=card_body.get("status"),
            size=card_body.get("size"),
            source=card_body.get("source", "Unknown"),
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
                    coords = geom["coordinates"]
                    if len(coords) >= 2:
                        # GeoJSON uses [longitude, latitude]
                        return Coordinate(latitude=coords[1], longitude=coords[0])
            # If no point found, try to get centroid of first polygon
            for geom in geometries:
                if geom["type"] == "Polygon":
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
        """Calculate the centroid of a top-level polygon."""
        coords = geometry["coordinates"]
        if not coords:
            return None

        all_points: list[tuple[float, float]] = []

        if len(coords) > 0:
            ring = coords[0]  # Outer ring
            for point in ring:
                if len(point) >= 2:
                    all_points.append((point[0], point[1]))

        if not all_points:
            return None

        avg_lon = sum(p[0] for p in all_points) / len(all_points)
        avg_lat = sum(p[1] for p in all_points) / len(all_points)

        return Coordinate(latitude=avg_lat, longitude=avg_lon)

    def _calculate_multipolygon_centroid(
        self, geometry: TopLevelMultiPolygonGeometry
    ) -> Coordinate | None:
        """Calculate the centroid of a multipolygon."""
        coords = geometry["coordinates"]
        if not coords:
            return None

        all_points: list[tuple[float, float]] = []

        for polygon in coords:
            if polygon and len(polygon) > 0:
                ring = polygon[0]  # Outer ring
                for point in ring:
                    if len(point) >= 2:
                        all_points.append((point[0], point[1]))

        if not all_points:
            return None

        avg_lon = sum(p[0] for p in all_points) / len(all_points)
        avg_lat = sum(p[1] for p in all_points) / len(all_points)

        return Coordinate(latitude=avg_lat, longitude=avg_lon)

    def _calculate_polygon_centroid_from_polygon(
        self, geometry: PolygonGeometry
    ) -> Coordinate | None:
        """Calculate the centroid of a nested polygon geometry."""
        coords = geometry["coordinates"]
        if not coords:
            return None

        all_points: list[tuple[float, float]] = []

        if len(coords) > 0:
            ring = coords[0]  # Outer ring
            for point in ring:
                if len(point) >= 2:
                    all_points.append((point[0], point[1]))

        if not all_points:
            return None

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
