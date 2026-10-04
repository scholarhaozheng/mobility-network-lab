#!/usr/bin/env python3
"""Versioned correctness pass for the existing Central Boston instance.

This script does not fetch data or rerun map matching.  It re-evaluates the
saved 30-segment match set, aligns model time to the observed GPS window,
creates a period-consistent capacity adapter, and audits long zone access.
Legacy match, calibration, assignment, and raw files remain unchanged.
"""

from __future__ import annotations

import hashlib
import json
import math
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import networkx as nx
import numpy as np
import pandas as pd
from pyproj import Transformer
from shapely import wkt
from shapely.geometry import LineString, Point
from shapely.ops import transform


import os
TASK_ROOT = Path(os.environ.get("MCL_BOSTON_SOURCE_ROOT", Path(__file__).resolve().parents[1])).resolve()
REPO_ROOT = TASK_ROOT.parents[1]
CONFIG_PATH = TASK_ROOT / "config" / "quality_correction_v1.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def config_and_signature() -> tuple[dict[str, Any], str]:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    canonical = json.dumps(config, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return config, hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def backup_affected_files(run_id: str) -> Path:
    backup = TASK_ROOT / "history" / f"pre_{run_id}"
    paths = [
        "config/city_config.yaml",
        "tools/city_database.py",
        "tools/finalize_database.py",
        "tools/build_public_component.py",
        "tools/package_deliveries.py",
        "database/observations/gps_segments.csv",
        "database/observations/gps_point_match.csv",
        "database/observations/gps_path_links.csv",
        "database/observations/gps_observations.csv",
        "database/observations/gps_match_engine_status.csv",
        "database/observations/gps_qc.json",
        "database/calibration/parameter_registry.csv",
        "database/calibration/observation_parameter_map.csv",
        "database/calibration/fit_and_holdout_results.csv",
        "database/network/field_mapping.csv",
        "database/network/attribute_provenance.csv",
        "reports/assignment_summary.json",
        "database/scenarios/capacity_stress_v1.json",
    ]
    delivery_root = REPO_ROOT / "deliveries" / "boston_database"
    for name in ["receiver_review.zip", "boston_public_increment.zip", "PACKAGE_SUMMARY.json"]:
        source = delivery_root / name
        if source.exists():
            destination = backup / "delivery" / name
            if not destination.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
    for relative in paths:
        source = TASK_ROOT / relative
        destination = backup / relative
        if source.exists() and not destination.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
    return backup


def raw_hashes() -> dict[str, str]:
    paths = [
        TASK_ROOT / "raw" / "gmns_plus_21_boston" / "node.csv",
        TASK_ROOT / "raw" / "gmns_plus_21_boston" / "link.csv",
        TASK_ROOT / "raw" / "gmns_plus_21_boston" / "demand.csv",
        TASK_ROOT / "raw" / "gtfs" / "mdb-437_20260918.zip",
        *sorted((TASK_ROOT / "raw" / "gps").glob("mbta_vehicles_snapshot_*.json")),
    ]
    return {path.relative_to(TASK_ROOT).as_posix(): sha256_file(path) for path in paths}


def _relation_id(entity: dict[str, Any], name: str) -> str:
    data = entity.get("relationships", {}).get(name, {}).get("data")
    return str(data.get("id", "")) if isinstance(data, dict) else ""


def raw_point_metadata() -> tuple[dict[tuple[str, str, float, float], dict[str, Any]], dict[str, Any]]:
    acquisition_path = TASK_ROOT / "raw" / "gps" / "mbta_vehicle_acquisition.json"
    acquisition = json.loads(acquisition_path.read_text(encoding="utf-8"))
    request_by_index = {
        int(item["snapshot_index"]): item["request_time_utc"] for item in acquisition["records"]
    }
    lookup: dict[tuple[str, str, float, float], dict[str, Any]] = {}
    statuses: Counter[str] = Counter()
    for path in sorted((TASK_ROOT / "raw" / "gps").glob("mbta_vehicles_snapshot_*.json")):
        index = int(path.stem.rsplit("_", 1)[-1])
        payload = json.loads(path.read_text(encoding="utf-8"))
        for entity in payload.get("data", []):
            attrs = entity.get("attributes", {})
            lon, lat = attrs.get("longitude"), attrs.get("latitude")
            if lon is None or lat is None:
                continue
            public_id = "mbtav:" + hashlib.sha256(str(entity.get("id", "")).encode("utf-8")).hexdigest()[:16]
            key = (public_id, str(attrs.get("updated_at", "")), round(float(lon), 6), round(float(lat), 6))
            statuses[str(attrs.get("current_status", "missing"))] += 1
            candidate = {
                "snapshot_index": index,
                "request_time_utc": request_by_index.get(index, ""),
                "current_status": str(attrs.get("current_status", "")),
                "stop_id": _relation_id(entity, "stop"),
                "route_id_raw": _relation_id(entity, "route"),
                "trip_id_raw": _relation_id(entity, "trip"),
            }
            existing = lookup.get(key)
            if existing is None or index < int(existing["snapshot_index"]):
                lookup[key] = candidate
    return lookup, {"raw_status_counts": dict(statuses), "raw_lookup_rows": len(lookup)}


def _window_fftt(points: pd.DataFrame, path: pd.DataFrame, link_lookup: pd.DataFrame) -> dict[str, Any]:
    first = points.iloc[0]
    last = points.iloc[-1]
    first_occ = int(first["path_occurrence"])
    last_occ = int(last["path_occurrence"])
    first_fraction = float(first["fraction"])
    last_fraction = float(last["fraction"])
    if last_occ < first_occ:
        return {"window_baseline_fftt_min": math.nan, "window_formula_status": "invalid_occurrence_order"}
    if first_occ == last_occ:
        link_id = str(path.loc[path["path_occurrence"].eq(first_occ), "link_id"].iloc[0])
        delta_fraction = last_fraction - first_fraction
        return {
            "window_baseline_fftt_min": delta_fraction * float(link_lookup.loc[link_id, "vdf_fftt"]),
            "window_formula_status": "same_occurrence_signed_fraction_difference",
        }
    first_link = str(path.loc[path["path_occurrence"].eq(first_occ), "link_id"].iloc[0])
    last_link = str(path.loc[path["path_occurrence"].eq(last_occ), "link_id"].iloc[0])
    value = (1.0 - first_fraction) * float(link_lookup.loc[first_link, "vdf_fftt"])
    if last_occ - first_occ > 1:
        for occurrence in range(first_occ + 1, last_occ):
            link_id = str(path.loc[path["path_occurrence"].eq(occurrence), "link_id"].iloc[0])
            value += float(link_lookup.loc[link_id, "vdf_fftt"])
    value += last_fraction * float(link_lookup.loc[last_link, "vdf_fftt"])
    return {
        "window_baseline_fftt_min": value,
        "window_formula_status": "first_remaining_plus_intermediate_plus_last_traversed",
    }


