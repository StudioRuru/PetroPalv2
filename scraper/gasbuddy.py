"""
Gas price scraper for tomorrow's Toronto gas price.

Despite the module name (gasbuddy.py), this scrapes Gas Wizard
(gaswizard.ca) which is the only public source for tomorrow's
predicted gas prices in Toronto. GasBuddy only shows current
user-reported prices, not predictions.
"""

import re
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

import config

_cache = {
    "data": None,
    "timestamp": 0,
}


def clear_cache():
    """Clear the in-memory price cache, forcing a fresh scrape on next request."""
    _cache["data"] = None
    _cache["timestamp"] = 0


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


def _parse_date_str(date_str):
    """Try to parse a date string like 'Friday - Mar 13, 2026' into a date object."""
    # Strip day name prefix: "Friday - Mar 13, 2026" -> "Mar 13, 2026"
    cleaned = re.sub(
        r'^(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)'
        r'[\s,\-]+',
        '', date_str, flags=re.IGNORECASE,
    ).strip()

    for fmt in ("%b %d, %Y", "%b %d %Y", "%b %d", "%B %d, %Y", "%B %d"):
        try:
            parsed = datetime.strptime(cleaned, fmt).date()
            # If no year was in the format, assume current year
            if parsed.year == 1900:
                parsed = parsed.replace(year=datetime.now().year)
            return parsed
        except ValueError:
            continue
    return None


def _get_tomorrow_date():
    """Return tomorrow's date in the configured timezone."""
    tz = ZoneInfo(config.TIMEZONE)
    return (datetime.now(tz) + timedelta(days=1)).date()


def _fetch_page_text():
    """Fetch the Gas Wizard page and return the plain text."""
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
    return soup.get_text()


def _parse_day_blocks(text):
    """Parse all date blocks from page text.

    Returns a list of (date_str, parsed_date, {fuel_type: {...}}).
    """
    date_header_pattern = re.compile(
        r'((?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)'
        r'[,\s\-]+\w+\s+\d{1,2}(?:,?\s*\d{4})?)',
        re.IGNORECASE,
    )

    fuel_pattern = re.compile(
        r'(Regular|Premium|Diesel)\s+'
        r'(\d{3}(?:\.\d)?)\s*'
        r'\(\s*([+\-\u2212]\s*\d+(?:\.\d+)?)\s*[¢c]?\s*\)',
        re.IGNORECASE,
    )

    headers_found = list(date_header_pattern.finditer(text))
    day_blocks = []
    scraped_at = datetime.now(timezone.utc).isoformat()

    for i, hdr in enumerate(headers_found):
        date_str = hdr.group(0).strip()
        parsed_date = _parse_date_str(date_str)

        start = hdr.end()
        end = headers_found[i + 1].start() if i + 1 < len(headers_found) else len(text)
        block_text = text[start:end]

        fuels = {}
        for match in fuel_pattern.finditer(block_text):
            fuel_name = match.group(1).lower()
            price = float(match.group(2))
            change = float(match.group(3).replace(" ", "").replace("\u2212", "-"))

            if change > 0:
                trend = "up"
            elif change < 0:
                trend = "down"
            else:
                trend = "stable"

            fuels[fuel_name] = {
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

        day_blocks.append((date_str, parsed_date, fuels, block_text[:500]))

    return day_blocks


def _select_block(day_blocks):
    """Pick the best date block for 'tomorrow' in the user's timezone.

    Returns (selected_reason, selected_fuels) or (reason, None).
    """
    tomorrow = _get_tomorrow_date()
    today = tomorrow - timedelta(days=1)

    for date_str, parsed_date, fuels, _text in day_blocks:
        if fuels and parsed_date == tomorrow:
            return f"matched tomorrow ({tomorrow})", fuels

    for date_str, parsed_date, fuels, _text in day_blocks:
        if fuels and parsed_date == today:
            return f"matched today ({today})", fuels

    for date_str, parsed_date, fuels, _text in day_blocks:
        if fuels:
            return "fallback to first block with prices", fuels

    return "no blocks with prices found", None


def debug_scrape():
    """Scrape Gas Wizard and return full debug info about what was parsed."""
    text = _fetch_page_text()
    day_blocks = _parse_day_blocks(text)
    tomorrow = _get_tomorrow_date()
    today = tomorrow - timedelta(days=1)
    reason, selected = _select_block(day_blocks)

    return {
        "timezone": config.TIMEZONE,
        "today_in_tz": str(today),
        "tomorrow_in_tz": str(tomorrow),
        "blocks_found": [
            {
                "date_str": date_str,
                "parsed_date": str(parsed_date),
                "fuel_count": len(fuels),
                "regular_price": fuels.get("regular", {}).get("price"),
                "regular_change": fuels.get("regular", {}).get("change"),
                "raw_text": block_text,
            }
            for date_str, parsed_date, fuels, block_text in day_blocks
        ],
        "selection_reason": reason,
        "selected_regular_price": selected.get("regular", {}).get("price") if selected else None,
        "selected_regular_change": selected.get("regular", {}).get("change") if selected else None,
    }


def _scrape_gas_wizard():
    """Scrape Gas Wizard for tomorrow's Toronto gas prices (all fuel types).

    Parses all date blocks on the page, then picks the one that matches
    tomorrow in the configured timezone. Falls back to the first block
    if no exact match is found.

    Returns a dict keyed by fuel type: { "regular": {...}, "premium": {...}, ... }
    """
    text = _fetch_page_text()
    day_blocks = _parse_day_blocks(text)
    _reason, selected = _select_block(day_blocks)

    if selected:
        return selected

    # Last resort: try the old broad parsing
    scraped_at = datetime.now(timezone.utc).isoformat()
    return _fallback_parse(text, scraped_at)


def _fallback_parse(text, scraped_at):
    """Fallback parser for when the structured parsing fails."""
    date_str = None
    date_match = re.search(
        r'(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)'
        r'[,\s-]+(\w+\s+\d{1,2}(?:,?\s*\d{4})?)',
        text, re.IGNORECASE
    )
    if date_match:
        date_str = date_match.group(0).strip()

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

    return {
        "regular": {
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
    }
