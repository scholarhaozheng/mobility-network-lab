#!/usr/bin/env python3
"""Build the Central Boston real-activity layer and a separate demand prior.

This script is deliberately incremental.  It reads the unchanged H3 zones,
unchanged free-flow skim, and a privacy-minimised MassGIS parcel-assessment
slice.  It never edits the legacy network-proxy scenario and never runs traffic
assignment.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from pyproj import Transformer
from shapely import make_valid
from shapely.geometry import shape
from shapely.ops import transform
from shapely.strtree import STRtree
from shapely.wkt import loads as load_wkt


import os
TASK_ROOT = Path(os.environ.get("MCL_BOSTON_SOURCE_ROOT", Path(__file__).resolve().parents[1])).resolve()
RUN_ID = "boston_activity_prior_r1_20260922"
SCENARIO_ID = "activity_informed_massgis_assessment_50k_v1"
SOURCE_ID = "massgis_property_tax_parcels_feature_service_20260917"
NETWORK_ID = "mcl_boston_central"
NETWORK_VERSION = "gmns_plus_21_boston_116447ab_analysis_v1"
ANALYSIS_CRS = "EPSG:32619"
DAILY_TOTAL = 50_000.0
BETA_PER_MINUTE = 0.08
MODE_SHARES = {"drive": 0.55, "transit": 0.25, "walk": 0.15, "bike": 0.05}
AM_PEAK_SHARE = 0.12
DRIVE_OCCUPANCY = 1.2
BALANCE_TOLERANCE = 1e-7
BALANCE_MAX_ITERATIONS = 500


RAW_DIR = TASK_ROOT / "raw" / "activity" / RUN_ID / "massgis_property_tax_parcels"
RAW_PATH = RAW_DIR / "massgis_parcel_assessment_slice.geojsonl.gz"
ACTIVITY_DIR = TASK_ROOT / "database" / "activity" / "runs" / RUN_ID
DEMAND_DIR = TASK_ROOT / "database" / "demand" / "scenarios" / RUN_ID
REPORT_DIR = TASK_ROOT / "reports" / RUN_ID
PROVENANCE_DIR = TASK_ROOT / "provenance" / RUN_ID


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def classify_use(description: Any) -> tuple[str, str]:
    """Return a conservative activity group and the explicit rule label."""
    text = str(description or "").strip().lower()
    if not text:
        return "unknown", "missing_use_desc"
    if "mixed use" in text or text.startswith("mixed "):
        return "mixed", "use_desc_keyword_mixed"
    industrial = ("industrial", "manufactur", "warehouse", "research & development", "r&d")
    commercial = (
        "office", "retail", "commercial", "hotel", "motel", "restaurant", "store",
        "service", "theater", "cinema", "bank", "supermarket", "shopping", "parking",
        "garage", "whlsale", "wholesale",
    )
    institutional = (
        "school", "college", "university", "hospital", "medical", "government",
        "municipal", "public safety", "charitable", "church", "religious", "library",
        "museum", "cultural", "court", "fire station", "police",
    )
    residential = (
        "residential", "condominium", "condo", "cndo", "apartment", "single family",
        "two-family", "two family", "three-family", "three family", "multiple houses",
        "congregate housing", "boarding house", "rooming house", "dwelling",
    )
    open_other = (
        "open space", "vacant", "undevelopable", "developable land", "public land",
        "water", "cemetery", "park", "forest", "agricultural", "removed june",
    )
    if any(word in text for word in industrial):
        return "industrial", "use_desc_keyword_industrial"
    if any(word in text for word in commercial):
        return "commercial", "use_desc_keyword_commercial"
    if any(word in text for word in institutional):
        return "institutional", "use_desc_keyword_institutional"
    if any(word in text for word in residential):
        return "residential", "use_desc_keyword_residential"
    if any(word in text for word in open_other):
        return "open_or_nonactivity", "use_desc_keyword_open_or_nonactivity"
    return "unknown", "no_keyword_match_preserved"


def read_zones() -> tuple[pd.DataFrame, list[Any], STRtree]:
    zones = pd.read_csv(TASK_ROOT / "database" / "zones" / "zone.csv")
    zones = zones[zones["zone_level"].eq("fine")].copy().reset_index(drop=True)
    if len(zones) != 177 or zones["zone_id"].duplicated().any():
        raise RuntimeError("Expected exactly 177 unique fine H3 zones")
    transformer = Transformer.from_crs("EPSG:4326", ANALYSIS_CRS, always_xy=True)
    geoms = [transform(transformer.transform, load_wkt(value)) for value in zones["clipped_geometry_wkt"]]
    if any(geom.is_empty or geom.area <= 0 for geom in geoms):
        raise RuntimeError("A fine-zone clipped geometry is empty or has nonpositive area")
    return zones, geoms, STRtree(geoms)


def load_source_records() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, int]]:
    if not RAW_PATH.exists():
        raise FileNotFoundError(RAW_PATH)
    to_metric = Transformer.from_crs("EPSG:4326", ANALYSIS_CRS, always_xy=True)
    records: list[dict[str, Any]] = []
    parcels: dict[str, dict[str, Any]] = {}
    counters: Counter[str] = Counter()
    seen_features: set[str] = set()
    with gzip.open(RAW_PATH, "rt", encoding="utf-8") as stream:
        for line in stream:
            feature = json.loads(line)
            props = feature["properties"]
            feature_id = f"massgis:{props['GlobalID']}"
            if feature_id in seen_features:
                raise RuntimeError(f"Duplicate source GlobalID: {feature_id}")
            seen_features.add(feature_id)
            geom_wgs = make_valid(shape(feature["geometry"]))
            if geom_wgs.is_empty:
                counters["empty_source_geometry"] += 1
                continue
            geom_metric = transform(to_metric.transform, geom_wgs)
            if geom_metric.is_empty or geom_metric.area <= 0:
                counters["nonpositive_metric_geometry"] += 1
                continue
            geom_hash = hashlib.sha256(geom_wgs.wkb).hexdigest()[:16]
            city = str(props.get("CITY") or "UNKNOWN").strip().upper()
            loc_id = str(props.get("LOC_ID") or "").strip()
            fallback = str(props.get("MAP_PAR_ID") or props.get("PROP_ID") or props.get("OBJECTID"))
            base_id = f"{city}:{props.get('TOWN_ID')}:{loc_id or fallback}"
            parcel_id = f"massgis-parcel:{base_id}:{geom_hash}"
            use_group, use_rule = classify_use(props.get("USE_DESC"))
            record = {
                "source_feature_id": feature_id,
                "source_parcel_id": parcel_id,
                "source_global_id": str(props["GlobalID"]),
                "object_id": props.get("OBJECTID"),
                "loc_id": loc_id,
                "map_par_id": props.get("MAP_PAR_ID"),
                "poly_type": props.get("POLY_TYPE"),
                "town_id": props.get("TOWN_ID"),
                "prop_id": props.get("PROP_ID"),
                "fiscal_year": props.get("FY"),
                "use_code": props.get("USE_CODE"),
                "municipality": city,
                "year_built": props.get("YEAR_BUILT"),
                "official_bld_area_sqft": safe_float(props.get("BLD_AREA")),
                "official_units": safe_float(props.get("UNITS")),
                "official_res_area_sqft": safe_float(props.get("RES_AREA")),
                "stories_source_text": props.get("STORIES"),
                "use_desc": props.get("USE_DESC"),
                "derived_use_group": use_group,
                "use_group_rule": use_rule,
                "source_id": SOURCE_ID,
                "run_id": RUN_ID,
            }
            records.append(record)
            if parcel_id not in parcels:
                point = geom_wgs.representative_point()
                parcels[parcel_id] = {
                    "source_parcel_id": parcel_id,
                    "municipality": city,
                    "town_id": props.get("TOWN_ID"),
                    "loc_id": loc_id,
                    "map_par_id": props.get("MAP_PAR_ID"),
                    "geometry_hash": geom_hash,
                    "geometry_wkt_epsg4326": geom_wgs.wkt,
                    "representative_lon": point.x,
                    "representative_lat": point.y,
                    "source_geometry_area_m2": geom_metric.area,
                    "geom_metric": geom_metric,
                    "assessment_record_count": 0,
                }
            parcels[parcel_id]["assessment_record_count"] += 1
            counters[f"municipality_{city}"] += 1
            counters[f"use_group_{use_group}"] += 1
    counters["records_loaded"] = len(records)
    counters["unique_parcel_geometries"] = len(parcels)
    counters["stacked_assessment_records"] = len(records) - len(parcels)
    return records, parcels, dict(counters)


def build_overlay(
    zones: pd.DataFrame,
    zone_geoms: list[Any],
    zone_tree: STRtree,
    records: list[dict[str, Any]],
    parcels: dict[str, dict[str, Any]],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    parcel_crosswalk_rows: list[dict[str, Any]] = []
    parcel_overlay: dict[str, list[dict[str, Any]]] = {}
    max_inside_sum = 0.0
    min_total_sum = 1.0
    for parcel_id, parcel in parcels.items():
        geom = parcel["geom_metric"]
        full_area = float(parcel["source_geometry_area_m2"])
        parts: list[dict[str, Any]] = []
        for index in zone_tree.query(geom, predicate="intersects"):
            intersection_area = geom.intersection(zone_geoms[int(index)]).area
            if intersection_area <= 1e-8:
                continue
            parts.append(
                {
                    "source_parcel_id": parcel_id,
                    "zone_id": str(zones.iloc[int(index)]["zone_id"]),
                    "allocation_weight": intersection_area / full_area,
                    "intersection_area_m2": intersection_area,
                    "source_geometry_area_m2": full_area,
                    "allocation_scope": "inside_existing_core_h3",
                }
            )
        inside_sum = sum(part["allocation_weight"] for part in parts)
        if inside_sum > 1.0 + 1e-6:
            raise RuntimeError(f"Overlapping H3 allocation exceeds source area for {parcel_id}: {inside_sum}")
        outside_weight = max(0.0, 1.0 - inside_sum)
        outside_area = max(0.0, full_area - sum(part["intersection_area_m2"] for part in parts))
        parts.append(
            {
                "source_parcel_id": parcel_id,
                "zone_id": "outside:central_boston_core",
                "allocation_weight": outside_weight,
                "intersection_area_m2": outside_area,
                "source_geometry_area_m2": full_area,
                "allocation_scope": "outside_existing_core_h3_retained",
            }
        )
        primary = max((part for part in parts if part["zone_id"].startswith("h3r9:")), key=lambda x: x["intersection_area_m2"], default=None)
        parcel["primary_zone_id"] = primary["zone_id"] if primary else "outside:central_boston_core"
        parcel["inside_core_weight"] = inside_sum
        parcel_overlay[parcel_id] = parts
        parcel_crosswalk_rows.extend(parts)
        max_inside_sum = max(max_inside_sum, inside_sum)
        min_total_sum = min(min_total_sum, inside_sum + outside_weight)

    feature_crosswalk_rows: list[dict[str, Any]] = []
    for record in records:
        for part in parcel_overlay[record["source_parcel_id"]]:
            feature_crosswalk_rows.append(
                {
                    "source_feature_id": record["source_feature_id"],
                    "source_parcel_id": record["source_parcel_id"],
                    "zone_id": part["zone_id"],
                    "allocation_weight": part["allocation_weight"],
                    "intersection_area_m2": part["intersection_area_m2"],
                    "source_geometry_area_m2": part["source_geometry_area_m2"],
                    "allocation_scope": part["allocation_scope"],
                    "allocation_method": "parcel_polygon_area_overlay_epsg32619",
                    "source_id": SOURCE_ID,
                    "run_id": RUN_ID,
                    "network_id": NETWORK_ID,
                    "network_version": NETWORK_VERSION,
                }
            )

    parcel_rows = []
    for parcel in parcels.values():
        parcel_rows.append({key: value for key, value in parcel.items() if key != "geom_metric"})
    parcel_df = pd.DataFrame(parcel_rows)
    parcel_crosswalk = pd.DataFrame(parcel_crosswalk_rows)
    feature_crosswalk = pd.DataFrame(feature_crosswalk_rows)
    feature_sums = feature_crosswalk.groupby("source_feature_id")["allocation_weight"].sum()
    parcel_sums = parcel_crosswalk.groupby("source_parcel_id")["allocation_weight"].sum()
    quality = {
        "unique_parcel_geometries": len(parcel_df),
        "parcel_crosswalk_rows": len(parcel_crosswalk),
        "feature_crosswalk_rows": len(feature_crosswalk),
        "max_inside_core_weight": max_inside_sum,
        "minimum_inside_plus_outside_weight": min_total_sum,
        "parcel_weight_sum_max_abs_error": float((parcel_sums - 1.0).abs().max()),
        "feature_weight_sum_max_abs_error": float((feature_sums - 1.0).abs().max()),
        "parcel_area_conservation_max_abs_m2": float(
            parcel_crosswalk.assign(delta=lambda x: x["intersection_area_m2"] - x["source_geometry_area_m2"] * x["allocation_weight"])
            .groupby("source_parcel_id")["delta"].sum().abs().max()
        ),
        "outside_parcel_geometry_count": int((parcel_df["inside_core_weight"] < 1.0 - 1e-9).sum()),
    }
    if quality["feature_weight_sum_max_abs_error"] > 1e-8:
        raise RuntimeError("Feature-to-zone allocation weights do not conserve to one")
    return parcel_df, parcel_crosswalk, feature_crosswalk, quality


def aggregate_activity(
    zones: pd.DataFrame,
    records_df: pd.DataFrame,
    parcel_df: pd.DataFrame,
    parcel_crosswalk: pd.DataFrame,
    feature_crosswalk: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    inside_feature = feature_crosswalk[feature_crosswalk["zone_id"].str.startswith("h3r9:")].merge(
        records_df, on=["source_feature_id", "source_parcel_id"], how="left", validate="many_to_one"
    )
    inside_parcel = parcel_crosswalk[parcel_crosswalk["zone_id"].str.startswith("h3r9:")].copy()
    zone_index = pd.DataFrame({"zone_id": zones["zone_id"].astype(str)})

    parcel_fraction = inside_parcel.groupby("zone_id")["allocation_weight"].sum().rename("parcel_fractional_count")
    record_fraction = inside_feature.groupby("zone_id")["allocation_weight"].sum().rename("assessment_record_fractional_count")
    primary_counts = (
        parcel_df[parcel_df["primary_zone_id"].str.startswith("h3r9:")]
        .groupby("primary_zone_id").size().rename_axis("zone_id").rename("parcel_primary_count")
    )
    result = zone_index.join(parcel_fraction, on="zone_id").join(record_fraction, on="zone_id").join(primary_counts, on="zone_id")

    metrics = {
        "official_res_area_sqft_weighted": (
            inside_feature["derived_use_group"].eq("residential"), "official_res_area_sqft"
        ),
        "official_nonres_bld_area_sqft_weighted": (
            inside_feature["derived_use_group"].isin(["commercial", "industrial", "institutional", "mixed"]),
            "official_bld_area_sqft",
        ),
        "official_residential_units_weighted": (
            inside_feature["derived_use_group"].eq("residential"), "official_units"
        ),
    }
    for output_name, (mask, source_column) in metrics.items():
        subset = inside_feature.loc[mask].copy()
        valid = pd.to_numeric(subset[source_column], errors="coerce").notna()
        subset = subset.loc[valid].copy()
        subset["weighted_value"] = pd.to_numeric(subset[source_column], errors="coerce") * subset["allocation_weight"]
        values = subset.groupby("zone_id")["weighted_value"].sum().rename(output_name)
        coverage = subset.groupby("zone_id")["allocation_weight"].sum().rename(output_name + "_record_fractional_count")
        result = result.join(values, on="zone_id").join(coverage, on="zone_id")

    groups = ["residential", "commercial", "industrial", "institutional", "mixed", "open_or_nonactivity", "unknown"]
    for group in groups:
        values = (
            inside_feature.loc[inside_feature["derived_use_group"].eq(group)]
            .groupby("zone_id")["allocation_weight"].sum()
            .rename(f"{group}_record_fractional_count")
        )
        result = result.join(values, on="zone_id")

    count_columns = [column for column in result.columns if column.endswith("_count")]
    result[count_columns] = result[count_columns].fillna(0.0)
    result["source_coverage_status"] = np.where(
        result["parcel_fractional_count"].gt(0), "observed_source_features", "no_source_feature_intersection"
    )
    result["production_prior_metric"] = "official_RES_AREA_residential_records_area_weighted"
    result["attraction_prior_metric"] = "official_BLD_AREA_nonresidential_and_mixed_records_area_weighted"
    result["source_id"] = SOURCE_ID
    result["run_id"] = RUN_ID
    result["network_id"] = NETWORK_ID
    result["network_version"] = NETWORK_VERSION

    hierarchy = pd.read_csv(TASK_ROOT / "database" / "zones" / "zone_hierarchy.csv")
    parent = result.merge(
        hierarchy[["child_zone_id", "parent_zone_id"]], left_on="zone_id", right_on="child_zone_id", how="left", validate="one_to_one"
    )
    additive = [
        column for column in result.columns
        if column.endswith("_count") or column in {
            "official_res_area_sqft_weighted", "official_nonres_bld_area_sqft_weighted", "official_residential_units_weighted"
        }
    ]
    parent_activity = parent.groupby("parent_zone_id", as_index=False)[additive].sum(min_count=1)
    parent_activity["aggregation_method"] = "sum_from_existing_r9_zone_activity_no_fresh_r7_overlay"
    parent_activity["source_id"] = SOURCE_ID
    parent_activity["run_id"] = RUN_ID
    parent_activity["network_id"] = NETWORK_ID
    parent_activity["network_version"] = NETWORK_VERSION

    diagnostics = {
        "fine_zone_rows": len(result),
        "parent_zone_rows": len(parent_activity),
        "zones_with_source_features": int(result["parcel_fractional_count"].gt(0).sum()),
        "zones_without_source_features": int(result["parcel_fractional_count"].eq(0).sum()),
        "residential_area_sqft_inside_core": float(result["official_res_area_sqft_weighted"].sum(skipna=True)),
        "nonresidential_and_mixed_bld_area_sqft_inside_core": float(result["official_nonres_bld_area_sqft_weighted"].sum(skipna=True)),
        "residential_units_inside_core": float(result["official_residential_units_weighted"].sum(skipna=True)),
        "fine_parent_res_area_abs_difference": float(abs(
            result["official_res_area_sqft_weighted"].sum(skipna=True)
            - parent_activity["official_res_area_sqft_weighted"].sum(skipna=True)
        )),
        "fine_parent_nonres_area_abs_difference": float(abs(
            result["official_nonres_bld_area_sqft_weighted"].sum(skipna=True)
            - parent_activity["official_nonres_bld_area_sqft_weighted"].sum(skipna=True)
        )),
    }
    return result, parent_activity, diagnostics


def build_demand(activity: pd.DataFrame) -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    sys.path.insert(0, str(TASK_ROOT / "tools"))
    from city_database import _balance_gravity  # type: ignore

    zone_ids = activity["zone_id"].astype(str).tolist()
    production_raw = pd.to_numeric(activity["official_res_area_sqft_weighted"], errors="coerce").fillna(0).to_numpy(float)
    attraction_raw = pd.to_numeric(activity["official_nonres_bld_area_sqft_weighted"], errors="coerce").fillna(0).to_numpy(float)
    if production_raw.sum() <= 0 or attraction_raw.sum() <= 0:
        raise RuntimeError("Actual source produced no positive production or attraction prior")
    productions = production_raw / production_raw.sum() * DAILY_TOTAL
    attractions = attraction_raw / attraction_raw.sum() * DAILY_TOTAL

    access = pd.read_csv(
        TASK_ROOT / "database" / "zones" / "access_runs" / "boston_quality_r1_20260922" / "zone_access_review.csv",
        dtype={"access_node_id": "string"},
    )
    access_subset = access[["zone_id", "access_node_id", "access_distance_m", "review_status"]].copy()
    pa = pd.DataFrame(
        {
            "zone_id": zone_ids,
            "production_prior_raw_official_res_area_sqft": production_raw,
            "attraction_prior_raw_official_nonres_bld_area_sqft": attraction_raw,
            "productions_person_trips_daily": productions,
            "attractions_person_trips_daily": attractions,
            "trip_purpose": "all_purpose_activity_informed_scenario_not_observed_travel",
            "period": "daily",
            "unit": "person_trips_per_assumed_scenario_day",
            "model": "actual_assessment_area_prior_scaled_to_assumed_total",
            "daily_total_status": "ASSUMED_50000_NOT_CALIBRATED",
            "scenario_id": SCENARIO_ID,
            "run_id": RUN_ID,
            "source_id": SOURCE_ID,
            "status": "ACTIVITY_INFORMED_PRIOR_NOT_CALIBRATED",
            "network_id": NETWORK_ID,
            "network_version": NETWORK_VERSION,
        }
    ).merge(access_subset, on="zone_id", how="left", validate="one_to_one")

    skim_df = pd.read_csv(TASK_ROOT / "database" / "demand" / "skim.csv")
    order = {zone_id: i for i, zone_id in enumerate(zone_ids)}
    skims = np.full((len(zone_ids), len(zone_ids)), np.inf, dtype=float)
    for row in skim_df.itertuples(index=False):
        if str(row.o_zone_id) in order and str(row.d_zone_id) in order and bool(row.reachable):
            skims[order[str(row.o_zone_id)], order[str(row.d_zone_id)]] = float(row.impedance_min)
    friction = np.exp(-BETA_PER_MINUTE * skims)
    friction[~np.isfinite(skims)] = 0.0
    matrix, iterations, balance_error = _balance_gravity(
        productions, attractions, friction, BALANCE_TOLERANCE, BALANCE_MAX_ITERATIONS
    )

    od_rows: list[dict[str, Any]] = []
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
                    "friction_function": "exp(-beta*minutes)",
                    "beta_per_minute": BETA_PER_MINUTE,
                    "beta_status": "ASSUMED_PRESERVED_FOR_SCENARIO_ISOLATION",
                    "scenario_id": SCENARIO_ID,
                    "run_id": RUN_ID,
                    "source_id": SOURCE_ID,
                    "status": "ACTIVITY_INFORMED_PRIOR_NOT_CALIBRATED",
                    "unit": "person_trips_per_assumed_scenario_day",
                    "network_id": NETWORK_ID,
                    "network_version": NETWORK_VERSION,
                }
            )
    od = pd.DataFrame(od_rows)
    mode_share_rows: list[dict[str, Any]] = []
    mode_period_rows: list[dict[str, Any]] = []
    for row in od.itertuples(index=False):
        for mode, share in MODE_SHARES.items():
            mode_share_rows.append(
                {
                    "o_zone_id": row.o_zone_id,
                    "d_zone_id": row.d_zone_id,
                    "mode": mode,
                    "mode_share": share,
                    "method": "given_share_preserved_for_scenario_isolation",
                    "scenario_id": SCENARIO_ID,
                    "run_id": RUN_ID,
                    "status": "GIVEN_SHARE_NOT_CALIBRATED",
                }
            )
            daily_mode = float(row.person_trips_daily) * share
            mode_period_rows.append(
                {
                    "o_zone_id": row.o_zone_id,
                    "d_zone_id": row.d_zone_id,
                    "mode": mode,
                    "period": "AM_0700_0800",
                    "daily_person_trips": daily_mode,
                    "period_share": AM_PEAK_SHARE,
                    "person_trips": daily_mode * AM_PEAK_SHARE,
                    "unit": "person_trips_per_assumed_analysis_period",
                    "assignment_status": "ready_for_drive_assignment" if mode == "drive" else "not_assigned_no_complete_mode_network",
                    "scenario_id": SCENARIO_ID,
                    "run_id": RUN_ID,
                    "period_share_status": "ASSUMED_NOT_CALIBRATED",
                }
            )
    mode_share = pd.DataFrame(mode_share_rows)
    mode_period = pd.DataFrame(mode_period_rows)
    drive = mode_period[mode_period["mode"].eq("drive")].copy()
    drive["vehicle_trips"] = drive["person_trips"] / DRIVE_OCCUPANCY
    drive["persons_per_vehicle"] = DRIVE_OCCUPANCY
    drive["unit"] = "vehicle_trips_per_assumed_analysis_period"
    drive["conversion_method"] = "given_average_occupancy_not_calibrated"

    origin_access = access_subset.rename(
        columns={
            "zone_id": "o_zone_id", "access_node_id": "o_node_id",
            "access_distance_m": "o_access_distance_m", "review_status": "o_access_review_status",
        }
    )
    destination_access = access_subset.rename(
        columns={
            "zone_id": "d_zone_id", "access_node_id": "d_node_id",
            "access_distance_m": "d_access_distance_m", "review_status": "d_access_review_status",
        }
    )
    assignment = drive.merge(origin_access, on="o_zone_id", how="left", validate="many_to_one").merge(
        destination_access, on="d_zone_id", how="left", validate="many_to_one"
    )
    assignment["assignment_eligibility"] = np.where(
        assignment["o_node_id"].eq(assignment["d_node_id"]),
        "unassigned_same_access_node_or_intrazonal",
        "assignment_input",
    )
    solver = (
        assignment[assignment["assignment_eligibility"].eq("assignment_input")]
        .groupby(["o_node_id", "d_node_id"], as_index=False)["vehicle_trips"].sum()
        .rename(columns={"o_node_id": "o_zone_id", "d_node_id": "d_zone_id", "vehicle_trips": "volume"})
    )
    solver["scenario_id"] = SCENARIO_ID
    solver["run_id"] = RUN_ID
    solver["status"] = "ASSIGNMENT_INPUT_READY_NOT_RUN"

    old_pa = pd.read_csv(TASK_ROOT / "database" / "demand" / "productions_attractions.csv")
    zone_comparison = old_pa[[
        "zone_id", "production_proxy_raw", "attraction_proxy_raw",
        "productions_person_trips_daily", "attractions_person_trips_daily", "scenario_id",
    ]].rename(columns={
        "production_proxy_raw": "old_network_proxy_production_raw",
        "attraction_proxy_raw": "old_network_proxy_attraction_raw",
        "productions_person_trips_daily": "old_productions_person_trips_daily",
        "attractions_person_trips_daily": "old_attractions_person_trips_daily",
        "scenario_id": "old_scenario_id",
    }).merge(
        pa[[
            "zone_id", "production_prior_raw_official_res_area_sqft",
            "attraction_prior_raw_official_nonres_bld_area_sqft",
            "productions_person_trips_daily", "attractions_person_trips_daily", "scenario_id",
        ]].rename(columns={
            "productions_person_trips_daily": "new_productions_person_trips_daily",
            "attractions_person_trips_daily": "new_attractions_person_trips_daily",
            "scenario_id": "new_scenario_id",
        }), on="zone_id", how="outer", validate="one_to_one"
    )
    zone_comparison["production_daily_difference_new_minus_old"] = (
        zone_comparison["new_productions_person_trips_daily"] - zone_comparison["old_productions_person_trips_daily"]
    )
    zone_comparison["attraction_daily_difference_new_minus_old"] = (
        zone_comparison["new_attractions_person_trips_daily"] - zone_comparison["old_attractions_person_trips_daily"]
    )
    zone_comparison["interpretation"] = "scenario_difference_not_accuracy_or_validation"

    old_od = pd.read_csv(TASK_ROOT / "database" / "demand" / "od_person.csv")
    od_comparison = old_od[["o_zone_id", "d_zone_id", "person_trips_daily"]].rename(
        columns={"person_trips_daily": "old_network_proxy_person_trips_daily"}
    ).merge(
        od[["o_zone_id", "d_zone_id", "person_trips_daily"]].rename(
            columns={"person_trips_daily": "new_activity_prior_person_trips_daily"}
        ), on=["o_zone_id", "d_zone_id"], how="outer", validate="one_to_one"
    ).fillna({"old_network_proxy_person_trips_daily": 0.0, "new_activity_prior_person_trips_daily": 0.0})
    od_comparison["person_trip_difference_new_minus_old"] = (
        od_comparison["new_activity_prior_person_trips_daily"] - od_comparison["old_network_proxy_person_trips_daily"]
    )
    od_comparison["interpretation"] = "scenario_difference_not_accuracy_or_validation"

    outputs = {
        "productions_attractions": pa,
        "od_person": od,
        "mode_share": mode_share,
        "od_mode_period": mode_period,
        "od_vehicle_period": drive,
        "assignment_od_crosswalk": assignment,
        "solver_demand": solver,
        "zone_activity_prior_comparison": zone_comparison,
        "od_prior_comparison": od_comparison,
    }
    summary = {
        "run_id": RUN_ID,
        "scenario_id": SCENARIO_ID,
        "built_at_utc": utc_now(),
        "actual_activity_source": SOURCE_ID,
        "production_prior": "official MassGIS RES_AREA for assessment records classified residential",
        "attraction_prior": "official MassGIS BLD_AREA for records classified commercial, industrial, institutional, or mixed",
        "not_network_proxy_fields": [
            "production_prior_raw_official_res_area_sqft",
            "attraction_prior_raw_official_nonres_bld_area_sqft",
        ],
        "preserved_assumptions": {
            "daily_person_trip_total": DAILY_TOTAL,
            "beta_per_minute": BETA_PER_MINUTE,
            "mode_shares": MODE_SHARES,
            "am_peak_share_of_daily": AM_PEAK_SHARE,
            "drive_persons_per_vehicle": DRIVE_OCCUPANCY,
        },
        "daily_productions": float(productions.sum()),
        "daily_attractions": float(attractions.sum()),
        "distributed_person_trips": float(matrix.sum()),
        "gravity_balance_iterations": iterations,
        "gravity_relative_max_margin_error": balance_error,
        "am_peak_all_mode_person_trips": float(mode_period["person_trips"].sum()),
        "am_peak_drive_person_trips": float(drive["person_trips"].sum()),
        "am_peak_drive_vehicle_trips": float(drive["vehicle_trips"].sum()),
        "assignment_input_vehicle_trips": float(solver["volume"].sum()),
        "unassigned_same_access_or_intrazonal_vehicle_trips": float(
            assignment.loc[assignment["assignment_eligibility"].ne("assignment_input"), "vehicle_trips"].sum()
        ),
        "assignment_run": False,
        "gps_gamma_fit": False,
        "interpretation": "Activity-informed prior and isolated scenario comparison; not calibrated or validated travel demand.",
    }
    return outputs, summary


def write_provenance(source_counts: dict[str, int]) -> None:
    source_manifest = json.loads((RAW_DIR / "source_manifest.json").read_text(encoding="utf-8"))
    source_register = pd.DataFrame([
        {
            "source_id": SOURCE_ID,
            "provider": source_manifest["provider"],
            "dataset": "MassGIS Property Tax Parcels - privacy-minimised parcel-assessment slice",
            "official_landing_page": source_manifest["official_landing_page"],
            "official_service_url": source_manifest["official_service_url"],
            "source_item_id": source_manifest["service_item_id"],
            "downloaded_at_utc": source_manifest["downloaded_at_utc"],
            "source_data_last_edit_epoch_ms": source_manifest["source_data_last_edit_epoch_ms"],
            "fiscal_year_coverage": "Boston FY2023; Cambridge FY2026; a small number of null FY rows retained",
            "source_crs": "ArcGIS service EPSG:3857; requested GeoJSON EPSG:4326",
            "analysis_crs": ANALYSIS_CRS,
            "terms_or_license": "Official public MassGIS service; see landing page for use and maintenance notes",
            "local_raw_path": str(RAW_PATH.relative_to(TASK_ROOT)),
            "sha256": sha256(RAW_PATH),
            "records": source_counts["records_loaded"],
            "privacy_scope": "No owner, mailing, contact, site-address, or registry fields requested",
            "status": "acquired_and_used",
        },
        {
            "source_id": "us_census_lodes8_ma_2023_not_acquired",
            "provider": "U.S. Census Bureau LEHD",
            "dataset": "LODES8 Massachusetts WAC/RAC/OD 2023",
            "official_landing_page": "https://lehd.ces.census.gov/data/lodes/LODES8/ma/",
            "official_service_url": "https://lehd.ces.census.gov/data/lodes/LODES8/ma/",
            "source_item_id": "not_applicable",
            "downloaded_at_utc": "",
            "source_data_last_edit_epoch_ms": "",
            "fiscal_year_coverage": "2023 files listed by official index but not acquired",
            "source_crs": "Census block identifiers; no spatial file acquired",
            "analysis_crs": "not_applicable",
            "terms_or_license": "U.S. Census Bureau public data; technical documentation linked in status record",
            "local_raw_path": "",
            "sha256": "",
            "records": 0,
            "privacy_scope": "No LODES microdata or file acquired",
            "status": "not_acquired_official_host_timed_out_after_bounded_attempts",
        },
    ])
    source_register.to_csv(PROVENANCE_DIR / "DATA_SOURCE_REGISTER.csv", index=False)
    write_json(PROVENANCE_DIR / "lodes_acquisition_status.json", {
        "checked_at_utc": utc_now(),
        "status": "not_acquired_official_host_unreachable_from_runtime_after_bounded_attempts",
        "official_index": "https://lehd.ces.census.gov/data/lodes/LODES8/ma/",
        "attempted_files": [
            "https://lehd.ces.census.gov/data/lodes/LODES8/ma/ma_wac_S000_JT00_2023.csv.gz",
            "https://lehd.ces.census.gov/data/lodes/LODES8/ma/ma_rac_S000_JT00_2023.csv.gz",
            "https://lehd.ces.census.gov/data/lodes/LODES8/ma/ma_od_main_JT00_2023.csv.gz",
            "https://lehd.ces.census.gov/data/lodes/LODES8/ma/ma_xwalk.csv.gz",
        ],
        "bounded_attempts": [
            "sandbox curl request timed out",
            "approved unrestricted curl request retried three times with 20-second connection/operation bounds and timed out",
        ],
        "semantic_note": {
            "WAC": "jobs tabulated by workplace census block",
            "RAC": "jobs tabulated by worker residence census block",
            "OD": "home-to-work job associations between residence and workplace blocks",
            "scope_warning": "LODES is not an all-purpose travel demand source and must not be represented as one.",
        },
        "effect_on_this_run": "No LODES value is used. Employment association remains unavailable; MassGIS assessment activity alone informs the new prior.",
        "open_item": "Acquire official LODES8 MA WAC/RAC/OD and crosswalk in a network environment that can reach lehd.ces.census.gov, then build a separate employment-association extension without overwriting this run.",
    })
    write_json(PROVENANCE_DIR / "capacity_source_evidence_status.json", {
        "status": "engineering_interpretation_not_dataset_snapshot_unit_proof",
        "finding": "The Boston source snapshot contains link.csv and repository metadata but no Boston-specific capacity settings file proving the period or PCE convention.",
        "supporting_context": [
            "The GMNS schema defines saturation capacity in pce/hour/lane.",
            "The GMNS Plus repository describes capacity as consistent with expected per-lane capacity.",
            "Neither statement proves that every Boston snapshot value was authored in that exact unit and period convention.",
        ],
        "current_adapter_interpretation": "Treat source capacity as pce/hour/lane, use source lanes and vdf_plf=1.0, and assume passenger-car PCE=1 for the existing engineering run.",
        "effect_on_previous_outputs": "No previous file is rewritten. This note narrows the evidence claim for receiver review.",
        "open_item": "Obtain dataset-author confirmation or Boston-generation configuration that explicitly states the source capacity unit and period convention.",
    })


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default=RUN_ID)
    args = parser.parse_args()
    if args.run_id != RUN_ID:
        raise ValueError(f"This immutable script build is pinned to run id {RUN_ID}")
    for directory in (ACTIVITY_DIR, DEMAND_DIR, REPORT_DIR, PROVENANCE_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    zones, zone_geoms, zone_tree = read_zones()
    records, parcels, source_counts = load_source_records()
    records_df = pd.DataFrame(records)
    parcel_df, parcel_crosswalk, feature_crosswalk, overlay_quality = build_overlay(
        zones, zone_geoms, zone_tree, records, parcels
    )
    activity, parent_activity, activity_quality = aggregate_activity(
        zones, records_df, parcel_df, parcel_crosswalk, feature_crosswalk
    )

    records_df.to_csv(ACTIVITY_DIR / "assessment_records.csv", index=False)
    parcel_df.to_csv(ACTIVITY_DIR / "parcel_geometries.csv", index=False)
    parcel_crosswalk.assign(
        allocation_method="parcel_polygon_area_overlay_epsg32619", source_id=SOURCE_ID, run_id=RUN_ID
    ).to_csv(ACTIVITY_DIR / "parcel_zone_crosswalk.csv", index=False)
    feature_crosswalk.to_csv(ACTIVITY_DIR / "assessment_feature_zone_crosswalk.csv", index=False)
    activity.to_csv(ACTIVITY_DIR / "zone_activity_r9.csv", index=False)
    parent_activity.to_csv(ACTIVITY_DIR / "zone_activity_r7_from_r9.csv", index=False)

    demand_outputs, demand_summary = build_demand(activity)
    for name, table in demand_outputs.items():
        table.to_csv(DEMAND_DIR / f"{name}.csv", index=False)
    write_json(DEMAND_DIR / "demand_prior_summary.json", demand_summary)
    write_json(DEMAND_DIR / "scenario_manifest.json", {
        "run_id": RUN_ID,
        "scenario_id": SCENARIO_ID,
        "created_at_utc": utc_now(),
        "old_scenario_preserved_at": "database/demand",
        "new_scenario_directory": str(DEMAND_DIR.relative_to(TASK_ROOT)),
        "actual_activity_source": SOURCE_ID,
        "spatial_allocation": "Exact parcel-polygon intersection with existing clipped r9 H3 zones in EPSG:32619; outside weight retained; r7 sums derived only from r9.",
        "assumption_status": "50,000 daily trips, beta, mode shares, AM share, and occupancy remain explicit uncalibrated assumptions.",
        "execution_scope": "Demand prior and assignment-ready input only; traffic assignment not run; GPS not touched.",
    })
    write_provenance(source_counts)

    prohibited = [column for column in records_df.columns if any(term in column.lower() for term in ("owner", "mail", "contact", "address"))]
    if prohibited:
        raise RuntimeError(f"Privacy-prohibited public columns found: {prohibited}")
    quality = {
        "run_id": RUN_ID,
        "built_at_utc": utc_now(),
        "source_counts": source_counts,
        "overlay": overlay_quality,
        "activity": activity_quality,
        "privacy": {
            "prohibited_owner_mail_contact_address_columns": prohibited,
            "raw_selected_fields_file": str((RAW_DIR / "selected_field_dictionary.csv").relative_to(TASK_ROOT)),
        },
        "demand": demand_summary,
        "assertions": {
            "fine_zone_count_177": len(activity) == 177,
            "feature_allocation_conserved": overlay_quality["feature_weight_sum_max_abs_error"] <= 1e-8,
            "r7_derived_from_r9": True,
            "old_scenario_not_overwritten": (TASK_ROOT / "database" / "demand" / "productions_attractions.csv").exists(),
            "assignment_not_run": True,
            "gps_not_touched": True,
        },
    }
    if not all(quality["assertions"].values()):
        raise RuntimeError(f"Quality assertion failed: {quality['assertions']}")
    write_json(REPORT_DIR / "activity_demand_quality_report.json", quality)

    output_files = sorted(
        [path for root in (ACTIVITY_DIR, DEMAND_DIR, REPORT_DIR, PROVENANCE_DIR) for path in root.rglob("*") if path.is_file()]
    )
    manifest_rows = []
    for path in output_files:
        manifest_rows.append({
            "path": str(path.relative_to(TASK_ROOT)).replace("\\", "/"),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "run_id": RUN_ID,
        })
    pd.DataFrame(manifest_rows).to_csv(REPORT_DIR / "output_manifest.csv", index=False)
    print(json.dumps({
        "run_id": RUN_ID,
        "assessment_records": len(records_df),
        "unique_parcel_geometries": len(parcel_df),
        "fine_zones": len(activity),
        "demand_od_rows": len(demand_outputs["od_person"]),
        "quality_report": str(REPORT_DIR / "activity_demand_quality_report.json"),
    }, indent=2))


if __name__ == "__main__":
    main()
