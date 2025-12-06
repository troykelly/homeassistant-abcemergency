# ABC Emergency for Home Assistant

[![GitHub Release](https://img.shields.io/github/release/troykelly/homeassistant-abcemergency.svg?style=flat-square)](https://github.com/troykelly/homeassistant-abcemergency/releases)
[![GitHub Activity](https://img.shields.io/github/commit-activity/y/troykelly/homeassistant-abcemergency.svg?style=flat-square)](https://github.com/troykelly/homeassistant-abcemergency/commits/main)
[![License](https://img.shields.io/github/license/troykelly/homeassistant-abcemergency.svg?style=flat-square)](LICENSE)
[![hacs](https://img.shields.io/badge/HACS-Custom-orange.svg?style=flat-square)](https://hacs.xyz)

A Home Assistant custom integration for [ABC Emergency](https://www.abc.net.au/emergency) - Australia's emergency information service from the Australian Broadcasting Corporation.

## Features

- Real-time emergency incident data for all Australian states and territories
- Location-based alerting with configurable radii per incident type
- Support for the Australian Warning System alert levels (Advice, Watch and Act, Emergency Warning)
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
4. Follow the configuration steps:
   - Select the Australian states/territories to monitor
   - Configure state-wide entity options
   - Set your monitoring zone (home location or custom)
   - Configure alert radii per incident type
   - Configure zone-filtered entity options

### Per-Incident-Type Radius

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

## Entities

### Sensors

| Sensor | Description |
|--------|-------------|
| `sensor.abc_emergency_incidents_total` | Total active incidents in monitored states |
| `sensor.abc_emergency_incidents_nearby` | Incidents within configured radii |
| `sensor.abc_emergency_nearest_incident` | Distance to nearest incident |
| `sensor.abc_emergency_highest_alert_level` | Highest warning level in monitored area |
| `sensor.abc_emergency_bushfires` | Active bushfire count |
| `sensor.abc_emergency_floods` | Active flood count |
| `sensor.abc_emergency_storms` | Active storm count |

### Binary Sensors

| Sensor | Description |
|--------|-------------|
| `binary_sensor.abc_emergency_active_alert` | Any alert in monitored area |
| `binary_sensor.abc_emergency_emergency_warning` | Emergency Warning (red) active |
| `binary_sensor.abc_emergency_watch_and_act` | Watch and Act (orange) or higher |
| `binary_sensor.abc_emergency_advice` | Advice (yellow) or higher |

## Automation Examples

### Emergency Warning Notification

```yaml
automation:
  - alias: "ABC Emergency Warning Alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.abc_emergency_emergency_warning
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "EMERGENCY WARNING"
          message: >
            {{ state_attr('sensor.abc_emergency_nearest_incident', 'headline') }}
            is {{ states('sensor.abc_emergency_nearest_incident') }}km away
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
        entity_id: sensor.abc_emergency_nearest_incident
        below: 20
    condition:
      - condition: state
        entity_id: sensor.abc_emergency_nearest_incident
        attribute: event_type
        state: "Bushfire"
    action:
      - service: notify.all_devices
        data:
          message: "Bushfire detected {{ states('sensor.abc_emergency_nearest_incident') }}km away!"
```

## Data Source

This integration uses data from [ABC Emergency](https://www.abc.net.au/emergency), which aggregates emergency information from state and territory emergency services across Australia.

**Note:** This is an unofficial integration and is not affiliated with or endorsed by the Australian Broadcasting Corporation.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
