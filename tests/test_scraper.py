"""Tests for the Gas Wizard scraper."""

from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from zoneinfo import ZoneInfo

import config
from scraper.gasbuddy import get_tomorrow_gas_price, _scrape_gas_wizard, _cache


def _tomorrow_date():
    """Return tomorrow's date in the configured timezone."""
    tz = ZoneInfo(config.TIMEZONE)
    return (datetime.now(tz) + timedelta(days=1)).date()


def _today_date():
    """Return today's date in the configured timezone."""
    tz = ZoneInfo(config.TIMEZONE)
    return datetime.now(tz).date()


def _fmt_date(d):
    """Format a date like Gas Wizard: 'Friday - Mar 13, 2026'."""
    return d.strftime("%A - %b %d, %Y")


def _make_sample_html(tomorrow_price=160.9, tomorrow_change="+2",
                      today_price=158.9, today_change="-3"):
    tomorrow = _fmt_date(_tomorrow_date())
    today = _fmt_date(_today_date())
    return f"""
<html>
<body>
<h1>Toronto Gas Prices</h1>
<ul>
  <li>
    {tomorrow}
    Regular
    {tomorrow_price} ({tomorrow_change}\u00a2)
    Premium
    {tomorrow_price + 30} ({tomorrow_change}\u00a2)
    Diesel
    {tomorrow_price + 38} ({tomorrow_change}\u00a2)
  </li>
  <li>
    {today}
    Regular
    {today_price} ({today_change}\u00a2)
    Premium
    {today_price + 30} ({today_change}\u00a2)
    Diesel
    {today_price + 38} ({today_change}\u00a2)
  </li>
</ul>
</body>
</html>
"""


class TestScraper:
    def setup_method(self):
        # Clear cache between tests
        _cache["data"] = None
        _cache["timestamp"] = 0

    @patch("scraper.gasbuddy.requests.get")
    def test_scrapes_price(self, mock_get):
        html = _make_sample_html()
        mock_resp = MagicMock()
        mock_resp.text = html
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = _scrape_gas_wizard()
        assert result["regular"]["price"] == 160.9
        assert result["regular"]["change"] == 2.0
        assert result["regular"]["trend"] == "up"
        assert result["regular"]["source"] == "gaswizard.ca"
        assert result["premium"]["price"] == 190.9
        assert result["diesel"]["price"] == 198.9

    @patch("scraper.gasbuddy.requests.get")
    def test_scrapes_price_down(self, mock_get):
        html = _make_sample_html(
            tomorrow_price=157.9, tomorrow_change="\u22123",
            today_price=160.9, today_change="+2",
        )
        mock_resp = MagicMock()
        mock_resp.text = html
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = _scrape_gas_wizard()
        assert result["regular"]["price"] == 157.9
        assert result["regular"]["change"] == -3.0
        assert result["regular"]["trend"] == "down"
        assert result["premium"]["price"] == 187.9

    @patch("scraper.gasbuddy.requests.get")
    def test_picks_tomorrow_not_today(self, mock_get):
        """When page has both today and tomorrow, should pick tomorrow's block."""
        html = _make_sample_html(
            tomorrow_price=165.0, tomorrow_change="+5",
            today_price=160.0, today_change="-2",
        )
        mock_resp = MagicMock()
        mock_resp.text = html
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = _scrape_gas_wizard()
        assert result["regular"]["price"] == 165.0
        assert result["regular"]["change"] == 5.0

    @patch("scraper.gasbuddy.requests.get")
    def test_caches_result(self, mock_get):
        html = _make_sample_html()
        mock_resp = MagicMock()
        mock_resp.text = html
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result1 = get_tomorrow_gas_price()
        assert mock_get.call_count == 1

        result2 = get_tomorrow_gas_price()
        assert mock_get.call_count == 1
        assert result1["price"] == result2["price"]

    @patch("scraper.gasbuddy.requests.get")
    def test_error_fallback(self, mock_get):
        mock_get.side_effect = Exception("Network error")

        result = get_tomorrow_gas_price()
        assert result["price"] is None
        assert "error" in result

    @patch("scraper.gasbuddy.requests.get")
    def test_stale_cache_on_error(self, mock_get):
        html = _make_sample_html()
        mock_resp = MagicMock()
        mock_resp.text = html
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp
        get_tomorrow_gas_price()

        _cache["timestamp"] = 0

        mock_get.side_effect = Exception("Network error")
        result = get_tomorrow_gas_price()
        assert result["price"] == 160.9

    @patch("scraper.gasbuddy.requests.get")
    def test_fuel_type_selection(self, mock_get):
        html = _make_sample_html()
        mock_resp = MagicMock()
        mock_resp.text = html
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        regular = get_tomorrow_gas_price("regular")
        assert regular["price"] == 160.9
        assert regular["fuel_type"] == "Regular"

        premium = get_tomorrow_gas_price("premium")
        assert premium["price"] == 190.9
        assert premium["fuel_type"] == "Premium"
