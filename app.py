"""PetroPal - Flask API for Petro-Canada station finder and gas price widget."""

import json
import logging
import math
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests as http_requests
from flask import Flask, Response, jsonify, redirect, request
from flask_cors import CORS

import config
from scraper.gasbuddy import clear_cache as clear_price_cache, debug_scrape, get_tomorrow_gas_price

log = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# In-memory station cache
_stations = None

# Cache for reverse-geocoded intersection names: { "lat,lng": "Street1 & Street2" }
_intersection_cache = {}

# Device location store: { device_id: { lat, lng, updated_at } }
# Persisted to disk so locations survive server restarts.
_device_locations = {}

# Fuel type preference per device: { device_id: "regular" | "premium" }
# Persisted to disk so preferences survive server restarts.
_fuel_preferences = {}
_FUEL_TYPES = ["regular", "premium"]
_FUEL_LABELS = {"regular": "87", "premium": "91"}


def _load_fuel_preferences():
    """Load saved fuel preferences from disk into memory."""
    global _fuel_preferences
    try:
        with open(config.FUEL_PREFERENCES_FILE, "r") as f:
            _fuel_preferences = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        _fuel_preferences = {}


def _save_fuel_preferences():
    """Persist fuel preferences to disk."""
    with open(config.FUEL_PREFERENCES_FILE, "w") as f:
        json.dump(_fuel_preferences, f, indent=2)


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


# Ensure persistent data directory exists (for Railway volume mounts)
os.makedirs(config.DATA_DIR, exist_ok=True)

# Load any previously saved data on startup
_load_device_locations()
_load_fuel_preferences()

# Clear gas price cache on startup so we always scrape fresh after deploy.
# This ensures code changes (e.g., regex fixes) take effect immediately.
clear_price_cache()


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


def _get_intersection(lat, lng):
    """Reverse-geocode a lat/lng to a two-street intersection label.

    Calls the Geocoding API without result_type filters and extracts
    the two nearest road/route names from the address components,
    returning them as 'Street A & Street B'.
    Results are cached in memory since station locations don't change.
    """
    cache_key = f"{lat},{lng}"
    if cache_key in _intersection_cache:
        return _intersection_cache[cache_key]

    if not config.GOOGLE_MAPS_API_KEY:
        return None

    try:
        resp = http_requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={
                "latlng": cache_key,
                "key": config.GOOGLE_MAPS_API_KEY,
            },
            timeout=5,
        )
        data = resp.json()
        status = data.get("status", "")
        if status not in ("OK", "ZERO_RESULTS"):
            log.warning("Geocoding for %s: %s", cache_key, status)

        if status == "OK" and data.get("results"):
            # Collect unique route names across all results
            routes = []
            seen = set()
            for result in data["results"]:
                for comp in result.get("address_components", []):
                    if "route" in comp.get("types", []):
                        name = comp.get("short_name", comp.get("long_name", ""))
                        if name and name not in seen:
                            seen.add(name)
                            routes.append(name)
                    if len(routes) >= 2:
                        break
                if len(routes) >= 2:
                    break

            if len(routes) >= 2:
                label = f"{routes[0]} & {routes[1]}"
            elif routes:
                label = routes[0]
            else:
                # Fallback: first line of formatted address
                full = data["results"][0].get("formatted_address", "")
                label = full.split(",")[0] if full else None

            if label:
                _intersection_cache[cache_key] = label
                return label
    except Exception as e:
        log.warning("Geocoding error for %s: %s", cache_key, e)

    _intersection_cache[cache_key] = None
    return None


