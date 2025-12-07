# Dashboard Maps

Display ABC Emergency incidents on Home Assistant dashboard maps.

---

## Quick Start

Add ABC Emergency incidents to a map card in just a few steps:

### 1. Find Your Source Name

Each ABC Emergency instance has a unique source name based on how you configured it:

| Instance Type | Example Name | Source Name |
|---------------|--------------|-------------|
| State (NSW) | "NSW" | `abc_emergency_nsw` |
| State (VIC) | "VIC" | `abc_emergency_vic` |
| Zone | "Home" | `abc_emergency_home` |
| Zone | "My Home" | `abc_emergency_my_home` |
| Person | "Dad" | `abc_emergency_dad` |

The source name is: `abc_emergency_` + your instance name (lowercase, spaces become underscores).

### 2. Basic Map Card

Add this to your dashboard (via UI or YAML), replacing the source with your instance:

```yaml
type: map
title: Nearby Emergencies
geo_location_sources:
  - abc_emergency_home
entities:
  - zone.home
default_zoom: 10
aspect_ratio: "16:9"
```

### 3. View the Result

The map will show markers for each active emergency incident from that instance. Marker positions update automatically as the integration polls for new data.

---

## Map Card Configuration

### Essential Options

| Option | Description | Example |
|--------|-------------|---------|
| `geo_location_sources` | Source filter for geo-location entities | `abc_emergency_home` |
| `default_zoom` | Initial zoom level (1-20) | `10` |
| `aspect_ratio` | Card aspect ratio | `"16:9"` |
| `dark_mode` | Force dark map tiles | `true` |

### Recommended Zoom Levels

| View | Zoom Level |
|------|------------|
| Neighborhood | 12-14 |
| City | 10-11 |
| Region | 8-9 |
| State | 5-6 |
| Country | 4-5 |

---

## Examples

### Home Zone Map

Show incidents near your home:

```yaml
type: map
title: Emergencies Near Home
geo_location_sources:
  - abc_emergency_home
entities:
  - zone.home
default_zoom: 12
aspect_ratio: "16:9"
```

### State-Wide Emergency Map

Monitor all incidents across an entire state:

```yaml
type: map
title: NSW Emergencies
geo_location_sources:
  - abc_emergency_nsw
default_zoom: 6
aspect_ratio: "16:9"
```

### Person Tracking Map

Follow a family member's location with nearby incidents:

```yaml
type: map
title: Dad's Location
geo_location_sources:
  - abc_emergency_dad
entities:
  - person.dad
default_zoom: 11
aspect_ratio: "16:9"
```

### Multiple Instances on One Map

Combine incidents from multiple ABC Emergency instances:

```yaml
type: map
title: Family Emergency Watch
geo_location_sources:
  - abc_emergency_home
  - abc_emergency_work
  - abc_emergency_dad
entities:
  - zone.home
  - zone.work
  - person.dad
default_zoom: 8
aspect_ratio: "16:9"
```

### Full-Screen Emergency Dashboard

Create a dedicated emergency monitoring view:

```yaml
type: vertical-stack
cards:
  - type: map
    geo_location_sources:
      - abc_emergency_home
    entities:
      - zone.home
    default_zoom: 10
    aspect_ratio: "21:9"
  - type: horizontal-stack
    cards:
      - type: entity
        entity: sensor.abc_emergency_home_incidents_nearby
        name: Nearby
      - type: entity
        entity: sensor.abc_emergency_home_bushfires
        name: Bushfires
      - type: entity
        entity: sensor.abc_emergency_home_highest_alert_level
        name: Alert Level
```

---

## Understanding Geo-Location Sources

### How Sources Work

Each ABC Emergency instance creates geo-location entities with a unique source:

| Your Instance | Source for Map |
|---------------|----------------|
| Zone named "Home" | `abc_emergency_home` |
| Zone named "Beach House" | `abc_emergency_beach_house` |
| State "nsw" | `abc_emergency_nsw` |
| State "vic" | `abc_emergency_vic` |
| Person named "Mum" | `abc_emergency_mum` |

The source is automatically generated from your instance configuration.

### Source Naming Rules

