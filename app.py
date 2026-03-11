"""PetroPal - Flask API for Petro-Canada station finder and gas price widget."""

import json
import math
from datetime import datetime, timezone

import requests as http_requests
from flask import Flask, Response, jsonify, redirect, request
from flask_cors import CORS

import config
from scraper.gasbuddy import get_tomorrow_gas_price

app = Flask(__name__)
CORS(app)

# In-memory station cache
_stations = None

# Device location store: { device_id: { lat, lng, updated_at } }
# Persisted to disk so locations survive server restarts.
_device_locations = {}


def _load_device_locations():
    """Load saved device locations from disk into memory."""
    global _device_locations
    try:
        with open(config.DEVICE_LOCATIONS_FILE, "r") as f:
            _device_locations = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        _device_locations = {}


def _save_device_locations():
    """Persist device locations to disk."""
    with open(config.DEVICE_LOCATIONS_FILE, "w") as f:
        json.dump(_device_locations, f, indent=2)


# Load any previously saved locations on startup
_load_device_locations()


def _load_stations():
    """Load stations from the static JSON file (cached in memory)."""
    global _stations
    if _stations is None:
        with open(config.STATIONS_FILE, "r") as f:
            _stations = json.load(f)
    return _stations


def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great-circle distance between two points in km."""
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def _get_nearby_stations(lat, lng, radius_km):
    """Return stations within radius_km of (lat, lng), sorted by distance."""
    stations = _load_stations()
    nearby = []
    for s in stations:
        dist = haversine(lat, lng, s["lat"], s["lng"])
        if dist <= radius_km:
            nearby.append(
                {
                    "id": s["id"],
                    "name": s["name"],
                    "lat": s["lat"],
                    "lng": s["lng"],
                    "address": s["address"],
                    "distance_km": round(dist, 1),
                    "nav_url": (
                        f"https://www.google.com/maps/dir/?api=1"
                        f"&destination={s['lat']},{s['lng']}"
                    ),
                }
            )
    nearby.sort(key=lambda x: x["distance_km"])
    return nearby


def _build_static_map_url(lat, lng, stations):
    """Build a Google Static Maps URL with station markers."""
    base = "https://maps.googleapis.com/maps/api/staticmap"
    params = (
        f"?center={lat},{lng}"
        f"&zoom={config.MAP_ZOOM}"
        f"&size={config.MAP_WIDTH}x{config.MAP_HEIGHT}"
        f"&maptype=roadmap"
        f"&markers=color:blue%7Clabel:U%7C{lat},{lng}"
    )

    # Add station markers (limit to 50 to stay within URL length)
    if stations:
        marker_locations = "%7C".join(
            f"{s['lat']},{s['lng']}" for s in stations[:50]
        )
        params += f"&markers=color:red%7C{marker_locations}"

    if not config.GOOGLE_MAPS_API_KEY:
        return None
    params += f"&key={config.GOOGLE_MAPS_API_KEY}"
    return base + params


def _trend_color(trend):
    """Return an iOS-style color hex for the price trend."""
    colors = {
        "up": "#FF3B30",      # Red (price increase = bad)
        "down": "#34C759",    # Green (price decrease = good)
        "stable": "#8E8E93",  # Gray
    }
    return colors.get(trend, "#8E8E93")


def _resolve_location():
    """Resolve lat/lng from query params, device_id lookup, or defaults."""
    device_id = request.args.get("device_id") or request.args.get("device")
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)

    # If lat/lng explicitly provided, use them
    if lat is not None and lng is not None:
        return lat, lng

    # If device_id provided, look up saved location
    if device_id and device_id in _device_locations:
        loc = _device_locations[device_id]
        return loc["lat"], loc["lng"]

    # Check the "default" device (iOS Shortcut sends without device_id)
    if "default" in _device_locations:
        loc = _device_locations["default"]
        return loc["lat"], loc["lng"]

    # Fall back to config defaults
    return config.DEFAULT_LAT, config.DEFAULT_LNG


@app.route("/api/update-location", methods=["POST", "GET"])
def api_update_location():
    """Save device GPS coordinates on the server.

    The iOS Shortcut calls this periodically to keep location fresh.
    Accepts GET or POST so it works easily with Shortcuts' "Get Contents of URL".

    Parameters:
        device_id: A string identifier for the device (e.g., "my-iphone")
        lat: Latitude
        lng: Longitude
    """
    device_id = (
        request.args.get("device_id")
        or request.args.get("device")
        or (request.get_json(silent=True) or {}).get("device_id")
        or "default"
    )
    lat = (
        request.args.get("lat", type=float)
        or (request.get_json(silent=True) or {}).get("lat")
    )
    lng = (
        request.args.get("lng", type=float)
        or (request.get_json(silent=True) or {}).get("lng")
    )

    if lat is None or lng is None:
        return jsonify({"error": "lat and lng are required"}), 400

    _device_locations[device_id] = {
        "lat": float(lat),
        "lng": float(lng),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_device_locations()

    return jsonify({
        "status": "ok",
        "device_id": device_id,
        "location": _device_locations[device_id],
    })


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/stations")
def api_stations():
    lat, lng = _resolve_location()
    radius = request.args.get("radius", config.SEARCH_RADIUS_KM, type=float)

    nearby = _get_nearby_stations(lat, lng, radius)
    return jsonify(
        {
            "stations": nearby,
            "count": len(nearby),
            "center": {"lat": lat, "lng": lng},
            "radius_km": radius,
        }
    )


@app.route("/api/map")
def api_map():
    lat, lng = _resolve_location()
    fmt = request.args.get("format", "redirect")

    nearby = _get_nearby_stations(lat, lng, config.SEARCH_RADIUS_KM)
    top_stations = nearby[: config.MAX_MAP_STATIONS]
    map_url = _build_static_map_url(lat, lng, top_stations)

    if map_url is None:
        return jsonify({"error": "GOOGLE_MAPS_API_KEY is not configured"}), 500

    if fmt == "json":
        return jsonify({"map_url": map_url})
    return redirect(map_url, code=302)


@app.route("/api/map-image")
def api_map_image():
    """Proxy the Google Static Map image and serve PNG bytes directly.

    This avoids CORS and redirect issues when loading the map in Widgy's
    JavaScript image layer.
    """
    lat, lng = _resolve_location()

    nearby = _get_nearby_stations(lat, lng, config.SEARCH_RADIUS_KM)
    top_stations = nearby[: config.MAX_MAP_STATIONS]
    map_url = _build_static_map_url(lat, lng, top_stations)

    if map_url is None:
        return jsonify({"error": "GOOGLE_MAPS_API_KEY is not configured"}), 500

    resp = http_requests.get(map_url, timeout=10)
    if resp.status_code != 200:
        return jsonify({"error": "Failed to fetch map image"}), 502

    return Response(
        resp.content,
        content_type=resp.headers.get("Content-Type", "image/png"),
        headers={"Cache-Control": "public, max-age=300"},
    )


@app.route("/api/gas-price")
def api_gas_price():
    data = get_tomorrow_gas_price()
    trend = data.get("trend", "unknown")
    return jsonify(
        {
            "price": data.get("price"),
            "unit": data.get("unit", "cents/litre"),
            "change": data.get("change"),
            "trend": trend,
            "color": _trend_color(trend),
            "date": data.get("date"),
            "source": data.get("source", "gaswizard.ca"),
            "stale": data.get("stale", False),
            "error": data.get("error"),
        }
    )


@app.route("/api/widget-data")
def api_widget_data():
    lat, lng = _resolve_location()

    # Stations
    nearby = _get_nearby_stations(lat, lng, config.SEARCH_RADIUS_KM)
    top_stations = nearby[: config.MAX_MAP_STATIONS]
    map_url = _build_static_map_url(lat, lng, top_stations)

    # Build list of nearest stations for display
    nearest_list = []
    for n in top_stations:
        nearest_list.append(
            {
                "name": n["name"],
                "distance_km": n["distance_km"],
                "display": f"{n['name']} ({n['distance_km']} km)",
                "nav_url": n["nav_url"],
            }
        )

    # Gas price
    price_data = get_tomorrow_gas_price()
    trend = price_data.get("trend", "unknown")
    price = price_data.get("price")
    change = price_data.get("change")

    display = f"{price} c/L" if price else "N/A"
    if change is not None:
        sign = "+" if change > 0 else ""
        change_display = f"{sign}{change}c"
    else:
        change_display = "N/A"

    # Format date for display
    date_raw = price_data.get("date")
    if date_raw and isinstance(date_raw, str) and len(date_raw) > 5:
        # Try to extract short date like "Mar 11"
        parts = date_raw.split()
        date_short = " ".join(parts[-2:]) if len(parts) >= 2 else date_raw
    else:
        date_short = date_raw

    return jsonify(
        {
            "map_url": map_url,
            "gas_price": {
                "price": str(price) if price else None,
                "display": display,
                "change": str(change) if change is not None else None,
                "change_display": change_display,
                "trend": trend,
                "color": _trend_color(trend),
                "date": date_short,
            },
            "stations": {
                "count": len(nearby),
                "nearest": nearest_list[0]["display"] if nearest_list else None,
                "nav_url": nearest_list[0]["nav_url"] if nearest_list else None,
                "top": nearest_list,
            },
            "meta": {
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "location": {"lat": lat, "lng": lng},
            },
        }
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG,
    )
