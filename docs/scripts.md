# Scripts Guide

Ready-to-use Home Assistant scripts for emergency response with ABC Emergency.

Scripts are reusable sequences of actions that can be triggered by automations, buttons, voice commands, or the UI.

---

## Emergency Briefing Script

Get a spoken summary of current emergency conditions.

```yaml
script:
  emergency_briefing:
    alias: "Emergency Briefing"
    description: "Announce current emergency status"
    sequence:
      - choose:
          # Emergency Warning active
          - conditions:
              - condition: state
                entity_id: binary_sensor.abc_emergency_home_emergency_warning
                state: "on"
            sequence:
              - service: tts.google_translate_say
                target:
                  entity_id: media_player.living_room_speaker
                data:
                  message: >
                    Emergency Warning in effect.
                    {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'event_type') }}
                    at {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}
                    is {{ states('sensor.abc_emergency_home_nearest_incident') }} kilometres
                    to the {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'direction') }}.
                    Total incidents nearby: {{ states('sensor.abc_emergency_home_incidents_nearby') }}.
                    You may need to act immediately.

          # Watch and Act active
          - conditions:
              - condition: state
                entity_id: binary_sensor.abc_emergency_home_watch_and_act
                state: "on"
            sequence:
              - service: tts.google_translate_say
                target:
                  entity_id: media_player.living_room_speaker
                data:
                  message: >
                    Watch and Act warning in effect.
                    {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'event_type') }}
                    is {{ states('sensor.abc_emergency_home_nearest_incident') }} kilometres away.
                    Stay alert and prepare to take action.
                    Total incidents nearby: {{ states('sensor.abc_emergency_home_incidents_nearby') }}.

          # Advice active
          - conditions:
              - condition: state
                entity_id: binary_sensor.abc_emergency_home_advice
                state: "on"
            sequence:
              - service: tts.google_translate_say
                target:
                  entity_id: media_player.living_room_speaker
                data:
                  message: >
                    Emergency Advice in effect.
                    {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'event_type') }}
                    is {{ states('sensor.abc_emergency_home_nearest_incident') }} kilometres away.
                    Stay informed and monitor conditions.

        # No active alerts
        default:
          - service: tts.google_translate_say
            target:
              entity_id: media_player.living_room_speaker
            data:
              message: >
                No active emergencies near your location.
                {{ states('sensor.abc_emergency_nsw_incidents_total') }} incidents are
                currently active across New South Wales.
```

---

## Evacuation Checklist Trigger

Activate a checklist and notification sequence when evacuation might be needed.

```yaml
script:
  evacuation_checklist:
    alias: "Evacuation Checklist"
    description: "Trigger evacuation preparation checklist"
    sequence:
      # Turn on bright lights throughout the house
      - service: light.turn_on
        target:
          entity_id:
            - light.living_room
            - light.bedroom
            - light.hallway
            - light.garage
        data:
          brightness: 255
          color_temp_kelvin: 6500

      # Announce the checklist
      - service: tts.google_translate_say
        target:
          entity_id: media_player.living_room_speaker
        data:
          message: >
            Attention. Evacuation may be required.
            Emergency is {{ states('sensor.abc_emergency_home_nearest_incident') }} kilometres away.
            Beginning evacuation checklist.

      - delay: "00:00:05"

      # Send detailed checklist to phones
      - service: notify.family_group
        data:
          title: "EVACUATION CHECKLIST"
          message: |
            Emergency is {{ states('sensor.abc_emergency_home_nearest_incident') }}km away.

            Immediate actions:
            [ ] Close all windows and doors
            [ ] Move cars to driveway, facing out
            [ ] Fill bathtubs and sinks with water
            [ ] Locate important documents

            Grab:
            [ ] Medications
            [ ] Phone chargers
            [ ] Cash/cards
            [ ] Pet supplies
            [ ] Emergency kit

            Before leaving:
            [ ] Turn off gas
            [ ] Unlock gates
            [ ] Inform neighbors
          data:
            priority: high

      - delay: "00:00:02"

      # Announce key items
      - service: tts.google_translate_say
        target:
          entity_id: media_player.living_room_speaker
        data:
          message: >
            Step 1. Close all windows and doors.
            Step 2. Move cars to driveway, facing out for quick exit.
            Step 3. Fill bathtubs with water.
            Step 4. Gather medications, documents, and emergency kit.
            Step 5. Put pets in carriers.
            Monitor ABC Emergency for updates.
```