def _street_from_address(address):
    """Extract just the street name from an address string.

    e.g. '1525, Markham Road, Scarborough, ON' -> 'Markham Road'
    """
    if not address or len(address) <= 3:
        return None
    parts = [p.strip() for p in address.split(",")]
    # parts[0] is usually the street number, parts[1] is the street name
    if len(parts) >= 2 and parts[1].strip():
        return parts[1].strip()
    return parts[0].strip()


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
    """Build a Google Static Maps URL with station markers in dark mode."""
    base = "https://maps.googleapis.com/maps/api/staticmap"
    params = (
        f"?center={lat},{lng}"
        f"&zoom={config.MAP_ZOOM}"
        f"&size={config.MAP_WIDTH}x{config.MAP_HEIGHT}"
        f"&scale=2"
        f"&maptype=roadmap"
        f"&markers=color:blue%7Clabel:U%7C{lat},{lng}"
    )

    # Custom dark-mode styling (exported from mapstyle.withgoogle.com)
    params += (
        "&style=element:geometry%7Ccolor:0x242f3e"
        "&style=element:labels.text.fill%7Ccolor:0xebebeb"
        "&style=element:labels.text.stroke%7Ccolor:0x242f3e"
        "&style=feature:administrative.locality%7Celement:labels%7Ccolor:0x232323"
        "&style=feature:administrative.locality%7Celement:labels.text.fill%7Ccolor:0xffffff"
        "&style=feature:poi%7Celement:labels.text.fill%7Ccolor:0xd59563"
        "&style=feature:poi.park%7Celement:geometry%7Ccolor:0x263c3f"
        "&style=feature:poi.park%7Celement:labels.text.fill%7Ccolor:0x6b9a76"
        "&style=feature:road%7Celement:geometry%7Ccolor:0x4d587b"
        "&style=feature:road%7Celement:geometry.stroke%7Ccolor:0x212a37"
        "&style=feature:road%7Celement:labels.text.fill%7Ccolor:0xd6d6d6"
        "&style=feature:road%7Celement:labels.text.stroke%7Ccolor:0x232323"
        "&style=feature:road.highway%7Celement:geometry%7Ccolor:0xa39b8a"
        "&style=feature:road.highway%7Celement:geometry.stroke%7Ccolor:0x1f2835"
        "&style=feature:road.highway%7Celement:labels.text.fill%7Ccolor:0xffffff"
        "&style=feature:transit%7Celement:geometry%7Ccolor:0x2f3948"
        "&style=feature:transit.station%7Celement:labels.text.fill%7Ccolor:0xd59563"
        "&style=feature:water%7Celement:geometry%7Ccolor:0x17263c"
        "&style=feature:water%7Celement:labels.text.fill%7Ccolor:0x515c6d"
        "&style=feature:water%7Celement:labels.text.stroke%7Ccolor:0x17263c"
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
        "updated_at": datetime.now(ZoneInfo(config.TIMEZONE)).isoformat(),
    }
    _save_device_locations()

    return jsonify({
        "status": "ok",
        "device_id": device_id,
        "location": _device_locations[device_id],
    })


def _build_gas_price_block(fuel):
    """Build the gas_price dict used in widget-data responses."""
    price_data = get_tomorrow_gas_price(fuel)
    trend = price_data.get("trend", "unknown")
    price = price_data.get("price")
    change = price_data.get("change")
    fuel_label = _FUEL_LABELS.get(fuel, "Regular")

    display = f"{price} c/L" if price else "N/A"
    if change is not None:
        sign = "+" if change > 0 else ""
        change_display = f"{sign}{change}c"
    else:
        change_display = "N/A"

    date_raw = price_data.get("date")
    if date_raw and isinstance(date_raw, str) and len(date_raw) > 5:
        parts = date_raw.split()
        date_short = " ".join(parts[-2:]) if len(parts) >= 2 else date_raw
    else:
        date_short = date_raw

    change_red = change_display if trend == "up" else " "
    change_green = change_display if trend == "down" else " "
    change_gray = change_display if trend == "stable" else " "

    return {
        "price": str(price) if price else None,
        "display": display,
        "change": str(change) if change is not None else None,
        "change_display": change_display,
        "change_red": change_red,
        "change_green": change_green,
        "change_gray": change_gray,
        "trend": trend,
        "color": _trend_color(trend),
        "date": date_short,
        "fuel_type": fuel,
        "fuel_label": fuel_label,
    }


