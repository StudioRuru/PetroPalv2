// =============================================================================
// PetroPal - Widgy JavaScript Snippets
// =============================================================================
// Each snippet below is SELF-CONTAINED. Paste it into the relevant layer.
//
// TEXT LAYERS:  Use "javascript[async + no main()]" mode
// IMAGE LAYERS: Choose either "JavaScript" (main) or "javascript[async + no main()]"
//
// IMPORTANT: Replace these placeholders before pasting:
//   YOUR_SERVER_URL → your deployed API (e.g., https://petropalv2-production.up.railway.app)
//   YOUR_LAT        → your latitude  (e.g., 43.6532)
//   YOUR_LNG        → your longitude (e.g., -79.3832)
//
// NOTE: navigator.geolocation is NOT available in Widgy's JS sandbox.
// For dynamic GPS-based location, use the iOS Shortcuts approach at the
// bottom of this file.
// =============================================================================


// =====================
// SNIPPET 1: Gas Price
// =====================
// Layer: Text  |  Mode: javascript[async + no main()]
// Expected output: "160.9 c/L"

const resp = await fetch('YOUR_SERVER_URL/api/widget-data?lat=YOUR_LAT&lng=YOUR_LNG');
const data = await resp.json();
data.gas_price.display;


// ===========================
// SNIPPET 2: Price Change
// ===========================
// Layer: Text  |  Mode: javascript[async + no main()]
// Expected output: "+2.0c"

const resp = await fetch('YOUR_SERVER_URL/api/widget-data?lat=YOUR_LAT&lng=YOUR_LNG');
const data = await resp.json();
data.gas_price.change_display;


// ==============================
// SNIPPET 3: Nearest Station
// ==============================
// Layer: Text  |  Mode: javascript[async + no main()]
// Expected output: "Petro-Canada - Yonge & Bloor (0.3 km)"

const resp = await fetch('YOUR_SERVER_URL/api/widget-data?lat=YOUR_LAT&lng=YOUR_LNG');
const data = await resp.json();
data.stations.nearest || 'No stations nearby';


// ============================
// SNIPPET 4: Station Count
// ============================
// Layer: Text  |  Mode: javascript[async + no main()]
// Expected output: "8"

const resp = await fetch('YOUR_SERVER_URL/api/widget-data?lat=YOUR_LAT&lng=YOUR_LNG');
const data = await resp.json();
String(data.stations.count);


// ============================
// SNIPPET 5: Map Image
// ============================
// Layer: Image  |  Go to: Image > Web and Maps > JavaScript
//
// The /api/map-image endpoint serves raw PNG bytes (no redirects).
// Choose ONE of the two options below depending on which JS mode you pick.

// --- OPTION A: "JavaScript" mode (uses main() function) ---

var main = function() {
    return 'YOUR_SERVER_URL/api/map-image?lat=YOUR_LAT&lng=YOUR_LNG';
}

// --- OPTION B: "javascript[async + no main()]" mode ---

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