---

## Family Location Check

Check and announce the status of all family members.

```yaml
script:
  family_location_check:
    alias: "Family Location Check"
    description: "Check emergency status for all family members"
    sequence:
      - service: notify.family_group
        data:
          title: "Family Emergency Check"
          message: |
            Current emergency status for family:

            🏠 Home: {{ 'ALERT' if is_state('binary_sensor.abc_emergency_home_active_alert', 'on') else 'Clear' }}
            {% if is_state('binary_sensor.abc_emergency_home_active_alert', 'on') %}
            Nearest: {{ states('sensor.abc_emergency_home_nearest_incident') }}km
            {% endif %}

            👨 Dad: {{ 'ALERT' if is_state('binary_sensor.abc_emergency_dad_active_alert', 'on') else 'Clear' }}
            {% if is_state('binary_sensor.abc_emergency_dad_active_alert', 'on') %}
            Nearest: {{ states('sensor.abc_emergency_dad_nearest_incident') }}km
            {% endif %}

            👩 Mum: {{ 'ALERT' if is_state('binary_sensor.abc_emergency_mum_active_alert', 'on') else 'Clear' }}
            {% if is_state('binary_sensor.abc_emergency_mum_active_alert', 'on') %}
            Nearest: {{ states('sensor.abc_emergency_mum_nearest_incident') }}km
            {% endif %}

            Reply with your status.
```

---

## Emergency Mode Activation

Activate a house-wide "emergency mode" with multiple actions.

```yaml
script:
  emergency_mode_on:
    alias: "Emergency Mode On"
    description: "Activate emergency mode for the house"
    sequence:
      # Set an input boolean to track mode
      - service: input_boolean.turn_on
        target:
          entity_id: input_boolean.emergency_mode

      # Flash exterior lights to alert neighbors
      - repeat:
          count: 3
          sequence:
            - service: light.turn_on
              target:
                entity_id: light.front_porch
              data:
                color_name: red
                brightness: 255
            - delay: "00:00:01"
            - service: light.turn_off
              target:
                entity_id: light.front_porch
            - delay: "00:00:01"

      # Leave exterior lights on red
      - service: light.turn_on
        target:
          entity_id:
            - light.front_porch
            - light.back_porch
        data:
          color_name: red
          brightness: 255

      # Interior lights bright white
      - service: light.turn_on
        target:
          entity_id:
            - light.living_room
            - light.kitchen
            - light.hallway
        data:
          brightness: 255
          color_temp_kelvin: 6500

      # Turn on all TVs to ABC
      - service: media_player.turn_on
        target:
          entity_id: media_player.living_room_tv

      # Announce
      - service: tts.google_translate_say
        target:
          entity_id: media_player.living_room_speaker
        data:
          message: >
            Emergency mode activated.
            {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'event_type') }}
            detected {{ states('sensor.abc_emergency_home_nearest_incident') }} kilometres away.
            Check TV for updates.

      # Notify everyone
      - service: notify.family_group
        data:
          title: "EMERGENCY MODE ACTIVATED"
          message: >
            Home is now in emergency mode.
            {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}
            is {{ states('sensor.abc_emergency_home_nearest_incident') }}km away.
          data:
            priority: critical

  emergency_mode_off:
    alias: "Emergency Mode Off"
    description: "Deactivate emergency mode"
    sequence:
      - service: input_boolean.turn_off
        target:
          entity_id: input_boolean.emergency_mode

      # Restore normal lighting
      - service: light.turn_on
        target:
          entity_id:
            - light.front_porch
            - light.back_porch
        data:
          color_temp_kelvin: 3000
          brightness: 128

      - service: scene.turn_on
        target:
          entity_id: scene.evening_lighting

      # Announce all clear
      - service: tts.google_translate_say
        target:
          entity_id: media_player.living_room_speaker
        data:
          message: >
            Emergency mode deactivated. Returning to normal operations.

      - service: notify.family_group
        data:
          title: "Emergency Mode Off"
          message: "Home has returned to normal mode. Stay safe."
```

