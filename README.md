<p align="center">
  <img src="https://github.com/troykelly/homeassistant-abcemergency/blob/70d4d2ecacfc94bf93ea839b5303861445a27e36/images/logo.png" alt="ABC Emergency Logo">
</p>

<h1 align="center">ABC Emergency for Home Assistant</h1>

<p align="center">
  <strong>Real-time Australian emergency alerts in your smart home</strong>
</p>

<p align="center">
  <a href="https://github.com/troykelly/homeassistant-abcemergency/releases"><img src="https://img.shields.io/github/release/troykelly/homeassistant-abcemergency.svg?style=flat-square" alt="GitHub Release"></a>
  <a href="https://github.com/troykelly/homeassistant-abcemergency/commits/main"><img src="https://img.shields.io/github/commit-activity/y/troykelly/homeassistant-abcemergency.svg?style=flat-square" alt="GitHub Activity"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/troykelly/homeassistant-abcemergency.svg?style=flat-square" alt="License"></a>
  <a href="https://hacs.xyz"><img src="https://img.shields.io/badge/HACS-Custom-orange.svg?style=flat-square" alt="HACS"></a>
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> &bull;
  <a href="docs/getting-started.md">Installation Guide</a> &bull;
  <a href="docs/automations.md">Automations</a> &bull;
  <a href="docs/troubleshooting.md">Troubleshooting</a>
</p>

---

