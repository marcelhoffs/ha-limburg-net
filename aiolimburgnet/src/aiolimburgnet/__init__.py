"""aiolimburgnet: async Python client for the public Limburg.net waste collection calendar API."""
from importlib.metadata import version

from .client import LimburgNetClient
from .exceptions import (
    CityNotFoundError,
    LimburgNetConnectionError,
    LimburgNetError,
    StreetNotFoundError,
)
from .models import City, CollectionEvent, Street

__version__ = version("aiolimburgnet")

__all__ = [
    "City",
    "CityNotFoundError",
    "CollectionEvent",
    "LimburgNetClient",
    "LimburgNetConnectionError",
    "LimburgNetError",
    "Street",
    "StreetNotFoundError",
    "__version__",
]
