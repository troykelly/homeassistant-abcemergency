# Changelog

All notable changes to ABC Emergency for Home Assistant.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- my.home-assistant.io one-click buttons throughout documentation
- Importable Home Assistant Blueprints for common automations
- FAQ, Glossary, and improved documentation structure
- Collapsible technical explanations for beginners

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
| 0.2.0 | 2025-12-07 | Instance-based map filtering, new events, enhanced attributes |
| 0.1.0 | 2025-12-07 | Initial release with all core features |

[Unreleased]: https://github.com/troykelly/homeassistant-abcemergency/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/troykelly/homeassistant-abcemergency/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/troykelly/homeassistant-abcemergency/releases/tag/v0.1.0
