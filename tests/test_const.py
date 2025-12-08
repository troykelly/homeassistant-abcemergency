"""Tests for ABC Emergency constants and TypedDict definitions."""

from __future__ import annotations

import pytest

from custom_components.abcemergency.const import (
    API_BASE_URL,
    CONF_STATE,
    CRS,
    DEFAULT_RADIUS_KM,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    SOURCE,
    STATES,
    USER_AGENT,
    AlertLevel,
    AlertLevelInfo,
    CardBody,
    Emergency,
    EmergencySearchResponse,
    EmergencyTimestamp,
    EventLabelInfo,
    Feature,
    FeatureProperties,
    PointGeometry,
    PolygonGeometry,
    StoredGeometry,
    StoredPolygon,
)


class TestDomainConstants:
    """Test domain-level constants."""

    def test_domain_value(self) -> None:
        """Test DOMAIN constant is correct."""
        assert DOMAIN == "abcemergency"

    def test_api_base_url(self) -> None:
        """Test API base URL is correct."""
        assert API_BASE_URL == "https://www.abc.net.au/emergency-web/api"

    def test_default_scan_interval(self) -> None:
        """Test default scan interval is 5 minutes (300 seconds)."""
        assert DEFAULT_SCAN_INTERVAL == 300

    def test_default_radius_km(self) -> None:
        """Test default radius is 50km."""
        assert DEFAULT_RADIUS_KM == 50

    def test_user_agent(self) -> None:
        """Test user agent string is set."""
        assert "HomeAssistant" in USER_AGENT
        assert "ABCEmergency" in USER_AGENT

    def test_source_identifier(self) -> None:
        """Test SOURCE constant for geo_location entities."""
        assert SOURCE == "abc_emergency"


class TestStateConstants:
    """Test state/territory constants."""

    def test_states_tuple_length(self) -> None:
        """Test all 8 Australian states/territories are defined."""
        assert len(STATES) == 8

    def test_states_contains_all_territories(self) -> None:
        """Test all expected states are present."""
        expected = {"nsw", "vic", "qld", "sa", "wa", "tas", "nt", "act"}
        assert set(STATES) == expected

    def test_conf_state_key(self) -> None:
        """Test CONF_STATE configuration key."""
        assert CONF_STATE == "state"


class TestAlertLevelClass:
    """Test AlertLevel class constants."""

    def test_emergency_level(self) -> None:
        """Test emergency alert level maps to 'extreme'."""
        assert AlertLevel.EMERGENCY == "extreme"

    def test_watch_and_act_level(self) -> None:
        """Test watch and act level maps to 'severe'."""
        assert AlertLevel.WATCH_AND_ACT == "severe"

    def test_advice_level(self) -> None:
        """Test advice level maps to 'moderate'."""
        assert AlertLevel.ADVICE == "moderate"

    def test_information_level(self) -> None:
        """Test information level maps to 'minor'."""
        assert AlertLevel.INFORMATION == "minor"


class TestTypedDictStructures:
    """Test TypedDict structures match API response format."""

    def test_alert_level_info_structure(self) -> None:
        """Test AlertLevelInfo TypedDict accepts valid data."""
        data: AlertLevelInfo = {
            "text": "Emergency",
            "level": "extreme",
            "style": "extreme",
        }
        assert data["text"] == "Emergency"
        assert data["level"] == "extreme"

    def test_emergency_timestamp_structure(self) -> None:
        """Test EmergencyTimestamp TypedDict accepts valid data."""
        data: EmergencyTimestamp = {
            "date": "2025-12-06T05:34:00+00:00",
            "formattedTime": "4:34:00 pm AEDT",
            "prefix": "Effective from",
            "updatedTime": "2025-12-06T05:53:02.97994+00:00",
        }
        assert data["date"] == "2025-12-06T05:34:00+00:00"

    def test_event_label_info_structure(self) -> None:
        """Test EventLabelInfo TypedDict accepts valid data."""
        data: EventLabelInfo = {
            "icon": "fire",
            "labelText": "Bushfire",
        }
        assert data["icon"] == "fire"
        assert data["labelText"] == "Bushfire"

    def test_card_body_structure(self) -> None:
        """Test CardBody TypedDict accepts valid data."""
        data: CardBody = {
            "type": "Bush Fire",
            "size": "9706 ha",
            "status": "Being controlled",
            "source": "NSW Rural Fire Service",
        }
        assert data["source"] == "NSW Rural Fire Service"

    def test_card_body_with_nulls(self) -> None:
        """Test CardBody TypedDict accepts null values for optional fields."""
        data: CardBody = {
            "type": None,
            "size": None,
            "status": "Active",
            "source": "Australian Government Bureau of Meteorology",
        }
        assert data["type"] is None


