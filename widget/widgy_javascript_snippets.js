// =============================================================================
// PetroPal - Widgy Data Source Reference
// =============================================================================
//
// IMPORTANT: Replace this placeholder before use:
//   YOUR_SERVER_URL → your deployed API (e.g., https://petropalv2-production.up.railway.app)
//
// HOW GPS WORKS:
//   1. An iOS Shortcut sends your GPS to the server once (and hourly via automation)
//   2. The server remembers your location
//   3. Widget URLs need NO coordinates -- the server uses the saved GPS
//
// See the "iOS Shortcut Setup" section at the bottom for the one-time setup.
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
//   3. Enter your API URL (no coordinates needed if Shortcut has run):
//
//      YOUR_SERVER_URL/api/widget-data
//
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
//   brand.short              → "PC" (or "Esso", "Shell")
//   brand.label              → "Petro-Canada" (or "Esso", "Shell")
//   stations.nearest         → "Petro-Canada - Hwy 7 & Warden (3.3 km)"
//   stations.count           → 10
//   stations.nav_url         → "https://www.google.com/maps/dir/..."
//   stations.top[0].display  → "Petro-Canada - Hwy 7 & Warden (3.3 km)"
//   stations.top[1].display  → "Petro-Canada - Kennedy & Denison (3.3 km)"
//   stations.top[2].display  → "Petro-Canada - McCowan & Steeles (7.1 km)"
//


// ============================
// MAP IMAGE LAYER
// ============================
// Layer: Image  |  Go to: Image > Web and Maps > URL
//
// The /api/map-image endpoint serves raw PNG bytes (no redirects).
// Just paste this URL directly (no coordinates needed if Shortcut has run):
//
//   YOUR_SERVER_URL/api/map-image
//
// Alternative: use "JavaScript" mode and paste:

var main = function() {
    return 'YOUR_SERVER_URL/api/map-image';
}


// =============================================================================
// iOS SHORTCUT SETUP: "PetroPal Refresh"
// =============================================================================
//
// This Shortcut sends your phone's GPS to the server so ALL widget layers
// automatically use your current location. No coordinates in URLs needed.
//
// --- Create the Shortcut ---
//
// Open the Shortcuts app and create a new Shortcut called "PetroPal Refresh":
//
//   STEP 1: "Get Current Location"
//      → This grabs your phone's GPS coordinates
//
//   STEP 2: "Get Contents of URL"  (this sends your GPS to the server)
//      → URL: YOUR_SERVER_URL/api/update-location?lat=[Latitude]&lng=[Longitude]
//        (Tap [Latitude] and [Longitude], then select the magic variables
//         from "Current Location" in step 1)
//      → Method: GET  (works with GET, no need to change to POST)
//
//   That's it! The server now knows your location and all widget URLs
//   (/api/widget-data, /api/map-image) will use it automatically.
//
//
// --- OPTIONAL: Also save data locally to iCloud (belt + suspenders) ---
//
//   STEP 3: "Get Contents of URL"
//      → URL: YOUR_SERVER_URL/api/widget-data?lat=[Latitude]&lng=[Longitude]
//      → This fetches the widget data using your fresh GPS
//
//   STEP 4: "Save File"
//      → Save to: iCloud Drive/Widgy/petropal.json
//      → Toggle OFF "Ask Where to Save"
//
//
// --- Automate it (hourly refresh) ---
//
//   1. Go to Shortcuts > Automation > "+"
//   2. Trigger: "Time of Day" → repeat every 1 hour
//   3. Action: "Run Shortcut" → select "PetroPal Refresh"
//   4. Toggle OFF "Ask Before Running"
//
//
// --- Trigger manually from widget ---
//
//   Add a "Tap Action" layer over the refresh icon:
//     • Tap Action type: "Run Shortcut"
//     • Select "PetroPal Refresh"
//   This lets you tap the widget to refresh GPS + data on demand.
//
//
// --- First-time setup ---
//
//   1. Build the Shortcut (steps 1-2 above)
//   2. Run it once manually (tap the play button)
//   3. Set up the hourly automation
//   4. In Widgy, add Endpoint data sources pointing to:
//        YOUR_SERVER_URL/api/widget-data     (for text layers)
//        YOUR_SERVER_URL/api/map-image        (for image layer)
//   5. No lat/lng needed in the URLs!
// =============================================================================
