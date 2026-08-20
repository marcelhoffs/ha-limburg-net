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

# Best-effort icon and translation_key for the waste types Limburg.net
# returns. Matched by keyword rather than exact title, since the exact
# wording of a waste type's title (e.g. "Glas" vs "Glas en flessen") can
# differ per municipality. Order matters: the first keyword found in the
# (lowercased) title wins.
#
# The translation_key drives the entity's localized display name (see
# strings.json / translations/*.json); when a title matches no keyword,
# callers fall back to displaying the raw (Dutch) title as-is.
WASTE_TYPE_KEYWORDS: list[tuple[str, str, str]] = [
    ("keukenafval", "mdi:faucet-variant", "kitchen_waste"),
    ("huisvuil", "mdi:trash-can", "residual_waste"),
    ("restafval", "mdi:trash-can", "residual_waste"),
    ("gft", "mdi:leaf", "gft"),
    ("pmd", "mdi:recycle", "pmd"),
    ("papier", "mdi:newspaper", "paper_cardboard"),
    ("karton", "mdi:newspaper", "paper_cardboard"),
    ("glas", "mdi:bottle-wine", "glass"),
    ("textiel", "mdi:tshirt-crew", "textile"),
    ("grofvuil", "mdi:sofa", "bulky_waste"),
    ("kerstboom", "mdi:pine-tree", "christmas_tree"),
    ("snoeiafval", "mdi:tree", "garden_waste"),
    ("tuinafval", "mdi:tree", "garden_waste"),
    ("groenafval", "mdi:tree", "garden_waste"),
]
DEFAULT_ICON = "mdi:trash-can-outline"


def get_waste_type_icon(waste_type: str) -> str:
    """Best-effort icon lookup for a waste type title, by keyword."""
    title = waste_type.lower()
    for keyword, icon, _ in WASTE_TYPE_KEYWORDS:
        if keyword in title:
            return icon
    return DEFAULT_ICON


def get_waste_type_translation_key(waste_type: str) -> str | None:
    """Best-effort translation_key lookup for a waste type title, by keyword.

    Returns None when the title matches no known waste type, in which case
    callers should fall back to displaying the raw title as-is.
    """
    title = waste_type.lower()
    for keyword, _, translation_key in WASTE_TYPE_KEYWORDS:
        if keyword in title:
            return translation_key
    return None


WASTE_TYPE_NAMES: dict[str, dict[str, str]] = {
    "kitchen_waste": {"en": "Kitchen waste", "nl": "Keukenafval"},
    "residual_waste": {"en": "Residual waste", "nl": "Huisvuil"},
    "gft": {"en": "GFT (organic waste)", "nl": "GFT"},
    "pmd": {"en": "PMD (plastic, metal & drink cartons)", "nl": "PMD"},
    "paper_cardboard": {"en": "Paper & cardboard", "nl": "Papier & karton"},
    "glass": {"en": "Glass", "nl": "Glas"},
    "textile": {"en": "Textile", "nl": "Textiel"},
    "bulky_waste": {"en": "Bulky waste", "nl": "Grofvuil"},
    "christmas_tree": {"en": "Christmas tree", "nl": "Kerstboom"},
    "garden_waste": {"en": "Garden waste", "nl": "Tuin- en snoeiafval"},
}


def get_waste_type_name(waste_type: str, language: str) -> str:
    """Localized display name for a waste type title.

    Falls back to the raw (Dutch) title when it matches no known waste type,
    or when no translation exists for the requested language.
    """
    translation_key = get_waste_type_translation_key(waste_type)
    if translation_key is None:
        return waste_type
    names = WASTE_TYPE_NAMES.get(translation_key, {})
    lang = language.split("-")[0].lower()
    return names.get(lang, names.get("en", waste_type))


NO_COLLECTION_TEXT = {
    "nl": "Geen afvalophaling",
}
DEFAULT_NO_COLLECTION_TEXT = "No waste collection"


def get_no_collection_text(language: str) -> str:
    """Localized placeholder for the today/tomorrow sensors when nothing is collected."""
    return NO_COLLECTION_TEXT.get(language.split("-")[0].lower(), DEFAULT_NO_COLLECTION_TEXT)
