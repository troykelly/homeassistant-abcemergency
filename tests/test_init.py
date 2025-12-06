"""Tests for ABC Emergency integration setup."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.abcemergency import (
    PLATFORMS,
    async_migrate_entry,
    async_setup_entry,
    async_unload_entry,
    async_update_options,
)
from custom_components.abcemergency.const import (
    CONF_INSTANCE_TYPE,
    CONF_PERSON_ENTITY_ID,
    CONF_PERSON_NAME,
    CONF_STATE,
    CONF_ZONE_NAME,
    DOMAIN,
    INSTANCE_TYPE_PERSON,
    INSTANCE_TYPE_STATE,
    INSTANCE_TYPE_ZONE,
)

if TYPE_CHECKING:
    pass


class TestPlatforms:
    """Test platform constants."""

    def test_platforms_defined(self) -> None:
        """Test that platforms are defined."""
        assert len(PLATFORMS) == 3

    def test_sensor_platform_included(self) -> None:
        """Test that sensor platform is included."""
        from homeassistant.const import Platform

        assert Platform.SENSOR in PLATFORMS

    def test_binary_sensor_platform_included(self) -> None:
        """Test that binary_sensor platform is included."""
        from homeassistant.const import Platform

        assert Platform.BINARY_SENSOR in PLATFORMS

    def test_geo_location_platform_included(self) -> None:
        """Test that geo_location platform is included."""
        from homeassistant.const import Platform

        assert Platform.GEO_LOCATION in PLATFORMS


class TestAsyncSetupEntry:
    """Test async_setup_entry function."""

    async def test_setup_creates_coordinator_state_mode(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Test that setup creates coordinator for state mode."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_STATE,
                CONF_STATE: "nsw",
            },
            unique_id="abc_emergency_state_nsw",
        )
        entry.add_to_hass(hass)

        with (
            patch("custom_components.abcemergency.ABCEmergencyClient"),
            patch(
                "custom_components.abcemergency.ABCEmergencyCoordinator"
            ) as mock_coordinator_class,
            patch.object(
                hass.config_entries, "async_forward_entry_setups", new_callable=AsyncMock
            ) as mock_forward,
        ):
            mock_coordinator = mock_coordinator_class.return_value
            mock_coordinator.async_config_entry_first_refresh = AsyncMock()

            result = await async_setup_entry(hass, entry)

            assert result is True
            assert DOMAIN in hass.data
            assert entry.entry_id in hass.data[DOMAIN]
            mock_coordinator_class.assert_called_once()
            # Verify state mode parameters
            call_kwargs = mock_coordinator_class.call_args.kwargs
            assert call_kwargs["instance_type"] == INSTANCE_TYPE_STATE
            assert call_kwargs["state"] == "nsw"
            mock_forward.assert_called_once_with(entry, PLATFORMS)

    async def test_setup_creates_coordinator_zone_mode(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Test that setup creates coordinator for zone mode."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE,
                CONF_ZONE_NAME: "Home",
                CONF_LATITUDE: -33.8688,
                CONF_LONGITUDE: 151.2093,
            },
            unique_id="abc_emergency_zone_home",
        )
        entry.add_to_hass(hass)

        with (
            patch("custom_components.abcemergency.ABCEmergencyClient"),
            patch(
                "custom_components.abcemergency.ABCEmergencyCoordinator"
            ) as mock_coordinator_class,
            patch.object(hass.config_entries, "async_forward_entry_setups", new_callable=AsyncMock),
        ):
            mock_coordinator = mock_coordinator_class.return_value
            mock_coordinator.async_config_entry_first_refresh = AsyncMock()

            result = await async_setup_entry(hass, entry)

            assert result is True
            call_kwargs = mock_coordinator_class.call_args.kwargs
            assert call_kwargs["instance_type"] == INSTANCE_TYPE_ZONE
            assert call_kwargs["latitude"] == -33.8688
            assert call_kwargs["longitude"] == 151.2093

    async def test_setup_creates_coordinator_person_mode(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Test that setup creates coordinator for person mode."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_PERSON,
                CONF_PERSON_ENTITY_ID: "person.john",
                CONF_PERSON_NAME: "John",
            },
            unique_id="abc_emergency_person_john",
        )
        entry.add_to_hass(hass)

        with (
            patch("custom_components.abcemergency.ABCEmergencyClient"),
            patch(
                "custom_components.abcemergency.ABCEmergencyCoordinator"
            ) as mock_coordinator_class,
            patch.object(hass.config_entries, "async_forward_entry_setups", new_callable=AsyncMock),
        ):
            mock_coordinator = mock_coordinator_class.return_value
            mock_coordinator.async_config_entry_first_refresh = AsyncMock()

            result = await async_setup_entry(hass, entry)

            assert result is True
            call_kwargs = mock_coordinator_class.call_args.kwargs
            assert call_kwargs["instance_type"] == INSTANCE_TYPE_PERSON
            assert call_kwargs["person_entity_id"] == "person.john"

    async def test_setup_registers_update_listener(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Test that setup registers options update listener."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_STATE,
                CONF_STATE: "nsw",
            },
            unique_id="abc_emergency_state_nsw",
        )
        entry.add_to_hass(hass)

        with (
            patch("custom_components.abcemergency.ABCEmergencyClient"),
            patch(
                "custom_components.abcemergency.ABCEmergencyCoordinator"
            ) as mock_coordinator_class,
            patch.object(hass.config_entries, "async_forward_entry_setups", new_callable=AsyncMock),
        ):
            mock_coordinator = mock_coordinator_class.return_value
            mock_coordinator.async_config_entry_first_refresh = AsyncMock()

            # Spy on entry.add_update_listener
            original_add = entry.add_update_listener
            entry.add_update_listener = MagicMock(wraps=original_add)

            await async_setup_entry(hass, entry)

            entry.add_update_listener.assert_called_once_with(async_update_options)


class TestAsyncUnloadEntry:
    """Test async_unload_entry function."""

    async def test_unload_success(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Test successful unload."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_STATE,
                CONF_STATE: "nsw",
            },
            unique_id="abc_emergency_state_nsw",
        )
        entry.add_to_hass(hass)

        # Set up the data structure
        hass.data[DOMAIN] = {entry.entry_id: MagicMock()}

        with patch.object(
            hass.config_entries,
            "async_unload_platforms",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_unload:
            result = await async_unload_entry(hass, entry)

            assert result is True
            mock_unload.assert_called_once_with(entry, PLATFORMS)
            assert entry.entry_id not in hass.data[DOMAIN]

    async def test_unload_failure(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Test unload failure keeps data."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_STATE,
                CONF_STATE: "nsw",
            },
            unique_id="abc_emergency_state_nsw",
        )
        entry.add_to_hass(hass)

        # Set up the data structure
        coordinator = MagicMock()
        hass.data[DOMAIN] = {entry.entry_id: coordinator}

        with patch.object(
            hass.config_entries,
            "async_unload_platforms",
            new_callable=AsyncMock,
            return_value=False,
        ):
            result = await async_unload_entry(hass, entry)

            assert result is False
            # Data should still be present since unload failed
            assert entry.entry_id in hass.data[DOMAIN]


class TestAsyncUpdateOptions:
    """Test async_update_options function."""

    async def test_update_options_reloads_entry(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Test that updating options reloads the config entry."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_STATE,
                CONF_STATE: "nsw",
            },
            unique_id="abc_emergency_state_nsw",
        )
        entry.add_to_hass(hass)

        with patch.object(
            hass.config_entries,
            "async_reload",
            new_callable=AsyncMock,
        ) as mock_reload:
            await async_update_options(hass, entry)

            mock_reload.assert_called_once_with(entry.entry_id)


class TestAsyncMigrateEntry:
    """Test config entry migration."""

    async def test_migrate_v1_to_v3(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Test migration from v1 to v3."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_STATE: "nsw",
            },
            unique_id="abc_emergency_nsw",
            version=1,
        )
        entry.add_to_hass(hass)

        result = await async_migrate_entry(hass, entry)

        assert result is True
        assert entry.version == 3
        assert entry.data[CONF_INSTANCE_TYPE] == INSTANCE_TYPE_STATE
        assert entry.data[CONF_STATE] == "nsw"

    async def test_migrate_v2_to_v3(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Test migration from v2 to v3."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "states": ["nsw", "vic"],
            },
            unique_id="abc_emergency_multi",
            version=2,
        )
        entry.add_to_hass(hass)

        result = await async_migrate_entry(hass, entry)

        assert result is True
        assert entry.version == 3
        assert entry.data[CONF_INSTANCE_TYPE] == INSTANCE_TYPE_STATE
        assert entry.data[CONF_STATE] == "nsw"  # First state only

    async def test_migrate_v2_no_states_fails(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Test migration from v2 with no states fails."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "states": [],
            },
            unique_id="abc_emergency_empty",
            version=2,
        )
        entry.add_to_hass(hass)

        result = await async_migrate_entry(hass, entry)

        assert result is False


class TestIntegrationSetup:
    """Integration tests for full setup/unload cycle."""

    async def test_full_setup_and_unload(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Test full setup and unload cycle."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_INSTANCE_TYPE: INSTANCE_TYPE_STATE,
                CONF_STATE: "nsw",
            },
            unique_id="abc_emergency_state_nsw",
        )
        entry.add_to_hass(hass)

        mock_coordinator = MagicMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_coordinator.data = None

        with (
            patch("custom_components.abcemergency.ABCEmergencyClient"),
            patch(
                "custom_components.abcemergency.ABCEmergencyCoordinator",
                return_value=mock_coordinator,
            ),
            patch.object(hass.config_entries, "async_forward_entry_setups", new_callable=AsyncMock),
            patch.object(
                hass.config_entries,
                "async_unload_platforms",
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            # Setup
            result = await async_setup_entry(hass, entry)
            assert result is True
            assert DOMAIN in hass.data
            assert entry.entry_id in hass.data[DOMAIN]

            # Unload
            result = await async_unload_entry(hass, entry)
            assert result is True
            assert entry.entry_id not in hass.data[DOMAIN]
