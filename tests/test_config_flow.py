"""Tests for ABC Emergency config flow."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.data_entry_flow import FlowResultType

from custom_components.abcemergency.const import (
    CONF_ENABLE_STATE_GEO,
    CONF_ENABLE_STATE_SENSORS,
    CONF_ENABLE_ZONE_GEO,
    CONF_ENABLE_ZONE_SENSORS,
    CONF_RADIUS_BUSHFIRE,
    CONF_RADIUS_EARTHQUAKE,
    CONF_RADIUS_FIRE,
    CONF_RADIUS_FLOOD,
    CONF_RADIUS_HEAT,
    CONF_RADIUS_OTHER,
    CONF_RADIUS_STORM,
    CONF_STATES,
    CONF_ZONE_NAME,
    CONF_ZONE_SOURCE,
    DEFAULT_RADIUS_BUSHFIRE,
    DEFAULT_RADIUS_EARTHQUAKE,
    DEFAULT_RADIUS_FIRE,
    DEFAULT_RADIUS_FLOOD,
    DEFAULT_RADIUS_HEAT,
    DEFAULT_RADIUS_OTHER,
    DEFAULT_RADIUS_STORM,
    DOMAIN,
    ZONE_SOURCE_CUSTOM,
    ZONE_SOURCE_HOME,
)
from custom_components.abcemergency.exceptions import (
    ABCEmergencyAPIError,
    ABCEmergencyConnectionError,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


@pytest.fixture
def mock_setup_entry(hass: HomeAssistant) -> AsyncMock:
    """Mock setting up a config entry."""
    from custom_components.abcemergency.const import DOMAIN

    async def mock_setup(hass_instance: HomeAssistant, entry: ConfigEntry) -> bool:
        """Mock setup that initializes hass.data."""
        hass_instance.data.setdefault(DOMAIN, {})
        # Create a mock coordinator for the entry
        hass_instance.data[DOMAIN][entry.entry_id] = MagicMock()
        return True

    with patch(
        "custom_components.abcemergency.async_setup_entry",
        side_effect=mock_setup,
    ) as mock:
        yield mock


@pytest.fixture
def mock_api_client() -> AsyncMock:
    """Mock ABC Emergency API client."""
    with patch("custom_components.abcemergency.config_flow.ABCEmergencyClient") as mock:
        mock_client = mock.return_value
        mock_client.async_get_emergencies_by_state = AsyncMock(
            return_value={
                "emergencies": [],
                "features": [],
                "mapBound": [[140.0, -38.0], [154.0, -28.0]],
                "stateName": "nsw",
                "incidentsNumber": 0,
                "stateCount": 0,
            }
        )
        yield mock


class TestConfigFlowUserStep:
    """Test the user step of config flow."""

    async def test_form_is_shown(self, hass: HomeAssistant) -> None:
        """Test that the form is shown on first load."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {}

    async def test_state_selection_proceeds_to_state_options(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
    ) -> None:
        """Test selecting states proceeds to state_options step."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STATES: ["nsw"]},
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "state_options"

    async def test_multi_state_selection(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
    ) -> None:
        """Test selecting multiple states proceeds to state_options step."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STATES: ["nsw", "vic", "qld"]},
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "state_options"

    async def test_no_states_selected_shows_error(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Test that selecting no states shows an error."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STATES: []},
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {"base": "no_states_selected"}

    async def test_connection_error_shows_error(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Test connection error shows appropriate error message."""
        with patch("custom_components.abcemergency.config_flow.ABCEmergencyClient") as mock:
            mock_client = mock.return_value
            mock_client.async_get_emergencies_by_state = AsyncMock(
                side_effect=ABCEmergencyConnectionError("Connection failed")
            )

            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )

            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_STATES: ["nsw"]},
            )

            assert result["type"] is FlowResultType.FORM
            assert result["errors"] == {"base": "cannot_connect"}

    async def test_api_error_shows_error(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Test API error shows appropriate error message."""
        with patch("custom_components.abcemergency.config_flow.ABCEmergencyClient") as mock:
            mock_client = mock.return_value
            mock_client.async_get_emergencies_by_state = AsyncMock(
                side_effect=ABCEmergencyAPIError("API error")
            )

            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )

            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_STATES: ["vic"]},
            )

            assert result["type"] is FlowResultType.FORM
            assert result["errors"] == {"base": "cannot_connect"}

    async def test_unexpected_error_shows_unknown(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Test unexpected error shows unknown error message."""
        with patch("custom_components.abcemergency.config_flow.ABCEmergencyClient") as mock:
            mock_client = mock.return_value
            mock_client.async_get_emergencies_by_state = AsyncMock(
                side_effect=RuntimeError("Unexpected")
            )

            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )

            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_STATES: ["qld"]},
            )

            assert result["type"] is FlowResultType.FORM
            assert result["errors"] == {"base": "unknown"}


class TestConfigFlowStateOptionsStep:
    """Test the state_options step of config flow."""

    async def test_state_options_proceeds_to_zone(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
    ) -> None:
        """Test state options step proceeds to zone step."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STATES: ["nsw"]},
        )
        assert result["step_id"] == "state_options"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ENABLE_STATE_SENSORS: True,
                CONF_ENABLE_STATE_GEO: False,
            },
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "zone"

    async def test_state_options_defaults(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
    ) -> None:
        """Test state options with default values."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STATES: ["nsw"]},
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},  # Use defaults
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "zone"


class TestConfigFlowZoneStep:
    """Test the zone step of config flow."""

    async def test_zone_home_proceeds_to_zone_radius(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
    ) -> None:
        """Test zone step with home location proceeds to zone_radius."""
        hass.config.latitude = -33.8688
        hass.config.longitude = 151.2093

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STATES: ["nsw"]},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ENABLE_STATE_SENSORS: True, CONF_ENABLE_STATE_GEO: True},
        )
        assert result["step_id"] == "zone"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ZONE_SOURCE: ZONE_SOURCE_HOME},
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "zone_radius"

    async def test_zone_custom_location(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
    ) -> None:
        """Test zone step with custom location."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STATES: ["vic"]},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ENABLE_STATE_SENSORS: True, CONF_ENABLE_STATE_GEO: True},
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ZONE_SOURCE: ZONE_SOURCE_CUSTOM,
                CONF_ZONE_NAME: "Melbourne",
                "location": {
                    "latitude": -37.8136,
                    "longitude": 144.9631,
                },
            },
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "zone_radius"


