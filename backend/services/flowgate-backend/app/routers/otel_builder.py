from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.otel_component_catalog import (
    ComponentCatalogService,
    ComponentSource,
    ComponentType,
)
from app.services.otel_builder_service import (
    OtelBuilderService,
    BuilderGenerateRequest,
    BuilderGenerateResponse,
)

router = APIRouter(prefix="/otel", tags=["otel-builder"])

catalog_service = ComponentCatalogService()
builder_service = OtelBuilderService()


@router.get("/components")
def list_components(
    component_type: ComponentType | None = Query(None, description="Component type filter"),
    source: ComponentSource = Query("static", description="Metadata source: static or live"),
    search: str | None = Query(None, description="Search string"),
):
    """
    Returns metadata describing collector components used by the builder.
    """
    components = catalog_service.get_components(component_type=component_type, source=source, search=search)
    return {
        "component_type": component_type or "all",
        "source": source,
        "items": components,
    }


@router.post("/builder/generate", response_model=BuilderGenerateResponse)
def generate_config(payload: BuilderGenerateRequest):
    """
    Converts the builder node/edge graph into collector YAML.
    """
    try:
        return builder_service.generate_config(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


class ParseConfigRequest(BaseModel):
    yaml_content: str


@router.post("/builder/parse", response_model=BuilderGenerateRequest)
def parse_config(payload: ParseConfigRequest):
    """
    Parses YAML configuration and converts it to builder node/edge graph format.
    """
    try:
        return builder_service.parse_config(payload.yaml_content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

