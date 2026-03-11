# PetroPal Widget - Widgy Setup Guide

## Prerequisites
- **Widgy app** installed from the App Store
- **PetroPal API** deployed (e.g., on Railway)
- Your API URL ready (e.g., `https://petropalv2-production.up.railway.app`)

---

## Step 1: Create the Widget

1. Open **Widgy** and tap **Create** to start a new widget
2. Choose **Large** widget size
3. Name it **"PetroPal"**

---

## Step 2: Add the Background Layer

1. Tap **"+"** to add a layer > select **Rectangle**
2. Set position: x=0, y=0, width=364, height=170
3. Background color: **#1C1C1E** (dark gray)
4. Corner radius: **16**

---

## Step 3: Add the Map Image Layer

The API has a `/api/map-image` endpoint that serves the map as raw PNG bytes.
Widgy's image JavaScript expects a `main()` function that returns an image URL.

1. Tap **"+"** > select **Image**
2. Set position: x=4, y=4, width=356, height=126
3. Corner radius: **12**
4. Go to **Image** > **Web and Maps** > **JavaScript**
5. Paste this code:

```javascript
var main = function() {
    return 'YOUR_SERVER_URL/api/map-image?lat=YOUR_LAT&lng=YOUR_LNG';
}
```

6. **Replace the placeholders:**
   - `YOUR_SERVER_URL` with your API URL (e.g., `https://petropalv2-production.up.railway.app`)
   - `YOUR_LAT` and `YOUR_LNG` with your coordinates (e.g., `43.6532` and `-79.3832`)
7. Tap **RUN** -- you should see the map image appear

> **Note:** `navigator.geolocation` is NOT available in Widgy's JavaScript
> sandbox, so coordinates must be hardcoded. To update your location
> dynamically, use an iOS Shortcut (see the Fallback section in
> `widgy_javascript_snippets.js`).

---

## Step 4: Add the Text Layers

For each text layer below:
1. Tap **"+"** > select **Text**
2. Set the position and style as shown
3. Tap the **cube icon** > choose **JavaScript**
4. Paste the snippet and **replace `YOUR_SERVER_URL`**
5. Tap **RUN** to verify

### Gas Icon (SF Symbol, not a text layer)
- Tap **"+"** > select **Symbol**
- SF Symbol: `fuelpump.fill`
- Position: x=8, y=134, width=16, height=16
- Tint color: **#FF9500** (orange)

### "Tomorrow:" Label (static text, no data source needed)
- Position: x=28, y=132, width=70, height=18
- Text: `Tomorrow:`
- Font: SF Pro, Regular, size 11
- Color: **#8E8E93** (gray)

### Gas Price (JavaScript data source)
- Position: x=96, y=132, width=80, height=18
- Font: SF Pro, **Bold**, size 13
- Color: **#FFFFFF** (white)
- JavaScript:
```javascript
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
```

### Price Change (JavaScript data source)
- Position: x=176, y=132, width=50, height=18
- Font: SF Pro Mono, Semibold, size 12
- Color: **#FFFFFF**
- JavaScript:
```javascript
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
```

### Pin Icon (SF Symbol)
- Tap **"+"** > select **Symbol**
- SF Symbol: `mappin.circle.fill`
- Position: x=8, y=152, width=16, height=16
- Tint color: **#FF3B30** (red)

### Nearest Station (JavaScript data source)
- Position: x=28, y=150, width=240, height=18
- Font: SF Pro, Regular, size 11
- Color: **#AEAEB2**
- JavaScript:
```javascript
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
```

### Station Count (JavaScript data source)
- Position: x=260, y=150, width=70, height=18
- Font: SF Pro, Regular, size 11
- Color: **#8E8E93**
- Text alignment: Right
- JavaScript:
```javascript
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
String(data.stations.count) + " nearby";
```

---

## Step 5: Add the Refresh Button

Widgy tap actions are **separate layers** -- they are invisible rectangles you place over content.

### Refresh Icon (visual only)
1. Tap **"+"** > select **Symbol**
2. SF Symbol: `arrow.clockwise.circle.fill`
3. Position: x=336, y=134, width=22, height=22
4. Tint color: **#48484A** (dark gray)

### Refresh Tap Action (the actual button)
1. Tap **"+"** > select **Tap Action**
2. Position it over the refresh icon: x=330, y=128, width=34, height=34
3. Set the action to: **Reload Widget**

This gives you a tap target in the bottom-right corner. Tapping it forces Widgy to reload all data sources immediately -- re-fetching your GPS location, the map, and gas prices.

### Map Tap Action (optional -- opens Google Maps)
1. Tap **"+"** > select **Tap Action**
2. Position it over the map: x=4, y=4, width=356, height=126
3. Set the action to: **External Action > Open URL**
4. URL: `https://www.google.com/maps/search/Petro-Canada/`

This opens Google Maps searching for "Petro-Canada" near your current location when you tap the map.

---

## Step 6: Location Permissions

For location-based results to work:
1. Go to **iOS Settings > Widgy > Location**
2. Set to **"Always"** or **"While Using the App"**
3. Make sure **"Precise Location"** is ON

---

## Refresh Behavior

| Trigger | What happens |
|---------|-------------|
| Auto (every 15 min) | iOS refreshes the widget, Widgy re-runs all JS, GPS updates |
| Tap refresh icon | Immediately reloads widget data with fresh GPS coordinates |
| Tap map | Opens Google Maps app to search Petro-Canada near you |

---

## Troubleshooting

**Map shows wrong area / default Toronto location:**
- Check that Widgy has location permissions (Step 6)
- Test the JS snippet by tapping RUN in the editor -- if it returns Toronto coordinates, `navigator.geolocation` may not be available. Use the Shortcuts fallback (see `widgy_javascript_snippets.js`)

**Data shows "N/A":**
- The gas price scraper may not have data yet -- check `YOUR_SERVER_URL/api/gas-price` in a browser
- Verify your API URL is correct and the server is running

**"Reload Widget" briefly opens Widgy app:**
- This is normal iOS behavior. Apple requires widgets to open the parent app before executing tap actions. It returns to the home screen automatically.

---

## Fallback: iOS Shortcuts Approach

If `navigator.geolocation` doesn't work in Widgy's JavaScript sandbox:

1. Open the **Shortcuts** app
2. Create a new Shortcut called **"PetroPal Refresh"**:
   - **Get Current Location**
   - **Get Contents of URL**: `YOUR_SERVER_URL/api/widget-data?lat=[Latitude]&lng=[Longitude]`
   - **Save File** to: iCloud Drive > Widgy > petropal.json
3. In Widgy, switch each text layer from JavaScript to **Files** data source:
   - File path: `iCloud Drive/Widgy/petropal.json`
   - JSON path: `gas_price.display` (etc.)
4. Add a Tap Action layer that runs the Shortcut:
   - Action: **External Action > Run Shortcut > "PetroPal Refresh"**
5. Optionally set up **iOS Automation** to run the Shortcut every hour
