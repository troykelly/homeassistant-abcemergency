# Notifications Guide

Comprehensive guide to setting up emergency notifications with ABC Emergency for Home Assistant.

---

## Overview

Emergency notifications are the primary way most users will interact with this integration. This guide covers:

- Mobile app notifications (iOS and Android)
- Critical alerts that bypass Do Not Disturb
- Actionable notifications
- Group notifications for families
- Third-party service integrations (Telegram, Discord, etc.)
- Email notifications
- Smart speaker announcements

---

## Mobile App Notifications

### Prerequisites

Install and configure the Home Assistant Companion App:
- **iOS:** [App Store](https://apps.apple.com/app/home-assistant/id1099568401)
- **Android:** [Google Play](https://play.google.com/store/apps/details?id=io.homeassistant.companion.android)

After setup, you'll have a notify service like `notify.mobile_app_your_phone`.

### Basic Notification

```yaml
service: notify.mobile_app_your_phone
data:
  title: "Emergency Alert"
  message: >
    {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}
    is {{ states('sensor.abc_emergency_home_nearest_incident') }}km away
```

### With Entity Picture

Include an image in the notification (requires external image URL):

```yaml
service: notify.mobile_app_your_phone
data:
  title: "Emergency Alert"
  message: "Active emergency nearby"
  data:
    image: "https://www.abc.net.au/emergency/img/icons/fire-icon.png"
```

### Notification Channel (Android)

Android allows notification channels for different alert types:

```yaml
service: notify.mobile_app_your_phone
data:
  title: "Emergency Alert"
  message: "Details here"
  data:
    channel: emergency_alerts
    importance: high
    vibrationPattern: "100, 1000, 100, 1000, 100"
    ledColor: red
```

---

## Critical Alerts

Critical alerts bypass Do Not Disturb and silent mode - use them only for genuine emergencies.

### iOS Critical Alerts

```yaml
service: notify.mobile_app_your_iphone
data:
  title: "EMERGENCY WARNING"
  message: >
    {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}
    is {{ states('sensor.abc_emergency_home_nearest_incident') }}km away!
  data:
    push:
      sound:
        name: default
        critical: 1
        volume: 1.0
```

**Note:** Critical alerts require enabling in iOS Settings:
1. Settings → Notifications → Home Assistant
2. Enable "Critical Alerts"

### Android High Priority

```yaml
service: notify.mobile_app_your_android
data:
  title: "EMERGENCY WARNING"
  message: >
    {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}
    is {{ states('sensor.abc_emergency_home_nearest_incident') }}km away!
  data:
    ttl: 0
    priority: high
    channel: alarm_stream
```

### Time-Sensitive Notifications (iOS 15+)

```yaml
service: notify.mobile_app_your_iphone
data:
  title: "WATCH AND ACT"
  message: "Take action now"
  data:
    push:
      interruption-level: time-sensitive
```

Interruption levels:
- `passive` - Silent delivery
- `active` - Default behavior
- `time-sensitive` - Breaks through Focus
- `critical` - Bypasses all settings (requires permission)

---

## Actionable Notifications

Add buttons to notifications for quick actions.

### iOS Actionable Notification

First, configure actions in your `configuration.yaml`:

```yaml
ios:
  push:
    categories:
      - name: Emergency Alert
        identifier: 'emergency_alert'
        actions:
          - identifier: 'VIEW_MAP'
            title: 'View Map'
            activationMode: 'foreground'
          - identifier: 'MARK_SAFE'
            title: 'Mark as Safe'
            activationMode: 'background'
          - identifier: 'CALL_000'
            title: 'Call 000'
            activationMode: 'foreground'
            destructive: true
```

Then send the notification:

```yaml
service: notify.mobile_app_your_iphone
data:
  title: "Emergency Warning"
  message: "Bushfire nearby"
  data:
    push:
      category: emergency_alert
```

Handle the action in an automation:

```yaml
automation:
  - id: abc_emergency_notification_action
    alias: "Handle Emergency Notification Action"
    trigger:
      - platform: event
        event_type: ios.notification_action_fired
        event_data:
          actionName: MARK_SAFE
    action:
      - service: input_boolean.turn_on
        target:
          entity_id: input_boolean.family_safe
```

### Android Actionable Notification

```yaml
service: notify.mobile_app_your_android
data:
  title: "Emergency Warning"
  message: "Bushfire nearby"
  data:
    actions:
      - action: "VIEW_MAP"
        title: "View Map"
      - action: "MARK_SAFE"
        title: "Mark as Safe"
      - action: "URI"
        title: "ABC Emergency"
        uri: "https://www.abc.net.au/emergency"
```

---

## Group Notifications

Send notifications to multiple family members at once.

### Create a Notification Group

In `configuration.yaml`:

```yaml
notify:
  - name: family_group
    platform: group
    services:
      - service: mobile_app_mum_iphone
      - service: mobile_app_dad_android
      - service: mobile_app_child_phone
```

### Use the Group

```yaml
service: notify.family_group
data:
  title: "Family Emergency Alert"
  message: >
    Emergency near our home!
    {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}
    is {{ states('sensor.abc_emergency_home_nearest_incident') }}km away.
```

---

## Telegram Integration

Send alerts via Telegram for cross-platform coverage.

### Setup

1. Create a Telegram bot via [@BotFather](https://t.me/botfather)
2. Get your chat ID
3. Add to `configuration.yaml`:

```yaml
telegram_bot:
  - platform: polling
    api_key: YOUR_BOT_API_KEY
    allowed_chat_ids:
      - YOUR_CHAT_ID

notify:
  - name: telegram_emergency
    platform: telegram
    chat_id: YOUR_CHAT_ID
```

### Send Alert

```yaml
service: notify.telegram_emergency
data:
  title: "ABC Emergency Alert"
  message: >
    *{{ state_attr('sensor.abc_emergency_home_nearest_incident', 'event_type') }}*

    {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}

    📍 Distance: {{ states('sensor.abc_emergency_home_nearest_incident') }}km
    🧭 Direction: {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'direction') }}
    ⚠️ Level: {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'alert_level') }}

    [View on ABC Emergency](https://www.abc.net.au/emergency)
```

### With Inline Buttons

```yaml
service: telegram_bot.send_message
data:
  target: YOUR_CHAT_ID
  message: "Emergency Alert - Respond with your status"
  inline_keyboard:
    - - text: "I'm Safe"
        callback_data: "/safe"
      - text: "Need Help"
        callback_data: "/help"
```

---

## Discord Integration

Send alerts to a Discord channel or user.

### Setup

1. Create a webhook in your Discord server
2. Add to `configuration.yaml`:

```yaml
notify:
  - name: discord_emergency
    platform: discord
    token: YOUR_BOT_TOKEN
```

### Send Alert

```yaml
service: notify.discord_emergency
data:
  target: YOUR_CHANNEL_ID
  title: "ABC Emergency Alert"
  message: >
    **{{ state_attr('sensor.abc_emergency_home_nearest_incident', 'event_type') }}**

    {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}

    📍 **Distance:** {{ states('sensor.abc_emergency_home_nearest_incident') }}km
    🧭 **Direction:** {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'direction') }}
  data:
    embed:
      color: 16711680  # Red
```

---

## Signal Messenger

Using the Signal Messenger integration:

```yaml
notify:
  - name: signal_emergency
    platform: signal_messenger
    url: "http://localhost:8080"  # signal-cli-rest-api URL
    number: "+61400000000"
    recipients:
      - "+61400111111"
      - "+61400222222"
```

```yaml
service: notify.signal_emergency
data:
  message: >
    🚨 EMERGENCY ALERT

    {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'event_type') }}:
    {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}

    Distance: {{ states('sensor.abc_emergency_home_nearest_incident') }}km
    Direction: {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'direction') }}

    Check ABC Emergency: https://www.abc.net.au/emergency
```

---

## Email Notifications

For less urgent updates or digests.

### Setup SMTP

In `configuration.yaml`:

```yaml
notify:
  - name: email_emergency
    platform: smtp
    server: smtp.gmail.com
    port: 587
    sender: your.email@gmail.com
    username: your.email@gmail.com
    password: YOUR_APP_PASSWORD
    recipient:
      - family@example.com
    sender_name: Home Assistant Emergency
```

### Send Email

```yaml
service: notify.email_emergency
data:
  title: "ABC Emergency Alert - {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'event_type') }}"
  message: >
    Emergency Alert

    Type: {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'event_type') }}
    Headline: {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}
    Distance: {{ states('sensor.abc_emergency_home_nearest_incident') }}km
    Direction: {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'direction') }}
    Alert Level: {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'alert_level') }}

    For more information, visit: https://www.abc.net.au/emergency

    --
    This is an automated message from Home Assistant.
```

### HTML Email

```yaml
service: notify.email_emergency
data:
  title: "Emergency Alert"
  message: "See HTML version"
  data:
    html: >
      <h1 style="color: red;">Emergency Alert</h1>
      <p><strong>{{ state_attr('sensor.abc_emergency_home_nearest_incident', 'event_type') }}</strong></p>
      <p>{{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}</p>
      <table>
        <tr><td>Distance:</td><td>{{ states('sensor.abc_emergency_home_nearest_incident') }}km</td></tr>
        <tr><td>Direction:</td><td>{{ state_attr('sensor.abc_emergency_home_nearest_incident', 'direction') }}</td></tr>
      </table>
      <p><a href="https://www.abc.net.au/emergency">View on ABC Emergency</a></p>
```

---

## Smart Speaker Announcements

### Google Home / Nest

```yaml
service: tts.google_translate_say
target:
  entity_id:
    - media_player.living_room_speaker
    - media_player.bedroom_speaker
data:
  message: >
    Attention. Emergency Alert.
    {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'event_type') }}
    detected {{ states('sensor.abc_emergency_home_nearest_incident') }} kilometres
    to the {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'direction') }}.
    {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}.
    Check ABC Emergency for more information.
```

### Amazon Alexa

Using Alexa Media Player integration:

```yaml
service: notify.alexa_media
data:
  target:
    - media_player.living_room_echo
    - media_player.kitchen_echo
  message: >
    <voice name="Nicole">
    <amazon:emotion name="excited" intensity="high">
    Attention! Emergency Alert!
    </amazon:emotion>
    {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'event_type') }}
    detected {{ states('sensor.abc_emergency_home_nearest_incident') }} kilometres away.
    {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}.
    </voice>
  data:
    type: announce
```

### Apple HomePod

```yaml
service: tts.cloud_say
target:
  entity_id: media_player.homepod
data:
  message: >
    Emergency Alert.
    {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'event_type') }}
    {{ states('sensor.abc_emergency_home_nearest_incident') }} kilometres away.
  options:
    voice: en-AU-Standard-A
```

---

## Notification Templates

### Emergency Levels

Create reusable notification templates using scripts or blueprints.

```yaml
script:
  emergency_notify_advice:
    alias: "Send Advice Level Notification"
    sequence:
      - service: notify.mobile_app_your_phone
        data:
          title: "Emergency Advice"
          message: >
            {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}
            ({{ states('sensor.abc_emergency_home_nearest_incident') }}km
            {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'direction') }})

  emergency_notify_watch_and_act:
    alias: "Send Watch and Act Notification"
    sequence:
      - service: notify.mobile_app_your_phone
        data:
          title: "WATCH AND ACT"
          message: >
            Take action now!
            {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}
            is {{ states('sensor.abc_emergency_home_nearest_incident') }}km to the
            {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'direction') }}
          data:
            priority: high

  emergency_notify_emergency_warning:
    alias: "Send Emergency Warning Notification"
    sequence:
      - service: notify.mobile_app_your_phone
        data:
          title: "EMERGENCY WARNING"
          message: >
            ACT IMMEDIATELY!
            {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}
            is {{ states('sensor.abc_emergency_home_nearest_incident') }}km away!
          data:
            priority: critical
            push:
              sound:
                critical: 1
                volume: 1.0
```

---

## Rate Limiting

Avoid notification spam with conditions and delays.

```yaml
automation:
  - id: abc_emergency_rate_limited
    alias: "ABC Emergency - Rate Limited Notification"
    trigger:
      - platform: state
        entity_id: binary_sensor.abc_emergency_home_active_alert
        to: "on"
    condition:
      # Don't send if we've notified in the last 30 minutes
      - condition: template
        value_template: >
          {{ (as_timestamp(now()) - as_timestamp(state_attr('automation.abc_emergency_rate_limited', 'last_triggered'))) > 1800 }}
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Emergency Alert"
          message: "Active emergency nearby"
```

Or use an input_datetime to track:

```yaml
input_datetime:
  last_emergency_notification:
    name: Last Emergency Notification
    has_date: true
    has_time: true

automation:
  - id: abc_emergency_rate_limited_v2
    alias: "ABC Emergency - Rate Limited v2"
    trigger:
      - platform: state
        entity_id: binary_sensor.abc_emergency_home_active_alert
        to: "on"
    condition:
      - condition: template
        value_template: >
          {{ (now() - states('input_datetime.last_emergency_notification') | as_datetime).total_seconds() > 1800 }}
    action:
      - service: input_datetime.set_datetime
        target:
          entity_id: input_datetime.last_emergency_notification
        data:
          datetime: "{{ now().isoformat() }}"
      - service: notify.mobile_app_your_phone
        data:
          title: "Emergency Alert"
          message: "Active emergency nearby"
```

---

## Notification Debugging

### Check Notification Service

```yaml
service: notify.mobile_app_your_phone
data:
  title: "Test Notification"
  message: "If you see this, notifications are working!"
```

### View Notification History

Check the Home Assistant logs:
**Settings** → **System** → **Logs**

Search for `notify` or your device name.

### Common Issues

| Issue | Solution |
|-------|----------|
| No notifications | Check device is registered in HA Companion App |
| Delayed notifications | Check phone battery optimization settings |
| Critical alerts not working | Enable in iOS Settings |
| Android channels not working | Recreate channel or reinstall app |

---

## Next Steps

- [Automations Guide](automations.md) - Complete automation examples
- [Scripts Guide](scripts.md) - Emergency scripts and sequences
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
