from app.services.otel_builder_service import (
    OtelBuilderService,
    BuilderGenerateRequest,
    BuilderNodeModel,
    BuilderEdgeModel,
)


def test_builder_generates_yaml_for_simple_pipeline():
    service = OtelBuilderService()
    nodes = [
        BuilderNodeModel(id="r1", type="receiver", component_id="otlp", config={"protocols": {"grpc": {}}}),
        BuilderNodeModel(id="p1", type="processor", component_id="batch"),
        BuilderNodeModel(id="e1", type="exporter", component_id="otlphttp", config={"endpoint": "http://collector:4318"}),
        BuilderNodeModel(id="pipeline", type="pipeline", component_id="default", pipeline_type="traces"),
    ]
    edges = [
        BuilderEdgeModel(id="r1-p1", source="r1", target="p1"),
        BuilderEdgeModel(id="p1-e1", source="p1", target="e1"),
        BuilderEdgeModel(id="e1-pipe", source="e1", target="pipeline"),
    ]

    payload = BuilderGenerateRequest(nodes=nodes, edges=edges)

    result = service.generate_config(payload)

    assert "receivers" in result.yaml
    assert "otlphttp" in result.yaml
    assert "service" in result.yaml
    assert result.pipelines