def evaluate_gps_quality(config: dict[str, Any], signature: str, run_dir: Path) -> dict[str, Any]:
    run_id = config["run_id"]
    rules = config["gps_quality"]
    obs_dir = TASK_ROOT / "database" / "observations"
    segments = pd.read_csv(obs_dir / "gps_segments.csv", keep_default_na=False)
    clean = pd.read_csv(obs_dir / "gps_points_clean.csv", keep_default_na=False)
    points = pd.read_csv(
        obs_dir / "gps_point_match.csv",
        dtype={"matched_link_id": "string"},
        keep_default_na=False,
    )
    paths = pd.read_csv(
        obs_dir / "gps_path_links.csv", dtype={"link_id": "string"}, keep_default_na=False
    )
    engine_status = pd.read_csv(obs_dir / "gps_match_engine_status.csv", keep_default_na=False)
    old_observations = pd.read_csv(obs_dir / "gps_observations.csv", keep_default_na=False)
    links = pd.read_csv(
        TASK_ROOT / "database" / "network" / "matcher" / "link.csv",
        dtype={"link_id": "string", "from_node_id": "string", "to_node_id": "string"},
        keep_default_na=False,
    )
    nodes = pd.read_csv(
        TASK_ROOT / "database" / "network" / "matcher" / "node.csv",
        dtype={"node_id": "string"}, keep_default_na=False,
    )
    link_lookup = links.set_index("link_id", drop=False)
    node_lookup = nodes.set_index("node_id", drop=False)
    forward = Transformer.from_crs("EPSG:4326", "EPSG:32619", always_xy=True)
    line_metric: dict[str, Any] = {
        link_id: transform(forward.transform, wkt.loads(str(row.geometry)))
        for link_id, row in link_lookup.iterrows()
    }
    raw_lookup, raw_summary = raw_point_metadata()
    status_lookup = engine_status.set_index("segment_id").to_dict("index")
    old_obs_lookup = old_observations.set_index("segment_id").to_dict("index")
    point_rows: list[dict[str, Any]] = []
    quality_rows: list[dict[str, Any]] = []
    observation_rows: list[dict[str, Any]] = []

    for segment in segments.itertuples(index=False):
        segment_id = str(segment.segment_id)
        selected = str(segment.matching_selection) == "selected_first_pass"
        segment_path = paths[paths["segment_id"].eq(segment_id)].sort_values("path_occurrence")
        segment_points = points[points["segment_id"].eq(segment_id)].sort_values("point_seq").copy()
        engine = status_lookup.get(segment_id, {})
        route_returned = not segment_path.empty and not segment_points.empty
        base = {
            "run_id": run_id,
            "config_signature_sha256": signature,
            "segment_id": segment_id,
            "vehicle_observation_id": str(segment.vehicle_observation_id),
            "route_id": str(segment.route_id),
            "matching_selection": str(segment.matching_selection),
            "route_returned": route_returned,
            "selected_engine": str(engine.get("selected_engine", "")),
            "fallback_reason": str(engine.get("hmm_error", "")) if str(engine.get("selected_engine", "")).startswith("native") else "",
        }
        if not selected:
            quality_rows.append({
                **base,
                "disposition": "not_selected",
                "topology_valid": "not_evaluated",
                "spatial_quality": "not_evaluated",
                "temporal_quality": "not_evaluated",
                "path_plausibility": "not_evaluated",
                "observation_eligible": False,
                "quality_class": "not_selected",
                "exclusion_reasons": "not_selected_for_matching",
            })
            continue
        if not route_returned:
            quality_rows.append({
                **base,
                "disposition": "selected_route_failed",
                "topology_valid": False,
                "spatial_quality": "not_evaluated",
                "temporal_quality": "not_evaluated",
                "path_plausibility": "not_evaluated",
                "observation_eligible": False,
                "quality_class": "route_failed",
                "exclusion_reasons": str(engine.get("selected_error", "route_not_returned")),
            })
            continue

        path_ids = segment_path["link_id"].astype(str).tolist()
        continuity = all(
            str(link_lookup.loc[a, "to_node_id"]) == str(link_lookup.loc[b, "from_node_id"])
            for a, b in zip(path_ids, path_ids[1:])
        )
        known = all(link_id in link_lookup.index for link_id in path_ids)
        physical = all(bool(link_lookup.loc[link_id, "gps_match_allowed"]) for link_id in path_ids)
        direction_errors = []
        occurrence_lengths: list[float] = []
        for link_id in path_ids:
            link = link_lookup.loc[link_id]
            line = line_metric[link_id]
            occurrence_lengths.append(float(line.length))
            from_node = node_lookup.loc[str(link["from_node_id"])]
            to_node = node_lookup.loc[str(link["to_node_id"])]
            p_from = transform(forward.transform, Point(float(from_node.x_coord), float(from_node.y_coord)))
            p_to = transform(forward.transform, Point(float(to_node.x_coord), float(to_node.y_coord)))
            direction_errors.append(max(Point(line.coords[0]).distance(p_from), Point(line.coords[-1]).distance(p_to)))
        direction_valid = max(direction_errors, default=math.inf) <= 1.0
        topology_valid = bool(known and continuity and physical and direction_valid)
        prefixes = np.cumsum([0.0] + occurrence_lengths[:-1]).tolist()

        timestamps = pd.to_datetime(segment_points["timestamp"], utc=True, errors="coerce")
        segment_points["timestamp_utc"] = timestamps
        cumulative = []
        status_values = []
        stop_values = []
        acquisition_lags = []
        for row in segment_points.itertuples(index=False):
            occurrence = int(row.path_occurrence)
            cumulative.append(prefixes[occurrence - 1] + float(row.offset_m))
            key = (
                str(row.vehicle_observation_id), str(row.timestamp),
                round(float(row.original_lon), 6), round(float(row.original_lat), 6),
            )
            raw = raw_lookup.get(key, {})
            status_values.append(str(raw.get("current_status", "missing")))
            stop_values.append(str(raw.get("stop_id", "")))
            request_time = pd.to_datetime(raw.get("request_time_utc", ""), utc=True, errors="coerce")
            observed_time = pd.to_datetime(row.timestamp, utc=True, errors="coerce")
            acquisition_lags.append(
                float((request_time - observed_time).total_seconds())
                if pd.notna(request_time) and pd.notna(observed_time) else math.nan
            )
        segment_points["cumulative_path_m"] = cumulative
        segment_points["along_delta_m"] = segment_points["cumulative_path_m"].diff()
        segment_points["time_delta_seconds"] = segment_points["timestamp_utc"].diff().dt.total_seconds()
        segment_points["along_speed_mps"] = np.where(
            segment_points["time_delta_seconds"] > 0,
            segment_points["along_delta_m"] / segment_points["time_delta_seconds"],
            np.nan,
        )
        segment_points["backtrack_m"] = np.maximum(-segment_points["along_delta_m"], 0.0)
        segment_points["current_status"] = status_values
        segment_points["reported_stop_id"] = stop_values
        segment_points["acquisition_lag_seconds"] = acquisition_lags
        segment_points["run_id"] = run_id
        segment_points["config_signature_sha256"] = signature
        point_rows.extend(segment_points.drop(columns=["timestamp_utc"]).to_dict("records"))

        max_lateral = float(pd.to_numeric(segment_points["lateral_error_m"]).max())
        outlier_points = int((pd.to_numeric(segment_points["lateral_error_m"]) > float(rules["spatial_lateral_error_limit_m"])).sum())
        spatial_pass = outlier_points == 0
        deltas = pd.to_numeric(segment_points["along_delta_m"], errors="coerce")
        time_deltas = pd.to_numeric(segment_points["time_delta_seconds"], errors="coerce")
        speeds = pd.to_numeric(segment_points["along_speed_mps"], errors="coerce")
        backtracks = pd.to_numeric(segment_points["backtrack_m"], errors="coerce")
        max_speed = float(speeds.max()) if speeds.notna().any() else math.nan
        max_backtrack = float(backtracks.max()) if backtracks.notna().any() else 0.0
        nonpositive_time = int((time_deltas.dropna() <= 0).sum())
        long_gaps = int((time_deltas > float(rules["max_sample_gap_seconds"])).sum())
        excessive_speed = int((speeds > float(rules["max_along_route_speed_mps"])).sum())
        excessive_backtrack = int((backtracks > float(rules["backtrack_tolerance_m"])).sum())
        window_progress = float(cumulative[-1] - cumulative[0])
        raw_displacement = float(segment.observed_displacement_m)
        detour_ratio = window_progress / raw_displacement if raw_displacement > 0 else math.inf
        detour_excess = window_progress - raw_displacement
        detour_fail = bool(
            detour_ratio > float(rules["detour_ratio_limit"])
            and detour_excess > float(rules["detour_excess_distance_m"])
        )
        temporal_pass = (
            nonpositive_time == 0 and long_gaps == 0 and excessive_speed == 0
            and excessive_backtrack == 0 and window_progress >= float(rules["minimum_window_progress_m"])
        )
        path_pass = topology_valid and not detour_fail
        eligible = bool(spatial_pass and temporal_pass and path_pass)
        reasons = []
        if not topology_valid:
            reasons.append("topology_or_direction_invalid")
        if not spatial_pass:
            reasons.append("lateral_error_over_200m")
        if nonpositive_time:
            reasons.append("nonpositive_time_delta")
        if long_gaps:
            reasons.append("sample_gap_over_300s")
        if excessive_speed:
            reasons.append("along_route_speed_over_55mps")
        if excessive_backtrack:
            reasons.append("backtrack_over_20m")
        if window_progress < float(rules["minimum_window_progress_m"]):
            reasons.append("insufficient_signed_window_progress")
        if detour_fail:
            reasons.append("path_detour_ratio_and_excess")
        formula = _window_fftt(segment_points, segment_path, link_lookup)
        if not math.isfinite(float(formula["window_baseline_fftt_min"])) or float(formula["window_baseline_fftt_min"]) <= 0:
            eligible = False
            reasons.append("nonpositive_window_baseline_time")
        old_obs = old_obs_lookup.get(segment_id, {})
        full_fftt = float(old_obs.get("baseline_path_fftt_min", math.nan))
        first_occ = int(segment_points.iloc[0]["path_occurrence"])
        last_occ = int(segment_points.iloc[-1]["path_occurrence"])
        coverage_complete = bool(
            first_occ == 1 and last_occ == len(path_ids)
            and float(segment_points.iloc[0]["fraction"]) <= 0.05
            and float(segment_points.iloc[-1]["fraction"]) >= 0.95
        )
        quality_class = "qualified" if eligible else "anomalous" if reasons else "candidate"
        quality = {
            **base,
            "disposition": "selected_path_returned",
            "topology_valid": topology_valid,
            "wkt_direction_valid": direction_valid,
            "max_wkt_endpoint_direction_error_m": max(direction_errors, default=math.nan),
            "road_permission_status": "physical_match_allowed_links_only" if physical else "contains_disallowed_link",
            "coordinate_reference_system": "EPSG:32619 metric checks; source and published coordinates EPSG:4326",
            "spatial_quality": "pass_all_points_within_200m" if spatial_pass else "fail_lateral_error_over_200m",
            "temporal_quality": "pass_with_declared_backtrack_tolerance" if temporal_pass else "fail_temporal_or_progress_rule",
            "path_plausibility": "pass" if path_pass else "fail_topology_direction_or_detour",
            "observation_eligible": eligible,
            "quality_class": quality_class,
            "exclusion_reasons": ";".join(dict.fromkeys(reasons)),
            "point_count": len(segment_points),
            "path_occurrences": len(path_ids),
            "lateral_error_over_200m_points": outlier_points,
            "mean_lateral_error_m": float(pd.to_numeric(segment_points["lateral_error_m"]).mean()),
            "max_lateral_error_m": max_lateral,
            "backtrack_steps_over_1m": int((backtracks > 1.0).sum()),
            "backtrack_steps_over_5m": int((backtracks > 5.0).sum()),
            "backtrack_steps_over_20m": int((backtracks > 20.0).sum()),
            "backtrack_steps_over_50m": int((backtracks > 50.0).sum()),
            "max_backtrack_m": max_backtrack,
            "max_along_route_speed_mps": max_speed,
            "raw_max_adjacent_speed_mps": float(segment.max_derived_step_speed_mps),
            "nonpositive_time_steps": nonpositive_time,
            "sample_gaps_over_300s": long_gaps,
            "max_sample_gap_seconds": float(time_deltas.max()) if time_deltas.notna().any() else math.nan,
            "window_path_progress_m": window_progress,
            "raw_endpoint_displacement_m": raw_displacement,
            "path_to_displacement_ratio": detour_ratio,
            "path_excess_over_displacement_m": detour_excess,
            "stopped_at_point_count": sum(value == "STOPPED_AT" for value in status_values),
            "missing_current_status_points": sum(value == "missing" for value in status_values),
            "mean_acquisition_lag_seconds": float(np.nanmean(acquisition_lags)) if any(math.isfinite(x) for x in acquisition_lags) else math.nan,
            "max_acquisition_lag_seconds": float(np.nanmax(acquisition_lags)) if any(math.isfinite(x) for x in acquisition_lags) else math.nan,
            "first_path_occurrence": first_occ,
            "last_path_occurrence": last_occ,
            "first_fraction": float(segment_points.iloc[0]["fraction"]),
            "last_fraction": float(segment_points.iloc[-1]["fraction"]),
            "full_returned_path_fftt_min_legacy": full_fftt,
            "window_baseline_fftt_min": float(formula["window_baseline_fftt_min"]),
            "window_baseline_fraction_of_full_path": float(formula["window_baseline_fftt_min"]) / full_fftt if full_fftt > 0 else math.nan,
            "window_formula_status": formula["window_formula_status"],
            "full_path_covered_by_first_last_points": coverage_complete,
            "observed_duration_min": float(segment.duration_seconds) / 60.0,
            "duration_source": "MBTA updated_at first-to-last within saved capture segment",
            "start_time_original_timezone": str(segment.start_time),
            "end_time_original_timezone": str(segment.end_time),
            "start_censored": bool(segment.start_censored),
            "end_censored": bool(segment.end_censored),
        }
        quality_rows.append(quality)
        observation_rows.append({
            "run_id": run_id,
            "config_signature_sha256": signature,
            "observation_id": f"obs-window:{segment_id}",
            "segment_id": segment_id,
            "vehicle_observation_id": str(segment.vehicle_observation_id),
            "route_id": str(segment.route_id),
            "mode": "bus",
            "observed_duration_min": quality["observed_duration_min"],
            "window_baseline_fftt_min": quality["window_baseline_fftt_min"],
            "legacy_full_path_fftt_min": full_fftt,
            "window_path_progress_m": window_progress,
            "first_path_occurrence": first_occ,
            "last_path_occurrence": last_occ,
            "first_fraction": quality["first_fraction"],
            "last_fraction": quality["last_fraction"],
            "link_time_allocation": config["observation_window"]["link_time_allocation"],
            "stopped_at_point_count": quality["stopped_at_point_count"],
            "max_sample_gap_seconds": quality["max_sample_gap_seconds"],
            "missing_time_steps": nonpositive_time,
            "observation_eligible": eligible,
            "quality_class": quality_class,
            "exclusion_reasons": quality["exclusion_reasons"],
            "calibration_use": "eligible_for_corrected_development_diagnostic" if eligible else "excluded_by_predeclared_quality_rules",
        })

    quality_frame = pd.DataFrame(quality_rows)
    point_frame = pd.DataFrame(point_rows)
    observation_frame = pd.DataFrame(observation_rows)
    gps_out = TASK_ROOT / "database" / "observations" / "quality_runs" / run_id
    gps_out.mkdir(parents=True, exist_ok=True)
    quality_frame.to_csv(gps_out / "gps_segment_quality.csv", index=False)
    point_frame.to_csv(gps_out / "gps_point_progress.csv", index=False)
    observation_frame.to_csv(gps_out / "gps_observations_windowed.csv", index=False)
    counts = {
        "segments_total": int(len(quality_frame)),
        "not_selected": int(quality_frame["disposition"].eq("not_selected").sum()),
        "selected": int(quality_frame["matching_selection"].eq("selected_first_pass").sum()),
        "selected_route_failed": int(quality_frame["disposition"].eq("selected_route_failed").sum()),
        "selected_route_returned": int(quality_frame["route_returned"].eq(True).sum()),
        "topology_valid": int(quality_frame["topology_valid"].eq(True).sum()),
        "spatial_pass": int(quality_frame["spatial_quality"].eq("pass_all_points_within_200m").sum()),
        "temporal_pass": int(quality_frame["temporal_quality"].eq("pass_with_declared_backtrack_tolerance").sum()),
        "observation_eligible": int(quality_frame["observation_eligible"].eq(True).sum()),
        "quality_classes": quality_frame["quality_class"].value_counts().to_dict(),
        "matched_points": int(len(point_frame)),
        "points_lateral_error_over_200m": int((pd.to_numeric(point_frame["lateral_error_m"], errors="coerce") > 200).sum()),
        "segments_with_lateral_error_over_200m": int(quality_frame["lateral_error_over_200m_points"].fillna(0).astype(float).gt(0).sum()),
        "segments_with_backtrack_over_1m": int(quality_frame["backtrack_steps_over_1m"].fillna(0).astype(float).gt(0).sum()),
        "segments_with_backtrack_over_20m": int(quality_frame["backtrack_steps_over_20m"].fillna(0).astype(float).gt(0).sum()),
    }
    assert counts["segments_total"] == 235
    assert counts["not_selected"] == 205
    assert counts["selected"] == 30
    assert counts["selected_route_returned"] == 28
    assert counts["selected_route_failed"] == 2
    summary = {
        "run_id": run_id,
        "config_signature_sha256": signature,
        "built_at_utc": utc_now(),
        "source": "existing saved MBTA V3 bus-position snapshots and existing 30-segment route results",
        "no_rematching_performed": True,
        "counts": counts,
        "rules": rules,
        "raw_metadata": raw_summary,
        "denominator_note": "205 not selected, 2 selected route failures, and 28 returned paths are distinct states; 207 is not reported as one failure count.",
        "semantics": "route_returned and topology_valid do not imply observation_eligible; native fallback is evaluated by identical spatial and temporal rules.",
    }
    write_json(gps_out / "gps_quality_summary.json", summary)
    target = TASK_ROOT / "database" / "observations" / "CURRENT_QUALITY_RUN.json"
    write_json(target, {
        "selected_run_id": run_id,
        "config_signature_sha256": signature,
        "selected_at_utc": utc_now(),
        "path": f"database/observations/quality_runs/{run_id}",
        "legacy_match_tables_preserved": True,
    })
    write_json(TASK_ROOT / "reports" / "gps_quality_summary.json", summary)
    regression_id = "mbtav:089b572ce1c6ea25:s01"
    regression = quality_frame[quality_frame["segment_id"].eq(regression_id)].iloc[0].to_dict()
    regression_points = point_frame[
        point_frame["segment_id"].eq(regression_id)
        & point_frame["point_seq"].astype(int).isin([7, 8])
    ].sort_values("point_seq")
    if len(regression_points) != 2:
        raise RuntimeError("The fixed point 7-to-8 GPS regression pair is missing")
    point_7, point_8 = regression_points.iloc[0], regression_points.iloc[1]
    raw_7 = transform(forward.transform, Point(float(point_7["original_lon"]), float(point_7["original_lat"])))
    raw_8 = transform(forward.transform, Point(float(point_8["original_lon"]), float(point_8["original_lat"])))
    regression_transition = {
        "from_point_seq": 7,
        "to_point_seq": 8,
        "time_delta_seconds": float(point_8["time_delta_seconds"]),
        "along_route_delta_m": float(point_8["along_delta_m"]),
        "along_route_speed_mps": float(point_8["along_speed_mps"]),
        "raw_point_displacement_m": float(raw_7.distance(raw_8)),
        "from_path_occurrence": int(point_7["path_occurrence"]),
        "to_path_occurrence": int(point_8["path_occurrence"]),
        "from_lateral_error_m": float(point_7["lateral_error_m"]),
        "to_lateral_error_m": float(point_8["lateral_error_m"]),
    }
    transition_is_anomalous = bool(
        regression_transition["time_delta_seconds"] == 17.0
        and regression_transition["along_route_delta_m"] > 8000.0
        and regression_transition["along_route_speed_mps"] > float(rules["max_along_route_speed_mps"])
        and regression_transition["raw_point_displacement_m"] < 100.0
    )
    write_json(gps_out / "regression_17s_8km.json", {
        "expected": "not observation eligible",
        "actual_observation_eligible": bool(regression["observation_eligible"]),
        "fixed_point_7_to_8_transition": regression_transition,
        "segment": regression,
        "passed_regression": transition_is_anomalous and not bool(regression["observation_eligible"]),
    })
    return summary


