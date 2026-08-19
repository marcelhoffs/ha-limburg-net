"""Tests for the Limburg.net config and options flows."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

from aiolimburgnet import (
    City,
    CityNotFoundError,
    LimburgNetConnectionError,
    Street,
    StreetNotFoundError,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.limburg_net.const import (
    CONF_CITY_ID,
    CONF_CITY_NAME,
    CONF_HOUSE_NUMBER,
    CONF_SCAN_INTERVAL_HOURS,
    CONF_STREET_ID,
    CONF_STREET_NAME,
    CONF_SUFFIX,
    DEFAULT_SCAN_INTERVAL_HOURS,
    DOMAIN,
)

MOCK_CITY = City(nis_code="71034", name="Genk")
MOCK_STREET = Street(id="12345", name="Stationsstraat")

USER_INPUT = {
    CONF_CITY_NAME: "Genk",
    CONF_STREET_NAME: "Stationsstraat",
    CONF_HOUSE_NUMBER: "12",
    CONF_SUFFIX: "",
}

ENTRY_DATA = {
    CONF_CITY_NAME: MOCK_CITY.name,
    CONF_CITY_ID: MOCK_CITY.nis_code,
    CONF_STREET_NAME: MOCK_STREET.name,
    CONF_STREET_ID: MOCK_STREET.id,
    CONF_HOUSE_NUMBER: "12",
    CONF_SUFFIX: "",
}


def _patch_client(*, find_city=None, find_street=None):
    """Patch the LimburgNetClient used by the config flow with an async mock."""
    client = AsyncMock()
    client.find_city = find_city or AsyncMock(return_value=MOCK_CITY)
    client.find_street = find_street or AsyncMock(return_value=MOCK_STREET)
    return patch(
        "custom_components.limburg_net.config_flow.LimburgNetClient",
        return_value=client,
    )


async def test_form_shown_with_no_input(hass: HomeAssistant) -> None:
    """The user step with no input just (re)shows the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


async def test_form_success_creates_entry(hass: HomeAssistant) -> None:
    """A valid address creates a config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with (
        _patch_client(),
        patch(
            "custom_components.limburg_net.async_setup_entry", return_value=True
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Stationsstraat 12, Genk"
    assert result["data"] == ENTRY_DATA


async def test_form_city_not_found(hass: HomeAssistant) -> None:
    """An unknown city surfaces a field-level error and redisplays the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with _patch_client(
        find_city=AsyncMock(side_effect=CityNotFoundError("Nowhereville"))
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {CONF_CITY_NAME: "city_not_found"}


async def test_form_city_lookup_cannot_connect(hass: HomeAssistant) -> None:
    """A connection error while looking up the city surfaces a base error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with _patch_client(
        find_city=AsyncMock(side_effect=LimburgNetConnectionError("boom"))
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_form_street_not_found(hass: HomeAssistant) -> None:
    """An unknown street surfaces a field-level error and redisplays the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with _patch_client(
        find_street=AsyncMock(side_effect=StreetNotFoundError("Nowhere"))
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {CONF_STREET_NAME: "street_not_found"}


async def test_form_street_lookup_cannot_connect(hass: HomeAssistant) -> None:
    """A connection error while looking up the street surfaces a base error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with _patch_client(
        find_street=AsyncMock(side_effect=LimburgNetConnectionError("boom"))
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_form_already_configured_aborts(hass: HomeAssistant) -> None:
    """The same address cannot be configured twice."""
    existing_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=f"{MOCK_CITY.nis_code}_{MOCK_STREET.id}_12_",
        data=ENTRY_DATA,
    )
    existing_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with _patch_client():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_options_flow_shows_current_value(hass: HomeAssistant) -> None:
    """The options step pre-fills the currently configured scan interval."""
    entry = MockConfigEntry(domain=DOMAIN, data=ENTRY_DATA, options={})
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    schema_defaults = {
        key.schema: key.default() for key in result["data_schema"].schema
    }
    assert schema_defaults[CONF_SCAN_INTERVAL_HOURS] == DEFAULT_SCAN_INTERVAL_HOURS


async def test_options_flow_updates_scan_interval(hass: HomeAssistant) -> None:
    """Submitting the options form updates the polling interval."""
    entry = MockConfigEntry(domain=DOMAIN, data=ENTRY_DATA, options={})
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_SCAN_INTERVAL_HOURS: 6}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_SCAN_INTERVAL_HOURS: 6}
