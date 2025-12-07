# Automations Guide

Ready-to-use Home Assistant automations for ABC Emergency alerts.

<p align="center">
  <a href="https://my.home-assistant.io/redirect/automations/"><img src="https://my.home-assistant.io/badges/automations.svg" alt="View Automations"></a>
  <a href="https://my.home-assistant.io/redirect/blueprints/"><img src="https://my.home-assistant.io/badges/blueprints.svg" alt="View Blueprints"></a>
</p>

> **Note:** All examples use placeholder entity names like `abc_emergency_home_*`. Replace `home` with your configured instance name.

---

## Importable Blueprints

Import these ready-to-use blueprints with one click:

| Blueprint | Description | Import |
|-----------|-------------|--------|
| **Basic Alert** | Simple notification for any alert | [![Import Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ftroykelly%2Fhomeassistant-abcemergency%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fabc_emergency_basic_alert.yaml) |
| **Tiered Notifications** | Different priorities by warning level | [![Import Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ftroykelly%2Fhomeassistant-abcemergency%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fabc_emergency_tiered_notifications.yaml) |
| **Distance Escalation** | Alerts as incidents approach (30km, 15km, 5km) | [![Import Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ftroykelly%2Fhomeassistant-abcemergency%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fabc_emergency_distance_escalation.yaml) |
| **TTS Announcement** | Announce on smart speakers | [![Import Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ftroykelly%2Fhomeassistant-abcemergency%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fabc_emergency_tts_announcement.yaml) |
| **Light Alert** | Flash/color lights based on alert level | [![Import Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ftroykelly%2Fhomeassistant-abcemergency%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fabc_emergency_light_alert.yaml) |
| **Family Safety** | Monitor alerts near family members | [![Import Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ftroykelly%2Fhomeassistant-abcemergency%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fabc_emergency_family_safety.yaml) |

---

## Basic Alert Notification

The simplest automation - notify when any emergency warning is active near you.

```yaml
automation:
  - id: abc_emergency_basic_alert
    alias: "ABC Emergency - Basic Alert"
    description: "Notify when any emergency warning is active nearby"
    trigger:
      - platform: state
        entity_id: binary_sensor.abc_emergency_home_advice
        to: "on"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Emergency Alert"
          message: >
            {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}
            ({{ states('sensor.abc_emergency_home_nearest_incident') }}km away)
```

---

## Tiered Notifications by Warning Level

Send different notification priorities based on the warning level.

```yaml
automation:
  # Advice level - informational, normal priority
  - id: abc_emergency_advice_notification
    alias: "ABC Emergency - Advice Level"
    description: "Informational notification for Advice level warnings"
    trigger:
      - platform: state
        entity_id: binary_sensor.abc_emergency_home_advice
        to: "on"
    condition:
      # Only trigger if this is exactly Advice level (not higher)
      - condition: state
        entity_id: binary_sensor.abc_emergency_home_watch_and_act
        state: "off"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Emergency Advice"
          message: >
            {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'event_type') }}:
            {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}
            ({{ states('sensor.abc_emergency_home_nearest_incident') }}km
            {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'direction') }})

  # Watch and Act - urgent, high priority
  - id: abc_emergency_watch_and_act_notification
    alias: "ABC Emergency - Watch and Act"
    description: "High priority notification for Watch and Act warnings"
    trigger:
      - platform: state
        entity_id: binary_sensor.abc_emergency_home_watch_and_act
        to: "on"
    condition:
      # Only trigger if this is exactly Watch and Act (not Emergency)
      - condition: state
        entity_id: binary_sensor.abc_emergency_home_emergency_warning
        state: "off"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "WATCH AND ACT"
          message: >
            Take action now!
            {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'event_type') }}:
            {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}
            is {{ states('sensor.abc_emergency_home_nearest_incident') }}km to the
            {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'direction') }}
          data:
            priority: high
            ttl: 0
            channel: alerts

  # Emergency Warning - critical, bypass Do Not Disturb
  - id: abc_emergency_emergency_warning_notification
    alias: "ABC Emergency - Emergency Warning"
    description: "Critical notification for Emergency Warning"
    trigger:
      - platform: state
        entity_id: binary_sensor.abc_emergency_home_emergency_warning
        to: "on"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "EMERGENCY WARNING"
          message: >
            ACT IMMEDIATELY!
            {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'event_type') }}:
            {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}
            is {{ states('sensor.abc_emergency_home_nearest_incident') }}km to the
            {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'direction') }}
          data:
            priority: critical
            ttl: 0
            channel: alarm_stream
```

---

## Distance-Based Escalation

Increase urgency as an incident gets closer.

```yaml
automation:
  # Warning when incident comes within 30km
  - id: abc_emergency_distance_30km
    alias: "ABC Emergency - Incident Within 30km"
    trigger:
      - platform: numeric_state
        entity_id: sensor.abc_emergency_home_nearest_incident
        below: 30
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Emergency Approaching"
          message: >
            {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}
            is now {{ states('sensor.abc_emergency_home_nearest_incident') }}km away

  # Urgent when incident comes within 15km
  - id: abc_emergency_distance_15km
    alias: "ABC Emergency - Incident Within 15km"
    trigger:
      - platform: numeric_state
        entity_id: sensor.abc_emergency_home_nearest_incident
        below: 15
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "EMERGENCY CLOSE BY"
          message: >
            {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}
            is now only {{ states('sensor.abc_emergency_home_nearest_incident') }}km away!
          data:
            priority: high

  # Critical when incident comes within 5km
  - id: abc_emergency_distance_5km
    alias: "ABC Emergency - Incident Within 5km"
    trigger:
      - platform: numeric_state
        entity_id: sensor.abc_emergency_home_nearest_incident
        below: 5
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "IMMEDIATE DANGER"
          message: >
            {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}
            is only {{ states('sensor.abc_emergency_home_nearest_incident') }}km away!
            Consider evacuating!
          data:
            priority: critical
            channel: alarm_stream
```

---

## Family Member Safety Alerts

Monitor emergencies near family members as they move.

```yaml
automation:
  # Alert when Dad enters an emergency zone
  - id: abc_emergency_dad_alert
    alias: "ABC Emergency - Dad Near Emergency"
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
            {{ state_attr('sensor.abc_emergency_dad_nearest_incident', 'event_type') }}:
            {{ state_attr('sensor.abc_emergency_dad_nearest_incident', 'headline') }}
            Distance: {{ states('sensor.abc_emergency_dad_nearest_incident') }}km

  # Alert for any family member with Emergency Warning
  - id: abc_emergency_family_emergency_warning
    alias: "ABC Emergency - Family Member Emergency Warning"
    trigger:
      - platform: state
        entity_id:
          - binary_sensor.abc_emergency_mum_emergency_warning
          - binary_sensor.abc_emergency_dad_emergency_warning
          - binary_sensor.abc_emergency_child_emergency_warning
        to: "on"
    action:
      - service: notify.family_group
        data:
          title: "EMERGENCY WARNING - Family Member"
          message: >
            {{ trigger.to_state.name }} has an Emergency Warning active!
            Check on them immediately.
          data:
            priority: critical
```

---

## Quiet Hours Handling

Adjust notification behavior during sleep hours.

```yaml
automation:
  - id: abc_emergency_quiet_hours
    alias: "ABC Emergency - Quiet Hours Aware"
    trigger:
      - platform: state
        entity_id: binary_sensor.abc_emergency_home_advice
        to: "on"
    action:
      - choose:
          # During quiet hours (10pm - 7am): only notify for Watch and Act or higher
          - conditions:
              - condition: time
                after: "22:00:00"
                before: "07:00:00"
              - condition: state
                entity_id: binary_sensor.abc_emergency_home_watch_and_act
                state: "on"
            sequence:
              - service: notify.mobile_app_your_phone
                data:
                  title: "URGENT: Emergency Alert"
                  message: >
                    {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}
                    ({{ states('sensor.abc_emergency_home_nearest_incident') }}km)
                  data:
                    priority: critical
          # During quiet hours: ignore Advice-only alerts
          - conditions:
              - condition: time
                after: "22:00:00"
                before: "07:00:00"
            sequence: []  # Do nothing for Advice during quiet hours
        # Normal hours: notify for everything
        default:
          - service: notify.mobile_app_your_phone
            data:
              title: "Emergency Alert"
              message: >
                {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}
                ({{ states('sensor.abc_emergency_home_nearest_incident') }}km)
```

---

## TTS Announcements

Announce emergencies on smart speakers.

```yaml
automation:
  # Announce on Google Home/Nest speakers
  - id: abc_emergency_tts_google
    alias: "ABC Emergency - TTS Announcement (Google)"
    trigger:
      - platform: state
        entity_id: binary_sensor.abc_emergency_home_watch_and_act
        to: "on"
    action:
      - service: tts.google_translate_say
        target:
          entity_id: media_player.living_room_speaker
        data:
          message: >
            Attention! Emergency Alert.
            {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'event_type') }}
            detected {{ states('sensor.abc_emergency_home_nearest_incident') }} kilometres
            to the {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'direction') }}.
            Please check ABC Emergency for more information.

  # Announce on Amazon Alexa
  - id: abc_emergency_tts_alexa
    alias: "ABC Emergency - TTS Announcement (Alexa)"
    trigger:
      - platform: state
        entity_id: binary_sensor.abc_emergency_home_watch_and_act
        to: "on"
    action:
      - service: notify.alexa_media
        data:
          target: media_player.kitchen_echo
          message: >
            <voice name="Nicole">
            <amazon:emotion name="excited" intensity="high">
            Attention! Emergency Alert!
            </amazon:emotion>
            {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'event_type') }}
            detected {{ states('sensor.abc_emergency_home_nearest_incident') }} kilometres away.
            </voice>
          data:
            type: announce
```

---

## Smart Light Alerts

Use your lights to indicate emergency status.

```yaml
automation:
  # Flash lights red for Emergency Warning
  - id: abc_emergency_lights_flash
    alias: "ABC Emergency - Flash Lights Red"
    trigger:
      - platform: state
        entity_id: binary_sensor.abc_emergency_home_emergency_warning
        to: "on"
    action:
      - repeat:
          count: 5
          sequence:
            - service: light.turn_on
              target:
                entity_id: light.living_room
              data:
                color_name: red
                brightness: 255
            - delay: "00:00:01"
            - service: light.turn_off
              target:
                entity_id: light.living_room
            - delay: "00:00:01"
      - service: light.turn_on
        target:
          entity_id: light.living_room
        data:
          color_name: red
          brightness: 128

  # Set light color based on warning level
  - id: abc_emergency_lights_color
    alias: "ABC Emergency - Warning Level Light Color"
    trigger:
      - platform: state
        entity_id: sensor.abc_emergency_home_highest_alert_level
    action:
      - choose:
          - conditions:
              - condition: state
                entity_id: sensor.abc_emergency_home_highest_alert_level
                state: "Emergency"
            sequence:
              - service: light.turn_on
                target:
                  entity_id: light.status_lamp
                data:
                  color_name: red
                  brightness: 255
          - conditions:
              - condition: state
                entity_id: sensor.abc_emergency_home_highest_alert_level
                state: "Watch and Act"
            sequence:
              - service: light.turn_on
                target:
                  entity_id: light.status_lamp
                data:
                  rgb_color: [255, 165, 0]  # Orange
                  brightness: 255
          - conditions:
              - condition: state
                entity_id: sensor.abc_emergency_home_highest_alert_level
                state: "Advice"
            sequence:
              - service: light.turn_on
                target:
                  entity_id: light.status_lamp
                data:
                  color_name: yellow
                  brightness: 200
        default:
          - service: light.turn_off
            target:
              entity_id: light.status_lamp
```

---

## Bushfire-Specific Alerts

Alert specifically for bushfire incidents.

```yaml
automation:
  - id: abc_emergency_bushfire_alert
    alias: "ABC Emergency - Bushfire Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.abc_emergency_home_bushfires
        above: 0
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Bushfire Alert"
          message: >
            {{ states('sensor.abc_emergency_home_bushfires') }} active bushfire(s) in your area.
            Nearest incident: {{ states('sensor.abc_emergency_home_nearest_incident') }}km away.

  - id: abc_emergency_bushfire_close
    alias: "ABC Emergency - Bushfire Close By"
    trigger:
      - platform: numeric_state
        entity_id: sensor.abc_emergency_home_nearest_incident
        below: 20
    condition:
      - condition: template
        value_template: >
          {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'event_type') == 'Bushfire' }}
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "BUSHFIRE CLOSE BY"
          message: >
            {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}
            is {{ states('sensor.abc_emergency_home_nearest_incident') }}km
            to the {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'direction') }}!
            Monitor conditions closely.
          data:
            priority: high
            channel: alerts
```

---

## Siren/Alarm Activation

Activate external sirens for critical emergencies.

```yaml
automation:
  - id: abc_emergency_siren
    alias: "ABC Emergency - Activate Siren"
    trigger:
      - platform: state
        entity_id: binary_sensor.abc_emergency_home_emergency_warning
        to: "on"
    condition:
      # Only during waking hours unless very close
      - condition: or
        conditions:
          - condition: time
            after: "07:00:00"
            before: "22:00:00"
          - condition: numeric_state
            entity_id: sensor.abc_emergency_home_nearest_incident
            below: 5
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.emergency_siren
      - delay: "00:00:30"  # Sound for 30 seconds
      - service: switch.turn_off
        target:
          entity_id: switch.emergency_siren
```

---

## All-Clear Notification

Notify when an emergency threat has passed.

```yaml
automation:
  - id: abc_emergency_all_clear
    alias: "ABC Emergency - All Clear"
    trigger:
      - platform: state
        entity_id: binary_sensor.abc_emergency_home_active_alert
        from: "on"
        to: "off"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "All Clear"
          message: >
            No active emergencies near your location.
            Stay safe and remain vigilant.
```

---

## Multi-Zone Monitoring

Monitor multiple locations and summarize.

```yaml
automation:
  - id: abc_emergency_multi_zone_summary
    alias: "ABC Emergency - Multi-Zone Summary"
    trigger:
      - platform: time
        at: "08:00:00"  # Daily morning summary
    condition:
      - condition: or
        conditions:
          - condition: state
            entity_id: binary_sensor.abc_emergency_home_active_alert
            state: "on"
          - condition: state
            entity_id: binary_sensor.abc_emergency_office_active_alert
            state: "on"
          - condition: state
            entity_id: binary_sensor.abc_emergency_beach_house_active_alert
            state: "on"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Morning Emergency Summary"
          message: >
            Active emergencies:
            Home: {{ states('sensor.abc_emergency_home_incidents_nearby') }} nearby
            Office: {{ states('sensor.abc_emergency_office_incidents_nearby') }} nearby
            Beach House: {{ states('sensor.abc_emergency_beach_house_incidents_nearby') }} nearby
```

---

<details>
<summary>Understanding Jinja2 Templates</summary>

Templates in Home Assistant use Jinja2 syntax to insert dynamic values into text.

**Basic syntax:**
- `{{ }}` - Output a value
- `{% %}` - Logic (if/else, loops)
- `states('entity_id')` - Get entity state
- `state_attr('entity_id', 'attribute')` - Get attribute

**Example breakdown:**
```yaml
message: >
  {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}
  is {{ states('sensor.abc_emergency_home_nearest_incident') }}km away
```

This produces: "Milsons Gully Bushfire is 12.4km away"

Test templates in **Developer Tools** -> **Template** before using them.

</details>

---

## Blueprint Template

Use this as a starting point for custom automations:

```yaml
automation:
  - id: abc_emergency_custom
    alias: "ABC Emergency - Custom Automation"
    description: "Describe your automation purpose"

    trigger:
      # Choose your trigger type:

      # Option 1: Warning level change
      - platform: state
        entity_id: binary_sensor.abc_emergency_home_advice
        to: "on"

      # Option 2: Distance threshold
      # - platform: numeric_state
      #   entity_id: sensor.abc_emergency_home_nearest_incident
      #   below: 25

      # Option 3: Incident count increase
      # - platform: numeric_state
      #   entity_id: sensor.abc_emergency_home_bushfires
      #   above: 0

    condition:
      # Optional conditions:

      # Time-based
      # - condition: time
      #   after: "07:00:00"
      #   before: "22:00:00"

      # Event type filter
      # - condition: template
      #   value_template: >
      #     {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'event_type') == 'Bushfire' }}

    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Your Title"
          message: >
            Your message using:
            - Headline: {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}
            - Distance: {{ states('sensor.abc_emergency_home_nearest_incident') }}km
            - Direction: {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'direction') }}
            - Type: {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'event_type') }}
            - Level: {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'alert_level') }}
```

---

## Event-Based Automations

The integration fires Home Assistant events when **new incidents** are detected. This enables real-time alerting for each individual incident as it appears, rather than relying on sensor state changes.

### Why Use Events?

- **Per-incident notifications** - Get alerted for each new incident, not just when counts change
- **Rich incident data** - Event payload contains all incident details for use in templates
- **Type-specific triggers** - Trigger only on bushfires, floods, storms, etc.
- **Instance awareness** - Event data identifies which integration instance detected the incident

### Basic New Incident Alert

```yaml
automation:
  - id: abc_emergency_new_incident
    alias: "ABC Emergency - New Incident Detected"
    description: "Alert when any new emergency incident is detected"
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
            Distance: {{ trigger.event.data.distance_km | round(1) }}km {{ trigger.event.data.direction }}
            {% endif %}
          data:
            priority: >
              {% if trigger.event.data.alert_level == 'Emergency Warning' %}critical
              {% elif trigger.event.data.alert_level == 'Watch and Act' %}high
              {% else %}normal{% endif %}
```

### Type-Specific Incident Alerts

Trigger automations only for specific incident types:

```yaml
automation:
  # Bushfire-specific alert
  - id: abc_emergency_new_bushfire
    alias: "ABC Emergency - New Bushfire"
    trigger:
      - platform: event
        event_type: abc_emergency_new_bushfire
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "🔥 New Bushfire Detected"
          message: >
            {{ trigger.event.data.headline }}
            {% if trigger.event.data.distance_km %}
            {{ trigger.event.data.distance_km | round(1) }}km {{ trigger.event.data.direction }}
            {% endif %}
          data:
            priority: high

  # Flood-specific alert
  - id: abc_emergency_new_flood
    alias: "ABC Emergency - New Flood"
    trigger:
      - platform: event
        event_type: abc_emergency_new_flood
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "🌊 New Flood Warning"
          message: "{{ trigger.event.data.headline }}"

  # Storm-specific alert
  - id: abc_emergency_new_storm
    alias: "ABC Emergency - New Storm"
    trigger:
      - platform: event
        event_type: abc_emergency_new_storm
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "⛈️ New Storm Warning"
          message: "{{ trigger.event.data.headline }}"
```

### Filter by Instance

If you have multiple integration instances (e.g., home, office, beach house), filter events by instance:

```yaml
automation:
  - id: abc_emergency_new_incident_home_only
    alias: "ABC Emergency - New Incident (Home Only)"
    trigger:
      - platform: event
        event_type: abc_emergency_new_incident
    condition:
      - condition: template
        value_template: "{{ trigger.event.data.instance_name == 'ABC Emergency (Home)' }}"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Emergency Near Home"
          message: "{{ trigger.event.data.headline }}"
```

### Filter by Distance

Only alert for incidents within a certain distance:

```yaml
automation:
  - id: abc_emergency_new_incident_close
    alias: "ABC Emergency - New Incident Within 25km"
    trigger:
      - platform: event
        event_type: abc_emergency_new_incident
    condition:
      - condition: template
        value_template: >
          {{ trigger.event.data.distance_km is not none and
             trigger.event.data.distance_km < 25 }}
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "NEARBY: {{ trigger.event.data.event_type }}"
          message: >
            {{ trigger.event.data.headline }}
            Only {{ trigger.event.data.distance_km | round(1) }}km away!
          data:
            priority: high
```

### Filter by Alert Level

Only trigger for serious warnings:

```yaml
automation:
  - id: abc_emergency_serious_incident
    alias: "ABC Emergency - Serious New Incident"
    trigger:
      - platform: event
        event_type: abc_emergency_new_incident
    condition:
      - condition: template
        value_template: >
          {{ trigger.event.data.alert_level in ['Emergency Warning', 'Watch and Act'] }}
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "{{ trigger.event.data.alert_level | upper }}"
          message: "{{ trigger.event.data.headline }}"
          data:
            priority: critical
```

### Event Reference

#### Available Events

| Event Type | Description |
|------------|-------------|
| `abc_emergency_new_incident` | Fired for any new incident |
| `abc_emergency_new_bushfire` | Fired for new bushfire incidents |
| `abc_emergency_new_flood` | Fired for new flood incidents |
| `abc_emergency_new_storm` | Fired for new storm incidents |
| `abc_emergency_new_extreme_heat` | Fired for new extreme heat incidents |
| `abc_emergency_new_cyclone` | Fired for new cyclone incidents |
| `abc_emergency_new_earthquake` | Fired for new earthquake incidents |

> **Note:** Type-specific events use a slugified version of the incident type (lowercase, spaces replaced with underscores).

#### Event Data Fields

All events include the following data fields:

| Field | Type | Description |
|-------|------|-------------|
| `config_entry_id` | string | Config entry ID of the integration instance |
| `instance_name` | string | Name of the integration instance (e.g., "ABC Emergency (Home)") |
| `instance_type` | string | Type: `"state"`, `"zone"`, or `"person"` |
| `incident_id` | string | Unique incident identifier |
| `headline` | string | Incident headline/title |
| `event_type` | string | Type: `"Bushfire"`, `"Flood"`, `"Storm"`, etc. |
| `event_icon` | string | Icon identifier for the incident type |
| `alert_level` | string | `"Emergency Warning"`, `"Watch and Act"`, `"Advice"`, or `"Information"` |
| `alert_text` | string | Alert level display text |
| `latitude` | float | Incident latitude |
| `longitude` | float | Incident longitude |
| `distance_km` | float \| null | Distance from monitored location (zone/person mode only) |
| `direction` | string \| null | Compass direction (zone/person mode only) |
| `bearing` | float \| null | Bearing in degrees (zone/person mode only) |
| `status` | string \| null | Incident status (e.g., "Out of control") |
| `size` | string \| null | Incident size (e.g., "500 ha") |
| `source` | string \| null | Data source agency (e.g., "NSW Rural Fire Service") |
| `updated` | string | ISO 8601 timestamp of last update |

---

## Next Steps

- [Notifications Guide](notifications.md) - Detailed notification setup
- [Scripts Guide](scripts.md) - Emergency scripts and sequences
- [Entities Reference](entities.md) - Complete entity documentation
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