def corrected_calibration(config: dict[str, Any], signature: str) -> dict[str, Any]:
    run_id = config["run_id"]
    gps_dir = TASK_ROOT / "database" / "observations" / "quality_runs" / run_id
    observations = pd.read_csv(gps_dir / "gps_observations_windowed.csv", keep_default_na=False)
    old_map = pd.read_csv(TASK_ROOT / "database" / "calibration" / "observation_parameter_map.csv", keep_default_na=False)
    split_lookup = {
        str(row.observation_id).replace("obs:", ""): str(row.split)
        for row in old_map.itertuples(index=False)
    }
    usable = observations[observations["observation_eligible"].astype(str).str.lower().eq("true")].copy()
    usable["split"] = usable["segment_id"].map(split_lookup).fillna("development_only_not_in_legacy_split")
    train = usable[usable["split"].eq("train")].copy()
    holdout = usable[usable["split"].eq("holdout")].copy()
    gamma = math.nan
    status = "NOT_ESTIMABLE"
    reason = "Fewer than two retained legacy-training segments after independent quality checks"
    results = []
    if len(train) >= 2:
        x = pd.to_numeric(train["window_baseline_fftt_min"]).to_numpy(float)
        y = pd.to_numeric(train["observed_duration_min"]).to_numpy(float)
        denominator = float(np.sum(x * x))
        if denominator > 0:
            gamma = max(float(np.sum(x * y) / denominator), 1e-9)
            status = "DEVELOPMENT_DIAGNOSTIC_NOT_INDEPENDENTLY_VALIDATED"
            reason = "Window-corrected fit uses the unchanged legacy split, but that holdout was already inspected in the prior run"
            for split_name, frame in (("train", train), ("holdout", holdout)):
                if frame.empty:
                    continue
                observed = pd.to_numeric(frame["observed_duration_min"]).to_numpy(float)
                baseline = pd.to_numeric(frame["window_baseline_fftt_min"]).to_numpy(float)
                for model, scale in (("window_baseline_gamma_1", 1.0), ("window_fitted_gamma", gamma)):
                    residual = observed - scale * baseline
                    results.append({
                        "run_id": run_id,
                        "config_signature_sha256": signature,
                        "split": split_name,
                        "model": model,
                        "gamma": scale,
                        "segments": len(frame),
                        "distinct_vehicle_groups": frame["vehicle_observation_id"].nunique(),
                        "mae_min": float(np.mean(np.abs(residual))),
                        "rmse_min": float(np.sqrt(np.mean(residual ** 2))),
                        "mean_error_min": float(np.mean(residual)),
                    })
    output = TASK_ROOT / "database" / "calibration" / "quality_runs" / run_id
    output.mkdir(parents=True, exist_ok=True)
    registry = pd.DataFrame([{
        "run_id": run_id,
        "config_signature_sha256": signature,
        "parameter_id": "bus_window_path_time_scale_gamma",
        "estimated_value": gamma if math.isfinite(gamma) else "",
        "status": status,
        "train_segments": len(train),
        "holdout_segments_retained": len(holdout),
        "legacy_split_reused": True,
        "entered_fw_or_forecast": False,
        "selection_used_fit_residual": False,
        "reason": reason,
        "identification_limit": "Combines traffic, dwell, signal, sampling and network mismatch; link time is allocated proportionally, not observed per link.",
    }])
    registry.to_csv(output / "parameter_registry.csv", index=False)
    usable[[
        "run_id", "config_signature_sha256", "observation_id", "segment_id",
        "vehicle_observation_id", "observed_duration_min", "window_baseline_fftt_min", "split",
    ]].to_csv(output / "observation_parameter_map.csv", index=False)
    pd.DataFrame(results).to_csv(output / "fit_and_holdout_results.csv", index=False)
    pointer = {
        "selected_run_id": run_id,
        "config_signature_sha256": signature,
        "status": status,
        "selected_at_utc": utc_now(),
        "path": f"database/calibration/quality_runs/{run_id}",
        "legacy_diagnostic_preserved_at": "database/calibration/*.csv and history/pre_boston_quality_r1_20260922",
        "use_in_assignment_or_forecast": False,
    }
    write_json(TASK_ROOT / "database" / "calibration" / "CURRENT_CALIBRATION_RUN.json", pointer)
    return {**pointer, "gamma": gamma if math.isfinite(gamma) else None, "train_segments": len(train), "holdout_segments": len(holdout)}


