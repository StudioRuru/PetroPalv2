// =============================================================================
// PetroPal - Widgy Data Source Reference
// =============================================================================
//
// IMPORTANT: Replace these placeholders before use:
//   YOUR_SERVER_URL → your deployed API (e.g., https://petropalv2-production.up.railway.app)
//   YOUR_LAT        → your latitude  (e.g., 43.6532)
//   YOUR_LNG        → your longitude (e.g., -79.3832)
//
// NOTE: navigator.geolocation is NOT available in Widgy's JS sandbox.
// For dynamic GPS-based location, use the iOS Shortcuts approach at the
// bottom of this file.
// =============================================================================


// =============================================================================
// TEXT LAYERS: Use Widgy's built-in "Endpoint" data source (NOT JavaScript)
// =============================================================================
//
// Widgy's JavaScript async mode is unreliable for fetch() calls in text layers.
// Instead, use the native Endpoint/JSON data source -- it's simpler and works:
//
// For each text layer:
//   1. Tap the DATA SOURCE cube icon on the text layer
//   2. Select "Endpoint"
//   3. Enter your API URL:
//      YOUR_SERVER_URL/api/widget-data?lat=YOUR_LAT&lng=YOUR_LNG
//   4. Tap "RUN" -- Widgy fetches the JSON and shows available fields
//   5. Select the field you want from the list
//
// Available JSON fields:
//
//   gas_price.display        → "152.9 c/L"
//   gas_price.change_display → "-8.0c"
//   gas_price.price          → "152.9"
//   gas_price.change         → "-8.0"
//   gas_price.trend          → "down"
//   gas_price.color          → "#34C759"
//   gas_price.date           → "12, 2026"
//   stations.nearest         → "Petro-Canada - Hwy 7 & Warden (3.3 km)"
//   stations.count           → 10
//   stations.nav_url         → "https://www.google.com/maps/dir/..."
//


// ============================
// MAP IMAGE LAYER
// ============================
// Layer: Image  |  Go to: Image > Web and Maps
//
// The /api/map-image endpoint serves raw PNG bytes (no redirects).
// Choose ONE of these approaches:
//
// --- OPTION A: Direct URL (simplest, recommended) ---
//   In the Image layer, go to: Image > Web and Maps > URL
//   Paste this URL directly:
//
//   YOUR_SERVER_URL/api/map-image?lat=YOUR_LAT&lng=YOUR_LNG
//
//
// --- OPTION B: "JavaScript" mode (uses main() function) ---
//   Go to: Image > Web and Maps > JavaScript
//   Select "JavaScript" mode and paste:

var main = function() {
    return 'YOUR_SERVER_URL/api/map-image?lat=YOUR_LAT&lng=YOUR_LNG';
}

// --- OPTION C: "javascript[async + no main()]" mode ---
//   Go to: Image > Web and Maps > JavaScript
//   Select "javascript[async + no main()]" and paste:

'YOUR_SERVER_URL/api/map-image?lat=YOUR_LAT&lng=YOUR_LNG';


// =============================================================================
// GPS-BASED LOCATION VIA iOS SHORTCUTS (recommended)
// =============================================================================
// Since navigator.geolocation is NOT available in Widgy's JS sandbox,
// use an iOS Shortcut to inject your GPS coordinates automatically.
//
// --- Shortcut: "PetroPal Refresh" ---
//
// Build this Shortcut in the iOS Shortcuts app:
//
//   1. "Get Current Location"
//      → This gets your phone's GPS coordinates
//
//   2. "Get Contents of URL"
//      → Method: GET
//      → URL: YOUR_SERVER_URL/api/widget-data?lat=[Latitude]&lng=[Longitude]
//        (Use "Select Variable" > "Current Location" > "Latitude" / "Longitude"
//         from step 1 to insert the magic variables)
//
//   3. "Save File"
//      → Save the response to: iCloud Drive/Widgy/petropal.json
//      → Toggle OFF "Ask Where to Save"
//
//   4. (Optional) "Get Contents of URL"
//      → URL: YOUR_SERVER_URL/api/map-image?lat=[Latitude]&lng=[Longitude]
//      → This downloads the map image
//
//   5. (Optional) "Save File"
//      → Save to: iCloud Drive/Widgy/petropal_map.png
//      → Toggle OFF "Ask Where to Save"
//
// --- Automate it ---
//
//   • Go to Shortcuts > Automation > "+" > Personal Automation
//   • Trigger: "Time of Day" → set to repeat every 1 hour
//   • Action: "Run Shortcut" → select "PetroPal Refresh"
//   • Toggle OFF "Ask Before Running"
//
// --- Use in Widgy ---
//
//   For TEXT layers (price, station, etc.):
//     • Data source: "Files"
//     • File: iCloud Drive/Widgy/petropal.json
//     • JSON path: gas_price.display (or change_display, stations.nearest, etc.)
//
//   For the MAP image layer:
//     • Data source: Image > Web and Maps > URL
//     • File: iCloud Drive/Widgy/petropal_map.png
//     (Or keep using the JavaScript approach above with hardcoded coordinates
//      as a simpler alternative)
//
// --- Trigger from widget ---
//
//   Add a "Tap Action" layer over the refresh icon:
//     • Tap Action type: "Run Shortcut"
//     • Select "PetroPal Refresh"
//   This lets you manually refresh location + data by tapping the widget.
// =============================================================================
