"""Tests for ABC Emergency config flow."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_RADIUS
from homeassistant.data_entry_flow import FlowResultType

from custom_components.abcemergency.const import (
    CONF_STATE,
    CONF_USE_HOME_LOCATION,
    DEFAULT_RADIUS_KM,
    DOMAIN,
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

    async def test_state_selection_proceeds_to_location(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
    ) -> None:
        """Test selecting a state proceeds to location step."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STATE: "nsw"},
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "location"

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
                {CONF_STATE: "nsw"},
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
                {CONF_STATE: "vic"},
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
                {CONF_STATE: "qld"},
            )

            assert result["type"] is FlowResultType.FORM
            assert result["errors"] == {"base": "unknown"}


class TestConfigFlowLocationStep:
    """Test the location step of config flow."""

    async def test_complete_flow_with_home_location(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
        mock_setup_entry: AsyncMock,
    ) -> None:
        """Test complete flow using home location."""
        # Set up home location in hass config
        hass.config.latitude = -33.8688
        hass.config.longitude = 151.2093

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STATE: "nsw"},
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "location"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USE_HOME_LOCATION: True,
                CONF_RADIUS: 50,
            },
        )

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == "ABC Emergency (New South Wales)"
        assert result["data"] == {
            CONF_STATE: "nsw",
            CONF_LATITUDE: -33.8688,
            CONF_LONGITUDE: 151.2093,
            CONF_RADIUS: 50,
            CONF_USE_HOME_LOCATION: True,
        }

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
            {CONF_STATE: "vic"},
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USE_HOME_LOCATION: False,
                "location": {
                    "latitude": -37.8136,
                    "longitude": 144.9631,
                },
                CONF_RADIUS: 100,
            },
        )

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == "ABC Emergency (Victoria)"
        assert result["data"][CONF_LATITUDE] == -37.8136
        assert result["data"][CONF_LONGITUDE] == 144.9631
        assert result["data"][CONF_RADIUS] == 100
        assert result["data"][CONF_USE_HOME_LOCATION] is False

    async def test_default_radius(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
        mock_setup_entry: AsyncMock,
    ) -> None:
        """Test default radius is used when not specified."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STATE: "sa"},
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USE_HOME_LOCATION: True,
            },
        )

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_RADIUS] == DEFAULT_RADIUS_KM


class TestConfigFlowDuplicates:
    """Test duplicate entry handling."""

    async def test_duplicate_state_aborts(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
        mock_setup_entry: AsyncMock,
    ) -> None:
        """Test that configuring same state twice aborts."""
        # Complete first entry
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STATE: "nsw"},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USE_HOME_LOCATION: True, CONF_RADIUS: 50},
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY

        # Try to configure same state again
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STATE: "nsw"},
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
        # Configure NSW
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STATE: "nsw"},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USE_HOME_LOCATION: True, CONF_RADIUS: 50},
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY

        # Configure VIC (should succeed)
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STATE: "vic"},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "location"


class TestOptionsFlow:
    """Test options flow."""

    async def test_options_flow_init(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
        mock_setup_entry: AsyncMock,
    ) -> None:
        """Test options flow initialization."""
        # Create config entry first
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STATE: "nsw"},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USE_HOME_LOCATION: True, CONF_RADIUS: 50},
        )

        # Get the config entry
        entry = hass.config_entries.async_entries(DOMAIN)[0]

        # Start options flow
        result = await hass.config_entries.options.async_init(entry.entry_id)

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "init"

    async def test_options_flow_update_radius(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
        mock_setup_entry: AsyncMock,
    ) -> None:
        """Test updating radius via options flow."""
        # Create config entry
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STATE: "nsw"},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USE_HOME_LOCATION: True, CONF_RADIUS: 50},
        )

        entry = hass.config_entries.async_entries(DOMAIN)[0]

        # Update options
        result = await hass.config_entries.options.async_init(entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {CONF_RADIUS: 100},
        )

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_RADIUS] == 100