> **Important:** This integration is **NOT** authorised, endorsed, or affiliated with the Australian Broadcasting Corporation (ABC). This is an independent community project that uses publicly available data from [ABC Emergency](https://www.abc.net.au/emergency) to help Australians stay informed during emergencies.

---

## Why ABC Emergency for Home Assistant?

When bushfires, floods, or storms threaten your home, every minute counts. This integration brings Australia's most comprehensive emergency information service directly into your smart home, enabling:

- **Instant mobile alerts** when emergencies occur near your home
- **Tiered notifications** based on Australian Warning System levels
- **Family safety monitoring** - track alerts near loved ones as they travel
- **Smart home automation** - trigger lights, sirens, or announcements during emergencies
- **Multi-location awareness** - monitor your home, workplace, and holiday house simultaneously

---

## Key Features

### Three Monitoring Modes

| Mode | Best For | How It Works |
|------|----------|--------------|
| **State Mode** | Overview of all emergencies | Monitors every incident in a state/territory |
| **Zone Mode** | Protecting fixed locations | Alerts within configurable radius of your home, office, etc. |
| **Person Mode** | Family safety | Follows a person's location as they move |

### Australian Warning System Integration

This integration uses the official [Australian Warning System](https://www.australianwarningsystem.com.au/) levels:

| Level | Color | Meaning | Your Action |
|-------|-------|---------|-------------|
| **Emergency Warning** | Red | You may be in danger | Act immediately to protect yourself |
| **Watch and Act** | Orange | Conditions changing | Take action now to prepare |
| **Advice** | Yellow | Incident occurring | Stay informed and monitor conditions |

### Comprehensive Incident Coverage

- Bushfires and grass fires
- Floods and storms
- Severe weather and cyclones
- Earthquakes
- Extreme heat and heatwaves
- Structure fires
- And more...

### Smart Alerting

- **Per-incident events** - Get notified for each new incident as it appears
- **Per-incident-type radius** - Bushfires alert at 50km, structure fires at 10km
- **Nearest incident tracking** - Know exactly how far away the closest threat is
- **Binary sensors** - Simple on/off triggers for each warning level
- **Geo-location entities** - See all incidents on your Home Assistant map

---

## Quick Start

### 1. Install via HACS

1. Open HACS in Home Assistant
2. Click the three dots menu → **Custom repositories**
3. Add: `https://github.com/troykelly/homeassistant-abcemergency`
4. Select category: **Integration**
5. Click **Install**
6. **Restart Home Assistant**

### 2. Add the Integration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **ABC Emergency**
4. Follow the setup wizard

### 3. Create Your First Automation

```yaml
automation:
  - alias: "Emergency Warning Alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.abc_emergency_home_emergency_warning
        to: "on"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "EMERGENCY WARNING"
          message: >
            {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}
            is {{ states('sensor.abc_emergency_home_nearest_incident') }}km away
          data:
            priority: high
            channel: emergency
```

**That's it!** You'll now receive critical alerts when emergencies threaten your home.

---

## Documentation

| Guide | Description |
|-------|-------------|
| [Getting Started](docs/getting-started.md) | Detailed installation and first-time setup |
| [Configuration](docs/configuration.md) | All configuration options explained |
| [Entities Reference](docs/entities.md) | Complete list of sensors and their attributes |
| [Automations](docs/automations.md) | Ready-to-use automation examples |
| [Events](docs/automations.md#event-based-automations) | Event-based per-incident alerting |
| [Notifications](docs/notifications.md) | Mobile alerts, critical notifications, TTS |
| [Scripts](docs/scripts.md) | Emergency briefings, evacuation checklists |
| [Troubleshooting](docs/troubleshooting.md) | Common issues and solutions |
| [Advanced Usage](docs/advanced.md) | Templates, Node-RED, AppDaemon |

---

## Example Automations

### Tiered Notifications by Warning Level

```yaml
automation:
  # Advice level - informational notification
  - alias: "ABC Emergency - Advice Notification"
    trigger:
      - platform: state
        entity_id: binary_sensor.abc_emergency_home_advice
        to: "on"
    condition:
      - condition: state
        entity_id: binary_sensor.abc_emergency_home_watch_and_act
        state: "off"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Emergency Advice"
          message: >
            {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}
            ({{ states('sensor.abc_emergency_home_nearest_incident') }}km away)

  # Watch and Act - more urgent
  - alias: "ABC Emergency - Watch and Act"
    trigger:
      - platform: state
        entity_id: binary_sensor.abc_emergency_home_watch_and_act
        to: "on"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "WATCH AND ACT"
          message: >
            Take action now! {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}
            is {{ states('sensor.abc_emergency_home_nearest_incident') }}km away
          data:
            priority: high

  # Emergency Warning - critical
  - alias: "ABC Emergency - Emergency Warning"
    trigger:
      - platform: state
        entity_id: binary_sensor.abc_emergency_home_emergency_warning
        to: "on"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "EMERGENCY WARNING"
          message: >
            Act immediately! {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}
            is {{ states('sensor.abc_emergency_home_nearest_incident') }}km away
          data:
            priority: critical
            channel: alarm
```

### Family Member Safety Alert

```yaml
automation:
  - alias: "Family Member Near Emergency"
    trigger:
      - platform: state
        entity_id: binary_sensor.abc_emergency_dad_active_alert
        to: "on"
    action:
      - service: notify.family_group
        data:
          title: "Emergency Near Dad"
          message: >
            There's an active emergency near Dad's location.
            Distance: {{ states('sensor.abc_emergency_dad_nearest_incident') }}km
            Type: {{ state_attr('sensor.abc_emergency_dad_nearest_incident', 'event_type') }}
```

### New Incident Event Alert

Get notified for each new incident as it appears:

```yaml
automation:
  - alias: "New Emergency Incident"
    trigger:
      - platform: event
        event_type: abc_emergency_new_incident
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "{{ trigger.event.data.event_type }}: {{ trigger.event.data.alert_text }}"
          message: >
            {{ trigger.event.data.headline }}
            {% if trigger.event.data.distance_km %}
            ({{ trigger.event.data.distance_km | round(1) }}km {{ trigger.event.data.direction }})
            {% endif %}
```

See [Automations Guide](docs/automations.md) for more examples including TTS announcements, smart light alerts, event-based alerting, and quiet hours handling.

---

## Entities Created

Each instance creates a device with these entities:

### Sensors

| Entity | Description |
|--------|-------------|
| `sensor.abc_emergency_*_incidents_total` | Total active incidents |
| `sensor.abc_emergency_*_incidents_nearby` | Incidents within your configured radii |
| `sensor.abc_emergency_*_nearest_incident` | Distance (km) to nearest incident |
| `sensor.abc_emergency_*_highest_alert_level` | Highest warning level active |
| `sensor.abc_emergency_*_bushfires` | Active bushfire count |
| `sensor.abc_emergency_*_floods` | Active flood count |
| `sensor.abc_emergency_*_storms` | Active storm count |

### Binary Sensors

| Entity | Meaning |
|--------|---------|
| `binary_sensor.abc_emergency_*_active_alert` | Any alert active |
| `binary_sensor.abc_emergency_*_emergency_warning` | Red level (highest) |
| `binary_sensor.abc_emergency_*_watch_and_act` | Orange level or higher |
| `binary_sensor.abc_emergency_*_advice` | Yellow level or higher |

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

This project follows:
- Test-Driven Development (TDD)
- Issue-Driven Development (all changes require a linked GitHub issue)
- Strict type safety (no `Any` types)

---

## The Story Behind This Integration

This integration was created in early December 2025 when bushfires broke out near a friend's house in Woy Woy, NSW. We needed a way to easily add alerting to our chosen family group so everyone could stay informed and safe.

What started as a quick hack to help friends became a full-featured integration that we hope helps other Australians protect their homes and loved ones.

---

## Acknowledgment of Country

This code was written on the land of the Gadigal and Wangal peoples of the Eora Nation. We pay our respects to Elders past, present, and emerging, and acknowledge that sovereignty was never ceded.

In the spirit of this integration's purpose - helping communities stay safe during emergencies - we acknowledge the tens of thousands of years of land management by First Nations peoples, including the use of cultural burning practices that helped maintain the health of Country.

---

## Data Source & Disclaimer

This integration uses publicly available data from [ABC Emergency](https://www.abc.net.au/emergency), which aggregates emergency information from state and territory emergency services across Australia.

**This is NOT an official ABC product.** The ABC Emergency website states:

> The information displayed on this page is assembled from multiple data sources and may not reflect the most up-to-date information available. For emergency information, contact your local emergency services.

**Always follow official emergency service instructions.** This integration is a convenience tool and should not be your only source of emergency information. In a life-threatening emergency, call **000**.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <sub>Made with care for the Australian community</sub>
</p>
