# ABC Emergency API Reference

Complete documentation for the ABC Emergency API, reverse-engineered from the ABC Emergency website.

## Base URL

```
https://www.abc.net.au/emergency-web/api/
```

## Authentication

**No authentication required.** The API is publicly accessible.

## Endpoints Overview

| Endpoint | Purpose | Status |
|----------|---------|--------|
| `/emergencySearch` | Search emergencies by state or geohash | **Active** |
| `/emergencyFeed` | All emergencies across Australia | **Active** |
| `/locationSearch` | Search for localities by name | **Active** |
| `/locationAndWeather` | Location details and weather forecasts | **Active** |
| `/disclaimerContent` | Disclaimer and emergency services info | **Active** |
| `/emergency/warning/{id}` | Warning detail page | **HTML only** (not a JSON API) |
| `/radio` | Radio endpoints | **Not found** (404) |
| `/collectionLoadMore` | Pagination endpoint | **Empty** (returns `{}`) |

---

## Emergency Search

```
GET /emergencySearch
```

Primary endpoint for retrieving emergency incidents for a specific state or geographic area.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `state` | string | No* | State code: `nsw`, `vic`, `qld`, `sa`, `wa`, `tas`, `nt`, `act` |
| `query` | string | No | Search query text |
| `radius` | string | No | Search radius: `TenKm`, `TwentyKm`, `FiftyKm`, `OneHundredKm` |
| `geohashes` | string | No* | JSON array of geohash prefixes for location filtering |

*Either `state` OR `geohashes` must be provided. Geohash search returns all incidents within the geohash area(s) regardless of state boundaries.

### Response Structure

```json
{
  "emergencies": [...],      // Array of Emergency objects (see api-types.md)
  "features": [...],         // Array of GeoJSON Feature objects (see below)
  "mapBound": [[lon1, lat1], [lon2, lat2]],  // Bounding box for the search area
  "stateName": "nsw",        // State code
  "incidentsNumber": 42,     // Number of incidents matching search criteria
  "stateCount": 125          // Total incidents in the state
}
```

### Example Requests

```bash
# Search by state
curl 'https://www.abc.net.au/emergency-web/api/emergencySearch?state=nsw' \
  -H 'User-Agent: Mozilla/5.0'

# Search by geohash (r65 = Sydney area)
curl 'https://www.abc.net.au/emergency-web/api/emergencySearch?geohashes=%5B%22r65%22%5D' \
  -H 'User-Agent: Mozilla/5.0'
```

### Geohash Reference

Geohashes provide location-based filtering. Common Australian prefixes:
- `r1`, `r3`, `r4`, `r5`, `r6`, `r7` - NSW regions
- `r65` - Sydney metropolitan area
- Use multiple geohashes for broader coverage

---

## Emergency Feed

```
GET /emergencyFeed
```

Returns all emergencies across Australia in a single call. No parameters required.

### Response Structure

```json
{
  "allEmergencies": [...],   // Array of Emergency objects
  "features": [...]          // Array of GeoJSON Feature objects
}
```

### Example Request

```bash
curl 'https://www.abc.net.au/emergency-web/api/emergencyFeed' \
  -H 'User-Agent: Mozilla/5.0'
```

---

## GeoJSON Features Array

Both `/emergencySearch` and `/emergencyFeed` return a `features` array containing GeoJSON Feature objects with extended properties. This is a separate representation of the same emergencies with additional map-specific data.

### Feature Structure

```json
{
  "type": "Feature",
  "id": "AUREMER-72446a8d6888092c5e42f6ed9985f935",
  "geometry": {
    "type": "Point|Polygon|MultiPolygon|GeometryCollection",
    "crs": { "type": "name", "properties": { "name": "EPSG:4326" } },
    "coordinates": [...]
  },
  "properties": { ... }
}
```

### Feature Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | string | Emergency ID (matches `emergencies[].id`) |
| `state` | string | State code |
| `headline` | string | Brief incident description |
| `textSummary` | string | Human-readable summary |
| `senderName` | string | Source agency full name |
| `orgName` | string | Organization name |
| `orgWeb` | string | Organization website URL |
| `orgAttribution` | string | HTML attribution text |
| `event` | string | Event type (see Event Types below) |
| `alertType` | `"warning"` \| `"incident"` | Classification |
| `alertLevel` | string \| null | Alert level text (see Alert Levels) |
| `alertLevelRaw` | string \| null | Raw alert level from source |
| `abcAlertLevel` | string | ABC internal priority (10=Emergency, 20=severe, etc.) |
| `displaySequence` | number | Sort order priority |
| `incidentType` | string \| null | Specific incident type |
| `incidentStatus` | string \| null | Current status |
| `size` | string \| null | Affected area size (e.g., "9706 ha") |
| `certainty` | string | Usually "Unknown" |
| `sent` | string | ISO 8601 timestamp when sent |
| `effective` | string \| null | ISO 8601 effective time |
| `areaDesc` | string | Affected area description |
| `responseTypes` | string[] | Response actions (e.g., ["Monitor"]) |
| `cyclonePath` | object \| null | Cyclone path data (rare) |
| `affectedAbcRegion` | object | ABC local radio region info |
| `centroid` | PointGeometry | Center point of the incident |
| `systemCreatedTime` | string | ISO 8601 system creation time |
| `systemUpdatedTime` | string | ISO 8601 last update time |
| `systemArchivedTime` | string \| null | ISO 8601 archive time |

