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

# Persistent data directory. Set DATA_DIR to a Railway volume mount (e.g., "/data")
# so that device locations and fuel preferences survive deploys.
# Falls back to the local data/ directory (ephemeral on Railway).
DATA_DIR = os.getenv("DATA_DIR", os.path.join(os.path.dirname(__file__), "data"))

STATIONS_FILE = os.path.join(os.path.dirname(__file__), "data", "petro_canada_stations.json")
DEVICE_LOCATIONS_FILE = os.path.join(DATA_DIR, "device_locations.json")
FUEL_PREFERENCES_FILE = os.path.join(DATA_DIR, "fuel_preferences.json")

FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