def time_alignment(config: dict[str, Any], signature: str) -> dict[str, Any]:
    run_id = config["run_id"]
    city = json.loads((TASK_ROOT / "config" / "city_config.yaml").read_text(encoding="utf-8"))
    clean = pd.read_csv(TASK_ROOT / "database" / "observations" / "gps_points_clean.csv")
    times_utc = pd.to_datetime(clean["timestamp"], utc=True, errors="coerce").dropna()
    tz = ZoneInfo(city["city"]["timezone"])
    gps_start_local = times_utc.min().to_pydatetime().astimezone(tz)
    gps_end_local = times_utc.max().to_pydatetime().astimezone(tz)
    scenario_date = datetime.fromisoformat(city["time"]["scenario_service_date"]).date()
    start_parts = [int(x) for x in city["time"]["local_start"].split(":")]
    end_parts = [int(x) for x in city["time"]["local_end"].split(":")]
    scenario_start = datetime(scenario_date.year, scenario_date.month, scenario_date.day, *start_parts, tzinfo=tz)
    scenario_end = datetime(scenario_date.year, scenario_date.month, scenario_date.day, *end_parts, tzinfo=tz)
    result = {
        "run_id": run_id,
        "config_signature_sha256": signature,
        "gps_observation_start_local": gps_start_local.isoformat(),
        "gps_observation_end_local": gps_end_local.isoformat(),
        "gps_observation_start_utc": times_utc.min().isoformat(),
        "gps_observation_end_utc": times_utc.max().isoformat(),
        "assignment_scenario_start_local": scenario_start.isoformat(),
        "assignment_scenario_end_local": scenario_end.isoformat(),
        "assignment_scenario_start_utc": scenario_start.astimezone(timezone.utc).isoformat(),
        "assignment_scenario_end_utc": scenario_end.astimezone(timezone.utc).isoformat(),
        "same_local_date": gps_start_local.date() == scenario_date,
        "time_of_day_overlap": max(gps_start_local.time(), scenario_start.time()) < min(gps_end_local.time(), scenario_end.time()),
        "aligned_for_assignment_calibration": False,
        "allowed_use": "GPS path-quality and window-method development diagnostic only",
        "reason": "The saved GPS capture is midday on 2026-09-21 local time; the engineering assignment window is 07:00-09:00 on 2026-09-22.",
        "network_source_version": city["network"]["network_version"],
        "network_source_commit_date": city["network"]["source_commit_date"],
        "execution_timezone_not_data_timezone": "Asia/Shanghai is the execution environment only and is not used as a Boston observation date.",
    }
    write_json(TASK_ROOT / "database" / "observations" / "quality_runs" / run_id / "time_alignment.json", result)
    write_json(TASK_ROOT / "reports" / "time_alignment.json", result)
    return result


