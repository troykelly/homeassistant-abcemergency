# Frequently Asked Questions

Common questions about ABC Emergency for Home Assistant.

---

## Installation & Setup

### Why isn't ABC Emergency appearing after I installed it from HACS?

You need to restart Home Assistant after installing from HACS. Go to **Settings** -> **System** -> **Restart**.

<details>
<summary>Still not working?</summary>

Check these common issues:
1. Clear your browser cache (Ctrl+F5)
2. Verify the folder exists at `/config/custom_components/abcemergency/`
3. Check logs for errors

</details>

### Do I need to restart Home Assistant after installation?

Yes. All custom component installations require a Home Assistant restart before they appear in the integrations list.

### Can I have multiple ABC Emergency instances?

Yes! You can add multiple instances to monitor different areas. Common setups include:
- One State instance for overview + Zone instances for specific locations
- Multiple Zone instances for home, office, and holiday house
- Person instances for each family member

[![Add Another Instance](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=abcemergency)

---

## Functionality

### Why does data only update every 5 minutes?

The 5-minute polling interval balances timely emergency information with responsible API usage. Emergency services typically update data every few minutes anyway, so faster polling wouldn't provide significantly fresher data.

The interval cannot be changed - this ensures consistent, responsible behavior across all installations.

### Does this work outside Australia?

No. ABC Emergency only covers Australia. The data comes from Australian state and territory emergency services and is aggregated by the ABC.

### What's the difference between Zone and Person mode?

| Mode | Location Source | Best For |
|------|-----------------|----------|
| **Zone Mode** | Fixed coordinates you configure | Monitoring your home, office, or property |
| **Person Mode** | Real-time GPS from a person entity | Tracking family safety as they travel |

### Why are there no incidents showing?

During calm periods (especially outside fire season), there may be few or no emergency incidents in your area. Check [ABC Emergency](https://www.abc.net.au/emergency) to verify current activity.

### Is my data sent anywhere?

No. The integration only:
- Fetches public data from ABC Emergency
- Processes it locally in your Home Assistant
- No data is sent from your system to any external service

---

## Entities

### Why is the nearest incident distance different from what I see on ABC Emergency website?

Distance is calculated as-the-crow-flies (straight line) from your configured location to the incident centroid. This may differ from:
- Road distances shown on some services
- Distances to the edge of large incidents (we calculate to the center)
- Your actual location if not precisely configured

### What does it mean when sensors show 'unknown'?

Sensors show `unknown` when:
1. Data hasn't been fetched yet (wait 5 minutes after setup)
2. There's no data available (e.g., no nearest incident when none exist)
3. There's a connection problem with the ABC Emergency API

### How do I know which entity to use in automations?

| Purpose | Entity to Use |
|---------|--------------|
| Trigger on any warning | `binary_sensor.*_advice` |
| Trigger on urgent warnings | `binary_sensor.*_watch_and_act` |
| Trigger on critical warnings | `binary_sensor.*_emergency_warning` |
| Check distance to nearest | `sensor.*_nearest_incident` |
| Count incidents by type | `sensor.*_bushfires`, `*_floods`, `*_storms` |

---

## Integration

### Can I change the update interval?

No. The 5-minute update interval is fixed and cannot be configured. This ensures responsible use of the ABC Emergency service.

### Does this integrate with other emergency services?

This integration specifically uses ABC Emergency data, which aggregates information from all Australian state and territory emergency services. It does not directly integrate with:
- State emergency service apps
- Bureau of Meteorology
- Other third-party services

### Can I use this with Apple HomeKit?

Yes, indirectly. Binary sensors can be exposed to HomeKit through Home Assistant's HomeKit integration, allowing HomeKit automations to trigger on ABC Emergency alerts.

---

## Privacy & Data

### Where does the data come from?

Data comes from [ABC Emergency](https://www.abc.net.au/emergency), which aggregates emergency information from all Australian state and territory emergency services.

### Is the ABC Emergency API official?

The API is not officially documented or supported by the ABC. This integration reverse-engineered the public API used by the ABC Emergency website. The API may change without notice.

### Is this integration affiliated with the ABC?

**No.** This is an independent community project. It is NOT authorised, endorsed, or affiliated with the Australian Broadcasting Corporation.

---

## Still Have Questions?

- Check the [Troubleshooting Guide](troubleshooting.md)
- Search [GitHub Issues](https://github.com/troykelly/homeassistant-abcemergency/issues)
- Create a new issue if your question isn't answered
