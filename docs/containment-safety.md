# Containment Detection Safety Guide

**Comprehensive guide to keeping you and your family safe when inside emergency zones.**

<p align="center">
  <a href="https://my.home-assistant.io/redirect/blueprints/"><img src="https://my.home-assistant.io/badges/blueprints.svg" alt="View Blueprints"></a>
  <a href="https://my.home-assistant.io/redirect/automations/"><img src="https://my.home-assistant.io/badges/automations.svg" alt="View Automations"></a>
</p>

---

## Understanding Containment Detection

### Proximity vs Containment: A Critical Difference

Traditional emergency alerts tell you an incident is "15km away." But what if you're actually **inside** the warning zone, even though the incident's center is far away?

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                        Emergency Polygon                        │
│                                                                 │
│                              ★                                  │
│                         (Centroid)                              │
│                         "15km away"                             │
│                                                                 │
│                                              🏠                 │
│                                          (Your Home)            │
│                                       INSIDE the zone           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Containment detection tells you when you're inside the actual boundary of an emergency zone, not just near its center.**

This matters because:
- Large bushfire zones can span 50+ kilometers
- Weather warnings cover entire regions
- Flood zones follow river systems with irregular shapes
- You could be "50km from the center" but still directly affected

---

## Importable Blueprints

One-click import these safety blueprints into your Home Assistant:

| Blueprint | Description | Import |
|-----------|-------------|--------|
| **Entered Zone Alert** | Notify when entering any emergency zone | [![Import Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ftroykelly%2Fhomeassistant-abcemergency%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fabc_emergency_entered_zone.yaml) |
| **Exited Zone Alert** | Notify when leaving an emergency zone | [![Import Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ftroykelly%2Fhomeassistant-abcemergency%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fabc_emergency_exited_zone.yaml) |
| **Severity Escalation** | Critical alert when emergency escalates while you're inside | [![Import Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ftroykelly%2Fhomeassistant-abcemergency%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fabc_emergency_severity_escalation.yaml) |
| **Inside Emergency Warning** | Maximum urgency when inside red-level zone | [![Import Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ftroykelly%2Fhomeassistant-abcemergency%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fabc_emergency_inside_emergency_warning.yaml) |
| **Family Member Inside Zone** | Alert family when someone enters an emergency zone | [![Import Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ftroykelly%2Fhomeassistant-abcemergency%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fabc_emergency_family_inside_zone.yaml) |
| **Periodic Zone Reminder** | Recurring alerts while inside a zone | [![Import Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ftroykelly%2Fhomeassistant-abcemergency%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fabc_emergency_periodic_zone_reminder.yaml) |

---

## Binary Sensors for Containment

The integration creates these binary sensors for Zone and Person mode instances:

| Sensor | ON When |
|--------|---------|
| `binary_sensor.abc_emergency_*_inside_polygon` | Inside **any** emergency polygon |
| `binary_sensor.abc_emergency_*_inside_emergency_warning` | Inside **Emergency Warning** (red) polygon |
| `binary_sensor.abc_emergency_*_inside_watch_and_act` | Inside **Watch and Act** (orange+) polygon |
| `binary_sensor.abc_emergency_*_inside_advice` | Inside **Advice** (yellow+) polygon |

### Sensor Attributes

The `inside_polygon` sensor includes these attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `containing_count` | int | Number of emergency polygons you're inside |
| `highest_alert_level` | string | Highest level of containing incidents |
| `incidents` | list | Details of each containing incident |

Each incident in the list contains:
- `id` - Unique incident identifier
- `headline` - Incident description
- `alert_level` - Warning level (extreme, severe, moderate, minor)
- `alert_text` - Human-readable level (Emergency Warning, Watch and Act, Advice)
- `event_type` - Type (Bushfire, Flood, Storm, etc.)

---

## Events for Automations

The integration fires these events for containment state changes:

| Event | When Fired |
|-------|------------|
| `abc_emergency_entered_polygon` | You enter an emergency zone |
| `abc_emergency_exited_polygon` | You leave an emergency zone |
| `abc_emergency_inside_polygon` | Each update while inside (for reminders) |
| `abc_emergency_containment_severity_changed` | Alert level changes while you're inside |

### Event Data Fields

All containment events include:

| Field | Type | Description |
|-------|------|-------------|
| `config_entry_id` | string | Config entry ID |
| `instance_name` | string | Your instance name ("Home Zone", "Troy", etc.) |
| `instance_type` | string | "zone" or "person" |
| `incident_id` | string | Unique incident ID |
| `headline` | string | Incident headline |
| `event_type` | string | "Bushfire", "Flood", "Storm", etc. |
| `alert_level` | string | "extreme", "severe", "moderate", "minor" |
| `alert_text` | string | "Emergency Warning", "Watch and Act", "Advice" |
| `monitored_latitude` | float | Your monitored location latitude |
| `monitored_longitude` | float | Your monitored location longitude |
| `latitude` | float | Incident centroid latitude |
| `longitude` | float | Incident centroid longitude |

### Severity Changed Event Additional Fields

| Field | Type | Description |
|-------|------|-------------|
| `previous_alert_level` | string | Previous level (extreme, severe, moderate, minor) |
| `previous_alert_text` | string | Previous text (Emergency Warning, Watch and Act, Advice) |
| `new_alert_level` | string | New alert level |
| `new_alert_text` | string | New alert text |
| `escalated` | boolean | `true` if severity increased, `false` if decreased |

---

## How Containment Detection Works

### The Technical Flow

1. **Polygon Geometry**: Emergency incidents from ABC Emergency include polygon boundaries (GeoJSON)
2. **Point-in-Polygon**: The integration uses [Shapely](https://shapely.readthedocs.io/) library for accurate geometric containment testing
3. **Cached Geometries**: Prepared geometries are cached for efficient repeated checks
4. **State Tracking**: The integration tracks previous containment state to detect changes

### What Triggers Enter/Exit Events

**Entered Polygon** fires when:
- A new incident appears that contains your location
- An existing incident's polygon **expands** to include your location
- You move into an incident's polygon (Person mode)

**Exited Polygon** fires when:
- An incident is resolved/removed
- An incident's polygon **shrinks** and no longer contains your location
- You move out of an incident's polygon (Person mode)

**Severity Changed** fires when:
- An incident's alert level changes (e.g., Advice to Watch and Act)
- Only fires while you're inside the incident's polygon

### First Update Behavior

Events are NOT fired on the first data load after startup. This prevents false "entered" events when Home Assistant restarts while you're already inside a zone. Events only fire on actual state transitions.

---

## Safety Automations

### Maximum Urgency: Inside Emergency Warning Zone

This is the most critical automation. If you're physically inside an Emergency Warning (red level) zone, you need to act immediately.

```yaml
automation:
  - id: abc_emergency_inside_red_zone
    alias: "EVACUATE - Inside Emergency Warning"
    description: >
      Maximum urgency alert when physically inside an Emergency Warning zone.
      This bypasses Do Not Disturb and plays a critical alert sound.
    trigger:
      - platform: state
        entity_id: binary_sensor.abc_emergency_home_inside_emergency_warning
        to: "on"
    action:
      # Flash all lights red
      - service: light.turn_on
        target:
          entity_id: all
        data:
          color_name: red
          brightness: 255
          flash: long

      # Send critical notification
      - service: notify.mobile_app_your_phone
        data:
          title: "EVACUATE NOW"
          message: >
            You are INSIDE an Emergency Warning zone!
            {% set incidents = state_attr('binary_sensor.abc_emergency_home_inside_emergency_warning', 'incidents') %}
            {{ incidents[0].headline if incidents else 'Unknown emergency' }}
          data:
            priority: critical
            ttl: 0
            channel: alarm_stream
            push:
              sound:
                name: default
                critical: 1
                volume: 1.0

      # Announce on all speakers
      - service: tts.google_translate_say
        target:
          entity_id: media_player.all_speakers
        data:
          message: >
            Attention! Attention! You are inside an Emergency Warning zone.
            Please evacuate immediately. This is not a drill.
```

### Entered Emergency Zone Alert

Get notified immediately when you enter any emergency polygon:

```yaml
automation:
  - id: abc_emergency_entered_zone
    alias: "Entered Emergency Zone"
    trigger:
      - platform: event
        event_type: abc_emergency_entered_polygon
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: >
            {% if trigger.event.data.alert_level == 'extreme' %}
            ENTERED EMERGENCY ZONE
            {% elif trigger.event.data.alert_level == 'severe' %}
            Entered Watch and Act Zone
            {% else %}
            Entered Emergency Zone
            {% endif %}
          message: >
            You are now inside: {{ trigger.event.data.headline }}
            Alert Level: {{ trigger.event.data.alert_text }}
            Type: {{ trigger.event.data.event_type }}
          data:
            priority: >
              {% if trigger.event.data.alert_level == 'extreme' %}critical
              {% elif trigger.event.data.alert_level == 'severe' %}high
              {% else %}normal{% endif %}
            actions:
              - action: "URI"
                title: "View on ABC Emergency"
                uri: "https://www.abc.net.au/emergency"
```

### Exited Emergency Zone (Relief Alert)

Let people know when they've left a danger zone:

```yaml
automation:
  - id: abc_emergency_exited_zone
    alias: "Exited Emergency Zone"
    trigger:
      - platform: event
        event_type: abc_emergency_exited_polygon
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Left Emergency Zone"
          message: >
            You have left: {{ trigger.event.data.headline }}
            Stay vigilant and monitor conditions.
```

### Severity Escalation Alert

This is critical - get notified when an emergency you're already inside gets worse:

```yaml
automation:
  - id: abc_emergency_severity_escalated
    alias: "Emergency Escalated While Inside"
    description: >
      Critical alert when an emergency escalates (e.g., Advice -> Watch and Act
      or Watch and Act -> Emergency Warning) while you're inside its polygon.
    trigger:
      - platform: event
        event_type: abc_emergency_containment_severity_changed
    condition:
      - condition: template
        value_template: "{{ trigger.event.data.escalated == true }}"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "ALERT LEVEL INCREASED"
          message: >
            {{ trigger.event.data.headline }} has escalated!
            {{ trigger.event.data.previous_alert_text }} to {{ trigger.event.data.new_alert_text }}
            Take action now!
          data:
            priority: critical
            ttl: 0
            channel: alarm_stream

      # Also announce on speakers
      - service: tts.google_translate_say
        target:
          entity_id: media_player.living_room_speaker
        data:
          message: >
            Warning! {{ trigger.event.data.event_type }} alert has escalated to
            {{ trigger.event.data.new_alert_text }}. Take action now.
```

### Severity De-escalation (Good News)

Let people know when conditions are improving:

```yaml
automation:
  - id: abc_emergency_severity_deescalated
    alias: "Emergency De-escalated"
    trigger:
      - platform: event
        event_type: abc_emergency_containment_severity_changed
    condition:
      - condition: template
        value_template: "{{ trigger.event.data.escalated == false }}"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Alert Level Reduced"
          message: >
            {{ trigger.event.data.headline }} has de-escalated from
            {{ trigger.event.data.previous_alert_text }} to {{ trigger.event.data.new_alert_text }}.
            Continue to monitor conditions.
```

---

## Family Safety Automations

### Alert Family When Member Enters Zone

For Person mode instances tracking family members:

```yaml
automation:
  - id: abc_emergency_dad_entered_zone
    alias: "Dad Entered Emergency Zone"
    trigger:
      - platform: event
        event_type: abc_emergency_entered_polygon
        event_data:
          instance_type: "person"
    condition:
      - condition: template
        value_template: "{{ 'dad' in trigger.event.data.instance_name | lower }}"
    action:
      - service: notify.family_group
        data:
          title: "Dad is in an Emergency Zone"
          message: >
            Dad has entered {{ trigger.event.data.headline }}.
            Alert level: {{ trigger.event.data.alert_text }}
          data:
            priority: high
```

### Family Member Inside Emergency Warning

Maximum alert when a family member is inside a red-level zone:

```yaml
automation:
  - id: abc_emergency_family_emergency_warning
    alias: "Family Member in Emergency Warning Zone"
    trigger:
      - platform: state
        entity_id:
          - binary_sensor.abc_emergency_mum_inside_emergency_warning
          - binary_sensor.abc_emergency_dad_inside_emergency_warning
          - binary_sensor.abc_emergency_child_inside_emergency_warning
        to: "on"
    action:
      - service: notify.family_group
        data:
          title: "FAMILY MEMBER IN DANGER ZONE"
          message: >
            {{ trigger.to_state.name | replace('_inside_emergency_warning', '') }}
            is inside an Emergency Warning zone!
            Contact them immediately!
          data:
            priority: critical
            channel: alarm_stream
```

### Track Multiple Family Members

Create a combined family safety dashboard:

```yaml
automation:
  - id: abc_emergency_family_containment_any
    alias: "Any Family Member Inside Zone"
    trigger:
      - platform: state
        entity_id:
          - binary_sensor.abc_emergency_mum_inside_polygon
          - binary_sensor.abc_emergency_dad_inside_polygon
          - binary_sensor.abc_emergency_child_inside_polygon
        to: "on"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Family Member Alert"
          message: >
            {% set name = trigger.entity_id | replace('binary_sensor.abc_emergency_', '') | replace('_inside_polygon', '') | title %}
            {{ name }} is now inside an emergency zone.
            {% set incidents = state_attr(trigger.entity_id, 'incidents') %}
            {{ incidents[0].headline if incidents else 'Unknown' }}
```

---

## Periodic Reminders While Inside Zone

The `abc_emergency_inside_polygon` event fires on each data update (every 5 minutes) while you're inside a zone. Use this for periodic reminders:

```yaml
automation:
  - id: abc_emergency_periodic_reminder
    alias: "Periodic Inside Zone Reminder"
    description: "Remind every 15 minutes while inside an Emergency Warning zone"
    trigger:
      - platform: event
        event_type: abc_emergency_inside_polygon
        event_data:
          alert_level: "extreme"
    condition:
      # Only trigger every 3rd event (15 minutes with 5-minute updates)
      - condition: template
        value_template: >
          {{ now().minute | int % 15 < 5 }}
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "STILL INSIDE EMERGENCY ZONE"
          message: >
            Reminder: You are still inside {{ trigger.event.data.headline }}.
            Alert level: {{ trigger.event.data.alert_text }}
```

---

## Comprehensive Handler Automation

Handle all containment events in a single automation:

```yaml
automation:
  - id: abc_emergency_containment_handler
    alias: "ABC Emergency - Containment Handler"
    description: "Comprehensive handler for all containment state changes"
    trigger:
      - platform: event
        event_type: abc_emergency_entered_polygon
        id: entered
      - platform: event
        event_type: abc_emergency_exited_polygon
        id: exited
      - platform: event
        event_type: abc_emergency_containment_severity_changed
        id: severity
    action:
      - choose:
          # Handle entering a zone
          - conditions:
              - condition: trigger
                id: entered
            sequence:
              - service: notify.mobile_app_your_phone
                data:
                  title: "Entered {{ trigger.event.data.alert_text }} Zone"
                  message: "{{ trigger.event.data.headline }}"
                  data:
                    priority: >
                      {% if trigger.event.data.alert_level == 'extreme' %}critical
                      {% elif trigger.event.data.alert_level == 'severe' %}high
                      {% else %}normal{% endif %}

          # Handle exiting a zone
          - conditions:
              - condition: trigger
                id: exited
            sequence:
              - service: notify.mobile_app_your_phone
                data:
                  title: "Left Emergency Zone"
                  message: "You have left {{ trigger.event.data.headline }}"

          # Handle severity changes
          - conditions:
              - condition: trigger
                id: severity
            sequence:
              - service: notify.mobile_app_your_phone
                data:
                  title: >
                    {% if trigger.event.data.escalated %}ALERT ESCALATED{% else %}Alert Reduced{% endif %}
                  message: >
                    {{ trigger.event.data.headline }}:
                    {{ trigger.event.data.previous_alert_text }} to {{ trigger.event.data.new_alert_text }}
                  data:
                    priority: "{{ 'critical' if trigger.event.data.escalated else 'normal' }}"
```

---

## Smart Home Integration Examples

### Emergency Lighting

Flash lights based on containment status:

```yaml
automation:
  - id: abc_emergency_containment_lights
    alias: "Emergency Zone Lighting"
    trigger:
      - platform: state
        entity_id: binary_sensor.abc_emergency_home_inside_polygon
        to: "on"
    action:
      - choose:
          # Emergency Warning - Urgent red flashing
          - conditions:
              - condition: state
                entity_id: binary_sensor.abc_emergency_home_inside_emergency_warning
                state: "on"
            sequence:
              - repeat:
                  count: 10
                  sequence:
                    - service: light.turn_on
                      target:
                        entity_id: light.living_room
                      data:
                        color_name: red
                        brightness: 255
                    - delay: "00:00:00.5"
                    - service: light.turn_off
                      target:
                        entity_id: light.living_room
                    - delay: "00:00:00.5"
              - service: light.turn_on
                target:
                  entity_id: light.living_room
                data:
                  color_name: red
                  brightness: 200

          # Watch and Act - Solid orange
          - conditions:
              - condition: state
                entity_id: binary_sensor.abc_emergency_home_inside_watch_and_act
                state: "on"
            sequence:
              - service: light.turn_on
                target:
                  entity_id: light.status_light
                data:
                  rgb_color: [255, 165, 0]
                  brightness: 255

          # Advice - Solid yellow
          - conditions:
              - condition: state
                entity_id: binary_sensor.abc_emergency_home_inside_advice
                state: "on"
            sequence:
              - service: light.turn_on
                target:
                  entity_id: light.status_light
                data:
                  color_name: yellow
                  brightness: 200
```

### Siren Activation

Trigger a siren when inside a red-level zone:

```yaml
automation:
  - id: abc_emergency_siren_containment
    alias: "Siren for Emergency Warning Containment"
    trigger:
      - platform: state
        entity_id: binary_sensor.abc_emergency_home_inside_emergency_warning
        to: "on"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.emergency_siren
      - delay: "00:00:30"
      - service: switch.turn_off
        target:
          entity_id: switch.emergency_siren
```

### Climate Control

Shut down HVAC to prevent smoke inhalation during bushfires:

```yaml
automation:
  - id: abc_emergency_hvac_shutdown
    alias: "HVAC Shutdown for Bushfire Zone"
    trigger:
      - platform: event
        event_type: abc_emergency_entered_polygon
    condition:
      - condition: template
        value_template: "{{ trigger.event.data.event_type == 'Bushfire' }}"
    action:
      - service: climate.turn_off
        target:
          entity_id: climate.home
      - service: notify.mobile_app_your_phone
        data:
          title: "HVAC Shut Down"
          message: >
            Air conditioning turned off due to bushfire zone entry.
            This prevents smoke being drawn into the home.
```

---

## Testing Your Automations

### Developer Tools Events

Test containment events using Developer Tools:

1. Go to **Developer Tools** > **Events**
2. Under "Fire an event", enter:

```yaml
Event type: abc_emergency_entered_polygon
Event data:
  instance_name: "ABC Emergency (Home)"
  instance_type: "zone"
  incident_id: "TEST-123"
  headline: "Test Bushfire at Test Location"
  event_type: "Bushfire"
  alert_level: "extreme"
  alert_text: "Emergency Warning"
  monitored_latitude: -33.8688
  monitored_longitude: 151.2093
```

3. Click "Fire Event" to test your automations

### Testing Severity Changes

```yaml
Event type: abc_emergency_containment_severity_changed
Event data:
  instance_name: "ABC Emergency (Home)"
  incident_id: "TEST-123"
  headline: "Test Bushfire at Test Location"
  event_type: "Bushfire"
  previous_alert_level: "moderate"
  previous_alert_text: "Advice"
  new_alert_level: "extreme"
  new_alert_text: "Emergency Warning"
  alert_level: "extreme"
  alert_text: "Emergency Warning"
  escalated: true
```

---

## Troubleshooting

### Events Not Firing

1. **Check instance type** - Containment only works for Zone and Person modes, not State mode
2. **Check polygon data** - Not all incidents have polygon boundaries (some are point-only)
3. **Wait for second update** - Events don't fire on first startup to prevent false positives

### Binary Sensors Always Off

1. **Verify location** - Check your configured location is correct
2. **Check for incidents** - There may be no incidents with polygons currently
3. **View diagnostics** - Download diagnostics to see polygon data

### Automations Not Triggering

1. **Test with Developer Tools** - Fire manual events to verify automation logic
2. **Check entity IDs** - Ensure sensor names match your configuration
3. **View automation traces** - Check why the automation didn't trigger

---

## Best Practices

### 1. Layer Your Alerts

Don't rely on a single notification. Use multiple channels:
- Mobile push notifications
- TTS announcements
- Visual indicators (lights)
- External sirens for critical alerts

### 2. Use Critical Notifications Wisely

Reserve `priority: critical` for genuinely life-threatening situations:
- Inside Emergency Warning zones
- Severity escalation to Emergency Warning
- Very close proximity to major incidents

### 3. Test Regularly

Fire test events periodically to ensure your automations still work:
- After Home Assistant updates
- After configuration changes
- Seasonally before fire/flood season

### 4. Consider Family Members

If using Person mode for family tracking:
- Get their consent before tracking
- Notify them when they enter zones (not just you)
- Consider their notification preferences

### 5. Have a Plan

Automations are aids, not replacements for emergency planning:
- Know your evacuation routes
- Have a bushfire survival plan
- Know your flood risk
- Keep emergency kits ready

---

## Related Documentation

- [Entities Reference](entities.md) - Complete entity documentation
- [Automations Guide](automations.md) - General automation examples
- [Configuration](configuration.md) - Setting up Zone and Person modes
- [Troubleshooting](troubleshooting.md) - Common issues

---

## Emergency Resources

In a life-threatening emergency, **call 000**.

- [ABC Emergency](https://www.abc.net.au/emergency) - Real-time emergency map
- [Australian Warning System](https://www.australianwarningsystem.com.au/) - Official warning levels
- [NSW RFS](https://www.rfs.nsw.gov.au/) - NSW Rural Fire Service
- [CFA Victoria](https://www.cfa.vic.gov.au/) - Country Fire Authority
- [QFES](https://www.qfes.qld.gov.au/) - Queensland Fire and Emergency Services
- [Bureau of Meteorology](http://www.bom.gov.au/australia/warnings/) - Weather warnings