class TestGeometryTypes:
    """Test geometry TypedDict structures."""

    def test_point_geometry(self) -> None:
        """Test PointGeometry TypedDict."""
        data: PointGeometry = {
            "type": "Point",
            "coordinates": [150.37262, -32.339939],
        }
        assert data["type"] == "Point"
        assert len(data["coordinates"]) == 2

    def test_polygon_geometry(self) -> None:
        """Test PolygonGeometry TypedDict."""
        ring = [[150.0, -32.0], [151.0, -32.0], [151.0, -33.0], [150.0, -32.0]]
        data: PolygonGeometry = {
            "type": "Polygon",
            "coordinates": [ring],
        }
        assert data["type"] == "Polygon"

    def test_crs_structure(self) -> None:
        """Test CRS TypedDict."""
        data: CRS = {
            "type": "name",
            "properties": {"name": "EPSG:4326"},
        }
        assert data["properties"]["name"] == "EPSG:4326"


class TestEmergencyTypedDict:
    """Test Emergency TypedDict matches API response."""

    @pytest.fixture
    def sample_emergency(self) -> Emergency:
        """Provide sample emergency data matching API format."""
        return {
            "id": "AUREMER-72446a8d6888092c5e42f6ed9985f935",
            "headline": "Milsons Gully",
            "to": "/emergency/warning/AUREMER-72446a8d6888092c5e42f6ed9985f935",
            "alertLevelInfoPrepared": {
                "text": "Emergency",
                "level": "extreme",
                "style": "extreme",
            },
            "emergencyTimestampPrepared": {
                "date": "2025-12-06T05:34:00+00:00",
                "formattedTime": "4:34:00 pm AEDT",
                "prefix": "Effective from",
                "updatedTime": "2025-12-06T05:53:02.97994+00:00",
            },
            "eventLabelPrepared": {
                "icon": "fire",
                "labelText": "Bushfire",
            },
            "cardBody": {
                "type": "Bush Fire",
                "size": "9706 ha",
                "status": "Being controlled",
                "source": "NSW Rural Fire Service",
            },
            "geometry": {
                "crs": {
                    "type": "name",
                    "properties": {"name": "EPSG:4326"},
                },
                "type": "GeometryCollection",
                "geometries": [
                    {"type": "Point", "coordinates": [150.37262, -32.339939]},
                ],
            },
        }

    def test_emergency_id(self, sample_emergency: Emergency) -> None:
        """Test emergency ID field."""
        assert sample_emergency["id"].startswith("AUREMER-")

    def test_emergency_headline(self, sample_emergency: Emergency) -> None:
        """Test emergency headline field."""
        assert sample_emergency["headline"] == "Milsons Gully"

    def test_emergency_alert_level(self, sample_emergency: Emergency) -> None:
        """Test nested alertLevelInfoPrepared."""
        alert = sample_emergency["alertLevelInfoPrepared"]
        assert alert["level"] == "extreme"
        assert alert["text"] == "Emergency"


class TestEmergencySearchResponse:
    """Test EmergencySearchResponse TypedDict."""

    def test_search_response_structure(self) -> None:
        """Test EmergencySearchResponse accepts valid data."""
        data: EmergencySearchResponse = {
            "emergencies": [],
            "features": [],
            "mapBound": [[149.0, -34.0], [152.0, -32.0]],
            "stateName": "nsw",
            "incidentsNumber": 0,
            "stateCount": 125,
        }
        assert data["stateName"] == "nsw"
        assert data["stateCount"] == 125


