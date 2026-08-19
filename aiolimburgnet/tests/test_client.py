"""Tests for aiolimburgnet.client, using aioresponses to mock the HTTP API."""
from __future__ import annotations

import re

import aiohttp
import pytest
from aioresponses import aioresponses

from aiolimburgnet import (
    City,
    CityNotFoundError,
    LimburgNetClient,
    LimburgNetConnectionError,
    Street,
    StreetNotFoundError,
)
from aiolimburgnet.client import API_BASE_URL


async def test_find_city_success() -> None:
    with aioresponses() as mocked:
        mocked.get(
            re.compile(rf"{re.escape(API_BASE_URL)}/afval-kalender/gemeenten/search.*"),
            payload=[{"nisCode": "71034", "naam": "Genk"}],
        )
        async with aiohttp.ClientSession() as session:
            city = await LimburgNetClient(session).find_city("Genk")

    assert city == City(nis_code="71034", name="Genk")


async def test_find_city_not_found() -> None:
    with aioresponses() as mocked:
        mocked.get(
            re.compile(rf"{re.escape(API_BASE_URL)}/afval-kalender/gemeenten/search.*"),
            payload=[],
        )
        async with aiohttp.ClientSession() as session:
            with pytest.raises(CityNotFoundError):
                await LimburgNetClient(session).find_city("Nowhereville")


async def test_find_street_success() -> None:
    city = City(nis_code="71034", name="Genk")
    with aioresponses() as mocked:
        mocked.get(
            re.compile(rf"{re.escape(API_BASE_URL)}/afval-kalender/gemeente/71034/straten/search.*"),
            payload=[{"nummer": "12345", "naam": "Stationsstraat"}],
        )
        async with aiohttp.ClientSession() as session:
            street = await LimburgNetClient(session).find_street(city, "Stationsstraat")

    assert street == Street(id="12345", name="Stationsstraat")


async def test_find_street_not_found() -> None:
    city = City(nis_code="71034", name="Genk")
    with aioresponses() as mocked:
        mocked.get(
            re.compile(rf"{re.escape(API_BASE_URL)}/afval-kalender/gemeente/71034/straten/search.*"),
            payload=[],
        )
        async with aiohttp.ClientSession() as session:
            with pytest.raises(StreetNotFoundError):
                await LimburgNetClient(session).find_street(city, "Nowhere")


async def test_get_upcoming_events_parses_dates_and_spans_months() -> None:
    city = City(nis_code="71034", name="Genk")
    street = Street(id="12345", name="Stationsstraat")

    with aioresponses() as mocked:
        mocked.get(
            re.compile(rf"{re.escape(API_BASE_URL)}/kalender/71034/\d{{4}}-\d{{1,2}}.*"),
            payload={
                "events": [
                    {"date": "2026-08-21T00:00:00+02:00", "title": "Huisvuil"},
                    {"date": "2026-08-25T00:00:00Z", "title": "PMD"},
                    {"date": None, "title": "Ignored - no date"},
                    {"date": "2026-08-30T00:00:00+02:00", "title": None},
                ]
            },
            repeat=True,
        )
        async with aiohttp.ClientSession() as session:
            events = await LimburgNetClient(session).get_upcoming_events(
                city, street, house_number="12", suffix="", months_ahead=3
            )

    # 2 valid events per month x 3 months; malformed entries are skipped.
    assert len(events) == 6
    assert events[0].waste_type == "Huisvuil"
    assert events[0].date.isoformat() == "2026-08-21"
    assert events[1].waste_type == "PMD"
    assert events[1].date.isoformat() == "2026-08-25"


async def test_connection_error_is_wrapped() -> None:
    with aioresponses() as mocked:
        mocked.get(
            re.compile(rf"{re.escape(API_BASE_URL)}/afval-kalender/gemeenten/search.*"),
            exception=aiohttp.ClientConnectionError("boom"),
        )
        async with aiohttp.ClientSession() as session:
            with pytest.raises(LimburgNetConnectionError):
                await LimburgNetClient(session).find_city("Genk")
