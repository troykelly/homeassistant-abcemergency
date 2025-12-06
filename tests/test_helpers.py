"""Tests for ABC Emergency helper functions."""

from __future__ import annotations

import pytest

from custom_components.abcemergency.helpers import (
    bearing_to_direction,
    calculate_distance,
    get_bearing,
)


class TestCalculateDistance:
    """Test Haversine distance calculations."""

    def test_sydney_to_melbourne(self) -> None:
        """Test distance between Sydney and Melbourne (~713 km)."""
        # Sydney: -33.8688, 151.2093
        # Melbourne: -37.8136, 144.9631
        distance = calculate_distance(-33.8688, 151.2093, -37.8136, 144.9631)
        # Actual distance is approximately 713 km
        assert 710 < distance < 720

    def test_same_point(self) -> None:
        """Test distance between same point is 0."""
        distance = calculate_distance(-33.8688, 151.2093, -33.8688, 151.2093)
        assert distance == 0.0

    def test_sydney_to_brisbane(self) -> None:
        """Test distance between Sydney and Brisbane (~730 km)."""
        # Sydney: -33.8688, 151.2093
        # Brisbane: -27.4698, 153.0251
        distance = calculate_distance(-33.8688, 151.2093, -27.4698, 153.0251)
        assert 725 < distance < 735

    def test_short_distance(self) -> None:
        """Test short distance (< 1 km)."""
        # Two points in Sydney CBD about 500m apart
        # Sydney Opera House: -33.8568, 151.2153
        # Circular Quay Station: -33.8610, 151.2108
        distance = calculate_distance(-33.8568, 151.2153, -33.8610, 151.2108)
        assert 0.3 < distance < 0.7  # Approximately 0.5 km

    def test_cross_hemisphere(self) -> None:
        """Test distance across equator."""
        # Sydney to Singapore
        # Sydney: -33.8688, 151.2093
        # Singapore: 1.3521, 103.8198
        distance = calculate_distance(-33.8688, 151.2093, 1.3521, 103.8198)
        # Approximately 6300 km
        assert 6200 < distance < 6400


class TestGetBearing:
    """Test bearing calculations."""

    def test_bearing_north(self) -> None:
        """Test bearing due north (0 degrees)."""
        # Point 1 to a point directly north
        bearing = get_bearing(-34.0, 151.0, -33.0, 151.0)
        assert -5 < bearing < 5  # Approximately 0 degrees

    def test_bearing_east(self) -> None:
        """Test bearing due east (~90 degrees)."""
        # Point 1 to a point directly east
        bearing = get_bearing(-33.5, 151.0, -33.5, 152.0)
        assert 85 < bearing < 95

    def test_bearing_south(self) -> None:
        """Test bearing due south (~180 degrees)."""
        bearing = get_bearing(-33.0, 151.0, -34.0, 151.0)
        assert 175 < bearing < 185

    def test_bearing_west(self) -> None:
        """Test bearing due west (~270 degrees)."""
        bearing = get_bearing(-33.5, 152.0, -33.5, 151.0)
        assert 265 < bearing < 275

    def test_bearing_northeast(self) -> None:
        """Test bearing northeast (~45 degrees)."""
        bearing = get_bearing(-34.0, 151.0, -33.0, 152.0)
        assert 30 < bearing < 60

    def test_bearing_southwest(self) -> None:
        """Test bearing southwest (~225 degrees)."""
        bearing = get_bearing(-33.0, 152.0, -34.0, 151.0)
        assert 210 < bearing < 240


class TestBearingToDirection:
    """Test conversion of bearing to compass direction."""

    @pytest.mark.parametrize(
        ("bearing", "expected"),
        [
            (0, "N"),
            (10, "N"),
            (22, "N"),
            (23, "NE"),
            (45, "NE"),
            (67, "NE"),
            (68, "E"),
            (90, "E"),
            (112, "E"),
            (113, "SE"),
            (135, "SE"),
            (157, "SE"),
            (158, "S"),
            (180, "S"),
            (202, "S"),
            (203, "SW"),
            (225, "SW"),
            (247, "SW"),
            (248, "W"),
            (270, "W"),
            (292, "W"),
            (293, "NW"),
            (315, "NW"),
            (337, "NW"),
            (338, "N"),
            (359, "N"),
            (360, "N"),
        ],
    )
    def test_direction_mapping(self, bearing: float, expected: str) -> None:
        """Test bearing to direction mapping for all compass points."""
        assert bearing_to_direction(bearing) == expected

    def test_negative_bearing(self) -> None:
        """Test negative bearing is normalized."""
        # -90 degrees should be 270 degrees (West)
        assert bearing_to_direction(-90) == "W"

    def test_large_bearing(self) -> None:
        """Test bearing > 360 is normalized."""
        # 450 degrees should be 90 degrees (East)
        assert bearing_to_direction(450) == "E"