**Supporting input_boolean:**

```yaml
input_boolean:
  emergency_mode:
    name: Emergency Mode
    icon: mdi:alert-circle
```

---

## Fire Danger Day Preparation

Prepare for high fire danger days proactively.

```yaml
script:
  fire_danger_prep:
    alias: "Fire Danger Day Preparation"
    description: "Prepare for high fire danger conditions"
    sequence:
      # Morning announcement
      - service: tts.google_translate_say
        target:
          entity_id: media_player.living_room_speaker
        data:
          message: >
            Good morning. Today is a high fire danger day.
            Currently {{ states('sensor.abc_emergency_nsw_bushfires') }} bushfires active in New South Wales.
            Remember to clear gutters, check your bushfire survival plan, and monitor conditions.

      # Send detailed checklist
      - service: notify.mobile_app_your_phone
        data:
          title: "Fire Danger Day Checklist"
          message: |
            High fire danger day - preparation checklist:

            Morning tasks:
            [ ] Check ABC Emergency for current incidents
            [ ] Clear any debris from gutters
            [ ] Move flammable items away from house
            [ ] Connect hoses and fill containers with water
            [ ] Ensure pets can be quickly secured

            Keep handy:
            [ ] Car keys and phones
            [ ] Important documents
            [ ] Medications

            Know your plan:
            [ ] Review evacuation routes
            [ ] Confirm meeting point with family
            [ ] Know when to leave (don't wait)

      # Set a reminder for evening
      - service: input_datetime.set_datetime
        target:
          entity_id: input_datetime.fire_danger_reminder
        data:
          time: "18:00:00"
```

---

## Emergency Info Summary

Generate a comprehensive emergency summary for sharing.

```yaml
script:
  emergency_summary:
    alias: "Generate Emergency Summary"
    description: "Create a text summary of current emergency conditions"
    fields:
      notify_target:
        description: "Notification service to send summary to"
        example: "notify.mobile_app_your_phone"
    sequence:
      - service: "{{ notify_target }}"
        data:
          title: "Emergency Summary - {{ now().strftime('%H:%M %d/%m') }}"
          message: |
            === ABC EMERGENCY SUMMARY ===

            🏠 HOME STATUS
            {% if is_state('binary_sensor.abc_emergency_home_active_alert', 'on') %}
            ⚠️ ACTIVE ALERT
            Nearest: {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}
            Distance: {{ states('sensor.abc_emergency_home_nearest_incident') }}km {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'direction') }}
            Level: {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'alert_level') }}
            Type: {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'event_type') }}
            {% else %}
            ✅ No active alerts near home
            {% endif %}

            📊 STATE OVERVIEW (NSW)
            Total Incidents: {{ states('sensor.abc_emergency_nsw_incidents_total') }}
            Bushfires: {{ states('sensor.abc_emergency_nsw_bushfires') }}
            Floods: {{ states('sensor.abc_emergency_nsw_floods') }}
            Storms: {{ states('sensor.abc_emergency_nsw_storms') }}
            Highest Level: {{ states('sensor.abc_emergency_nsw_highest_alert_level') }}

            🔗 More info: abc.net.au/emergency

            Generated: {{ now().strftime('%Y-%m-%d %H:%M:%S') }}
```

**Usage:**

```yaml
service: script.emergency_summary
data:
  notify_target: notify.mobile_app_your_phone
```

---

## Pet Evacuation Reminder

Special reminder for pet owners during emergencies.

