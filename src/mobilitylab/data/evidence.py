"""Load and validate the compact public mobility-evidence catalog.

The catalog contains accepted aggregate results and provenance, never raw feeds,
city geometries, endpoint URLs, or a synthetic sum across evidence layers.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CATALOG = ROOT / "catalog" / "open-data-evidence.json"
REQUIRED_LAYERS = {
    "global_city_frame",
    "gtfs_static",
    "gtfs_realtime",
    "osm_map_features",
    "gbfs_shared_mobility",
    "model_interoperability",
}


def load_evidence_catalog(path: str | Path | None = None) -> dict[str, Any]:
    """Read the compact evidence catalog and validate its public contract."""
    catalog_path = Path(path) if path is not None else DEFAULT_CATALOG
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    validate_evidence_catalog(catalog)
    return catalog


def validate_evidence_catalog(catalog: dict[str, Any]) -> None:
    """Reject malformed catalogs and cross-layer coverage arithmetic."""
    if catalog.get("schema_version") != "mobilitylab_open_data_evidence_v1":
        raise ValueError("Unsupported open-data evidence schema")
    if catalog.get("layers_are_additive") is not False:
        raise ValueError("Evidence layers must be explicitly non-additive")
    layers = catalog.get("layers")
    if not isinstance(layers, list):
        raise ValueError("layers must be a list")
    ids = [layer.get("id") for layer in layers if isinstance(layer, dict)]
    if len(ids) != len(set(ids)):
        raise ValueError("Evidence layer IDs must be unique")
    if set(ids) != REQUIRED_LAYERS:
        raise ValueError(f"Unexpected evidence layers: {sorted(set(ids) ^ REQUIRED_LAYERS)}")
    for layer in layers:
        if layer.get("additive_across_layers") is not False:
            raise ValueError(f"Layer is not marked non-additive: {layer.get('id')}")
        metrics = layer.get("metrics")
        if not isinstance(metrics, list) or not metrics:
            raise ValueError(f"Layer has no metrics: {layer.get('id')}")
        for metric in metrics:
            if not isinstance(metric.get("value"), (int, float, str)):
                raise ValueError(f"Metric value is not scalar: {layer.get('id')}")
            if metric.get("strict_count_effect") not in (0, 439):
                raise ValueError("Only the frozen strict catalog scenario may affect strict count")
        if not layer.get("does_not_support"):
            raise ValueError(f"Missing claim boundary: {layer.get('id')}")


def headline_metrics(catalog: dict[str, Any] | None = None) -> dict[str, int | float | str]:
    """Return layer-qualified headline values keyed by metric ID."""
    source = catalog or load_evidence_catalog()
    values: dict[str, int | float | str] = {}
    for layer in source["layers"]:
        for metric in layer["metrics"]:
            key = f"{layer['id']}.{metric['id']}"
            if key in values:
                raise ValueError(f"Duplicate qualified metric ID: {key}")
            values[key] = metric["value"]
    return values
