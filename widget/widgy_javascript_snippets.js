// =============================================================================
// PetroPal - Widgy JavaScript Snippets
// =============================================================================
// Each snippet below goes into a SEPARATE text layer's JavaScript editor.
// In Widgy: select a text layer > tap cube icon > choose "JavaScript" > paste.
//
// IMPORTANT: Replace YOUR_SERVER_URL with your actual deployed URL, e.g.:
//   https://petropalv2-production.up.railway.app
// =============================================================================


// ------------------------------------
// HELPER: Shared fetch function
// ------------------------------------
// This async function gets the user's location and calls the PetroPal API.
// It is included at the top of each snippet so every layer is self-contained.
//
// How it works:
//   1. Uses navigator.geolocation to get the phone's GPS coordinates
//   2. Passes lat/lng to your PetroPal API
//   3. Returns the full JSON response
//
// If navigator.geolocation is NOT available in Widgy's JS sandbox,
// see the "FALLBACK" section at the bottom of this file.
// ------------------------------------


// =====================
// SNIPPET 1: Gas Price
// =====================
// Layer: "Gas Price" text layer
// Expected output: "160.9 c/L"

async function getLocation() {
  return new Promise((resolve, reject) => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        pos => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
        () => resolve({ lat: 43.6532, lng: -79.3832 })
      );
    } else {
      resolve({ lat: 43.6532, lng: -79.3832 });
    }
  });
}
const loc = await getLocation();
const resp = await fetch(`YOUR_SERVER_URL/api/widget-data?lat=${loc.lat}&lng=${loc.lng}`);
const data = await resp.json();
data.gas_price.display;


// ===========================
// SNIPPET 2: Price Change
// ===========================
// Layer: "Price Change" text layer
// Expected output: "+2.0c"

async function getLocation() {
  return new Promise((resolve, reject) => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        pos => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
        () => resolve({ lat: 43.6532, lng: -79.3832 })
      );
    } else {
      resolve({ lat: 43.6532, lng: -79.3832 });
    }
  });
}
const loc = await getLocation();
const resp = await fetch(`YOUR_SERVER_URL/api/widget-data?lat=${loc.lat}&lng=${loc.lng}`);
const data = await resp.json();
data.gas_price.change_display;


// ==============================
// SNIPPET 3: Nearest Station
// ==============================
// Layer: "Nearest Station" text layer
// Expected output: "Petro-Canada - Yonge & Bloor (0.3 km)"

async function getLocation() {
  return new Promise((resolve, reject) => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        pos => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
        () => resolve({ lat: 43.6532, lng: -79.3832 })
      );
    } else {
      resolve({ lat: 43.6532, lng: -79.3832 });
    }
  });
}
const loc = await getLocation();
const resp = await fetch(`YOUR_SERVER_URL/api/widget-data?lat=${loc.lat}&lng=${loc.lng}`);
const data = await resp.json();
data.stations.nearest || "No stations nearby";


// ============================
// SNIPPET 4: Station Count
// ============================
// Layer: "Station Count" text layer
// Expected output: "8" (Widgy appends " nearby" via text_suffix if configured)

async function getLocation() {
  return new Promise((resolve, reject) => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        pos => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
        () => resolve({ lat: 43.6532, lng: -79.3832 })
      );
    } else {
      resolve({ lat: 43.6532, lng: -79.3832 });
    }
  });
}
const loc = await getLocation();
const resp = await fetch(`YOUR_SERVER_URL/api/widget-data?lat=${loc.lat}&lng=${loc.lng}`);
const data = await resp.json();
String(data.stations.count);


// ============================
// SNIPPET 5: Map Image
// ============================
// Layer: "Station Map" IMAGE layer (not text)
// In Widgy: Image > Web and Maps > JavaScript
//
// Widgy's image JS expects a main() function that returns an image URL.
// The /api/map-image endpoint serves raw PNG bytes, so Widgy can load
// it directly as an image source.
//
// NOTE: navigator.geolocation is NOT available in Widgy's JS sandbox,
// so we hardcode coordinates. Replace with your own lat/lng.

var main = function() {
    return 'YOUR_SERVER_URL/api/map-image?lat=YOUR_LAT&lng=YOUR_LNG';
}


// =============================================================================
// FALLBACK: If navigator.geolocation does NOT work in Widgy
// =============================================================================
// If geolocation is unavailable in Widgy's JavaScript sandbox, use one of
// these alternative approaches:
//
// OPTION A: Use the JSON endpoint data source (no location, uses server default)
//   - Select "JSON endpoint" instead of "JavaScript"
//   - URL: YOUR_SERVER_URL/api/widget-data
//   - json_path: gas_price.display (or whichever field)
//   - This uses Toronto as the default location
//
// OPTION B: iOS Shortcuts integration (recommended if geolocation fails)
//   1. Create an iOS Shortcut called "PetroPal Refresh":
//      - Action 1: "Get Current Location"
//      - Action 2: "Get Contents of URL"
//        URL: YOUR_SERVER_URL/api/widget-data?lat=[Latitude]&lng=[Longitude]
//      - Action 3: "Save File" to iCloud Drive/Widgy/petropal.json
//   2. In Widgy, use the "Files" data source on each text layer:
//      - File: iCloud Drive/Widgy/petropal.json
//      - json_path: gas_price.display (etc.)
//   3. Set up iOS Automation to run the Shortcut every hour, or
//      add a Tap Action layer that runs the Shortcut on tap.
//
// OPTION C: Hardcode your home location (simplest fallback)
//   Replace the getLocation() function in each snippet with:
//
//   const loc = { lat: YOUR_LAT, lng: YOUR_LNG };
//
//   Example for downtown Toronto:
//   const loc = { lat: 43.6532, lng: -79.3832 };
// =============================================================================
