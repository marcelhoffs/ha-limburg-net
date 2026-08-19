"""Config flow for the Limburg.net Afvalkalender integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from aiolimburgnet import (
    CityNotFoundError,
    LimburgNetClient,
    LimburgNetConnectionError,
    StreetNotFoundError,
)

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_CITY_ID,
    CONF_CITY_NAME,
    CONF_HOUSE_NUMBER,
    CONF_SCAN_INTERVAL_HOURS,
    CONF_STREET_ID,
    CONF_STREET_NAME,
    CONF_SUFFIX,
    DEFAULT_SCAN_INTERVAL_HOURS,
    DOMAIN,
    MAX_SCAN_INTERVAL_HOURS,
    MIN_SCAN_INTERVAL_HOURS,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CITY_NAME): str,
        vol.Required(CONF_STREET_NAME): str,
        vol.Required(CONF_HOUSE_NUMBER): str,
        vol.Optional(CONF_SUFFIX, default=""): str,
    }
)


class LimburgNetConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Limburg.net, driven entirely by the HA UI."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        errors: dict[str, str] = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            client = LimburgNetClient(session)

            city_name = user_input[CONF_CITY_NAME].strip()
            street_name = user_input[CONF_STREET_NAME].strip()
            house_number = user_input[CONF_HOUSE_NUMBER].strip()
            suffix = user_input[CONF_SUFFIX].strip()

            city = None
            street = None

            try:
                city = await client.find_city(city_name)
            except CityNotFoundError:
                errors[CONF_CITY_NAME] = "city_not_found"
            except LimburgNetConnectionError:
                errors["base"] = "cannot_connect"

            if city is not None and not errors:
                try:
                    street = await client.find_street(city, street_name)
                except StreetNotFoundError:
                    errors[CONF_STREET_NAME] = "street_not_found"
                except LimburgNetConnectionError:
                    errors["base"] = "cannot_connect"

            if city is not None and street is not None and not errors:
                unique_id = f"{city.nis_code}_{street.id}_{house_number}_{suffix}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                title = f"{street.name} {house_number}, {city.name}".strip()

                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_CITY_NAME: city.name,
                        CONF_CITY_ID: city.nis_code,
                        CONF_STREET_NAME: street.name,
                        CONF_STREET_ID: street.id,
                        CONF_HOUSE_NUMBER: house_number,
                        CONF_SUFFIX: suffix,
                    },
                )
        else:
            user_input = {}

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(STEP_USER_SCHEMA, user_input),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> "LimburgNetOptionsFlow":
        return LimburgNetOptionsFlow(config_entry)


class LimburgNetOptionsFlow(OptionsFlow):
    """Let the user tweak the polling interval after setup, via the UI."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current = self._config_entry.options.get(
            CONF_SCAN_INTERVAL_HOURS, DEFAULT_SCAN_INTERVAL_HOURS
        )
        schema = vol.Schema(
            {
                vol.Optional(CONF_SCAN_INTERVAL_HOURS, default=current): vol.All(
                    vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL_HOURS, max=MAX_SCAN_INTERVAL_HOURS)
                )
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
