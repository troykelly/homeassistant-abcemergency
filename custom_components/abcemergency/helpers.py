"""Helper functions for ABC Emergency integration.

This module provides utility functions for geographic calculations,
including distance, bearing, and compass direction conversions.
"""

from __future__ import annotations

import math

# Earth's radius in kilometers
EARTH_RADIUS_KM = 6371.0


def calculate_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """Calculate distance between two points in kilometers using Haversine formula.

    The Haversine formula determines the great-circle distance between two points
    on a sphere given their longitudes and latitudes.

    Args:
        lat1: Latitude of first point in degrees.
        lon1: Longitude of first point in degrees.
        lat2: Latitude of second point in degrees.
        lon2: Longitude of second point in degrees.

    Returns:
        Distance between the two points in kilometers.
    """
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    # Haversine formula
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_KM * c


def get_bearing(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """Calculate initial bearing from point 1 to point 2 in degrees.

    The bearing is the direction you would need to travel from point 1
    to reach point 2, measured clockwise from north.

    Args:
        lat1: Latitude of first point in degrees.
        lon1: Longitude of first point in degrees.
        lat2: Latitude of second point in degrees.
        lon2: Longitude of second point in degrees.

    Returns:
        Bearing in degrees (0-360), where 0 is north, 90 is east, etc.
    """
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lon = math.radians(lon2 - lon1)

    x = math.sin(delta_lon) * math.cos(lat2_rad)
    y = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(
        lat2_rad
    ) * math.cos(delta_lon)

    bearing_rad = math.atan2(x, y)
    bearing_deg = math.degrees(bearing_rad)

    # Normalize to 0-360
    return (bearing_deg + 360) % 360


def bearing_to_direction(bearing: float) -> str:
    """Convert bearing in degrees to compass direction.

    Args:
        bearing: Bearing in degrees (any value, will be normalized).

    Returns:
        One of 8 compass directions: N, NE, E, SE, S, SW, W, NW.
    """
    # Normalize bearing to 0-360
    bearing = bearing % 360

    # Each direction covers 45 degrees, centered on the cardinal/intercardinal points
    # N: 337.5 - 22.5 (includes 0)
    # NE: 22.5 - 67.5
    # E: 67.5 - 112.5
    # SE: 112.5 - 157.5
    # S: 157.5 - 202.5
    # SW: 202.5 - 247.5
    # W: 247.5 - 292.5
    # NW: 292.5 - 337.5

    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

    # Add 22.5 to shift the boundaries (so 0 is center of N, not edge)
    # Then divide by 45 to get the index
    index = int((bearing + 22.5) / 45) % 8

    return directions[index]
