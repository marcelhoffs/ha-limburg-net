"""Tests for aiolimburgnet.client, using aioresponses to mock the HTTP API."""
from __future__ import annotations

import re
from datetime import date

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


CITY_SEARCH = re.compile(rf"{re.escape(API_BASE_URL)}/afval-kalender/gemeenten/search.*")
STREET_SEARCH = re.compile(rf"{re.escape(API_BASE_URL)}/afval-kalender/gemeente/71016/straten/search.*")
GENK = City(nis_code="71016", name="Genk")


async def test_find_street_prefers_exact_match_over_first_result() -> None:
    with aioresponses() as mocked:
        mocked.get(
            STREET_SEARCH,
            payload=[
                {"nummer": "1", "naam": "Kerkeweg"},
                {"nummer": "2", "naam": "Kerkstraat"},
            ],
        )
        async with aiohttp.ClientSession() as session:
            street = await LimburgNetClient(session).find_street(GENK, "  kerkstraat ")

    assert street == Street(id="2", name="Kerkstraat")


async def test_find_street_accepts_single_prefix_result() -> None:
    with aioresponses() as mocked:
        mocked.get(STREET_SEARCH, payload=[{"nummer": "2", "naam": "Kerkstraat"}])
        async with aiohttp.ClientSession() as session:
            street = await LimburgNetClient(session).find_street(GENK, "Kerkstr")

    assert street.name == "Kerkstraat"


async def test_find_street_ambiguous_prefix_lists_candidates() -> None:
    with aioresponses() as mocked:
        mocked.get(
            STREET_SEARCH,
            payload=[
                {"nummer": "1", "naam": "Kerkeweg"},
                {"nummer": "2", "naam": "Kerkstraat"},
            ],
        )
        async with aiohttp.ClientSession() as session:
            with pytest.raises(StreetNotFoundError) as exc_info:
                await LimburgNetClient(session).find_street(GENK, "Kerk")

    assert exc_info.value.candidates == ["Kerkeweg", "Kerkstraat"]


async def test_find_city_ambiguous_prefix_lists_candidates() -> None:
    with aioresponses() as mocked:
        mocked.get(
            CITY_SEARCH,
            payload=[{"nisCode": "71020", "naam": "Halen"}, {"nisCode": "71072", "naam": "Hasselt"}],
        )
        async with aiohttp.ClientSession() as session:
            with pytest.raises(CityNotFoundError) as exc_info:
                await LimburgNetClient(session).find_city("Ha")

    assert exc_info.value.candidates == ["Halen", "Hasselt"]


async def test_blank_query_raises_not_found_without_request() -> None:
    with aioresponses():  # any request would fail with a connection error
        async with aiohttp.ClientSession() as session:
            client = LimburgNetClient(session)
            with pytest.raises(CityNotFoundError):
                await client.find_city("   ")
            with pytest.raises(StreetNotFoundError):
                await client.find_street(GENK, "")


async def test_timeout_is_wrapped() -> None:
    with aioresponses() as mocked:
        mocked.get(CITY_SEARCH, exception=TimeoutError())
        async with aiohttp.ClientSession() as session:
            with pytest.raises(LimburgNetConnectionError):
                await LimburgNetClient(session).find_city("Genk")


@pytest.mark.parametrize(
    "payload",
    [[{"unexpected": "shape"}], [{"nisCode": "71016", "naam": None}], {"not": "a list"}],
)
async def test_malformed_search_response_is_wrapped(payload) -> None:
    with aioresponses() as mocked:
        mocked.get(CITY_SEARCH, payload=payload)
        async with aiohttp.ClientSession() as session:
            with pytest.raises(LimburgNetConnectionError):
                await LimburgNetClient(session).find_city("Genk")


async def test_malformed_calendar_response_is_wrapped() -> None:
    street = Street(id="12345", name="Stationsstraat")
    with aioresponses() as mocked:
        mocked.get(re.compile(rf"{re.escape(API_BASE_URL)}/kalender/.*"), payload=["not", "a", "dict"])
        async with aiohttp.ClientSession() as session:
            with pytest.raises(LimburgNetConnectionError):
                await LimburgNetClient(session).get_upcoming_events(GENK, street, "12")


async def test_get_upcoming_events_walks_months_from_given_date_across_year_end() -> None:
    street = Street(id="12345", name="Stationsstraat")
    with aioresponses() as mocked:
        for month, day in (("2026-12", "2026-12-05"), ("2027-1", "2027-01-05"), ("2027-2", "2027-02-05")):
            mocked.get(
                re.compile(rf"{re.escape(API_BASE_URL)}/kalender/71016/{month}\?.*"),
                payload={"events": [{"date": f"{day}T21:40:45+01:00", "title": "PMD"}]},
            )
        async with aiohttp.ClientSession() as session:
            events = await LimburgNetClient(session).get_upcoming_events(
                GENK, street, "12", from_date=date(2026, 12, 31)
            )

    assert [e.date for e in events] == [date(2026, 12, 5), date(2027, 1, 5), date(2027, 2, 5)]
