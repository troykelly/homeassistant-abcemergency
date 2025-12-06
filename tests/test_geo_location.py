"""Tests for ABC Emergency geo location platform."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_RADIUS, UnitOfLength
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.abcemergency.const import (
    CONF_STATE,
    CONF_USE_HOME_LOCATION,
    DOMAIN,
    SOURCE,
    AlertLevel,
)
from custom_components.abcemergency.geo_location import (
    ABCEmergencyGeolocationEvent,
    ABCEmergencyGeoLocationManager,
    async_setup_entry,
)
from custom_components.abcemergency.models import (
    CoordinatorData,
    EmergencyIncident,
)

if TYPE_CHECKING:
    pass


class TestABCEmergencyGeolocationEvent:
    """Test ABCEmergencyGeolocationEvent entity."""

    def test_unique_id(
        self,
        mock_coordinator: MagicMock,
        mock_incident_bushfire: EmergencyIncident,
    ) -> None:
        """Test unique ID is correctly generated."""
        event = ABCEmergencyGeolocationEvent(mock_coordinator, mock_incident_bushfire)

        assert event.unique_id == f"{SOURCE}_{mock_incident_bushfire.id}"

    def test_name(
        self,
        mock_coordinator: MagicMock,
        mock_incident_bushfire: EmergencyIncident,
    ) -> None:
        """Test name is set to headline."""
        event = ABCEmergencyGeolocationEvent(mock_coordinator, mock_incident_bushfire)

        assert event.name == mock_incident_bushfire.headline

    def test_source(
        self,
        mock_coordinator: MagicMock,
        mock_incident_bushfire: EmergencyIncident,
    ) -> None:
        """Test source property."""
        event = ABCEmergencyGeolocationEvent(mock_coordinator, mock_incident_bushfire)

        assert event.source == SOURCE

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
        assert attrs["source"] == "NSW Rural Fire Service"
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
            data={
                CONF_STATE: "nsw",
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

    async def test_setup_registers_listener(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test that setup registers update listener."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_STATE: "nsw",
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
