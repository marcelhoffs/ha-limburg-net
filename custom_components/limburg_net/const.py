"""Constants for the Limburg.net Afvalkalender integration."""
DOMAIN = "limburg_net"

CONF_CITY_NAME = "city_name"
CONF_CITY_ID = "city_id"
CONF_STREET_NAME = "street_name"
CONF_STREET_ID = "street_id"
CONF_HOUSE_NUMBER = "house_number"
CONF_SUFFIX = "suffix"

CONF_SCAN_INTERVAL_HOURS = "scan_interval_hours"
DEFAULT_SCAN_INTERVAL_HOURS = 12
MIN_SCAN_INTERVAL_HOURS = 1
MAX_SCAN_INTERVAL_HOURS = 48

# Number of calendar months (including the current one) to fetch on every
# refresh. The upstream API only exposes data one month at a time.
MONTHS_AHEAD = 3

API_BASE_URL = "https://limburg.net/api-proxy/public"

# Best-effort icons for the waste types Limburg.net returns. Matched by
# keyword rather than exact title, since the exact wording of a waste type's
# title (e.g. "Glas" vs "Glas en flessen") can differ per municipality.
# Order matters: the first keyword found in the (lowercased) title wins.
WASTE_TYPE_ICON_KEYWORDS: list[tuple[str, str]] = [
    ("keukenafval", "mdi:faucet-variant"),
    ("huisvuil", "mdi:trash-can"),
    ("restafval", "mdi:trash-can"),
    ("gft", "mdi:leaf"),
    ("pmd", "mdi:recycle"),
    ("papier", "mdi:newspaper"),
    ("karton", "mdi:newspaper"),
    ("glas", "mdi:bottle-wine"),
    ("textiel", "mdi:tshirt-crew"),
    ("grofvuil", "mdi:sofa"),
    ("kerstboom", "mdi:pine-tree"),
    ("snoeiafval", "mdi:tree"),
    ("tuinafval", "mdi:tree"),
    ("groenafval", "mdi:tree"),
]
DEFAULT_ICON = "mdi:trash-can-outline"


def get_waste_type_icon(waste_type: str) -> str:
    """Best-effort icon lookup for a waste type title, by keyword."""
    title = waste_type.lower()
    for keyword, icon in WASTE_TYPE_ICON_KEYWORDS:
        if keyword in title:
            return icon
    return DEFAULT_ICON
