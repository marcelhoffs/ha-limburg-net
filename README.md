# Limburg.net Afvalkalender for Home Assistant

![Limburg.net](custom_components/limburg_net/brand/logo.png)

A custom Home Assistant integration that creates sensors for your household
waste collection dates using the public [limburg.net](https://limburg.net)
calendar API. No YAML editing required — everything is configured through the
Home Assistant UI when you install and set up the integration.

This repo contains two packages:

- **`aiolimburgnet/`** — a standalone, HA-independent async Python library
  (`aiohttp`-based) that talks to the Limburg.net API. Home Assistant core
  requires all API-specific code to live in a published third-party library
  rather than be embedded in the integration itself, so this is what the
  integration depends on.
- **`custom_components/limburg_net/`** — the Home Assistant integration
  itself: config flow, coordinator, sensors. It depends on `aiolimburgnet`
  via `manifest.json`'s `requirements`.

## Features

- Config flow (Settings → Devices & Services → Add Integration) asks for your
  city, street, house number and optional bus/suffix number, validates them
  against the Limburg.net API, and creates the entry.
- One sensor per waste type Limburg.net returns for your address (e.g.
  `Huisvuil`, `GFT`, `PMD`, `Papier`, `Glas`, `Textiel`, `Grofvuil`) — sensors
  are created automatically, you don't pick them manually.
- Each sensor's state is the next collection date (`device_class: date`); the
  `upcoming_dates` attribute lists all known future dates for that type.
- Two extra sensors, `Today` and `Tomorrow`, show which waste type(s) (if any)
  are collected on that day — handy for a "put the bins out" automation or
  dashboard card, without having to compare dates yourself.
- An Options flow lets you change the polling interval later, also from the UI.
- Data refreshes automatically (every 12 hours by default) via a
  `DataUpdateCoordinator`.

## Installation

### HACS (recommended)

1. In HACS, add this repository as a custom repository (category:
   Integration).
2. Install "Limburg.net Afvalkalender".
3. Restart Home Assistant.

### Manual

1. Copy `custom_components/limburg_net` into your Home Assistant
   `config/custom_components/` directory.
2. Restart Home Assistant.

## Setup (all via the UI)

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **Limburg.net Afvalkalender**.
3. Fill in your city, street name, house number, and suffix (if you have a
   bus number) exactly as they appear on the official Limburg.net calendar.
4. Submit — the integration looks up your city and street on Limburg.net and,
   once matched, creates one device with a sensor per waste type collected at
   your address.

To change how often it polls, open the integration's entry and click
**Configure**.

## Branding

`custom_components/limburg_net/brand/` ships the official Limburg.net logo as
`icon.png` / `icon@2x.png` (square) and `logo.png` / `logo@2x.png` (landscape),
generated from the source `logo.svg` at the repo root. Home Assistant 2026.3+
picks these up automatically from a custom integration's own `brand/` folder —
no submission to the `home-assistant/brands` repo needed — so the icon shows
up in Settings → Devices & Services and in the HACS store listing out of the
box.

## Notes

- The integration uses the same public, unauthenticated
  `limburg.net/api-proxy/public` endpoints that limburg.net's own website
  uses — no API key is required.
- `aiolimburgnet` is [published on PyPI](https://pypi.org/project/aiolimburgnet/)
  and installs automatically as a dependency when Home Assistant sets up
  this integration — no manual steps needed. New releases are published via
  the `publish-aiolimburgnet.yml` GitHub Actions workflow (PyPI trusted
  publishing), triggered by pushing a tag like `aiolimburgnet-v0.1.1`.
- The library's own test suite (`aiolimburgnet/tests/test_client.py`, using
  `aioresponses` to mock the HTTP API) was written but **not executed** —
  run `pip install -e ".[test]"` and `pytest` yourself before trusting it.
