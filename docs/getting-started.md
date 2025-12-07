# Getting Started with ABC Emergency

This guide walks you through installing and configuring ABC Emergency for Home Assistant.

---

## Prerequisites

Before installing, ensure you have:

- **Home Assistant** 2024.1.0 or newer
- **HACS** (Home Assistant Community Store) installed - [Install HACS](https://hacs.xyz/docs/setup/download)
- An Australian location configured in Home Assistant (for Zone/Person modes)

---

## Installation

### Method 1: HACS (Recommended)

HACS makes installation and updates easy.

#### Step 1: Add Custom Repository

1. Open Home Assistant
2. Navigate to **HACS** in the sidebar
3. Click the **three dots menu** (⋮) in the top right
4. Select **Custom repositories**
5. Enter the repository URL:
   ```
   https://github.com/troykelly/homeassistant-abcemergency
   ```
6. Select **Integration** as the category
7. Click **Add**

#### Step 2: Install the Integration

1. In HACS, click **Integrations**
2. Click **Explore & Download Repositories**
3. Search for **ABC Emergency**
4. Click on it, then click **Download**
5. Choose the latest version
6. Click **Download**

#### Step 3: Restart Home Assistant

1. Go to **Settings** → **System** → **Restart**
2. Click **Restart**
3. Wait for Home Assistant to fully restart

### Method 2: Manual Installation

If you prefer not to use HACS:

1. Download the [latest release](https://github.com/troykelly/homeassistant-abcemergency/releases)
2. Extract the ZIP file
3. Copy the `custom_components/abcemergency` folder to your Home Assistant's `custom_components` directory
   ```
   /config/custom_components/abcemergency/
   ```
4. Restart Home Assistant

---

## Adding the Integration

After installation and restart:

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration** (bottom right)
3. Search for **ABC Emergency**
4. Click on it to begin setup

---

## Configuration Wizard

The setup wizard guides you through configuring your monitoring preferences.

### Step 1: Choose Monitoring Mode

You'll be asked to select how you want to monitor emergencies:

| Option | Use Case |
|--------|----------|
| **Monitor a State/Territory** | See all emergencies in a state (NSW, VIC, QLD, etc.) |
| **Monitor a fixed location (zone)** | Get alerts within a radius of a specific location |
| **Monitor a person's location** | Track alerts near a person as they move |

### Step 2: Configure Your Choice

#### For State Mode

1. Select your state from the dropdown:
   - New South Wales (NSW)
   - Victoria (VIC)
   - Queensland (QLD)
   - South Australia (SA)
   - Western Australia (WA)
   - Tasmania (TAS)
   - Northern Territory (NT)
   - Australian Capital Territory (ACT)
2. Click **Submit**

#### For Zone Mode

1. Enter a **name** for this zone (e.g., "Home", "Office", "Beach House")
2. Select the location on the map, or enter coordinates manually
3. Configure **alert radii** for each incident type (optional - defaults shown below):

| Incident Type | Default Radius | Why |
|---------------|----------------|-----|
| Bushfire | 50 km | Bushfires can spread rapidly and affect large areas |
| Earthquake | 100 km | Seismic events are felt over wide distances |
| Storm | 75 km | Severe storms affect broad regions |
| Flood | 30 km | Floods are typically more localized |
| Structure Fire | 10 km | Structure fires rarely affect distant areas |
| Extreme Heat | 100 km | Heatwaves cover entire regions |
| Other | 25 km | Balanced default for miscellaneous incidents |

4. Click **Submit**

#### For Person Mode

1. Select a **person entity** from the dropdown
   - This must be a `person.*` entity configured in Home Assistant
   - The person entity tracks location via mobile app or device trackers
2. Configure **alert radii** for each incident type (same defaults as Zone Mode)
3. Click **Submit**

---

## Verifying Installation

After configuration, verify everything is working:

### Check the Device

1. Go to **Settings** → **Devices & Services**
2. Find **ABC Emergency**
3. Click on your configured instance
4. You should see a device with multiple entities

### Check the Entities

Navigate to **Developer Tools** → **States** and search for `abc_emergency`. You should see:

**Sensors:**
- `sensor.abc_emergency_[name]_incidents_total` - Total incidents in monitored area
- `sensor.abc_emergency_[name]_highest_alert_level` - Current highest warning level
- `sensor.abc_emergency_[name]_bushfires` - Active bushfire count
- `sensor.abc_emergency_[name]_floods` - Active flood count
- `sensor.abc_emergency_[name]_storms` - Active storm count

**For Zone/Person modes only:**
- `sensor.abc_emergency_[name]_incidents_nearby` - Incidents within your radii
- `sensor.abc_emergency_[name]_nearest_incident` - Distance to nearest incident

**Binary Sensors:**
- `binary_sensor.abc_emergency_[name]_active_alert` - Any alert active
- `binary_sensor.abc_emergency_[name]_emergency_warning` - Red level alert
- `binary_sensor.abc_emergency_[name]_watch_and_act` - Orange level or higher
- `binary_sensor.abc_emergency_[name]_advice` - Yellow level or higher

### Check the Map

If using Zone or Person mode with geo-location entities enabled:

1. Go to your Home Assistant **Map**
2. You should see markers for active incidents in your monitored area

---

## Adding Multiple Instances

You can add multiple instances to monitor different areas:

1. Go to **Settings** → **Devices & Services**
2. Click **ABC Emergency**
3. Click **+ Add Entry**
4. Configure the new instance

**Example configurations:**

- One State instance for NSW overview + one Zone instance for your home
- Zone instances for home, office, and holiday house
- Person instances for each family member

---

## Next Steps

Now that you're set up:

1. **[Configure notifications](notifications.md)** - Set up mobile alerts
2. **[Create automations](automations.md)** - Automate your emergency response
3. **[Explore entities](entities.md)** - Understand all available data
4. **[Troubleshoot issues](troubleshooting.md)** - If something's not working

---

## Updating the Integration

### Via HACS

1. Open HACS
2. Go to **Integrations**
3. If an update is available, you'll see a notification
4. Click **Update**
5. Restart Home Assistant

### Manual Update

1. Download the new release
2. Replace the contents of `custom_components/abcemergency`
3. Restart Home Assistant

---

## Uninstalling

### Via HACS

1. Open HACS → **Integrations**
2. Find **ABC Emergency**
3. Click the three dots menu → **Remove**
4. Remove the integration from **Settings** → **Devices & Services**
5. Restart Home Assistant

### Manual

1. Delete the `custom_components/abcemergency` folder
2. Remove the integration from **Settings** → **Devices & Services**
3. Restart Home Assistant
