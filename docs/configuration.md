# Configuration Guide

This guide covers all configuration options for ABC Emergency for Home Assistant.

---

## Configuration Overview

ABC Emergency supports three monitoring modes, each with different configuration options:

| Mode | Purpose | Location Source |
|------|---------|-----------------|
| **State Mode** | Monitor all incidents in a state/territory | Fixed state boundary |
| **Zone Mode** | Monitor incidents near a fixed location | User-defined coordinates |
| **Person Mode** | Monitor incidents near a moving person | Person entity's GPS location |

---

## State Mode Configuration

State Mode monitors all emergencies in an Australian state or territory.

### Initial Setup

1. Select **"Monitor a State/Territory"**
2. Choose your state:
   - `nsw` - New South Wales
   - `vic` - Victoria
   - `qld` - Queensland
   - `sa` - South Australia
   - `wa` - Western Australia
   - `tas` - Tasmania
   - `nt` - Northern Territory
   - `act` - Australian Capital Territory

### State Mode Options

State Mode has minimal configuration - just the state selection. There's no radius configuration because it monitors the entire state.

### Best Use Cases

- Getting a complete picture of emergency activity in your state
- Situational awareness during fire seasons
- Monitoring conditions before travel
- News/media monitoring

### Entities Created

- `sensor.abc_emergency_[state]_incidents_total`
- `sensor.abc_emergency_[state]_highest_alert_level`
- `sensor.abc_emergency_[state]_bushfires`
- `sensor.abc_emergency_[state]_floods`
- `sensor.abc_emergency_[state]_storms`
- `binary_sensor.abc_emergency_[state]_active_alert`
- `binary_sensor.abc_emergency_[state]_emergency_warning`
- `binary_sensor.abc_emergency_[state]_watch_and_act`
- `binary_sensor.abc_emergency_[state]_advice`

---

## Zone Mode Configuration

Zone Mode monitors emergencies within configurable distances of a fixed location.

### Initial Setup

1. Select **"Monitor a fixed location (zone)"**
2. Enter a **name** for the zone (e.g., "Home", "Office", "Farm")
3. Set the **location**:
   - Click on the map to set coordinates, OR
   - Enter latitude and longitude manually
4. Configure **alert radii** for each incident type

### Zone Name

The zone name becomes part of entity IDs:
- Name: "Home" → `sensor.abc_emergency_home_incidents_total`
- Name: "Beach House" → `sensor.abc_emergency_beach_house_incidents_total`

Use descriptive names that are easy to identify in automations.

### Location Selection

You can set the location by:

1. **Clicking on the map** - Zoom to your location and click
2. **Manual coordinates** - Enter latitude (e.g., `-33.8688`) and longitude (e.g., `151.2093`)
3. **Using Home Assistant zones** - If you have zones configured, you can match coordinates

### Per-Incident-Type Radius

Different emergency types have different area impacts. Zone Mode lets you configure separate alert radii for each type:

| Incident Type | Default | Range | Rationale |
|---------------|---------|-------|-----------|
| **Bushfire** | 50 km | 5-200 km | Can spread rapidly; smoke and ember attack extend far |
| **Earthquake** | 100 km | 10-500 km | Seismic effects felt over large distances |
| **Storm** | 75 km | 10-200 km | Severe storms cover broad areas |
| **Flood** | 30 km | 5-100 km | Typically more localized to waterways |
| **Structure Fire** | 10 km | 1-50 km | Rarely affects distant areas unless major |
| **Extreme Heat** | 100 km | 20-200 km | Heatwaves are regional events |
| **Other** | 25 km | 5-100 km | Balanced default for miscellaneous |

#### Adjusting Radii

Consider adjusting based on:

- **Rural vs urban** - Rural areas may need larger radii due to spread potential
- **Local geography** - Valleys may channel smoke/fire; coastal areas have different risks
- **Personal risk tolerance** - Increase for earlier warning; decrease to reduce noise
- **Historical events** - Past incidents in your area can guide appropriate distances

### Modifying Zone Options

After initial setup, you can modify options:

1. Go to **Settings** → **Devices & Services**
2. Find **ABC Emergency**
3. Click on your Zone instance
4. Click **Configure**
5. Adjust radii as needed
6. Click **Submit**

### Entities Created

Zone Mode creates all State Mode entities plus:

- `sensor.abc_emergency_[name]_incidents_nearby` - Count within radii
- `sensor.abc_emergency_[name]_nearest_incident` - Distance in km

---

## Person Mode Configuration

Person Mode monitors emergencies near a person's current location as they move.

### Prerequisites

You need a `person.*` entity with location tracking:

1. **Home Assistant Companion App** - Provides GPS location
2. **Device trackers** - GPS-based trackers linked to a person
3. **Other location sources** - Any device tracker assigned to a person

### Initial Setup

1. Select **"Monitor a person's location"**
2. Choose the **person entity** from the dropdown
3. Configure **alert radii** for each incident type (same options as Zone Mode)

### Person Entity Selection

Only `person.*` entities with location tracking appear in the dropdown. If your person doesn't appear:

1. Ensure the person has a device tracker assigned
2. Verify the device tracker is reporting location
3. Check **Developer Tools** → **States** for `person.*` entities with `latitude`/`longitude` attributes

### How Location Updates Work

1. The person entity's location updates (via mobile app, etc.)
2. ABC Emergency checks for incidents near the new location
3. Entities update to reflect incidents near the person's current position

**Update frequency:** The integration polls every 5 minutes. Location updates are processed on the next poll.

### Privacy Considerations

- Person Mode uses existing Home Assistant location data
- No additional tracking is introduced
- Location data stays within your Home Assistant instance
- The integration only reads location; it doesn't track or store history

### Best Use Cases

- Family safety monitoring
- Alerting when someone travels into an emergency zone
- Peace of mind for family members
- Traveler safety

### Entities Created

Same as Zone Mode, with entity names based on the person:

- `sensor.abc_emergency_[person]_nearest_incident`
- `binary_sensor.abc_emergency_[person]_emergency_warning`
- etc.

---

## Multiple Instances

You can run multiple instances of ABC Emergency simultaneously.

### Adding Another Instance

1. Go to **Settings** → **Devices & Services**
2. Click **ABC Emergency**
3. Click **+ Add Entry**
4. Configure the new instance

### Example Multi-Instance Setups

#### Family Safety Setup

| Instance | Mode | Purpose |
|----------|------|---------|
| NSW Overview | State | See all NSW emergencies |
| Home | Zone | Alerts for home location |
| Mum | Person | Track alerts near Mum |
| Dad | Person | Track alerts near Dad |

#### Property Portfolio

| Instance | Mode | Purpose |
|----------|------|---------|
| Primary Residence | Zone | Main home |
| Investment Property | Zone | Rental property |
| Holiday House | Zone | Coastal property |
| Farm | Zone | Rural property |

#### Traveler Setup

| Instance | Mode | Purpose |
|----------|------|---------|
| VIC | State | Home state overview |
| NSW | State | Neighboring state |
| QLD | State | Holiday destination |
| Self | Person | Personal location tracking |

### Instance Naming Best Practices

- Use descriptive, unique names
- Avoid special characters in names
- Keep names concise for entity IDs
- Consider how names will appear in automations

---

## Options Flow (Post-Setup Changes)

Most configuration can be modified after setup without removing the integration.

### Accessing Options

1. **Settings** → **Devices & Services**
2. Find **ABC Emergency**
3. Click on the specific instance
4. Click **Configure**

### What Can Be Changed

| Mode | Changeable Options |
|------|-------------------|
| State | State selection |
| Zone | Alert radii (not location) |
| Person | Alert radii, person entity |

### What Requires Reconfiguration

To change these, remove and re-add the instance:

- Zone location (coordinates)
- Zone name
- Switching between modes

---

## Update Interval

The integration polls ABC Emergency data at a fixed 5-minute interval.

### Why 5 Minutes?

- Balances timeliness with responsible API usage
- Emergency data typically updates every few minutes at the source
- Provides near-real-time awareness without overwhelming the data source

### Cannot Be Changed

The update interval is not configurable. This ensures:
- Consistent behavior across all installations
- Respectful use of the public ABC Emergency service
- Reliable data freshness for emergency purposes

---

## Data Refresh

### Manual Refresh

If you need to force a data refresh:

1. Go to **Developer Tools** → **Services**
2. Search for `homeassistant.update_entity`
3. Select your ABC Emergency sensor entity
4. Click **Call Service**

### Automatic Refresh

Data refreshes automatically:
- Every 5 minutes
- After Home Assistant restart
- After configuration changes

---

## Configuration Examples

### Minimal Setup (State Mode)

Just monitoring NSW:

```
Mode: State
State: NSW
```

Creates entities like `sensor.abc_emergency_nsw_incidents_total`.

### Home Monitoring (Zone Mode)

Monitoring your home in Sydney:

```
Mode: Zone
Name: Home
Latitude: -33.8688
Longitude: 151.2093
Radii:
  Bushfire: 50 km
  Earthquake: 100 km
  Storm: 75 km
  Flood: 30 km
  Structure Fire: 10 km
  Extreme Heat: 100 km
  Other: 25 km
```

### Rural Property (Zone Mode with Larger Radii)

Monitoring a farm in rural Victoria:

```
Mode: Zone
Name: Farm
Latitude: -37.5500
Longitude: 143.8500
Radii:
  Bushfire: 100 km    # Increased for rural fire spread
  Earthquake: 150 km
  Storm: 100 km
  Flood: 50 km        # Increased for river catchment
  Structure Fire: 20 km
  Extreme Heat: 150 km
  Other: 50 km
```

### Family Member Tracking (Person Mode)

Monitoring emergencies near a family member:

```
Mode: Person
Person: person.dad
Radii:
  Bushfire: 30 km     # Reduced for urban travel
  Earthquake: 100 km
  Storm: 50 km
  Flood: 20 km
  Structure Fire: 5 km
  Extreme Heat: 100 km
  Other: 15 km
```
