"""Tests for the Gas Wizard scraper."""

from unittest.mock import patch, MagicMock

from scraper.gasbuddy import get_tomorrow_gas_price, _scrape_gas_wizard, _cache


# Matches actual Gas Wizard format: "Regular: 160.9¢ (+2¢)"
# Matches actual Gas Wizard format: label on one line, price on next
SAMPLE_HTML = """
<html>
<body>
<h1>Toronto Gas Prices</h1>
<p>Wednesday - Mar 11, 2026</p>
<ul>
  <li>
    Regular
    160.9 (+2¢)
    Premium
    190.9 (+2¢)
    Diesel
    198.9 (-3¢)
  </li>
</ul>
</body>
</html>
"""

# Uses Unicode minus sign (U+2212) like the real site
SAMPLE_HTML_DOWN = """
<html>
<body>
<h1>Toronto Gas Prices</h1>
<p>Thursday - Mar 12, 2026</p>
<ul>
  <li>
    Regular
    157.9 (\u22123¢)
    Premium
    187.9 (\u22123¢)
    Diesel
    195.9 (\u22125¢)
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
        mock_resp = MagicMock()
        mock_resp.text = SAMPLE_HTML
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = _scrape_gas_wizard()
        assert result["regular"]["price"] == 160.9
        assert result["regular"]["change"] == 2.0
        assert result["regular"]["trend"] == "up"
        assert result["regular"]["source"] == "gaswizard.ca"
        assert result["premium"]["price"] == 190.9
        assert result["diesel"]["price"] == 198.9
        assert result["diesel"]["change"] == -3.0
        assert result["diesel"]["trend"] == "down"

    @patch("scraper.gasbuddy.requests.get")
    def test_scrapes_price_down(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = SAMPLE_HTML_DOWN
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = _scrape_gas_wizard()
        assert result["regular"]["price"] == 157.9
        assert result["regular"]["change"] == -3.0
        assert result["regular"]["trend"] == "down"
        assert result["premium"]["price"] == 187.9
        assert result["diesel"]["price"] == 195.9

    @patch("scraper.gasbuddy.requests.get")
    def test_caches_result(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = SAMPLE_HTML
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        # First call should hit the network
        result1 = get_tomorrow_gas_price()
        assert mock_get.call_count == 1

        # Second call should use cache
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
        # First successful call
        mock_resp = MagicMock()
        mock_resp.text = SAMPLE_HTML
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp
        get_tomorrow_gas_price()

        # Expire cache
        _cache["timestamp"] = 0

        # Second call fails — should return cached regular data
        mock_get.side_effect = Exception("Network error")
        result = get_tomorrow_gas_price()
        assert result["price"] == 160.9

    @patch("scraper.gasbuddy.requests.get")
    def test_fuel_type_selection(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = SAMPLE_HTML
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        regular = get_tomorrow_gas_price("regular")
        assert regular["price"] == 160.9
        assert regular["fuel_type"] == "Regular"

        premium = get_tomorrow_gas_price("premium")
        assert premium["price"] == 190.9
        assert premium["fuel_type"] == "Premium"
