# ABC Emergency Dashboard Examples

This directory contains example Lovelace dashboard configurations for displaying ABC Emergency incidents.

## Files

| File | Description |
|------|-------------|
| `dashboard_emergency_map.yaml` | Complete dashboard with 4 views: Map, Overview, Bushfires, All Incidents |
| `cards/map_card.yaml` | Simple map card for embedding in any dashboard |
| `cards/alert_status_card.yaml` | Color-coded alert status tiles with status message |
| `cards/incident_summary_card.yaml` | Entity list showing incident counts |

## Usage

### Full Dashboard

1. Copy `dashboard_emergency_map.yaml` to your Home Assistant config directory
2. Add to your `configuration.yaml`:

```yaml
lovelace:
  mode: storage
  dashboards:
    emergency:
      mode: yaml
      title: Emergency
      icon: mdi:alert
      show_in_sidebar: true
      filename: dashboard_emergency_map.yaml
```

3. Restart Home Assistant

### Individual Cards

Copy the YAML from any card file and paste it into your Lovelace dashboard using the "Manual" card option in the UI editor.

## Configuration

All examples use placeholder entity names. You must update them to match your installation:

1. **Entity names**: Replace `treehouse` with your zone name (lowercase, underscores for spaces)
   - Example: `sensor.abc_emergency_treehouse_bushfires` -> `sensor.abc_emergency_sydney_bushfires`

2. **Map source**: Replace `ABC Emergency (Treehouse)` with your config entry title
   - Find this in Settings > Devices & Services > ABC Emergency
   - Example: `ABC Emergency (Sydney)`, `ABC Emergency (Melbourne)`

## Views

The full dashboard includes:

- **Map**: Full-screen interactive map showing all incidents as markers
- **Overview**: Dashboard with embedded map, alert tiles, and incident summary
- **Bushfires**: Focused view with map and bushfire incident table
- **All Incidents**: Scrollable list of all nearby incidents with details
