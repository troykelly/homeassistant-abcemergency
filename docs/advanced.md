# Advanced Usage Guide

Power user features, template sensors, and third-party integrations for ABC Emergency.

---

## Template Sensors

Create custom sensors derived from ABC Emergency data.

### Bushfire Risk Level Sensor

Combine multiple factors into a risk level:

```yaml
template:
  - sensor:
      - name: "Bushfire Risk Level"
        unique_id: bushfire_risk_level
        state: >
          {% set bushfires = states('sensor.abc_emergency_home_bushfires') | int(0) %}
          {% set nearest = states('sensor.abc_emergency_home_nearest_incident') | float(999) %}
          {% set is_bushfire = state_attr('sensor.abc_emergency_home_nearest_incident', 'event_type') == 'Bushfire' %}
          {% set level = states('sensor.abc_emergency_home_highest_alert_level') %}

          {% if level == 'Emergency' and is_bushfire and nearest < 20 %}
            Extreme
          {% elif level in ['Emergency', 'Watch and Act'] and is_bushfire and nearest < 50 %}
            Very High
          {% elif bushfires > 0 and nearest < 75 %}
            High
          {% elif bushfires > 0 %}
            Moderate
          {% else %}
            Low
          {% endif %}
        icon: >
          {% if is_state('sensor.bushfire_risk_level', 'Extreme') %}
            mdi:fire-alert
          {% elif is_state('sensor.bushfire_risk_level', 'Very High') %}
            mdi:fire
          {% elif is_state('sensor.bushfire_risk_level', 'High') %}
            mdi:fire
          {% else %}
            mdi:fire-off
          {% endif %}
```

### Nearest Incident Summary Sensor

A single sensor with formatted summary:

```yaml
template:
  - sensor:
      - name: "Emergency Summary"
        unique_id: emergency_summary
        state: >
          {% if is_state('binary_sensor.abc_emergency_home_active_alert', 'on') %}
            {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'event_type') }}
            {{ states('sensor.abc_emergency_home_nearest_incident') }}km
            {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'direction') }}
          {% else %}
            No active alerts
          {% endif %}
        attributes:
          headline: >
            {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}
          alert_level: >
            {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'alert_level') }}
          url: "https://www.abc.net.au/emergency"
```

### Family Safety Status Sensor

Aggregate family member safety:

```yaml
template:
  - sensor:
      - name: "Family Emergency Status"
        unique_id: family_emergency_status
        state: >
          {% set alerts = namespace(count=0) %}
          {% if is_state('binary_sensor.abc_emergency_mum_active_alert', 'on') %}
            {% set alerts.count = alerts.count + 1 %}
          {% endif %}
          {% if is_state('binary_sensor.abc_emergency_dad_active_alert', 'on') %}
            {% set alerts.count = alerts.count + 1 %}
          {% endif %}
          {% if is_state('binary_sensor.abc_emergency_child_active_alert', 'on') %}
            {% set alerts.count = alerts.count + 1 %}
          {% endif %}

          {% if alerts.count == 0 %}
            All Clear
          {% elif alerts.count == 1 %}
            1 Member in Alert Zone
          {% else %}
            {{ alerts.count }} Members in Alert Zones
          {% endif %}
        attributes:
          mum_status: >
            {{ 'Alert' if is_state('binary_sensor.abc_emergency_mum_active_alert', 'on') else 'Clear' }}
          dad_status: >
            {{ 'Alert' if is_state('binary_sensor.abc_emergency_dad_active_alert', 'on') else 'Clear' }}
          child_status: >
            {{ 'Alert' if is_state('binary_sensor.abc_emergency_child_active_alert', 'on') else 'Clear' }}
```

---

## Custom Lovelace Cards

### Emergency Status Card

```yaml
type: vertical-stack
cards:
  - type: markdown
    content: |
      # Emergency Status
      **Highest Alert:** {{ states('sensor.abc_emergency_home_highest_alert_level') }}

      {% if is_state('binary_sensor.abc_emergency_home_active_alert', 'on') %}
      ## ⚠️ Active Alert

      **{{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}**

      | | |
      |---|---|
      | Type | {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'event_type') }} |
      | Distance | {{ states('sensor.abc_emergency_home_nearest_incident') }} km |
      | Direction | {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'direction') }} |
      | Level | {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'alert_level') }} |
      {% else %}
      ✅ No active emergencies near your location.
      {% endif %}

  - type: entities
    entities:
      - entity: sensor.abc_emergency_home_incidents_total
      - entity: sensor.abc_emergency_home_incidents_nearby
      - entity: sensor.abc_emergency_home_bushfires
      - entity: sensor.abc_emergency_home_floods
      - entity: sensor.abc_emergency_home_storms
```

