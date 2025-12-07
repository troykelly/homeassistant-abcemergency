# Automations Guide

Ready-to-use Home Assistant automations for ABC Emergency alerts.

> **Note:** All examples use placeholder entity names like `abc_emergency_home_*`. Replace `home` with your configured instance name.

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

## Next Steps

- [Notifications Guide](notifications.md) - Detailed notification setup
- [Scripts Guide](scripts.md) - Emergency scripts and sequences
- [Entities Reference](entities.md) - Complete entity documentation
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
