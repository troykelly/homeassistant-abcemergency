"""Config flow for ABC Emergency integration.

This module provides the configuration flow for setting up ABC Emergency
via the Home Assistant UI. Users can select states, configure state-wide
and zone-filtered monitoring with per-incident-type radius settings.
"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    BooleanSelector,
    LocationSelector,
    LocationSelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import ABCEmergencyClient
from .const import (
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
    STATE_NAMES,
    STATES,
    ZONE_SOURCE_CUSTOM,
    ZONE_SOURCE_HOME,
)
from .exceptions import ABCEmergencyAPIError, ABCEmergencyConnectionError

_LOGGER = logging.getLogger(__name__)


class ABCEmergencyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for ABC Emergency."""

    VERSION = 2

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle the initial step - state/territory selection."""
        errors: dict[str, str] = {}

        if user_input is not None:
            states = user_input[CONF_STATES]
            if not states:
                errors["base"] = "no_states_selected"
            else:
                # Create unique ID from sorted states
                unique_id = f"abc_emergency_{'_'.join(sorted(states))}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                # Test API connectivity with first state
                try:
                    session = async_get_clientsession(self.hass)
                    client = ABCEmergencyClient(session)
                    await client.async_get_emergencies_by_state(states[0])
                except ABCEmergencyConnectionError:
                    errors["base"] = "cannot_connect"
                except ABCEmergencyAPIError:
                    errors["base"] = "cannot_connect"
                except Exception:
                    _LOGGER.exception("Unexpected error during API test")
                    errors["base"] = "unknown"

                if not errors:
                    self._data[CONF_STATES] = states
                    return await self.async_step_state_options()

        # Build state options
        state_options = [
            SelectOptionDict(value=code, label=STATE_NAMES.get(code, code.upper()))
            for code in STATES
        ]

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STATES, default=[]): SelectSelector(
                        SelectSelectorConfig(
                            options=state_options,
                            mode=SelectSelectorMode.DROPDOWN,
                            multiple=True,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_state_options(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle state-wide options configuration."""
        if user_input is not None:
            self._data[CONF_ENABLE_STATE_SENSORS] = user_input.get(CONF_ENABLE_STATE_SENSORS, True)
            self._data[CONF_ENABLE_STATE_GEO] = user_input.get(CONF_ENABLE_STATE_GEO, True)
            return await self.async_step_zone()

        return self.async_show_form(
            step_id="state_options",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ENABLE_STATE_SENSORS, default=True): BooleanSelector(),
                    vol.Required(CONF_ENABLE_STATE_GEO, default=True): BooleanSelector(),
                }
            ),
        )

    async def async_step_zone(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle zone configuration."""
        if user_input is not None:
            zone_source = user_input.get(CONF_ZONE_SOURCE, ZONE_SOURCE_HOME)
            self._data[CONF_ZONE_SOURCE] = zone_source

            if zone_source == ZONE_SOURCE_HOME:
                # Use Home Assistant's configured location
                self._data[CONF_LATITUDE] = self.hass.config.latitude
                self._data[CONF_LONGITUDE] = self.hass.config.longitude
                self._data[CONF_ZONE_NAME] = "home"
            else:
                # Use custom location
                location = user_input.get("location", {})
                self._data[CONF_LATITUDE] = location.get("latitude", self.hass.config.latitude)
                self._data[CONF_LONGITUDE] = location.get("longitude", self.hass.config.longitude)
                self._data[CONF_ZONE_NAME] = user_input.get(CONF_ZONE_NAME, "custom")

            return await self.async_step_zone_radius()

        zone_options = [
            SelectOptionDict(value=ZONE_SOURCE_HOME, label="Home Zone"),
            SelectOptionDict(value=ZONE_SOURCE_CUSTOM, label="Custom Location"),
        ]

        return self.async_show_form(
            step_id="zone",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ZONE_SOURCE, default=ZONE_SOURCE_HOME): SelectSelector(
                        SelectSelectorConfig(
                            options=zone_options,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional(CONF_ZONE_NAME): vol.All(str, vol.Length(min=1, max=50)),
                    vol.Optional("location"): LocationSelector(
                        LocationSelectorConfig(radius=False, icon="mdi:map-marker")
                    ),
                }
            ),
        )

    async def async_step_zone_radius(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle per-incident-type radius configuration."""
        if user_input is not None:
            self._data[CONF_RADIUS_BUSHFIRE] = user_input.get(
                CONF_RADIUS_BUSHFIRE, DEFAULT_RADIUS_BUSHFIRE
            )
            self._data[CONF_RADIUS_EARTHQUAKE] = user_input.get(
                CONF_RADIUS_EARTHQUAKE, DEFAULT_RADIUS_EARTHQUAKE
            )
            self._data[CONF_RADIUS_STORM] = user_input.get(CONF_RADIUS_STORM, DEFAULT_RADIUS_STORM)
            self._data[CONF_RADIUS_FLOOD] = user_input.get(CONF_RADIUS_FLOOD, DEFAULT_RADIUS_FLOOD)
            self._data[CONF_RADIUS_FIRE] = user_input.get(CONF_RADIUS_FIRE, DEFAULT_RADIUS_FIRE)
            self._data[CONF_RADIUS_HEAT] = user_input.get(CONF_RADIUS_HEAT, DEFAULT_RADIUS_HEAT)
            self._data[CONF_RADIUS_OTHER] = user_input.get(CONF_RADIUS_OTHER, DEFAULT_RADIUS_OTHER)
            return await self.async_step_zone_options()

        radius_config = NumberSelectorConfig(
            min=1,
            max=500,
            step=1,
            unit_of_measurement="km",
            mode=NumberSelectorMode.BOX,
        )

        return self.async_show_form(
            step_id="zone_radius",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_RADIUS_BUSHFIRE, default=DEFAULT_RADIUS_BUSHFIRE
                    ): NumberSelector(radius_config),
                    vol.Required(
                        CONF_RADIUS_EARTHQUAKE, default=DEFAULT_RADIUS_EARTHQUAKE
                    ): NumberSelector(radius_config),
                    vol.Required(CONF_RADIUS_STORM, default=DEFAULT_RADIUS_STORM): NumberSelector(
                        radius_config
                    ),
                    vol.Required(CONF_RADIUS_FLOOD, default=DEFAULT_RADIUS_FLOOD): NumberSelector(
                        radius_config
                    ),
                    vol.Required(CONF_RADIUS_FIRE, default=DEFAULT_RADIUS_FIRE): NumberSelector(
                        radius_config
                    ),
                    vol.Required(CONF_RADIUS_HEAT, default=DEFAULT_RADIUS_HEAT): NumberSelector(
                        radius_config
                    ),
                    vol.Required(CONF_RADIUS_OTHER, default=DEFAULT_RADIUS_OTHER): NumberSelector(
                        radius_config
                    ),
                }
            ),
        )

    async def async_step_zone_options(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle zone-filtered entity options."""
        if user_input is not None:
            self._data[CONF_ENABLE_ZONE_SENSORS] = user_input.get(CONF_ENABLE_ZONE_SENSORS, True)
            self._data[CONF_ENABLE_ZONE_GEO] = user_input.get(CONF_ENABLE_ZONE_GEO, True)

            # Build title from states
            states = self._data.get(CONF_STATES, [])
            if len(states) == 1:
                state_label = STATE_NAMES.get(states[0], states[0].upper())
            elif len(states) <= 3:
                state_label = ", ".join(STATE_NAMES.get(s, s.upper()) for s in states)
            else:
                state_label = f"{len(states)} states"

            return self.async_create_entry(
                title=f"ABC Emergency ({state_label})",
                data=self._data,
            )

        return self.async_show_form(
            step_id="zone_options",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ENABLE_ZONE_SENSORS, default=True): BooleanSelector(),
                    vol.Required(CONF_ENABLE_ZONE_GEO, default=True): BooleanSelector(),
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Get the options flow."""
        return ABCEmergencyOptionsFlow()


class ABCEmergencyOptionsFlow(OptionsFlow):
    """Options flow for ABC Emergency."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle options - show main menu."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["state_options", "zone_radius", "zone_options"],
        )

    async def async_step_state_options(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle state-wide options."""
        if user_input is not None:
            new_options = dict(self.config_entry.options)
            new_options[CONF_ENABLE_STATE_SENSORS] = user_input.get(CONF_ENABLE_STATE_SENSORS, True)
            new_options[CONF_ENABLE_STATE_GEO] = user_input.get(CONF_ENABLE_STATE_GEO, True)
            return self.async_create_entry(title="", data=new_options)

        current_sensors = self.config_entry.options.get(
            CONF_ENABLE_STATE_SENSORS,
            self.config_entry.data.get(CONF_ENABLE_STATE_SENSORS, True),
        )
        current_geo = self.config_entry.options.get(
            CONF_ENABLE_STATE_GEO,
            self.config_entry.data.get(CONF_ENABLE_STATE_GEO, True),
        )

        return self.async_show_form(
            step_id="state_options",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_ENABLE_STATE_SENSORS, default=current_sensors
                    ): BooleanSelector(),
                    vol.Required(CONF_ENABLE_STATE_GEO, default=current_geo): BooleanSelector(),
                }
            ),
        )

    async def async_step_zone_radius(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle per-incident-type radius options."""
        if user_input is not None:
            new_options = dict(self.config_entry.options)
            new_options[CONF_RADIUS_BUSHFIRE] = user_input.get(
                CONF_RADIUS_BUSHFIRE, DEFAULT_RADIUS_BUSHFIRE
            )
            new_options[CONF_RADIUS_EARTHQUAKE] = user_input.get(
                CONF_RADIUS_EARTHQUAKE, DEFAULT_RADIUS_EARTHQUAKE
            )
            new_options[CONF_RADIUS_STORM] = user_input.get(CONF_RADIUS_STORM, DEFAULT_RADIUS_STORM)
            new_options[CONF_RADIUS_FLOOD] = user_input.get(CONF_RADIUS_FLOOD, DEFAULT_RADIUS_FLOOD)
            new_options[CONF_RADIUS_FIRE] = user_input.get(CONF_RADIUS_FIRE, DEFAULT_RADIUS_FIRE)
            new_options[CONF_RADIUS_HEAT] = user_input.get(CONF_RADIUS_HEAT, DEFAULT_RADIUS_HEAT)
            new_options[CONF_RADIUS_OTHER] = user_input.get(CONF_RADIUS_OTHER, DEFAULT_RADIUS_OTHER)
            return self.async_create_entry(title="", data=new_options)

        def get_radius(key: str, default: int) -> int:
            value = self.config_entry.options.get(key, self.config_entry.data.get(key, default))
            return int(value) if value is not None else default

        radius_config = NumberSelectorConfig(
            min=1,
            max=500,
            step=1,
            unit_of_measurement="km",
            mode=NumberSelectorMode.BOX,
        )

        return self.async_show_form(
            step_id="zone_radius",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_RADIUS_BUSHFIRE,
                        default=get_radius(CONF_RADIUS_BUSHFIRE, DEFAULT_RADIUS_BUSHFIRE),
                    ): NumberSelector(radius_config),
                    vol.Required(
                        CONF_RADIUS_EARTHQUAKE,
                        default=get_radius(CONF_RADIUS_EARTHQUAKE, DEFAULT_RADIUS_EARTHQUAKE),
                    ): NumberSelector(radius_config),
                    vol.Required(
                        CONF_RADIUS_STORM,
                        default=get_radius(CONF_RADIUS_STORM, DEFAULT_RADIUS_STORM),
                    ): NumberSelector(radius_config),
                    vol.Required(
                        CONF_RADIUS_FLOOD,
                        default=get_radius(CONF_RADIUS_FLOOD, DEFAULT_RADIUS_FLOOD),
                    ): NumberSelector(radius_config),
                    vol.Required(
                        CONF_RADIUS_FIRE,
                        default=get_radius(CONF_RADIUS_FIRE, DEFAULT_RADIUS_FIRE),
                    ): NumberSelector(radius_config),
                    vol.Required(
                        CONF_RADIUS_HEAT,
                        default=get_radius(CONF_RADIUS_HEAT, DEFAULT_RADIUS_HEAT),
                    ): NumberSelector(radius_config),
                    vol.Required(
                        CONF_RADIUS_OTHER,
                        default=get_radius(CONF_RADIUS_OTHER, DEFAULT_RADIUS_OTHER),
                    ): NumberSelector(radius_config),
                }
            ),
        )

    async def async_step_zone_options(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle zone-filtered entity options."""
        if user_input is not None:
            new_options = dict(self.config_entry.options)
            new_options[CONF_ENABLE_ZONE_SENSORS] = user_input.get(CONF_ENABLE_ZONE_SENSORS, True)
            new_options[CONF_ENABLE_ZONE_GEO] = user_input.get(CONF_ENABLE_ZONE_GEO, True)
            return self.async_create_entry(title="", data=new_options)

        current_sensors = self.config_entry.options.get(
            CONF_ENABLE_ZONE_SENSORS,
            self.config_entry.data.get(CONF_ENABLE_ZONE_SENSORS, True),
        )
        current_geo = self.config_entry.options.get(
            CONF_ENABLE_ZONE_GEO,
            self.config_entry.data.get(CONF_ENABLE_ZONE_GEO, True),
        )

        return self.async_show_form(
            step_id="zone_options",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_ENABLE_ZONE_SENSORS, default=current_sensors
                    ): BooleanSelector(),
                    vol.Required(CONF_ENABLE_ZONE_GEO, default=current_geo): BooleanSelector(),
                }
            ),
        )
