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
    CONF_INSTANCE_TYPE,
    CONF_PERSON_ENTITY_ID,
    CONF_PERSON_NAME,
    CONF_RADIUS_BUSHFIRE,
    CONF_RADIUS_EARTHQUAKE,
    CONF_RADIUS_FIRE,
    CONF_RADIUS_FLOOD,
    CONF_RADIUS_HEAT,
    CONF_RADIUS_OTHER,
    CONF_RADIUS_STORM,
    CONF_STATE,
    CONF_ZONE_NAME,
    DEFAULT_RADIUS_BUSHFIRE,
    DEFAULT_RADIUS_EARTHQUAKE,
    DEFAULT_RADIUS_FIRE,
    DEFAULT_RADIUS_FLOOD,
    DEFAULT_RADIUS_HEAT,
    DEFAULT_RADIUS_OTHER,
    DEFAULT_RADIUS_STORM,
    DOMAIN,
    INSTANCE_TYPE_PERSON,
    INSTANCE_TYPE_STATE,
    INSTANCE_TYPE_ZONE,
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
    """Test the user step of config flow (instance type selection)."""

    async def test_form_is_shown(self, hass: HomeAssistant) -> None:
        """Test that the form is shown on first load."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"

    async def test_selecting_state_proceeds_to_state_step(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Test selecting state instance type proceeds to state step."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_INSTANCE_TYPE: INSTANCE_TYPE_STATE},
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "state"

    async def test_selecting_zone_proceeds_to_zone_name_step(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Test selecting zone instance type proceeds to zone_name step."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE},
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "zone_name"

    async def test_selecting_person_proceeds_to_person_step(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Test selecting person instance type proceeds to person step."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_INSTANCE_TYPE: INSTANCE_TYPE_PERSON},
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "person"


class TestConfigFlowStateStep:
    """Test the state step of config flow."""

    async def test_state_selection_creates_entry(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
        mock_setup_entry: AsyncMock,
    ) -> None:
        """Test selecting a state creates an entry."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_INSTANCE_TYPE: INSTANCE_TYPE_STATE},
        )
        assert result["step_id"] == "state"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STATE: "nsw"},
        )

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == "ABC Emergency (New South Wales)"
        assert result["data"][CONF_INSTANCE_TYPE] == INSTANCE_TYPE_STATE
        assert result["data"][CONF_STATE] == "nsw"

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
                {CONF_INSTANCE_TYPE: INSTANCE_TYPE_STATE},
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
                {CONF_INSTANCE_TYPE: INSTANCE_TYPE_STATE},
            )

            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_STATE: "vic"},
            )

            assert result["type"] is FlowResultType.FORM
            assert result["errors"] == {"base": "api_error"}

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
                {CONF_INSTANCE_TYPE: INSTANCE_TYPE_STATE},
            )

            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_STATE: "qld"},
            )

            assert result["type"] is FlowResultType.FORM
            assert result["errors"] == {"base": "unknown"}

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
            {CONF_INSTANCE_TYPE: INSTANCE_TYPE_STATE},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STATE: "nsw"},
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY

        # Try to configure same state again
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_INSTANCE_TYPE: INSTANCE_TYPE_STATE},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STATE: "nsw"},
        )

        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "already_configured"


