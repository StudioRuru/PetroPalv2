import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

DEFAULT_LAT = float(os.getenv("DEFAULT_LAT", "43.6532"))
DEFAULT_LNG = float(os.getenv("DEFAULT_LNG", "-79.3832"))

SEARCH_RADIUS_KM = float(os.getenv("SEARCH_RADIUS_KM", "10"))

MAP_WIDTH = int(os.getenv("MAP_WIDTH", "600"))
MAP_HEIGHT = int(os.getenv("MAP_HEIGHT", "400"))
MAP_ZOOM = int(os.getenv("MAP_ZOOM", "16"))
MAX_MAP_STATIONS = int(os.getenv("MAX_MAP_STATIONS", "3"))

CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))

GAS_WIZARD_URL = "https://gaswizard.ca/gas-prices/toronto/"

STATIONS_FILE = os.path.join(os.path.dirname(__file__), "data", "petro_canada_stations.json")
DEVICE_LOCATIONS_FILE = os.path.join(os.path.dirname(__file__), "data", "device_locations.json")

FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
