#!/usr/bin/env python3
"""Thin, reproducible builder for the MCL Central Boston database.

The source GMNS files are never modified.  All paths in the config are resolved
relative to the task root so that the work tree can be moved as a unit.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import hashlib
import json
import math
import os
import sqlite3
import subprocess
import sys
import time
import urllib.request
import io
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import h3
import networkx as nx
import numpy as np
import pandas as pd
from pyproj import Transformer
from shapely import wkt
from shapely.geometry import LineString, Point, Polygon, box, mapping
from shapely.ops import transform


import os
TASK_ROOT = Path(os.environ.get("MCL_BOSTON_SOURCE_ROOT", Path(__file__).resolve().parents[1])).resolve()
DEFAULT_CONFIG = TASK_ROOT / "config" / "city_config.yaml"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    # JSON is a strict subset of YAML.  This avoids an unnecessary PyYAML
    # dependency while keeping the user-requested filename and portability.
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_task_path(value: str | Path) -> Path:
    value = Path(value)
    return value if value.is_absolute() else TASK_ROOT / value


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, value: Any) -> None:
    ensure_parent(path)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_geojson(path: Path, features: list[dict[str, Any]]) -> None:
    write_json(path, {"type": "FeatureCollection", "features": features})


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def append_csv(path: Path, fieldnames: list[str], row: dict[str, Any]) -> None:
    ensure_parent(path)
    exists = path.exists() and path.stat().st_size > 0
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerow({name: row.get(name, "") for name in fieldnames})


def append_tool_usage(
    component: str,
    source_version: str,
    function_or_cli: str,
    inputs: str,
    outputs: str,
    status: str,
    notes: str = "",
) -> None:
    append_csv(
        TASK_ROOT / "provenance" / "tool_usage.csv",
        [
            "recorded_at_utc",
            "component",
            "source_version",
            "function_or_cli",
            "inputs",
            "outputs",
            "execution_status",
            "notes",
        ],
        {
            "recorded_at_utc": utc_now(),
            "component": component,
            "source_version": source_version,
            "function_or_cli": function_or_cli,
            "inputs": inputs,
            "outputs": outputs,
            "execution_status": status,
            "notes": notes,
        },
    )


def process_rss_bytes() -> int | None:
    if os.name != "nt":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        counters = PROCESS_MEMORY_COUNTERS()
        counters.cb = ctypes.sizeof(counters)
        handle = ctypes.windll.kernel32.GetCurrentProcess()
        ok = ctypes.windll.psapi.GetProcessMemoryInfo(
            handle, ctypes.byref(counters), counters.cb
        )
        return int(counters.WorkingSetSize) if ok else None
    except Exception:
        return None


def record_stage(
    stage: str,
    started: float,
    input_rows: int,
    output_rows: int,
    input_bytes: int,
    output_paths: Iterable[Path],
    status: str = "completed",
    notes: str = "",
) -> None:
    output_bytes = sum(p.stat().st_size for p in output_paths if p.exists() and p.is_file())
    row = {
        "stage": stage,
        "status": status,
        "started_at_utc": datetime.fromtimestamp(started, tz=timezone.utc).isoformat(),
        "finished_at_utc": utc_now(),
        "wall_seconds": round(time.time() - started, 6),
        "sampled_process_rss_bytes_at_finish": process_rss_bytes(),
        "input_rows": int(input_rows),
        "output_rows": int(output_rows),
        "input_bytes": int(input_bytes),
        "output_bytes": int(output_bytes),
        "notes": notes,
    }
    path = TASK_ROOT / "provenance" / "stage_runs.jsonl"
    ensure_parent(path)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def source_tables(config: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    source_dir = resolve_task_path(config["network"]["source_dir"])
    ids = {
        "node_id": "string",
        "zone_id": "string",
    }
    node = pd.read_csv(source_dir / "node.csv", dtype=ids, keep_default_na=False)
    link = pd.read_csv(
        source_dir / "link.csv",
        dtype={"link_id": "string", "from_node_id": "string", "to_node_id": "string"},
        keep_default_na=False,
    )
    demand = pd.read_csv(
        source_dir / "demand.csv",
        dtype={"o_zone_id": "string", "d_zone_id": "string"},
        keep_default_na=False,
    )
    return node, link, demand


def transformers(config: dict[str, Any]) -> tuple[Transformer, Transformer]:
    analysis_crs = config["study_area"]["analysis_crs"]
    forward = Transformer.from_crs("EPSG:4326", analysis_crs, always_xy=True)
    reverse = Transformer.from_crs(analysis_crs, "EPSG:4326", always_xy=True)
    return forward, reverse


def boundary_geometries(config: dict[str, Any]) -> tuple[Polygon, Polygon, Polygon, Polygon]:
    west, south, east, north = config["study_area"]["core_bbox_wgs84"]
    core_wgs = box(west, south, east, north)
    forward, reverse = transformers(config)
    core_metric = transform(forward.transform, core_wgs)
    analysis_metric = core_metric.buffer(config["study_area"]["analysis_buffer_m"])
    analysis_wgs = transform(reverse.transform, analysis_metric)
    return core_wgs, analysis_wgs, core_metric, analysis_metric


def classify_against_boundaries(geom: Any, core: Polygon, analysis: Polygon) -> str:
    if geom.within(core):
        return "core_inside"
    if geom.intersects(core):
        return "core_crossing"
    if geom.within(analysis):
        return "analysis_buffer_inside"
    if geom.intersects(analysis):
        return "analysis_boundary_crossing"
    return "outside"


def build_network(config: dict[str, Any]) -> dict[str, Any]:
    started = time.time()
    node, link, _ = source_tables(config)
    source_dir = resolve_task_path(config["network"]["source_dir"])
    input_bytes = sum((source_dir / name).stat().st_size for name in ("node.csv", "link.csv"))

    core_wgs, analysis_wgs, core_metric, analysis_metric = boundary_geometries(config)
    forward, _ = transformers(config)
    link["_geom"] = link["geometry"].map(wkt.loads)
    link["_geom_metric"] = link["_geom"].map(lambda g: transform(forward.transform, g))

    connector_type = int(config["network"]["centroid_connector_link_type"])
    link_type_numeric = pd.to_numeric(link["link_type"], errors="coerce")
    physical_mask = link_type_numeric.ne(connector_type)
    selected_physical = link.loc[
        physical_mask & link["_geom_metric"].map(analysis_metric.intersects)
    ].copy()
    physical_node_ids = set(selected_physical["from_node_id"]) | set(
        selected_physical["to_node_id"]
    )
    selected_connectors = link.loc[
        ~physical_mask
        & (
            link["from_node_id"].isin(physical_node_ids)
            | link["to_node_id"].isin(physical_node_ids)
        )
    ].copy()
    selected = pd.concat([selected_physical, selected_connectors], ignore_index=True)
    selected_node_ids = set(selected["from_node_id"]) | set(selected["to_node_id"])
    selected_nodes = node[node["node_id"].isin(selected_node_ids)].copy()

    network_id = config["network"]["network_id"]
    network_version = config["network"]["network_version"]
    selected_nodes["source_node_id"] = selected_nodes["node_id"]
    selected_nodes["network_id"] = network_id
    selected_nodes["network_version"] = network_version
    selected_nodes["node_role"] = np.where(
        selected_nodes["zone_id"].astype(str).str.len().gt(0), "source_taz_centroid", "physical"
    )
    selected_nodes["boundary_status"] = [
        classify_against_boundaries(Point(float(x), float(y)), core_wgs, analysis_wgs)
        for x, y in zip(selected_nodes["x_coord"], selected_nodes["y_coord"])
    ]

    selected["source_link_id"] = selected["link_id"]
    selected["network_id"] = network_id
    selected["network_version"] = network_version
    selected["is_physical"] = pd.to_numeric(selected["link_type"], errors="coerce").ne(
        connector_type
    )
    selected["is_centroid_connector"] = ~selected["is_physical"]
    selected["gps_match_allowed"] = selected["is_physical"]
    selected["geometry_quality"] = "source_provided_curved_centerline_wkt"
    selected["boundary_status"] = [
        classify_against_boundaries(g, core_wgs, analysis_wgs) for g in selected["_geom"]
    ]
    selected["crosses_core_boundary"] = selected["boundary_status"].eq("core_crossing")

    node_out = TASK_ROOT / "database" / "network" / "gmns" / "node.csv"
    link_out = TASK_ROOT / "database" / "network" / "gmns" / "link.csv"
    matcher_node_out = TASK_ROOT / "database" / "network" / "matcher" / "node.csv"
    matcher_link_out = TASK_ROOT / "database" / "network" / "matcher" / "link.csv"
    ensure_parent(node_out)
    ensure_parent(matcher_node_out)
    selected_nodes.to_csv(node_out, index=False)
    selected.drop(columns=["_geom", "_geom_metric"]).to_csv(link_out, index=False)
    matcher_nodes = selected_nodes[selected_nodes["node_id"].isin(physical_node_ids)].copy()
    matcher_links = selected[selected["is_physical"]].copy()
    matcher_nodes.to_csv(matcher_node_out, index=False)
    matcher_links.drop(columns=["_geom", "_geom_metric"]).to_csv(matcher_link_out, index=False)

    boundary_props = {
        "network_id": network_id,
        "network_version": network_version,
        "crs": "EPSG:4326",
    }
    core_out = TASK_ROOT / "database" / "boundary" / "core.geojson"
    analysis_out = TASK_ROOT / "database" / "boundary" / "analysis.geojson"
    write_geojson(
        core_out,
        [{"type": "Feature", "properties": {**boundary_props, "boundary": "core"}, "geometry": mapping(core_wgs)}],
    )
    write_geojson(
        analysis_out,
        [
            {
                "type": "Feature",
                "properties": {
                    **boundary_props,
                    "boundary": "analysis",
                    "buffer_m": config["study_area"]["analysis_buffer_m"],
                },
                "geometry": mapping(analysis_wgs),
            }
        ],
    )

    field_mapping = pd.DataFrame(
        [
            ("node", "node_id", "node_id", "string", "identifier", "identity", "source primary key; preserve as string"),
            ("node", "zone_id", "zone_id", "string", "source TAZ identifier", "identity", "never reused for H3 or OMDV IDs"),
            ("node", "x_coord", "x_coord", "float64", "decimal degree longitude EPSG:4326", "identity", "source coordinate"),
            ("node", "y_coord", "y_coord", "float64", "decimal degree latitude EPSG:4326", "identity", "source coordinate"),
            ("node", "geometry", "geometry", "WKT POINT", "EPSG:4326", "identity", "source geometry"),
            ("link", "link_id", "link_id", "string", "identifier", "identity", "source primary key; preserve as string"),
            ("link", "from_node_id", "from_node_id", "string", "identifier", "identity", "directed A node"),
            ("link", "to_node_id", "to_node_id", "string", "identifier", "identity", "directed B node"),
            ("link", "dir_flag", "dir_flag", "integer", "source code", "identity", "links are already directed rows"),
            ("link", "length", "length", "float64", "metre", "identity", "source metric view"),
            ("link", "vdf_length_mi", "vdf_length_mi", "float64", "mile", "identity", "source VDF view; not mixed with length"),
            ("link", "free_speed", "free_speed", "float64", "kilometre/hour", "identity", "source metric view"),
            ("link", "vdf_free_speed_mph", "vdf_free_speed_mph", "float64", "mile/hour", "identity", "source VDF view"),
            ("link", "vdf_fftt", "vdf_fftt", "float64", "minute", "identity", "source free-flow travel time"),
            ("link", "vdf_toll", "vdf_toll", "float64", "source-defined generalized-cost term", "identity", "not treated as observed money without source evidence"),
            ("link", "link_type", "link_type", "integer", "source facility code", "identity", "0 is a nonphysical centroid connector"),
            ("link", "vdf_alpha", "vdf_alpha", "float64", "dimensionless", "identity", "source BPR/VDF parameter"),
            ("link", "vdf_beta", "vdf_beta", "float64", "dimensionless", "identity", "source BPR/VDF exponent"),
            ("link", "vdf_plf", "vdf_plf", "float64", "dimensionless", "identity", "source peak-load factor"),
            ("link", "lanes", "lanes", "integer", "lane count", "identity", "source provided"),
            ("link", "capacity", "capacity", "float64", "source VDF vehicles/time period", "identity", "VDF parameter; not a hard flow ceiling"),
            ("link", "ref_volume", "ref_volume", "float64", "source volume unit", "identity", "source reference; provenance not upgraded to observed"),
            ("link", "obs_volume", "obs_volume", "float64", "source volume unit", "identity", "source field; zero is not treated as new observation"),
            ("link", "geometry", "geometry", "WKT LINESTRING", "EPSG:4326", "identity", "source curved centerline/reference line"),
        ],
        columns=["table", "source_field", "target_field", "target_type", "unit", "conversion", "basis"],
    )
    mapping_out = TASK_ROOT / "database" / "network" / "field_mapping.csv"
    field_mapping.to_csv(mapping_out, index=False)

    crosswalk_rows: list[dict[str, Any]] = []
    for identifier in selected_nodes["node_id"]:
        crosswalk_rows.append(
            {
                "entity_type": "node",
                "source_id": identifier,
                "current_id": identifier,
                "network_id": network_id,
                "network_version": network_version,
                "mapping_method": "identity_subset",
            }
        )
    for identifier in selected["link_id"]:
        crosswalk_rows.append(
            {
                "entity_type": "link",
                "source_id": identifier,
                "current_id": identifier,
                "network_id": network_id,
                "network_version": network_version,
                "mapping_method": "identity_subset",
            }
        )
    crosswalk_out = TASK_ROOT / "database" / "network" / "id_crosswalk.csv"
    pd.DataFrame(crosswalk_rows).to_csv(crosswalk_out, index=False)

    provenance_rows = []
    for row in field_mapping.itertuples(index=False):
        provenance_rows.append(
            {
                "entity_table": row.table,
                "attribute": row.target_field,
                "record_scope": "all retained source records",
                "provenance_class": "source_provided",
                "source_id": "gmns_plus_21_boston",
                "method": row.conversion,
                "unit": row.unit,
                "network_id": network_id,
                "network_version": network_version,
            }
        )
    provenance_out = TASK_ROOT / "database" / "network" / "attribute_provenance.csv"
    pd.DataFrame(provenance_rows).to_csv(provenance_out, index=False)

    profile_out = TASK_ROOT / "database" / "network" / "gmns_profile.json"
    write_json(
        profile_out,
        {
            "profile_id": "mcl_boston_gmns_plus_analysis_v1",
            "network_id": network_id,
            "network_version": network_version,
            "crs": "EPSG:4326",
            "directed_link_rows": True,
            "source_profile": "GMNS Plus 21_Boston",
            "source_commit": config["network"]["source_commit"],
            "physical_link_types": config["network"]["physical_link_types"],
            "centroid_connector_link_type": connector_type,
            "matcher_view": "database/network/matcher (physical links only)",
            "assignment_view": "generated later from physical network and H3 access nodes",
            "extensions": [
                "network_id",
                "network_version",
                "source_node_id/source_link_id",
                "boundary_status",
                "gps_match_allowed",
                "geometry_quality",
            ],
            "extensions_are_official_gmns": False,
        },
    )

    node_lookup = selected_nodes.set_index("node_id")
    endpoint_errors = []
    for from_node_id, to_node_id, geom in zip(
        selected["from_node_id"], selected["to_node_id"], selected["_geom"]
    ):
        start = Point(geom.coords[0])
        end = Point(geom.coords[-1])
        a = node_lookup.loc[str(from_node_id)]
        b = node_lookup.loc[str(to_node_id)]
        a_point = Point(float(a.x_coord), float(a.y_coord))
        b_point = Point(float(b.x_coord), float(b.y_coord))
        endpoint_errors.append(
            (
                transform(forward.transform, start).distance(transform(forward.transform, a_point)),
                transform(forward.transform, end).distance(transform(forward.transform, b_point)),
            )
        )
    metric_physical = selected[selected["is_physical"]]
    length_error = (
        pd.to_numeric(metric_physical["length"], errors="coerce")
        - pd.to_numeric(metric_physical["vdf_length_mi"], errors="coerce") * 1609.344
    ).abs()
    speed_error = (
        pd.to_numeric(metric_physical["free_speed"], errors="coerce")
        - pd.to_numeric(metric_physical["vdf_free_speed_mph"], errors="coerce") * 1.609344
    ).abs()
    fftt_calc = (
        pd.to_numeric(metric_physical["vdf_length_mi"], errors="coerce")
        / pd.to_numeric(metric_physical["vdf_free_speed_mph"], errors="coerce")
        * 60.0
    )
    fftt_error = (fftt_calc - pd.to_numeric(metric_physical["vdf_fftt"], errors="coerce")).abs()
    pairs = list(zip(selected["from_node_id"], selected["to_node_id"]))
    pair_counts = Counter(pairs)
    pair_set = set(pairs)
    validation = {
        "validated_at_utc": utc_now(),
        "network_id": network_id,
        "network_version": network_version,
        "source_rows": {"nodes": len(node), "links": len(link)},
        "retained_rows": {
            "nodes_total": len(selected_nodes),
            "physical_nodes": len(physical_node_ids),
            "links_total": len(selected),
            "physical_links": len(selected_physical),
            "centroid_connectors": len(selected_connectors),
        },
        "checks": {
            "node_pk_unique": bool(selected_nodes["node_id"].is_unique),
            "link_pk_unique": bool(selected["link_id"].is_unique),
            "from_fk_missing": int((~selected["from_node_id"].isin(selected_node_ids)).sum()),
            "to_fk_missing": int((~selected["to_node_id"].isin(selected_node_ids)).sum()),
            "all_link_geometry_parseable": bool(selected["_geom"].notna().all()),
            "max_from_endpoint_error_m": float(max(x[0] for x in endpoint_errors)),
            "max_to_endpoint_error_m": float(max(x[1] for x in endpoint_errors)),
            "max_length_vs_mile_conversion_error_m": float(length_error.max()),
            "max_speed_conversion_error_kmh": float(speed_error.max()),
            "max_fftt_formula_error_min": float(fftt_error.max()),
            "parallel_directed_pairs": int(sum(v > 1 for v in pair_counts.values())),
            "links_with_reverse_pair": int(sum((b, a) in pair_set for a, b in pairs)),
            "crossing_core_links": int(selected["crosses_core_boundary"].sum()),
        },
        "interpretation": {
            "connector_rule": "link_type=0 is retained for source TAZ access but excluded from physical/matcher views",
            "units": "length/free_speed and vdf_* remain separate documented unit views",
            "capacity": "source VDF parameter, not a hard physical flow ceiling",
        },
    }
    validation_out = TASK_ROOT / "reports" / "network_validation.json"
    write_json(validation_out, validation)

    outputs = [
        node_out,
        link_out,
        matcher_node_out,
        matcher_link_out,
        core_out,
        analysis_out,
        mapping_out,
        crosswalk_out,
        provenance_out,
        profile_out,
        validation_out,
    ]
    record_stage(
        "build_network",
        started,
        len(node) + len(link),
        len(selected_nodes) + len(selected),
        input_bytes,
        outputs,
        notes="Metric buffer in EPSG:32619; raw source unchanged.",
    )
    append_tool_usage(
        "GMNS network subset and validation",
        f"GMNS Plus commit {config['network']['source_commit']}",
        "tools/city_database.py build-network",
        config["network"]["source_dir"],
        "database/network/gmns; database/network/matcher; reports/network_validation.json",
        "completed",
        "Matcher view excludes link_type=0 centroid connectors.",
    )
    return validation


def h3_polygon(cell_id: str) -> Polygon:
    boundary = h3.cell_to_boundary(cell_id)
    return Polygon([(lng, lat) for lat, lng in boundary])


def _tag_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    if isinstance(value, (list, tuple, set)):
        return ";".join(str(x) for x in value)
    return str(value)


def fetch_osm_activity(config: dict[str, Any]) -> dict[str, Any]:
    """Fetch only core-area OSM building and POI features through OSMnx."""
    started = time.time()
    import osmnx as ox

    raw_dir = TASK_ROOT / "raw" / "osm"
    cache_dir = raw_dir / "osmnx_cache"
    raw_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    ox.settings.use_cache = True
    ox.settings.cache_folder = str(cache_dir)
    ox.settings.requests_timeout = 180
    ox.settings.log_console = True
    # The default public endpoint returned repeated 504 responses for even a
    # quarter-core query.  Use another documented public Overpass instance;
    # the query and OSM data semantics are unchanged.
    ox.settings.overpass_url = "https://overpass.kumi.systems/api"
    ox.settings.overpass_rate_limit = False
    bbox = tuple(config["study_area"]["core_bbox_wgs84"])
    west, south, east, north = bbox
    middle_x = (west + east) / 2.0
    middle_y = (south + north) / 2.0
    building_tiles = [
        (west, south, middle_x, middle_y),
        (middle_x, south, east, middle_y),
        (west, middle_y, middle_x, north),
        (middle_x, middle_y, east, north),
    ]
    poi_tags = {
        "amenity": True,
        "shop": True,
        "office": True,
        "tourism": True,
        "leisure": True,
    }
    datasets = [
        ("buildings", [(tile, {"building": True}) for tile in building_tiles]),
        ("pois", [(bbox, poi_tags)]),
    ]
    outputs: list[Path] = []
    counts: dict[str, int] = {}
    request_log: list[dict[str, Any]] = []
    for name, requests in datasets:
        output = raw_dir / f"{name}.csv"
        frames = []
        for request_bbox, tags in requests:
            gdf = ox.features_from_bbox(request_bbox, tags)
            frames.append(gdf.reset_index())
            request_log.append({"dataset": name, "bbox": request_bbox, "tags": tags})
        flat = pd.concat(frames, ignore_index=True)
        keep = [
            col
            for col in [
                "element",
                "id",
                "name",
                "building",
                "building:levels",
                "amenity",
                "shop",
                "office",
                "tourism",
                "leisure",
                "landuse",
                "geometry",
            ]
            if col in flat.columns
        ]
        selected = flat[keep].copy()
        if "element" not in selected:
            selected["element"] = ""
        if "id" not in selected:
            selected["id"] = np.arange(len(selected)).astype(str)
        selected["osm_type"] = selected["element"].map(_tag_text)
        selected["osm_id"] = selected["id"].map(_tag_text)
        selected["source_feature_id"] = (
            selected["osm_type"].astype(str) + ":" + selected["osm_id"].astype(str)
        )
        selected["geometry_wkt"] = selected["geometry"].map(lambda value: value.wkt)
        selected["geometry_type"] = selected["geometry"].map(lambda value: value.geom_type)
        selected["source_id"] = "openstreetmap"
        selected["source_retrieved_at_utc"] = utc_now()
        selected["source_license"] = "ODbL-1.0"
        selected = selected.drop(columns=[c for c in ("element", "id", "geometry") if c in selected])
        for col in selected.columns:
            selected[col] = selected[col].map(_tag_text)
        selected.to_csv(output, index=False)
        outputs.append(output)
        counts[name] = len(selected)

    metadata_out = raw_dir / "acquisition.json"
    write_json(
        metadata_out,
        {
            "retrieved_at_utc": utc_now(),
            "source": "OpenStreetMap via OSMnx features_from_bbox",
            "osmnx_version": ox.__version__,
            "bbox_wgs84": bbox,
            "requests": request_log,
            "outputs": {
                path.name: {
                    "rows": counts[path.stem],
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
                for path in outputs
            },
            "attribution": "© OpenStreetMap contributors",
            "license": "ODbL-1.0",
        },
    )
    outputs.append(metadata_out)
    record_stage(
        "fetch_osm_activity",
        started,
        0,
        sum(counts.values()),
        0,
        outputs,
        notes="Two sequential core-bbox queries; OSMnx HTTP cache retained for restartability.",
    )
    append_tool_usage(
        "OSM activity acquisition",
        f"OSMnx {ox.__version__}",
        "osmnx.features_from_bbox",
        json.dumps({"core_bbox": bbox, "requests": request_log}),
        "raw/osm/buildings.csv; raw/osm/pois.csv",
        "completed",
        "Core bbox only; ODbL attribution retained.",
    )
    return {"counts": counts, "files": [str(path.relative_to(TASK_ROOT)) for path in outputs]}


def build_activity(config: dict[str, Any]) -> dict[str, Any]:
    started = time.time()
    raw_dir = TASK_ROOT / "raw" / "osm"
    building_path = raw_dir / "buildings.csv"
    poi_path = raw_dir / "pois.csv"
    if not building_path.exists() or not poi_path.exists():
        raise FileNotFoundError("Run fetch-activity before build-activity")
    buildings = pd.read_csv(building_path, dtype="string", keep_default_na=False)
    pois = pd.read_csv(poi_path, dtype="string", keep_default_na=False)
    buildings = buildings.drop_duplicates("source_feature_id", keep="first").copy()
    pois = pois.drop_duplicates("source_feature_id", keep="first").copy()
    buildings["_geom"] = buildings["geometry_wkt"].map(wkt.loads)
    pois["_geom"] = pois["geometry_wkt"].map(wkt.loads)

    fine_res = int(config["zones"]["fine_resolution"])
    parent_res = int(config["zones"]["parent_resolution"])
    zones = pd.read_csv(TASK_ROOT / "database" / "zones" / "zone.csv", keep_default_na=False)
    fine = zones[zones["zone_level"].eq("fine")].copy()
    fine_cells = set(fine["full_cell_id"].astype(str))
    forward, _ = transformers(config)
    core_wgs, _, _, _ = boundary_geometries(config)
    residential_types = {
        "apartments",
        "bungalow",
        "cabin",
        "detached",
        "dormitory",
        "house",
        "residential",
        "semidetached_house",
        "terrace",
    }

    building_rows: list[dict[str, Any]] = []
    for _, row in buildings.iterrows():
        geom = row["_geom"]
        clipped = geom.intersection(core_wgs)
        if clipped.is_empty:
            continue
        rep = clipped.representative_point()
        cell = h3.latlng_to_cell(rep.y, rep.x, fine_res)
        if cell not in fine_cells:
            continue
        building_type = _tag_text(row.get("building", "")) or "unknown"
        area_m2 = transform(forward.transform, clipped).area if clipped.geom_type not in {"Point", "MultiPoint"} else 0.0
        building_rows.append(
            {
                "building_id": str(row["source_feature_id"]),
                "osm_type": str(row["osm_type"]),
                "osm_id": str(row["osm_id"]),
                "building_type": building_type,
                "building_class": "residential" if building_type in residential_types else ("unknown" if building_type in {"", "yes", "unknown"} else "nonresidential"),
                "area_m2": round(area_m2, 3),
                "area_status": "measured_from_osm_geometry" if area_m2 > 0 else "not_polygon_zero_area",
                "fine_zone_id": f"h3r{fine_res}:{cell}",
                "parent_zone_id": f"h3r{parent_res}:{h3.cell_to_parent(cell, parent_res)}",
                "assignment_method": "clipped_geometry_representative_point_h3",
                "source_id": "openstreetmap",
                "source_license": "ODbL-1.0",
                "geometry_wkt": clipped.wkt,
            }
        )
    building_out = TASK_ROOT / "database" / "activity" / "building.csv"
    pd.DataFrame(building_rows).to_csv(building_out, index=False)

    poi_rows: list[dict[str, Any]] = []
    tag_columns = ["amenity", "shop", "office", "tourism", "leisure"]
    for _, row in pois.iterrows():
        geom = row["_geom"]
        clipped = geom.intersection(core_wgs)
        if clipped.is_empty:
            continue
        rep = clipped.representative_point()
        cell = h3.latlng_to_cell(rep.y, rep.x, fine_res)
        if cell not in fine_cells:
            continue
        tags = [(col, _tag_text(row.get(col, ""))) for col in tag_columns]
        tags = [(key, value) for key, value in tags if value]
        category_key, category_value = tags[0] if tags else ("unknown", "unknown")
        poi_rows.append(
            {
                "poi_id": str(row["source_feature_id"]),
                "osm_type": str(row["osm_type"]),
                "osm_id": str(row["osm_id"]),
                "poi_name": _tag_text(row.get("name", "")),
                "poi_type": f"{category_key}:{category_value}",
                "all_type_tags": ";".join(f"{key}={value}" for key, value in tags),
                "fine_zone_id": f"h3r{fine_res}:{cell}",
                "parent_zone_id": f"h3r{parent_res}:{h3.cell_to_parent(cell, parent_res)}",
                "assignment_method": "geometry_representative_point_h3",
                "source_id": "openstreetmap",
                "source_license": "ODbL-1.0",
                "x_coord": rep.x,
                "y_coord": rep.y,
                "geometry_wkt": clipped.wkt,
            }
        )
    poi_out = TASK_ROOT / "database" / "activity" / "poi.csv"
    pd.DataFrame(poi_rows).to_csv(poi_out, index=False)

    building_frame = pd.DataFrame(building_rows)
    poi_frame = pd.DataFrame(poi_rows)
    activity_rows: list[dict[str, Any]] = []
    coefficients = config["demand_scenario"]["generation_proxy_coefficients"]
    for zone in fine.itertuples(index=False):
        zone_id = str(zone.zone_id)
        b = building_frame[building_frame["fine_zone_id"].eq(zone_id)] if not building_frame.empty else building_frame
        p = poi_frame[poi_frame["fine_zone_id"].eq(zone_id)] if not poi_frame.empty else poi_frame
        residential_area = float(b.loc[b["building_class"].eq("residential"), "area_m2"].sum()) if not b.empty else 0.0
        nonresidential_area = float(b.loc[b["building_class"].eq("nonresidential"), "area_m2"].sum()) if not b.empty else 0.0
        unknown_area = float(b.loc[b["building_class"].eq("unknown"), "area_m2"].sum()) if not b.empty else 0.0
        poi_count = len(p)
        production_proxy = (
            coefficients["production_residential_area_m2"] * residential_area
            + coefficients["production_nonresidential_area_m2"] * nonresidential_area
            + coefficients["production_poi_count"] * poi_count
        )
        attraction_proxy = (
            coefficients["attraction_residential_area_m2"] * residential_area
            + coefficients["attraction_nonresidential_area_m2"] * nonresidential_area
            + coefficients["attraction_poi_count"] * poi_count
        )
        activity_rows.append(
            {
                "zone_id": zone_id,
                "parent_zone_id": f"h3r{parent_res}:{h3.cell_to_parent(str(zone.full_cell_id), parent_res)}",
                "building_count": len(b),
                "building_area_m2": float(b["area_m2"].sum()) if not b.empty else 0.0,
                "residential_building_area_m2": residential_area,
                "nonresidential_building_area_m2": nonresidential_area,
                "unknown_building_area_m2": unknown_area,
                "poi_count": poi_count,
                "production_proxy_raw": production_proxy,
                "attraction_proxy_raw": attraction_proxy,
                "proxy_unit": "scenario_weight_not_population_or_employment",
                "building_assignment": "one_representative_point_per_unique_osm_feature",
                "source_id": "openstreetmap",
                "source_license": "ODbL-1.0",
                "status": "observed_osm_activity_proxy" if len(b) + poi_count > 0 else "no_osm_activity_in_snapshot",
                "network_id": config["network"]["network_id"],
                "network_version": config["network"]["network_version"],
            }
        )
    activity_out = TASK_ROOT / "database" / "activity" / "zone_activity.csv"
    activity_frame = pd.DataFrame(activity_rows)
    activity_frame.to_csv(activity_out, index=False)
    summary = {
        "built_at_utc": utc_now(),
        "unique_buildings": len(building_frame),
        "unique_pois": len(poi_frame),
        "fine_zones": len(activity_frame),
        "zones_with_activity": int(activity_frame["status"].eq("observed_osm_activity_proxy").sum()),
        "total_building_area_m2": float(activity_frame["building_area_m2"].sum()),
        "residential_area_m2": float(activity_frame["residential_building_area_m2"].sum()),
        "nonresidential_area_m2": float(activity_frame["nonresidential_building_area_m2"].sum()),
        "unknown_area_m2": float(activity_frame["unknown_building_area_m2"].sum()),
        "semantics": "Counts and areas are activity proxies, not observed population or employment.",
    }
    summary_out = TASK_ROOT / "reports" / "activity_summary.json"
    write_json(summary_out, summary)
    outputs = [building_out, poi_out, activity_out, summary_out]
    record_stage(
        "build_activity",
        started,
        len(buildings) + len(pois),
        len(building_frame) + len(poi_frame) + len(activity_frame),
        building_path.stat().st_size + poi_path.stat().st_size,
        outputs,
        notes="Unique OSM feature IDs; buildings assigned once by representative point to avoid duplicate counts.",
    )
    append_tool_usage(
        "Zone activity preparation",
        "Shapely 2.1.2; H3 4.5.0",
        "tools/city_database.py build-activity",
        "raw/osm/buildings.csv; raw/osm/pois.csv; database/zones/zone.csv",
        "database/activity",
        "completed",
        "OSM activity remains a proxy and is not called population or employment.",
    )
    return summary


def build_activity_fallback(config: dict[str, Any]) -> dict[str, Any]:
    """Build a transparent network-accessibility proxy when OSM activity is unavailable."""
    started = time.time()
    zones = pd.read_csv(TASK_ROOT / "database" / "zones" / "zone.csv", keep_default_na=False)
    fine = zones[zones["zone_level"].eq("fine")].copy()
    allocation = pd.read_csv(
        TASK_ROOT / "database" / "zones" / "zone_overlap_or_allocation.csv",
        dtype={"entity_id": "string"},
        keep_default_na=False,
    )
    nodes = pd.read_csv(
        TASK_ROOT / "database" / "network" / "matcher" / "node.csv",
        dtype={"node_id": "string"},
        keep_default_na=False,
    )
    links = pd.read_csv(
        TASK_ROOT / "database" / "network" / "matcher" / "link.csv",
        dtype={"link_id": "string", "from_node_id": "string", "to_node_id": "string"},
        keep_default_na=False,
    )
    fine_res = int(config["zones"]["fine_resolution"])
    parent_res = int(config["zones"]["parent_resolution"])
    node_zone = {
        str(row.entity_id): str(row.fine_zone_id)
        for row in allocation[allocation["status"].eq("allocated")].itertuples(index=False)
    }
    node_counts = Counter(node_zone.values())
    degree_counts: Counter[str] = Counter()
    link_length: defaultdict[str, float] = defaultdict(float)
    link_counts: Counter[str] = Counter()
    for row in links.itertuples(index=False):
        u = str(row.from_node_id)
        v = str(row.to_node_id)
        if u in node_zone:
            degree_counts[node_zone[u]] += 1
        if v in node_zone:
            degree_counts[node_zone[v]] += 1
        geom = wkt.loads(str(row.geometry))
        midpoint = geom.interpolate(0.5, normalized=True)
        cell = h3.latlng_to_cell(midpoint.y, midpoint.x, fine_res)
        zone_id = f"h3r{fine_res}:{cell}"
        if zone_id in set(fine["zone_id"]):
            link_length[zone_id] += float(row.length)
            link_counts[zone_id] += 1

    activity_rows = []
    for zone in fine.itertuples(index=False):
        zone_id = str(zone.zone_id)
        nodes_n = node_counts[zone_id]
        degree_n = degree_counts[zone_id]
        length_km = link_length[zone_id] / 1000.0
        production_proxy = nodes_n + 0.5 * length_km
        attraction_proxy = degree_n + length_km
        activity_rows.append(
            {
                "zone_id": zone_id,
                "parent_zone_id": f"h3r{parent_res}:{h3.cell_to_parent(str(zone.full_cell_id), parent_res)}",
                "building_count": "",
                "building_area_m2": "",
                "residential_building_area_m2": "",
                "nonresidential_building_area_m2": "",
                "unknown_building_area_m2": "",
                "poi_count": "",
                "physical_node_count": nodes_n,
                "directed_incident_degree_count": degree_n,
                "physical_link_midpoint_count": link_counts[zone_id],
                "physical_link_length_km": length_km,
                "production_proxy_raw": production_proxy,
                "attraction_proxy_raw": attraction_proxy,
                "proxy_unit": "network_accessibility_scenario_weight_not_activity_population_or_employment",
                "building_assignment": "not_available",
                "source_id": "gmns_plus_21_boston",
                "source_license": "Apache-2.0",
                "status": "fallback_network_accessibility_proxy" if nodes_n + link_counts[zone_id] > 0 else "no_network_activity_proxy",
                "network_id": config["network"]["network_id"],
                "network_version": config["network"]["network_version"],
            }
        )
    activity_out = TASK_ROOT / "database" / "activity" / "zone_activity.csv"
    activity = pd.DataFrame(activity_rows)
    activity.to_csv(activity_out, index=False)
    missing_out = TASK_ROOT / "database" / "activity" / "SOURCE_STATUS.md"
    missing_out.write_text(
        "# Activity source status\n\n"
        "OSM building and POI acquisition was attempted on 2026-09-22 through OSMnx 2.0.1. "
        "The default Overpass endpoint returned HTTP 504 for the full bbox and a quarter tile; "
        "the alternate Kumi endpoint timed out after 180 seconds for the same quarter tile. "
        "No building or POI rows are claimed. `zone_activity.csv` therefore contains an explicit "
        "network-accessibility engineering proxy derived from real GMNS nodes and links. It is "
        "not observed activity, population, employment, or a substitute for a later OSM refresh.\n",
        encoding="utf-8",
    )
    summary = {
        "built_at_utc": utc_now(),
        "status": "FALLBACK_NETWORK_ACCESSIBILITY_PROXY",
        "fine_zones": len(activity),
        "zones_with_nonzero_proxy": int((activity["production_proxy_raw"] > 0).sum()),
        "physical_nodes_counted": int(activity["physical_node_count"].sum()),
        "directed_link_midpoints_counted": int(activity["physical_link_midpoint_count"].sum()),
        "physical_link_length_km": float(activity["physical_link_length_km"].sum()),
        "missing": ["OSM buildings", "OSM POIs"],
        "semantics": "Scenario accessibility weights only; not observed activity, population, or employment.",
    }
    summary_out = TASK_ROOT / "reports" / "activity_summary.json"
    write_json(summary_out, summary)
    outputs = [activity_out, missing_out, summary_out]
    record_stage(
        "build_activity_fallback",
        started,
        len(nodes) + len(links),
        len(activity),
        (TASK_ROOT / "database" / "network" / "matcher" / "node.csv").stat().st_size
        + (TASK_ROOT / "database" / "network" / "matcher" / "link.csv").stat().st_size,
        outputs,
        status="completed_with_source_gap",
        notes="External OSM activity unavailable after bounded attempts; no synthetic POI/building records created.",
    )
    append_tool_usage(
        "Zone activity fallback",
        f"GMNS Plus commit {config['network']['source_commit']}",
        "tools/city_database.py build-activity-fallback",
        "database/network/matcher; database/zones",
        "database/activity/zone_activity.csv",
        "completed_with_source_gap",
        "Network accessibility proxy only; no building/POI claims.",
    )
    return summary


def _best_directed_graph(links: pd.DataFrame) -> tuple[nx.DiGraph, dict[tuple[str, str], str]]:
    graph = nx.DiGraph()
    best_link: dict[tuple[str, str], str] = {}
    for row in links.itertuples(index=False):
        u, v = str(row.from_node_id), str(row.to_node_id)
        weight = float(row.vdf_fftt)
        if not graph.has_edge(u, v) or weight < graph[u][v]["weight"]:
            graph.add_edge(u, v, weight=weight)
            best_link[(u, v)] = str(row.link_id)
    return graph, best_link


def _balance_gravity(
    productions: np.ndarray,
    attractions: np.ndarray,
    friction: np.ndarray,
    tolerance: float,
    max_iterations: int,
) -> tuple[np.ndarray, int, float]:
    matrix = friction.copy().astype(float)
    matrix[~np.isfinite(matrix)] = 0.0
    matrix[matrix < 0] = 0.0
    if not matrix.any():
        raise RuntimeError("Gravity seed matrix contains no reachable positive cells")
    for iteration in range(1, max_iterations + 1):
        row_sums = matrix.sum(axis=1)
        row_factors = np.divide(productions, row_sums, out=np.zeros_like(productions), where=row_sums > 0)
        matrix *= row_factors[:, None]
        col_sums = matrix.sum(axis=0)
        col_factors = np.divide(attractions, col_sums, out=np.zeros_like(attractions), where=col_sums > 0)
        matrix *= col_factors[None, :]
        row_error = np.max(np.abs(matrix.sum(axis=1) - productions))
        col_error = np.max(np.abs(matrix.sum(axis=0) - attractions))
        scale = max(float(productions.sum()), 1.0)
        error = max(float(row_error), float(col_error)) / scale
        if error <= tolerance:
            return matrix, iteration, error
    return matrix, max_iterations, error


def build_demand(config: dict[str, Any]) -> dict[str, Any]:
    started = time.time()
    demand_dir = TASK_ROOT / "database" / "demand"
    demand_dir.mkdir(parents=True, exist_ok=True)
    activity = pd.read_csv(TASK_ROOT / "database" / "activity" / "zone_activity.csv", keep_default_na=False)
    access = pd.read_csv(
        TASK_ROOT / "database" / "zones" / "zone_access.csv",
        dtype={"access_node_id": "string"},
        keep_default_na=False,
    )
    links = pd.read_csv(
        TASK_ROOT / "database" / "network" / "matcher" / "link.csv",
        dtype={"link_id": "string", "from_node_id": "string", "to_node_id": "string"},
        keep_default_na=False,
    )
    activity = activity.merge(
        access[["zone_id", "access_node_id", "access_distance_m", "status"]],
        on="zone_id",
        how="left",
        validate="one_to_one",
        suffixes=("", "_access"),
    )
    zone_ids = activity["zone_id"].astype(str).tolist()
    graph, _ = _best_directed_graph(links)
    skims = np.full((len(zone_ids), len(zone_ids)), np.inf, dtype=float)
    access_speed_m_per_min = 500.0  # 30 km/h model connector speed.
    access_costs = pd.to_numeric(activity["access_distance_m"], errors="coerce").fillna(0).to_numpy() / access_speed_m_per_min
    for i, origin_node in enumerate(activity["access_node_id"].astype(str)):
        distances = nx.single_source_dijkstra_path_length(graph, origin_node, weight="weight")
        for j, destination_node in enumerate(activity["access_node_id"].astype(str)):
            if destination_node in distances:
                base = float(distances[destination_node])
                if i == j or base == 0:
                    base = 1.0
                skims[i, j] = base + access_costs[i] + access_costs[j]
    skim_rows = []
    for i, origin in enumerate(zone_ids):
        for j, destination in enumerate(zone_ids):
            reachable = math.isfinite(skims[i, j])
            skim_rows.append(
                {
                    "o_zone_id": origin,
                    "d_zone_id": destination,
                    "impedance_min": skims[i, j] if reachable else "",
                    "network_time_component": "free_flow_vdf_fftt",
                    "access_time_component": "access_distance_at_30_kmh",
                    "unit": "minute",
                    "reachable": reachable,
                    "intrazonal": i == j,
                    "network_id": config["network"]["network_id"],
                    "network_version": config["network"]["network_version"],
                    "status": "reachable" if reachable else "unreachable_retained",
                }
            )
    skim_out = demand_dir / "skim.csv"
    pd.DataFrame(skim_rows).to_csv(skim_out, index=False)

    total = float(config["demand_scenario"]["daily_person_trip_total"])
    p_proxy = pd.to_numeric(activity["production_proxy_raw"], errors="coerce").fillna(0).to_numpy(float)
    a_proxy = pd.to_numeric(activity["attraction_proxy_raw"], errors="coerce").fillna(0).to_numpy(float)
    if p_proxy.sum() <= 0 or a_proxy.sum() <= 0:
        raise RuntimeError("No positive production/attraction proxy is available")
    productions = p_proxy / p_proxy.sum() * total
    attractions = a_proxy / a_proxy.sum() * total
    pa = pd.DataFrame(
        {
            "zone_id": zone_ids,
            "production_proxy_raw": p_proxy,
            "attraction_proxy_raw": a_proxy,
            "productions_person_trips_daily": productions,
            "attractions_person_trips_daily": attractions,
            "trip_purpose": "all_purpose_engineering_scenario",
            "period": "daily",
            "unit": "person_trips_per_scenario_day",
            "model": "scaled_activity_proxy",
            "scenario_id": config["demand_scenario"]["scenario_id"],
            "status": config["demand_scenario"]["status"],
            "network_id": config["network"]["network_id"],
            "network_version": config["network"]["network_version"],
        }
    )
    pa_out = demand_dir / "productions_attractions.csv"
    pa.to_csv(pa_out, index=False)

    beta = float(config["demand_scenario"]["beta_per_minute"])
    friction = np.exp(-beta * skims)
    friction[~np.isfinite(skims)] = 0.0
    matrix, balance_iterations, balance_error = _balance_gravity(
        productions,
        attractions,
        friction,
        float(config["demand_scenario"]["balance_tolerance"]),
        int(config["demand_scenario"]["balance_max_iterations"]),
    )
    od_rows = []
    for i, origin in enumerate(zone_ids):
        for j, destination in enumerate(zone_ids):
            volume = float(matrix[i, j])
            if volume <= 1e-10:
                continue
            od_rows.append(
                {
                    "o_zone_id": origin,
                    "d_zone_id": destination,
                    "person_trips_daily": volume,
                    "impedance_min": skims[i, j],
                    "friction_factor": friction[i, j],
                    "distribution_model": "doubly_constrained_gravity_ipf",
                    "friction_function": config["demand_scenario"]["friction_function"],
                    "beta_per_minute": beta,
                    "scenario_id": config["demand_scenario"]["scenario_id"],
                    "status": config["demand_scenario"]["status"],
                    "unit": "person_trips_per_scenario_day",
                    "network_id": config["network"]["network_id"],
                    "network_version": config["network"]["network_version"],
                }
            )
    od = pd.DataFrame(od_rows)
    od_out = demand_dir / "od_person.csv"
    od.to_csv(od_out, index=False)

    mode_shares = config["demand_scenario"]["mode_shares"]
    if abs(sum(mode_shares.values()) - 1.0) > 1e-12 or min(mode_shares.values()) < 0:
        raise ValueError("Configured mode shares must be nonnegative and sum to one")
    mode_share_rows = []
    mode_period_rows = []
    period_share = float(config["demand_scenario"]["am_peak_share_of_daily"])
    for row in od.itertuples(index=False):
        for mode, share in mode_shares.items():
            mode_share_rows.append(
                {
                    "o_zone_id": row.o_zone_id,
                    "d_zone_id": row.d_zone_id,
                    "mode": mode,
                    "mode_share": share,
                    "method": config["demand_scenario"]["mode_share_method"],
                    "scenario_id": row.scenario_id,
                    "status": "GIVEN_SHARE_NOT_CALIBRATED",
                }
            )
            daily_mode = float(row.person_trips_daily) * share
            mode_period_rows.append(
                {
                    "o_zone_id": row.o_zone_id,
                    "d_zone_id": row.d_zone_id,
                    "mode": mode,
                    "period": config["time"]["analysis_period_id"],
                    "daily_person_trips": daily_mode,
                    "period_share": period_share,
                    "person_trips": daily_mode * period_share,
                    "unit": "person_trips_per_analysis_period",
                    "assignment_status": "ready_for_drive_assignment" if mode == "drive" else "not_assigned_no_complete_mode_network",
                    "scenario_id": row.scenario_id,
                }
            )
    mode_share_out = demand_dir / "mode_share.csv"
    mode_period_out = demand_dir / "od_mode_period.csv"
    pd.DataFrame(mode_share_rows).to_csv(mode_share_out, index=False)
    mode_period = pd.DataFrame(mode_period_rows)
    mode_period.to_csv(mode_period_out, index=False)

    drive = mode_period[mode_period["mode"].eq("drive")].copy()
    occupancy = float(config["demand_scenario"]["drive_persons_per_vehicle"])
    drive["vehicle_trips"] = drive["person_trips"] / occupancy
    drive["persons_per_vehicle"] = occupancy
    drive["unit"] = "vehicle_trips_per_analysis_period"
    drive["conversion_method"] = "given_average_occupancy"
    vehicle_out = demand_dir / "od_vehicle_period.csv"
    drive.to_csv(vehicle_out, index=False)

    solver = drive.merge(
        access[["zone_id", "access_node_id"]].rename(columns={"zone_id": "o_zone_id", "access_node_id": "o_node_id"}),
        on="o_zone_id",
        how="left",
        validate="many_to_one",
    ).merge(
        access[["zone_id", "access_node_id"]].rename(columns={"zone_id": "d_zone_id", "access_node_id": "d_node_id"}),
        on="d_zone_id",
        how="left",
        validate="many_to_one",
    )
    solver["assignment_eligibility"] = np.where(
        solver["o_node_id"].eq(solver["d_node_id"]),
        "unassigned_same_access_node_or_intrazonal",
        "assignment_input",
    )
    assignment_dir = TASK_ROOT / "staging" / "assignment" / "baseline"
    assignment_dir.mkdir(parents=True, exist_ok=True)
    assignment_links = links.copy()
    assignment_links.to_csv(assignment_dir / "link.csv", index=False)
    solver_demand = (
        solver[solver["assignment_eligibility"].eq("assignment_input")]
        .groupby(["o_node_id", "d_node_id"], as_index=False)["vehicle_trips"]
        .sum()
        .rename(columns={"o_node_id": "o_zone_id", "d_node_id": "d_zone_id", "vehicle_trips": "volume"})
    )
    solver_demand.to_csv(assignment_dir / "demand.csv", index=False)
    solver_out = demand_dir / "assignment_od_crosswalk.csv"
    solver.to_csv(solver_out, index=False)

    source_node, _, source_demand = source_tables(config)
    boundary_lookup = {}
    core_wgs, analysis_wgs, _, _ = boundary_geometries(config)
    for row in source_node[source_node["zone_id"].astype(str).str.len().gt(0)].itertuples(index=False):
        boundary_lookup[str(row.zone_id)] = classify_against_boundaries(
            Point(float(row.x_coord), float(row.y_coord)), core_wgs, analysis_wgs
        )
    scope_rows = []
    for row in source_demand.itertuples(index=False):
        o_status = boundary_lookup.get(str(row.o_zone_id), "unknown")
        d_status = boundary_lookup.get(str(row.d_zone_id), "unknown")
        o_core = o_status.startswith("core_")
        d_core = d_status.startswith("core_")
        if o_core and d_core:
            trip_class = "internal_core"
        elif not o_core and d_core:
            trip_class = "entering_core"
        elif o_core and not d_core:
            trip_class = "leaving_core"
        else:
            trip_class = "external_or_through_unknown_path"
        scope_rows.append(
            {
                "o_source_taz_id": str(row.o_zone_id),
                "d_source_taz_id": str(row.d_zone_id),
                "source_volume": float(row.volume),
                "origin_boundary_status": o_status,
                "destination_boundary_status": d_status,
                "endpoint_trip_class": trip_class,
                "source_id": "gmns_plus_demand",
                "status": "preserved_source_demand_not_used_in_h3_engineering_scenario",
            }
        )
    source_scope_out = demand_dir / "source_demand_scope.csv"
    pd.DataFrame(scope_rows).to_csv(source_scope_out, index=False)

    summary = {
        "built_at_utc": utc_now(),
        "scenario_id": config["demand_scenario"]["scenario_id"],
        "status": config["demand_scenario"]["status"],
        "fine_zones": len(zone_ids),
        "daily_productions": float(productions.sum()),
        "daily_attractions": float(attractions.sum()),
        "distributed_person_trips": float(matrix.sum()),
        "gravity_balance_iterations": balance_iterations,
        "gravity_relative_max_margin_error": balance_error,
        "reachable_od_cells": int(np.isfinite(skims).sum()),
        "unreachable_od_cells": int((~np.isfinite(skims)).sum()),
        "mode_share_sum": sum(mode_shares.values()),
        "am_peak_all_mode_person_trips": float(mode_period["person_trips"].sum()),
        "am_peak_drive_person_trips": float(drive["person_trips"].sum()),
        "am_peak_drive_vehicle_trips": float(drive["vehicle_trips"].sum()),
        "assignment_input_vehicle_trips": float(solver_demand["volume"].sum()),
        "unassigned_same_access_or_intrazonal_vehicle_trips": float(
            solver.loc[solver["assignment_eligibility"].ne("assignment_input"), "vehicle_trips"].sum()
        ),
        "four_stage_scope": "single-pass prototype using free-flow skim; drive mode only is assignment-ready",
    }
    summary_out = TASK_ROOT / "reports" / "demand_summary.json"
    write_json(summary_out, summary)
    outputs = [
        skim_out,
        pa_out,
        od_out,
        mode_share_out,
        mode_period_out,
        vehicle_out,
        solver_out,
        assignment_dir / "link.csv",
        assignment_dir / "demand.csv",
        source_scope_out,
        summary_out,
    ]
    record_stage(
        "build_demand",
        started,
        len(activity) + len(access) + len(links),
        sum(len(pd.read_csv(path)) for path in [pa_out, od_out, mode_share_out, mode_period_out, vehicle_out]),
        sum(path.stat().st_size for path in [TASK_ROOT / "database" / "activity" / "zone_activity.csv", TASK_ROOT / "database" / "zones" / "zone_access.csv", TASK_ROOT / "database" / "network" / "matcher" / "link.csv"]),
        outputs,
        notes="Four explicit stages prepared through drive assignment input; all assumptions remain scenario-labeled.",
    )
    append_tool_usage(
        "Trip generation/distribution/mode split",
        "MCL thin orchestration; networkx 3.3",
        "tools/city_database.py build-demand",
        "database/activity; database/zones; database/network/matcher",
        "database/demand; staging/assignment/baseline",
        "completed_engineering_scenario",
        "Doubly constrained gravity with free-flow skim and given mode shares; not calibrated.",
    )
    return summary


def _parse_fw_log(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"log_path": str(path.relative_to(TASK_ROOT))}
    if not path.exists():
        return result
    text = path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("* Iterations:"):
            result["iterations"] = int(stripped.split(":", 1)[1])
        elif stripped.startswith("* Total Objective:"):
            result["objective"] = float(stripped.split(":", 1)[1].replace(",", ""))
        elif stripped.startswith("* Relative Gap:"):
            result["relative_gap_percent"] = float(stripped.split(":", 1)[1].replace("%", ""))
        elif stripped.startswith("* Computational Time:"):
            result["solver_reported_seconds"] = float(stripped.split(":", 1)[1].replace("s", ""))
        elif "Converged (Gap < 0.01%)" in stripped:
            result["converged"] = True
    result.setdefault("converged", False)
    return result


def run_assignment(config: dict[str, Any]) -> dict[str, Any]:
    started = time.time()
    input_dir = TASK_ROOT / "staging" / "assignment" / "baseline"
    output_root = TASK_ROOT / "outputs" / "assignment"
    solver_path = TASK_ROOT.parents[1] / "github_upload" / "algorithms" / "static_fw" / "tap_frank_wolfe.py"
    if not solver_path.exists():
        raise FileNotFoundError(solver_path)
    max_iter = int(config["assignment"]["max_iterations"])
    timeout = int(config["assignment"]["wall_clock_limit_seconds"])
    runs = [
        ("boston_baseline", 1.0, "baseline source VDF capacity"),
        ("boston_capacity_stress", 1.2, "stress scenario: effective VDF capacity divided by 1.2"),
    ]
    run_results = []
    output_paths: list[Path] = []
    for run_name, cap_scale, interpretation in runs:
        run_dir = output_root / run_name
        run_dir.mkdir(parents=True, exist_ok=True)
        code = (
            "import importlib.util; "
            f"p=r'{solver_path}'; "
            "s=importlib.util.spec_from_file_location('mcl_static_fw',p); "
            "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
            f"m.solve_fw_refined(r'{input_dir}',run_name='{run_name}',max_iter={max_iter},cap_scale={cap_scale})"
        )
        run_started = time.time()
        status = "completed"
        stop_reason = "solver_returned"
        try:
            completed = subprocess.run(
                [sys.executable, "-c", code],
                cwd=run_dir,
                text=True,
                capture_output=True,
                timeout=timeout,
                env={
                    **os.environ,
                    "OMP_NUM_THREADS": "2",
                    "OPENBLAS_NUM_THREADS": "2",
                    "MKL_NUM_THREADS": "2",
                },
            )
            if completed.returncode != 0:
                status = "failed"
                stop_reason = f"return_code_{completed.returncode}"
        except subprocess.TimeoutExpired:
            completed = None
            status = "timed_out"
            stop_reason = f"wall_clock_limit_{timeout}s"
        stdout_path = run_dir / "wrapper_stdout.txt"
        stderr_path = run_dir / "wrapper_stderr.txt"
        stdout_path.write_text(completed.stdout if completed else "", encoding="utf-8")
        stderr_path.write_text(completed.stderr if completed else "", encoding="utf-8")
        log_path = run_dir / f"{run_name}_fw_log.txt"
        solution_path = run_dir / f"{run_name}_solution.csv"
        parsed = _parse_fw_log(log_path)
        parsed.update(
            {
                "run_name": run_name,
                "status": status,
                "stop_reason": "relative_gap_tolerance" if parsed.get("converged") else stop_reason,
                "cap_scale": cap_scale,
                "capacity_interpretation": interpretation,
                "model": config["assignment"]["model"],
                "wall_seconds_wrapper": time.time() - run_started,
                "solution_exists": solution_path.exists(),
            }
        )
        if solution_path.exists():
            solution = pd.read_csv(solution_path)
            parsed.update(
                {
                    "links": len(solution),
                    "total_link_volume_sum_not_trip_total": float(solution["volume"].sum()),
                    "links_with_positive_volume": int((solution["volume"] > 0).sum()),
                    "max_vc_ratio": float(solution["vc_ratio"].max()),
                }
            )
        run_results.append(parsed)
        output_paths.extend([stdout_path, stderr_path, log_path, solution_path])

    demand_summary = json.loads((TASK_ROOT / "reports" / "demand_summary.json").read_text(encoding="utf-8"))
    accounting_rows = [
        {
            "stage": "trip_generation_daily",
            "mode": "all",
            "period": "daily",
            "amount": demand_summary["daily_productions"],
            "unit": "person_trips",
            "status": "engineering_scenario",
        },
        {
            "stage": "mode_period_split",
            "mode": "all",
            "period": config["time"]["analysis_period_id"],
            "amount": demand_summary["am_peak_all_mode_person_trips"],
            "unit": "person_trips",
            "status": "given_period_share",
        },
        {
            "stage": "vehicle_conversion",
            "mode": "drive",
            "period": config["time"]["analysis_period_id"],
            "amount": demand_summary["am_peak_drive_vehicle_trips"],
            "unit": "vehicle_trips",
            "status": "given_occupancy",
        },
        {
            "stage": "assignment_input",
            "mode": "drive",
            "period": config["time"]["analysis_period_id"],
            "amount": demand_summary["assignment_input_vehicle_trips"],
            "unit": "vehicle_trips",
            "status": "assigned_network_input",
        },
        {
            "stage": "assignment_unassigned",
            "mode": "drive",
            "period": config["time"]["analysis_period_id"],
            "amount": demand_summary["unassigned_same_access_or_intrazonal_vehicle_trips"],
            "unit": "vehicle_trips",
            "status": "same_access_node_or_intrazonal_not_loaded",
        },
    ]
    accounting_out = output_root / "assignment_accounting.csv"
    pd.DataFrame(accounting_rows).to_csv(accounting_out, index=False)
    output_paths.append(accounting_out)
    scenario_out = TASK_ROOT / "database" / "scenarios" / "capacity_stress_v1.json"
    write_json(
        scenario_out,
        {
            "scenario_id": "capacity_stress_v1",
            "baseline": "boston_baseline",
            "changed_parameter_only": {"effective_capacity_divisor": {"from": 1.0, "to": 1.2}},
            "unchanged": ["network topology", "source VDF fields", "demand", "BPR alpha", "BPR beta"],
            "interpretation": "Engineering stress test only; source capacity CSV is not overwritten and result is not a future prediction.",
            "execution_status": next(x["status"] for x in run_results if x["run_name"] == "boston_capacity_stress"),
        },
    )
    output_paths.append(scenario_out)
    summary_out = TASK_ROOT / "reports" / "assignment_summary.json"
    summary = {
        "run_at_utc": utc_now(),
        "solver_entry": "solve_fw_refined(data_dir, run_name, max_iter, cap_scale)",
        "model": config["assignment"]["model"],
        "runs": run_results,
        "demand_accounting": accounting_rows,
        "single_pass_prototype": True,
    }
    write_json(summary_out, summary)
    output_paths.append(summary_out)
    record_stage(
        "run_assignment",
        started,
        len(pd.read_csv(input_dir / "link.csv")) + len(pd.read_csv(input_dir / "demand.csv")),
        sum(item.get("links", 0) for item in run_results),
        (input_dir / "link.csv").stat().st_size + (input_dir / "demand.csv").stat().st_size,
        output_paths,
        status="completed" if all(x["status"] == "completed" for x in run_results) else "completed_with_solver_issue",
        notes="One baseline and one single-parameter capacity stress scenario; source network files unchanged.",
    )
    append_tool_usage(
        "Static trip assignment",
        "MCL existing static FW core",
        "solve_fw_refined(data_dir, run_name, max_iter, cap_scale)",
        "staging/assignment/baseline/link.csv; staging/assignment/baseline/demand.csv",
        "outputs/assignment",
        "completed" if all(x["status"] == "completed" for x in run_results) else "completed_with_solver_issue",
        "Existing numerical core imported directly; module __main__ was not executed.",
    )
    return summary


def _gtfs_time_seconds(value: str) -> int | None:
    try:
        hour, minute, second = (int(part) for part in str(value).split(":"))
        if minute < 0 or minute >= 60 or second < 0 or second >= 60 or hour < 0:
            return None
        return hour * 3600 + minute * 60 + second
    except Exception:
        return None


def build_transit(config: dict[str, Any]) -> dict[str, Any]:
    started = time.time()
    gtfs_config = config["gtfs"]
    zip_path = resolve_task_path(gtfs_config["local_zip"])
    if not zip_path.exists():
        raise FileNotFoundError(zip_path)
    actual_sha = sha256_file(zip_path)
    if actual_sha.lower() != str(gtfs_config["content_sha256"]).lower():
        raise ValueError(f"GTFS SHA mismatch: {actual_sha}")
    transit_dir = TASK_ROOT / "database" / "transit"
    transit_dir.mkdir(parents=True, exist_ok=True)
    service_date = str(config["time"]["scenario_service_date"]).replace("-", "")
    service_datetime = datetime.strptime(service_date, "%Y%m%d")
    weekday = service_datetime.strftime("%A").lower()
    with zipfile.ZipFile(zip_path) as archive:
        unsafe = [
            info.filename
            for info in archive.infolist()
            if info.filename.startswith(("/", "\\")) or ".." in Path(info.filename).parts
        ]
        if unsafe:
            raise ValueError(f"Unsafe ZIP members: {unsafe}")
        members = {info.filename for info in archive.infolist()}
        required = {
            "agency.txt",
            "calendar.txt",
            "calendar_dates.txt",
            "feed_info.txt",
            "routes.txt",
            "shapes.txt",
            "stop_times.txt",
            "stops.txt",
            "transfers.txt",
            "trips.txt",
        }
        missing = sorted(required - members)
        if missing:
            raise ValueError(f"Missing required GTFS members: {missing}")

        read = lambda name: pd.read_csv(archive.open(name), dtype="string", keep_default_na=False)
        agency = read("agency.txt")
        feed_info = read("feed_info.txt")
        calendar = read("calendar.txt")
        calendar_dates = read("calendar_dates.txt")
        routes = read("routes.txt")
        stops = read("stops.txt")
        trips = read("trips.txt")
        transfers = read("transfers.txt")

        date_num = int(service_date)
        regular = calendar[
            (pd.to_numeric(calendar["start_date"], errors="coerce") <= date_num)
            & (pd.to_numeric(calendar["end_date"], errors="coerce") >= date_num)
            & calendar[weekday].eq("1")
        ]
        active_services = set(regular["service_id"].astype(str))
        date_exceptions = calendar_dates[calendar_dates["date"].eq(service_date)]
        active_services |= set(
            date_exceptions.loc[date_exceptions["exception_type"].eq("1"), "service_id"].astype(str)
        )
        active_services -= set(
            date_exceptions.loc[date_exceptions["exception_type"].eq("2"), "service_id"].astype(str)
        )
        active_trips = trips[trips["service_id"].isin(active_services)].copy()
        active_trip_ids = set(active_trips["trip_id"].astype(str))

        _, analysis_wgs, _, _ = boundary_geometries(config)
        stop_points = []
        for lon, lat in zip(stops["stop_lon"], stops["stop_lat"]):
            try:
                stop_points.append(Point(float(lon), float(lat)))
            except (TypeError, ValueError):
                stop_points.append(None)
        stops["study_area_status"] = [
            "missing_coordinate"
            if point is None
            else ("inside_analysis" if analysis_wgs.covers(point) else "outside_analysis")
            for point in stop_points
        ]
        analysis_stop_ids = set(
            stops.loc[stops["study_area_status"].eq("inside_analysis"), "stop_id"].astype(str)
        )

        selected_trip_ids: set[str] = set()
        first_pass_rows = 0
        for chunk in pd.read_csv(
            archive.open("stop_times.txt"),
            dtype="string",
            keep_default_na=False,
            chunksize=200_000,
        ):
            first_pass_rows += len(chunk)
            mask = chunk["trip_id"].isin(active_trip_ids) & chunk["stop_id"].isin(analysis_stop_ids)
            selected_trip_ids |= set(chunk.loc[mask, "trip_id"].astype(str))

        selected_trips = active_trips[active_trips["trip_id"].isin(selected_trip_ids)].copy()
        selected_trip_ids = set(selected_trips["trip_id"].astype(str))
        selected_route_ids = set(selected_trips["route_id"].astype(str))
        selected_routes = routes[routes["route_id"].isin(selected_route_ids)].copy()
        selected_shape_ids = set(
            selected_trips.loc[selected_trips["shape_id"].astype(str).str.len().gt(0), "shape_id"].astype(str)
        )
        selected_service_ids = set(selected_trips["service_id"].astype(str))

        stop_times_out = transit_dir / "stop_times.txt"
        stop_times_out.unlink(missing_ok=True)
        referenced_stop_ids: set[str] = set()
        second_pass_rows = 0
        selected_stop_time_rows = 0
        stop_route_types: defaultdict[str, set[str]] = defaultdict(set)
        trip_to_route = dict(zip(selected_trips["trip_id"].astype(str), selected_trips["route_id"].astype(str)))
        route_to_type = dict(zip(routes["route_id"].astype(str), routes["route_type"].astype(str)))
        wrote_header = False
        over_24_hour_times = 0
        invalid_time_values = 0
        for chunk in pd.read_csv(
            archive.open("stop_times.txt"),
            dtype="string",
            keep_default_na=False,
            chunksize=200_000,
        ):
            second_pass_rows += len(chunk)
            selected_chunk = chunk[chunk["trip_id"].isin(selected_trip_ids)].copy()
            if selected_chunk.empty:
                continue
            selected_stop_time_rows += len(selected_chunk)
            referenced_stop_ids |= set(selected_chunk["stop_id"].astype(str))
            for value in pd.concat([selected_chunk["arrival_time"], selected_chunk["departure_time"]]):
                seconds = _gtfs_time_seconds(str(value))
                if seconds is None:
                    invalid_time_values += 1
                elif seconds >= 24 * 3600:
                    over_24_hour_times += 1
            for trip_id, stop_id in zip(selected_chunk["trip_id"], selected_chunk["stop_id"]):
                route_id = trip_to_route.get(str(trip_id), "")
                route_type = route_to_type.get(route_id, "")
                if route_type:
                    stop_route_types[str(stop_id)].add(route_type)
            selected_chunk.to_csv(stop_times_out, mode="a", index=False, header=not wrote_header)
            wrote_header = True

        selected_stops = stops[stops["stop_id"].isin(referenced_stop_ids)].copy()
        selected_transfers = transfers[
            transfers["from_stop_id"].isin(referenced_stop_ids)
            & transfers["to_stop_id"].isin(referenced_stop_ids)
        ].copy()
        selected_calendar = calendar[calendar["service_id"].isin(selected_service_ids)].copy()
        selected_calendar_dates = calendar_dates[
            calendar_dates["service_id"].isin(selected_service_ids)
        ].copy()
        selected_agency_ids = set(selected_routes["agency_id"].astype(str))
        selected_agency = agency[agency["agency_id"].isin(selected_agency_ids)].copy()
        shapes = read("shapes.txt")
        selected_shapes = shapes[shapes["shape_id"].isin(selected_shape_ids)].copy()

    outputs_by_name = {
        "agency.txt": selected_agency,
        "calendar.txt": selected_calendar,
        "calendar_dates.txt": selected_calendar_dates,
        "feed_info.txt": feed_info,
        "routes.txt": selected_routes,
        "shapes.txt": selected_shapes,
        "stops.txt": selected_stops,
        "transfers.txt": selected_transfers,
        "trips.txt": selected_trips,
    }
    output_paths = [stop_times_out]
    for name, frame in outputs_by_name.items():
        path = transit_dir / name
        frame.to_csv(path, index=False)
        output_paths.append(path)

    matcher_nodes = pd.read_csv(
        TASK_ROOT / "database" / "network" / "matcher" / "node.csv",
        dtype={"node_id": "string"},
        keep_default_na=False,
    )
    forward, _ = transformers(config)
    node_xy = np.array(
        [forward.transform(float(x), float(y)) for x, y in zip(matcher_nodes["x_coord"], matcher_nodes["y_coord"])]
    )
    from scipy.spatial import cKDTree

    tree = cKDTree(node_xy)
    core_wgs, analysis_wgs, _, _ = boundary_geometries(config)
    access_rows = []
    for row in selected_stops.itertuples(index=False):
        route_types = sorted(stop_route_types.get(str(row.stop_id), set()))
        try:
            point = Point(float(row.stop_lon), float(row.stop_lat))
        except (TypeError, ValueError):
            point = None
        core_status = (
            classify_against_boundaries(point, core_wgs, analysis_wgs)
            if point is not None
            else "missing_coordinate"
        )
        if point is not None and analysis_wgs.covers(point):
            x, y = forward.transform(point.x, point.y)
            distance, index = tree.query([x, y], k=1)
            node_id = str(matcher_nodes.iloc[int(index)]["node_id"])
            has_road_service = any(
                route_type == "3" or (route_type.isdigit() and 700 <= int(route_type) < 800)
                for route_type in route_types
            )
            method = (
                "nearest_physical_node_model_walk_access_bus_stop"
                if has_road_service
                else "nearest_physical_node_model_walk_access_nonroad_mode"
            )
            status = "access_candidate_not_field_verified"
        elif point is not None:
            distance, node_id, method, status = "", "", "not_mapped_outside_analysis", "outside_analysis"
        else:
            distance, node_id, method, status = "", "", "not_mapped_missing_coordinate", "missing_coordinate"
        access_rows.append(
            {
                "stop_id": str(row.stop_id),
                "stop_name": str(row.stop_name),
                "stop_lon": float(row.stop_lon) if point is not None else "",
                "stop_lat": float(row.stop_lat) if point is not None else "",
                "gtfs_route_types": ";".join(route_types),
                "boundary_status": core_status,
                "access_node_id": node_id,
                "access_distance_m": distance,
                "access_method": method,
                "shape_to_road_relation": "separate_table_not_implied_by_stop_access",
                "network_id": config["network"]["network_id"],
                "network_version": config["network"]["network_version"],
                "feed_id": gtfs_config["feed_id"],
                "service_date": config["time"]["scenario_service_date"],
                "status": status,
            }
        )
    access_out = transit_dir / "stop_network_access.csv"
    pd.DataFrame(access_rows).to_csv(access_out, index=False)
    output_paths.append(access_out)

    # Exercise the installed MapMatching4GMNS geometric engine on one actual
    # planned bus shape.  This is plan-to-road conflation, not GPS evidence.
    conflation_rows: list[dict[str, Any]] = []
    conflation_status = "not_run_no_selected_bus_route"
    bus_routes = selected_routes[selected_routes["route_type"].eq("3")]
    if not bus_routes.empty:
        trip_counts = selected_trips[selected_trips["route_id"].isin(bus_routes["route_id"])]["route_id"].value_counts()
        route_id = str(trip_counts.index[0]) if not trip_counts.empty else str(bus_routes.iloc[0]["route_id"])
        try:
            import mapmatching4gmns as mm
            from mapmatching4gmns.adapters.gtfs import to_evidence

            evidence = to_evidence(str(transit_dir), route_id=route_id, corridor_id=f"gtfs:{route_id}", stride=5)
            matched = mm.match(
                evidence,
                network_dir=str(TASK_ROOT / "database" / "network" / "matcher"),
                gp_types=("1", "2", "3", "4", "5"),
                engine="geometric",
            )
            for order, link_id in enumerate(matched.matched_link_sequence, start=1):
                conflation_rows.append(
                    {
                        "feed_id": gtfs_config["feed_id"],
                        "route_id": route_id,
                        "planned_shape_corridor_id": matched.trajectory_id,
                        "path_order": order,
                        "matched_link_id": str(link_id),
                        "engine": matched.source_engine,
                        "engine_version": "mapmatching4gmns 0.3.0",
                        "geometry_error_m": matched.geometry_error,
                        "confidence_score": matched.confidence_score,
                        "relationship": "planned_gtfs_shape_to_physical_road_conflation",
                        "observation_status": "planned_not_observed",
                        "network_id": config["network"]["network_id"],
                        "network_version": config["network"]["network_version"],
                    }
                )
            conflation_status = "completed" if conflation_rows else "engine_returned_empty"
        except Exception as exc:
            conflation_status = f"failed:{type(exc).__name__}:{exc}"
    conflation_out = transit_dir / "shape_network_conflation.csv"
    pd.DataFrame(
        conflation_rows,
        columns=[
            "feed_id", "route_id", "planned_shape_corridor_id", "path_order", "matched_link_id",
            "engine", "engine_version", "geometry_error_m", "confidence_score", "relationship",
            "observation_status", "network_id", "network_version",
        ],
    ).to_csv(conflation_out, index=False)
    output_paths.append(conflation_out)

    selected_stop_times = pd.read_csv(stop_times_out, dtype="string", keep_default_na=False)
    validations = {
        "built_at_utc": utc_now(),
        "feed_id": gtfs_config["feed_id"],
        "source_zip_sha256": actual_sha,
        "source_zip_bytes": zip_path.stat().st_size,
        "service_date": config["time"]["scenario_service_date"],
        "agency_timezones": sorted(selected_agency["agency_timezone"].unique().tolist()),
        "active_service_ids": len(active_services),
        "selected_service_ids": len(selected_service_ids),
        "selected_trips": len(selected_trips),
        "selected_routes": len(selected_routes),
        "selected_shapes_points": len(selected_shapes),
        "selected_stops_all_referenced": len(selected_stops),
        "selected_stops_inside_analysis": int(selected_stops["study_area_status"].eq("inside_analysis").sum()),
        "selected_stop_times": len(selected_stop_times),
        "source_stop_times_rows_first_pass": first_pass_rows,
        "source_stop_times_rows_second_pass": second_pass_rows,
        "stop_times_trip_fk_missing": int((~selected_stop_times["trip_id"].isin(selected_trip_ids)).sum()),
        "stop_times_stop_fk_missing": int((~selected_stop_times["stop_id"].isin(referenced_stop_ids)).sum()),
        "trip_route_fk_missing": int((~selected_trips["route_id"].isin(selected_route_ids)).sum()),
        "trip_service_fk_missing": int((~selected_trips["service_id"].isin(selected_service_ids)).sum()),
        "trip_shape_fk_missing": int((~selected_trips.loc[selected_trips["shape_id"].str.len().gt(0), "shape_id"].isin(selected_shape_ids)).sum()),
        "over_24_hour_arrival_or_departure_values": over_24_hour_times,
        "invalid_arrival_or_departure_values": invalid_time_values,
        "planned_shape_conflation_status": conflation_status,
        "semantics": "GTFS shapes are planned service geometry, not vehicle GPS observations; transit person demand is not assigned in this version.",
        "redistribution_status": gtfs_config["redistribution_status"],
    }
    validation_out = TASK_ROOT / "reports" / "transit_validation.json"
    write_json(validation_out, validations)
    output_paths.append(validation_out)
    record_stage(
        "build_transit",
        started,
        first_pass_rows,
        len(selected_stop_times) + len(selected_trips) + len(selected_stops) + len(selected_shapes),
        zip_path.stat().st_size,
        output_paths,
        notes="stop_times streamed twice; selected trips touch analysis stops and retain all referenced stops/times/shapes.",
    )
    append_tool_usage(
        "MBTA GTFS study-area slice",
        str(gtfs_config["feed_version"]),
        "tools/city_database.py build-transit",
        str(gtfs_config["local_zip"]),
        "database/transit; reports/transit_validation.json",
        "completed",
        "One current snapshot; raw ZIP redistribution remains unclear and is excluded from public package.",
    )
    append_tool_usage(
        "GTFS planned shape to road conflation",
        "mapmatching4gmns 0.3.0",
        "mapmatching4gmns.adapters.gtfs.to_evidence; mapmatching4gmns.match(engine='geometric')",
        "database/transit GTFS slice; database/network/matcher",
        "database/transit/shape_network_conflation.csv",
        conflation_status,
        "Planned shape conflation is separate from stop access and is not GPS observation.",
    )
    return validations


def fetch_mbta_gps(config: dict[str, Any]) -> dict[str, Any]:
    """Capture a short, sequential series of official MBTA bus positions."""
    started = time.time()
    gps_config = config["gps"]
    raw_dir = TASK_ROOT / "raw" / "gps"
    raw_dir.mkdir(parents=True, exist_ok=True)
    count = int(gps_config["snapshot_count"])
    interval = int(gps_config["snapshot_interval_seconds"])
    max_bytes = int(gps_config["snapshot_max_bytes"])
    retries = int(gps_config["request_retries"])
    endpoint = str(gps_config["source_url"])
    records = []
    for index in range(count):
        path = raw_dir / f"mbta_vehicles_snapshot_{index:03d}.json"
        if path.exists() and path.stat().st_size > 0:
            payload = path.read_bytes()
            json.loads(payload)
            records.append(
                {
                    "snapshot_index": index,
                    "request_time_utc": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
                    "status": "reused_existing_valid_json",
                    "http_status": "",
                    "bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "path": str(path.relative_to(TASK_ROOT)),
                }
            )
        else:
            last_error = None
            for attempt in range(retries + 1):
                request_time = utc_now()
                try:
                    request = urllib.request.Request(
                        endpoint,
                        headers={"User-Agent": "MobilityComputationLab-Boston/1.0 (research; contact via repository)"},
                    )
                    with urllib.request.urlopen(request, timeout=60) as response:
                        content_length = response.headers.get("Content-Length")
                        if content_length and int(content_length) > max_bytes:
                            raise ValueError(f"Snapshot Content-Length exceeds cap: {content_length}")
                        payload = response.read(max_bytes + 1)
                        if len(payload) > max_bytes:
                            raise ValueError("Snapshot exceeded configured byte cap")
                        status_code = int(response.status)
                    json.loads(payload)
                    path.write_bytes(payload)
                    records.append(
                        {
                            "snapshot_index": index,
                            "request_time_utc": request_time,
                            "status": "downloaded",
                            "http_status": status_code,
                            "bytes": len(payload),
                            "sha256": hashlib.sha256(payload).hexdigest(),
                            "path": str(path.relative_to(TASK_ROOT)),
                        }
                    )
                    last_error = None
                    break
                except Exception as exc:
                    last_error = f"{type(exc).__name__}: {exc}"
                    if attempt < retries:
                        time.sleep(min(2 ** attempt, 4))
            if last_error is not None:
                records.append(
                    {
                        "snapshot_index": index,
                        "request_time_utc": utc_now(),
                        "status": "failed",
                        "http_status": "",
                        "bytes": 0,
                        "sha256": "",
                        "path": str(path.relative_to(TASK_ROOT)),
                        "error": last_error,
                    }
                )
                break
        if index < count - 1:
            time.sleep(interval)
    manifest_out = raw_dir / "mbta_vehicle_acquisition.json"
    write_json(
        manifest_out,
        {
            "source": "MBTA V3 API /vehicles filtered to route_type=3",
            "endpoint": endpoint,
            "mode": "bus",
            "captured_at_utc": utc_now(),
            "requested_snapshots": count,
            "interval_seconds": interval,
            "records": records,
            "privacy": "Public transit vehicle identifiers are retained locally; no person/user identity is collected.",
            "semantic_limit": "Vehicle positions are not passenger OD and do not measure passenger volume.",
        },
    )
    output_paths = [resolve_task_path(row["path"]) for row in records if row["status"] != "failed"] + [manifest_out]
    record_stage(
        "fetch_mbta_gps",
        started,
        0,
        len(records),
        0,
        output_paths,
        status="completed" if len(records) == count and all(r["status"] != "failed" for r in records) else "partial",
        notes="Sequential snapshots; no API key; bus vehicles only; no passenger OD semantics.",
    )
    append_tool_usage(
        "Mode-known Boston GPS acquisition",
        "MBTA V3 API snapshot series",
        "tools/city_database.py fetch-mbta-gps",
        endpoint,
        "raw/gps/mbta_vehicles_snapshot_*.json",
        "completed" if len(records) == count and all(r["status"] != "failed" for r in records) else "partial",
        "Public bus vehicle positions; raw JSON excluded from public package.",
    )
    return {
        "requested": count,
        "records": len(records),
        "successful": sum(row["status"] != "failed" for row in records),
        "bytes": sum(int(row["bytes"]) for row in records),
        "wall_seconds": time.time() - started,
    }


def _safe_relation_id(entity: dict[str, Any], name: str) -> str:
    data = entity.get("relationships", {}).get(name, {}).get("data")
    return str(data.get("id", "")) if isinstance(data, dict) else ""


def _monotone_project_points(
    points: list[Point], path_geometries: list[LineString]
) -> list[tuple[int, Point, float, float]]:
    """Minimum-distance monotone point-to-path-occurrence alignment."""
    if not points or not path_geometries:
        return []
    costs = np.array([[point.distance(line) for line in path_geometries] for point in points])
    n_points, n_links = costs.shape
    dp = np.full((n_points, n_links), np.inf)
    parent = np.full((n_points, n_links), -1, dtype=int)
    dp[0, :] = costs[0, :]
    for i in range(1, n_points):
        best_value = np.inf
        best_index = -1
        for j in range(n_links):
            if dp[i - 1, j] < best_value:
                best_value = dp[i - 1, j]
                best_index = j
            dp[i, j] = best_value + costs[i, j]
            parent[i, j] = best_index
    link_index = int(np.argmin(dp[-1]))
    indices = [link_index]
    for i in range(n_points - 1, 0, -1):
        link_index = int(parent[i, link_index])
        indices.append(link_index)
    indices.reverse()
    result = []
    for point, occurrence in zip(points, indices):
        line = path_geometries[occurrence]
        offset = float(line.project(point))
        projected = line.interpolate(offset)
        fraction = offset / line.length if line.length > 0 else 0.0
        result.append((occurrence, projected, offset, fraction))
    return result


def _metric_errors(observed: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    residual = observed - predicted
    return {
        "mae_min": float(np.mean(np.abs(residual))),
        "rmse_min": float(np.sqrt(np.mean(residual ** 2))),
        "mean_error_min": float(np.mean(residual)),
    }


def process_match_calibrate_gps(config: dict[str, Any]) -> dict[str, Any]:
    started = time.time()
    import mapmatching4gmns as mm
    from mapmatching4gmns.adapters.gps import trace_to_evidence

    raw_dir = TASK_ROOT / "raw" / "gps"
    snapshot_paths = sorted(raw_dir.glob("mbta_vehicles_snapshot_*.json"))
    if not snapshot_paths:
        raise FileNotFoundError("No MBTA vehicle snapshots; run fetch-mbta-gps")
    core_wgs, analysis_wgs, _, _ = boundary_geometries(config)
    forward, reverse = transformers(config)
    fine_res = int(config["zones"]["fine_resolution"])
    network_id = config["network"]["network_id"]
    network_version = config["network"]["network_version"]
    raw_total = 0
    raw_rows: list[dict[str, Any]] = []
    for snapshot_index, path in enumerate(snapshot_paths):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for entity in payload.get("data", []):
            raw_total += 1
            attrs = entity.get("attributes", {})
            lon, lat = attrs.get("longitude"), attrs.get("latitude")
            if lon is None or lat is None:
                continue
            point = Point(float(lon), float(lat))
            if not analysis_wgs.covers(point):
                continue
            vehicle_id = str(entity.get("id", ""))
            vehicle_observation_id = "mbtav:" + hashlib.sha256(vehicle_id.encode("utf-8")).hexdigest()[:16]
            raw_rows.append(
                {
                    "snapshot_index": snapshot_index,
                    "vehicle_observation_id": vehicle_observation_id,
                    "route_id": _safe_relation_id(entity, "route"),
                    "trip_id": _safe_relation_id(entity, "trip"),
                    "stop_id": _safe_relation_id(entity, "stop"),
                    "longitude": float(lon),
                    "latitude": float(lat),
                    "timestamp": str(attrs.get("updated_at", "")),
                    "bearing_deg_north": attrs.get("bearing"),
                    "speed": attrs.get("speed"),
                    "current_status": attrs.get("current_status"),
                    "direction_id": attrs.get("direction_id"),
                    "mode": "bus",
                    "source_id": "mbta_v3_vehicle_positions",
                }
            )
    raw_frame = pd.DataFrame(raw_rows)
    if raw_frame.empty:
        raise RuntimeError("No MBTA bus positions fell inside the analysis boundary")
    raw_frame["timestamp_dt"] = pd.to_datetime(raw_frame["timestamp"], utc=True, errors="coerce")
    invalid_time = int(raw_frame["timestamp_dt"].isna().sum())
    raw_frame = raw_frame.dropna(subset=["timestamp_dt"]).copy()
    before_dedup = len(raw_frame)
    raw_frame = raw_frame.drop_duplicates(
        ["vehicle_observation_id", "timestamp", "longitude", "latitude"], keep="first"
    ).copy()
    duplicate_rows = before_dedup - len(raw_frame)
    raw_frame = raw_frame.sort_values(["vehicle_observation_id", "timestamp_dt"])

    gap_limit = float(config["gps"]["gap_seconds"])
    speed_limit = float(config["gps"]["max_speed_mps_flag"])
    clean_rows: list[dict[str, Any]] = []
    segment_summaries: list[dict[str, Any]] = []
    for vehicle_id, group in raw_frame.groupby("vehicle_observation_id", sort=True):
        group = group.sort_values("timestamp_dt").copy()
        segment_index = 0
        current: list[dict[str, Any]] = []
        previous: dict[str, Any] | None = None
        for row in group.to_dict("records"):
            split_reason = ""
            if previous is not None:
                dt_seconds = (row["timestamp_dt"] - previous["timestamp_dt"]).total_seconds()
                p0 = transform(forward.transform, Point(previous["longitude"], previous["latitude"]))
                p1 = transform(forward.transform, Point(row["longitude"], row["latitude"]))
                step_distance = p0.distance(p1)
                speed_mps = step_distance / dt_seconds if dt_seconds > 0 else math.inf
                if dt_seconds <= 0:
                    split_reason = "nonpositive_time_gap"
                elif dt_seconds > gap_limit:
                    split_reason = "long_time_gap"
                elif row["route_id"] != previous["route_id"]:
                    split_reason = "route_change"
                elif speed_mps > speed_limit:
                    split_reason = "implausible_speed"
            if split_reason and current:
                segment_index += 1
                _finish_gps_segment(current, vehicle_id, segment_index, segment_summaries, clean_rows, forward)
                current = []
            row["split_before_reason"] = split_reason
            current.append(row)
            previous = row
        if current:
            segment_index += 1
            _finish_gps_segment(current, vehicle_id, segment_index, segment_summaries, clean_rows, forward)

    segments = pd.DataFrame(segment_summaries)
    clean = pd.DataFrame(clean_rows)
    eligible = segments[
        (segments["point_count"] >= 4)
        & (segments["duration_seconds"] >= 30)
        & (segments["observed_displacement_m"] >= 30)
        & segments["route_id"].astype(str).str.len().gt(0)
    ].copy()
    eligible = eligible.sort_values(
        ["point_count", "observed_displacement_m", "duration_seconds"], ascending=False
    ).head(30)
    eligible_ids = set(eligible["segment_id"])
    segments["matching_selection"] = np.where(
        segments["segment_id"].isin(eligible_ids), "selected_first_pass", "not_selected_qc_or_cap"
    )

    matcher_dir = TASK_ROOT / "database" / "network" / "matcher"
    link_frame = pd.read_csv(
        matcher_dir / "link.csv",
        dtype={"link_id": "string", "from_node_id": "string", "to_node_id": "string"},
        keep_default_na=False,
    )
    link_lookup = link_frame.set_index("link_id", drop=False)
    point_match_rows: list[dict[str, Any]] = []
    path_rows: list[dict[str, Any]] = []
    observation_rows: list[dict[str, Any]] = []
    match_status_rows: list[dict[str, Any]] = []
    for segment in eligible.itertuples(index=False):
        trace = clean[clean["segment_id"].eq(segment.segment_id)].sort_values("point_seq").copy()
        trace_input = trace.rename(
            columns={"original_lon": "longitude", "original_lat": "latitude"}
        )[["longitude", "latitude", "timestamp", "bearing_deg_north", "speed"]]
        evidence = trace_to_evidence(trace_input, corridor_id=str(segment.segment_id))
        hmm_status = "not_attempted"
        hmm_error = ""
        selected_path = None
        selected_engine = ""
        hmm_options = {
            "search_radius": float(config["gps"]["matcher_search_radius_m"]),
            "max_gap_seconds": gap_limit,
            "min_link_len": 0.0,
            "use_heading": False,
            "noise_sigma": 20.0,
        }
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                selected_path = mm.match(
                    evidence,
                    network_dir=str(matcher_dir),
                    gp_types=("1", "2", "3", "4", "5"),
                    engine="mapmatcher4gmns",
                    mapmatcher_options=hmm_options,
                )
            if selected_path is None or not getattr(selected_path, "matched_link_sequence", None):
                raise RuntimeError("mapmatcher4gmns returned no matched link sequence")
            hmm_status = "success"
            selected_engine = "mapmatcher4gmns_external_hmm"
        except Exception as exc:
            hmm_status = "failed"
            hmm_error = f"{type(exc).__name__}: {exc}"[:500]
            try:
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    selected_path = mm.match(evidence, network_dir=str(matcher_dir), engine="native")
                if selected_path is None or not getattr(selected_path, "matched_link_sequence", None):
                    raise RuntimeError("native matcher returned no matched link sequence")
                selected_engine = "native_connected_path_after_recorded_hmm_failure"
            except Exception as native_exc:
                match_status_rows.append(
                    {
                        "segment_id": segment.segment_id,
                        "preferred_engine": "mapmatcher4gmns_external_hmm",
                        "hmm_status": hmm_status,
                        "hmm_error": hmm_error,
                        "selected_engine": "none",
                        "selected_status": "failed",
                        "selected_error": f"{type(native_exc).__name__}: {native_exc}"[:500],
                    }
                )
                continue
        link_sequence = [str(item) for item in selected_path.matched_link_sequence]
        unknown_links = [item for item in link_sequence if item not in link_lookup.index]
        continuity = all(
            str(link_lookup.loc[a, "to_node_id"]) == str(link_lookup.loc[b, "from_node_id"])
            for a, b in zip(link_sequence, link_sequence[1:])
        ) if link_sequence else False
        if unknown_links or not link_sequence or not continuity:
            match_status_rows.append(
                {
                    "segment_id": segment.segment_id,
                    "preferred_engine": "mapmatcher4gmns_external_hmm",
                    "hmm_status": hmm_status,
                    "hmm_error": hmm_error,
                    "selected_engine": selected_engine,
                    "selected_status": "failed_path_validation",
                    "selected_error": f"unknown_links={unknown_links};continuous={continuity}",
                }
            )
            continue
        metric_lines = [
            transform(forward.transform, wkt.loads(str(link_lookup.loc[link_id, "geometry"])))
            for link_id in link_sequence
        ]
        metric_points = [
            transform(forward.transform, Point(float(row.original_lon), float(row.original_lat)))
            for row in trace.itertuples(index=False)
        ]
        projections = _monotone_project_points(metric_points, metric_lines)
        occurrence_counts: Counter[int] = Counter(item[0] for item in projections)
        lateral_errors = []
        for trace_row, metric_point, projection in zip(trace.itertuples(index=False), metric_points, projections):
            occurrence, projected_metric, offset_m, fraction = projection
            projected_wgs = transform(reverse.transform, projected_metric)
            lateral_error = float(metric_point.distance(projected_metric))
            lateral_errors.append(lateral_error)
            point_match_rows.append(
                {
                    "trace_id": trace_row.trace_id,
                    "segment_id": trace_row.segment_id,
                    "vehicle_observation_id": trace_row.vehicle_observation_id,
                    "point_seq": trace_row.point_seq,
                    "original_lon": trace_row.original_lon,
                    "original_lat": trace_row.original_lat,
                    "timestamp": trace_row.timestamp,
                    "mode": "bus",
                    "network_id": network_id,
                    "network_version": network_version,
                    "matched_link_id": link_sequence[occurrence],
                    "path_occurrence": occurrence + 1,
                    "projected_lon": projected_wgs.x,
                    "projected_lat": projected_wgs.y,
                    "offset_m": offset_m,
                    "fraction": fraction,
                    "lateral_error_m": lateral_error,
                    "match_status": "matched_derived_monotone_projection" if lateral_error <= 200 else "matched_path_projection_outlier",
                    "engine": selected_engine,
                    "engine_version": "mapmatching4gmns 0.3.0",
                    "projection_method": "derived_point_projection_monotone_over_matched_occurrences",
                    "confidence": "",
                }
            )
        path_fftt = 0.0
        path_length = 0.0
        for occurrence, link_id in enumerate(link_sequence, start=1):
            link = link_lookup.loc[link_id]
            path_fftt += float(link["vdf_fftt"])
            path_length += float(link["length"])
            path_rows.append(
                {
                    "trace_id": segment.trace_id,
                    "segment_id": segment.segment_id,
                    "vehicle_observation_id": segment.vehicle_observation_id,
                    "path_order": occurrence,
                    "path_occurrence": occurrence,
                    "link_id": link_id,
                    "from_node_id": str(link["from_node_id"]),
                    "to_node_id": str(link["to_node_id"]),
                    "direction": "AB",
                    "point_projection_count": occurrence_counts[occurrence - 1],
                    "evidence_status": "projected_points_on_occurrence" if occurrence_counts[occurrence - 1] else "inferred_traversal",
                    "candidate_or_uncertain": hmm_status != "success",
                    "start_censored": True,
                    "end_censored": True,
                    "engine": selected_engine,
                    "network_id": network_id,
                    "network_version": network_version,
                }
            )
        duration_min = float(segment.duration_seconds) / 60.0
        observation_rows.append(
            {
                "observation_id": f"obs:{segment.segment_id}",
                "trace_id": segment.trace_id,
                "segment_id": segment.segment_id,
                "vehicle_observation_id": segment.vehicle_observation_id,
                "route_id": segment.route_id,
                "mode": "bus",
                "observed_duration_min": duration_min,
                "duration_source": "original_mbta_updated_at_timestamps",
                "baseline_path_fftt_min": path_fftt,
                "baseline_source": "sum_of_matched_source_vdf_fftt",
                "path_length_m": path_length,
                "matched_link_occurrences": len(link_sequence),
                "gps_point_count": int(segment.point_count),
                "mean_lateral_error_m": float(np.mean(lateral_errors)),
                "max_lateral_error_m": float(np.max(lateral_errors)),
                "engine": selected_engine,
                "hmm_status": hmm_status,
                "quality_status": "usable_end_to_end_vehicle_segment" if np.max(lateral_errors) <= 200 else "projection_error_over_200m",
                "sample_od_status": "capture_window_censored_vehicle_segment_not_passenger_od",
                "network_id": network_id,
                "network_version": network_version,
                "observation_date": str(trace.iloc[0]["timestamp"])[:10],
            }
        )
        match_status_rows.append(
            {
                "segment_id": segment.segment_id,
                "preferred_engine": "mapmatcher4gmns_external_hmm",
                "hmm_status": hmm_status,
                "hmm_error": hmm_error,
                "selected_engine": selected_engine,
                "selected_status": "success",
                "selected_error": "",
            }
        )

    observation = pd.DataFrame(observation_rows)
    match_status = pd.DataFrame(match_status_rows)
    matched_segment_ids = set(observation["segment_id"]) if not observation.empty else set()
    segments = segments.merge(match_status, on="segment_id", how="left")
    segments["match_status"] = np.where(
        segments["segment_id"].isin(matched_segment_ids), "matched", "unmatched_or_not_selected"
    )
    clean["match_selection_status"] = np.where(
        clean["segment_id"].isin(eligible_ids), "segment_selected", "segment_not_selected"
    )

    obs_dir = TASK_ROOT / "database" / "observations"
    obs_dir.mkdir(parents=True, exist_ok=True)
    clean_out = obs_dir / "gps_points_clean.csv"
    segments_out = obs_dir / "gps_segments.csv"
    point_match_out = obs_dir / "gps_point_match.csv"
    path_out = obs_dir / "gps_path_links.csv"
    observations_out = obs_dir / "gps_observations.csv"
    status_out = obs_dir / "gps_match_engine_status.csv"
    sample_od_out = obs_dir / "gps_sample_od.csv"
    link_use_out = obs_dir / "gps_link_use.csv"
    clean.drop(columns=["timestamp_dt"], errors="ignore").to_csv(clean_out, index=False)
    segments.to_csv(segments_out, index=False)
    pd.DataFrame(point_match_rows).to_csv(point_match_out, index=False)
    pd.DataFrame(path_rows).to_csv(path_out, index=False)
    observation.to_csv(observations_out, index=False)
    match_status.to_csv(status_out, index=False)

    sample_od_rows = []
    for segment_id in sorted(matched_segment_ids):
        trace = clean[clean["segment_id"].eq(segment_id)].sort_values("point_seq")
        first = trace.iloc[0]
        last = trace.iloc[-1]
        sample_od_rows.append(
            {
                "segment_id": segment_id,
                "origin_lon": first["original_lon"],
                "origin_lat": first["original_lat"],
                "destination_lon": last["original_lon"],
                "destination_lat": last["original_lat"],
                "origin_h3_zone_id": f"h3r{fine_res}:{h3.latlng_to_cell(float(first['original_lat']), float(first['original_lon']), fine_res)}",
                "destination_h3_zone_id": f"h3r{fine_res}:{h3.latlng_to_cell(float(last['original_lat']), float(last['original_lon']), fine_res)}",
                "mode": "bus",
                "od_status": "capture_window_censored_vehicle_segment_not_passenger_od",
                "start_censored": True,
                "end_censored": True,
            }
        )
    pd.DataFrame(sample_od_rows).to_csv(sample_od_out, index=False)
    path_frame = pd.DataFrame(path_rows)
    if not path_frame.empty:
        link_use = (
            path_frame.groupby("link_id", as_index=False)
            .agg(
                traversal_occurrences=("path_occurrence", "count"),
                distinct_segments=("segment_id", "nunique"),
                distinct_vehicles=("vehicle_observation_id", "nunique"),
            )
        )
        link_use["unit_note"] = "sample traversal occurrences; not population flow or observed volume"
    else:
        link_use = pd.DataFrame(columns=["link_id", "traversal_occurrences", "distinct_segments", "distinct_vehicles", "unit_note"])
    link_use.to_csv(link_use_out, index=False)

    calibration_dir = TASK_ROOT / "database" / "calibration"
    calibration_dir.mkdir(parents=True, exist_ok=True)
    calibration = _calibrate_gamma(observation, calibration_dir, config)
    qc = {
        "built_at_utc": utc_now(),
        "source": "MBTA V3 bus vehicle positions",
        "raw_snapshot_files": len(snapshot_paths),
        "raw_api_rows": raw_total,
        "inside_analysis_rows": len(raw_rows),
        "invalid_timestamp_rows": invalid_time,
        "duplicate_rows_removed": duplicate_rows,
        "clean_points": len(clean),
        "segments_total": len(segments),
        "segments_selected_for_matching": len(eligible),
        "segments_matched": len(matched_segment_ids),
        "segments_unmatched_or_not_selected": len(segments) - len(matched_segment_ids),
        "external_hmm_successes": int(match_status["hmm_status"].eq("success").sum()) if not match_status.empty else 0,
        "external_hmm_failures": int(match_status["hmm_status"].eq("failed").sum()) if not match_status.empty else 0,
        "native_selected_successes": int(match_status["selected_engine"].astype(str).str.startswith("native").sum()) if not match_status.empty else 0,
        "matched_point_rows": len(point_match_rows),
        "path_link_occurrences": len(path_rows),
        "path_continuity_checked": True,
        "point_count_closure": {
            "selected_segment_clean_points": int(clean["segment_id"].isin(eligible_ids).sum()),
            "matched_point_rows": len(point_match_rows),
            "note": "Difference, if any, is retained in failed match status rather than discarded.",
        },
        "privacy": "Public transit vehicle IDs are one-way hashed in derived tables; no passenger or OSM user identity is present.",
        "semantic_limit": "Vehicle traces are temporally capture-window censored and are not passenger OD or full service trips.",
        "calibration": calibration,
    }
    qc_out = obs_dir / "gps_qc.json"
    write_json(qc_out, qc)
    source_status_out = obs_dir / "SOURCE_STATUS.md"
    source_status_out.write_text(
        "# GPS source status\n\n"
        "OSM public tracepoints were attempted through both `api.openstreetmap.org` and "
        "`www.openstreetmap.org` on 2026-09-22; each connection timed out, and no OSM GPX "
        "content was obtained. The implemented real GPS source is therefore the official MBTA "
        "V3 bus vehicle endpoint. These are mode-known public transit vehicle positions, not "
        "passenger origins/destinations or passenger counts. External `mapmatcher4gmns` HMM "
        "attempts and any explicit native-engine selections are preserved per segment in "
        "`gps_match_engine_status.csv`.\n",
        encoding="utf-8",
    )
    outputs = [
        clean_out, segments_out, point_match_out, path_out, observations_out, status_out,
        sample_od_out, link_use_out, qc_out, source_status_out,
        calibration_dir / "parameter_registry.csv",
        calibration_dir / "observation_parameter_map.csv",
        calibration_dir / "fit_and_holdout_results.csv",
    ]
    record_stage(
        "process_match_calibrate_gps",
        started,
        raw_total,
        len(clean) + len(point_match_rows) + len(path_rows),
        sum(path.stat().st_size for path in snapshot_paths),
        outputs,
        status="completed" if matched_segment_ids else "completed_no_successful_matches",
        notes="Real bus GPS; strict external HMM attempted first and native selected only after recorded failure.",
    )
    append_tool_usage(
        "GPS road matching and point projection",
        "mapmatching4gmns 0.3.0; mapmatcher4gmns 0.2.1",
        "trace_to_evidence; match(engine='mapmatcher4gmns'); explicit match(engine='native') after recorded failure; derived monotone projection",
        "raw/gps/mbta_vehicles_snapshot_*.json; database/network/matcher",
        "database/observations",
        "completed" if matched_segment_ids else "completed_no_successful_matches",
        "No silent fallback; per-segment engine status retained.",
    )
    return qc


def _finish_gps_segment(
    records: list[dict[str, Any]],
    vehicle_id: str,
    segment_index: int,
    segment_summaries: list[dict[str, Any]],
    clean_rows: list[dict[str, Any]],
    forward: Transformer,
) -> None:
    records = sorted(records, key=lambda row: row["timestamp_dt"])
    segment_id = f"{vehicle_id}:s{segment_index:02d}"
    trace_id = vehicle_id
    metric = [
        transform(forward.transform, Point(float(row["longitude"]), float(row["latitude"])))
        for row in records
    ]
    step_distances = [0.0] + [metric[i - 1].distance(metric[i]) for i in range(1, len(metric))]
    step_seconds = [0.0] + [
        (records[i]["timestamp_dt"] - records[i - 1]["timestamp_dt"]).total_seconds()
        for i in range(1, len(records))
    ]
    for point_seq, (row, distance, seconds) in enumerate(zip(records, step_distances, step_seconds), start=1):
        clean_rows.append(
            {
                "trace_id": trace_id,
                "segment_id": segment_id,
                "vehicle_observation_id": vehicle_id,
                "point_seq": point_seq,
                "original_lon": row["longitude"],
                "original_lat": row["latitude"],
                "timestamp": row["timestamp"],
                "timestamp_dt": row["timestamp_dt"],
                "route_id": row["route_id"],
                "trip_id": row["trip_id"],
                "mode": "bus",
                "bearing_deg_north": row["bearing_deg_north"],
                "speed": row["speed"],
                "step_distance_m": distance,
                "step_seconds": seconds,
                "derived_step_speed_mps": distance / seconds if seconds > 0 else "",
                "start_censored": point_seq == 1,
                "end_censored": point_seq == len(records),
                "source_id": "mbta_v3_vehicle_positions",
                "qc_status": "retained",
            }
        )
    duration = (records[-1]["timestamp_dt"] - records[0]["timestamp_dt"]).total_seconds() if len(records) > 1 else 0.0
    displacement = metric[0].distance(metric[-1]) if len(metric) > 1 else 0.0
    path_distance = sum(step_distances)
    segment_summaries.append(
        {
            "trace_id": trace_id,
            "segment_id": segment_id,
            "vehicle_observation_id": vehicle_id,
            "route_id": records[0]["route_id"],
            "trip_id": records[0]["trip_id"],
            "mode": "bus",
            "point_count": len(records),
            "start_time": records[0]["timestamp"],
            "end_time": records[-1]["timestamp"],
            "duration_seconds": duration,
            "observed_path_point_distance_m": path_distance,
            "observed_displacement_m": displacement,
            "max_derived_step_speed_mps": max(
                [distance / seconds for distance, seconds in zip(step_distances, step_seconds) if seconds > 0],
                default=0.0,
            ),
            "start_censored": True,
            "end_censored": True,
            "censoring_reason": "finite_live_capture_window_and_analysis_boundary_filter",
            "source_id": "mbta_v3_vehicle_positions",
            "segment_status": "candidate",
        }
    )


def _calibrate_gamma(
    observations: pd.DataFrame, calibration_dir: Path, config: dict[str, Any]
) -> dict[str, Any]:
    usable = observations[
        observations["quality_status"].eq("usable_end_to_end_vehicle_segment")
        & (pd.to_numeric(observations["baseline_path_fftt_min"], errors="coerce") > 0)
        & (pd.to_numeric(observations["observed_duration_min"], errors="coerce") > 0)
    ].copy() if not observations.empty else observations.copy()
    vehicle_ids = sorted(usable["vehicle_observation_id"].unique().tolist()) if not usable.empty else []
    holdout_vehicles = set(vehicle_ids[::5]) if len(vehicle_ids) >= 5 else set()
    usable["split"] = np.where(usable["vehicle_observation_id"].isin(holdout_vehicles), "holdout", "train") if not usable.empty else []
    train = usable[usable["split"].eq("train")] if not usable.empty else usable
    holdout = usable[usable["split"].eq("holdout")] if not usable.empty else usable
    status = "NOT_ESTIMABLE"
    reason = "Fewer than two usable, independently grouped vehicle segments"
    gamma = math.nan
    result_rows = []
    if len(train) >= 2:
        x = train["baseline_path_fftt_min"].to_numpy(float)
        y = train["observed_duration_min"].to_numpy(float)
        denominator = float(np.sum(x * x))
        if denominator > 0:
            gamma = max(float(np.sum(x * y) / denominator), 1e-9)
            status = "ESTIMATED_NOT_VALIDATED"
            reason = "No independent holdout groups available"
            for split_name, frame in (("train", train), ("holdout", holdout)):
                if frame.empty:
                    continue
                observed = frame["observed_duration_min"].to_numpy(float)
                baseline = frame["baseline_path_fftt_min"].to_numpy(float)
                for model, predicted in (("baseline_gamma_1", baseline), ("fitted_gamma", gamma * baseline)):
                    result_rows.append(
                        {
                            "parameter_id": "bus_path_time_scale_gamma",
                            "split": split_name,
                            "model": model,
                            "gamma": 1.0 if model == "baseline_gamma_1" else gamma,
                            "segments": len(frame),
                            "distinct_vehicle_groups": frame["vehicle_observation_id"].nunique(),
                            **_metric_errors(observed, predicted),
                        }
                    )
            if len(holdout) >= 2 and holdout["vehicle_observation_id"].nunique() >= 2:
                baseline_holdout = next(
                    row["rmse_min"]
                    for row in result_rows
                    if row["split"] == "holdout" and row["model"] == "baseline_gamma_1"
                )
                fitted_holdout = next(
                    row["rmse_min"]
                    for row in result_rows
                    if row["split"] == "holdout" and row["model"] == "fitted_gamma"
                )
                if fitted_holdout < baseline_holdout:
                    status = "ESTIMATED_AND_HOLDOUT_IMPROVED_WITH_LIMITATIONS"
                    reason = "Independent vehicle-group holdout improved; no statistical significance claim"
                else:
                    status = "ESTIMATED_BUT_HOLDOUT_NOT_IMPROVED"
                    reason = (
                        "Independent vehicle-group holdout was evaluated but fitted RMSE did not improve; "
                        "retain only as a diagnostic estimate"
                    )
    registry = pd.DataFrame(
        [
            {
                "parameter_id": "bus_path_time_scale_gamma",
                "parameter_name": "shared captured bus path travel-time scale",
                "initial_value": 1.0,
                "estimated_value": gamma if math.isfinite(gamma) else "",
                "constraint": "gamma > 0",
                "loss": "sum((observed_duration_min - gamma * baseline_path_fftt_min)^2)",
                "status": status,
                "mode": "bus",
                "observation_source": "MBTA V3 vehicle updated_at timestamps",
                "network_baseline": config["network"]["network_version"],
                "identification_limit": "Captures traffic, dwell, signal, sampling, and map/network mismatch together; not BPR alpha/beta or future speed truth.",
                "temporal_limit": "GPS capture is 2026-09-21 local; GMNS source commit is 2025-05-02 and roadway vintage is not independently established.",
                "reason": reason,
            }
        ]
    )
    registry.to_csv(calibration_dir / "parameter_registry.csv", index=False)
    mapping_rows = [
        {
            "observation_id": row.observation_id,
            "model_quantity": "matched_path_sum_vdf_fftt_min",
            "parameter_id": "bus_path_time_scale_gamma",
            "split": row.split,
            "observed_value": row.observed_duration_min,
            "observed_unit": "minute",
            "baseline_value": row.baseline_path_fftt_min,
            "baseline_unit": "minute",
            "independence_group": row.vehicle_observation_id,
        }
        for row in usable.itertuples(index=False)
    ]
    pd.DataFrame(
        mapping_rows,
        columns=[
            "observation_id", "model_quantity", "parameter_id", "split", "observed_value",
            "observed_unit", "baseline_value", "baseline_unit", "independence_group",
        ],
    ).to_csv(calibration_dir / "observation_parameter_map.csv", index=False)
    pd.DataFrame(
        result_rows,
        columns=[
            "parameter_id", "split", "model", "gamma", "segments", "distinct_vehicle_groups",
            "mae_min", "rmse_min", "mean_error_min",
        ],
    ).to_csv(calibration_dir / "fit_and_holdout_results.csv", index=False)
    return {
        "status": status,
        "reason": reason,
        "gamma": gamma if math.isfinite(gamma) else None,
        "usable_segments": len(usable),
        "train_segments": len(train),
        "holdout_segments": len(holdout),
        "train_vehicle_groups": int(train["vehicle_observation_id"].nunique()) if not train.empty else 0,
        "holdout_vehicle_groups": int(holdout["vehicle_observation_id"].nunique()) if not holdout.empty else 0,
    }


def build_spatial(config: dict[str, Any]) -> dict[str, Any]:
    started = time.time()
    network_dir = TASK_ROOT / "database" / "network" / "matcher"
    node_path = network_dir / "node.csv"
    link_path = network_dir / "link.csv"
    nodes = pd.read_csv(node_path, dtype={"node_id": "string"}, keep_default_na=False)
    links = pd.read_csv(
        link_path,
        dtype={"link_id": "string", "from_node_id": "string", "to_node_id": "string"},
        keep_default_na=False,
    )
    core_wgs, analysis_wgs, core_metric, _ = boundary_geometries(config)
    forward, _ = transformers(config)
    fine_res = int(config["zones"]["fine_resolution"])
    parent_res = int(config["zones"]["parent_resolution"])
    west, south, east, north = config["study_area"]["core_bbox_wgs84"]
    latlng_poly = h3.LatLngPoly(
        [(south, west), (south, east), (north, east), (north, west)]
    )
    fine_cells = sorted(h3.h3shape_to_cells(latlng_poly, fine_res))
    parent_cells = sorted({h3.cell_to_parent(cell, parent_res) for cell in fine_cells})

    network_id = config["network"]["network_id"]
    network_version = config["network"]["network_version"]
    zone_rows: list[dict[str, Any]] = []
    zone_features: list[dict[str, Any]] = []
    cell_polygons: dict[str, Polygon] = {}
    for level, cells in (("fine", fine_cells), ("parent", parent_cells)):
        for cell in cells:
            full = h3_polygon(cell)
            clipped = full.intersection(core_wgs)
            zone_id = f"h3r{h3.get_resolution(cell)}:{cell}"
            cell_polygons[cell] = full
            zone_rows.append(
                {
                    "zone_id": zone_id,
                    "zone_system": "H3",
                    "zone_level": level,
                    "h3_resolution": h3.get_resolution(cell),
                    "full_cell_id": cell,
                    "centroid_lon": h3.cell_to_latlng(cell)[1],
                    "centroid_lat": h3.cell_to_latlng(cell)[0],
                    "full_area_km2": h3.cell_area(cell, unit="km^2"),
                    "clipped_area_km2": transform(forward.transform, clipped).area / 1_000_000.0,
                    "geometry_crs": "EPSG:4326",
                    "full_geometry_wkt": full.wkt,
                    "clipped_geometry_wkt": clipped.wkt,
                    "network_id": network_id,
                    "network_version": network_version,
                    "source_id": "h3_4.5.0",
                    "status": "project_model_zone",
                }
            )
            zone_features.append(
                {
                    "type": "Feature",
                    "properties": {
                        "zone_id": zone_id,
                        "zone_level": level,
                        "h3_resolution": h3.get_resolution(cell),
                        "full_cell_id": cell,
                        "geometry_variant": "clipped_to_core",
                    },
                    "geometry": mapping(clipped),
                }
            )
    zone_out = TASK_ROOT / "database" / "zones" / "zone.csv"
    zone_geo_out = TASK_ROOT / "database" / "zones" / "zone.geojson"
    pd.DataFrame(zone_rows).to_csv(zone_out, index=False)
    write_geojson(zone_geo_out, zone_features)

    hierarchy_rows = [
        {
            "child_zone_id": f"h3r{fine_res}:{cell}",
            "parent_zone_id": f"h3r{parent_res}:{h3.cell_to_parent(cell, parent_res)}",
            "relationship": "h3_logical_parent",
            "allocation_weight": 1.0,
            "network_id": network_id,
            "network_version": network_version,
            "method": "h3.cell_to_parent",
        }
        for cell in fine_cells
    ]
    hierarchy_out = TASK_ROOT / "database" / "zones" / "zone_hierarchy.csv"
    pd.DataFrame(hierarchy_rows).to_csv(hierarchy_out, index=False)

    node_points = {
        str(row.node_id): Point(float(row.x_coord), float(row.y_coord))
        for row in nodes.itertuples(index=False)
    }
    graph = nx.DiGraph()
    best_link: dict[tuple[str, str], tuple[str, float]] = {}
    for row in links.itertuples(index=False):
        u, v = str(row.from_node_id), str(row.to_node_id)
        weight = float(row.vdf_fftt)
        graph.add_edge(u, v, weight=weight)
        current = best_link.get((u, v))
        if current is None or weight < current[1]:
            best_link[(u, v)] = (str(row.link_id), weight)
    strongly_connected = list(nx.strongly_connected_components(graph))
    largest_scc = max(strongly_connected, key=len)
    eligible_nodes = [n for n in graph if graph.in_degree(n) > 0 and graph.out_degree(n) > 0]
    preferred_nodes = [n for n in eligible_nodes if n in largest_scc]
    node_metric = {node_id: transform(forward.transform, node_points[node_id]) for node_id in preferred_nodes}

    allocation_rows: list[dict[str, Any]] = []
    fine_cell_set = set(fine_cells)
    for node_id, point in node_points.items():
        cell = h3.latlng_to_cell(point.y, point.x, fine_res)
        allocation_rows.append(
            {
                "entity_type": "physical_node",
                "entity_id": node_id,
                "fine_zone_id": f"h3r{fine_res}:{cell}" if cell in fine_cell_set else "",
                "parent_zone_id": f"h3r{parent_res}:{h3.cell_to_parent(cell, parent_res)}" if cell in fine_cell_set else "",
                "allocation_method": "point_h3_index",
                "allocation_weight": 1.0 if cell in fine_cell_set else "",
                "status": "allocated" if cell in fine_cell_set else "outside_core",
                "network_id": network_id,
                "network_version": network_version,
            }
        )
    allocation_out = TASK_ROOT / "database" / "zones" / "zone_overlap_or_allocation.csv"
    pd.DataFrame(allocation_rows).to_csv(allocation_out, index=False)

    access_rows: list[dict[str, Any]] = []
    for cell in fine_cells:
        cell_poly = cell_polygons[cell]
        center_lat, center_lon = h3.cell_to_latlng(cell)
        center_metric = transform(forward.transform, Point(center_lon, center_lat))
        in_cell = [n for n in preferred_nodes if cell_poly.covers(node_points[n])]
        candidates = in_cell if in_cell else preferred_nodes
        selected_node = min(candidates, key=lambda n: center_metric.distance(node_metric[n]))
        distance = center_metric.distance(node_metric[selected_node])
        access_rows.append(
            {
                "zone_id": f"h3r{fine_res}:{cell}",
                "access_node_id": selected_node,
                "connector_id": f"mclc:{cell}:{selected_node}",
                "connector_type": "model_zone_access_nonphysical",
                "direction": "bidirectional_access_to_directed_network",
                "weight": 1.0,
                "access_distance_m": round(distance, 3),
                "selection_method": "nearest_eligible_node_within_cell" if in_cell else "nearest_largest_scc_node",
                "node_in_largest_scc": True,
                "ordinary_road_use_allowed": False,
                "gps_match_allowed": False,
                "network_id": network_id,
                "network_version": network_version,
                "status": "reachable_access",
            }
        )
    access_out = TASK_ROOT / "database" / "zones" / "zone_access.csv"
    pd.DataFrame(access_rows).to_csv(access_out, index=False)

    source_nodes = pd.read_csv(
        TASK_ROOT / "database" / "network" / "gmns" / "node.csv",
        dtype={"node_id": "string", "zone_id": "string"},
        keep_default_na=False,
    )
    taz_rows = []
    for row in source_nodes[source_nodes["node_role"].eq("source_taz_centroid")].itertuples(index=False):
        cell = h3.latlng_to_cell(float(row.y_coord), float(row.x_coord), fine_res)
        inside = cell in fine_cell_set
        taz_rows.append(
            {
                "source_taz_id": str(row.zone_id),
                "source_centroid_node_id": str(row.node_id),
                "fine_zone_id": f"h3r{fine_res}:{cell}" if inside else "",
                "parent_zone_id": f"h3r{parent_res}:{h3.cell_to_parent(cell, parent_res)}" if inside else "",
                "relationship": "centroid_point_h3_index" if inside else "outside_core_no_h3_assignment",
                "network_id": network_id,
                "network_version": network_version,
            }
        )
    taz_out = TASK_ROOT / "database" / "zones" / "source_taz_h3_crosswalk.csv"
    pd.DataFrame(taz_rows).to_csv(taz_out, index=False)

    core_nodes = [
        node_id
        for node_id in largest_scc
        if core_wgs.covers(node_points[node_id])
    ]
    if len(core_nodes) < 2:
        raise RuntimeError("Fewer than two strongly connected physical nodes in core boundary")
    y_mid = (south + north) / 2.0
    west_candidates = sorted(core_nodes, key=lambda n: (abs(node_points[n].y - y_mid), node_points[n].x))[:100]
    east_candidates = sorted(core_nodes, key=lambda n: (abs(node_points[n].y - y_mid), -node_points[n].x))[:100]
    start_node = min(west_candidates, key=lambda n: node_points[n].x)
    end_node = max(east_candidates, key=lambda n: node_points[n].x)
    node_path_ids = nx.shortest_path(graph, start_node, end_node, weight="weight")
    corridor_links = []
    for order, (u, v) in enumerate(zip(node_path_ids[:-1], node_path_ids[1:]), start=1):
        link_id, travel_time = best_link[(u, v)]
        corridor_links.append(
            {
                "corridor_id": "mcl_central_boston_ew_01",
                "occurrence": order,
                "member_order": order,
                "link_id": link_id,
                "from_node_id": u,
                "to_node_id": v,
                "direction": "AB",
                "static_free_flow_time_min": travel_time,
                "time_aggregation": "ordered_sum_of_member_vdf_fftt",
                "network_id": network_id,
                "network_version": network_version,
            }
        )
    corridor_link_out = TASK_ROOT / "database" / "corridors" / "corridor_link.csv"
    pd.DataFrame(corridor_links).to_csv(corridor_link_out, index=False)
    corridor_out = TASK_ROOT / "database" / "corridors" / "corridor.csv"
    pd.DataFrame(
        [
            {
                "corridor_id": "mcl_central_boston_ew_01",
                "name": "Central Boston west-to-east model corridor",
                "direction": "west_to_east",
                "start_node_id": start_node,
                "end_node_id": end_node,
                "member_occurrences": len(corridor_links),
                "static_free_flow_time_min": sum(x["static_free_flow_time_min"] for x in corridor_links),
                "capacity_aggregation": "not_additive_not_reported",
                "flow_aggregation": "not_additive_not_reported",
                "network_id": network_id,
                "network_version": network_version,
                "status": "directed_continuous_physical_path",
            }
        ]
    ).to_csv(corridor_out, index=False)

    validations = {
        "validated_at_utc": utc_now(),
        "fine_zones": len(fine_cells),
        "parent_zones": len(parent_cells),
        "zone_access_rows": len(access_rows),
        "fine_zones_with_access": sum(x["status"] == "reachable_access" for x in access_rows),
        "max_access_distance_m": max(x["access_distance_m"] for x in access_rows),
        "nodes_allocated_to_core_h3": sum(x["status"] == "allocated" for x in allocation_rows),
        "nodes_outside_core": sum(x["status"] == "outside_core" for x in allocation_rows),
        "logical_parent_weight_sum_by_child_valid": all(x["allocation_weight"] == 1.0 for x in hierarchy_rows),
        "directed_physical_graph_nodes": graph.number_of_nodes(),
        "directed_physical_graph_edges": graph.number_of_edges(),
        "strong_components": len(strongly_connected),
        "largest_scc_nodes": len(largest_scc),
        "corridor_member_occurrences": len(corridor_links),
        "corridor_continuous": all(
            corridor_links[i]["to_node_id"] == corridor_links[i + 1]["from_node_id"]
            for i in range(len(corridor_links) - 1)
        ),
        "core_area_km2": core_metric.area / 1_000_000.0,
        "h3_semantics": "Parent relation uses H3 logical parent; clipped polygon areas are not used as hierarchy weights.",
    }
    validation_out = TASK_ROOT / "reports" / "spatial_validation.json"
    write_json(validation_out, validations)

    outputs = [
        zone_out,
        zone_geo_out,
        hierarchy_out,
        allocation_out,
        access_out,
        taz_out,
        corridor_out,
        corridor_link_out,
        validation_out,
    ]
    record_stage(
        "build_spatial",
        started,
        len(nodes) + len(links),
        len(zone_rows) + len(allocation_rows) + len(access_rows) + len(corridor_links),
        node_path.stat().st_size + link_path.stat().st_size,
        outputs,
        notes="H3 logical hierarchy and metric nearest-access selection; corridor is an ordered directed path.",
    )
    append_tool_usage(
        "H3 zones and network linkage",
        "h3 4.5.0",
        "h3.h3shape_to_cells; h3.cell_to_parent; tools/city_database.py build-spatial",
        "database/boundary/core.geojson; database/network/matcher",
        "database/zones; database/corridors",
        "completed",
        "H3 resolutions are project modelling levels, not competition labels.",
    )
    return validations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build-network")
    sub.add_parser("build-spatial")
    sub.add_parser("fetch-activity")
    sub.add_parser("build-activity")
    sub.add_parser("build-activity-fallback")
    sub.add_parser("build-demand")
    sub.add_parser("run-assignment")
    sub.add_parser("build-transit")
    sub.add_parser("fetch-mbta-gps")
    sub.add_parser("process-gps")
    sub.add_parser("build-base")
    args = parser.parse_args(argv)
    config = load_config(args.config)
    if args.command in {"build-network", "build-base"}:
        print(json.dumps(build_network(config), indent=2))
    if args.command in {"build-spatial", "build-base"}:
        print(json.dumps(build_spatial(config), indent=2))
    if args.command == "fetch-activity":
        print(json.dumps(fetch_osm_activity(config), indent=2))
    if args.command == "build-activity":
        print(json.dumps(build_activity(config), indent=2))
    if args.command == "build-activity-fallback":
        print(json.dumps(build_activity_fallback(config), indent=2))
    if args.command == "build-demand":
        print(json.dumps(build_demand(config), indent=2))
    if args.command == "run-assignment":
        print(json.dumps(run_assignment(config), indent=2))
    if args.command == "build-transit":
        print(json.dumps(build_transit(config), indent=2))
    if args.command == "fetch-mbta-gps":
        print(json.dumps(fetch_mbta_gps(config), indent=2))
    if args.command == "process-gps":
        print(json.dumps(process_match_calibrate_gps(config), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