def capacity_adapter(config: dict[str, Any], signature: str) -> dict[str, Any]:
    run_id = config["run_id"]
    cap = config["capacity_adapter"]
    links = pd.read_csv(TASK_ROOT / "database" / "network" / "matcher" / "link.csv", keep_default_na=False)
    source_capacity = pd.to_numeric(links["capacity"], errors="raise")
    lanes = pd.to_numeric(links["lanes"], errors="raise")
    plf = pd.to_numeric(links["vdf_plf"], errors="raise")
    period_hours = float(cap["capacity_period_hours"])
    effective = source_capacity * lanes * period_hours * plf
    stress = effective / float(cap["stress_divisor"])
    semantics = pd.DataFrame({
        "run_id": run_id,
        "config_signature_sha256": signature,
        "link_id": links["link_id"],
        "capacity_source": source_capacity,
        "capacity_source_unit": cap["source_capacity_unit"],
        "lanes_source": lanes,
        "lane_basis": cap["lane_basis"],
        "vdf_plf_source": plf,
        "capacity_period_hours": period_hours,
        "demand_period_hours": float(cap["demand_period_hours"]),
        "capacity_effective_baseline_period": effective,
        "capacity_effective_stress_period": stress,
        "effective_capacity_unit": "passenger_car_equivalents_per_two_hour_analysis_period",
        "vehicle_pce_assumption": float(cap["vehicle_pce_assumption"]),
        "conversion_formula": cap["effective_capacity_formula"],
        "source_fields_overwritten": False,
    })
    output = TASK_ROOT / "database" / "network" / "capacity_runs" / run_id
    output.mkdir(parents=True, exist_ok=True)
    semantics.to_csv(output / "link_capacity_semantics.csv", index=False)
    staging = TASK_ROOT / "staging" / "assignment" / run_id
    staging.mkdir(parents=True, exist_ok=True)
    adapted = links.copy()
    adapted["capacity_source"] = source_capacity
    adapted["capacity_source_unit"] = cap["source_capacity_unit"]
    adapted["capacity_effective"] = effective
    adapted["capacity_period_hours"] = period_hours
    adapted["demand_period_hours"] = float(cap["demand_period_hours"])
    adapted["lane_basis"] = cap["lane_basis"]
    adapted["capacity_conversion_note"] = cap["effective_capacity_formula"]
    adapted["capacity"] = effective
    adapted.to_csv(staging / "link.csv", index=False)
    shutil.copy2(TASK_ROOT / "staging" / "assignment" / "baseline" / "demand.csv", staging / "demand.csv")
    evidence = f"""# Capacity and period basis

Run: `{run_id}`  
Configuration SHA-256: `{signature}`

- The source `capacity`, `lanes`, `vdf_plf`, and `vdf_fftt` columns are unchanged in the canonical network table.
- The current GMNS link schema defines link `capacity` as saturation capacity in passenger-car equivalents per hour per lane: https://github.com/zephyr-data-specs/GMNS/blob/main/spec/link.schema.json
- The ASU TAPLite MPO guide documents period conversion as `capacity × lanes × period_hours × vdf_plf`: https://github.com/asu-trans-ai-lab/TAPLite4MPO/blob/main/USER_GUIDE_VOL2_MPO.md
- This fixed source snapshot provides no separate Boston configuration that overrides the GMNS per-hour/per-lane definition. All physical links have `vdf_plf=1`; that value is retained as an engineering assumption, not claimed as locally calibrated.
- The engineering demand is vehicle trips over 07:00–09:00, so the adapter uses a two-hour capacity. Drive vehicles are assumed to be 1.0 PCE for this single-class demonstration.
- Stress capacity is the baseline effective period capacity divided by 1.2. Both source-capacity V/C and model-effective-capacity V/C must be shown separately.
"""
    (output / "CAPACITY_BASIS.md").write_text(evidence, encoding="utf-8")
    summary = {
        "run_id": run_id,
        "config_signature_sha256": signature,
        "links": len(links),
        "source_capacity_unchanged": True,
        "all_vdf_plf_equal_one": bool(np.allclose(plf, 1.0)),
        "capacity_effective_baseline_min": float(effective.min()),
        "capacity_effective_baseline_max": float(effective.max()),
        "capacity_effective_stress_min": float(stress.min()),
        "capacity_effective_stress_max": float(stress.max()),
        "staging_path": staging.relative_to(TASK_ROOT).as_posix(),
        "assignment_rerun_required": True,
        "reason": "The existing solver input used two-hour trip demand against unexpanded per-hour/per-lane source capacity.",
    }
    write_json(output / "capacity_adapter_summary.json", summary)
    write_json(TASK_ROOT / "database" / "network" / "CURRENT_CAPACITY_RUN.json", {
        "selected_run_id": run_id,
        "config_signature_sha256": signature,
        "path": f"database/network/capacity_runs/{run_id}",
        "source_network_fields_preserved": True,
    })
    field_mapping_path = TASK_ROOT / "database" / "network" / "field_mapping.csv"
    field_mapping = pd.read_csv(field_mapping_path, keep_default_na=False)
    capacity_row = field_mapping["source_field"].eq("capacity") & field_mapping["table"].eq("link")
    if int(capacity_row.sum()) != 1:
        raise RuntimeError("Expected one link.capacity field-mapping row")
    field_mapping.loc[capacity_row, "unit"] = "passenger-car equivalent/hour/lane"
    field_mapping.loc[capacity_row, "basis"] = (
        "GMNS schema basis; canonical source value unchanged; assignment adapter expands lanes and two-hour period"
    )
    field_mapping.to_csv(field_mapping_path, index=False)
    attribute_path = TASK_ROOT / "database" / "network" / "attribute_provenance.csv"
    attribute = pd.read_csv(attribute_path, keep_default_na=False)
    attribute_capacity = attribute["attribute"].eq("capacity") & attribute["entity_table"].eq("link")
    if int(attribute_capacity.sum()) != 1:
        raise RuntimeError("Expected one link.capacity attribute-provenance row")
    attribute.loc[attribute_capacity, "unit"] = "passenger-car equivalent/hour/lane"
    attribute.loc[attribute_capacity, "method"] = (
        "identity; canonical value unchanged; see selected capacity adapter for period conversion"
    )
    attribute.to_csv(attribute_path, index=False)
    return summary


