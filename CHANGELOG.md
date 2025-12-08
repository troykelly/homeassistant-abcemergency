# Changelog

All notable changes to ABC Emergency for Home Assistant.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

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

### Changed

- EmergencyIncident model now stores polygon geometry data
- Coordinator performs containment checks during each update cycle

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
| 0.3.0 | 2025-12-07 | Documentation improvements, Blueprints, my.home-assistant.io buttons |
| 0.2.0 | 2025-12-07 | Instance-based map filtering, new events, enhanced attributes |
| 0.1.0 | 2025-12-07 | Initial release with all core features |

[Unreleased]: https://github.com/troykelly/homeassistant-abcemergency/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/troykelly/homeassistant-abcemergency/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/troykelly/homeassistant-abcemergency/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/troykelly/homeassistant-abcemergency/releases/tag/v0.1.0
