# PetroPal Widgy Widget Setup Guide

## Prerequisites

1. **Widgy app** installed on your iOS device ([App Store](https://apps.apple.com/us/app/widgy-widgets-home-lock-watch/id1524540481))
2. **PetroPal API** deployed and accessible (see main README)
3. Your API server URL (e.g., `https://petropalv2-production.up.railway.app`)

## How GPS Works

An **iOS Shortcut** sends your phone's GPS to the server once (and hourly via automation). The server remembers your location, so **widget URLs don't need coordinates**. See the [Setup Guide](SETUP_GUIDE.md) for full Shortcut setup instructions.

## Widget Setup

### Option 1: Manual Setup in Widgy

1. Open Widgy and tap **Create New Widget**
2. Select **Large** widget size
3. Run the **"PetroPal Refresh"** iOS Shortcut once (see [Setup Guide](SETUP_GUIDE.md#step-0-ios-shortcut-setup-do-this-first))
4. Add the following layers:

#### Layer 1: Background
- Type: Rectangle
- Color: `#1C1C1E`
- Corner radius: 16
- Fill entire widget

#### Layer 2: Map Image
- Type: Image
- Source: Image > Web and Maps > URL
- URL: `https://YOUR_SERVER/api/map-image`
- Position: top 75% of widget (x:4, y:4, w:356, h:126)
- Corner radius: 12
- **Tap Action**: Open URL → `https://www.google.com/maps/search/Petro-Canada/`

#### Layer 3: Gas Price Text
- Type: Text
- Data source: **Endpoint** (tap the cube icon > select "Endpoint")
- URL: `https://YOUR_SERVER/api/widget-data`
- Tap "RUN", then select field: `gas_price.display`
- Font: SF Pro Bold, 13pt, White

#### Layer 4: Price Change
- Type: Text
- Data source: **Endpoint** (same URL as above)
- Field: `gas_price.change_display`
- Font: SF Pro Mono Semibold, 12pt
- Color: Use `gas_price.color` from API response (red for up, green for down)

#### Layer 5: Station Info
- Type: Text
- Data source: **Endpoint** (same URL)
- Field: `stations.nearest`
- Font: SF Pro Regular, 11pt, `#AEAEB2`

### Option 2: Import JSON Template

1. Copy `petropal_widget.json` to your iOS device
2. Open the file and find/replace `YOUR_SERVER_URL` with your actual API URL
3. In Widgy, go to **Manage** → **Import**
4. Select the modified JSON file

> **Note**: Widgy's import format may differ from the reference JSON provided. If the import doesn't work directly, use the JSON as a reference for the manual setup in Option 1.

## Location Access

GPS is handled server-side. The **"PetroPal Refresh" iOS Shortcut** sends your coordinates to `/api/update-location`, and all widget endpoints use the saved location automatically.

- **First time**: Run the Shortcut manually once
- **Ongoing**: The hourly automation keeps it updated
- **Manual refresh**: Tap the refresh button on the widget to re-run the Shortcut
- **Fallback**: You can still pass explicit `?lat=X&lng=Y` in any URL if needed

## Tap Actions

- **Tap the map**: Opens Google Maps with a search for "Petro-Canada" near your location
- **Tap the refresh icon**: Runs the "PetroPal Refresh" Shortcut to update GPS + data
- **Alternative**: Change the map tap URL to navigate directly to the nearest station using the `nav_url` from the API

## Troubleshooting

- **Map not loading**: Check that your `GOOGLE_MAPS_API_KEY` is valid and the Static Maps API is enabled. Make sure the Shortcut has run at least once.
- **Price showing N/A**: Gas Wizard may be temporarily unavailable; the API will serve cached data when possible
- **Location wrong / shows Toronto**: Run the "PetroPal Refresh" Shortcut manually to send fresh GPS
- **Widget not refreshing**: Widgy refreshes at minimum every 15 minutes; iOS may throttle background refreshes
