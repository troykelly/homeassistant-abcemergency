# Home Assistant ABC Emergency Integration

A Home Assistant integration for ABC Emergency (Australian Broadcasting Corporation) incident data.

## Project Overview

This custom Home Assistant integration provides real-time Australian emergency incident data from ABC Emergency (abc.net.au/emergency). It enables location-based alerting and warnings for bushfires, floods, storms, cyclones, and other emergencies across Australia.

## What is ABC Emergency?

ABC Emergency is the Australian Broadcasting Corporation's emergency information service that aggregates data from state and territory emergency services across Australia. It provides:

- Real-time incident mapping for all Australian states/territories
- Official warnings using the Australian Warning System levels
- Coverage of bushfires, floods, storms, cyclones, extreme heat, and severe weather

### Australian Warning System Levels

| Level | Icon Color | Meaning |
|-------|------------|---------|
| **Advice** | Yellow | An incident has started. No immediate danger. Stay informed. |
| **Watch and Act** | Orange | Heightened threat. Conditions changing. Take action now. |
| **Emergency Warning** | Red | Highest level. You may be in danger. Act immediately. |

## Project Management

### GitHub Project

**ALL work MUST be tracked via GitHub Issues and the Project Board.**

| Item | Value |
|------|-------|
| Project URL | https://github.com/users/troykelly/projects/3 |
| Project Name | Home Assistant ABC Emergency Component |
| Repository | troykelly/homeassistant-abcemergency |

### The Iron Law

```
NO CODE CHANGES WITHOUT A LINKED GITHUB ISSUE
```

This is a **VIOLATION**. Every commit, every PR, every change must reference an issue.

**Before writing ANY code:**
1. Check if an issue exists for this work
2. If not, create one
3. Assign yourself and add `status: in-progress`
4. Create branch: `issue-{N}-{description}`
5. Commit with issue reference: `type(scope): message (#N)`
6. Create PR with `Fixes #N` in body

## Mandatory Development Rules

### 1. Test-Driven Development (TDD)

**Every line of code MUST start with a failing test.**

```
RED -> GREEN -> REFACTOR
```

- Write test first
- Watch it fail (if it passes immediately, your test is wrong)
- Write minimal code to pass
- Refactor while keeping tests green
- No exceptions for "simple" code

### 2. No `Any` Type

**NEVER use `Any` in type annotations.**

- Use TypedDict for API response structures
- Use dataclasses for internal models
- Use Protocol for interfaces
- Use Generics for containers
- The only exception: `**kwargs: Any` when overriding HA base class methods that require it

### 3. Two Failures = Research

**If code fails twice, STOP and research.**

- Don't guess-and-check
- Read official documentation
- Examine working implementations in HA core
- Understand before attempting again

## Core Features

### Location-Based Alerting

The integration enables alerting based on:

- **Home location** - Configured Home Assistant zone
- **Custom zones** - User-defined geographic areas to monitor
- **Radius-based** - Alerts within configurable distance from a point
- **State/Region** - Monitor entire states or regions

### Entity Types

| Platform | Entity | Purpose |
|----------|--------|---------|
| `sensor` | `sensor.abc_emergency_*` | Incident counts, nearest incident, alert levels |
| `binary_sensor` | `binary_sensor.abc_emergency_*` | Active alerts in monitored areas |
| `geo_location` | `geo_location.abc_emergency_*` | Individual incidents on map |

### Sensor Details

| Sensor | Description |
|--------|-------------|
| `sensor.abc_emergency_incidents_total` | Total active incidents |
| `sensor.abc_emergency_incidents_nearby` | Incidents within configured radius |
| `sensor.abc_emergency_nearest_incident` | Distance/direction to nearest incident |
| `sensor.abc_emergency_highest_alert_level` | Highest warning level in area |
| `sensor.abc_emergency_bushfires` | Active bushfire count |
| `sensor.abc_emergency_floods` | Active flood count |
| `sensor.abc_emergency_storms` | Active storm count |

### Binary Sensors

