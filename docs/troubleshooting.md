# Troubleshooting Guide

Solutions to common issues with ABC Emergency for Home Assistant.

<p align="center">
  <a href="https://my.home-assistant.io/redirect/logs/"><img src="https://my.home-assistant.io/badges/logs.svg" alt="View Logs"></a>
  <a href="https://my.home-assistant.io/redirect/developer_states/"><img src="https://my.home-assistant.io/badges/developer_states.svg" alt="Developer States"></a>
  <a href="https://my.home-assistant.io/redirect/repairs/"><img src="https://my.home-assistant.io/badges/repairs.svg" alt="Repairs"></a>
</p>

---

## Installation Issues

### Integration Not Found After Installation

**Symptom:** After installing via HACS, "ABC Emergency" doesn't appear when adding integrations.

**Solutions:**

1. **Restart Home Assistant**
   - HACS installations require a restart
   - Settings → System → Restart

2. **Check Installation Location**
   - The integration should be at `/config/custom_components/abcemergency/`
   - Verify the folder structure is correct

3. **Check for Errors in Logs**
   - Settings → System → Logs
   - Look for errors mentioning `abcemergency`

4. **Clear Browser Cache**
   - Sometimes the integration list is cached
   - Hard refresh (Ctrl+F5) or clear browser cache

### HACS Not Showing the Integration

**Symptom:** Can't find ABC Emergency in HACS even after adding as custom repository.

**Solutions:**

1. **Verify Custom Repository URL**
   - URL should be: `https://github.com/troykelly/homeassistant-abcemergency`
   - Category should be: Integration

2. **Refresh HACS**
   - HACS → Integrations → Three dots menu → Reload

3. **Check HACS Logs**
   - HACS has its own log accessible from its menu
   - Look for errors fetching the repository

---

## Configuration Issues

### Can't Select Location on Map

**Symptom:** The map picker doesn't respond or location can't be set.

**Solutions:**

1. **Check Browser Console**
   - Press F12 → Console tab
   - Look for JavaScript errors

2. **Try Manual Coordinates**
   - You can enter latitude/longitude directly
   - Use Google Maps to find coordinates

3. **Different Browser**
   - Try a different browser (Chrome, Firefox, Safari)
   - Some map features have browser-specific issues

### Person Entity Not Appearing

**Symptom:** When setting up Person Mode, no person entities appear in the dropdown.

**Solutions:**

1. **Verify Person Has Location**
   - Developer Tools → States
   - Search for `person.`
   - Check that your person has `latitude` and `longitude` attributes

2. **Assign Device Tracker to Person**
   - Settings → People → Select person
   - Add device trackers under "Devices"

3. **Verify Device Tracker is Updating**
   - The device tracker must be reporting GPS coordinates
   - Check the Companion App settings on the mobile device

---

## Entity Issues

### Entities Show "Unknown" or "Unavailable"

**Symptom:** Sensors show `unknown` or `unavailable` instead of values.