### Map Styling Properties

| Property | Type | Description |
|----------|------|-------------|
| `fillColour` | string | Polygon fill color (hex) |
| `fillOpacity` | number | Fill opacity (0-1) |
| `fillOpacityActive` | number | Fill opacity when active |
| `lineColour` | string | Border color (hex) |
| `lineOpacity` | number | Border opacity (0-1) |
| `lineWidth` | number | Border width |
| `icon` | string | Icon identifier (see Icon Types) |
| `iconOpacity` | number | Icon opacity (0-1) |
| `iconSize` | number | Icon scale factor |
| `visible` | string | "true" or "false" |

### Icon Types

```python
FeatureIcon = Literal[
    "FireMinorDefault",
    "FireModerateDefault",
    "FireSevereDefault",
    "FireExtremeDefault",
    "WeatherMinorDefault",
    "WeatherModerateDefault",
    "HeatSevereDefault",
    "OtherMinorDefault",
]
```

### Fill/Line Colors

| Color | Hex | Meaning |
|-------|-----|---------|
| White | `#fff` | Minor/Information |
| Yellow | `#fbe032` | Advice |
| Orange | `#ff9b45` | Watch and Act |
| Red | `#d31717` | Emergency |

### ABC Alert Level Priority

| Value | Meaning |
|-------|---------|
| `10` | Emergency Warning |
| `20` | Watch and Act (Severe) |
| `30` | Advice (Moderate) |
| `35-46` | Various priority levels |
| `99` | Minor/Information |

### Affected ABC Region

```json
{
  "region": "sydney",
  "regionName": "Sydney",
  "serviceName": "local_sydney",
  "serviceNameRadio": "local_sydney",
  "brandName": "ABC Radio Sydney"
}
```

Known regions: `sydney`, `melbourne`, `brisbane`, `perth`, `adelaide`, `hobart`, `darwin`, `canberra`, `newcastle`, `illawarra`, `centralcoast`, `upperhunter`, `newengland`, `midnorthcoast`, `northcoast`, `riverina`, `centralwest`, `westernplains`, `southeastnsw`, `gippsland`, `shepparton`, `goulburnmurray`, `centralvic`, `ballarat`, `wimmera`, `milduraswanhill`, `southwestvic`, `goldfields`, `kimberley`, `pilbara`, `northandwest`, `wheatbelt`, `greatsouthern`, `southwestwa`, `northqld`, `farnorth`, `capricornia`, `widebay`, `sunshine`, `southqld`, `westqld`, `tropic`, `northtas`, `northwest`, `riverland`, `katherine`

### Response Types

```python
ResponseType = Literal["Monitor", "Unknown", "None", "Assess"]
```

### Geometry Types in Features

| Type | Count (typical) | Description |
|------|-----------------|-------------|
| `Point` | ~40% | Single location marker |
| `Polygon` | ~35% | Area boundary |
| `GeometryCollection` | ~22% | Combined point + polygon |
| `MultiPolygon` | ~3% | Multiple separate areas |

---

## Location Search

```
GET /locationSearch?searchQuery={query}
```

Search for Australian localities by name or postcode. Returns up to 10 matching results.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `searchQuery` | string | Yes | Suburb name or postcode |

### Response Structure

```json
{
  "locations": {
    "byLocalitySearch": [
      {
        "id": "aurora://location/loc46e6625bb24d",
        "suburb": "Sydney",
        "state": { "id": "nsw", "__typename": "State" },
        "postcode": "2000",
        "lat": "-33.8688",
        "long": "151.2093",
        "abcRegion": {
          "region": "sydney",
          "regionName": "Sydney",
          "__typename": "ABCRegion"
        },
        "__typename": "Location"
      }
    ],
    "__typename": "LocationsRoot"
  }
}
```

### Example Request