class TestConfigFlowZoneRadiusStep:
    """Test the zone_radius step of config flow."""

    async def test_zone_radius_proceeds_to_zone_options(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
    ) -> None:
        """Test zone_radius step proceeds to zone_options."""
        hass.config.latitude = -33.8688
        hass.config.longitude = 151.2093

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STATES: ["nsw"]},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ZONE_SOURCE: ZONE_SOURCE_HOME},
        )
        assert result["step_id"] == "zone_radius"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_RADIUS_BUSHFIRE: 60,
                CONF_RADIUS_EARTHQUAKE: 120,
                CONF_RADIUS_STORM: 80,
                CONF_RADIUS_FLOOD: 40,
                CONF_RADIUS_FIRE: 15,
                CONF_RADIUS_HEAT: 110,
                CONF_RADIUS_OTHER: 30,
            },
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "zone_options"

    async def test_zone_radius_defaults(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
    ) -> None:
        """Test zone_radius step with default values."""
        hass.config.latitude = -33.8688
        hass.config.longitude = 151.2093

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STATES: ["nsw"]},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ZONE_SOURCE: ZONE_SOURCE_HOME},
        )

        # Use defaults by providing empty dict (form has required fields with defaults)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "zone_options"


class TestConfigFlowZoneOptionsStep:
    """Test the zone_options step of config flow."""

    async def test_complete_flow_with_home_location(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
        mock_setup_entry: AsyncMock,
    ) -> None:
        """Test complete flow using home location."""
        hass.config.latitude = -33.8688
        hass.config.longitude = 151.2093

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STATES: ["nsw"]},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ENABLE_STATE_SENSORS: True, CONF_ENABLE_STATE_GEO: True},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ZONE_SOURCE: ZONE_SOURCE_HOME},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},  # Use default radii
        )
        assert result["step_id"] == "zone_options"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ENABLE_ZONE_SENSORS: True, CONF_ENABLE_ZONE_GEO: True},
        )

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == "ABC Emergency (New South Wales)"
        assert result["data"][CONF_STATES] == ["nsw"]
        assert result["data"][CONF_LATITUDE] == -33.8688
        assert result["data"][CONF_LONGITUDE] == 151.2093
        assert result["data"][CONF_ENABLE_STATE_SENSORS] is True
        assert result["data"][CONF_ENABLE_STATE_GEO] is True
        assert result["data"][CONF_ENABLE_ZONE_SENSORS] is True
        assert result["data"][CONF_ENABLE_ZONE_GEO] is True
        assert result["data"][CONF_RADIUS_BUSHFIRE] == DEFAULT_RADIUS_BUSHFIRE
        assert result["data"][CONF_RADIUS_EARTHQUAKE] == DEFAULT_RADIUS_EARTHQUAKE
        assert result["data"][CONF_RADIUS_STORM] == DEFAULT_RADIUS_STORM
        assert result["data"][CONF_RADIUS_FLOOD] == DEFAULT_RADIUS_FLOOD
        assert result["data"][CONF_RADIUS_FIRE] == DEFAULT_RADIUS_FIRE
        assert result["data"][CONF_RADIUS_HEAT] == DEFAULT_RADIUS_HEAT
        assert result["data"][CONF_RADIUS_OTHER] == DEFAULT_RADIUS_OTHER

    async def test_complete_flow_with_custom_location(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
        mock_setup_entry: AsyncMock,
    ) -> None:
        """Test complete flow using custom location."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STATES: ["vic"]},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ENABLE_STATE_SENSORS: False, CONF_ENABLE_STATE_GEO: True},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ZONE_SOURCE: ZONE_SOURCE_CUSTOM,
                CONF_ZONE_NAME: "Melbourne",
                "location": {"latitude": -37.8136, "longitude": 144.9631},
            },
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_RADIUS_BUSHFIRE: 100,
                CONF_RADIUS_EARTHQUAKE: 150,
                CONF_RADIUS_STORM: 100,
                CONF_RADIUS_FLOOD: 50,
                CONF_RADIUS_FIRE: 20,
                CONF_RADIUS_HEAT: 120,
                CONF_RADIUS_OTHER: 40,
            },
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ENABLE_ZONE_SENSORS: True, CONF_ENABLE_ZONE_GEO: False},
        )

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == "ABC Emergency (Victoria)"
        assert result["data"][CONF_LATITUDE] == -37.8136
        assert result["data"][CONF_LONGITUDE] == 144.9631
        assert result["data"][CONF_ZONE_NAME] == "Melbourne"
        assert result["data"][CONF_ENABLE_STATE_SENSORS] is False
        assert result["data"][CONF_ENABLE_ZONE_GEO] is False

    async def test_complete_flow_with_multiple_states(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
        mock_setup_entry: AsyncMock,
    ) -> None:
        """Test complete flow with multiple states selected."""
        hass.config.latitude = -33.8688
        hass.config.longitude = 151.2093

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STATES: ["nsw", "vic", "qld"]},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ZONE_SOURCE: ZONE_SOURCE_HOME},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert "New South Wales" in result["title"]
        assert "Victoria" in result["title"]
        assert "Queensland" in result["title"]

    async def test_complete_flow_with_many_states(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
        mock_setup_entry: AsyncMock,
    ) -> None:
        """Test complete flow with more than 3 states shows count."""
        hass.config.latitude = -33.8688
        hass.config.longitude = 151.2093

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STATES: ["nsw", "vic", "qld", "sa"]},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ZONE_SOURCE: ZONE_SOURCE_HOME},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == "ABC Emergency (4 states)"


class TestConfigFlowDuplicates:
    """Test duplicate entry handling."""

    async def test_duplicate_states_aborts(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
        mock_setup_entry: AsyncMock,
    ) -> None:
        """Test that configuring same states twice aborts."""
        hass.config.latitude = -33.8688
        hass.config.longitude = 151.2093

        # Complete first entry
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STATES: ["nsw"]},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ZONE_SOURCE: ZONE_SOURCE_HOME},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY

        # Try to configure same states again
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STATES: ["nsw"]},
        )

        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "already_configured"

    async def test_different_states_allowed(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
        mock_setup_entry: AsyncMock,
    ) -> None:
        """Test that different states can be configured."""
        hass.config.latitude = -33.8688
        hass.config.longitude = 151.2093

        # Configure NSW
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STATES: ["nsw"]},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ZONE_SOURCE: ZONE_SOURCE_HOME},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY

        # Configure VIC (should succeed)
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STATES: ["vic"]},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "state_options"


class TestOptionsFlow:
    """Test options flow."""

    async def test_options_flow_shows_menu(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
        mock_setup_entry: AsyncMock,
    ) -> None:
        """Test options flow shows menu."""
        hass.config.latitude = -33.8688
        hass.config.longitude = 151.2093

        # Create config entry first
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STATES: ["nsw"]},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ZONE_SOURCE: ZONE_SOURCE_HOME},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )

        # Get the config entry
        entry = hass.config_entries.async_entries(DOMAIN)[0]

        # Start options flow
        result = await hass.config_entries.options.async_init(entry.entry_id)

        assert result["type"] is FlowResultType.MENU
        assert result["step_id"] == "init"

    async def test_options_flow_state_options(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
        mock_setup_entry: AsyncMock,
    ) -> None:
        """Test updating state options via options flow."""
        hass.config.latitude = -33.8688
        hass.config.longitude = 151.2093

        # Create config entry
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STATES: ["nsw"]},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ZONE_SOURCE: ZONE_SOURCE_HOME},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )

        entry = hass.config_entries.async_entries(DOMAIN)[0]

        # Navigate to state_options
        result = await hass.config_entries.options.async_init(entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {"next_step_id": "state_options"},
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "state_options"

        # Update options
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {CONF_ENABLE_STATE_SENSORS: False, CONF_ENABLE_STATE_GEO: True},
        )

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_ENABLE_STATE_SENSORS] is False
        assert result["data"][CONF_ENABLE_STATE_GEO] is True

    async def test_options_flow_zone_radius(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
        mock_setup_entry: AsyncMock,
    ) -> None:
        """Test updating zone radius via options flow."""
        hass.config.latitude = -33.8688
        hass.config.longitude = 151.2093

        # Create config entry
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STATES: ["nsw"]},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ZONE_SOURCE: ZONE_SOURCE_HOME},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )

        entry = hass.config_entries.async_entries(DOMAIN)[0]

        # Navigate to zone_radius
        result = await hass.config_entries.options.async_init(entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {"next_step_id": "zone_radius"},
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "zone_radius"

        # Update radius values
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                CONF_RADIUS_BUSHFIRE: 100,
                CONF_RADIUS_EARTHQUAKE: 200,
                CONF_RADIUS_STORM: 150,
                CONF_RADIUS_FLOOD: 60,
                CONF_RADIUS_FIRE: 25,
                CONF_RADIUS_HEAT: 150,
                CONF_RADIUS_OTHER: 50,
            },
        )

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_RADIUS_BUSHFIRE] == 100
        assert result["data"][CONF_RADIUS_EARTHQUAKE] == 200

    async def test_options_flow_zone_options(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
        mock_setup_entry: AsyncMock,
    ) -> None:
        """Test updating zone options via options flow."""
        hass.config.latitude = -33.8688
        hass.config.longitude = 151.2093

        # Create config entry
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STATES: ["nsw"]},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ZONE_SOURCE: ZONE_SOURCE_HOME},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )

        entry = hass.config_entries.async_entries(DOMAIN)[0]

        # Navigate to zone_options
        result = await hass.config_entries.options.async_init(entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {"next_step_id": "zone_options"},
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "zone_options"

        # Update options
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {CONF_ENABLE_ZONE_SENSORS: False, CONF_ENABLE_ZONE_GEO: False},
        )

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_ENABLE_ZONE_SENSORS] is False
        assert result["data"][CONF_ENABLE_ZONE_GEO] is False
