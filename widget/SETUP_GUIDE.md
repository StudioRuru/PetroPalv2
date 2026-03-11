# PetroPal Widget - Widgy Setup Guide

## Prerequisites
- **Widgy app** installed from the App Store
- **PetroPal API** deployed (e.g., on Railway)
- Your API URL ready (e.g., `https://petropalv2-production.up.railway.app`)

## Before you start

**Replace these placeholders** in every snippet:
- `YOUR_SERVER_URL` → your deployed API URL
- `YOUR_LAT` → your latitude (e.g., `43.6532`)
- `YOUR_LNG` → your longitude (e.g., `-79.3832`)

> `navigator.geolocation` is **NOT available** in Widgy's JS sandbox.
> Coordinates must be hardcoded. For automatic GPS updates, see
> [GPS via iOS Shortcuts](#gps-via-ios-shortcuts) at the bottom.

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

The `/api/map-image` endpoint serves the map as raw PNG bytes (no redirects, no CORS issues).

1. Tap **"+"** > select **Image**
2. Set position: x=4, y=4, width=356, height=126
3. Corner radius: **12**
4. Go to **Image** > **Web and Maps** > **JavaScript**
5. **Delete any predefined code** (like the fox image example)
6. Select either JS mode and paste the corresponding code:

**If you chose `JavaScript` (main function) mode:**
```javascript
var main = function() {
    return 'YOUR_SERVER_URL/api/map-image?lat=YOUR_LAT&lng=YOUR_LNG';
}
```

**If you chose `javascript[async + no main()]` mode:**
```javascript
'YOUR_SERVER_URL/api/map-image?lat=YOUR_LAT&lng=YOUR_LNG';
```

7. **Replace the placeholders** with your actual values
8. Tap **RUN** -- you should see the map image appear

---

## Step 4: Add the Text Layers

For each text layer below:
1. Tap **"+"** > select **Text**
2. Set the position and style as shown
3. Tap the **cube icon** > choose **javascript[async + no main()]**
4. **Delete any predefined code**, paste the snippet, and **replace placeholders**
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

### Gas Price
- Position: x=96, y=132, width=80, height=18
- Font: SF Pro, **Bold**, size 13
- Color: **#FFFFFF** (white)
- JavaScript:
```javascript
const resp = await fetch('YOUR_SERVER_URL/api/widget-data?lat=YOUR_LAT&lng=YOUR_LNG');
const data = await resp.json();
data.gas_price.display;
```

### Price Change
- Position: x=176, y=132, width=50, height=18
- Font: SF Pro Mono, Semibold, size 12
- Color: **#FFFFFF**
- JavaScript:
```javascript
const resp = await fetch('YOUR_SERVER_URL/api/widget-data?lat=YOUR_LAT&lng=YOUR_LNG');
const data = await resp.json();
data.gas_price.change_display;
```

### Pin Icon (SF Symbol)
- Tap **"+"** > select **Symbol**
- SF Symbol: `mappin.circle.fill`
- Position: x=8, y=152, width=16, height=16
- Tint color: **#FF3B30** (red)

### Nearest Station
- Position: x=28, y=150, width=240, height=18
- Font: SF Pro, Regular, size 11
- Color: **#AEAEB2**
- JavaScript:
```javascript
const resp = await fetch('YOUR_SERVER_URL/api/widget-data?lat=YOUR_LAT&lng=YOUR_LNG');
const data = await resp.json();
data.stations.nearest || 'No stations nearby';
```

### Station Count
- Position: x=260, y=150, width=70, height=18
- Font: SF Pro, Regular, size 11
- Color: **#8E8E93**
- Text alignment: Right
- JavaScript:
```javascript
const resp = await fetch('YOUR_SERVER_URL/api/widget-data?lat=YOUR_LAT&lng=YOUR_LNG');
const data = await resp.json();
String(data.stations.count) + ' nearby';
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

### Map Tap Action (optional -- opens Google Maps)
1. Tap **"+"** > select **Tap Action**
2. Position it over the map: x=4, y=4, width=356, height=126
3. Set the action to: **External Action > Open URL**
4. URL: `https://www.google.com/maps/search/Petro-Canada/`

---

## Troubleshooting

**Map shows blank / "user undefined":**
- Make sure you **deleted the predefined fox image code** before pasting
- Check that you replaced `YOUR_LAT` and `YOUR_LNG` with actual numbers
- Test the URL directly in a browser: `YOUR_SERVER_URL/api/map-image?lat=43.6532&lng=-79.3832`

**Data shows "N/A":**
- The gas price scraper may not have data yet -- check `YOUR_SERVER_URL/api/gas-price` in a browser
- Verify your API URL is correct and the server is running

**"Reload Widget" briefly opens Widgy app:**
- This is normal iOS behavior. Apple requires widgets to open the parent app before executing tap actions.

---

## GPS via iOS Shortcuts

To get **dynamic GPS-based location** (since Widgy's JS can't access GPS):

### Create the Shortcut

1. Open the **Shortcuts** app
2. Create a new Shortcut called **"PetroPal Refresh"**
3. Add these actions in order:

| # | Action | Configuration |
|---|--------|---------------|
| 1 | **Get Current Location** | (no config needed) |
| 2 | **Get Contents of URL** | URL: `YOUR_SERVER_URL/api/widget-data?lat=[Latitude]&lng=[Longitude]` -- tap the `[Latitude]` and `[Longitude]` placeholders and select the magic variables from step 1 |
| 3 | **Save File** | Destination: `iCloud Drive/Widgy/petropal.json` -- toggle OFF "Ask Where to Save" |
| 4 | **Get Contents of URL** | URL: `YOUR_SERVER_URL/api/map-image?lat=[Latitude]&lng=[Longitude]` (same magic variables) |
| 5 | **Save File** | Destination: `iCloud Drive/Widgy/petropal_map.png` -- toggle OFF "Ask Where to Save" |

### Automate It

1. Go to **Shortcuts > Automation > "+"**
2. Trigger: **Time of Day** → repeat every 1 hour
3. Action: **Run Shortcut** → select "PetroPal Refresh"
4. Toggle OFF **"Ask Before Running"**

### Use in Widgy

Once the Shortcut has run at least once:

**For text layers** -- switch from JavaScript to **Files** data source:
- File: `iCloud Drive/Widgy/petropal.json`
- JSON path: `gas_price.display` (or `change_display`, `stations.nearest`, etc.)

**For the map image** -- use Image > **Web and Maps** > **URL**:
- File: `iCloud Drive/Widgy/petropal_map.png`

### Manual Refresh via Widget

Add a Tap Action layer over the refresh icon:
- Action: **External Action > Run Shortcut > "PetroPal Refresh"**

This lets you tap the widget to get fresh GPS + data on demand.
