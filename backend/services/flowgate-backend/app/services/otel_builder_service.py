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

