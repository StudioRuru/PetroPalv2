# PetroPal Widget - Widgy Setup Guide

## Prerequisites
- **Widgy app** installed from the App Store
- **PetroPal API** deployed (e.g., on Railway)
- Your API URL ready (e.g., `https://petropalv2-production.up.railway.app`)

## Before you start

**Replace this placeholder** in every URL:
- `YOUR_SERVER_URL` → your deployed API URL

> **GPS is handled automatically.** An iOS Shortcut sends your location to
> the server, so widget URLs don't need latitude/longitude parameters.
> See [Step 0: iOS Shortcut Setup](#step-0-ios-shortcut-setup-do-this-first) below.

---

## Step 0: iOS Shortcut Setup (do this first!)

The Shortcut sends your phone's GPS to the server so all widget layers
automatically use your current location.

### Create the Shortcut

1. Open the **Shortcuts** app
2. Create a new Shortcut called **"PetroPal Refresh"**
3. Add these actions in order:

| # | Action | Configuration |
|---|--------|---------------|
| 1 | **Get Current Location** | (no config needed) |
| 2 | **Get Contents of URL** | URL: `YOUR_SERVER_URL/api/update-location?lat=[Latitude]&lng=[Longitude]` -- tap `[Latitude]` and `[Longitude]` and select the magic variables from step 1's Current Location |

That's it! The server now remembers your GPS. All widget URLs will use it.

### Automate It (hourly refresh)

1. Go to **Shortcuts > Automation > "+"**
2. Trigger: **Time of Day** → repeat every 1 hour
3. Action: **Run Shortcut** → select "PetroPal Refresh"
4. Toggle OFF **"Ask Before Running"**

### Run It Once Now

Tap the **play button** on the Shortcut to send your location to the server for the first time. This must happen before the widget URLs will return location-specific data.

### Create the "PetroPal Toggle Fuel" Shortcut

This Shortcut lets you tap the fuel grade label to toggle between **87 (Regular)** and **91 (Premium)**.

1. Open the **Shortcuts** app
2. Create a new Shortcut called **"PetroPal Toggle Fuel"**
3. Add these actions in order:

| # | Action | Configuration |
|---|--------|---------------|
| 1 | **Get Contents of URL** | URL: `YOUR_SERVER_URL/api/toggle-fuel` |
| 2 | **Wait** | 1 second |
| 3 | **Open App** | App: **Widgy** |

Step 1 toggles the fuel preference on the server (the response includes the updated price).
Step 2 gives the server a moment to commit the change.
Step 3 opens Widgy which triggers a widget data refresh with the new fuel type.

### Create the "PetroPal Toggle Brand" Shortcut

This Shortcut lets you tap the brand badge to cycle through **Petro-Canada → Esso → Shell** independently from the octane toggle.

1. Open the **Shortcuts** app
2. Create a new Shortcut called **"PetroPal Toggle Brand"**
3. Add these actions in order:

| # | Action | Configuration |
|---|--------|---------------|
| 1 | **Get Contents of URL** | URL: `YOUR_SERVER_URL/api/toggle-brand` |
| 2 | **Wait** | 1 second |
| 3 | **Open App** | App: **Widgy** |

Step 1 cycles to the next brand on the server.
Step 2 gives the server a moment to commit the change.
Step 3 opens Widgy which triggers a widget data refresh with the new brand's stations.

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
After the Shortcut has run, no coordinates are needed in the URL.

1. Tap **"+"** > select **Image**
2. Set position: x=4, y=4, width=356, height=126
3. Corner radius: **12**
4. Go to **Image** > **Web and Maps** > **URL**
5. Enter: `YOUR_SERVER_URL/api/map-image`
6. The map should appear showing your location and nearby Petro-Canada stations

**Alternative (JavaScript mode):** If the URL option doesn't work, use **JavaScript** mode:
```javascript
var main = function() {
    return 'YOUR_SERVER_URL/api/map-image';
}
```

---

## Step 4: Add the Text Layers

For each text layer below, use Widgy's built-in **Endpoint** data source (not JavaScript -- the JS async mode is unreliable for `fetch()` in text layers):

1. Tap **"+"** > select **Text**
2. Set the position and style as shown
3. Tap the **data source cube icon**
4. Select **"Endpoint"**
5. Enter your API URL (no coordinates needed):
   ```
   YOUR_SERVER_URL/api/widget-data
   ```
6. Tap **"RUN"** -- Widgy fetches the JSON and shows all available fields
7. Select the field listed for each layer below

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
- Endpoint field: **`gas_price.display`** (shows "152.9 c/L")

### Price Change (3 stacked layers — red / green / gray)

Create **three text layers** at the **same position**. Only one will have text at a time; the others will be empty. This gives you dynamic color without JavaScript.

**Layer A — Price Up (red)**
- Position: x=176, y=132, width=50, height=18
- Font: SF Pro Mono, Semibold, size 12
- Color: **#FF3B30** (red)
- Endpoint field: **`gas_price.change_red`** (shows "+2.0c" only when price goes up)

**Layer B — Price Down (green)**
- Position: x=176, y=132, width=50, height=18
- Font: SF Pro Mono, Semibold, size 12
- Color: **#34C759** (green)
- Endpoint field: **`gas_price.change_green`** (shows "-8.0c" only when price goes down)

**Layer C — Stable (gray)**
- Position: x=176, y=132, width=50, height=18
- Font: SF Pro Mono, Semibold, size 12
- Color: **#8E8E93** (gray)
- Endpoint field: **`gas_price.change_gray`** (shows "0.0c" only when price is stable)

### Pin Icon (SF Symbol)
- Tap **"+"** > select **Symbol**
- SF Symbol: `mappin.circle.fill`
- Position: x=8, y=152, width=16, height=16
- Tint color: **#FF3B30** (red)

### Nearest Station
- Position: x=28, y=150, width=240, height=18
- Font: SF Pro, Regular, size 11
- Color: **#AEAEB2**
- Endpoint field: **`stations.nearest`** (shows "Petro-Canada - Hwy 7 & Warden (3.3 km)")

### Station Count
- Position: x=260, y=150, width=70, height=18
- Font: SF Pro, Regular, size 11
- Color: **#8E8E93**
- Text alignment: Right
- Endpoint field: **`stations.count`** (shows "10")

### Brand Badge (tappable — cycles Petro-Canada / Esso / Shell)
1. Tap **"+"** > select **Text**
2. Position: x=322, y=150, width=36, height=16
3. Font: SF Pro, **Bold**, size 10
4. Text color: **#FFFFFF** (white)
5. Text alignment: Center
6. Background color: **#48484A** (dark gray badge)
7. Corner radius: **4**
8. Endpoint field: **`brand.short`** (shows "PC", "Esso", or "Shell")

### Brand Toggle Tap Action
1. Tap **"+"** > select **Tap Action**
2. Position over the brand badge: x=318, y=144, width=44, height=26
3. Set action to: **External Action > Run Shortcut > "PetroPal Toggle Brand"**

Tapping the badge cycles the brand. The map, stations, and nav URL all update to the new brand on the next widget refresh.

---

## Step 5: Add the Fuel Grade Toggle

This button shows "87" or "91" and toggles between Regular and Premium octane when tapped.

### Fuel Grade Label
1. Tap **"+"** > select **Text**
2. Position: x=300, y=134, width=24, height=18
3. Font: SF Pro Mono, **Bold**, size 12
4. Color: **#FF9500** (orange)
5. Text alignment: Center
6. Endpoint field: **`gas_price.fuel_label`** (shows "87" or "91")

### Fuel Toggle Tap Action
1. Tap **"+"** > select **Tap Action**
2. Position over the fuel grade label: x=294, y=128, width=36, height=26
3. Set action to: **External Action > Run Shortcut > "PetroPal Toggle Fuel"**

**Important:** Make sure this does NOT overlap with the refresh button tap area (which starts at x=332). Leave a gap between them.

Tapping "87" switches to "91" (Premium) and the c/L price updates accordingly.

---

## Step 6: Add the Refresh Button

Widgy tap actions are **separate layers** -- they are invisible rectangles you place over content.

### Refresh Icon (visual only)
1. Tap **"+"** > select **Symbol**
2. SF Symbol: `arrow.clockwise.circle.fill`
3. Position: x=338, y=134, width=22, height=22
4. Tint color: **#48484A** (dark gray)

### Refresh Tap Action (the actual button)
1. Tap **"+"** > select **Tap Action**
2. Position it over the refresh icon: x=332, y=128, width=32, height=34
3. Set the action to: **External Action > Run Shortcut > "PetroPal Refresh"**

**Important:** This must NOT overlap with the fuel toggle tap area (which ends at x=330).

This lets you tap the refresh icon to update your GPS and data on demand.

### Map Tap Action (optional -- opens Google Maps)
1. Tap **"+"** > select **Tap Action**
2. Position it over the map: x=4, y=4, width=356, height=126
3. Set the action to: **External Action > Open URL**
4. URL: `https://www.google.com/maps/search/Petro-Canada/`

---

## Troubleshooting

**Map shows blank:**
- Make sure the iOS Shortcut has run at least once (tap play to run manually)
- Test the URL in a browser: `YOUR_SERVER_URL/api/map-image`
- If still blank, try with explicit coords: `YOUR_SERVER_URL/api/map-image?lat=43.6532&lng=-79.3832`

**Data shows "N/A":**
- The gas price scraper may not have data yet -- check `YOUR_SERVER_URL/api/gas-price` in a browser
- Verify your API URL is correct and the server is running

**Location is wrong / shows default Toronto:**
- Run the "PetroPal Refresh" Shortcut manually to send fresh GPS
- Check the server received it: `YOUR_SERVER_URL/api/update-location` should not return an error

**"Reload Widget" briefly opens Widgy app:**
- This is normal iOS behavior. Apple requires widgets to open the parent app before executing tap actions.
