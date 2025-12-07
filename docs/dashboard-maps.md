# Dashboard Maps

Display ABC Emergency incidents on Home Assistant dashboard maps.

---

## Quick Start

Add ABC Emergency incidents to a map card in just a few steps:

### 1. Find Your Source Name

Each ABC Emergency instance uses its **configuration title** as the source name:

| Instance Type | Configuration Title | Source for Map Card |
|---------------|---------------------|---------------------|
| State (NSW) | ABC Emergency (NSW) | `"ABC Emergency (NSW)"` |
| State (VIC) | ABC Emergency (VIC) | `"ABC Emergency (VIC)"` |
| Zone | ABC Emergency (Home) | `"ABC Emergency (Home)"` |
| Zone | ABC Emergency (Treehouse) | `"ABC Emergency (Treehouse)"` |
| Person | ABC Emergency (Dad) | `"ABC Emergency (Dad)"` |

The source name is exactly what you see in **Settings → Devices & Services → ABC Emergency**.

### 2. Basic Map Card

Add this to your dashboard (via UI or YAML), replacing the source with your instance title:

```yaml
type: map
title: Nearby Emergencies
geo_location_sources:
  - "ABC Emergency (Home)"
entities:
  - zone.home
default_zoom: 10
aspect_ratio: "16:9"
```

> **Note:** The source must be quoted because it contains spaces and parentheses.

### 3. View the Result

The map will show markers for each active emergency incident from that instance. Marker positions update automatically as the integration polls for new data.

---

## Map Card Configuration

### Essential Options

| Option | Description | Example |
|--------|-------------|---------|
| `geo_location_sources` | Source filter for geo-location entities | `"ABC Emergency (Home)"` |
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
  - "ABC Emergency (Home)"
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
  - "ABC Emergency (NSW)"
default_zoom: 6
aspect_ratio: "16:9"
```

### Person Tracking Map

Follow a family member's location with nearby incidents:

```yaml
type: map
title: Dad's Location
geo_location_sources:
  - "ABC Emergency (Dad)"
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
  - "ABC Emergency (Home)"
  - "ABC Emergency (Work)"
  - "ABC Emergency (Dad)"
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
      - "ABC Emergency (Home)"
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

Each ABC Emergency instance creates geo-location entities with a source matching the configuration title:

| Your Instance Title | Source for Map |
|---------------------|----------------|
| ABC Emergency (Home) | `"ABC Emergency (Home)"` |
| ABC Emergency (Beach House) | `"ABC Emergency (Beach House)"` |
| ABC Emergency (NSW) | `"ABC Emergency (NSW)"` |
| ABC Emergency (VIC) | `"ABC Emergency (VIC)"` |
| ABC Emergency (Mum) | `"ABC Emergency (Mum)"` |

The source is the **exact title** shown in your integration configuration.

### Geo-Location Entity Attributes

Each geo-location entity includes:

| Attribute | Description | Example |
|-----------|-------------|---------|
| **state** | Distance from monitored location | `12.5` (km) |
| **latitude** | Incident latitude | `-33.8688` |
| **longitude** | Incident longitude | `151.2093` |
| **source** | Instance title for map filtering | `ABC Emergency (Home)` |
| **agency** | Reporting emergency service | `NSW Rural Fire Service` |
| **alert_level** | Warning level | `moderate` |
| **alert_text** | Warning text | `Advice` |
| **event_type** | Incident type | `Bushfire` |
| **status** | Current status | `Being controlled` |
| **direction** | Direction from you | `NW` |

---

## Filtering by Instance

### Show Only One Instance

```yaml
type: map
geo_location_sources:
  - "ABC Emergency (Home)"  # Only home zone incidents
```

### Show Multiple Instances

```yaml
type: map
geo_location_sources:
  - "ABC Emergency (Home)"
  - "ABC Emergency (NSW)"
```

### Separate Maps per Instance

Create different map cards for different purposes:

**Nearby incidents (filtered by radius):**
```yaml
type: map
title: Nearby Emergencies
geo_location_sources:
  - "ABC Emergency (Home)"
entities:
  - zone.home
default_zoom: 12
```

**All state incidents:**
```yaml
type: map
title: All NSW Incidents
geo_location_sources:
  - "ABC Emergency (NSW)"
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
    - "ABC Emergency (Home)"
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
    - "ABC Emergency (Home)"
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
              - "ABC Emergency (Home)"
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
3. **Source must be quoted**: Use `"ABC Emergency (Home)"` not `ABC Emergency (Home)`

### Find Your Exact Source Name

1. Go to **Developer Tools** → **States**
2. Filter for `geo_location`
3. Click on any ABC Emergency geo_location entity
4. Look at the `source` attribute - this is what you use in your map card

### Map Centered Wrong

By default, the map centers on entities in the `entities` list. To auto-fit to incidents:

```yaml
type: map
geo_location_sources:
  - "ABC Emergency (Home)"
# Omit 'entities' to auto-fit to geo_locations
```

---

## Related Documentation

- [Entities Reference](entities.md) - All sensor and binary sensor details
- [Automations](automations.md) - Complete automation examples
- [Getting Started](getting-started.md) - Initial setup guide
