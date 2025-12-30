"""Tests for ABC Emergency geo location platform."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_RADIUS, UnitOfLength
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.abcemergency.const import (
    CONF_USE_HOME_LOCATION,
    DOMAIN,
    AlertLevel,
)
from custom_components.abcemergency.geo_location import (
    ABCEmergencyGeolocationEvent,
    ABCEmergencyGeoLocationManager,
    _get_instance_source,
    async_setup_entry,
)
from custom_components.abcemergency.models import (
    CoordinatorData,
    EmergencyIncident,
)

if TYPE_CHECKING:
    pass


class TestGetInstanceSource:
    """Test the _get_instance_source helper function."""

    def test_returns_title_directly(self) -> None:
        """Test source returns the entry title directly."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="ABC Emergency (Treehouse)",
            data={},
        )
        assert _get_instance_source(entry) == "ABC Emergency (Treehouse)"

    def test_title_with_state(self) -> None:
        """Test source for state-style title."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="ABC Emergency (NSW)",
            data={},
        )
        assert _get_instance_source(entry) == "ABC Emergency (NSW)"

    def test_title_with_person_name(self) -> None:
        """Test source for person-style title."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="ABC Emergency (Dad)",
            data={},
        )
        assert _get_instance_source(entry) == "ABC Emergency (Dad)"

    def test_empty_title_fallback(self) -> None:
        """Test fallback when title is empty."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="",
            data={},
        )
        assert _get_instance_source(entry) == "ABC Emergency"


class TestABCEmergencyGeolocationEvent:
    """Test ABCEmergencyGeolocationEvent entity."""

    def test_entity_id_matches_sensor_format(
        self,
        mock_coordinator: MagicMock,
        mock_incident_bushfire: EmergencyIncident,
    ) -> None:
        """Test entity_id is explicitly set to match sensor entity_ids attribute format.

        This ensures geo_location entity IDs are predictable and match what sensors
        report in their entity_ids attribute for map card integration (#103).
        """
        from homeassistant.util import slugify

        event = ABCEmergencyGeolocationEvent(
            mock_coordinator, mock_incident_bushfire, instance_source="abc_emergency_home"
        )

        expected_id = f"geo_location.{slugify(f'abc_emergency_home_{mock_incident_bushfire.id}')}"
        assert event.entity_id == expected_id

    def test_entity_id_avoids_headline_collision(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test that entity_ids are unique even when headlines match.

        Using incident ID in entity_id avoids collisions when multiple
        incidents have the same location/headline.
        """
        from custom_components.abcemergency.models import Coordinate

        incident1 = EmergencyIncident(
            id="AUREMER-001",
            headline="Pacific Highway Hornsby",
            alert_level="extreme",
            alert_text="Emergency",
            event_type="Bushfire",
            event_icon="fire",
            status="Active",
            size=None,
            source="NSW RFS",
            location=Coordinate(latitude=-33.7, longitude=151.1),
            updated=datetime(2025, 1, 15, 10, 0, 0, tzinfo=UTC),
        )
        incident2 = EmergencyIncident(
            id="AUREMER-002",
            headline="Pacific Highway Hornsby",  # Same headline!
            alert_level="severe",
            alert_text="Watch and Act",
            event_type="Bushfire",
            event_icon="fire",
            status="Active",
            size=None,
            source="NSW RFS",
            location=Coordinate(latitude=-33.7, longitude=151.1),
            updated=datetime(2025, 1, 15, 11, 0, 0, tzinfo=UTC),
        )

        event1 = ABCEmergencyGeolocationEvent(
            mock_coordinator, incident1, instance_source="abc_emergency"
        )
        event2 = ABCEmergencyGeolocationEvent(
            mock_coordinator, incident2, instance_source="abc_emergency"
        )

        # Entity IDs should be different despite same headline
        assert event1.entity_id != event2.entity_id
        assert "auremer_001" in event1.entity_id
        assert "auremer_002" in event2.entity_id

    def test_entity_id_with_default_source(
        self,
        mock_coordinator: MagicMock,
        mock_incident_bushfire: EmergencyIncident,
    ) -> None:
        """Test entity_id with default source."""
        from homeassistant.util import slugify

        event = ABCEmergencyGeolocationEvent(mock_coordinator, mock_incident_bushfire)

        expected_id = f"geo_location.{slugify(f'abc_emergency_{mock_incident_bushfire.id}')}"
        assert event.entity_id == expected_id

    def test_unique_id_with_default_source(
        self,
        mock_coordinator: MagicMock,
        mock_incident_bushfire: EmergencyIncident,
    ) -> None:
        """Test unique ID is correctly generated with default source."""
        event = ABCEmergencyGeolocationEvent(mock_coordinator, mock_incident_bushfire)

        assert event.unique_id == f"abc_emergency_{mock_incident_bushfire.id}"

    def test_unique_id_with_instance_source(
        self,
        mock_coordinator: MagicMock,
        mock_incident_bushfire: EmergencyIncident,
    ) -> None:
        """Test unique ID uses instance source."""
        event = ABCEmergencyGeolocationEvent(
            mock_coordinator, mock_incident_bushfire, instance_source="abc_emergency_home"
        )

        assert event.unique_id == f"abc_emergency_home_{mock_incident_bushfire.id}"

    def test_name(
        self,
        mock_coordinator: MagicMock,
        mock_incident_bushfire: EmergencyIncident,
    ) -> None:
        """Test name is set to headline."""
        event = ABCEmergencyGeolocationEvent(mock_coordinator, mock_incident_bushfire)

        assert event.name == mock_incident_bushfire.headline

    def test_source_with_instance_source(
        self,
        mock_coordinator: MagicMock,
        mock_incident_bushfire: EmergencyIncident,
    ) -> None:
        """Test source property uses provided instance source."""
        event = ABCEmergencyGeolocationEvent(
            mock_coordinator, mock_incident_bushfire, instance_source="abc_emergency_home"
        )

        assert event.source == "abc_emergency_home"

    def test_source_for_state_instance(
        self,
        mock_coordinator: MagicMock,
        mock_incident_bushfire: EmergencyIncident,
    ) -> None:
        """Test source for state instance."""
        event = ABCEmergencyGeolocationEvent(
            mock_coordinator, mock_incident_bushfire, instance_source="abc_emergency_nsw"
        )

        assert event.source == "abc_emergency_nsw"

    def test_source_for_zone_instance(
        self,
        mock_coordinator: MagicMock,
        mock_incident_bushfire: EmergencyIncident,
    ) -> None:
        """Test source for zone instance."""
        event = ABCEmergencyGeolocationEvent(
            mock_coordinator, mock_incident_bushfire, instance_source="abc_emergency_my_home"
        )

        assert event.source == "abc_emergency_my_home"

    def test_source_for_person_instance(
        self,
        mock_coordinator: MagicMock,
        mock_incident_bushfire: EmergencyIncident,
    ) -> None:
        """Test source for person instance."""
        event = ABCEmergencyGeolocationEvent(
            mock_coordinator, mock_incident_bushfire, instance_source="abc_emergency_dad"
        )

        assert event.source == "abc_emergency_dad"

    def test_latitude(
        self,
        mock_coordinator: MagicMock,
        mock_incident_bushfire: EmergencyIncident,
    ) -> None:
        """Test latitude property."""
        event = ABCEmergencyGeolocationEvent(mock_coordinator, mock_incident_bushfire)

        assert event.latitude == mock_incident_bushfire.location.latitude

    def test_longitude(
        self,
        mock_coordinator: MagicMock,
        mock_incident_bushfire: EmergencyIncident,
    ) -> None:
        """Test longitude property."""
        event = ABCEmergencyGeolocationEvent(mock_coordinator, mock_incident_bushfire)

        assert event.longitude == mock_incident_bushfire.location.longitude

    def test_distance(
        self,
        mock_coordinator: MagicMock,
        mock_incident_bushfire: EmergencyIncident,
    ) -> None:
        """Test distance property."""
        event = ABCEmergencyGeolocationEvent(mock_coordinator, mock_incident_bushfire)

        assert event.distance == mock_incident_bushfire.distance_km

    def test_unit_of_measurement(
        self,
        mock_coordinator: MagicMock,
        mock_incident_bushfire: EmergencyIncident,
    ) -> None:
        """Test unit of measurement is kilometers."""
        event = ABCEmergencyGeolocationEvent(mock_coordinator, mock_incident_bushfire)

        assert event.unit_of_measurement == UnitOfLength.KILOMETERS

    def test_should_poll(
        self,
        mock_coordinator: MagicMock,
        mock_incident_bushfire: EmergencyIncident,
    ) -> None:
        """Test should_poll is False."""
        event = ABCEmergencyGeolocationEvent(mock_coordinator, mock_incident_bushfire)

        assert event.should_poll is False

    def test_extra_state_attributes(
        self,
        mock_coordinator: MagicMock,
        mock_incident_bushfire: EmergencyIncident,
    ) -> None:
        """Test extra state attributes."""
        event = ABCEmergencyGeolocationEvent(mock_coordinator, mock_incident_bushfire)

        attrs = event.extra_state_attributes

        assert attrs["alert_level"] == AlertLevel.EMERGENCY
        assert attrs["alert_text"] == "Emergency"
        assert attrs["event_type"] == "Bushfire"
        assert attrs["event_icon"] == "fire"
        assert attrs["status"] == "Out of control"
        assert attrs["agency"] == "NSW Rural Fire Service"
        assert attrs["direction"] == "S"
        assert attrs["size"] == "500 ha"
        assert "updated" in attrs

    def test_extra_state_attributes_no_size(
        self,
        mock_coordinator: MagicMock,
        mock_incident_flood: EmergencyIncident,
    ) -> None:
        """Test extra state attributes when size is None."""
        event = ABCEmergencyGeolocationEvent(mock_coordinator, mock_incident_flood)

        attrs = event.extra_state_attributes

        assert "size" not in attrs

    def test_extra_state_attributes_no_geojson_for_point_only(
        self,
        mock_coordinator: MagicMock,
        mock_incident_point_only: EmergencyIncident,
    ) -> None:
        """Test that geojson is not included for point-only incidents."""
        event = ABCEmergencyGeolocationEvent(mock_coordinator, mock_incident_point_only)

        attrs = event.extra_state_attributes

        assert "geojson" not in attrs

    def test_extra_state_attributes_no_geojson_when_no_polygon_data(
        self,
        mock_coordinator: MagicMock,
        mock_incident_bushfire: EmergencyIncident,
    ) -> None:
        """Test that geojson is not included when incident has no polygon data."""
        event = ABCEmergencyGeolocationEvent(mock_coordinator, mock_incident_bushfire)

        attrs = event.extra_state_attributes

        # Default mock_incident_bushfire has no polygon data
        assert "geojson" not in attrs

    def test_extra_state_attributes_with_single_polygon(
        self,
        mock_coordinator: MagicMock,
        mock_incident_with_single_polygon: EmergencyIncident,
    ) -> None:
        """Test that geojson is included with correct Polygon format."""
        event = ABCEmergencyGeolocationEvent(mock_coordinator, mock_incident_with_single_polygon)

        attrs = event.extra_state_attributes

        assert "geojson" in attrs
        geojson = attrs["geojson"]
        assert geojson["type"] == "Polygon"
        assert len(geojson["coordinates"]) == 1  # Just outer ring
        assert geojson["coordinates"][0] == [
            [151.2, -33.8],
            [151.3, -33.8],
            [151.3, -33.9],
            [151.2, -33.9],
            [151.2, -33.8],
        ]

    def test_extra_state_attributes_with_polygon_and_hole(
        self,
        mock_coordinator: MagicMock,
        mock_incident_with_polygon_and_hole: EmergencyIncident,
    ) -> None:
        """Test that geojson includes inner rings (holes)."""
        event = ABCEmergencyGeolocationEvent(mock_coordinator, mock_incident_with_polygon_and_hole)

        attrs = event.extra_state_attributes

        assert "geojson" in attrs
        geojson = attrs["geojson"]
        assert geojson["type"] == "Polygon"
        assert len(geojson["coordinates"]) == 2  # Outer ring + 1 hole
        # First ring is outer boundary
        assert geojson["coordinates"][0] == [
            [151.0, -33.7],
            [151.4, -33.7],
            [151.4, -34.0],
            [151.0, -34.0],
            [151.0, -33.7],
        ]
        # Second ring is the hole
        assert geojson["coordinates"][1] == [
            [151.15, -33.8],
            [151.25, -33.8],
            [151.25, -33.9],
            [151.15, -33.9],
            [151.15, -33.8],
        ]

    def test_extra_state_attributes_with_multipolygon(
        self,
        mock_coordinator: MagicMock,
        mock_incident_with_multipolygon: EmergencyIncident,
    ) -> None:
        """Test that geojson uses MultiPolygon format for multiple polygons."""
        event = ABCEmergencyGeolocationEvent(mock_coordinator, mock_incident_with_multipolygon)

        attrs = event.extra_state_attributes

        assert "geojson" in attrs
        geojson = attrs["geojson"]
        assert geojson["type"] == "MultiPolygon"
        assert len(geojson["coordinates"]) == 2  # Two polygons
        # First polygon
        assert geojson["coordinates"][0] == [
            [
                [151.2, -33.8],
                [151.3, -33.8],
                [151.3, -33.9],
                [151.2, -33.9],
                [151.2, -33.8],
            ]
        ]
        # Second polygon
        assert geojson["coordinates"][1] == [
            [
                [151.4, -33.7],
                [151.5, -33.7],
                [151.5, -33.8],
                [151.4, -33.8],
                [151.4, -33.7],
            ]
        ]

    def test_extra_state_attributes_geojson_with_geometry_type(
        self,
        mock_coordinator: MagicMock,
        mock_incident_with_single_polygon: EmergencyIncident,
    ) -> None:
        """Test that geometry_type attribute is also exposed."""
        event = ABCEmergencyGeolocationEvent(mock_coordinator, mock_incident_with_single_polygon)

        attrs = event.extra_state_attributes

        assert attrs.get("geometry_type") == "Polygon"

    def test_extra_state_attributes_has_polygon_true(
        self,
        mock_coordinator: MagicMock,
        mock_incident_with_single_polygon: EmergencyIncident,
    ) -> None:
        """Test that has_polygon attribute is exposed when true."""
        event = ABCEmergencyGeolocationEvent(mock_coordinator, mock_incident_with_single_polygon)

        attrs = event.extra_state_attributes

        assert attrs.get("has_polygon") is True

    def test_extra_state_attributes_has_polygon_false(
        self,
        mock_coordinator: MagicMock,
        mock_incident_point_only: EmergencyIncident,
    ) -> None:
        """Test that has_polygon attribute is exposed when false."""
        event = ABCEmergencyGeolocationEvent(mock_coordinator, mock_incident_point_only)

        attrs = event.extra_state_attributes

        assert attrs.get("has_polygon") is False

    def test_extra_state_attributes_multipolygon_with_holes(
        self,
        mock_coordinator: MagicMock,
        mock_incident_with_multipolygon_and_holes: EmergencyIncident,
    ) -> None:
        """Test MultiPolygon with inner rings in some polygons."""
        event = ABCEmergencyGeolocationEvent(
            mock_coordinator, mock_incident_with_multipolygon_and_holes
        )

        attrs = event.extra_state_attributes

        assert "geojson" in attrs
        geojson = attrs["geojson"]
        assert geojson["type"] == "MultiPolygon"
        assert len(geojson["coordinates"]) == 2

        # First polygon has an inner ring (hole)
        first_poly = geojson["coordinates"][0]
        assert len(first_poly) == 2  # outer + 1 hole
        assert first_poly[1] == [
            [151.22, -33.82],
            [151.28, -33.82],
            [151.28, -33.88],
            [151.22, -33.88],
            [151.22, -33.82],
        ]

        # Second polygon has no inner rings
        second_poly = geojson["coordinates"][1]
        assert len(second_poly) == 1  # just outer ring

    def test_extra_state_attributes_no_geojson_when_empty_polygon_list(
        self,
        mock_coordinator: MagicMock,
        mock_incident_has_polygon_but_empty_list: EmergencyIncident,
    ) -> None:
        """Test that geojson is not included when polygons list is empty."""
        event = ABCEmergencyGeolocationEvent(
            mock_coordinator, mock_incident_has_polygon_but_empty_list
        )

        attrs = event.extra_state_attributes

        # has_polygon may be True but geojson should not be present if list is empty
        assert "geojson" not in attrs

    def test_build_geojson_returns_none_for_empty_polygon_list(
        self,
        mock_coordinator: MagicMock,
        mock_incident_has_polygon_but_empty_list: EmergencyIncident,
    ) -> None:
        """Test that _build_geojson returns None when polygons list is empty."""
        event = ABCEmergencyGeolocationEvent(
            mock_coordinator, mock_incident_has_polygon_but_empty_list
        )

        # Call the private method directly to ensure coverage
        result = event._build_geojson()

        assert result is None

    def test_handle_coordinator_update_found(
        self,
        mock_coordinator: MagicMock,
        mock_incident_bushfire: EmergencyIncident,
    ) -> None:
        """Test handling coordinator update when incident is found."""
        event = ABCEmergencyGeolocationEvent(mock_coordinator, mock_incident_bushfire)
        event.async_write_ha_state = MagicMock()

        # Simulate coordinator update with updated incident
        updated_incident = EmergencyIncident(
            id=mock_incident_bushfire.id,
            headline="Updated Bushfire Headline",
            alert_level=mock_incident_bushfire.alert_level,
            alert_text=mock_incident_bushfire.alert_text,
            event_type=mock_incident_bushfire.event_type,
            event_icon=mock_incident_bushfire.event_icon,
            status=mock_incident_bushfire.status,
            size=mock_incident_bushfire.size,
            source=mock_incident_bushfire.source,
            location=mock_incident_bushfire.location,
            updated=datetime.now(UTC),
            distance_km=mock_incident_bushfire.distance_km,
            bearing=mock_incident_bushfire.bearing,
            direction=mock_incident_bushfire.direction,
        )
        mock_coordinator.data.incidents = [updated_incident]

        event._handle_coordinator_update()

        assert event._incident == updated_incident
        assert event.name == "Updated Bushfire Headline"
        event.async_write_ha_state.assert_called_once()

    def test_handle_coordinator_update_not_found(
        self,
        mock_coordinator: MagicMock,
        mock_incident_bushfire: EmergencyIncident,
    ) -> None:
        """Test handling coordinator update when incident is no longer present."""
        event = ABCEmergencyGeolocationEvent(mock_coordinator, mock_incident_bushfire)
        event.async_write_ha_state = MagicMock()

        # Simulate coordinator update without this incident
        mock_coordinator.data.incidents = []

        event._handle_coordinator_update()

        # Should not write state since incident is gone
        event.async_write_ha_state.assert_not_called()


class TestABCEmergencyGeoLocationManager:
    """Test ABCEmergencyGeoLocationManager."""

    def test_init(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test manager initialization."""
        add_entities = MagicMock()

        manager = ABCEmergencyGeoLocationManager(hass, mock_coordinator, add_entities)

        assert manager._hass is hass
        assert manager._coordinator is mock_coordinator
        assert manager._async_add_entities is add_entities
        assert manager._entities == {}

    def test_async_update_adds_new_entities(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
        mock_incident_bushfire: EmergencyIncident,
    ) -> None:
        """Test that async_update adds new entities."""
        add_entities = MagicMock()
        mock_coordinator.data = CoordinatorData(
            incidents=[mock_incident_bushfire],
            total_count=1,
            nearby_count=1,
        )

        manager = ABCEmergencyGeoLocationManager(hass, mock_coordinator, add_entities)
        manager.async_update()

        add_entities.assert_called_once()
        added = add_entities.call_args[0][0]
        assert len(added) == 1
        assert mock_incident_bushfire.id in manager._entities

    def test_async_update_no_duplicate_entities(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
        mock_incident_bushfire: EmergencyIncident,
    ) -> None:
        """Test that async_update doesn't add duplicates."""
        add_entities = MagicMock()
        mock_coordinator.data = CoordinatorData(
            incidents=[mock_incident_bushfire],
            total_count=1,
            nearby_count=1,
        )

        manager = ABCEmergencyGeoLocationManager(hass, mock_coordinator, add_entities)

        # First update adds entity
        manager.async_update()
        assert add_entities.call_count == 1

        # Second update should not add again
        manager.async_update()
        assert add_entities.call_count == 1

    def test_async_update_removes_old_entities(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
        mock_incident_bushfire: EmergencyIncident,
    ) -> None:
        """Test that async_update removes entities for removed incidents."""
        add_entities = MagicMock()
        mock_coordinator.data = CoordinatorData(
            incidents=[mock_incident_bushfire],
            total_count=1,
            nearby_count=1,
        )

        manager = ABCEmergencyGeoLocationManager(hass, mock_coordinator, add_entities)
        manager.async_update()

        # Get the entity that was added
        entity = manager._entities[mock_incident_bushfire.id]
        entity.async_remove = AsyncMock()

        # Update coordinator to have no incidents
        mock_coordinator.data = CoordinatorData(
            incidents=[],
            total_count=0,
            nearby_count=0,
        )

        manager.async_update()

        # Entity should be removed
        assert mock_incident_bushfire.id not in manager._entities

    def test_async_update_handles_none_data(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test that async_update handles None coordinator data."""
        add_entities = MagicMock()
        mock_coordinator.data = None

        manager = ABCEmergencyGeoLocationManager(hass, mock_coordinator, add_entities)
        manager.async_update()

        # Should not call add_entities when data is None
        add_entities.assert_not_called()

    def test_async_update_adds_multiple_entities(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
        mock_incident_bushfire: EmergencyIncident,
        mock_incident_flood: EmergencyIncident,
        mock_incident_storm: EmergencyIncident,
    ) -> None:
        """Test that async_update adds multiple entities."""
        add_entities = MagicMock()
        mock_coordinator.data = CoordinatorData(
            incidents=[mock_incident_bushfire, mock_incident_flood, mock_incident_storm],
            total_count=3,
            nearby_count=3,
        )

        manager = ABCEmergencyGeoLocationManager(hass, mock_coordinator, add_entities)
        manager.async_update()

        add_entities.assert_called_once()
        added = add_entities.call_args[0][0]
        assert len(added) == 3
        assert len(manager._entities) == 3


class TestAsyncSetupEntry:
    """Test async_setup_entry for geo location platform."""

    async def test_setup_creates_manager_and_updates(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test that setup creates manager and calls initial update."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="ABC Emergency (NSW)",
            data={
                CONF_LATITUDE: -33.8688,
                CONF_LONGITUDE: 151.2093,
                CONF_RADIUS: 50,
                CONF_USE_HOME_LOCATION: True,
            },
            unique_id="abc_emergency_nsw",
        )
        entry.add_to_hass(hass)

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = mock_coordinator

        entities_added: list = []

        def mock_add_entities(entities: list) -> None:
            entities_added.extend(entities)

        # Need to mock async_on_unload
        entry.async_on_unload = MagicMock()

        await async_setup_entry(hass, entry, mock_add_entities)

        # Should have added 3 entities (from mock_coordinator_data fixture)
        assert len(entities_added) == 3
        assert all(isinstance(e, ABCEmergencyGeolocationEvent) for e in entities_added)

    async def test_setup_uses_friendly_title_as_source(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test that source uses the friendly entry title directly."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="ABC Emergency (VIC)",
            data={},
            unique_id="abc_emergency_state_vic",
        )
        entry.add_to_hass(hass)

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = mock_coordinator

        entities_added: list[ABCEmergencyGeolocationEvent] = []

        def mock_add_entities(entities: list) -> None:
            entities_added.extend(entities)

        entry.async_on_unload = MagicMock()

        await async_setup_entry(hass, entry, mock_add_entities)

        # All entities should have the friendly title as source
        assert len(entities_added) == 3
        for entity in entities_added:
            assert entity.source == "ABC Emergency (VIC)"

    async def test_setup_zone_uses_friendly_title_as_source(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test that zone instance uses friendly title as source."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="ABC Emergency (My Home)",
            data={
                CONF_LATITUDE: -33.8688,
                CONF_LONGITUDE: 151.2093,
            },
            unique_id="abc_emergency_zone_my_home",
        )
        entry.add_to_hass(hass)

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = mock_coordinator

        entities_added: list[ABCEmergencyGeolocationEvent] = []

        def mock_add_entities(entities: list) -> None:
            entities_added.extend(entities)

        entry.async_on_unload = MagicMock()

        await async_setup_entry(hass, entry, mock_add_entities)

        # All entities should have the friendly title as source
        assert len(entities_added) == 3
        for entity in entities_added:
            assert entity.source == "ABC Emergency (My Home)"

    async def test_setup_person_uses_friendly_title_as_source(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test that person instance uses friendly title as source."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="ABC Emergency (Dad)",
            data={},
            unique_id="abc_emergency_person_dad",
        )
        entry.add_to_hass(hass)

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = mock_coordinator

        entities_added: list[ABCEmergencyGeolocationEvent] = []

        def mock_add_entities(entities: list) -> None:
            entities_added.extend(entities)

        entry.async_on_unload = MagicMock()

        await async_setup_entry(hass, entry, mock_add_entities)

        # All entities should have the friendly title as source
        assert len(entities_added) == 3
        for entity in entities_added:
            assert entity.source == "ABC Emergency (Dad)"

    async def test_setup_registers_listener(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test that setup registers update listener."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="ABC Emergency (NSW)",
            data={
                CONF_LATITUDE: -33.8688,
                CONF_LONGITUDE: 151.2093,
                CONF_RADIUS: 50,
                CONF_USE_HOME_LOCATION: True,
            },
            unique_id="abc_emergency_nsw",
        )
        entry.add_to_hass(hass)

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = mock_coordinator

        def mock_add_entities(entities: list) -> None:
            pass

        entry.async_on_unload = MagicMock()

        await async_setup_entry(hass, entry, mock_add_entities)

        # Should have registered listener
        mock_coordinator.async_add_listener.assert_called_once()
        entry.async_on_unload.assert_called_once()
