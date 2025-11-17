from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Literal, Any

import httpx

from app.config import settings

STATIC_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "otel_components_static.json"
REGISTRY_INDEX_URL = "https://opentelemetry.io/ecosystem/registry/index.json"

ComponentType = Literal["receiver", "processor", "exporter", "connector", "extension"]
ComponentSource = Literal["static", "live"]


class ComponentCatalogService:
    """Provides component metadata for the builder (static + live)."""

    def __init__(self) -> None:
        self._static_data = self._load_static_components()
        self._live_cache: Dict[str, Any] = {"timestamp": 0, "data": None}
        self._cache_ttl = 60 * 60  # 1 hour

    def _load_static_components(self) -> Dict[str, List[Dict[str, Any]]]:
        if not STATIC_DATA_PATH.exists():
            return {}
        with STATIC_DATA_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _get_live_registry(self) -> Optional[List[Dict[str, Any]]]:
        now = time.time()
        if self._live_cache["data"] and now - self._live_cache["timestamp"] < self._cache_ttl:
            return self._live_cache["data"]

        try:
            with httpx.Client(timeout=settings.http_timeout_seconds) as client:
                resp = client.get(REGISTRY_INDEX_URL)
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, list):
                    self._live_cache = {"timestamp": now, "data": data}
                    return data
        except Exception:
            # Fail silently - callers will fall back to static data
            return None
        return None

    def _normalize_entry(self, entry: Dict[str, Any], component_type: ComponentType) -> Dict[str, Any]:
        urls = entry.get("urls") or {}
        default_config: Dict[str, Any] = {}
        if component_type == "receiver" and entry.get("title", "").lower().startswith("prometheus"):
            default_config = {
                "config": {
                    "scrape_configs": [
                        {
                            "job_name": "default",
                            "static_configs": [{"targets": ["0.0.0.0:8888"]}],
                        }
                    ]
                }
            }
        return {
            "id": entry.get("package", {}).get("name") or entry.get("_key") or entry.get("title"),
            "name": entry.get("title"),
            "type": component_type,
            "description": entry.get("description"),
            "doc_url": urls.get("docs") or urls.get("repo") or urls.get("website"),
            "stability": ", ".join(entry.get("flags", [])) or None,
            "language": entry.get("language"),
            "tags": entry.get("tags") or [],
            "supported_signals": entry.get("tags", []),
            "default_config": default_config,
        }

    def get_components(
        self,
        component_type: Optional[ComponentType] = None,
        source: ComponentSource = "static",
        search: Optional[str] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        if source == "live":
            result = self._get_live_components(component_type, search)
            if result:
                return result
        return self._get_static_components(component_type, search)

    def _get_static_components(
        self, component_type: Optional[ComponentType], search: Optional[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        data = self._static_data
        if component_type:
            entries = data.get(f"{component_type}s", [])
            return {
                f"{component_type}s": self._filter_entries(entries, search, component_type)
            }
        filtered = {}
        for key, entries in data.items():
            inferred_type = key[:-1] if key.endswith("s") else key
            filtered[key] = self._filter_entries(entries, search, inferred_type)  # type: ignore[arg-type]
        return filtered

    def _get_live_components(
        self, component_type: Optional[ComponentType], search: Optional[str]
    ) -> Optional[Dict[str, List[Dict[str, Any]]]]:
        registry = self._get_live_registry()
        if not registry:
            return None

        def convert(entries: List[Dict[str, Any]], ctype: ComponentType) -> List[Dict[str, Any]]:
            normalized = [self._normalize_entry(entry, ctype) for entry in entries]
            return self._filter_entries(normalized, search, ctype)

        registry_types = ["receiver", "processor", "exporter", "extension", "connector"]

        if component_type:
            if component_type not in registry_types:
                return None
            entries = [item for item in registry if item.get("registryType") == component_type]
            return {f"{component_type}s": convert(entries, component_type)}

        aggregated: Dict[str, List[Dict[str, Any]]] = {}
        for rt in registry_types:
            entries = [item for item in registry if item.get("registryType") == rt]
            aggregated[f"{rt}s"] = convert(entries, rt)  # type: ignore[arg-type]
        return aggregated

    def _filter_entries(
        self, entries: List[Dict[str, Any]], search: Optional[str], component_type: Optional[str]
    ) -> List[Dict[str, Any]]:
        if not search:
            return entries
        term = search.lower()
        filtered = []
        for entry in entries:
            haystacks = [
                entry.get("name", ""),
                entry.get("id", ""),
                entry.get("description", ""),
                entry.get("doc_url", ""),
            ]
            if component_type:
                haystacks.append(component_type)
            if any(term in (text or "").lower() for text in haystacks):
                filtered.append(entry)
        return filtered

