# ABC Emergency Documentation

Welcome to the ABC Emergency for Home Assistant documentation.

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=troykelly&repository=homeassistant-abcemergency&category=integration"><img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Add to HACS"></a>
  <a href="https://my.home-assistant.io/redirect/config_flow_start/?domain=abcemergency"><img src="https://my.home-assistant.io/badges/config_flow_start.svg" alt="Add Integration"></a>
</p>

---

## Quick Navigation

### Getting Started

| Guide | Description |
|-------|-------------|
| [Getting Started](getting-started.md) | Installation, first-time setup, and verification |
| [Configuration](configuration.md) | All configuration options and modes explained |

### Using the Integration

| Guide | Description |
|-------|-------------|
| [Entities Reference](entities.md) | Complete list of sensors and their attributes |
| [Automations](automations.md) | Ready-to-use automation examples and blueprints |
| [Containment Safety Guide](containment-safety.md) | **Critical:** Alerts when you're inside emergency zones |
| [Notifications](notifications.md) | Mobile alerts, critical notifications, TTS |
| [Scripts](scripts.md) | Emergency briefings and scripts |
| [Dashboard Maps](dashboard-maps.md) | Map card configuration |

### Advanced & Troubleshooting

| Guide | Description |
|-------|-------------|
| [Advanced Usage](advanced.md) | Templates, Node-RED, AppDaemon |
| [Troubleshooting](troubleshooting.md) | Common issues and solutions |
| [FAQ](faq.md) | Frequently asked questions |
| [Glossary](glossary.md) | Term definitions |

### Developer Documentation

| Guide | Description |
|-------|-------------|
| [API Reference](api-reference.md) | ABC Emergency API documentation |
| [API Types](api-types.md) | TypedDict definitions |

---

## Start Here

**New to ABC Emergency?** Start with [Getting Started](getting-started.md) for installation instructions.

**Already installed?** Jump to [Automations](automations.md) to set up alerts.

**Having issues?** Check [Troubleshooting](troubleshooting.md) for solutions.

---

## Monitoring Modes

ABC Emergency supports three ways to monitor emergencies:

| Mode | Best For | Description |
|------|----------|-------------|
| **State Mode** | Overview | Monitor all incidents in a state/territory |
| **Zone Mode** | Fixed locations | Alerts within radius of home, office, etc. |
| **Person Mode** | Family safety | Track alerts near people as they move |

---

## Point-in-Polygon Containment Detection

Zone and Person modes can detect when you're not just *near* an emergency, but actually **inside** the warning zone boundary:

| Type | Meaning | Example |
|------|---------|---------|
| **Proximity** | Within X km of incident | "Bushfire 15km away" |
| **Containment** | Inside polygon boundary | "You are INSIDE the bushfire warning zone" |

**This is a life-safety feature.** Being inside an emergency zone is fundamentally different from being nearby.

See the **[Containment Safety Guide](containment-safety.md)** for comprehensive documentation, blueprints, and automations.

Quick links:
- [Containment Binary Sensors](entities.md#containment-binary-sensors-zoneperson-mode-only)
- [Containment Events](entities.md#containment-events)
- [Containment Automations](automations.md#containment-based-automations)

---

## Australian Warning System

This integration uses the official [Australian Warning System](https://www.australianwarningsystem.com.au/) levels:

| Level | Color | Meaning |
|-------|-------|---------|
| **Emergency Warning** | Red | Act immediately - you may be in danger |
| **Watch and Act** | Orange | Take action now - conditions changing |
| **Advice** | Yellow | Stay informed - incident occurring |

---

## Need Help?

- [Troubleshooting Guide](troubleshooting.md) - Common issues and solutions
- [GitHub Issues](https://github.com/troykelly/homeassistant-abcemergency/issues) - Report bugs or request features
- [CLAUDE.md](../CLAUDE.md) - Developer documentation
