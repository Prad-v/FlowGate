from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Literal, Optional, Set, Tuple

import yaml
from pydantic import BaseModel, Field, validator


class PositionModel(BaseModel):
    x: float
    y: float


class BuilderNodeModel(BaseModel):
    id: str
    type: Literal["receiver", "processor", "exporter", "connector", "extension", "pipeline"]
    component_id: str
    label: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    pipeline_type: Optional[Literal["metrics", "logs", "traces"]] = None
    position: Optional[PositionModel] = None

    @validator("component_id")
    def validate_component_id(cls, value: str) -> str:
        if not value:
            raise ValueError("component_id is required")
        return value


class BuilderEdgeModel(BaseModel):
    id: str
    source: str
    target: str


class BuilderGenerateRequest(BaseModel):
    nodes: List[BuilderNodeModel]
    edges: List[BuilderEdgeModel]


class BuilderGenerateResponse(BaseModel):
    yaml: str
    pipelines: Dict[str, Any]
    warnings: List[str]


SECTION_MAP = {
    "receiver": "receivers",
    "processor": "processors",
    "exporter": "exporters",
    "connector": "connectors",
    "extension": "extensions",
}


class OtelBuilderService:
    """Transforms builder node/edge graphs into collector configuration YAML."""

    def __init__(self) -> None:
        pass

    def generate_config(self, payload: BuilderGenerateRequest) -> BuilderGenerateResponse:
        node_map = {node.id: node for node in payload.nodes}
        forward_graph = defaultdict(list)
        reverse_graph = defaultdict(list)
        for edge in payload.edges:
            if edge.source in node_map and edge.target in node_map:
                forward_graph[edge.source].append(edge.target)
                reverse_graph[edge.target].append(edge.source)

        sections: Dict[str, Dict[str, Any]] = defaultdict(dict)
        warnings: List[str] = []

        for node in payload.nodes:
            if node.type == "pipeline":
                continue
            section_name = SECTION_MAP.get(node.type)
            if not section_name:
                continue
            sections[section_name][node.component_id] = node.config or {}

        pipelines: Dict[str, Any] = {}
        for node in payload.nodes:
            if node.type != "pipeline":
                continue
            if not node.pipeline_type:
                warnings.append(f"Pipeline node '{node.label or node.id}' is missing pipeline_type")
                continue
            reachable = self._collect_upstream(node.id, reverse_graph)
            ordered_nodes = self._sort_nodes(reachable, node_map)
            pipeline_key = f"{node.pipeline_type}/{node.component_id}"
            pipelines[pipeline_key] = self._build_pipeline_sections(ordered_nodes, node_map)

        config: Dict[str, Any] = {}
        config.update({k: v for k, v in sections.items() if v})
        config["service"] = {"pipelines": pipelines}

        yaml_body = yaml.safe_dump(config, sort_keys=False)
        return BuilderGenerateResponse(yaml=yaml_body, pipelines=pipelines, warnings=warnings)

    def _collect_upstream(self, start: str, reverse_graph: Dict[str, List[str]]) -> Set[str]:
        visited: Set[str] = set()
        stack = [start]
        while stack:
            current = stack.pop()
            for parent in reverse_graph.get(current, []):
                if parent not in visited:
                    visited.add(parent)
                    stack.append(parent)
        return visited

    def _sort_nodes(self, node_ids: Set[str], node_map: Dict[str, BuilderNodeModel]) -> List[BuilderNodeModel]:
        def node_sort_key(node_id: str) -> Tuple[float, str]:
            node = node_map[node_id]
            position = node.position.x if node.position else 0.0  # type: ignore[union-attr]
            return (position, node.component_id)

        return [node_map[node_id] for node_id in sorted(node_ids, key=node_sort_key)]

    def _build_pipeline_sections(
        self, nodes: List[BuilderNodeModel], node_map: Dict[str, BuilderNodeModel]
    ) -> Dict[str, List[str]]:
        pipeline: Dict[str, List[str]] = {"receivers": [], "processors": [], "exporters": []}

        def append_unique(section: str, component_id: str) -> None:
            if component_id not in pipeline.setdefault(section, []):
                pipeline[section].append(component_id)

        for node in nodes:
            if node.type == "receiver":
                append_unique("receivers", node.component_id)
            elif node.type == "processor":
                append_unique("processors", node.component_id)
            elif node.type == "exporter":
                append_unique("exporters", node.component_id)
            elif node.type == "connector":
                append_unique("connectors", node.component_id)
        return pipeline

    def parse_config(self, yaml_content: str) -> BuilderGenerateRequest:
        """
        Parse YAML configuration and convert it to builder graph format.
        
        Args:
            yaml_content: YAML configuration string
            
        Returns:
            BuilderGenerateRequest with nodes and edges
        """
        try:
            config = yaml.safe_load(yaml_content)
            if not config:
                return BuilderGenerateRequest(nodes=[], edges=[])
            
            nodes: List[BuilderNodeModel] = []
            edges: List[BuilderEdgeModel] = []
            node_id_map: Dict[str, str] = {}  # Maps component_id to node id (for lookup by component_id)
            node_id_map_by_type: Dict[tuple, str] = {}  # Maps (component_type, component_id) to node id
            pipeline_nodes: Dict[str, List[str]] = {}  # Maps pipeline key to ordered component IDs
            
            # Reverse SECTION_MAP for lookup
            section_to_type = {v: k for k, v in SECTION_MAP.items()}
            
            # Extract components from sections
            x_position = 0
            y_position = 0
            y_spacing = 150
            
            for section_name, components in config.items():
                if section_name == "service":
                    continue
                    
                component_type = section_to_type.get(section_name)
                if not component_type:
                    continue
                
                for component_id, component_config in components.items():
                    # Skip invalid component IDs
                    if not component_id or not isinstance(component_id, str):
                        continue
                    
                    # Handle component IDs with slashes (e.g., "otlp/observability-backend")
                    # Use the full component_id as the key, but create a safe node ID
                    base_component_id = component_id.split('/')[0] if '/' in component_id else component_id
                    
                    # Generate unique node ID - use component_id directly to ensure uniqueness
                    node_id = f"{component_type}-{component_id.replace('/', '-')}-{len(nodes)}"
                    # Store in both maps for different lookup needs
                    node_id_map[component_id] = node_id  # Last one wins (for backward compatibility)
                    node_id_map_by_type[(component_type, component_id)] = node_id  # Type-specific lookup
                    
                    # Ensure config is a dict
                    if not isinstance(component_config, dict):
                        component_config = {}
                    
                    # Create node
                    try:
                        node = BuilderNodeModel(
                            id=node_id,
                            type=component_type,
                            component_id=component_id,
                            label=component_id,
                            config=component_config,
                            position=PositionModel(x=x_position, y=y_position),
                        )
                        nodes.append(node)
                    except Exception as e:
                        # Skip invalid nodes
                        continue
                    
                    y_position += y_spacing
                    if y_position > 800:
                        y_position = 0
                        x_position += 250
            
            # Extract pipelines and build edges
            if "service" in config and "pipelines" in config["service"]:
                pipelines = config["service"]["pipelines"]
                
                for pipeline_key, pipeline_config in pipelines.items():
                    # Parse pipeline key
                    # Format can be either "traces" or "traces/my-pipeline"
                    if "/" in pipeline_key:
                        parts = pipeline_key.split("/", 1)
                        pipeline_type, pipeline_id = parts[0], parts[1]
                    else:
                        # If no slash, the key itself is the pipeline type
                        pipeline_type = pipeline_key
                        pipeline_id = pipeline_key  # Use type as ID for simple pipelines
                    
                    # Collect components by type in order
                    receiver_ids: List[str] = []
                    processor_ids: List[str] = []
                    exporter_ids: List[str] = []
                    connector_ids: List[str] = []
                    
                    if "receivers" in pipeline_config:
                        receiver_ids = pipeline_config["receivers"]
                    if "processors" in pipeline_config:
                        processor_ids = pipeline_config["processors"]
                    if "exporters" in pipeline_config:
                        exporter_ids = pipeline_config["exporters"]
                    if "connectors" in pipeline_config:
                        connector_ids = pipeline_config["connectors"]
                    
                    # Create pipeline node
                    pipeline_node_id = f"pipeline-{pipeline_id}-{len(nodes)}"
                    pipeline_node = BuilderNodeModel(
                        id=pipeline_node_id,
                        type="pipeline",
                        component_id=pipeline_id,
                        label=pipeline_id,
                        config={},
                        pipeline_type=pipeline_type,
                        position=PositionModel(x=x_position + 200, y=len(pipelines) * y_spacing),
                    )
                    nodes.append(pipeline_node)
                    
                    # Build edges showing the flow: receivers -> processors -> exporters -> pipeline
                    # All components also connect to pipeline for upstream collection in generate_config
                    
                    # Track all component node IDs for pipeline connection
                    all_component_node_ids: List[str] = []
                    
                    # Connect receivers to processors (if processors exist)
                    receiver_node_ids: List[str] = []
                    for receiver_id in receiver_ids:
                        # Look up receiver by type to avoid conflicts with same-named components
                        receiver_key = ("receiver", receiver_id)
                        if receiver_key in node_id_map_by_type:
                            receiver_node_id = node_id_map_by_type[receiver_key]
                            receiver_node_ids.append(receiver_node_id)
                            all_component_node_ids.append(receiver_node_id)
                            
                            # Connect receiver to first processor
                            if processor_ids:
                                first_processor_id = processor_ids[0]
                                processor_key = ("processor", first_processor_id)
                                if processor_key in node_id_map_by_type:
                                    processor_node_id = node_id_map_by_type[processor_key]
                                    edge = BuilderEdgeModel(
                                        id=f"edge-{receiver_node_id}-{processor_node_id}-{len(edges)}",
                                        source=receiver_node_id,
                                        target=processor_node_id,
                                    )
                                    edges.append(edge)
                    
                    # Connect processors in sequence
                    processor_node_ids: List[str] = []
                    prev_processor_node_id = None
                    for processor_id in processor_ids:
                        processor_key = ("processor", processor_id)
                        if processor_key in node_id_map_by_type:
                            processor_node_id = node_id_map_by_type[processor_key]
                            processor_node_ids.append(processor_node_id)
                            all_component_node_ids.append(processor_node_id)
                            
                            # Connect previous processor to current processor
                            if prev_processor_node_id:
                                edge = BuilderEdgeModel(
                                    id=f"edge-{prev_processor_node_id}-{processor_node_id}-{len(edges)}",
                                    source=prev_processor_node_id,
                                    target=processor_node_id,
                                )
                                edges.append(edge)
                            
                            prev_processor_node_id = processor_node_id
                    
                    # Connect last processor (or receivers if no processors) to exporters
                    source_node_ids = processor_node_ids if processor_node_ids else receiver_node_ids
                    if source_node_ids and exporter_ids:
                        last_source_node_id = source_node_ids[-1]
                        first_exporter_id = exporter_ids[0]
                        exporter_key = ("exporter", first_exporter_id)
                        if exporter_key in node_id_map_by_type:
                            exporter_node_id = node_id_map_by_type[exporter_key]
                            edge = BuilderEdgeModel(
                                id=f"edge-{last_source_node_id}-{exporter_node_id}-{len(edges)}",
                                source=last_source_node_id,
                                target=exporter_node_id,
                            )
                            edges.append(edge)
                    
                    # Connect exporters in sequence
                    exporter_node_ids: List[str] = []
                    prev_exporter_node_id = None
                    for exporter_id in exporter_ids:
                        exporter_key = ("exporter", exporter_id)
                        if exporter_key in node_id_map_by_type:
                            exporter_node_id = node_id_map_by_type[exporter_key]
                            exporter_node_ids.append(exporter_node_id)
                            all_component_node_ids.append(exporter_node_id)
                            
                            # Connect previous exporter to current exporter
                            if prev_exporter_node_id:
                                edge = BuilderEdgeModel(
                                    id=f"edge-{prev_exporter_node_id}-{exporter_node_id}-{len(edges)}",
                                    source=prev_exporter_node_id,
                                    target=exporter_node_id,
                                )
                                edges.append(edge)
                            
                            prev_exporter_node_id = exporter_node_id
                    
                    # Handle connectors
                    for connector_id in connector_ids:
                        connector_key = ("connector", connector_id)
                        if connector_key in node_id_map_by_type:
                            connector_node_id = node_id_map_by_type[connector_key]
                            all_component_node_ids.append(connector_node_id)
                    
                    # Connect all components to pipeline (for upstream collection in generate_config)
                    for component_node_id in all_component_node_ids:
                        edge = BuilderEdgeModel(
                            id=f"edge-{component_node_id}-{pipeline_node_id}-{len(edges)}",
                            source=component_node_id,
                            target=pipeline_node_id,
                        )
                        edges.append(edge)
            
            return BuilderGenerateRequest(nodes=nodes, edges=edges)
            
        except Exception as e:
            raise ValueError(f"Failed to parse YAML configuration: {str(e)}")