class TestConfigFlowZoneSteps:
    """Test the zone configuration flow."""

    async def test_zone_name_empty_shows_error(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Test zone name empty shows error."""
        hass.config.latitude = -33.8688
        hass.config.longitude = 151.2093

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE},
        )
        assert result["step_id"] == "zone_name"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ZONE_NAME: "",  # Empty name
                "location": {"latitude": -33.8688, "longitude": 151.2093},
            },
        )

        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": "name_required"}

    async def test_zone_name_step_proceeds_to_radius(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Test zone_name step proceeds to zone_radius."""
        hass.config.latitude = -33.8688
        hass.config.longitude = 151.2093

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE},
        )
        assert result["step_id"] == "zone_name"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ZONE_NAME: "Home",
                "location": {"latitude": -33.8688, "longitude": 151.2093},
            },
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "zone_radius"

    async def test_zone_flow_creates_entry(
        self,
        hass: HomeAssistant,
        mock_setup_entry: AsyncMock,
    ) -> None:
        """Test complete zone flow creates entry."""
        hass.config.latitude = -33.8688
        hass.config.longitude = 151.2093

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ZONE_NAME: "Home",
                "location": {"latitude": -33.8688, "longitude": 151.2093},
            },
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},  # Use default radii
        )

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == "ABC Emergency (Home)"
        assert result["data"][CONF_INSTANCE_TYPE] == INSTANCE_TYPE_ZONE
        assert result["data"][CONF_ZONE_NAME] == "Home"
        assert result["data"][CONF_LATITUDE] == -33.8688
        assert result["data"][CONF_LONGITUDE] == 151.2093
        assert result["data"][CONF_RADIUS_BUSHFIRE] == DEFAULT_RADIUS_BUSHFIRE
        assert result["data"][CONF_RADIUS_EARTHQUAKE] == DEFAULT_RADIUS_EARTHQUAKE
        assert result["data"][CONF_RADIUS_STORM] == DEFAULT_RADIUS_STORM
        assert result["data"][CONF_RADIUS_FLOOD] == DEFAULT_RADIUS_FLOOD
        assert result["data"][CONF_RADIUS_FIRE] == DEFAULT_RADIUS_FIRE
        assert result["data"][CONF_RADIUS_HEAT] == DEFAULT_RADIUS_HEAT
        assert result["data"][CONF_RADIUS_OTHER] == DEFAULT_RADIUS_OTHER

    async def test_zone_custom_radii(
        self,
        hass: HomeAssistant,
        mock_setup_entry: AsyncMock,
    ) -> None:
        """Test zone flow with custom radii."""
        hass.config.latitude = -33.8688
        hass.config.longitude = 151.2093

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ZONE_NAME: "Office",
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

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_RADIUS_BUSHFIRE] == 100
        assert result["data"][CONF_RADIUS_EARTHQUAKE] == 150

    async def test_duplicate_zone_name_aborts(
        self,
        hass: HomeAssistant,
        mock_setup_entry: AsyncMock,
    ) -> None:
        """Test that configuring same zone name twice aborts."""
        hass.config.latitude = -33.8688
        hass.config.longitude = 151.2093

        # Complete first zone entry
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ZONE_NAME: "Home",
                "location": {"latitude": -33.8688, "longitude": 151.2093},
            },
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY

        # Try to configure same zone name again
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ZONE_NAME: "Home",
                "location": {"latitude": -34.0, "longitude": 151.0},
            },
        )

        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "already_configured"


class TestConfigFlowPersonSteps:
    """Test the person configuration flow."""

    async def test_person_step_requires_entity(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Test person step shows form."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_INSTANCE_TYPE: INSTANCE_TYPE_PERSON},
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "person"

    async def test_person_name_from_entity_registry(
        self,
        hass: HomeAssistant,
        mock_setup_entry: AsyncMock,
    ) -> None:
        """Test person name is taken from entity registry when available."""
        from homeassistant.helpers import entity_registry as er

        # Create entity in registry with a custom name
        ent_reg = er.async_get(hass)
        ent_reg.async_get_or_create(
            domain="person",
            platform="test",
            unique_id="registry_person",
            suggested_object_id="registry_person",
        )
        # Update the entity entry with a name
        entity_entry = ent_reg.async_get("person.registry_person")
        if entity_entry:
            ent_reg.async_update_entity(
                "person.registry_person",
                name="Registry Name",
            )

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_INSTANCE_TYPE: INSTANCE_TYPE_PERSON},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PERSON_ENTITY_ID: "person.registry_person"},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_PERSON_NAME] == "Registry Name"

    async def test_person_name_from_entity_id_fallback(
        self,
        hass: HomeAssistant,
        mock_setup_entry: AsyncMock,
    ) -> None:
        """Test person name falls back to entity_id when no other name available."""
        # Create person entity with no friendly_name attribute and no registry name
        hass.states.async_set(
            "person.some_user",
            "home",
            {},  # No friendly_name attribute
        )

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_INSTANCE_TYPE: INSTANCE_TYPE_PERSON},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PERSON_ENTITY_ID: "person.some_user"},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )

        assert result["type"] is FlowResultType.CREATE_ENTRY
        # Name should be extracted from entity_id: "some_user" -> "Some User"
        assert result["data"][CONF_PERSON_NAME] == "Some User"

    async def test_person_flow_creates_entry(
        self,
        hass: HomeAssistant,
        mock_setup_entry: AsyncMock,
    ) -> None:
        """Test complete person flow creates entry."""
        # Create a mock person entity
        hass.states.async_set(
            "person.john",
            "home",
            {"friendly_name": "John", "latitude": -33.8688, "longitude": 151.2093},
        )

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_INSTANCE_TYPE: INSTANCE_TYPE_PERSON},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PERSON_ENTITY_ID: "person.john"},
        )
        assert result["step_id"] == "person_radius"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},  # Use default radii
        )

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == "ABC Emergency (John)"
        assert result["data"][CONF_INSTANCE_TYPE] == INSTANCE_TYPE_PERSON
        assert result["data"][CONF_PERSON_ENTITY_ID] == "person.john"
        assert result["data"][CONF_PERSON_NAME] == "John"
        assert result["data"][CONF_RADIUS_BUSHFIRE] == DEFAULT_RADIUS_BUSHFIRE

    async def test_person_custom_radii(
        self,
        hass: HomeAssistant,
        mock_setup_entry: AsyncMock,
    ) -> None:
        """Test person flow with custom radii."""
        hass.states.async_set(
            "person.jane",
            "home",
            {"friendly_name": "Jane", "latitude": -33.8688, "longitude": 151.2093},
        )

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_INSTANCE_TYPE: INSTANCE_TYPE_PERSON},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PERSON_ENTITY_ID: "person.jane"},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_RADIUS_BUSHFIRE: 80,
                CONF_RADIUS_EARTHQUAKE: 120,
                CONF_RADIUS_STORM: 90,
                CONF_RADIUS_FLOOD: 40,
                CONF_RADIUS_FIRE: 15,
                CONF_RADIUS_HEAT: 110,
                CONF_RADIUS_OTHER: 35,
            },
        )

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_RADIUS_BUSHFIRE] == 80

    async def test_duplicate_person_aborts(
        self,
        hass: HomeAssistant,
        mock_setup_entry: AsyncMock,
    ) -> None:
        """Test that configuring same person twice aborts."""
        hass.states.async_set(
            "person.john",
            "home",
            {"friendly_name": "John", "latitude": -33.8688, "longitude": 151.2093},
        )

        # Complete first person entry
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_INSTANCE_TYPE: INSTANCE_TYPE_PERSON},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PERSON_ENTITY_ID: "person.john"},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY

        # Try to configure same person again
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_INSTANCE_TYPE: INSTANCE_TYPE_PERSON},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PERSON_ENTITY_ID: "person.john"},
        )

        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "already_configured"


