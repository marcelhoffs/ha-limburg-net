# aiolimburgnet

Async Python client for the public [limburg.net](https://limburg.net) waste
collection calendar API. It has no dependency on Home Assistant — it's a
plain `aiohttp`-based library, usable standalone or as the backing library
for the `limburg_net` Home Assistant integration.

## Installation

```bash
pip install aiolimburgnet
```

## Usage

```python
import asyncio

import aiohttp

from aiolimburgnet import LimburgNetClient


async def main() -> None:
    async with aiohttp.ClientSession() as session:
        client = LimburgNetClient(session)

        city = await client.find_city("Genk")
        street = await client.find_street(city, "Stationsstraat")

        events = await client.get_upcoming_events(
            city, street, house_number="12", suffix=""
        )

        for event in events:
            print(event.date, event.waste_type)


asyncio.run(main())
```

## API

- `LimburgNetClient(session: aiohttp.ClientSession)`
- `await client.find_city(query: str) -> City`
- `await client.find_street(city: City, query: str) -> Street`
- `await client.get_upcoming_events(city, street, house_number, suffix="", months_ahead=3, from_date=None) -> list[CollectionEvent]`
  (`from_date` picks the first month; defaults to today in the system timezone)

The search API matches by prefix. `find_city` / `find_street` return the exact
(case-insensitive) match, or the only result if there is just one; otherwise
they raise, with the matching names in the exception's `candidates` list.

`City`, `Street`, and `CollectionEvent` are frozen dataclasses. All lookup
failures raise a subclass of `LimburgNetError`:

- `CityNotFoundError` — no single city matched the query (`candidates` lists ambiguous matches)
- `StreetNotFoundError` — no single street matched the query within that city (same `candidates`)
- `LimburgNetConnectionError` — the API could not be reached, timed out (30 s), or returned an error or unexpected data

## Development

```bash
pip install -e ".[test]"
pytest
```
