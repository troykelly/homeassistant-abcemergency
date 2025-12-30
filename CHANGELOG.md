# Changelog

All notable changes to ABC Emergency for Home Assistant.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.4.5] - 2025-12-30

### Fixed

- **Longitude normalization** - Fixed state determination for locations with longitude outside the standard -180 to 180 range
  - Longitude -237.115606 now correctly normalizes to 122.884394 (Western Australia)
  - Normalization applied at start of `get_state_from_coordinates()` before checking state bounding boxes

## [0.4.4] - 2025-12-30

### Fixed

- **Entity ID predictability** - Geo-location entities now use explicit entity IDs matching the format exposed in sensor `entity_ids` attributes
  - Previous: Entity IDs generated from headline (could collide for duplicate headlines)
  - New: Entity IDs follow format `geo_location.{source}_{incident_id}` matching sensor references
  - Eliminates mismatch between sensor `entity_ids` attribute and actual geo-location entity IDs

## [0.4.3] - 2025-12-30

### Added

- **Entity discovery attributes** - Sensors and binary sensors now expose entity IDs for dynamic geo-location entity discovery
  - `entity_ids` attribute on count sensors: `incidents_total`, `bushfires`, `floods`, `storms`, `incidents_nearby`
  - `containing_entity_ids` attribute on containment binary sensors
- **Alert-level count sensors** - New sensors for filtering by Australian Warning System level:
  - `sensor.*_emergency_warnings` - Count of incidents at Emergency Warning (red) level
  - `sensor.*_watch_and_acts` - Count of incidents at Watch and Act (orange) level
  - `sensor.*_advices` - Count of incidents at Advice (yellow) level
  - Each includes `entity_ids`, `incidents`, and `containing_count` attributes

## [0.4.2] - 2025-12-30

### Added