def zone_access_review(config: dict[str, Any], signature: str) -> dict[str, Any]:
    run_id = config["run_id"]
    thresholds = config["zone_access_review"]
    zones = pd.read_csv(TASK_ROOT / "database" / "zones" / "zone.csv", keep_default_na=False)
    zones = zones[zones["zone_level"].eq("fine")].copy()
    access = pd.read_csv(TASK_ROOT / "database" / "zones" / "zone_access.csv", keep_default_na=False)
    activity = pd.read_csv(TASK_ROOT / "database" / "activity" / "zone_activity.csv", keep_default_na=False)
    nodes = pd.read_csv(TASK_ROOT / "database" / "network" / "matcher" / "node.csv", dtype={"node_id": "string"}, keep_default_na=False)
    links = pd.read_csv(TASK_ROOT / "database" / "network" / "matcher" / "link.csv", dtype={"link_id": "string", "from_node_id": "string", "to_node_id": "string"}, keep_default_na=False)
    forward = Transformer.from_crs("EPSG:4326", "EPSG:32619", always_xy=True)
    node_lookup = nodes.set_index("node_id")
    zone_lookup = zones.set_index("zone_id")
    activity_lookup = activity.set_index("zone_id")
    graph = nx.DiGraph()
    graph.add_edges_from(zip(links["from_node_id"].astype(str), links["to_node_id"].astype(str)))
    largest_scc = max(nx.strongly_connected_components(graph), key=len)
    line_metrics = [transform(forward.transform, wkt.loads(value)) for value in links["geometry"]]
    rows = []
    for row in access.itertuples(index=False):
        zone = zone_lookup.loc[str(row.zone_id)]
        node = node_lookup.loc[str(row.access_node_id)]
        centroid = transform(forward.transform, Point(float(zone.centroid_lon), float(zone.centroid_lat)))
        node_point = transform(forward.transform, Point(float(node.x_coord), float(node.y_coord)))
        clipped = wkt.loads(str(zone.clipped_geometry_wkt))
        node_in_zone = bool(clipped.covers(Point(float(node.x_coord), float(node.y_coord))))
        nearest_road_distance = min(centroid.distance(line) for line in line_metrics)
        distance = float(row.access_distance_m)
        if distance > float(thresholds["high_priority_threshold_m"]):
            review = "high_priority_review_over_1km"
        elif distance > float(thresholds["review_threshold_m"]):
            review = "review_over_500m"
        else:
            review = "distance_below_500m_no_physical_access_claim"
        rows.append({
            "run_id": run_id,
            "config_signature_sha256": signature,
            "zone_id": str(row.zone_id),
            "access_node_id": str(row.access_node_id),
            "access_distance_m": distance,
            "recomputed_centroid_to_node_distance_m": float(centroid.distance(node_point)),
            "nearest_physical_road_geometry_distance_m": float(nearest_road_distance),
            "access_node_inside_clipped_zone": node_in_zone,
            "physical_nodes_in_zone": int(activity_lookup.loc[str(row.zone_id), "physical_node_count"]),
            "access_node_in_largest_strong_component": str(row.access_node_id) in largest_scc,
            "incident_in_links": int((links["to_node_id"].astype(str) == str(row.access_node_id)).sum()),
            "incident_out_links": int((links["from_node_id"].astype(str) == str(row.access_node_id)).sum()),
            "selection_method": str(row.selection_method),
            "review_status": review,
            "water_or_barrier_status": "unknown_no_land_water_or_barrier_layer",
            "pedestrian_or_access_mode_status": "not_verified_no_mode_specific_access_network",
            "ordinary_road_use_allowed": False,
            "gps_match_allowed": False,
            "model_use": "nonphysical_zone_access_only",
        })
    frame = pd.DataFrame(rows)
    output = TASK_ROOT / "database" / "zones" / "access_runs" / run_id
    output.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output / "zone_access_review.csv", index=False)
    summary = {
        "run_id": run_id,
        "config_signature_sha256": signature,
        "zones_reviewed": len(frame),
        "over_500m": int((frame["access_distance_m"] > 500).sum()),
        "over_1000m": int((frame["access_distance_m"] > 1000).sum()),
        "maximum_distance_m": float(frame["access_distance_m"].max()),
        "unique_access_nodes": int(frame["access_node_id"].nunique()),
        "long_access_with_zero_physical_nodes_in_zone": int(((frame["access_distance_m"] > 500) & (frame["physical_nodes_in_zone"] == 0)).sum()),
        "long_access_node_outside_zone": int(((frame["access_distance_m"] > 500) & ~frame["access_node_inside_clipped_zone"]).sum()),
        "all_access_nodes_in_largest_scc": bool(frame["access_node_in_largest_strong_component"].all()),
        "physical_access_verified": False,
        "reason": "No pedestrian network or land/water/barrier layer exists in the fixed inputs; long connectors remain review-required model access and are not claimed as traversable facilities.",
    }
    write_json(output / "zone_access_summary.json", summary)
    write_json(TASK_ROOT / "reports" / "zone_access_review.json", summary)
    write_json(TASK_ROOT / "database" / "zones" / "CURRENT_ACCESS_REVIEW.json", {
        "selected_run_id": run_id,
        "config_signature_sha256": signature,
        "path": f"database/zones/access_runs/{run_id}",
    })
    return summary


