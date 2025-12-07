# Glossary

Definitions of terms used in ABC Emergency documentation.

---

## Home Assistant Terms

### Entity
A data point in Home Assistant representing something that can be tracked or controlled. Examples include sensors, switches, and lights. Each entity has a unique Entity ID.

### Sensor
An entity that reports a value, such as a number or text. ABC Emergency sensors report incident counts, distances, and alert levels.

### Binary Sensor
An entity that can only be in one of two states: **on** or **off**. Used to represent true/false conditions like "is there an alert active?"

### Geo-Location Entity
A special entity type with latitude/longitude coordinates that can be displayed on the Home Assistant map. ABC Emergency creates these for each incident.

### Automation
Rules that trigger actions based on conditions. For example, "when the emergency_warning binary sensor turns on, send a notification."

### Blueprint
A reusable automation template that can be imported and configured. ABC Emergency provides several ready-to-use blueprints.

### Zone
A named geographic area in Home Assistant, defined by coordinates and a radius. Commonly used for home, work, or school locations.

### Person
A Home Assistant entity that tracks an individual's location, usually via the Companion App on their phone.

### Config Entry
A configured instance of an integration. You can have multiple config entries for ABC Emergency (e.g., one for home, one for work).

### HACS
Home Assistant Community Store - a third-party tool for installing and managing custom integrations, cards, and themes.

### Companion App
The official Home Assistant mobile app for iOS and Android that provides location tracking, notifications, and remote access.

---

## Emergency Terms

### ABC Emergency
The Australian Broadcasting Corporation's emergency information service that aggregates data from state and territory emergency services across Australia.

### Australian Warning System
A national framework for emergency warnings used by all Australian states and territories. Uses three levels: Advice (yellow), Watch and Act (orange), and Emergency Warning (red).

### Emergency Warning
The highest alert level in the Australian Warning System (red). Indicates you may be in danger and need to take action immediately to protect yourself.

### Watch and Act
The middle alert level in the Australian Warning System (orange). Indicates there is a heightened level of threat and conditions are changing. You need to start taking action now.

### Advice
The lowest official warning level in the Australian Warning System (yellow). Indicates an incident has started. Stay informed and monitor conditions.

### Bushfire
A fire burning in the bush, forest, or grassland. Known as "wildfire" in other countries. Australia's most common emergency type during summer months.

### Hazard Reduction Burn
A controlled, planned fire used to reduce fuel loads and lower bushfire risk. Also called "planned burn" or "prescribed burn."

---

## Australian Emergency Services

### RFS
Rural Fire Service - the volunteer firefighting organization in New South Wales.

### CFA
Country Fire Authority - the volunteer firefighting organization in Victoria.

### QFES
Queensland Fire and Emergency Services.

### CFS
Country Fire Service - the volunteer firefighting organization in South Australia.

### SES
State Emergency Service - handles floods, storms, and other non-fire emergencies in each state.

### Bureau of Meteorology (BOM)
Australia's national weather, climate, and water agency. Issues severe weather warnings.

---

## Technical Terms

### API
Application Programming Interface - the way software systems communicate. ABC Emergency uses an API to fetch emergency data.

### Polling
Periodically checking for updates. ABC Emergency polls the ABC API every 5 minutes for new data.

### Coordinator
A Home Assistant component that manages data updates and distributes data to entities. Ensures efficient API usage.

### Entity ID
A unique identifier for an entity in Home Assistant, following the pattern `domain.name` (e.g., `sensor.abc_emergency_home_nearest_incident`).

### Geohash
A system that encodes geographic coordinates into a short string. Used by the ABC Emergency API for location-based filtering.

### Haversine
A formula for calculating the great-circle distance between two points on a sphere. Used to calculate distances to incidents.

---

## Abbreviations

| Abbreviation | Meaning |
|--------------|---------|
| ABC | Australian Broadcasting Corporation |
| HA | Home Assistant |
| HACS | Home Assistant Community Store |
| TTS | Text-to-Speech |
| GPS | Global Positioning System |
| API | Application Programming Interface |
| BOM | Bureau of Meteorology |
| RFS | Rural Fire Service (NSW) |
| CFA | Country Fire Authority (VIC) |
| SES | State Emergency Service |
