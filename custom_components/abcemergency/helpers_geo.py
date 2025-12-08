"""Geospatial helper functions for ABC Emergency.

This module provides point-in-polygon detection for containment checking
of emergency incident zones.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from shapely.geometry import Point, Polygon  # type: ignore[import-untyped]

if TYPE_CHECKING:
    from .const import StoredPolygon

_LOGGER = logging.getLogger(__name__)


def stored_polygon_to_shapely(poly_data: StoredPolygon) -> Polygon:
    """Convert stored polygon data to Shapely Polygon.

    Args:
        poly_data: Stored polygon data with outer_ring and optional inner_rings.

    Returns:
        Shapely Polygon object.
    """
    # Shapely uses (x, y) which is (longitude, latitude)
    shell = [(coord[0], coord[1]) for coord in poly_data["outer_ring"]]
    holes = None
    inner_rings = poly_data.get("inner_rings")
    if inner_rings is not None:
        holes = [[(coord[0], coord[1]) for coord in ring] for ring in inner_rings]
    return Polygon(shell, holes)


def point_in_polygons(
    latitude: float,
    longitude: float,
    polygons: list[StoredPolygon] | None,
) -> bool:
    """Check if a geographic point is inside any of the given polygons.

    Args:
        latitude: Point latitude (y-coordinate).
        longitude: Point longitude (x-coordinate).
        polygons: List of stored polygon data, or None.

    Returns:
        True if point is inside any polygon, False otherwise.
    """
    if not polygons:
        return False

    point = Point(longitude, latitude)  # Shapely: (x, y) = (lon, lat)

    for poly_data in polygons:
        try:
            polygon = stored_polygon_to_shapely(poly_data)
            if polygon.is_valid and polygon.contains(point):
                return True
        except Exception:
            # Skip malformed polygons - log but don't crash
            _LOGGER.debug("Skipping malformed polygon during containment check")
            continue

    return False
