"""Tests for geospatial helper functions."""

from __future__ import annotations

import pytest

from custom_components.abcemergency.const import StoredPolygon
from custom_components.abcemergency.helpers_geo import (
    point_in_polygons,
    stored_polygon_to_shapely,
)


class TestStoredPolygonToShapely:
    """Test conversion from StoredPolygon to Shapely Polygon."""

    def test_simple_polygon_conversion(self) -> None:
        """Test converting a simple square polygon."""
        polygon: StoredPolygon = {
            "outer_ring": [[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0], [0.0, 0.0]],
            "inner_rings": None,
        }
        shapely_poly = stored_polygon_to_shapely(polygon)
        assert shapely_poly.is_valid
        assert shapely_poly.area > 0

    def test_polygon_with_hole_conversion(self) -> None:
        """Test converting a polygon with an inner hole."""
        polygon: StoredPolygon = {
            "outer_ring": [
                [0.0, 0.0],
                [20.0, 0.0],
                [20.0, 20.0],
                [0.0, 20.0],
                [0.0, 0.0],
            ],
            "inner_rings": [
                [[5.0, 5.0], [15.0, 5.0], [15.0, 15.0], [5.0, 15.0], [5.0, 5.0]],
            ],
        }
        shapely_poly = stored_polygon_to_shapely(polygon)
        assert shapely_poly.is_valid
        # Outer area is 400, hole area is 100, so net area is 300
        assert shapely_poly.area == pytest.approx(300.0, abs=0.1)


class TestPointInPolygons:
    """Test point-in-polygon detection."""

    def test_point_inside_simple_polygon(self) -> None:
        """Point clearly inside a square polygon."""
        polygon: StoredPolygon = {
            "outer_ring": [[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0], [0.0, 0.0]],
            "inner_rings": None,
        }
        assert point_in_polygons(5.0, 5.0, [polygon]) is True

    def test_point_outside_simple_polygon(self) -> None:
        """Point clearly outside a polygon."""
        polygon: StoredPolygon = {
            "outer_ring": [[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0], [0.0, 0.0]],
            "inner_rings": None,
        }
        assert point_in_polygons(15.0, 5.0, [polygon]) is False

    def test_point_in_hole_is_outside(self) -> None:
        """Point inside outer ring but inside a hole = outside."""
        polygon: StoredPolygon = {
            "outer_ring": [
                [0.0, 0.0],
                [20.0, 0.0],
                [20.0, 20.0],
                [0.0, 20.0],
                [0.0, 0.0],
            ],
            "inner_rings": [
                [[5.0, 5.0], [15.0, 5.0], [15.0, 15.0], [5.0, 15.0], [5.0, 5.0]],
            ],
        }
        # Point at (10, 10) is inside the hole, so outside the polygon
        assert point_in_polygons(10.0, 10.0, [polygon]) is False

    def test_point_outside_hole_but_inside_outer(self) -> None:
        """Point inside outer ring but outside hole = inside polygon."""
        polygon: StoredPolygon = {
            "outer_ring": [
                [0.0, 0.0],
                [20.0, 0.0],
                [20.0, 20.0],
                [0.0, 20.0],
                [0.0, 0.0],
            ],
            "inner_rings": [
                [[5.0, 5.0], [15.0, 5.0], [15.0, 15.0], [5.0, 15.0], [5.0, 5.0]],
            ],
        }
        # Point at (2, 2) is inside outer but outside hole = inside
        assert point_in_polygons(2.0, 2.0, [polygon]) is True

    def test_point_in_one_of_multiple_polygons(self) -> None:
        """Point inside second polygon of a multi-polygon list."""
        poly1: StoredPolygon = {
            "outer_ring": [[0.0, 0.0], [5.0, 0.0], [5.0, 5.0], [0.0, 5.0], [0.0, 0.0]],
            "inner_rings": None,
        }
        poly2: StoredPolygon = {
            "outer_ring": [
                [10.0, 10.0],
                [15.0, 10.0],
                [15.0, 15.0],
                [10.0, 15.0],
                [10.0, 10.0],
            ],
            "inner_rings": None,
        }
        # Point inside poly2
        assert point_in_polygons(12.0, 12.0, [poly1, poly2]) is True

    def test_point_outside_all_polygons(self) -> None:
        """Point outside all polygons in the list."""
        poly1: StoredPolygon = {
            "outer_ring": [[0.0, 0.0], [5.0, 0.0], [5.0, 5.0], [0.0, 5.0], [0.0, 0.0]],
            "inner_rings": None,
        }
        poly2: StoredPolygon = {
            "outer_ring": [
                [10.0, 10.0],
                [15.0, 10.0],
                [15.0, 15.0],
                [10.0, 15.0],
                [10.0, 10.0],
            ],
            "inner_rings": None,
        }
        # Point outside both
        assert point_in_polygons(7.0, 7.0, [poly1, poly2]) is False


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_polygons_list(self) -> None:
        """Empty list returns False."""
        assert point_in_polygons(0.0, 0.0, []) is False

    def test_none_polygons(self) -> None:
        """None polygons list returns False."""
        assert point_in_polygons(0.0, 0.0, None) is False  # type: ignore[arg-type]

    def test_malformed_polygon_empty_outer_ring(self) -> None:
        """Malformed polygon with empty outer ring should not crash."""
        polygon: StoredPolygon = {
            "outer_ring": [],
            "inner_rings": None,
        }
        # Should handle gracefully without crashing
        assert point_in_polygons(5.0, 5.0, [polygon]) is False

    def test_malformed_polygon_insufficient_points(self) -> None:
        """Polygon with insufficient points should not crash."""
        polygon: StoredPolygon = {
            "outer_ring": [[0.0, 0.0], [10.0, 0.0]],  # Only 2 points
            "inner_rings": None,
        }
        assert point_in_polygons(5.0, 5.0, [polygon]) is False


