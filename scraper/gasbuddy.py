"""
Gas price scraper for tomorrow's Toronto gas price.

Despite the module name (gasbuddy.py), this scrapes Gas Wizard
(gaswizard.ca) which is the only public source for tomorrow's
predicted gas prices in Toronto. GasBuddy only shows current
user-reported prices, not predictions.
"""

import time
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

import config

_cache = {
    "data": None,
    "timestamp": 0,
}


def get_tomorrow_gas_price():
    """Fetch tomorrow's predicted gas price for Toronto from Gas Wizard.

    Returns a dict with price info, using an in-memory cache with TTL.
    """
    now = time.time()
    if _cache["data"] and (now - _cache["timestamp"]) < config.CACHE_TTL_SECONDS:
        return _cache["data"]

    try:
        result = _scrape_gas_wizard()
        _cache["data"] = result
        _cache["timestamp"] = now
        return result
    except Exception:
        if _cache["data"]:
            stale = dict(_cache["data"])
            stale["stale"] = True
            return stale
        return {
            "price": None,
            "unit": "cents/litre",
            "currency": "CAD",
            "change": None,
            "trend": "unknown",
            "date": None,
            "fuel_type": "Regular",
            "source": "gaswizard.ca",
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "error": "Unable to fetch price data",
        }


def _scrape_gas_wizard():
    """Scrape Gas Wizard for tomorrow's Toronto gas price."""
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

    price = None
    change = None
    date_str = None

    # Gas Wizard typically shows price in a prominent heading/span
    # Look for price patterns (3-digit number with possible decimal)
    import re

    text = soup.get_text()

    # Find price pattern like "160.9" or "145.5"
    price_match = re.search(r'(\d{3}(?:\.\d)?)\s*[¢c]', text)
    if not price_match:
        # Try finding a 3-digit number near "regular" or "price"
        price_match = re.search(r'(?:regular|price)[^\d]*(\d{3}(?:\.\d)?)', text, re.IGNORECASE)
    if not price_match:
        # Broader search for any 3-digit price
        price_match = re.search(r'(\d{3}\.\d)', text)

    if price_match:
        price = float(price_match.group(1))

    # Find change pattern like "+2" or "-3" or "+2.0"
    change_match = re.search(r'([+-]\s*\d+(?:\.\d+)?)\s*(?:cents?|¢|c/l)', text, re.IGNORECASE)
    if not change_match:
        change_match = re.search(r'(?:change|adjust)[^\d+-]*([+-]\s*\d+(?:\.\d+)?)', text, re.IGNORECASE)

    if change_match:
        change = float(change_match.group(1).replace(" ", ""))

    # Find date
    date_match = re.search(
        r'(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)'
        r'[,\s-]+(\w+\s+\d{1,2}(?:,?\s*\d{4})?)',
        text, re.IGNORECASE
    )
    if date_match:
        date_str = date_match.group(0).strip()

    # Determine trend
    if change is not None:
        if change > 0:
            trend = "up"
        elif change < 0:
            trend = "down"
        else:
            trend = "stable"
    else:
        trend = "unknown"

    return {
        "price": price,
        "unit": "cents/litre",
        "currency": "CAD",
        "change": change,
        "trend": trend,
        "date": date_str,
        "fuel_type": "Regular",
        "source": "gaswizard.ca",
        "scraped_at": datetime.now(timezone.utc).isoformat(),
    }
