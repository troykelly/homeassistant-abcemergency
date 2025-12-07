# Dashboard Maps

Display ABC Emergency incidents on Home Assistant dashboard maps.

---

## Quick Start

Add ABC Emergency incidents to a map card in just a few steps:

### 1. Basic Map Card

Add this to your dashboard (via UI or YAML):

```yaml
type: map
geo_location_sources:
  - abc_emergency
default_zoom: 8
```

This displays all ABC Emergency geo-location entities on a map, centered on your Home location.

### 2. View the Result

The map will show markers for each active emergency incident. Marker positions update automatically as the integration polls for new data.

---

## Map Card Configuration

### Essential Options

| Option | Description | Example |
|--------|-------------|---------|
| `geo_location_sources` | Source filter for geo-location entities | `abc_emergency` |
| `default_zoom` | Initial zoom level (1-20) | `8` |
| `aspect_ratio` | Card aspect ratio | `16:9` |
| `dark_mode` | Force dark map tiles | `true` |

### Recommended Settings for Australia

```yaml
type: map
geo_location_sources:
  - abc_emergency
default_zoom: 6
aspect_ratio: 16:9
```

Zoom level `6` provides a good overview of a single Australian state.

---

## Examples

### State-Wide Emergency Map

Monitor all incidents across an entire state:

```yaml
type: map
title: NSW Emergencies
geo_location_sources:
  - abc_emergency
default_zoom: 6
aspect_ratio: 16:9
```

### Home-Focused Map

Center on your home with nearby incidents:

```yaml
type: map
title: Nearby Emergencies
geo_location_sources:
  - abc_emergency
entities:
  - zone.home
default_zoom: 10
aspect_ratio: 16:9
```

Adding `zone.home` to `entities` draws a marker for your home location.

### Multiple Zones Map

Show your home, work, and family locations together:

```yaml
type: map
title: Family Emergency Watch
geo_location_sources:
  - abc_emergency
entities:
  - zone.home
  - zone.work
  - person.dad
  - person.mum
default_zoom: 8
aspect_ratio: 16:9
```

### Full-Screen Emergency Dashboard

Create a dedicated emergency monitoring view:

```yaml
type: vertical-stack
cards:
  - type: map
    geo_location_sources:
      - abc_emergency
    entities:
      - zone.home
    default_zoom: 9
    aspect_ratio: 21:9
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

### How It Works

The ABC Emergency integration creates `geo_location` entities for each active incident. These entities have:

- **State**: Distance from your monitored location (in km)
- **Latitude/Longitude**: Incident coordinates
- **Source**: `abc_emergency` (used for filtering)
- **Attributes**: Alert level, event type, status, headline

### Source Filtering

The `geo_location_sources` option filters which geo-location entities appear on the map:

```yaml
geo_location_sources:
  - abc_emergency  # Only ABC Emergency incidents
```

If you have other geo-location integrations (e.g., USGS Earthquakes), they won't appear on this map.

### Multiple Instances

If you have multiple ABC Emergency instances (e.g., "Home" + "NSW State"), all will share the same `abc_emergency` source. The map will show incidents from all instances.

---

## Marker Appearance

### Default Markers

Geo-location entities appear as circular markers on the map. The marker shows:
- Position at incident coordinates
- Popup with entity name (headline) on click

### Custom Marker Colors (Advanced)

Home Assistant's map card doesn't directly support custom marker colors for geo-location entities. However, you can use custom cards from HACS for advanced styling:

- **Lovelace Plotly Graph Card** - For custom maps with colored markers
- **Leaflet Map Card** - More map customization options

---

## Filtering Incidents

### By Instance Type

Create separate map cards for different monitoring modes:

**Zone-based (nearby incidents only):**
```yaml
type: map
title: Nearby Emergencies
geo_location_sources:
  - abc_emergency
entities:
  - zone.home
default_zoom: 10
```

**State-wide view:**
```yaml
type: map
title: All NSW Incidents
geo_location_sources:
  - abc_emergency
default_zoom: 6
```

### Using Conditional Cards

Show the map only when there are active alerts:

```yaml
type: conditional
conditions:
  - entity: binary_sensor.abc_emergency_home_active_alert
    state: "on"
card:
  type: map
  title: Active Emergencies!
  geo_location_sources:
    - abc_emergency
  default_zoom: 9
```

---

## Automation Integration

### Trigger When Incidents Appear

```yaml
automation:
  - alias: "New Emergency Near Home"
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
              - abc_emergency
            entities:
              - zone.home
            default_zoom: 10
```

### Navigate to Map on Alert

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

1. **Use Zone/Person mode** instead of State mode - Only shows nearby incidents
2. **Set appropriate radii** - Smaller radii = fewer markers
3. **Consider separate maps** - One for nearby, one for state overview

### Update Frequency

The integration updates every 5 minutes by default. Map markers update automatically when new data arrives.

---

## Troubleshooting

### Map Shows No Incidents

1. **Check if incidents exist**: Look at `sensor.abc_emergency_*_incidents_total`
2. **Verify geo_location source**: Must be exactly `abc_emergency`
3. **Check integration status**: Settings → Devices & Services → ABC Emergency

### Incidents Not Updating

1. **Check coordinator status**: Download diagnostics for timestamp
2. **Verify network access**: Integration needs to reach abc.net.au
3. **Restart integration**: Settings → Devices & Services → ABC Emergency → Reload

### Map Centered Wrong

By default, the map centers on your Home zone. To override:

```yaml
type: map
geo_location_sources:
  - abc_emergency
# No entities = map auto-fits to show all geo_locations
```

Remove `entities` to let the map auto-fit to incident locations.

---

## Related Documentation

- [Entities Reference](entities.md) - All sensor and binary sensor details
- [Automations](automations.md) - Complete automation examples
- [Getting Started](getting-started.md) - Initial setup guide
