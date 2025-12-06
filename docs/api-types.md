# ABC Emergency API Type Definitions

Complete TypedDict definitions for the ABC Emergency API, based on comprehensive analysis of all emergency data across all 8 Australian states/territories.

## Table of Contents

1. [Emergency Object Types](#emergency-object-types)
2. [GeoJSON Feature Types](#geojson-feature-types)
3. [Location and Weather Types](#location-and-weather-types)
4. [Disclaimer Content Types](#disclaimer-content-types)
5. [Literal Type Values](#literal-type-values)
6. [Sample Objects](#sample-objects)

---

## Emergency Object Types

These types are used in the `emergencies` and `allEmergencies` arrays.

### Alert Levels

```python
AlertLevel = Literal["extreme", "severe", "moderate", "minor"]
```

### Alert Text

```python
AlertText = Literal["", "Advice", "Emergency", "Watch and Act"]
```

### Alert Style

```python
AlertStyle = Literal["extreme", "severe", "moderate", "minor"]
```

### Event Icons

```python
EventIcon = Literal["fire", "heat", "other", "weather"]
```

### Event Labels

```python
EventLabel = Literal[
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

### Card Types

```python
CardType = Literal[
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
    "Hazard Reduction",
    "MVA/Transport",
    "Medical",
    "Other",
    "Planned Event",
    "Storm",
    "Structure Fire",
    "Truck Fire",
    "Unknown",
] | None
```

### Card Statuses

```python
CardStatus = Literal[
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
    "Unknown",
] | None
```

### Card Sources

```python
CardSource = Literal[
    "Australian Government Bureau of Meteorology",
    "Bushfires NT",
    "Department of Fire and Emergency Services (DFES)",
    "Department of Fire and Emergency Services WA",
    "Department of Health",
    "Emergency Management Victoria",
    "Fire and Rescue NSW",
    "Forest Fire Management Victoria",
    "Forestry Corporation of NSW",
    "Geoscience Australia",
    "NSW National Parks and Wildlife Service",
    "NSW Rural Fire Service",
    "NTFRS",
    "New South Wales State Emergency Service",
    "Queensland Fire Department",
    "South Australian Country Fire Service",
    "Tasmania Fire Service",
    "Tasmanian Department of Premier and Cabinet",
    "Unknown",
    "VIC Country Fire Authority",
]
```

### Geometry Types

```python
GeometryType = Literal["GeometryCollection", "MultiPolygon", "Point", "Polygon"]
```

---

## Complete Emergency TypedDict Definitions

```python
from __future__ import annotations

from typing import Literal, TypedDict


# Coordinate types
Coordinate = tuple[float, float]  # [longitude, latitude]
PolygonRing = list[Coordinate]
PolygonCoordinates = list[PolygonRing]
MultiPolygonCoordinates = list[PolygonCoordinates]


class CRSProperties(TypedDict):
    """Coordinate Reference System properties."""
    name: str  # e.g., "EPSG:4326"


class CRS(TypedDict):
    """Coordinate Reference System."""
    type: Literal["name"]
    properties: CRSProperties


class PointGeometry(TypedDict):
    """GeoJSON Point geometry."""
    type: Literal["Point"]
    coordinates: Coordinate


class PolygonGeometry(TypedDict):
    """GeoJSON Polygon geometry."""
    type: Literal["Polygon"]
    coordinates: PolygonCoordinates


class MultiPolygonGeometry(TypedDict):
    """GeoJSON MultiPolygon geometry."""
    type: Literal["MultiPolygon"]
    coordinates: MultiPolygonCoordinates


class GeometryCollectionGeometry(TypedDict):
    """GeoJSON GeometryCollection - can contain Points and Polygons."""
    type: Literal["GeometryCollection"]
    crs: CRS
    geometries: list[PointGeometry | PolygonGeometry]


class TopLevelPolygonGeometry(TypedDict):
    """Top-level Polygon geometry with CRS (used by BOM warnings)."""
    type: Literal["Polygon"]
    crs: CRS
    coordinates: PolygonCoordinates


class TopLevelMultiPolygonGeometry(TypedDict):
    """Top-level MultiPolygon geometry with CRS (used by BOM warnings)."""
    type: Literal["MultiPolygon"]
    crs: CRS
    coordinates: MultiPolygonCoordinates


# Union type for all possible top-level geometry types
Geometry = GeometryCollectionGeometry | TopLevelPolygonGeometry | TopLevelMultiPolygonGeometry


class AlertLevelInfo(TypedDict):
    """Alert level information using Australian Warning System."""
    text: Literal["", "Advice", "Emergency", "Watch and Act"]
    level: Literal["extreme", "severe", "moderate", "minor"]
    style: Literal["extreme", "severe", "moderate", "minor"]


class EmergencyTimestamp(TypedDict):
    """Timestamp information for an emergency."""
    date: str  # ISO 8601 datetime, e.g., "2025-12-06T05:34:00+00:00"
    formattedTime: str  # Human-readable, e.g., "4:34:00 pm AEDT"
    prefix: str  # e.g., "Effective from"
    updatedTime: str  # ISO 8601 datetime with microseconds


class EventLabelInfo(TypedDict):
    """Event categorization information."""
    icon: Literal["fire", "heat", "other", "weather"]
    labelText: str  # See EventLabel Literal type above for known values


class CardBody(TypedDict):
    """Card body information - varies by incident type."""
    type: str | None  # See CardType Literal above; None for BOM warnings
    size: str | None  # Fire size, e.g., "100 ha", "706.500"; None for non-fire
    status: str | None  # See CardStatus Literal above
    source: str  # See CardSource Literal above


class Emergency(TypedDict):
    """A single emergency incident."""
    id: str  # e.g., "AUREMER-72446a8d6888092c5e42f6ed9985f935"
    headline: str  # e.g., "Nimbin Rd, Koolewong"
    to: str  # URL path, e.g., "/emergency/warning/AUREMER-..."
    alertLevelInfoPrepared: AlertLevelInfo
    emergencyTimestampPrepared: EmergencyTimestamp
    eventLabelPrepared: EventLabelInfo
    cardBody: CardBody
    geometry: Geometry


class EmergencySearchResponse(TypedDict):
    """Response from /emergencySearch endpoint."""
    emergencies: list[Emergency]
    features: list[Feature]  # GeoJSON features (see Feature type below)
    mapBound: list[list[float]]  # [[lon1, lat1], [lon2, lat2]]
    stateName: str  # State code, e.g., "nsw"
    incidentsNumber: int  # Number of incidents in search area
    stateCount: int  # Total incidents in state


class EmergencyFeedResponse(TypedDict):
    """Response from /emergencyFeed endpoint."""
    allEmergencies: list[Emergency]
    features: list[Feature]  # GeoJSON features
```

---

## GeoJSON Feature Types

The `features` array contains GeoJSON Feature objects with extended properties for map display.

### Feature Icon Types

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

### Feature Alert Types

```python
FeatureAlertType = Literal["warning", "incident"]
```

### Feature Incident Types

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

### Feature Incident Statuses

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

### Feature Alert Level Raw

```python
FeatureAlertLevelRaw = Literal[
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

### Feature Organization Names

```python
FeatureOrgName = Literal[
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

### Feature Response Types

```python
FeatureResponseType = Literal["Monitor", "Unknown", "None", "Assess"]
```

### ABC Alert Level Priority

```python
ABCAlertLevel = Literal["10", "20", "30", "35", "40", "45", "46", "99"]
```

### Fill/Line Colors

```python
FillColour = Literal["#fff", "#fbe032", "#ff9b45", "#d31717"]
```

### Complete Feature TypedDict Definitions

```python
class AffectedAbcRegion(TypedDict):
    """ABC Local Radio region information."""
    region: str  # e.g., "sydney"
    regionName: str  # e.g., "Sydney"
    serviceName: str  # e.g., "local_sydney"
    serviceNameRadio: str  # e.g., "local_sydney"
    brandName: str  # e.g., "ABC Radio Sydney"


class FeatureProperties(TypedDict, total=False):
    """Properties of a GeoJSON Feature object."""
    # Core identification
    id: str
    state: str
    headline: str
    textSummary: str

    # Source information
    senderName: str
    orgName: str
    orgWeb: str
    orgAttribution: str

    # Event classification
    event: str
    alertType: Literal["warning", "incident"]
    alertLevel: str | None
    alertLevelRaw: str | None
    abcAlertLevel: str
    displaySequence: int

    # Incident details
    incidentType: str | None
    incidentStatus: str | None
    size: str | None
    certainty: str

    # Timestamps
    sent: str
    effective: str | None
    systemCreatedTime: str
    systemUpdatedTime: str
    systemArchivedTime: str | None

    # Location
    areaDesc: str
    centroid: PointGeometry
    affectedAbcRegion: AffectedAbcRegion

    # Response
    responseTypes: list[str]
    cyclonePath: dict | None

    # Map styling
    fillColour: str
    fillOpacity: float
    fillOpacityActive: float
    lineColour: str
    lineOpacity: float
    lineWidth: float
    icon: str
    iconOpacity: float
    iconSize: float
    visible: str


class FeatureGeometry(TypedDict):
    """Geometry for a Feature - can be Point, Polygon, MultiPolygon, or GeometryCollection."""
    type: str
    crs: CRS
    coordinates: list  # Structure varies by type


class Feature(TypedDict):
    """GeoJSON Feature with extended properties."""
    type: Literal["Feature"]
    id: str
    geometry: FeatureGeometry
    properties: FeatureProperties
```

---

## Location and Weather Types

### State

```python
class State(TypedDict):
    """State information."""
    id: str  # e.g., "nsw"
    __typename: Literal["State"]
```

### ABC Region

```python
class ABCRegion(TypedDict):
    """ABC Local Radio region."""
    region: str  # e.g., "sydney"
    regionName: str  # e.g., "Sydney"
    __typename: Literal["ABCRegion"]
```

### Location

```python
class Location(TypedDict):
    """Location from location search."""
    id: str  # e.g., "aurora://location/loc46e6625bb24d"
    suburb: str  # e.g., "Sydney"
    state: State
    postcode: str  # e.g., "2000"
    lat: str  # e.g., "-33.8688" (note: string, not float)
    long: str  # e.g., "151.2093" (note: string, not float)
    abcRegion: ABCRegion
    __typename: Literal["Location"]
```

### Location Search Response

```python
class LocationResults(TypedDict):
    """Location search results."""
    byLocalitySearch: list[Location]
    __typename: Literal["LocationsRoot"]


class LocationSearchResponse(TypedDict):
    """Response from /locationSearch endpoint."""
    locations: LocationResults
```

### Weather Types

```python
WeatherIcon = Literal[
    "Clear",
    "Cloud",
    "LightShower",
    "PartCloudy",
    "Storm",
    "Sunny",
]

UVDescription = Literal["Extreme", "Very High", "High", "Moderate", "Low"] | None

WindDirection = Literal["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


class WeatherForecast(TypedDict):
    """Weather forecast data for a single day."""
    dailyRainfallRange: str  # "0 mm", "0 to 1 mm"
    dayName: str  # "Saturday"
    expectedWeatherDescription: str  # "Cloudy", "Possible shower"
    expectedWindDirection: str  # "NE", "SE"
    expectedWindSpeedKph: int  # 17
    icon: str  # "Cloud", "LightShower", "PartCloudy"
    maximumTemperature: int  # 39
    minimumTemperature: int  # 23
    rainfallProbability: int  # 0-100
    startTime: str  # "2025-12-06 00:00:00"
    uvDescription: str | None  # "Extreme", "High", or null
    uvIndex: int  # 0-12+
    __typename: Literal["WeatherUrbanForecast"]


class CurrentConditions(TypedDict):
    """Current weather conditions."""
    feelsLikeTempC: float  # 26.8
    generationTime: str  # ISO 8601
    relativeHumidityPct: int  # 0-100
    startTime: str  # ISO 8601
    tempC: float  # 30.4
    __typename: Literal["WeatherHistoricDetailedConditionsData"]


class HistoricConditions(TypedDict):
    """Container for historic conditions values."""
    values: list[CurrentConditions]
    __typename: Literal["WeatherHistoricDetailedConditions"]


class UrbanForecast(TypedDict):
    """Container for forecast data."""
    forecasts: list[WeatherForecast]
    __typename: Literal["WeatherUrbanForecastLocation"]


class Weather(TypedDict):
    """Weather resource containing forecasts and conditions."""
    urbanForecast: UrbanForecast
    detailedHistoricConditions: list[HistoricConditions]
    __typename: Literal["WeatherResource"]


class LocationWithWeather(TypedDict):
    """Location with weather data."""
    id: str
    suburb: str
    state: State
    postcode: str
    abcRegion: ABCRegion
    weather: Weather
    __typename: Literal["Location"]


class LocationByIdResult(TypedDict):
    """Result for location by ID lookup."""
    byId: LocationWithWeather
    __typename: Literal["LocationsRoot"]


class LocationAndWeatherResponse(TypedDict):
    """Response from /locationAndWeather endpoint with WEATHER query."""
    locations: LocationByIdResult
```

---

## Disclaimer Content Types

```python
class DescriptorNode(TypedDict, total=False):
    """A node in the descriptor tree."""
    type: Literal["tagname", "text"]
    key: str  # HTML tag or "@@standfirst"
    props: dict  # HTML attributes like href, target, rel
    children: list[DescriptorNode]
    content: str  # Text content (for type="text")


class DisclaimerContent(TypedDict):
    """Disclaimer content structure."""
    descriptor: DescriptorNode


class Disclaimer(TypedDict):
    """Disclaimer information."""
    disclaimerHeading: str
    disclaimerContent: DisclaimerContent
    disclaimerContentUri: str  # e.g., "coremedia://teaser/12433246"


class EmergencyServices(TypedDict):
    """Emergency services information."""
    emergencyServicesHeading: str
    emergencyServicesContentPrepared: DisclaimerContent
    emergencyServicesContentUri: str


class DisclaimerContentResponse(TypedDict):
    """Response from /disclaimerContent endpoint."""
    disclaimer: Disclaimer
    emergencyServices: EmergencyServices
```

---

## Literal Type Values

### Complete Reference

| Category | Field | Values |
|----------|-------|--------|
| Alert Level | `alertLevelInfoPrepared.level` | `extreme`, `severe`, `moderate`, `minor` |
| Alert Text | `alertLevelInfoPrepared.text` | `""`, `Advice`, `Emergency`, `Watch and Act` |
| Alert Style | `alertLevelInfoPrepared.style` | `extreme`, `severe`, `moderate`, `minor` |
| Event Icon | `eventLabelPrepared.icon` | `fire`, `heat`, `other`, `weather` |
| Feature Alert Type | `properties.alertType` | `warning`, `incident` |
| ABC Alert Level | `properties.abcAlertLevel` | `10`, `20`, `30`, `35`, `40`, `45`, `46`, `99` |
| Fill/Line Color | `properties.fillColour` | `#fff`, `#fbe032`, `#ff9b45`, `#d31717` |

---

## Size Field Format Notes

The `cardBody.size` field has different formats depending on the source:

| Source | Format | Examples |
|--------|--------|----------|
| NSW RFS, Fire and Rescue NSW, etc. | Integer with unit | `"100 ha"`, `"0 ha"`, `"9706 ha"` |
| Tasmania Fire Service | Decimal without unit | `"706.500"`, `"43.900"` |
| BOM/Weather warnings | Absent or null | Field may not exist |

---

## Sample Objects

### Sample Emergency Object (Fire Service)

```json
{
  "id": "AUREMER-72446a8d6888092c5e42f6ed9985f935",
  "headline": "Milsons Gully",
  "to": "/emergency/warning/AUREMER-72446a8d6888092c5e42f6ed9985f935",
  "alertLevelInfoPrepared": {
    "text": "Emergency",
    "level": "extreme",
    "style": "extreme"
  },
  "emergencyTimestampPrepared": {
    "date": "2025-12-06T05:34:00+00:00",
    "formattedTime": "4:34:00 pm AEDT",
    "prefix": "Effective from",
    "updatedTime": "2025-12-06T05:53:02.97994+00:00"
  },
  "eventLabelPrepared": {
    "icon": "fire",
    "labelText": "Bushfire"
  },
  "cardBody": {
    "type": "Bush Fire",
    "size": "9706 ha",
    "status": "Being controlled",
    "source": "NSW Rural Fire Service"
  },
  "geometry": {
    "crs": {
      "type": "name",
      "properties": {
        "name": "EPSG:4326"
      }
    },
    "type": "GeometryCollection",
    "geometries": [
      {
        "type": "Point",
        "coordinates": [150.37262, -32.339939]
      },
      {
        "type": "Polygon",
        "coordinates": [[[150.286554, -32.380201], ...]]
      }
    ]
  }
}
```

### Sample BOM Warning Object

BOM warnings have some differences from fire service incidents:

```json
{
  "id": "AUREMER-2e8be225833f43cc63cccf9eef5f0922",
  "headline": "Severe heatwave warning for New South Wales",
  "to": "/emergency/warning/AUREMER-2e8be225833f43cc63cccf9eef5f0922",
  "alertLevelInfoPrepared": {
    "text": "",
    "level": "severe",
    "style": "minor"
  },
  "emergencyTimestampPrepared": {
    "date": "2025-12-06T03:26:30+00:00",
    "formattedTime": "2:26:30 pm AEDT",
    "prefix": "Effective from",
    "updatedTime": "2025-12-06T03:48:17.071859+00:00"
  },
  "eventLabelPrepared": {
    "icon": "other",
    "labelText": "Heatwave"
  },
  "cardBody": {
    "type": null,
    "status": "Active",
    "source": "Australian Government Bureau of Meteorology"
  },
  "geometry": {
    "crs": {
      "type": "name",
      "properties": {
        "name": "EPSG:4326"
      }
    },
    "type": "MultiPolygon",
    "coordinates": [[[[148.468676, -33.614906], ...]]]
  }
}
```

Key differences:
- `alertLevelInfoPrepared.text` is empty string `""`
- `alertLevelInfoPrepared.style` is `"minor"` even when `level` is `"severe"`
- `cardBody.type` is `null`
- `cardBody.size` is absent (no size field at all)
- `geometry.type` is `"MultiPolygon"` directly (not wrapped in GeometryCollection)

### Sample GeoJSON Feature Object

```json
{
  "type": "Feature",
  "id": "AUREMER-72446a8d6888092c5e42f6ed9985f935",
  "geometry": {
    "type": "GeometryCollection",
    "crs": {
      "type": "name",
      "properties": { "name": "EPSG:4326" }
    },
    "geometries": [
      { "type": "Point", "coordinates": [150.3735, -32.3403] },
      { "type": "Polygon", "coordinates": [...] }
    ]
  },
  "properties": {
    "id": "AUREMER-72446a8d6888092c5e42f6ed9985f935",
    "state": "nsw",
    "headline": "Milsons Gully",
    "textSummary": "The New South Wales Rural Fire Service says there is an Emergency-level Bushfire at Merriwa",
    "senderName": "NSW Rural Fire Service",
    "orgName": "NSW Rural Fire Service",
    "orgWeb": "https://www.rfs.nsw.gov.au/",
    "orgAttribution": "Data supplied by <a href=\"https://www.rfs.nsw.gov.au/\" target=\"_blank\">NSW Rural Fire Service</a>",
    "event": "Bushfire",
    "alertType": "warning",
    "alertLevel": "Emergency",
    "alertLevelRaw": "Emergency Warning",
    "abcAlertLevel": "10",
    "displaySequence": 10,
    "incidentType": "Bush Fire",
    "incidentStatus": "Being controlled",
    "size": "9706 ha",
    "certainty": "Unknown",
    "sent": "2025-12-06T05:34:00+00:00",
    "effective": "2025-12-06T05:34:00+00:00",
    "areaDesc": "CULLINGRAL RD, MERRIWA 2329",
    "responseTypes": ["Monitor"],
    "cyclonePath": null,
    "affectedAbcRegion": {
      "region": "upperhunter",
      "regionName": "Upper Hunter",
      "serviceName": "local_upperhunter",
      "serviceNameRadio": "local_upperhunter",
      "brandName": "ABC Upper Hunter"
    },
    "centroid": { "type": "Point", "coordinates": [150.3735, -32.3403] },
    "systemCreatedTime": "2025-12-06T05:47:55.151307+00:00",
    "systemUpdatedTime": "2025-12-06T06:07:58.045699+00:00",
    "systemArchivedTime": null,
    "fillColour": "#d31717",
    "fillOpacity": 0.16,
    "fillOpacityActive": 0.26,
    "lineColour": "#d31717",
    "lineOpacity": 0.8,
    "lineWidth": 1.8,
    "icon": "FireExtremeDefault",
    "iconOpacity": 1,
    "iconSize": 0.5,
    "visible": "true"
  }
}
```

### Sample Weather Response

```json
{
  "locations": {
    "byId": {
      "id": "aurora://location/loc46e6625bb24d",
      "suburb": "Sydney",
      "state": { "id": "nsw", "__typename": "State" },
      "postcode": "2000",
      "abcRegion": {
        "region": "sydney",
        "regionName": "Sydney",
        "__typename": "ABCRegion"
      },
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

### Sample Location Search Response

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
