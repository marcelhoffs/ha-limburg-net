# Limburg.net Afvalkalender for Home Assistant

![Limburg.net](custom_components/limburg_net/brand/logo.png)

A custom Home Assistant integration that creates sensors for your household
waste collection dates using the public [limburg.net](https://limburg.net)
calendar API. No YAML editing required — everything is configured through the
Home Assistant UI when you install and set up the integration.

This repo contains two packages:

- **`aiolimburgnet/`** — a standalone, HA-independent async Python library
  (`aiohttp`-based) that talks to the Limburg.net API, published on PyPI so
  it can be versioned and tested independently of the integration.
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
  dashboard card, without having to compare dates yourself. They roll over at
  midnight. Their state is display text in your Home Assistant language, so in
  automations test the `waste_types` attribute instead (e.g.
  `{{ state_attr('sensor.x_tomorrow', 'waste_types') | length > 0 }}`).
- A calendar entity with every collection as an all-day event, usable with
  calendar triggers.
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
   your address. A partial name is accepted only when it matches a single
   city/street; otherwise the form lists the candidates to choose from.

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
- Requires Home Assistant 2025.2 or newer.

## Development

Both test suites run in CI (`.github/workflows/tests.yml`). Locally:

```bash
# library (pins aiohttp<3.13 for aioresponses)
pip install -e "aiolimburgnet[test]" && pytest aiolimburgnet

# integration
pip install -r requirements_test.txt && pytest
```

Releasing a library change: bump `aiolimburgnet/pyproject.toml`, push a
`aiolimburgnet-vX.Y.Z` tag, and only then release an integration version whose
`manifest.json` requires it.
