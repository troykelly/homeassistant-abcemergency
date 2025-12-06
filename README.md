# ABC Emergency for Home Assistant

[![GitHub Release](https://img.shields.io/github/release/troykelly/homeassistant-abcemergency.svg?style=flat-square)](https://github.com/troykelly/homeassistant-abcemergency/releases)
[![GitHub Activity](https://img.shields.io/github/commit-activity/y/troykelly/homeassistant-abcemergency.svg?style=flat-square)](https://github.com/troykelly/homeassistant-abcemergency/commits/main)
[![License](https://img.shields.io/github/license/troykelly/homeassistant-abcemergency.svg?style=flat-square)](LICENSE)
[![hacs](https://img.shields.io/badge/HACS-Custom-orange.svg?style=flat-square)](https://hacs.xyz)

A Home Assistant custom integration for [ABC Emergency](https://www.abc.net.au/emergency) - Australia's emergency information service from the Australian Broadcasting Corporation.

## Features

- Real-time emergency incident data for all Australian states and territories
- Three monitoring modes:
  - **State Mode** - Monitor all incidents in a state/territory
  - **Zone Mode** - Monitor incidents near a fixed location with configurable radii
  - **Person Mode** - Monitor incidents near a person's dynamic location
- Support for the Australian Warning System alert levels (Advice, Watch and Act, Emergency Warning)
- Per-incident-type radius configuration for location-based monitoring
- Sensors for incident counts, nearest incident, and alert levels
- Binary sensors for active alerts at each warning level
- Geo-location entities for mapping incidents

### Supported Incident Types

- Bushfires and grass fires
- Floods
- Storms and severe weather
- Earthquakes
- Extreme heat and heatwaves
- Structure fires
- And more...

### Australian Warning System

| Level | Meaning |
|-------|---------|
| **Advice** (Yellow) | An incident has started. No immediate danger. Stay informed. |
| **Watch and Act** (Orange) | Heightened threat. Conditions changing. Take action now. |
| **Emergency Warning** (Red) | Highest level. You may be in danger. Act immediately. |

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots in the top right corner
3. Select "Custom repositories"
4. Add `https://github.com/troykelly/homeassistant-abcemergency` with category "Integration"
5. Click "Install"
6. Restart Home Assistant

### Manual Installation

1. Download the latest release from [GitHub](https://github.com/troykelly/homeassistant-abcemergency/releases)
2. Extract and copy the `custom_components/abcemergency` folder to your Home Assistant `custom_components` directory
3. Restart Home Assistant

## Configuration

1. Go to **Settings** > **Devices & Services**
2. Click **Add Integration**
3. Search for "ABC Emergency"
4. Select your monitoring mode:

### State Mode

Monitor all incidents in an Australian state or territory.

1. Select "Monitor a State/Territory"
2. Choose the state (NSW, VIC, QLD, SA, WA, TAS, NT, or ACT)
3. Done! All incidents in that state will be tracked.

**Use case:** Get a complete overview of emergency activity in your state.

### Zone Mode

Monitor incidents near a fixed location (your home, office, etc.).

1. Select "Monitor a fixed location (zone)"
2. Enter a name for the zone (e.g., "Home", "Office")
3. Select the location on the map
4. Configure alert radii for each incident type

**Use case:** Get alerts for incidents that could affect a specific location.

### Person Mode

Monitor incidents near a person's dynamic location as they move.

1. Select "Monitor a person's location"
2. Choose a person entity from your Home Assistant
3. Configure alert radii for each incident type

**Use case:** Track emergency situations around family members as they travel.

### Per-Incident-Type Radius (Zone/Person modes)

Different incident types have different default alert radii:

| Incident Type | Default Radius |
|---------------|----------------|
| Bushfire | 50 km |
| Earthquake | 100 km |
| Storm | 75 km |
| Flood | 30 km |
| Structure Fire | 10 km |
| Extreme Heat | 100 km |
| Other | 25 km |

Radii can be adjusted in the options flow after setup.

## Multiple Instances

You can add multiple instances of the integration to monitor different areas:

- One state instance for NSW + one for VIC
- A zone instance for your home + a zone for your workplace
- Person instances for each family member

Each instance creates its own set of entities.

## Entities

Each instance creates a device with the following entities:

### Sensors (All Modes)

| Sensor | Description |
|--------|-------------|
| `incidents_total` | Total active incidents |
| `highest_alert_level` | Highest warning level |
| `bushfires` | Active bushfire count |
| `floods` | Active flood count |
| `storms` | Active storm count |

### Additional Sensors (Zone/Person Modes Only)

| Sensor | Description |
|--------|-------------|
| `incidents_nearby` | Incidents within configured radii |
| `nearest_incident` | Distance to nearest incident (km) |

### Binary Sensors (All Modes)

| Sensor | Description |
|--------|-------------|
| `active_alert` | Any alert in monitored area |
| `emergency_warning` | Emergency Warning (red) active |
| `watch_and_act` | Watch and Act (orange) or higher |
| `advice` | Advice (yellow) or higher |

## Automation Examples

### Emergency Warning Notification

```yaml
automation:
  - alias: "ABC Emergency Warning Alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.abc_emergency_home_emergency_warning
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "EMERGENCY WARNING"
          message: >
            {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}
            is {{ states('sensor.abc_emergency_home_nearest_incident') }}km away
          data:
            priority: high
            channel: emergency
```

### Nearby Bushfire Alert

```yaml
automation:
  - alias: "Bushfire Within 20km"
    trigger:
      - platform: numeric_state
        entity_id: sensor.abc_emergency_home_nearest_incident
        below: 20
    condition:
      - condition: state
        entity_id: sensor.abc_emergency_home_nearest_incident
        attribute: event_type
        state: "Bushfire"
    action:
      - service: notify.all_devices
        data:
          message: "Bushfire detected {{ states('sensor.abc_emergency_home_nearest_incident') }}km away!"
```

### Alert When Person Enters Emergency Zone

```yaml
automation:
  - alias: "Family Member Near Emergency"
    trigger:
      - platform: state
        entity_id: binary_sensor.abc_emergency_dad_active_alert
        to: "on"
    action:
      - service: notify.mobile_app_mum
        data:
          title: "Emergency Near Dad"
          message: >
            There's an active emergency near Dad's location.
            Distance: {{ states('sensor.abc_emergency_dad_nearest_incident') }}km
```

## Migration from Previous Versions

If upgrading from v1 or v2, your existing configuration will be automatically migrated:

- **From v1:** Single state config becomes a State mode instance
- **From v2:** Multi-state config becomes a State mode instance for the first state

After migration, you can add additional instances as needed.

## Data Source

This integration uses data from [ABC Emergency](https://www.abc.net.au/emergency), which aggregates emergency information from state and territory emergency services across Australia.

**Note:** This is an unofficial integration and is not affiliated with or endorsed by the Australian Broadcasting Corporation.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
