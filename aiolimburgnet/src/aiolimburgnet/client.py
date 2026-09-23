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
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=30)


class LimburgNetClient:
    """Async client for the public, unauthenticated Limburg.net calendar API.

    The caller owns the aiohttp session (create it, pass it in, close it) so
    it can be shared with the rest of the caller's application.
    """

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def find_city(self, query: str) -> City:
        """Look up a city (gemeente) by name.

        The API does prefix matching, so this returns the exact
        (case-insensitive) match, or the only result if there is just one.
        Otherwise it raises CityNotFoundError, listing any candidates.
        """
        if not query.strip():
            raise CityNotFoundError(query)
        data = await self._get(f"{API_BASE_URL}/afval-kalender/gemeenten/search", {"query": query})
        try:
            match = _pick_match(data, query)
            if match is None:
                raise CityNotFoundError(query, [item["naam"] for item in data])
            return City(nis_code=str(match["nisCode"]), name=match["naam"])
        except (KeyError, TypeError) as err:
            raise LimburgNetConnectionError(f"Unexpected city search response: {err!r}") from err

    async def find_street(self, city: City, query: str) -> Street:
        """Look up a street within a city, with the same matching as find_city."""
        if not query.strip():
            raise StreetNotFoundError(query)
        url = f"{API_BASE_URL}/afval-kalender/gemeente/{city.nis_code}/straten/search"
        data = await self._get(url, {"query": query})
        try:
            match = _pick_match(data, query)
            if match is None:
                raise StreetNotFoundError(query, [item["naam"] for item in data])
            return Street(id=str(match["nummer"]), name=match["naam"])
        except (KeyError, TypeError) as err:
            raise LimburgNetConnectionError(f"Unexpected street search response: {err!r}") from err

    async def get_upcoming_events(
        self,
        city: City,
        street: Street,
        house_number: str,
        suffix: str = "",
        months_ahead: int = 3,
        from_date: date | None = None,
    ) -> list[CollectionEvent]:
        """Fetch collection events for the current and next few months.

        The upstream API only exposes one calendar month per request, so this
        walks forward `months_ahead` months, starting with the month of
        `from_date` (default: today in the system timezone).
        """
        events: list[CollectionEvent] = []
        start = from_date or date.today()
        year, month = start.year, start.month

        for _ in range(months_ahead):
            url = f"{API_BASE_URL}/kalender/{city.nis_code}/{year}-{month}"
            params = {
                "straatNummer": street.id,
                "huisNummer": house_number,
                "toevoeging": suffix or "",
            }
            month_data = await self._get(url, params)

            try:
                for item in month_data.get("events", []):
                    raw_date = item.get("date")
                    waste_type = item.get("title")
                    if not raw_date or not waste_type:
                        continue
                    events.append(CollectionEvent(waste_type=waste_type, date=_parse_date(raw_date)))
            except (AttributeError, TypeError, ValueError) as err:
                raise LimburgNetConnectionError(f"Unexpected calendar response: {err!r}") from err

            month += 1
            if month > 12:
                month = 1
                year += 1

        return events

    async def _get(self, url: str, params: dict[str, Any]) -> Any:
        _LOGGER.debug("GET %s params=%s", url, params)
        try:
            async with self._session.get(url, params=params, timeout=REQUEST_TIMEOUT) as response:
                response.raise_for_status()
                return await response.json()
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise LimburgNetConnectionError(str(err) or type(err).__name__) from err


def _pick_match(data: list[dict[str, Any]], query: str) -> dict[str, Any] | None:
    """Return the exact case-insensitive name match, else the sole result, else None."""
    wanted = query.strip().casefold()
    for item in data:
        if item["naam"].casefold() == wanted:
            return item
    return data[0] if len(data) == 1 else None


def _parse_date(raw: str) -> date:
    """Parse an ISO-8601 date/datetime string returned by the API into a date."""
    try:
        return datetime.fromisoformat(raw).date()
    except ValueError:
        return date.fromisoformat(raw[:10])