| Sensor | Description |
|--------|-------------|
| `binary_sensor.abc_emergency_active_alert` | Any alert in monitored area |
| `binary_sensor.abc_emergency_emergency_warning` | Red-level warning active |
| `binary_sensor.abc_emergency_watch_and_act` | Orange-level or higher warning |
| `binary_sensor.abc_emergency_advice` | Any warning level active |

## ABC Emergency API Documentation

### Base URL

```
https://www.abc.net.au/emergency-web/api/
```

### Authentication

**No authentication required.** The API is publicly accessible.

### Endpoints

#### Emergency Search

```
GET /emergencySearch
```

Retrieves emergency incidents for a state/territory.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `state` | string | No* | State code: `nsw`, `vic`, `qld`, `sa`, `wa`, `tas`, `nt`, `act` |
| `query` | string | No | Search query text |
| `radius` | string | No | Search radius: `TenKm`, `TwentyKm`, `FiftyKm`, `OneHundredKm` |
| `geohashes` | string | No* | JSON array of geohash prefixes for location filtering |

*Either `state` OR `geohashes` must be provided. Geohash search returns all incidents within the geohash area(s) regardless of state boundaries.

**Example Requests:**

```bash
# Search by state
curl 'https://www.abc.net.au/emergency-web/api/emergencySearch?state=nsw' \
  -H 'User-Agent: Mozilla/5.0'

# Search by geohash (r65 = Sydney area)
curl 'https://www.abc.net.au/emergency-web/api/emergencySearch?geohashes=%5B%22r65%22%5D' \
  -H 'User-Agent: Mozilla/5.0'
```

**Geohash Reference:**

Geohashes provide location-based filtering. Common Australian prefixes:
- `r1`, `r3`, `r4`, `r5`, `r6`, `r7` - NSW regions
- `r65` - Sydney metropolitan area
- Use multiple geohashes for broader coverage

**Response Structure:**

```json
{
  "emergencies": [...],
  "features": [...],
  "mapBound": [[lon1, lat1], [lon2, lat2]],
  "stateName": "nsw",
  "incidentsNumber": 0,
  "stateCount": 125
}
```

### Response Types

For complete TypedDict definitions, see [docs/api-types.md](docs/api-types.md).

**Alert Level Mapping:**

| API Level | API Text | Australian Warning System | Color |
|-----------|----------|---------------------------|-------|
| `extreme` | `"Emergency"` | Emergency Warning | Red |
| `severe` | `"Watch and Act"` | Watch and Act | Orange |
| `moderate` | `"Advice"` | Advice | Yellow |
| `minor` | `""` | Information | Blue/Grey |

### State Codes

| Code | State/Territory |
|------|-----------------|
| `nsw` | New South Wales |
| `vic` | Victoria |
| `qld` | Queensland |
| `sa` | South Australia |
| `wa` | Western Australia |
| `tas` | Tasmania |
| `nt` | Northern Territory |
| `act` | Australian Capital Territory |

### Rate Limiting

No rate limiting has been observed, but the integration should:

- Poll no more frequently than every 5 minutes
- Include a reasonable User-Agent header
- Handle HTTP 429 responses gracefully if they occur

### Additional Endpoints

#### Location Search

```
GET /locationSearch?searchQuery={query}
```

Search for Australian localities by name. Returns matching suburbs with coordinates.

**Response:**

```python
class LocationSearchResponse(TypedDict):
    locations: LocationResults

class LocationResults(TypedDict):
    byLocalitySearch: list[Location]

class Location(TypedDict):
    id: str          # "aurora://location/loc46e6625bb24d"
    suburb: str      # "Sydney"
    state: State     # {"id": "nsw", "__typename": "State"}
    postcode: str    # "2000"
    lat: str         # "-33.8688"
    long: str        # "151.2093"
    abcRegion: ABCRegion
```

**Example:**

```bash
curl 'https://www.abc.net.au/emergency-web/api/locationSearch?searchQuery=Sydney' \
  -H 'User-Agent: Mozilla/5.0'
```

#### Location and Weather

```
GET /locationAndWeather?query={type}&locationId={id}
GET /locationAndWeather?query=LOCATION&searchQuery={query}
```

Retrieve location details and weather forecasts.

**Query Types:**