@app.route("/api/toggle-fuel", methods=["GET", "POST"])
def api_toggle_fuel():
    """Toggle or set fuel type preference for a device.

    - No 'fuel' param: cycles regular → premium → regular
    - With 'fuel' param: sets to that specific type

    Returns the updated gas_price block so the Shortcut can use the
    new price immediately without a separate widget-data fetch.
    """
    device_id = (
        request.args.get("device_id")
        or request.args.get("device")
        or (request.get_json(silent=True) or {}).get("device_id")
        or "default"
    )
    explicit = (
        request.args.get("fuel")
        or (request.get_json(silent=True) or {}).get("fuel")
    )

    if explicit and explicit.lower() in _FUEL_TYPES:
        new_fuel = explicit.lower()
    else:
        current = _fuel_preferences.get(device_id, config.DEFAULT_FUEL_TYPE)
        idx = _FUEL_TYPES.index(current) if current in _FUEL_TYPES else 0
        new_fuel = _FUEL_TYPES[(idx + 1) % len(_FUEL_TYPES)]

    _fuel_preferences[device_id] = new_fuel
    _save_fuel_preferences()

    return jsonify({
        "status": "ok",
        "device_id": device_id,
        "fuel_type": new_fuel,
        "fuel_label": _FUEL_LABELS[new_fuel],
        "gas_price": _build_gas_price_block(new_fuel),
    })


@app.route("/api/fuel-type")
def api_fuel_type():
    """Return the current fuel type preference for a device."""
    device_id = (
        request.args.get("device_id")
        or request.args.get("device")
        or "default"
    )
    current = _fuel_preferences.get(device_id, config.DEFAULT_FUEL_TYPE)
    return jsonify({
        "fuel_type": current,
        "fuel_label": _FUEL_LABELS.get(current, "Regular"),
    })


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/debug/geocode")
def api_debug_geocode():
    """Debug endpoint: test reverse geocoding for a given lat/lng.

    Also shows the raw route components found, so you can verify the
    intersection label is correct.
    """
    lat = request.args.get("lat", config.DEFAULT_LAT, type=float)
    lng = request.args.get("lng", config.DEFAULT_LNG, type=float)

    # Clear cache for this coord so we get a fresh result
    cache_key = f"{lat},{lng}"
    _intersection_cache.pop(cache_key, None)

    intersection = _get_intersection(lat, lng)
    street = _street_from_address(
        next(
            (s["address"] for s in _load_stations()
             if s["lat"] == lat and s["lng"] == lng),
            "",
        )
    )

    # Also show raw geocoding data for debugging
    raw_routes = []
    if config.GOOGLE_MAPS_API_KEY:
        try:
            resp = http_requests.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={"latlng": cache_key, "key": config.GOOGLE_MAPS_API_KEY},
                timeout=5,
            )
            data = resp.json()
            for result in data.get("results", [])[:5]:
                for comp in result.get("address_components", []):
                    if "route" in comp.get("types", []):
                        raw_routes.append({
                            "short_name": comp.get("short_name"),
                            "long_name": comp.get("long_name"),
                        })
        except Exception:
            pass

    return jsonify({
        "lat": lat,
        "lng": lng,
        "api_key_set": bool(config.GOOGLE_MAPS_API_KEY),
        "geocoded_intersection": intersection,
        "address_fallback": street,
        "final_label": intersection or street or "Petro-Canada",
        "raw_routes_found": raw_routes,
    })


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
    """Proxy the Google Static Map image and serve PNG bytes directly."""
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
        headers={"Cache-Control": "public, max-age=60"},
    )


@app.route("/api/clear-cache", methods=["GET", "POST"])
def api_clear_cache():
    """Clear the gas price cache, forcing a fresh scrape on next request."""
    clear_price_cache()
    return jsonify({"status": "ok", "message": "Cache cleared"})


@app.route("/api/debug-scrape")
def api_debug_scrape():
    """Show what the scraper sees: all date blocks, parsed dates, and selection logic."""
    clear_price_cache()
    return jsonify(debug_scrape())