- **Lowercase**: "Home" becomes `home`
- **Spaces to underscores**: "My Home" becomes `my_home`
- **Special characters removed**: "Dad's Place" becomes `dads_place`

### Geo-Location Entity Attributes

Each geo-location entity includes:

- **State**: Distance from monitored location (in km)
- **Latitude/Longitude**: Incident coordinates
- **Source**: Instance-specific (e.g., `abc_emergency_home`)
- **Attributes**: Alert level, event type, status, headline, reporting agency

---

## Filtering by Instance

### Show Only One Instance

```yaml
type: map
geo_location_sources:
  - abc_emergency_home  # Only home zone incidents
```

### Show Multiple Instances

```yaml
type: map
geo_location_sources:
  - abc_emergency_home
  - abc_emergency_nsw
```

### Separate Maps per Instance

Create different map cards for different purposes:

**Nearby incidents (filtered by radius):**
```yaml
type: map
title: Nearby Emergencies
geo_location_sources:
  - abc_emergency_home
entities:
  - zone.home
default_zoom: 12
```

**All state incidents:**
```yaml
type: map
title: All NSW Incidents
geo_location_sources:
  - abc_emergency_nsw
default_zoom: 6
```

---

## Conditional Maps

### Show Map Only When Alerts Exist

```yaml
type: conditional
conditions:
  - entity: binary_sensor.abc_emergency_home_active_alert
    state: "on"
card:
  type: map
  title: Active Emergencies!
  geo_location_sources:
    - abc_emergency_home
  entities:
    - zone.home
  default_zoom: 10
```

### Show Different Maps Based on Alert Level

```yaml
type: conditional
conditions:
  - entity: binary_sensor.abc_emergency_home_emergency_warning
    state: "on"
card:
  type: map
  title: "⚠️ EMERGENCY WARNING"
  geo_location_sources:
    - abc_emergency_home
  entities:
    - zone.home
  default_zoom: 11
```

---

## Automation Integration

### Popup Map on Alert

```yaml
automation:
  - alias: "Show Emergency Map"
    trigger:
      - platform: state
        entity_id: sensor.abc_emergency_home_incidents_nearby
    condition:
      - condition: numeric_state
        entity_id: sensor.abc_emergency_home_incidents_nearby
        above: 0
    action:
      - service: browser_mod.popup
        data:
          title: "Emergency Alert"
          card:
            type: map
            geo_location_sources:
              - abc_emergency_home
            entities:
              - zone.home
            default_zoom: 10
```

### Navigate to Map View

```yaml
automation:
  - alias: "Show Map on Emergency Warning"
    trigger:
      - platform: state
        entity_id: binary_sensor.abc_emergency_home_emergency_warning
        to: "on"
    action:
      - service: navigate
        data:
          navigation_path: /lovelace/emergency-map
```

---

## Performance Tips

### Large Number of Incidents

During major events, there may be hundreds of incidents. To improve map performance:

1. **Use Zone/Person mode** - Only shows nearby incidents (filtered by radius)
2. **Set appropriate radii** - Smaller radii = fewer markers
3. **Separate maps** - One map for nearby (Zone instance), one for state overview (State instance)

### Update Frequency

The integration updates every 5 minutes by default. Map markers update automatically when new data arrives.

---

## Troubleshooting

### Map Shows No Incidents

1. **Check if incidents exist**: Look at `sensor.abc_emergency_*_incidents_total`
2. **Verify source name**: Check Developer Tools → States for your geo_location entities
3. **Source spelling**: Must match exactly (lowercase, underscores for spaces)

### Find Your Exact Source Name

1. Go to **Developer Tools** → **States**
2. Filter for `geo_location.abc_emergency`
3. Click on any entity
4. Look at the `source` attribute

### Map Centered Wrong

By default, the map centers on entities in the `entities` list. To auto-fit to incidents:

```yaml
type: map
geo_location_sources:
  - abc_emergency_home
# Omit 'entities' to auto-fit to geo_locations
```

---

## Related Documentation

- [Entities Reference](entities.md) - All sensor and binary sensor details
- [Automations](automations.md) - Complete automation examples
- [Getting Started](getting-started.md) - Initial setup guide
