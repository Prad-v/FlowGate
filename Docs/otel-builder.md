# OpenTelemetry Collector Builder

The OpenTelemetry Collector Builder is a visual drag-and-drop interface for creating OpenTelemetry Collector configurations. It provides an intuitive way to design collector pipelines without manually writing YAML configuration files.

## Overview

The builder allows users to:
- Drag and drop components (receivers, processors, exporters, connectors, extensions) onto a canvas
- Connect components to create data pipelines
- Configure component properties through a visual interface
- Preview the generated YAML configuration in real-time
- Save configurations as templates with version control
- Export and import builder state as JSON

## Accessing the Builder

1. Navigate to the **Templates** page in the FlowGate UI
2. Click the **"Open Builder"** button in the top-right corner
3. The builder interface will open in a new tab

## Component Palette

The left sidebar displays the component palette, organized by component type:

- **Receivers**: Components that receive telemetry data (e.g., `otlp`, `prometheus`, `filelog`)
- **Processors**: Components that process telemetry data (e.g., `batch`, `resource`, `attributes`)
- **Exporters**: Components that export telemetry data (e.g., `otlp`, `prometheus`, `loki`)
- **Connectors**: Components that connect pipelines (e.g., `routing`, `spanmetrics`)
- **Extensions**: Components that extend collector functionality (e.g., `health_check`, `pprof`)

### Component Metadata Sources

The builder supports two metadata sources:

- **Static**: Uses bundled component metadata (faster, works offline)
- **Live**: Fetches component metadata from the OpenTelemetry registry (requires internet, more up-to-date)

You can toggle between sources using the "Data Source" selector in the component palette.

### Filtering Components

- **Search**: Type in the search box to filter components by name or description
- **Type Filter**: Use the dropdown to filter by component type (receivers, processors, etc.)

## Building a Configuration

### Adding Components

1. **Drag and Drop**: Drag a component from the palette onto the canvas
2. **Add Pipeline**: Click the "Add Pipeline" button to create a pipeline node

### Connecting Components

1. Click and drag from a component's output handle to another component's input handle
2. Connections represent data flow in the pipeline
3. Pipeline nodes should be connected to the components they include

### Configuring Components

1. Click on a component node to select it
2. The right sidebar will show the component configuration panel
3. Edit the following properties:
   - **Component ID**: The unique identifier for this component instance
   - **Label**: Display name for the component
   - **Pipeline Type** (for pipeline nodes): Select `metrics`, `logs`, or `traces`
   - **Configuration**: JSON configuration for the component

### Pipeline Configuration

Pipelines define how telemetry flows through the collector:

1. Create a pipeline node using the "Add Pipeline" button
2. Set the pipeline type (metrics, logs, or traces)
3. Connect components to the pipeline node:
   - Receivers should connect to the pipeline (data flows into the pipeline)
   - Processors should be connected between receivers and exporters
   - Exporters should connect from the pipeline (data flows out of the pipeline)

## YAML Preview

The right sidebar displays a live preview of the generated YAML configuration. The preview updates automatically as you modify the graph.

### Warnings

If there are any issues with the configuration (e.g., missing pipeline types, invalid connections), warnings will be displayed above the YAML preview.

## Saving as Template

1. Click the **"Save as Template"** button in the canvas toolbar
2. Fill in the template details:
   - **Template Name**: Required name for the template
   - **Description**: Optional description
   - **Template Type**: Select the appropriate type (composite, metrics, logs, traces, routing)
3. Click **"Save"** to create the template

The template will be saved with version control and can be managed from the Templates page.

## Export and Import

### Exporting Builder State

1. Click the **"Export JSON"** button in the canvas toolbar
2. The builder state (nodes and edges) will be displayed in a modal
3. Click **"Copy to Clipboard"** to copy the JSON
4. Save the JSON to a file for later use

### Importing Builder State

1. Click the **"Import JSON"** button in the canvas toolbar
2. Select a JSON file containing builder state
3. The graph will be restored with all nodes and connections

## API Reference

### Get Components

```http
GET /api/v1/otel/components
```

Query Parameters:
- `component_type` (optional): Filter by type (`receiver`, `processor`, `exporter`, `connector`, `extension`)
- `source` (default: `static`): Metadata source (`static` or `live`)
- `search` (optional): Search term to filter components

Response:
```json
{
  "component_type": "all",
  "source": "static",
  "items": {
    "receivers": [...],
    "processors": [...],
    "exporters": [...],
    "connectors": [...],
    "extensions": [...]
  }
}
```

### Generate Configuration

```http
POST /api/v1/otel/builder/generate
```

Request Body:
```json
{
  "nodes": [
    {
      "id": "node-1",
      "type": "receiver",
      "component_id": "otlp",
      "label": "OTLP Receiver",
      "config": {},
      "position": { "x": 100, "y": 100 }
    },
    {
      "id": "node-2",
      "type": "pipeline",
      "component_id": "pipeline-1",
      "pipeline_type": "metrics",
      "position": { "x": 300, "y": 100 }
    }
  ],
  "edges": [
    {
      "id": "edge-1",
      "source": "node-1",
      "target": "node-2"
    }
  ]
}
```

Response:
```json
{
  "yaml": "receivers:\n  otlp:\n    ...",
  "pipelines": {
    "metrics/pipeline-1": {
      "receivers": ["otlp"],
      "processors": [],
      "exporters": []
    }
  },
  "warnings": []
}
```

## Troubleshooting

### Components Not Loading

- Check your internet connection if using "Live" source
- Try switching to "Static" source
- Check browser console for errors

### YAML Generation Fails

- Ensure pipeline nodes have a `pipeline_type` set
- Verify that components are properly connected
- Check the warnings panel for specific issues

### Import Fails

- Ensure the JSON file matches the expected format
- Verify that all required fields (`nodes`, `edges`) are present
- Check browser console for parsing errors

## Best Practices

1. **Start with Receivers**: Add receivers first, then connect processors and exporters
2. **Use Descriptive Labels**: Give components meaningful labels for easier identification
3. **Organize with Pipelines**: Use pipeline nodes to group related components
4. **Validate Before Saving**: Review the YAML preview and warnings before saving
5. **Export Regularly**: Export your work as JSON to avoid losing progress

## Examples

### Simple Metrics Pipeline

1. Drag `prometheus` receiver onto canvas
2. Drag `batch` processor onto canvas
3. Drag `otlp` exporter onto canvas
4. Create a pipeline node and set type to `metrics`
5. Connect: `prometheus` → `batch` → `otlp` → `pipeline`
6. Save as template

### Multi-Signal Pipeline

1. Create separate pipelines for metrics, logs, and traces
2. Connect appropriate receivers to each pipeline
3. Add processors specific to each signal type
4. Connect exporters to each pipeline
5. Save as a composite template

## Related Documentation

- [Template Management](api.md#templates) - Managing templates with version control
- [OpenTelemetry Collector Documentation](https://opentelemetry.io/docs/collector/) - Official collector docs
- [Component Registry](https://opentelemetry.io/ecosystem/registry/) - OpenTelemetry component registry

