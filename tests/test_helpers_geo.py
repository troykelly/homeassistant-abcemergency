"""Tests for geospatial helper functions."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from custom_components.abcemergency.const import StoredPolygon
from custom_components.abcemergency.helpers_geo import (
    get_prepared_polygons,
    point_in_incident,
    point_in_polygons,
    stored_polygon_to_shapely,
)
from custom_components.abcemergency.models import Coordinate, EmergencyIncident


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


class TestGetPreparedPolygons:
    """Test prepared polygon caching."""

    def test_caches_prepared_polygons(self) -> None:
        """Prepared polygons are cached on first call."""
        incident = EmergencyIncident(
            id="test-1",
            headline="Test Incident",
            alert_level="moderate",
            alert_text="Advice",
            event_type="Bushfire",
            event_icon="fire",
            status="Going",
            size="10 ha",
            source="Test Service",
            location=Coordinate(latitude=-33.8688, longitude=151.2093),
            updated=datetime.now(UTC),
            polygons=[
                {
                    "outer_ring": [[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0], [0.0, 0.0]],
                    "inner_rings": None,
                }
            ],
            has_polygon=True,
        )

        # First call builds cache
        prepared1 = get_prepared_polygons(incident)
        assert len(prepared1) == 1
        assert incident._prepared_polygons is not None

        # Second call returns cached
        prepared2 = get_prepared_polygons(incident)
        assert prepared1 is prepared2  # Same object reference

    def test_empty_polygons_returns_empty_list(self) -> None:
        """Incident with no polygons returns empty list."""
        incident = EmergencyIncident(
            id="test-2",
            headline="Test Incident",
            alert_level="moderate",
            alert_text="Advice",
            event_type="Bushfire",
            event_icon="fire",
            status="Going",
            size="10 ha",
            source="Test Service",
            location=Coordinate(latitude=-33.8688, longitude=151.2093),
            updated=datetime.now(UTC),
            polygons=None,
            has_polygon=False,
        )

        prepared = get_prepared_polygons(incident)
        assert prepared == []
        assert incident._prepared_polygons == []

    def test_skips_invalid_polygons(self) -> None:
        """Invalid polygons are skipped during preparation."""
        incident = EmergencyIncident(
            id="test-3",
            headline="Test Incident",
            alert_level="moderate",
            alert_text="Advice",
            event_type="Bushfire",
            event_icon="fire",
            status="Going",
            size="10 ha",
            source="Test Service",
            location=Coordinate(latitude=-33.8688, longitude=151.2093),
            updated=datetime.now(UTC),
            polygons=[
                # Valid polygon
                {
                    "outer_ring": [[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0], [0.0, 0.0]],
                    "inner_rings": None,
                },
                # Invalid self-intersecting polygon (bowtie)
                {
                    "outer_ring": [
                        [0.0, 0.0],
                        [10.0, 10.0],
                        [10.0, 0.0],
                        [0.0, 10.0],
                        [0.0, 0.0],
                    ],
                    "inner_rings": None,
                },
            ],
            has_polygon=True,
        )

        prepared = get_prepared_polygons(incident)
        # Only the valid polygon should be included
        assert len(prepared) == 1


class TestPointInIncident:
    """Test point_in_incident with cached prepared geometries."""

    def test_point_inside_incident_polygon(self) -> None:
        """Point inside incident polygon returns True."""
        incident = EmergencyIncident(
            id="test-1",
            headline="Test Incident",
            alert_level="moderate",
            alert_text="Advice",
            event_type="Bushfire",
            event_icon="fire",
            status="Going",
            size="10 ha",
            source="Test Service",
            location=Coordinate(latitude=-33.8688, longitude=151.2093),
            updated=datetime.now(UTC),
            polygons=[
                {
                    "outer_ring": [[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0], [0.0, 0.0]],
                    "inner_rings": None,
                }
            ],
            has_polygon=True,
        )

        assert point_in_incident(5.0, 5.0, incident) is True

    def test_point_outside_incident_polygon(self) -> None:
        """Point outside incident polygon returns False."""
        incident = EmergencyIncident(
            id="test-2",
            headline="Test Incident",
            alert_level="moderate",
            alert_text="Advice",
            event_type="Bushfire",
            event_icon="fire",
            status="Going",
            size="10 ha",
            source="Test Service",
            location=Coordinate(latitude=-33.8688, longitude=151.2093),
            updated=datetime.now(UTC),
            polygons=[
                {
                    "outer_ring": [[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0], [0.0, 0.0]],
                    "inner_rings": None,
                }
            ],
            has_polygon=True,
        )

        assert point_in_incident(15.0, 5.0, incident) is False

    def test_incident_without_polygon(self) -> None:
        """Incident without polygon returns False."""
        incident = EmergencyIncident(
            id="test-3",
            headline="Test Incident",
            alert_level="moderate",
            alert_text="Advice",
            event_type="Bushfire",
            event_icon="fire",
            status="Going",
            size="10 ha",
            source="Test Service",
            location=Coordinate(latitude=-33.8688, longitude=151.2093),
            updated=datetime.now(UTC),
            polygons=None,
            has_polygon=False,
        )

        assert point_in_incident(5.0, 5.0, incident) is False

    def test_uses_cached_prepared_polygons(self) -> None:
        """point_in_incident uses cached prepared geometries."""
        incident = EmergencyIncident(
            id="test-4",
            headline="Test Incident",
            alert_level="moderate",
            alert_text="Advice",
            event_type="Bushfire",
            event_icon="fire",
            status="Going",
            size="10 ha",
            source="Test Service",
            location=Coordinate(latitude=-33.8688, longitude=151.2093),
            updated=datetime.now(UTC),
            polygons=[
                {
                    "outer_ring": [[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0], [0.0, 0.0]],
                    "inner_rings": None,
                }
            ],
            has_polygon=True,
        )

        # Cache should be None initially
        assert incident._prepared_polygons is None

        # First call should build cache
        point_in_incident(5.0, 5.0, incident)
        assert incident._prepared_polygons is not None
        cached = incident._prepared_polygons

        # Second call should use same cache
        point_in_incident(15.0, 5.0, incident)
        assert incident._prepared_polygons is cached

    def test_point_in_hole_returns_false(self) -> None:
        """Point inside hole of polygon returns False."""
        incident = EmergencyIncident(
            id="test-5",
            headline="Test Incident",
            alert_level="moderate",
            alert_text="Advice",
            event_type="Bushfire",
            event_icon="fire",
            status="Going",
            size="10 ha",
            source="Test Service",
            location=Coordinate(latitude=-33.8688, longitude=151.2093),
            updated=datetime.now(UTC),
            polygons=[
                {
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
            ],
            has_polygon=True,
        )

        # Point in hole
        assert point_in_incident(10.0, 10.0, incident) is False
        # Point in polygon but outside hole
        assert point_in_incident(2.0, 2.0, incident) is True


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