def main() -> int:
    config, signature = config_and_signature()
    run_id = config["run_id"]
    backup = backup_affected_files(run_id)
    hashes_before = raw_hashes()
    run_dir = TASK_ROOT / "corrections" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    gps = evaluate_gps_quality(config, signature, run_dir)
    calibration = corrected_calibration(config, signature)
    timing = time_alignment(config, signature)
    capacity = capacity_adapter(config, signature)
    access = zone_access_review(config, signature)
    hashes_after = raw_hashes()
    unchanged = hashes_before == hashes_after
    if not unchanged:
        raise RuntimeError("A raw input hash changed during the correction pass")
    manifest = {
        "run_id": run_id,
        "config_signature_sha256": signature,
        "created_at_utc": utc_now(),
        "selected": True,
        "scope": "quality re-evaluation and adapter correction only; no fetching and no rematching",
        "backup_path": backup.relative_to(TASK_ROOT).as_posix(),
        "raw_inputs_byte_unchanged": unchanged,
        "raw_input_sha256": hashes_after,
        "gps_quality": gps,
        "corrected_calibration": calibration,
        "time_alignment": timing,
        "capacity_adapter": capacity,
        "zone_access_review": access,
        "legacy_results_preserved": True,
        "grid2demand_execution_status": "not_used; demand remains local doubly-constrained gravity plus given mode shares",
    }
    write_json(run_dir / "run_manifest.json", manifest)
    write_json(TASK_ROOT / "corrections" / "CURRENT_CORRECTION_RUN.json", {
        "selected_run_id": run_id,
        "config_signature_sha256": signature,
        "path": f"corrections/{run_id}",
        "selected_at_utc": utc_now(),
    })
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