@app.route("/api/debug-state")
def api_debug_state():
    """Show the full server state: saved locations, fuel prefs, and current prices.

    Also shows what widget-data would return for each fuel type so you can
    verify the label and price match.
    """
    fuel = _fuel_preferences.get("default", config.DEFAULT_FUEL_TYPE)
    regular_block = _build_gas_price_block("regular")
    premium_block = _build_gas_price_block("premium")
    return jsonify({
        "device_locations": _device_locations,
        "fuel_preferences": _fuel_preferences,
        "default_fuel_type_env": config.DEFAULT_FUEL_TYPE,
        "resolved_fuel_type": fuel,
        "resolved_fuel_label": _FUEL_LABELS.get(fuel, "?"),
        "regular_price": {
            "label": "87",
            "price": regular_block.get("price"),
            "change": regular_block.get("change_display"),
            "display": regular_block.get("display"),
        },
        "premium_price": {
            "label": "91",
            "price": premium_block.get("price"),
            "change": premium_block.get("change_display"),
            "display": premium_block.get("display"),
        },
        "widget_would_show": {
            "fuel_label": _FUEL_LABELS.get(fuel, "?"),
            "display": regular_block.get("display") if fuel == "regular" else premium_block.get("display"),
        },
        "default_location": {
            "lat": config.DEFAULT_LAT,
            "lng": config.DEFAULT_LNG,
        },
    })


def _resolve_fuel_type():
    """Resolve fuel type from query param or device preference."""
    explicit = request.args.get("fuel")
    if explicit and explicit.lower() in _FUEL_TYPES:
        return explicit.lower()
    device_id = (
        request.args.get("device_id")
        or request.args.get("device")
        or "default"
    )
    return _fuel_preferences.get(device_id, config.DEFAULT_FUEL_TYPE)


@app.route("/api/gas-price")
def api_gas_price():
    fuel = _resolve_fuel_type()
    data = get_tomorrow_gas_price(fuel)
    trend = data.get("trend", "unknown")
    return jsonify(
        {
            "price": data.get("price"),
            "unit": data.get("unit", "cents/litre"),
            "change": data.get("change"),
            "trend": trend,
            "color": _trend_color(trend),
            "date": data.get("date"),
            "fuel_type": data.get("fuel_type", "Regular"),
            "source": data.get("source", "gaswizard.ca"),
            "stale": data.get("stale", False),
            "error": data.get("error"),
        }
    )


def _compute_widget_data():
    """Build the full widget-data dict from current state."""
    lat, lng = _resolve_location()

    # Stations
    nearby = _get_nearby_stations(lat, lng, config.SEARCH_RADIUS_KM)
    top_stations = nearby[: config.MAX_MAP_STATIONS]
    map_url = _build_static_map_url(lat, lng, top_stations)

    # Build list of nearest stations for display
    nearest_list = []
    for n in top_stations:
        intersection = _get_intersection(n["lat"], n["lng"])
        if not intersection:
            intersection = _street_from_address(n.get("address", ""))
        label = intersection if intersection else n["name"]
        nearest_list.append(
            {
                "name": n["name"],
                "intersection": label,
                "distance_km": n["distance_km"],
                "display": f"{label} ({n['distance_km']} km)",
                "nav_url": n["nav_url"],
            }
        )

    # Gas price
    fuel = _resolve_fuel_type()
    gas_price = _build_gas_price_block(fuel)

    return {
        "map_url": map_url,
        "gas_price": gas_price,
        "stations": {
            "count": len(nearby),
            "nearest": nearest_list[0]["display"] if nearest_list else None,
            "station_1": nearest_list[0]["display"] if len(nearest_list) > 0 else " ",
            "station_2": nearest_list[1]["display"] if len(nearest_list) > 1 else " ",
            "station_3": nearest_list[2]["display"] if len(nearest_list) > 2 else " ",
            "nav_url": nearest_list[0]["nav_url"] if nearest_list else None,
            "top": nearest_list,
        },
        "meta": {
            "updated_at": datetime.now(ZoneInfo(config.TIMEZONE)).isoformat(),
            "location": {"lat": lat, "lng": lng},
        },
    }


@app.route("/api/widget-data")
def api_widget_data():
    return jsonify(_compute_widget_data())


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG,
    )
