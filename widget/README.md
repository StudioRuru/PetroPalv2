# PetroPal Widgy Widget Setup Guide

## Prerequisites

1. **Widgy app** installed on your iOS device ([App Store](https://apps.apple.com/us/app/widgy-widgets-home-lock-watch/id1524540481))
2. **PetroPal API** deployed and accessible (see main README)
3. Your API server URL (e.g., `https://your-app.onrender.com`)

## Widget Setup

### Option 1: Manual Setup in Widgy

1. Open Widgy and tap **Create New Widget**
2. Select **Large** widget size
3. Add the following layers:

#### Layer 1: Background
- Type: Rectangle
- Color: `#1C1C1E`
- Corner radius: 16
- Fill entire widget

#### Layer 2: Map Image
- Type: Image
- Source: Image > Web and Maps > URL
- URL: `https://YOUR_SERVER/api/map-image?lat=YOUR_LAT&lng=YOUR_LNG`
- Position: top 75% of widget (x:4, y:4, w:356, h:126)
- Corner radius: 12
- **Tap Action**: Open URL → `https://www.google.com/maps/search/Petro-Canada/@{{location.latitude}},{{location.longitude}},13z`

#### Layer 3: Gas Price Text
- Type: Text
- Data source: **Endpoint** (tap the cube icon > select "Endpoint")
- URL: `https://YOUR_SERVER/api/widget-data?lat=YOUR_LAT&lng=YOUR_LNG`
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

Widgy's JS sandbox does **not** support `navigator.geolocation`. You have two options:

- **Hardcode coordinates** in the URLs (e.g., `lat=43.874168&lng=-79.258543`)
- **Use iOS Shortcuts** for automatic GPS -- see the [Setup Guide](SETUP_GUIDE.md#gps-via-ios-shortcuts) for the full shortcut steps

## Tap Actions

- **Tap the map**: Opens Google Maps with a search for "Petro-Canada" near your location, showing all nearby stations
- **Alternative**: Change the tap URL to navigate directly to the nearest station using the `nav_url` from the API

## Troubleshooting

- **Map not loading**: Check that your `GOOGLE_MAPS_API_KEY` is valid and the Static Maps API is enabled
- **Price showing N/A**: Gas Wizard may be temporarily unavailable; the API will serve cached data when possible
- **Widget not refreshing**: Widgy refreshes at minimum every 15 minutes; iOS may throttle background refreshes