class TestBoundaryConditions:
    """Test boundary and vertex edge cases."""

    def test_point_on_polygon_boundary(self) -> None:
        """Point exactly on polygon edge.

        Note: Shapely's contains() returns False for boundary points.
        This is implementation-specific behavior that we document here.
        """
        polygon: StoredPolygon = {
            "outer_ring": [[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0], [0.0, 0.0]],
            "inner_rings": None,
        }
        # Point on the left edge at (0, 5)
        # Shapely's contains() returns False for boundary points
        assert point_in_polygons(5.0, 0.0, [polygon]) is False

    def test_point_at_polygon_vertex(self) -> None:
        """Point exactly at a polygon vertex.

        Note: Shapely's contains() returns False for vertex points.
        """
        polygon: StoredPolygon = {
            "outer_ring": [[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0], [0.0, 0.0]],
            "inner_rings": None,
        }
        # Point at vertex (0, 0)
        assert point_in_polygons(0.0, 0.0, [polygon]) is False

    def test_self_intersecting_polygon_is_invalid(self) -> None:
        """Self-intersecting (bowtie) polygon should be handled as invalid."""
        # Creates a bowtie/figure-8 shape by crossing lines
        bowtie: StoredPolygon = {
            "outer_ring": [
                [0.0, 0.0],
                [10.0, 10.0],  # Cross to opposite corner
                [10.0, 0.0],
                [0.0, 10.0],  # Cross back
                [0.0, 0.0],
            ],
            "inner_rings": None,
        }
        # Self-intersecting polygon is invalid, so point_in_polygons should
        # return False because polygon.is_valid check fails
        assert point_in_polygons(5.0, 5.0, [bowtie]) is False


class TestPerformance:
    """Performance tests for polygon operations."""

    def test_performance_large_polygon(self) -> None:
        """Check performance with polygon of many vertices.

        This test ensures the containment check completes in reasonable time
        for polygons with complex boundaries.
        """
        import math
        import time

        # Create a polygon with 1000+ vertices (a circle approximation)
        num_points = 1000
        radius = 10.0
        center = (50.0, 50.0)

        outer_ring: list[list[float]] = []
        for i in range(num_points):
            angle = (2 * math.pi * i) / num_points
            x = center[0] + radius * math.cos(angle)
            y = center[1] + radius * math.sin(angle)
            outer_ring.append([x, y])
        # Close the polygon
        outer_ring.append(outer_ring[0])

        large_polygon: StoredPolygon = {
            "outer_ring": outer_ring,
            "inner_rings": None,
        }

        # Test point inside
        start = time.time()
        result = point_in_polygons(center[1], center[0], [large_polygon])
        elapsed = time.time() - start

        assert result is True
        # Should complete in well under 1 second
        assert elapsed < 1.0, f"Large polygon check took {elapsed:.3f}s"

    def test_multiple_large_polygons(self) -> None:
        """Check performance with multiple polygons to check."""
        import math
        import time

        # Create 10 polygons with 100 vertices each
        polygons: list[StoredPolygon] = []
        for j in range(10):
            offset = j * 30
            outer_ring: list[list[float]] = []
            for i in range(100):
                angle = (2 * math.pi * i) / 100
                x = offset + 10.0 * math.cos(angle)
                y = 10.0 * math.sin(angle)
                outer_ring.append([x, y])
            outer_ring.append(outer_ring[0])
            polygons.append({"outer_ring": outer_ring, "inner_rings": None})

        # Test point outside all polygons
        start = time.time()
        result = point_in_polygons(-100.0, -100.0, polygons)
        elapsed = time.time() - start

        assert result is False
        assert elapsed < 1.0, f"Multiple polygon check took {elapsed:.3f}s"


class TestRealWorldCoordinates:
    """Test with realistic Australian coordinates."""

    def test_sydney_point_in_nsw_polygon(self) -> None:
        """Test with realistic NSW polygon containing Sydney."""
        # Simplified NSW-ish polygon (bounding box)
        nsw_polygon: StoredPolygon = {
            "outer_ring": [
                [140.9, -34.0],
                [153.6, -34.0],
                [153.6, -28.0],
                [140.9, -28.0],
                [140.9, -34.0],
            ],
            "inner_rings": None,
        }
        # Sydney: -33.8688, 151.2093
        assert point_in_polygons(-33.8688, 151.2093, [nsw_polygon]) is True

    def test_melbourne_point_outside_nsw_polygon(self) -> None:
        """Melbourne should be outside simplified NSW polygon."""
        nsw_polygon: StoredPolygon = {
            "outer_ring": [
                [140.9, -34.0],
                [153.6, -34.0],
                [153.6, -28.0],
                [140.9, -28.0],
                [140.9, -34.0],
            ],
            "inner_rings": None,
        }
        # Melbourne: -37.8136, 144.9631 (outside - too far south)
        assert point_in_polygons(-37.8136, 144.9631, [nsw_polygon]) is False

    def test_bushfire_zone_containment(self) -> None:
        """Test realistic bushfire zone containment scenario."""
        # Simulated bushfire zone near Sydney
        fire_zone: StoredPolygon = {
            "outer_ring": [
                [150.0, -33.0],
                [151.0, -33.0],
                [151.0, -34.0],
                [150.0, -34.0],
                [150.0, -33.0],
            ],
            "inner_rings": None,
        }
        # Home location inside the zone
        assert point_in_polygons(-33.5, 150.5, [fire_zone]) is True
        # Home location outside the zone
        assert point_in_polygons(-35.0, 152.0, [fire_zone]) is False