### Conditional Alert Banner

```yaml
type: conditional
conditions:
  - entity: binary_sensor.abc_emergency_home_emergency_warning
    state: "on"
card:
  type: markdown
  content: |
    # 🚨 EMERGENCY WARNING 🚨

    **{{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}**
    is **{{ states('sensor.abc_emergency_home_nearest_incident') }}km** away!

    **ACT IMMEDIATELY**
  style: |
    ha-card {
      background-color: #d31717;
      color: white;
    }
```

### Warning Level Gauge

Using a gauge to show proximity:

```yaml
type: gauge
entity: sensor.abc_emergency_home_nearest_incident
name: Nearest Emergency
min: 0
max: 100
severity:
  green: 50
  yellow: 20
  red: 10
needle: true
```

---

## Node-RED Integration

### Basic Alert Flow

```json
[
    {
        "id": "abc_emergency_trigger",
        "type": "server-state-changed",
        "name": "Emergency Warning",
        "server": "",
        "entityid": "binary_sensor.abc_emergency_home_emergency_warning",
        "entityidtype": "exact",
        "outputonlyonchange": true,
        "outputproperties": [
            {
                "property": "payload",
                "propertyType": "msg",
                "value": "",
                "valueType": "entityState"
            }
        ],
        "x": 150,
        "y": 100,
        "wires": [["filter_on"]]
    },
    {
        "id": "filter_on",
        "type": "switch",
        "name": "Filter On",
        "property": "payload",
        "rules": [
            {"t": "eq", "v": "on", "vt": "str"}
        ],
        "x": 350,
        "y": 100,
        "wires": [["get_details"]]
    },
    {
        "id": "get_details",
        "type": "api-current-state",
        "name": "Get Incident Details",
        "server": "",
        "outputs": 1,
        "entityid": "sensor.abc_emergency_home_nearest_incident",
        "x": 550,
        "y": 100,
        "wires": [["format_message"]]
    },
    {
        "id": "format_message",
        "type": "function",
        "name": "Format Message",
        "func": "msg.payload = {\n    title: 'EMERGENCY WARNING',\n    message: msg.data.attributes.headline + ' is ' + msg.data.state + 'km away!',\n    data: {\n        priority: 'critical'\n    }\n};\nreturn msg;",
        "x": 750,
        "y": 100,
        "wires": [["notify"]]
    },
    {
        "id": "notify",
        "type": "api-call-service",
        "name": "Send Notification",
        "server": "",
        "service": "notify.mobile_app_phone",
        "x": 950,
        "y": 100,
        "wires": [[]]
    }
]
```

### Distance-Based Escalation Flow

```json
[
    {
        "id": "distance_monitor",
        "type": "server-state-changed",
        "name": "Distance Changed",
        "entityid": "sensor.abc_emergency_home_nearest_incident",
        "x": 150,
        "y": 200,
        "wires": [["distance_check"]]
    },
    {
        "id": "distance_check",
        "type": "switch",
        "name": "Check Distance",
        "property": "payload",
        "rules": [
            {"t": "lt", "v": "5", "vt": "num"},
            {"t": "lt", "v": "15", "vt": "num"},
            {"t": "lt", "v": "30", "vt": "num"}
        ],
        "x": 350,
        "y": 200,
        "wires": [["critical"], ["urgent"], ["warning"]]
    }
]
```

---

## AppDaemon Integration

### Emergency Monitor App

Create `apps/emergency_monitor.py`:

```python
import appdaemon.plugins.hass.hassapi as hass
from datetime import datetime


class EmergencyMonitor(hass.Hass):
    """Monitor ABC Emergency and take actions."""

    def initialize(self):
        """Initialize the app."""
        self.log("Emergency Monitor starting")

        # Monitor emergency warning sensor
        self.listen_state(
            self.emergency_warning_changed,
            "binary_sensor.abc_emergency_home_emergency_warning",
        )

        # Monitor distance changes
        self.listen_state(
            self.distance_changed,
            "sensor.abc_emergency_home_nearest_incident",
        )

        # Track last notification time to avoid spam
        self.last_notification = {}

    def emergency_warning_changed(self, entity, attribute, old, new, kwargs):
        """Handle emergency warning state changes."""
        if new == "on":
            self.handle_emergency_warning()
        elif new == "off" and old == "on":
            self.handle_all_clear()

    def handle_emergency_warning(self):
        """React to emergency warning."""
        nearest = self.get_state("sensor.abc_emergency_home_nearest_incident")
        headline = self.get_state(
            "sensor.abc_emergency_home_nearest_incident",
            attribute="headline"
        )
        event_type = self.get_state(
            "sensor.abc_emergency_home_nearest_incident",
            attribute="event_type"
        )

        # Turn on emergency lights
        self.turn_on("light.living_room", brightness=255, color_name="red")

        # Flash lights
        for _ in range(3):
            self.turn_off("light.front_porch")
            self.run_in(lambda *args: self.turn_on("light.front_porch", color_name="red"), 0.5)
            self.run_in(lambda *args: self.turn_off("light.front_porch"), 1.0)

        # Send critical notification
        self.call_service(
            "notify/mobile_app_phone",
            title="EMERGENCY WARNING",
            message=f"{event_type}: {headline} is {nearest}km away!",
            data={"priority": "critical"},
        )

        # Announce on speakers
        self.call_service(
            "tts/google_translate_say",
            entity_id="media_player.living_room_speaker",
            message=f"Emergency Warning! {event_type} is {nearest} kilometres away. Take action immediately!",
        )

    def handle_all_clear(self):
        """Handle when emergency warning clears."""
        self.turn_on("light.living_room", color_temp_kelvin=3000, brightness=128)

        self.call_service(
            "notify/mobile_app_phone",
            title="All Clear",
            message="Emergency warning has been cleared. Stay vigilant.",
        )

    def distance_changed(self, entity, attribute, old, new, kwargs):
        """Handle distance changes for escalating alerts."""
        try:
            old_dist = float(old) if old not in ["unknown", "unavailable", None] else 999
            new_dist = float(new) if new not in ["unknown", "unavailable", None] else 999
        except (ValueError, TypeError):
            return

        # Only alert if getting closer
        if new_dist >= old_dist:
            return

        # Rate limit notifications
        now = datetime.now()
        threshold = None

        if new_dist < 5 and old_dist >= 5:
            threshold = "5km"
        elif new_dist < 15 and old_dist >= 15:
            threshold = "15km"
        elif new_dist < 30 and old_dist >= 30:
            threshold = "30km"

        if threshold:
            last = self.last_notification.get(threshold)
            if last and (now - last).total_seconds() < 1800:  # 30 min cooldown
                return

            self.last_notification[threshold] = now
            self.send_distance_alert(new_dist, threshold)

    def send_distance_alert(self, distance, threshold):
        """Send distance-based alert."""
        headline = self.get_state(
            "sensor.abc_emergency_home_nearest_incident",
            attribute="headline"
        )

        priority = "critical" if threshold == "5km" else "high"

        self.call_service(
            "notify/mobile_app_phone",
            title=f"Emergency Now Within {threshold}",
            message=f"{headline} is {distance:.1f}km away and approaching!",
            data={"priority": priority},
        )
```

Configure in `apps/apps.yaml`:

```yaml
emergency_monitor:
  module: emergency_monitor
  class: EmergencyMonitor
```

---

## REST API Access

Access ABC Emergency data via Home Assistant's REST API.

### Get Sensor State

```bash
curl -X GET \
  -H "Authorization: Bearer YOUR_LONG_LIVED_TOKEN" \
  -H "Content-Type: application/json" \
  http://your-ha-instance:8123/api/states/sensor.abc_emergency_home_nearest_incident
```

### Trigger Update

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_LONG_LIVED_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "sensor.abc_emergency_home_incidents_total"}' \
  http://your-ha-instance:8123/api/services/homeassistant/update_entity
```

---

## WebSocket Integration

### Subscribe to State Changes

```javascript
const socket = new WebSocket('ws://your-ha-instance:8123/api/websocket');

socket.onopen = () => {
  // Authenticate
  socket.send(JSON.stringify({
    type: 'auth',
    access_token: 'YOUR_LONG_LIVED_TOKEN'
  }));
};