| Type | Description |
|------|-------------|
| `LOCATION` | Search for location by name (use `searchQuery` param) |
| `WEATHER` | Get weather for location (use `locationId` param) |

**Weather Response:**

```python
class WeatherForecast(TypedDict):
    dailyRainfallRange: str      # "0 mm", "0 to 1 mm"
    dayName: str                 # "Saturday"
    expectedWeatherDescription: str  # "Cloudy", "Possible shower"
    expectedWindDirection: str   # "NE", "SE"
    expectedWindSpeedKph: int    # 17
    icon: str                    # "Cloud", "LightShower", "PartCloudy"
    maximumTemperature: int      # 39
    minimumTemperature: int      # 23
    rainfallProbability: int     # 20
    startTime: str               # "2025-12-06 00:00:00"
    uvDescription: str           # "Extreme", "High"
    uvIndex: int                 # 11

class CurrentConditions(TypedDict):
    feelsLikeTempC: float        # 26.8
    generationTime: str          # ISO 8601
    relativeHumidityPct: int     # 40
    startTime: str               # ISO 8601
    tempC: float                 # 30.4
```

**Example:**

```bash
# Get weather for Sydney
curl 'https://www.abc.net.au/emergency-web/api/locationAndWeather?query=WEATHER&locationId=aurora://location/loc46e6625bb24d' \
  -H 'User-Agent: Mozilla/5.0'
```

#### Disclaimer Content

```
GET /disclaimerContent?state={state}
```

Returns disclaimer and emergency services information for a state.

**Response includes:**
- Disclaimer text about data accuracy
- Emergency services contact information
- Links to official agencies

### Warning Detail Endpoint

Individual warning details can be fetched from:

```
GET /emergency/warning/{id}
```

This returns full warning details including:
- Full description text
- Affected areas
- What to do instructions
- Update history

## Project Structure

```
custom_components/abcemergency/
├── __init__.py           # Integration setup
├── manifest.json         # Integration metadata
├── config_flow.py        # UI configuration flow
├── const.py              # Constants, types, TypedDicts
├── coordinator.py        # DataUpdateCoordinator
├── entity.py             # Base ABCEmergencyEntity class
├── api.py                # ABC Emergency API client
├── models.py             # Dataclasses for incidents
│
│   # Entity Platforms
├── sensor.py             # Incident count sensors
├── binary_sensor.py      # Alert state sensors
├── geo_location.py       # Map markers for incidents
│
│   # Supporting
├── helpers.py            # Geolocation calculations
├── exceptions.py         # Custom exceptions
├── diagnostics.py        # Diagnostic download
├── strings.json          # English translations
└── translations/
    └── en.json

tests/
├── conftest.py           # Pytest fixtures
├── test_init.py          # Setup/unload tests
├── test_config_flow.py   # Config flow tests
├── test_coordinator.py   # Coordinator tests
├── test_api.py           # API client tests
├── test_sensor.py        # Sensor tests
├── test_binary_sensor.py # Binary sensor tests
├── test_geo_location.py  # Geo location tests
└── ...
```

## Key Technologies

- **Python 3.12+** - Type hints with modern syntax (`X | None`, not `Optional[X]`)
- **Home Assistant 2025.x** - Latest patterns and APIs
- **pytest + pytest-homeassistant-custom-component** - Testing framework
- **mypy strict** - Type checking
- **aiohttp** - Async HTTP client
- **geopy** - Distance calculations (if needed)

## Configuration

### Config Flow Steps

1. **User step** - Select monitoring mode (home zone, custom location, region)
2. **Location step** - Enter coordinates or select zone/region
3. **Options step** - Set alert radius, incident types to monitor
4. Create config entry

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| **Monitor Location** | Home zone | Location to monitor for alerts |
| **Alert Radius** | 50 km | Distance for "nearby" alerts |
| **Incident Types** | All | Filter by bushfire, flood, storm, etc. |
| **Minimum Alert Level** | Advice | Minimum warning level to track |
| **Update Interval** | 5 min | Polling frequency |

## Automation Examples

### Emergency Warning Notification