```yaml
script:
  pet_evacuation_reminder:
    alias: "Pet Evacuation Reminder"
    description: "Remind about pet safety during evacuation"
    sequence:
      - service: notify.mobile_app_your_phone
        data:
          title: "PET EVACUATION REMINDER"
          message: |
            Don't forget your pets!

            🐕 Dogs:
            [ ] Leash and collar with ID
            [ ] Carrier or crate
            [ ] Food and water bowls
            [ ] Medications

            🐈 Cats:
            [ ] Secure carrier
            [ ] Litter tray and litter
            [ ] Food
            [ ] Medications

            🐦 Birds/Small Animals:
            [ ] Covered cage
            [ ] Food and water
            [ ] Towel for warmth

            🐴 Horses/Livestock:
            [ ] Open gates if you must leave them
            [ ] Remove rugs and halters if leaving
            [ ] Photograph and note identifying marks

            Never leave pets in vehicles!
          data:
            priority: high

      - service: tts.google_translate_say
        target:
          entity_id: media_player.living_room_speaker
        data:
          message: >
            Don't forget your pets during evacuation.
            Make sure all animals are secured in carriers or on leashes.
```

---

## Shelter in Place Mode

For situations where evacuation is not possible or advised.

```yaml
script:
  shelter_in_place:
    alias: "Shelter in Place Mode"
    description: "Activate shelter in place procedures"
    sequence:
      - service: input_boolean.turn_on
        target:
          entity_id: input_boolean.shelter_in_place

      # Close all blinds/covers
      - service: cover.close_cover
        target:
          entity_id: all

      # Turn on all interior lights
      - service: light.turn_on
        target:
          entity_id: light.all_interior
        data:
          brightness: 255

      # Announcement
      - service: tts.google_translate_say
        target:
          entity_id: media_player.living_room_speaker
        data:
          message: >
            Shelter in place mode activated.
            Close all windows and doors.
            Block gaps under doors with wet towels.
            Turn off air conditioning.
            Move to an interior room away from windows.
            Monitor ABC Emergency for updates.

      - service: notify.family_group
        data:
          title: "SHELTER IN PLACE"
          message: |
            Shelter in place mode activated.

            Immediate actions:
            [ ] Close all windows and doors
            [ ] Block gaps with wet towels
            [ ] Turn off A/C and fans
            [ ] Go to interior room

            Stay away from:
            - Windows
            - External walls
            - Attics

            Monitor ABC Emergency for all-clear.
          data:
            priority: critical
```

---

## Using Scripts in Automations

Trigger scripts from automations:

```yaml
automation:
  - id: abc_emergency_trigger_evacuation
    alias: "Trigger Evacuation Checklist on Emergency"
    trigger:
      - platform: state
        entity_id: binary_sensor.abc_emergency_home_emergency_warning
        to: "on"
    action:
      - service: script.evacuation_checklist
```

---

## Using Scripts with Voice Assistants

### Google Assistant / Alexa

Create a routine that calls your script:

```yaml
# In configuration.yaml, expose the script:
homeassistant:
  customize:
    script.emergency_briefing:
      google_assistant_type: script
      google_assistant_name: Emergency Briefing
```

Then say: "Hey Google, activate Emergency Briefing"

### With Assist

```yaml
intent_script:
  EmergencyBriefing:
    speech:
      text: "Getting emergency briefing"
    action:
      - service: script.emergency_briefing
```

---

## Script Dashboard Card

Create a dashboard card with emergency scripts:

```yaml
type: vertical-stack
cards:
  - type: markdown
    content: |
      ## Emergency Scripts
      Tap to activate emergency procedures
  - type: horizontal-stack
    cards:
      - type: button
        entity: script.emergency_briefing
        name: Briefing
        icon: mdi:bullhorn
        tap_action:
          action: call-service
          service: script.emergency_briefing
      - type: button
        entity: script.evacuation_checklist
        name: Evacuate
        icon: mdi:exit-run
        tap_action:
          action: call-service
          service: script.evacuation_checklist
  - type: horizontal-stack
    cards:
      - type: button
        entity: script.emergency_mode_on
        name: Emergency On
        icon: mdi:alert
        tap_action:
          action: call-service
          service: script.emergency_mode_on
      - type: button
        entity: script.emergency_mode_off
        name: All Clear
        icon: mdi:check-circle
        tap_action:
          action: call-service
          service: script.emergency_mode_off
```

---

## Next Steps

- [Automations Guide](automations.md) - Trigger scripts from automations
- [Notifications Guide](notifications.md) - Notification options
- [Advanced Usage](advanced.md) - Complex integrations