- **GeoJSON geometry exposure** - Geo-location entities now expose polygon geometry data for map rendering
  - `geojson_geometry` attribute with full GeoJSON geometry object (Point or Polygon)
  - `geometry_type` attribute indicating "Point" or "Polygon"
  - `polygon_coordinates` attribute with coordinate arrays (when polygon available)
  - Supports single polygons, multi-polygons, and inner rings (holes)
  - Enables [ABC Emergency Map Card](https://github.com/troykelly/lovelace-abc-emergency-map) to render incident boundaries

## [0.4.1] - 2025-12-08

### Added

- **Containment Severity Change Event** - New `abc_emergency_containment_severity_changed` event fires when an emergency's alert level changes while you're inside its polygon
  - Enables automations to respond to escalation (e.g., Advice → Emergency Warning) or de-escalation
  - Event includes `previous_alert_level`, `new_alert_level`, and `escalated` boolean flag
- New automation examples in documentation for severity escalation alerts

### Changed

- **Refactored containment tracking** - Now tracks actual containment state per incident rather than just IDs
  - Enables detection of polygon boundary changes (expansion/contraction)
  - Polygon expansion now correctly fires `abc_emergency_entered_polygon`
  - Polygon contraction now correctly fires `abc_emergency_exited_polygon`

### Fixed

- Containment events now fire correctly when polygon boundaries change without the incident ID changing
- Exit events now fire when a polygon shrinks to no longer contain your location (even if the incident still exists)

## [0.4.0] - 2025-12-08

### Added

- **Point-in-Polygon Containment Detection** - Detect when your monitored location is inside an emergency polygon boundary, not just nearby
- New binary sensors (Zone/Person modes only):
  - `binary_sensor.abc_emergency_*_inside_polygon` - Inside any emergency polygon
  - `binary_sensor.abc_emergency_*_inside_emergency_warning` - Inside Emergency Warning (red) polygon
  - `binary_sensor.abc_emergency_*_inside_watch_and_act` - Inside Watch and Act (orange+) polygon
  - `binary_sensor.abc_emergency_*_inside_advice` - Inside Advice (yellow+) polygon
- New events (Zone/Person modes only):
  - `abc_emergency_entered_polygon` - Fired when entering a polygon
  - `abc_emergency_exited_polygon` - Fired when exiting a polygon
  - `abc_emergency_inside_polygon` - Fired each update while inside
- New sensor attributes:
  - `contains_point` - Whether incident polygon contains your location
  - `has_polygon` - Whether incident has polygon geometry data
  - `containing_count` - Number of polygons containing your location
  - `inside_polygon` - Quick boolean flag for template use
  - `highest_containing_level` - Highest alert level of containing incidents
- Added `shapely` dependency for accurate geospatial polygon calculations
- Comprehensive documentation for containment detection
- TTL-based cleanup for seen incident storage to prevent unbounded growth
- Cached Shapely prepared geometries for efficient containment checks

### Changed

- EmergencyIncident model now stores polygon geometry data
- Coordinator performs containment checks during each update cycle

### Fixed

- Added missing containment binary sensor translations
- Added types-shapely for mypy type checking in CI

## [0.3.0] - 2025-12-07

### Added
- my.home-assistant.io one-click buttons throughout documentation for easier navigation
- Importable Home Assistant Blueprints for common automations (Basic Alert, Tiered Notifications, Distance Escalation, TTS Announcement, Light Alert, Family Safety)
- FAQ documentation with common questions and answers
- Glossary of Australian emergency terminology
- Documentation index (`docs/README.md`) for easier navigation
- Collapsible technical explanations for beginners throughout documentation
- Additional shields.io badges for Home Assistant and Python version compatibility

### Changed
- Improved documentation structure with better organization
- Event documentation moved to user-facing docs (`docs/automations.md`)

## [0.2.0] - 2025-12-07

### Added
- **Instance-based map filtering** - Geo-location entities now use the config entry title as `source` attribute
- **Enhanced geo-location attributes** - Agency, status, size, and direction now included
- **New incident events** - `abc_emergency_new_incident` and type-specific events for automation triggers
- **Improved dashboard maps** - Filter incidents by instance using `geo_location_sources`

### Changed
- Geo-location source now matches config entry title exactly (e.g., "ABC Emergency (Home)")
- Updated documentation with map card examples

## [0.1.0] - 2025-12-07

### Added
- Initial release of ABC Emergency for Home Assistant
- **Three monitoring modes:**
  - State Mode - Monitor all incidents in a state/territory
  - Zone Mode - Alerts within radius of a fixed location
  - Person Mode - Track alerts near a person as they move
- **Per-incident-type radius** - Configure different alert distances for bushfires, floods, storms, etc.
- **Sensor entities:**
  - Total incidents count
  - Nearby incidents count (Zone/Person mode)
  - Nearest incident distance
  - Highest alert level
  - Bushfire, flood, and storm counts
- **Binary sensor entities:**
  - Active alert indicator
  - Emergency Warning level
  - Watch and Act level
  - Advice level
- **Geo-location entities** - Map markers for each incident
- Support for Australian Warning System alert levels
- Configurable via Home Assistant UI
- Comprehensive documentation

### Technical
- Full type safety with TypedDict definitions
- 100% test coverage
- Async API client with proper error handling
- DataUpdateCoordinator for efficient polling

---

## Version History Summary

| Version | Date | Highlights |
|---------|------|------------|
| 0.4.5 | 2025-12-30 | Longitude normalization for state determination |
| 0.4.4 | 2025-12-30 | Predictable geo-location entity IDs matching sensor attributes |
| 0.4.3 | 2025-12-30 | Entity discovery attributes, alert-level count sensors |
| 0.4.2 | 2025-12-30 | GeoJSON geometry exposure for map card polygon rendering |
| 0.4.1 | 2025-12-08 | Containment severity change event, improved polygon boundary change detection |
| 0.4.0 | 2025-12-08 | Point-in-polygon containment detection, new containment binary sensors and events |
| 0.3.0 | 2025-12-07 | Documentation improvements, Blueprints, my.home-assistant.io buttons |
| 0.2.0 | 2025-12-07 | Instance-based map filtering, new events, enhanced attributes |
| 0.1.0 | 2025-12-07 | Initial release with all core features |

[Unreleased]: https://github.com/troykelly/homeassistant-abcemergency/compare/v0.4.5...HEAD
[0.4.5]: https://github.com/troykelly/homeassistant-abcemergency/compare/v0.4.4...v0.4.5
[0.4.4]: https://github.com/troykelly/homeassistant-abcemergency/compare/v0.4.3...v0.4.4
[0.4.3]: https://github.com/troykelly/homeassistant-abcemergency/compare/v0.4.2...v0.4.3
[0.4.2]: https://github.com/troykelly/homeassistant-abcemergency/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/troykelly/homeassistant-abcemergency/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/troykelly/homeassistant-abcemergency/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/troykelly/homeassistant-abcemergency/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/troykelly/homeassistant-abcemergency/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/troykelly/homeassistant-abcemergency/releases/tag/v0.1.0