[![Open Developer Tools States](https://my.home-assistant.io/badges/developer_states.svg)](https://my.home-assistant.io/redirect/developer_states/)

**Solutions:**

1. **Wait for First Update**
   - After setup, data takes up to 5 minutes to populate
   - Check back after the first refresh cycle

2. **Check API Connectivity**
   - Developer Tools → Services
   - Call `homeassistant.update_entity` on any ABC Emergency sensor
   - Check logs for API errors

3. **Verify Internet Connectivity**
   - The integration requires internet access to `www.abc.net.au`
   - Check if the ABC Emergency website is accessible

4. **Check for API Changes**
   - Occasionally the ABC Emergency API may change
   - Check the GitHub repository for known issues

### Nearest Incident Shows Wrong Distance

**Symptom:** The distance to nearest incident seems incorrect.

**Solutions:**

1. **Verify Configured Location**
   - Go to Settings → Devices & Services → ABC Emergency
   - Check that latitude/longitude are correct

2. **Check Person Entity Location**
   - For Person Mode, verify the person entity's coordinates
   - Developer Tools → States → Search for your person

3. **Understand Distance Calculation**
   - Distance is calculated as-the-crow-flies (not road distance)
   - Large incidents may have centroids far from their edges

### Binary Sensors Not Triggering

**Symptom:** Automations based on binary sensors don't fire.

**Solutions:**

1. **Check Binary Sensor States**
   - Developer Tools → States
   - Search for `binary_sensor.abc_emergency_`
   - Verify the sensor transitions from `off` to `on`

2. **Verify Alert Level**
   - Binary sensors only turn on for nearby incidents (Zone/Person mode)
   - State mode uses state-wide alerts

3. **Test with Lower Thresholds**
   - Temporarily increase your alert radii
   - This can help determine if it's a threshold issue

---

## API and Connectivity

### "Unable to Fetch Data" Error

**Symptom:** Error in logs about failing to fetch emergency data.

**Solutions:**

1. **Check ABC Emergency Website**
   - Visit https://www.abc.net.au/emergency
   - If the website is down, the API won't work

2. **Check Network Connectivity**
   - Verify Home Assistant can reach external websites
   - Try `ping www.abc.net.au` from the host machine

3. **Check for Firewall/Proxy Issues**
   - Some networks block certain domains
   - Verify outbound HTTPS (port 443) is allowed

### Rate Limiting

**Symptom:** Occasional errors or delays in data updates.

**Solutions:**

The ABC Emergency API doesn't appear to have strict rate limits, but:

1. **Don't Lower Update Interval**
   - The 5-minute interval is appropriate
   - More frequent polling won't be more effective

2. **Check for Multiple Instances**
   - Many instances will multiply API calls
   - Consider consolidating if you have many

---

## Automation Issues

### Automations Not Triggering

**Symptom:** Automations using ABC Emergency entities don't run.

[![Open Automations](https://my.home-assistant.io/badges/automations.svg)](https://my.home-assistant.io/redirect/automations/)

**Solutions:**

1. **Check Automation is Enabled**
   - Settings → Automations & Scenes
   - Ensure the automation toggle is on

2. **Trace the Automation**
   - Open the automation → Three dots → Traces
   - See why it didn't trigger

3. **Verify Entity Names**
   - Entity IDs must match exactly
   - Check for typos in entity names

4. **Test Trigger Conditions**
   - Manually check if conditions would be true
   - Use Developer Tools → Template to test

### Template Errors in Notifications

**Symptom:** Notifications show template text instead of values, or error messages.

**Solutions:**

1. **Check Template Syntax**
   - Jinja2 templates are sensitive to syntax
   - Use Developer Tools → Template to test

2. **Handle Missing Attributes**
   - Attributes may not exist when no incidents are present
   - Use default filters: `{{ state_attr('sensor...', 'headline') | default('No incident') }}`

3. **Check Entity State**
   - If sensor is `unknown`, attributes won't exist
   - Add conditions to check sensor availability

**Example with error handling:**

```yaml
message: >
  {% if states('sensor.abc_emergency_home_nearest_incident') not in ['unknown', 'unavailable'] %}
    {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}
    is {{ states('sensor.abc_emergency_home_nearest_incident') }}km away
  {% else %}
    No active incidents
  {% endif %}
```

---

## Performance Issues

### Slow Dashboard Loading

**Symptom:** Dashboards with ABC Emergency entities load slowly.

**Solutions:**

1. **Limit Map Entities**
   - Geo-location entities can be numerous
   - Consider filtering by distance in custom cards

2. **Use History Exclusions**
   - Exclude ABC Emergency entities from history if not needed:
   ```yaml
   recorder:
     exclude:
       entity_globs:
         - geo_location.abc_emergency_*
   ```

### High Memory Usage

**Symptom:** Home Assistant memory usage increases over time.

**Solutions:**

1. **Check for Many Instances**
   - Each instance maintains its own data
   - Reduce instances if memory is limited

2. **Restart Periodically**
   - Schedule regular Home Assistant restarts if needed
   - This clears any accumulated memory

---

## Debug Logging

### Enable Debug Logs

To see detailed logs for troubleshooting:

```yaml
# In configuration.yaml
logger:
  default: warning
  logs:
    custom_components.abcemergency: debug
```

After adding, restart Home Assistant.

### View Logs

[![Open Logs](https://my.home-assistant.io/badges/logs.svg)](https://my.home-assistant.io/redirect/logs/)

1. **Via UI**
   - Settings → System → Logs
   - Filter by "abcemergency"

2. **Via File**
   - `/config/home-assistant.log`
   - Search for "abcemergency"

### What to Look For

| Log Pattern | Meaning |
|-------------|---------|
| `Fetching emergency data for...` | Normal update cycle |
| `Found X emergencies` | Successful data fetch |
| `Error fetching data` | API or network issue |
| `Coordinator update failed` | Update cycle problem |

---

## Diagnostic Information

### Download Diagnostics

[![Open Integrations](https://my.home-assistant.io/badges/integrations.svg)](https://my.home-assistant.io/redirect/integrations/)

Navigate to ABC Emergency, or manually:

1. Settings → Devices & Services → ABC Emergency
2. Click on your instance
3. Click "Download Diagnostics"

This file contains:
- Configuration (sensitive data redacted)
- Current sensor states
- Cached incident data
- Last update timestamp

**Include this when reporting issues.**

---

## Common Error Messages

### "Authentication failed"

This shouldn't occur as the API is public. If you see this:
- Clear the integration and re-add
- Check for network proxy issues

### "Connection timeout"

- Check internet connectivity
- ABC Emergency website may be temporarily unavailable
- Check for DNS issues

### "Unexpected response format"

- The API may have changed
- Check GitHub issues for reports
- Wait for an integration update

---

## Reporting Issues

If you can't resolve an issue:

1. **Search Existing Issues**
   - https://github.com/troykelly/homeassistant-abcemergency/issues

2. **Gather Information**
   - Home Assistant version
   - Integration version
   - Debug logs
   - Diagnostics download
   - Steps to reproduce

3. **Create New Issue**
   - Use the Bug Report template
   - Include all gathered information

---

## FAQ

<details>
<summary>Why does data update every 5 minutes?</summary>

The integration polls the ABC Emergency API every 5 minutes. This interval is fixed and cannot be changed.

**Why 5 minutes?**
1. **Source data freshness** - Emergency services typically update data every few minutes, so polling faster wouldn't give fresher data
2. **Responsible API usage** - The ABC Emergency service is free and public; we shouldn't overload it
3. **Battery/resource usage** - More frequent polling means more processing and network usage
4. **Emergency response** - 5 minutes is fast enough for emergency awareness while being responsible

**What if I need faster updates?**
For critical situations, rely on official emergency service apps which may push notifications in real-time. ABC Emergency integration is for awareness, not as a primary alert system.

</details>

### Q: Why is data only updated every 5 minutes?

The 5-minute interval balances:
- Timely emergency information
- Responsible use of the ABC Emergency service
- Typical update frequency of source data

Emergency data at the source typically updates every few minutes, so more frequent polling wouldn't provide significantly fresher data.

### Q: Can I change the update interval?

No, the update interval is fixed at 5 minutes to ensure consistent, responsible behavior across all installations.

### Q: Why are there no incidents showing?

During calm periods, there may be few or no emergency incidents. Check the ABC Emergency website to verify current activity in your area.

### Q: Does this work outside Australia?

No. The ABC Emergency service only covers Australia. The integration requires Australian coordinates to be configured.

### Q: Is my data sent anywhere?

No. The integration only:
- Fetches public data from ABC Emergency
- Processes it locally in your Home Assistant
- No data is sent from your system

---

## Next Steps

- [Getting Started](getting-started.md) - Initial setup guide
- [Configuration](configuration.md) - Configuration options
- [Entities Reference](entities.md) - Entity documentation
- [GitHub Issues](https://github.com/troykelly/homeassistant-abcemergency/issues) - Report bugs
