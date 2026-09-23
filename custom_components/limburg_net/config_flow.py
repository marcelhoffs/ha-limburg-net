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

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
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

# Cap the "did you mean" list so a short prefix doesn't flood the form.
MAX_SUGGESTIONS = 10

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
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        placeholders: dict[str, str] = {}

        if user_input is not None:
            client = LimburgNetClient(async_get_clientsession(self.hass))

            city_name = user_input[CONF_CITY_NAME].strip()
            street_name = user_input[CONF_STREET_NAME].strip()
            house_number = user_input[CONF_HOUSE_NUMBER].strip()
            suffix = user_input[CONF_SUFFIX].strip()

            try:
                city = await client.find_city(city_name)
                street = await client.find_street(city, street_name)
            except CityNotFoundError as err:
                errors[CONF_CITY_NAME] = _not_found_error("city", err.candidates, placeholders)
            except StreetNotFoundError as err:
                errors[CONF_STREET_NAME] = _not_found_error("street", err.candidates, placeholders)
            except LimburgNetConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001 - surface anything else as a form error
                _LOGGER.exception("Unexpected error while validating the address")
                errors["base"] = "unknown"
            else:
                if not house_number:
                    errors[CONF_HOUSE_NUMBER] = "house_number_required"
                else:
                    unique_id = f"{city.nis_code}_{street.id}_{house_number}_{suffix}"
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=f"{street.name} {house_number}, {city.name}",
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
            description_placeholders=placeholders,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> LimburgNetOptionsFlow:
        return LimburgNetOptionsFlow()


def _not_found_error(kind: str, candidates: list[str], placeholders: dict[str, str]) -> str:
    """Return the error key for a failed lookup, filling in suggestions if ambiguous."""
    if not candidates:
        return f"{kind}_not_found"
    placeholders["suggestions"] = ", ".join(candidates[:MAX_SUGGESTIONS])
    return f"{kind}_ambiguous"


class LimburgNetOptionsFlow(OptionsFlow):
    """Let the user tweak the polling interval after setup, via the UI."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current = self.config_entry.options.get(
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
