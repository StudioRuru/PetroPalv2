import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

DEFAULT_LAT = float(os.getenv("DEFAULT_LAT", "43.8563"))
DEFAULT_LNG = float(os.getenv("DEFAULT_LNG", "-79.3300"))

SEARCH_RADIUS_KM = float(os.getenv("SEARCH_RADIUS_KM", "10"))

MAP_WIDTH = int(os.getenv("MAP_WIDTH", "640"))
MAP_HEIGHT = int(os.getenv("MAP_HEIGHT", "640"))
MAP_ZOOM = int(os.getenv("MAP_ZOOM", "17"))
MAX_MAP_STATIONS = int(os.getenv("MAX_MAP_STATIONS", "3"))

CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))

# Timezone for determining "tomorrow". Gas Wizard updates on Eastern time,
# so users in other timezones may see a day-ahead prediction too early.
# Set to your local timezone (e.g., "America/Toronto", "America/Vancouver").
TIMEZONE = os.getenv("TIMEZONE", "America/Toronto")

GAS_WIZARD_URL = "https://gaswizard.ca/gas-prices/toronto/"

# Default fuel type — survives deploys via env var even without persistent storage.
DEFAULT_FUEL_TYPE = os.getenv("DEFAULT_FUEL_TYPE", "regular")

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

STATIONS_FILE = os.path.join(_DATA_DIR, "petro_canada_stations.json")
ESSO_STATIONS_FILE = os.path.join(_DATA_DIR, "esso_stations.json")
SHELL_STATIONS_FILE = os.path.join(_DATA_DIR, "shell_stations.json")

BRAND_STATIONS_FILES = {
    "petro-canada": STATIONS_FILE,
    "esso": ESSO_STATIONS_FILE,
    "shell": SHELL_STATIONS_FILE,
}

DEFAULT_BRAND = os.getenv("DEFAULT_BRAND", "petro-canada")

DEVICE_LOCATIONS_FILE = os.path.join(_DATA_DIR, "device_locations.json")
FUEL_PREFERENCES_FILE = os.path.join(_DATA_DIR, "fuel_preferences.json")
BRAND_PREFERENCES_FILE = os.path.join(_DATA_DIR, "brand_preferences.json")
STATION_INDEX_FILE = os.path.join(_DATA_DIR, "station_index.json")

FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
