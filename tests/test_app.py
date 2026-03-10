"""Tests for the PetroPal Flask API."""

import json
import math
from unittest.mock import patch

import pytest

import config

# Set a test API key so URL builder doesn't return None
config.GOOGLE_MAPS_API_KEY = "TEST_KEY"

from app import app, haversine, _get_nearby_stations, _build_static_map_url


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestHaversine:
    def test_same_point(self):
        assert haversine(43.6532, -79.3832, 43.6532, -79.3832) == 0.0

    def test_known_distance(self):
        # Toronto to Ottawa ~353 km
        dist = haversine(43.6532, -79.3832, 45.4215, -75.6972)
        assert 350 < dist < 360

    def test_short_distance(self):
        # Two points ~1 km apart
        dist = haversine(43.6532, -79.3832, 43.6622, -79.3832)
        assert 0.5 < dist < 1.5


class TestNearbyStations:
    def test_returns_sorted_by_distance(self):
        stations = _get_nearby_stations(43.6532, -79.3832, 15)
        if len(stations) >= 2:
            for i in range(len(stations) - 1):
                assert stations[i]["distance_km"] <= stations[i + 1]["distance_km"]

    def test_respects_radius(self):
        stations = _get_nearby_stations(43.6532, -79.3832, 5)
        for s in stations:
            assert s["distance_km"] <= 5.0

    def test_nav_url_present(self):
        stations = _get_nearby_stations(43.6532, -79.3832, 15)
        for s in stations:
            assert "google.com/maps/dir" in s["nav_url"]

    def test_no_stations_far_away(self):
        # Middle of the ocean
        stations = _get_nearby_stations(0.0, 0.0, 15)
        assert len(stations) == 0


class TestStaticMapUrl:
    def test_contains_api_key(self):
        url = _build_static_map_url(43.6532, -79.3832, [])
        assert "key=" in url

    def test_contains_center(self):
        url = _build_static_map_url(43.6532, -79.3832, [])
        assert "center=43.6532,-79.3832" in url

    def test_contains_station_markers(self):
        stations = [{"lat": 43.67, "lng": -79.39}]
        url = _build_static_map_url(43.6532, -79.3832, stations)
        assert "markers=color:red" in url
        assert "43.67,-79.39" in url

    def test_limits_markers_to_50(self):
        stations = [{"lat": 43.0 + i * 0.01, "lng": -79.0} for i in range(100)]
        url = _build_static_map_url(43.6532, -79.3832, stations)
        # Count station coordinate occurrences (excluding user marker)
        red_marker_section = url.split("markers=color:red")[1].split("&key=")[0] if "markers=color:red" in url else ""
        coords = red_marker_section.split("|")
        # First element is empty or style, remaining are coords
        coord_count = len([c for c in coords if "," in c and "color" not in c])
        assert coord_count <= 50


class TestHealthEndpoint:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.get_json() == {"status": "ok"}


class TestStationsEndpoint:
    def test_default_location(self, client):
        resp = client.get("/api/stations")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "stations" in data
        assert "count" in data
        assert data["count"] == len(data["stations"])

    def test_custom_radius(self, client):
        resp = client.get("/api/stations?lat=43.6532&lng=-79.3832&radius=2")
        data = resp.get_json()
        for s in data["stations"]:
            assert s["distance_km"] <= 2.0


class TestMapEndpoint:
    def test_redirect_format(self, client):
        resp = client.get("/api/map?lat=43.6532&lng=-79.3832")
        assert resp.status_code == 302
        assert "maps.googleapis.com" in resp.headers["Location"]

    def test_json_format(self, client):
        resp = client.get("/api/map?lat=43.6532&lng=-79.3832&format=json")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "map_url" in data


class TestGasPriceEndpoint:
    @patch("app.get_tomorrow_gas_price")
    def test_returns_price_data(self, mock_price, client):
        mock_price.return_value = {
            "price": 160.9,
            "unit": "cents/litre",
            "change": 2.0,
            "trend": "up",
            "date": "Wednesday - Mar 11, 2026",
            "source": "gaswizard.ca",
        }
        resp = client.get("/api/gas-price")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["price"] == 160.9
        assert data["trend"] == "up"
        assert data["color"] == "#FF3B30"

    @patch("app.get_tomorrow_gas_price")
    def test_down_trend_color(self, mock_price, client):
        mock_price.return_value = {
            "price": 155.0,
            "change": -3.0,
            "trend": "down",
        }
        resp = client.get("/api/gas-price")
        data = resp.get_json()
        assert data["color"] == "#34C759"


class TestWidgetDataEndpoint:
    @patch("app.get_tomorrow_gas_price")
    def test_combined_response(self, mock_price, client):
        mock_price.return_value = {
            "price": 160.9,
            "unit": "cents/litre",
            "change": 2.0,
            "trend": "up",
            "date": "Mar 11",
            "source": "gaswizard.ca",
        }
        resp = client.get("/api/widget-data?lat=43.6532&lng=-79.3832")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "map_url" in data
        assert "gas_price" in data
        assert "stations" in data
        assert "meta" in data
        assert data["gas_price"]["display"] == "160.9 c/L"
        assert data["gas_price"]["change_display"] == "+2.0c"