class TestFeatureTypedDicts:
    """Test Feature TypedDict structures."""

    def test_feature_properties_structure(self) -> None:
        """Test FeatureProperties TypedDict."""
        # FeatureProperties is total=False so all fields are optional
        data: FeatureProperties = {
            "id": "AUREMER-test",
            "state": "nsw",
            "headline": "Test Fire",
            "alertType": "warning",
            "abcAlertLevel": "10",
        }
        assert data["id"] == "AUREMER-test"

    def test_feature_structure(self) -> None:
        """Test Feature TypedDict."""
        data: Feature = {
            "type": "Feature",
            "id": "AUREMER-test",
            "geometry": {
                "type": "Point",
                "crs": {
                    "type": "name",
                    "properties": {"name": "EPSG:4326"},
                },
                "coordinates": [150.0, -33.0],
            },
            "properties": {
                "id": "AUREMER-test",
                "state": "nsw",
            },
        }
        assert data["type"] == "Feature"


class TestStoredPolygonTypeDicts:
    """Test StoredPolygon and StoredGeometry TypedDict structures."""

    def test_stored_polygon_with_outer_ring_only(self) -> None:
        """Test StoredPolygon with just an outer boundary."""
        polygon: StoredPolygon = {
            "outer_ring": [
                [151.0, -33.0],
                [152.0, -33.0],
                [152.0, -34.0],
                [151.0, -34.0],
                [151.0, -33.0],
            ],
            "inner_rings": None,
        }
        assert len(polygon["outer_ring"]) == 5
        assert polygon["inner_rings"] is None

    def test_stored_polygon_with_holes(self) -> None:
        """Test StoredPolygon with inner rings (holes)."""
        polygon: StoredPolygon = {
            "outer_ring": [
                [150.0, -32.0],
                [153.0, -32.0],
                [153.0, -35.0],
                [150.0, -35.0],
                [150.0, -32.0],
            ],
            "inner_rings": [
                [  # First hole
                    [151.0, -33.0],
                    [152.0, -33.0],
                    [152.0, -34.0],
                    [151.0, -34.0],
                    [151.0, -33.0],
                ],
            ],
        }
        assert len(polygon["outer_ring"]) == 5
        assert polygon["inner_rings"] is not None
        assert len(polygon["inner_rings"]) == 1

    def test_stored_geometry_point(self) -> None:
        """Test StoredGeometry for Point type."""
        geometry: StoredGeometry = {
            "type": "Point",
            "polygons": None,
        }
        assert geometry["type"] == "Point"
        assert geometry["polygons"] is None

    def test_stored_geometry_polygon(self) -> None:
        """Test StoredGeometry for Polygon type."""
        geometry: StoredGeometry = {
            "type": "Polygon",
            "polygons": [
                {
                    "outer_ring": [
                        [151.0, -33.0],
                        [152.0, -33.0],
                        [152.0, -34.0],
                        [151.0, -33.0],
                    ],
                    "inner_rings": None,
                }
            ],
        }
        assert geometry["type"] == "Polygon"
        assert geometry["polygons"] is not None
        assert len(geometry["polygons"]) == 1

    def test_stored_geometry_multipolygon(self) -> None:
        """Test StoredGeometry for MultiPolygon type."""
        geometry: StoredGeometry = {
            "type": "MultiPolygon",
            "polygons": [
                {
                    "outer_ring": [[150.0, -32.0], [151.0, -32.0], [150.5, -33.0], [150.0, -32.0]],
                    "inner_rings": None,
                },
                {
                    "outer_ring": [[152.0, -34.0], [153.0, -34.0], [152.5, -35.0], [152.0, -34.0]],
                    "inner_rings": None,
                },
            ],
        }
        assert geometry["type"] == "MultiPolygon"
        assert geometry["polygons"] is not None
        assert len(geometry["polygons"]) == 2
