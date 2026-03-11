"""
Gas price scraper for tomorrow's Toronto gas price.

Despite the module name (gasbuddy.py), this scrapes Gas Wizard
(gaswizard.ca) which is the only public source for tomorrow's
predicted gas prices in Toronto. GasBuddy only shows current
user-reported prices, not predictions.
"""

import re
import time
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

import config

_cache = {
    "data": None,
    "timestamp": 0,
}


def get_tomorrow_gas_price(fuel_type="regular"):
    """Fetch tomorrow's predicted gas price for Toronto from Gas Wizard.

    Args:
        fuel_type: One of 'regular', 'premium', or 'diesel'.

    Returns a dict with price info, using an in-memory cache with TTL.
    """
    now = time.time()
    if not _cache["data"] or (now - _cache["timestamp"]) >= config.CACHE_TTL_SECONDS:
        try:
            result = _scrape_gas_wizard()
            _cache["data"] = result
            _cache["timestamp"] = now
        except Exception:
            if not _cache["data"]:
                return {
                    "price": None,
                    "unit": "cents/litre",
                    "currency": "CAD",
                    "change": None,
                    "trend": "unknown",
                    "date": None,
                    "fuel_type": fuel_type,
                    "source": "gaswizard.ca",
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                    "error": "Unable to fetch price data",
                }

    all_fuels = _cache["data"]
    key = fuel_type.lower()
    if key in all_fuels:
        return all_fuels[key]

    # Stale fallback
    if _cache["data"]:
        entry = dict(all_fuels.get("regular", {}))
        entry["stale"] = True
        return entry

    return {
        "price": None,
        "unit": "cents/litre",
        "currency": "CAD",
        "change": None,
        "trend": "unknown",
        "date": None,
        "fuel_type": fuel_type,
        "source": "gaswizard.ca",
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "error": "Unable to fetch price data",
    }


def _scrape_gas_wizard():
    """Scrape Gas Wizard for tomorrow's Toronto gas prices (all fuel types).

    Returns a dict keyed by fuel type: { "regular": {...}, "premium": {...}, "diesel": {...} }
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    resp = requests.get(config.GAS_WIZARD_URL, headers=headers, timeout=10)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    text = soup.get_text()

    # Find the tomorrow row — the first date line with prices
    # Pattern: "Thursday - Mar 12, 2026:" or "Thursday, Mar 12:"
    # followed by "Regular: 153.9¢ (-7¢)" etc.
    date_str = None
    date_match = re.search(
        r'(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)'
        r'[,\s-]+(\w+\s+\d{1,2}(?:,?\s*\d{4})?)',
        text, re.IGNORECASE
    )
    if date_match:
        date_str = date_match.group(0).strip()

    # Parse all fuel type rows: "Regular: 153.9¢ (-7¢)"
    fuel_pattern = re.compile(
        r'(Regular|Premium|Diesel)\s*:\s*(\d{3}(?:\.\d)?)\s*[¢c]'
        r'\s*\(\s*([+-]\s*\d+(?:\.\d+)?)\s*[¢c]?\s*\)',
        re.IGNORECASE,
    )

    scraped_at = datetime.now(timezone.utc).isoformat()
    result = {}

    for match in fuel_pattern.finditer(text):
        fuel_name = match.group(1).lower()
        price = float(match.group(2))
        change = float(match.group(3).replace(" ", ""))

        if change > 0:
            trend = "up"
        elif change < 0:
            trend = "down"
        else:
            trend = "stable"

        result[fuel_name] = {
            "price": price,
            "unit": "cents/litre",
            "currency": "CAD",
            "change": change,
            "trend": trend,
            "date": date_str,
            "fuel_type": fuel_name.capitalize(),
            "source": "gaswizard.ca",
            "scraped_at": scraped_at,
        }

    # If the new pattern didn't match, fall back to the old broad parsing
    if "regular" not in result:
        price = None
        change = None

        price_match = re.search(r'(\d{3}(?:\.\d)?)\s*[¢c]', text)
        if not price_match:
            price_match = re.search(r'(?:regular|price)[^\d]*(\d{3}(?:\.\d)?)', text, re.IGNORECASE)
        if not price_match:
            price_match = re.search(r'(\d{3}\.\d)', text)
        if price_match:
            price = float(price_match.group(1))

        change_match = re.search(r'([+-]\s*\d+(?:\.\d+)?)\s*(?:cents?|¢|c/l)', text, re.IGNORECASE)
        if not change_match:
            change_match = re.search(r'(?:change|adjust)[^\d+-]*([+-]\s*\d+(?:\.\d+)?)', text, re.IGNORECASE)
        if change_match:
            change = float(change_match.group(1).replace(" ", ""))

        if change is not None:
            trend = "up" if change > 0 else ("down" if change < 0 else "stable")
        else:
            trend = "unknown"

        result["regular"] = {
            "price": price,
            "unit": "cents/litre",
            "currency": "CAD",
            "change": change,
            "trend": trend,
            "date": date_str,
            "fuel_type": "Regular",
            "source": "gaswizard.ca",
            "scraped_at": scraped_at,
        }

    return result