```bash
curl 'https://www.abc.net.au/emergency-web/api/locationSearch?searchQuery=Sydney' \
  -H 'User-Agent: Mozilla/5.0'

# Search by postcode
curl 'https://www.abc.net.au/emergency-web/api/locationSearch?searchQuery=2000' \
  -H 'User-Agent: Mozilla/5.0'
```

---

## Location and Weather

```
GET /locationAndWeather?query={type}&locationId={id}
GET /locationAndWeather?query=LOCATION&searchQuery={query}
```

Retrieve location details and weather forecasts.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Query type: `LOCATION` or `WEATHER` |
| `locationId` | string | For WEATHER | Location ID (e.g., `aurora://location/loc46e6625bb24d`) |
| `searchQuery` | string | For LOCATION | Search text for locality |

### WEATHER Response Structure

```json
{
  "locations": {
    "byId": {
      "id": "aurora://location/loc46e6625bb24d",
      "suburb": "Sydney",
      "state": { "id": "nsw", "__typename": "State" },
      "postcode": "2000",
      "abcRegion": { ... },
      "weather": {
        "urbanForecast": {
          "forecasts": [
            {
              "dailyRainfallRange": "0 mm",
              "dayName": "Saturday",
              "expectedWeatherDescription": "Cloudy",
              "expectedWindDirection": "NE",
              "expectedWindSpeedKph": 17,
              "icon": "Cloud",
              "maximumTemperature": 39,
              "minimumTemperature": 23,
              "rainfallProbability": 20,
              "startTime": "2025-12-06 00:00:00",
              "uvDescription": "Extreme",
              "uvIndex": 11,
              "__typename": "WeatherUrbanForecast"
            }
          ],
          "__typename": "WeatherUrbanForecastLocation"
        },
        "detailedHistoricConditions": [
          {
            "values": [
              {
                "feelsLikeTempC": 26.3,
                "generationTime": "2025-12-06T16:41:03+11:00",
                "relativeHumidityPct": 39,
                "startTime": "2025-12-06T16:40:00+11:00",
                "tempC": 30.7,
                "__typename": "WeatherHistoricDetailedConditionsData"
              }
            ],
            "__typename": "WeatherHistoricDetailedConditions"
          }
        ],
        "__typename": "WeatherResource"
      },
      "__typename": "Location"
    },
    "__typename": "LocationsRoot"
  }
}
```

### Weather Icon Values

```python
WeatherIcon = Literal[
    "Clear",
    "Cloud",
    "LightShower",
    "PartCloudy",
    "Storm",
    "Sunny",
]
```

### UV Descriptions

```python
UVDescription = Literal["Extreme", "Very High", "High", "Moderate", "Low"] | None
```

### Wind Directions

Standard compass directions: `N`, `NE`, `E`, `SE`, `S`, `SW`, `W`, `NW`

### Example Request

```bash
# Get weather for Sydney
curl 'https://www.abc.net.au/emergency-web/api/locationAndWeather?query=WEATHER&locationId=aurora://location/loc46e6625bb24d' \
  -H 'User-Agent: Mozilla/5.0'

# Search for a location
curl 'https://www.abc.net.au/emergency-web/api/locationAndWeather?query=LOCATION&searchQuery=Brisbane' \
  -H 'User-Agent: Mozilla/5.0'
```

---

## Disclaimer Content

```
GET /disclaimerContent?state={state}
```

Returns disclaimer and emergency services information for a specific state.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `state` | string | Yes | State code |

### Response Structure

```json
{
  "disclaimer": {
    "disclaimerHeading": "About the information displayed on this page",
    "disclaimerContent": {
      "descriptor": {
        "type": "tagname",
        "key": "div",
        "children": [...]
      }
    },
    "disclaimerContentUri": "coremedia://teaser/12433246"
  },
  "emergencyServices": {
    "emergencyServicesHeading": "Emergency services in NSW",
    "emergencyServicesContentPrepared": {
      "descriptor": {
        "type": "tagname",
        "key": "div",
        "children": [...]
      }
    },
    "emergencyServicesContentUri": "coremedia://teaser/12374516"
  }
}
```

The `descriptor` content uses a custom markup structure with:
- `type`: `"tagname"` or `"text"`
- `key`: HTML tag name (e.g., `"div"`, `"p"`, `"ul"`, `"li"`, `"a"`) or `"@@standfirst"` for lead text
- `props`: HTML attributes (e.g., `href`, `target`, `rel`)
- `children`: Nested content array
- `content`: Text content (for `type: "text"`)

### Example Request

```bash
curl 'https://www.abc.net.au/emergency-web/api/disclaimerContent?state=nsw' \
  -H 'User-Agent: Mozilla/5.0'
```

---

## Non-Functional Endpoints

### Warning Detail Page

```
GET /emergency/warning/{id}
```

