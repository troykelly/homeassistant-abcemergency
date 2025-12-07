# Entities Reference

Complete documentation for all entities created by ABC Emergency for Home Assistant.

[![Open Developer Tools States](https://my.home-assistant.io/badges/developer_states.svg)](https://my.home-assistant.io/redirect/developer_states/)

Use Developer Tools to view entity states in your Home Assistant instance.

---

## Entity Naming Convention

All entities follow the naming pattern:

```
{domain}.abc_emergency_{instance_name}_{entity_key}
```

Where:
- `{domain}` - `sensor`, `binary_sensor`, or `geo_location`
- `{instance_name}` - Your configured name (e.g., "home", "nsw", "dad")
- `{entity_key}` - The specific entity type (e.g., "incidents_total")

**Examples:**
- `sensor.abc_emergency_home_incidents_total`
- `binary_sensor.abc_emergency_nsw_emergency_warning`
- `sensor.abc_emergency_dad_nearest_incident`

<details>
<summary>How do Entity IDs work?</summary>

Entity IDs in Home Assistant follow a pattern: `domain.unique_name`

For ABC Emergency:
```
sensor.abc_emergency_home_incidents_total
│      │              │    └── Entity type
│      │              └── Your instance name
│      └── Integration name
└── Entity domain (sensor, binary_sensor, etc.)
```

Your instance name comes from what you configured during setup. If you named your zone "Home", entities use `home`. If "Beach House", they use `beach_house`.

</details>

<details>
<summary>What is a Binary Sensor?</summary>

A binary sensor is a Home Assistant entity that can only be in one of two states: **on** or **off**.

For ABC Emergency, binary sensors indicate whether a condition is true:
- `on` = Alert is active
- `off` = No alert

Binary sensors are ideal for automation triggers because the state change from `off` to `on` is easy to detect.

</details>

---

## Sensors

### All Instance Types

These sensors are created for State, Zone, and Person modes.

#### incidents_total

| Property | Value |
|----------|-------|
| **Entity ID** | `sensor.abc_emergency_*_incidents_total` |
| **State** | Integer count of total active incidents |
| **State Class** | `measurement` |
| **Unit** | None |

**Description:** Total count of all active emergency incidents in the monitored area. For State mode, this is the entire state. For Zone/Person modes, this is all incidents in the state (not filtered by radius).

**Example state:** `42`

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `incidents` | list | Array of all incidents with details |

Each incident in the `incidents` list contains:
- `headline` (string): Incident location description
- `alert_level` (string): Warning level (extreme, severe, moderate, minor)
- `event_type` (string): Type of incident (Bushfire, Flood, Storm, etc.)
- `distance_km` (float\|null): Distance from monitored location in km
- `direction` (string\|null): Compass direction (N, NE, E, etc.)

**Example attributes:**
```yaml
incidents:
  - headline: "Milsons Gully"
    alert_level: "extreme"
    event_type: "Bushfire"
    distance_km: 12.4
    direction: "NW"
  - headline: "Mount Victoria"
    alert_level: "severe"
    event_type: "Bushfire"
    distance_km: 28.7
    direction: "W"
```

---

#### highest_alert_level

| Property | Value |
|----------|-------|
| **Entity ID** | `sensor.abc_emergency_*_highest_alert_level` |
| **State** | Alert level string |
| **State Class** | None |
| **Unit** | None |

**Description:** The highest active alert level in the monitored area.

**Possible states:**
| State | Australian Warning System | Meaning |
|-------|---------------------------|---------|
| `Emergency` | Emergency Warning (Red) | Highest level - immediate danger |
| `Watch and Act` | Watch and Act (Orange) | Heightened threat - prepare to act |
| `Advice` | Advice (Yellow) | Incident occurring - stay informed |
| `none` | No active alerts | No warnings currently active |

**Example state:** `Watch and Act`

---

#### bushfires

| Property | Value |
|----------|-------|
| **Entity ID** | `sensor.abc_emergency_*_bushfires` |
| **State** | Integer count |
| **State Class** | `measurement` |
| **Unit** | None |

**Description:** Count of active bushfire/grass fire incidents.

**Example state:** `7`

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `incidents` | list | Array of bushfire incidents only |

Each incident contains: `headline`, `alert_level`, `event_type`, `distance_km`, `direction`

**Example attributes:**
```yaml
incidents:
  - headline: "Milsons Gully"
    alert_level: "extreme"
    event_type: "Bushfire"
    distance_km: 12.4
    direction: "NW"
```

---

#### floods

| Property | Value |
|----------|-------|
| **Entity ID** | `sensor.abc_emergency_*_floods` |
| **State** | Integer count |
| **State Class** | `measurement` |
| **Unit** | None |

**Description:** Count of active flood incidents.

**Example state:** `3`

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `incidents` | list | Array of flood incidents only |

Each incident contains: `headline`, `alert_level`, `event_type`, `distance_km`, `direction`

---

#### storms

| Property | Value |
|----------|-------|
| **Entity ID** | `sensor.abc_emergency_*_storms` |
| **State** | Integer count |
| **State Class** | `measurement` |
| **Unit** | None |

**Description:** Count of active storm/severe weather incidents.

**Example state:** `12`

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `incidents` | list | Array of storm incidents only |

Each incident contains: `headline`, `alert_level`, `event_type`, `distance_km`, `direction`

---

### Zone/Person Mode Only

These sensors are only created for Zone and Person mode instances (not State mode).

#### incidents_nearby

| Property | Value |
|----------|-------|
| **Entity ID** | `sensor.abc_emergency_*_incidents_nearby` |
| **State** | Integer count |
| **State Class** | `measurement` |
| **Unit** | None |

**Description:** Count of incidents within your configured alert radii. Different incident types have different radii (e.g., bushfires 50km, structure fires 10km).

**Example state:** `2`

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `incidents` | list | Array of nearby incidents with details |

Each incident in the `incidents` list contains:
- `headline` (string): Incident location description
- `alert_level` (string): Warning level (extreme, severe, moderate, minor)
- `event_type` (string): Type of incident (Bushfire, Flood, Storm, etc.)
- `distance_km` (float): Distance from monitored location in km
- `direction` (string): Compass direction (N, NE, E, etc.)

**Example attributes:**
```yaml
incidents:
  - headline: "Milsons Gully"
    alert_level: "extreme"
    event_type: "Bushfire"
    distance_km: 12.4
    direction: "NW"
  - headline: "Severe Thunderstorm"
    alert_level: "moderate"
    event_type: "Storm"
    distance_km: 45.0
    direction: "SE"
```

---

#### nearest_incident

| Property | Value |
|----------|-------|
| **Entity ID** | `sensor.abc_emergency_*_nearest_incident` |
| **State** | Distance in kilometers |
| **Device Class** | `distance` |
| **State Class** | `measurement` |
| **Unit** | `km` |

**Description:** Distance to the nearest emergency incident from your monitored location.

**State:** Numeric value in kilometers, rounded to 1 decimal place. Returns `unknown` if no incidents exist.

**Example state:** `12.4`

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `headline` | string | Brief description of the incident |
| `alert_level` | string | Warning level (Emergency, Watch and Act, Advice) |
| `event_type` | string | Type of incident (Bushfire, Flood, Storm, etc.) |
| `direction` | string | Compass direction to the incident (N, NE, E, etc.) |

**Example attributes:**
```yaml
headline: "Milsons Gully"
alert_level: "Emergency"
event_type: "Bushfire"
direction: "NW"
```

---

## Binary Sensors

Binary sensors are created for all instance types and are ideal for automations.

### active_alert

| Property | Value |
|----------|-------|
| **Entity ID** | `binary_sensor.abc_emergency_*_active_alert` |
| **Device Class** | `safety` |
| **On when** | Any incident is active |

**Description:** Indicates whether there are any active emergency incidents in your monitored area.

**Behavior by mode:**
- **State mode:** On when `incidents_total > 0`
- **Zone/Person mode:** On when `incidents_nearby > 0` (within your radii)

---

### emergency_warning

| Property | Value |
|----------|-------|
| **Entity ID** | `binary_sensor.abc_emergency_*_emergency_warning` |
| **Device Class** | `safety` |
| **On when** | Emergency Warning (red) level active |

**Description:** Indicates the highest alert level - Emergency Warning. This means you may be in danger and should act immediately.

**Attributes (when on):**

For Zone/Person modes:
| Attribute | Type | Description |
|-----------|------|-------------|
| `count` | integer | Number of Emergency Warning incidents |
| `nearest_headline` | string | Description of nearest red-level incident |
| `nearest_distance_km` | float | Distance to nearest in km |
| `nearest_direction` | string | Compass direction |

For State mode:
| Attribute | Type | Description |
|-----------|------|-------------|
| `count` | integer | Total Emergency Warning incidents in state |
| `headline` | string | Description of first red-level incident |

---

### watch_and_act

| Property | Value |
|----------|-------|
| **Entity ID** | `binary_sensor.abc_emergency_*_watch_and_act` |
| **Device Class** | `safety` |
| **On when** | Watch and Act (orange) OR Emergency Warning (red) active |

**Description:** Indicates Watch and Act level or higher. Conditions are changing and you should prepare to take action.

**Note:** This sensor is "on" for both Watch and Act AND Emergency Warning levels, making it useful for "at least this severity" automations.

**Attributes:** Same structure as `emergency_warning`, but includes incidents at both levels.

---

### advice

| Property | Value |
|----------|-------|
| **Entity ID** | `binary_sensor.abc_emergency_*_advice` |
| **Device Class** | `safety` |
| **On when** | Any warning level active (Advice, Watch and Act, or Emergency Warning) |

**Description:** Indicates any official warning is active. An incident has started and you should stay informed.

**Note:** This is the most sensitive alert level - it turns on for any official warning.

---

## Binary Sensor Hierarchy

The binary sensors form a hierarchy where higher-level sensors also trigger lower ones:

```
emergency_warning: ON → watch_and_act: ON → advice: ON → active_alert: ON
```

| Scenario | emergency_warning | watch_and_act | advice | active_alert |
|----------|-------------------|---------------|--------|--------------|
| No incidents | OFF | OFF | OFF | OFF |
| Minor incident (no warning) | OFF | OFF | OFF | ON |
| Advice level | OFF | OFF | ON | ON |
| Watch and Act | OFF | ON | ON | ON |
| Emergency Warning | ON | ON | ON | ON |

---

## Geo-Location Entities

When enabled, the integration creates geo-location entities for mapping incidents.

### Geo-Location Entity

| Property | Value |
|----------|-------|
| **Entity ID** | `geo_location.abc_emergency_*_{incident_id}` |
| **State** | Distance in km |
| **Latitude** | Incident location |
| **Longitude** | Incident location |

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `source` | string | Instance title for map filtering (e.g., `ABC Emergency (Home)`) |
| `agency` | string | Reporting emergency service (e.g., `NSW Rural Fire Service`) |
| `alert_level` | string | Warning level |
| `alert_text` | string | Warning level text (e.g., `Advice`, `Watch and Act`, `Emergency`) |
| `event_type` | string | Type of incident |
| `event_icon` | string | Icon identifier for the event type |
| `status` | string | Current incident status |
| `direction` | string | Compass direction from monitored location |
| `updated` | string | ISO 8601 timestamp of last update |
| `size` | string | Affected area size (for fires, when available) |

**Note:** The `source` attribute matches your configuration title exactly. Use this in map card `geo_location_sources` to filter incidents by instance. For example:

```yaml
type: map
geo_location_sources:
  - "ABC Emergency (Home)"  # Must be quoted due to spaces/parentheses
```

---

## Using Entities in Automations

### Triggering on Warning Levels

```yaml
# Trigger on any warning
trigger:
  - platform: state
    entity_id: binary_sensor.abc_emergency_home_advice
    to: "on"

# Trigger on Watch and Act or higher
trigger:
  - platform: state
    entity_id: binary_sensor.abc_emergency_home_watch_and_act
    to: "on"

# Trigger only on Emergency Warning
trigger:
  - platform: state
    entity_id: binary_sensor.abc_emergency_home_emergency_warning
    to: "on"
```

### Triggering on Distance

```yaml
# Trigger when nearest incident is within 20km
trigger:
  - platform: numeric_state
    entity_id: sensor.abc_emergency_home_nearest_incident
    below: 20

# Trigger when nearest incident gets closer than 10km
trigger:
  - platform: numeric_state
    entity_id: sensor.abc_emergency_home_nearest_incident
    below: 10
```

### Using Attributes in Messages

```yaml
action:
  - service: notify.mobile_app_phone
    data:
      title: "Emergency Alert"
      message: >
        {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'headline') }}
        is {{ states('sensor.abc_emergency_home_nearest_incident') }}km to the
        {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'direction') }}
```

### Conditional Logic Based on Event Type

```yaml
condition:
  - condition: template
    value_template: >
      {{ state_attr('sensor.abc_emergency_home_nearest_incident', 'event_type') == 'Bushfire' }}
```

### Using Incidents List in Messages

Access the list of incidents from count sensors:

```yaml
action:
  - service: notify.mobile_app_phone
    data:
      title: "{{ states('sensor.abc_emergency_home_bushfires') }} Active Bushfires"
      message: >
        {% set fires = state_attr('sensor.abc_emergency_home_bushfires', 'incidents') %}
        {% for fire in fires %}
        - {{ fire.headline }} ({{ fire.distance_km }}km {{ fire.direction }}) - {{ fire.alert_level }}
        {% endfor %}
```

### Iterating Over All Nearby Incidents

```yaml
# Create a summary of all nearby incidents
action:
  - service: notify.mobile_app_phone
    data:
      title: "Emergency Update"
      message: >
        {% set incidents = state_attr('sensor.abc_emergency_home_incidents_nearby', 'incidents') %}
        {{ incidents | length }} incidents nearby:
        {% for inc in incidents %}
        - {{ inc.event_type }}: {{ inc.headline }} ({{ inc.distance_km }}km)
        {% endfor %}
```

---

## Entity State Diagrams

### Binary Sensor State Flow

```
┌──────────────────────────────────────────────────────────────┐
│                    No Active Incidents                       │
│                                                              │
│  active_alert: OFF    advice: OFF    watch_and_act: OFF      │
│  emergency_warning: OFF                                      │
└────────────────────────────┬─────────────────────────────────┘
                             │ Incident starts
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                    Minor Incident (no warning)               │
│                                                              │
│  active_alert: ON     advice: OFF    watch_and_act: OFF      │
│  emergency_warning: OFF                                      │
└────────────────────────────┬─────────────────────────────────┘
                             │ Advice warning issued
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                    Advice Level                              │
│                                                              │
│  active_alert: ON     advice: ON     watch_and_act: OFF      │
│  emergency_warning: OFF                                      │
└────────────────────────────┬─────────────────────────────────┘
                             │ Upgraded to Watch and Act
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                    Watch and Act Level                       │
│                                                              │
│  active_alert: ON     advice: ON     watch_and_act: ON       │
│  emergency_warning: OFF                                      │
└────────────────────────────┬─────────────────────────────────┘
                             │ Upgraded to Emergency Warning
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                    Emergency Warning Level                   │
│                                                              │
│  active_alert: ON     advice: ON     watch_and_act: ON       │
│  emergency_warning: ON                                       │
└──────────────────────────────────────────────────────────────┘
```

---

## Event Types

The `event_type` attribute can contain various values depending on the incident:

| Event Type | Description |
|------------|-------------|
| `Bushfire` | Bush or grass fire |
| `Structure Fire` | Building fire |
| `Flood` | Flooding event |
| `Storm` | Severe storm |
| `Thunderstorm` | Electrical storm |
| `Earthquake` | Seismic event |
| `Extreme Heat` | Heatwave warning |
| `Heatwave` | Extended heat event |
| `Cyclone` | Tropical cyclone |
| `Planned Burn` | Hazard reduction burn |
| `Burn Off` | Controlled burn |
| `Other` | Miscellaneous events |

---

## Diagnostic Information

For troubleshooting, entities include diagnostic information accessible via:

[![Open Integrations](https://my.home-assistant.io/badges/integrations.svg)](https://my.home-assistant.io/redirect/integrations/)

Navigate to **ABC Emergency** → **[Your Instance]** → **Download Diagnostics**

Or manually: **Settings** → **Devices & Services** → **ABC Emergency** → **[Your Instance]** → **Download Diagnostics**

This includes:
- Current sensor states
- Cached incident data
- Configuration options
- Last update timestamp
- API response information