```yaml
automation:
  - alias: "ABC Emergency Warning Alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.abc_emergency_emergency_warning
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "EMERGENCY WARNING"
          message: >
            {{ state_attr('sensor.abc_emergency_nearest_incident', 'title') }}
            is {{ state_attr('sensor.abc_emergency_nearest_incident', 'distance_km') }}km away
          data:
            priority: high
            channel: emergency
```

### Nearby Bushfire Alert

```yaml
automation:
  - alias: "Bushfire Within 20km"
    trigger:
      - platform: numeric_state
        entity_id: sensor.abc_emergency_nearest_incident
        below: 20
    condition:
      - condition: state
        entity_id: sensor.abc_emergency_nearest_incident
        attribute: incident_type
        state: "bushfire"
    action:
      - service: notify.all_devices
        data:
          message: "Bushfire detected {{ states('sensor.abc_emergency_nearest_incident') }}km away!"
```

## Development Commands

```bash
# Run tests
pytest tests/

# Run tests with coverage
pytest tests/ --cov=custom_components.abcemergency --cov-report=term-missing --cov-fail-under=100

# Run specific test
pytest tests/test_api.py::test_fetch_incidents -v

# Type checking
mypy custom_components/abcemergency/

# Linting
ruff check custom_components/abcemergency/
ruff format custom_components/abcemergency/
```

## Testing Patterns

### Required Fixtures (conftest.py)

```python
@pytest.fixture
def mock_abc_client() -> Generator[MagicMock, None, None]:
    """Mock ABC Emergency API client."""
    with patch("custom_components.abcemergency.ABCEmergencyClient", autospec=True) as mock:
        yield mock.return_value

@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Create mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_LATITUDE: -33.8688,
            CONF_LONGITUDE: 151.2093,
            CONF_RADIUS: 50,
        },
        unique_id="sydney",
    )
```

### Test Coverage Requirements

- 100% coverage for all code
- All config flow paths (success, errors, abort)
- All entity states
- API response handling
- Error handling paths
- Geolocation calculations

## Environment Variables

### Testing Environment

```bash
# Optional: For testing with real API (once discovered)
ABC_EMERGENCY_BASE_URL=https://api.emergency.abc.net.au
```

### Home Assistant Devcontainer Testing

```bash
HOMEASSISTANT_URL=http://localhost:8123
HOMEASSISTANT_TOKEN=your-long-lived-access-token
```

## Code Style

- Use `from __future__ import annotations`
- Modern union syntax: `str | None` not `Optional[str]`
- Explicit return types on all functions
- Type all class attributes in `__init__`
- Use `_attr_*` pattern for entity attributes
- Never do I/O in properties

## Resources

- [Home Assistant Developer Docs](https://developers.home-assistant.io/)
- [Config Flow Docs](https://developers.home-assistant.io/docs/config_entries_config_flow_handler/)
- [ABC Emergency Website](https://www.abc.net.au/emergency)
- [Australian Warning System](https://www.australianwarningsystem.com.au/)
- [GeoLocation Entity Docs](https://developers.home-assistant.io/docs/core/entity/geo-location/)

## Development Phases

### Phase 1: API Discovery - COMPLETE

The ABC Emergency API has been reverse engineered and documented above. Key findings:

- **Base URL:** `https://www.abc.net.au/emergency-web/api/`
- **No authentication required**
- **State parameter is required** - must specify state code
- **Rich data available:** coordinates, polygons, alert levels, sources, timestamps

### Phase 2: Core Implementation

1. **API Client** (`api.py`)
   - Async HTTP client using aiohttp
   - State-based fetching
   - TypedDict response parsing
   - Error handling and retries

2. **Data Coordinator** (`coordinator.py`)
   - DataUpdateCoordinator for polling
   - Configurable update interval (default 5 min)
   - Distance calculations from home location

3. **Config Flow** (`config_flow.py`)
   - State selection
   - Location configuration (use HA home zone or custom)
   - Alert radius setting

### Phase 3: Entity Platforms

1. **Sensors** - Incident counts, nearest incident distance
2. **Binary Sensors** - Alert level states
3. **Geo Location** - Map markers for each incident

### Phase 4: Polish

1. **Diagnostics** - Debug info download
2. **Translations** - Localization support
3. **Documentation** - User guide and README