**This is NOT a JSON API endpoint.** It returns an HTML page that is rendered client-side. The emergency data is embedded in the page JavaScript, not returned as JSON.

### Radio Endpoints

All radio-related URL patterns return 404 HTML pages:
- `/radio`
- `/radio/{region}`

### Collection Load More

```
GET /collectionLoadMore
```

Returns empty `{}` regardless of parameters. This endpoint appears to be either deprecated, not implemented, or requires specific session context.

---

## State Codes

| Code | State/Territory | Full Name |
|------|-----------------|-----------|
| `nsw` | NSW | New South Wales |
| `vic` | VIC | Victoria |
| `qld` | QLD | Queensland |
| `sa` | SA | South Australia |
| `wa` | WA | Western Australia |
| `tas` | TAS | Tasmania |
| `nt` | NT | Northern Territory |
| `act` | ACT | Australian Capital Territory |

---

## Alert Level Mapping

The API uses the Australian Warning System:

| API Level | API Text | Australian Warning System | Color | Priority |
|-----------|----------|---------------------------|-------|----------|
| `extreme` | `"Emergency"` | Emergency Warning | Red (#d31717) | 10 |
| `severe` | `"Watch and Act"` | Watch and Act | Orange (#ff9b45) | 20 |
| `moderate` | `"Advice"` | Advice | Yellow (#fbe032) | 30-46 |
| `minor` | `""` | Information | White (#fff) | 99 |

**Note:** BOM heatwave warnings use `level: "severe"` or `level: "extreme"` but with `text: ""` and `style: "minor"`.

---

## Event Types

Events observed across all states:

```python
EventType = Literal[
    "Assist Agency",
    "Burn Off",
    "Bushfire",
    "Earthquake",
    "Extreme Heat",
    "Fire",
    "Fire ban",
    "Fuel Reduction Burn",
    "Grass Fire",
    "Hazardous Materials",
    "Heatwave",
    "Motor Vehicle Accident",
    "Other Non-Urgent Alerts",
    "Planned Burn",
    "Rescue",
    "Sheep Grazier Warning",
    "Storm",
    "Structure Fire",
    "Thunderstorm",
    "Vehicle Fire",
    "Weather",
    "Wind",
]
```

---

## Incident Types (from Features)

```python
FeatureIncidentType = Literal[
    "Assist Other Agency",
    "Burn off",
    "Bush Fire",
    "Bushfire",
    "Car Fire",
    "FIRE PERMITTED BURN",
    "FIRE VEGETATION",
    "Fire ban",
    "Flood/Storm/Tree Down",
    "Grass Fire",
    "Haystack fire",
    "Hazard Reduction",
    "Medical",
    "MOTOR VEHICLE ACCIDENT",
    "MVA/Transport",
    "Other",
    "Planned Event",
    "Storm",
    "Structure Fire",
    "Truck Fire",
    "Unknown",
] | None
```

---

## Incident Statuses (from Features)

```python
FeatureIncidentStatus = Literal[
    "Active",
    "Actual",
    "Being controlled",
    "Contained",
    "GOING",
    "Investigating",
    "Minor",
    "Not yet controlled",
    "Patrol",
    "Request For Assistance",
    "Responding",
    "Safe",
    "Under Control",
    "Under control",
    "Units On Route",
    "Unknown",
] | None
```

---

## Alert Level Raw Values (from Features)

```python
AlertLevelRaw = Literal[
    "Advice",
    "Bushfire Advice",
    "Emergency Warning",
    "Heatwave Watch and Act",
    "Information",
    "N/A",
    "Not Applicable",
    "Planned Burn",
    "Planned Burn Advice",
    "Update",
    "Watch and Act",
] | None
```

---

## Organization Names (from Features)

```python
OrgName = Literal[
    "ACT Emergency Services Agency",
    "Bureau of Meteorology",
    "Emergency WA",
    "Geoscience Australia",
    "NSW Rural Fire Service",
    "NSWSES",
    "Queensland Fire Department",
    "SecureNT",
    "South Australian Country Fire Service",
    "Department of Premier and Cabinet",
    "VicEmergency",
]
```

---

## Rate Limiting

No rate limiting has been observed, but integrations should:

- Poll no more frequently than every 5 minutes
- Include a reasonable User-Agent header
- Handle HTTP 429 responses gracefully if they occur

---

## Error Handling

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 404 | Endpoint not found (returns HTML) |
| 429 | Rate limited (not observed, but handle gracefully) |
| 5xx | Server error |

When an endpoint returns HTML instead of JSON, it indicates either:
1. The endpoint doesn't exist
2. The endpoint is for browser rendering only (e.g., warning detail pages)