socket.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'auth_ok') {
    // Subscribe to emergency sensor
    socket.send(JSON.stringify({
      id: 1,
      type: 'subscribe_events',
      event_type: 'state_changed'
    }));
  }

  if (data.type === 'event' && data.event.data.entity_id.startsWith('abc_emergency')) {
    console.log('Emergency update:', data.event.data);
  }
};
```

---

## Database Queries

Query ABC Emergency history from the Home Assistant database.

### SQLite Query Example

```sql
-- Get all emergency warning activations
SELECT
  datetime(last_changed, 'localtime') as time,
  state
FROM states
WHERE entity_id = 'binary_sensor.abc_emergency_home_emergency_warning'
  AND state IN ('on', 'off')
ORDER BY last_changed DESC
LIMIT 50;

-- Get nearest incident distance over time
SELECT
  datetime(last_changed, 'localtime') as time,
  state as distance_km,
  json_extract(attributes, '$.headline') as headline
FROM states
WHERE entity_id = 'sensor.abc_emergency_home_nearest_incident'
  AND state NOT IN ('unknown', 'unavailable')
ORDER BY last_changed DESC
LIMIT 100;
```

---

## Integration with External Services

### IFTTT Integration

Create applets triggered by ABC Emergency:

1. **Trigger:** Webhook (receive from HA)
2. **Action:** SMS, email, smart home action

In Home Assistant:

```yaml
automation:
  - alias: "IFTTT Emergency Alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.abc_emergency_home_emergency_warning
        to: "on"
    action:
      - service: ifttt.trigger
        data:
          event: emergency_warning
          value1: "{{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}"
          value2: "{{ states('sensor.abc_emergency_home_nearest_incident') }}"
```

### Pushover with Sounds

```yaml
automation:
  - alias: "Pushover Emergency"
    trigger:
      - platform: state
        entity_id: binary_sensor.abc_emergency_home_emergency_warning
        to: "on"
    action:
      - service: notify.pushover
        data:
          title: "EMERGENCY"
          message: "{{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}"
          data:
            sound: siren
            priority: 2
            retry: 30
            expire: 3600
```

---

## Statistics and Long-term Storage

### InfluxDB Export

Configure for long-term analytics:

```yaml
influxdb:
  host: localhost
  include:
    entities:
      - sensor.abc_emergency_home_incidents_total
      - sensor.abc_emergency_home_nearest_incident
      - sensor.abc_emergency_home_bushfires
```

### Grafana Dashboard

Query examples for Grafana:

```sql
-- Incident count over time
SELECT mean("value")
FROM "sensor.abc_emergency_home_incidents_total"
WHERE $timeFilter
GROUP BY time($interval)

-- Emergency warning activations
SELECT count("value")
FROM "binary_sensor.abc_emergency_home_emergency_warning"
WHERE "value" = 'on' AND $timeFilter
GROUP BY time(1d)
```

---

## Performance Optimization

### Exclude from Recorder

Reduce database size:

```yaml
recorder:
  exclude:
    entity_globs:
      - geo_location.abc_emergency_*
    entities:
      - sensor.abc_emergency_nsw_incidents_total  # If you don't need history
```

### Exclude from Logbook

```yaml
logbook:
  exclude:
    entity_globs:
      - geo_location.abc_emergency_*
```

---

## Security Considerations

### Sensitive Data

- ABC Emergency data is public
- Your location data stays local
- No authentication required for the API

### Automation Safety

Add confirmation for destructive actions:

```yaml
automation:
  - alias: "Emergency Mode with Confirmation"
    trigger:
      - platform: state
        entity_id: binary_sensor.abc_emergency_home_emergency_warning
        to: "on"
    action:
      - service: notify.mobile_app_phone
        data:
          title: "Activate Emergency Mode?"
          message: "Tap to confirm"
          data:
            actions:
              - action: "ACTIVATE_EMERGENCY"
                title: "Activate"
              - action: "DISMISS"
                title: "Dismiss"
```

---

## Next Steps

- [Automations Guide](automations.md) - Automation examples
- [Scripts Guide](scripts.md) - Script examples
- [Troubleshooting](troubleshooting.md) - Common issues
- [Contributing](../CONTRIBUTING.md) - How to contribute