class TestOptionsFlow:
    """Test options flow."""

    async def test_options_flow_aborts_for_state(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
        mock_setup_entry: AsyncMock,
    ) -> None:
        """Test options flow aborts for state instances."""
        # Create state entry
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_INSTANCE_TYPE: INSTANCE_TYPE_STATE},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STATE: "nsw"},
        )

        # Get the config entry
        entry = hass.config_entries.async_entries(DOMAIN)[0]

        # Start options flow
        result = await hass.config_entries.options.async_init(entry.entry_id)

        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "no_options_state"

    async def test_options_flow_for_zone(
        self,
        hass: HomeAssistant,
        mock_setup_entry: AsyncMock,
    ) -> None:
        """Test options flow for zone instances."""
        hass.config.latitude = -33.8688
        hass.config.longitude = 151.2093

        # Create zone entry
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_INSTANCE_TYPE: INSTANCE_TYPE_ZONE},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ZONE_NAME: "Home",
                "location": {"latitude": -33.8688, "longitude": 151.2093},
            },
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )

        # Get the config entry
        entry = hass.config_entries.async_entries(DOMAIN)[0]

        # Start options flow
        result = await hass.config_entries.options.async_init(entry.entry_id)

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "radius"

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

    async def test_options_flow_for_person(
        self,
        hass: HomeAssistant,
        mock_setup_entry: AsyncMock,
    ) -> None:
        """Test options flow for person instances."""
        hass.states.async_set(
            "person.john",
            "home",
            {"friendly_name": "John", "latitude": -33.8688, "longitude": 151.2093},
        )

        # Create person entry
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_INSTANCE_TYPE: INSTANCE_TYPE_PERSON},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PERSON_ENTITY_ID: "person.john"},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )

        # Get the config entry
        entry = hass.config_entries.async_entries(DOMAIN)[0]

        # Start options flow
        result = await hass.config_entries.options.async_init(entry.entry_id)

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "radius"

        # Update radius values
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                CONF_RADIUS_BUSHFIRE: 75,
                CONF_RADIUS_EARTHQUAKE: 125,
                CONF_RADIUS_STORM: 80,
                CONF_RADIUS_FLOOD: 35,
                CONF_RADIUS_FIRE: 12,
                CONF_RADIUS_HEAT: 90,
                CONF_RADIUS_OTHER: 30,
            },
        )

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_RADIUS_BUSHFIRE] == 75
