"""Config flow for ABC Emergency integration.

This module provides the configuration flow for setting up ABC Emergency
via the Home Assistant UI. Users can select their state, monitoring location,
and alert preferences.
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
    CONF_RADIUS,
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
    CONF_STATE,
    CONF_USE_HOME_LOCATION,
    DEFAULT_RADIUS_KM,
    DOMAIN,
    STATES,
)
from .exceptions import ABCEmergencyAPIError, ABCEmergencyConnectionError

_LOGGER = logging.getLogger(__name__)

# State names for display
STATE_NAMES: dict[str, str] = {
    "nsw": "New South Wales",
    "vic": "Victoria",
    "qld": "Queensland",
    "sa": "South Australia",
    "wa": "Western Australia",
    "tas": "Tasmania",
    "nt": "Northern Territory",
    "act": "Australian Capital Territory",
}


class ABCEmergencyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for ABC Emergency."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._state: str | None = None
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle the initial step - state selection."""
        errors: dict[str, str] = {}

        if user_input is not None:
            state = user_input[CONF_STATE]

            # Check if already configured
            await self.async_set_unique_id(f"abc_emergency_{state}")
            self._abort_if_unique_id_configured()

            # Test API connectivity
            try:
                session = async_get_clientsession(self.hass)
                client = ABCEmergencyClient(session)
                await client.async_get_emergencies_by_state(state)
            except ABCEmergencyConnectionError:
                errors["base"] = "cannot_connect"
            except ABCEmergencyAPIError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during API test")
                errors["base"] = "unknown"

            if not errors:
                self._state = state
                self._data[CONF_STATE] = state
                return await self.async_step_location()

        # Build state options
        state_options = [
            SelectOptionDict(value=code, label=STATE_NAMES.get(code, code.upper()))
            for code in STATES
        ]

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STATE): SelectSelector(
                        SelectSelectorConfig(
                            options=state_options,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_location(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle location configuration."""
        if user_input is not None:
            use_home = user_input.get(CONF_USE_HOME_LOCATION, True)

            if use_home:
                # Use Home Assistant's configured location
                self._data[CONF_LATITUDE] = self.hass.config.latitude
                self._data[CONF_LONGITUDE] = self.hass.config.longitude
            else:
                # Use custom location
                location = user_input.get("location", {})
                self._data[CONF_LATITUDE] = location.get("latitude", self.hass.config.latitude)
                self._data[CONF_LONGITUDE] = location.get("longitude", self.hass.config.longitude)

            self._data[CONF_RADIUS] = user_input.get(CONF_RADIUS, DEFAULT_RADIUS_KM)
            self._data[CONF_USE_HOME_LOCATION] = use_home

            state_name = STATE_NAMES.get(self._state or "", "Unknown")
            return self.async_create_entry(
                title=f"ABC Emergency ({state_name})",
                data=self._data,
            )

        return self.async_show_form(
            step_id="location",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USE_HOME_LOCATION, default=True): BooleanSelector(),
                    vol.Optional("location"): LocationSelector(
                        LocationSelectorConfig(radius=False, icon="mdi:map-marker")
                    ),
                    vol.Required(CONF_RADIUS, default=DEFAULT_RADIUS_KM): NumberSelector(
                        NumberSelectorConfig(
                            min=1,
                            max=500,
                            step=1,
                            unit_of_measurement="km",
                            mode=NumberSelectorMode.SLIDER,
                        )
                    ),
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
        """Handle options."""
        if user_input is not None:
            # Update the config entry with new options
            return self.async_create_entry(
                title="",
                data=user_input,
            )

        current_radius = self.config_entry.options.get(
            CONF_RADIUS,
            self.config_entry.data.get(CONF_RADIUS, DEFAULT_RADIUS_KM),
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_RADIUS, default=current_radius): NumberSelector(
                        NumberSelectorConfig(
                            min=1,
                            max=500,
                            step=1,
                            unit_of_measurement="km",
                            mode=NumberSelectorMode.SLIDER,
                        )
                    ),
                }
            ),
        )
