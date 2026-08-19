"""Async client for the public Limburg.net waste collection calendar API."""
from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any

import aiohttp

from .exceptions import CityNotFoundError, LimburgNetConnectionError, StreetNotFoundError
from .models import City, CollectionEvent, Street

_LOGGER = logging.getLogger(__name__)

API_BASE_URL = "https://limburg.net/api-proxy/public"


class LimburgNetClient:
    """Async client for the public, unauthenticated Limburg.net calendar API.

    The caller owns the aiohttp session (create it, pass it in, close it) so
    it can be shared with the rest of the caller's application.
    """

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def find_city(self, query: str) -> City:
        """Look up a city (gemeente) by name and return the best match."""
        data = await self._get(f"{API_BASE_URL}/afval-kalender/gemeenten/search", {"query": query})
        if not data:
            raise CityNotFoundError(query)
        match = data[0]
        return City(nis_code=str(match["nisCode"]), name=match["naam"])

    async def find_street(self, city: City, query: str) -> Street:
        """Look up a street within a city and return the best match."""
        url = f"{API_BASE_URL}/afval-kalender/gemeente/{city.nis_code}/straten/search"
        data = await self._get(url, {"query": query})
        if not data:
            raise StreetNotFoundError(query)
        match = data[0]
        return Street(id=str(match["nummer"]), name=match["naam"])

    async def get_upcoming_events(
        self,
        city: City,
        street: Street,
        house_number: str,
        suffix: str = "",
        months_ahead: int = 3,
    ) -> list[CollectionEvent]:
        """Fetch collection events for the current and next few months.

        The upstream API only exposes one calendar month per request, so this
        walks forward `months_ahead` months (including the current one).
        """
        events: list[CollectionEvent] = []
        today = date.today()
        year, month = today.year, today.month

        for _ in range(months_ahead):
            url = f"{API_BASE_URL}/kalender/{city.nis_code}/{year}-{month}"
            params = {
                "straatNummer": street.id,
                "huisNummer": house_number,
                "toevoeging": suffix or "",
            }
            month_data = await self._get(url, params)

            for item in month_data.get("events", []):
                raw_date = item.get("date")
                waste_type = item.get("title")
                if not raw_date or not waste_type:
                    continue
                events.append(CollectionEvent(waste_type=waste_type, date=_parse_date(raw_date)))

            month += 1
            if month > 12:
                month = 1
                year += 1

        return events

    async def _get(self, url: str, params: dict[str, Any]) -> Any:
        _LOGGER.debug("GET %s params=%s", url, params)
        try:
            async with self._session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as err:
            raise LimburgNetConnectionError(str(err)) from err


def _parse_date(raw: str) -> date:
    """Parse an ISO-8601 date/datetime string returned by the API into a date."""
    text = f"{raw[:-1]}+00:00" if raw.endswith("Z") else raw
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        return date.fromisoformat(text[:10])
