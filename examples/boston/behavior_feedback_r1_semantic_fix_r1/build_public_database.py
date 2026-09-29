#!/usr/bin/env python3
"""Build the Central Boston public SQLite database from packaged CSV files."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def value_type(value: str) -> str:
    if value == "":
        return "EMPTY"
    try:
        int(value)
        return "INTEGER"
    except ValueError:
        pass
    try:
        float(value)
        return "REAL"
    except ValueError:
        return "TEXT"


def identifier_like(name: str) -> bool:
    """Fields whose lexical representation is part of their identity."""
    lowered = name.lower()
    return (
        lowered.endswith("_id")
        or lowered.endswith("_code")
        or lowered in {"id", "geoid", "fips", "h3", "use_code", "stop_code", "zip", "zipcode", "postal_code"}
        or "geoid" in lowered
        or "fips" in lowered
        or lowered.startswith("h3_")
    )


def infer_types(path: Path, sample_rows: int = 2000) -> tuple[list[str], list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise RuntimeError(f"Missing CSV header: {path}")
        names = list(reader.fieldnames)
        seen = {name: set() for name in names}
        for index, row in enumerate(reader):
            for name in names:
                seen[name].add(value_type(row.get(name, "")))
            if index + 1 >= sample_rows:
                break
    types = []
    for name in names:
        if identifier_like(name):
            types.append("TEXT")
            continue
        kinds = seen[name] - {"EMPTY"}
        if not kinds:
            types.append("TEXT")
        elif "TEXT" in kinds:
            types.append("TEXT")
        elif "REAL" in kinds:
            types.append("REAL")
        else:
            types.append("INTEGER")
    return names, types


def convert(value: str, kind: str):
    if value == "":
        return None
    if kind == "INTEGER":
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                # SQLite permits mixed storage classes. Keep late alphanumeric
                # identifiers instead of failing when the bounded type sample
                # saw only numeric-looking values.
                return value
    if kind == "REAL":
        try:
            return float(value)
        except ValueError:
            return value
    return value


def load_csv(connection: sqlite3.Connection, table: str, path: Path) -> int:
    names, types = infer_types(path)
    columns = ",".join(f"{quote(name)} {kind}" for name, kind in zip(names, types))
    connection.execute(f"DROP TABLE IF EXISTS {quote(table)}")
    connection.execute(f"CREATE TABLE {quote(table)} ({columns})")
    placeholders = ",".join("?" for _ in names)
    insert = f"INSERT INTO {quote(table)} VALUES ({placeholders})"
    total = 0
    batch = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            batch.append(tuple(convert(row.get(name, ""), kind) for name, kind in zip(names, types)))
            if len(batch) >= 5000:
                connection.executemany(insert, batch)
                total += len(batch)
                batch.clear()
        if batch:
            connection.executemany(insert, batch)
            total += len(batch)
    return total


def main() -> int:
    component_root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=component_root / "boston_central_public.sqlite",
        help="Output SQLite path (default: beside this script)",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=component_root / "data" / "public_table_manifest.csv",
        help="Packaged table manifest",
    )
    args = parser.parse_args()
    manifest_path = args.manifest.resolve()
    root = manifest_path.parent.parent
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".building.sqlite")
    if temporary.exists():
        temporary.unlink()
    connection = sqlite3.connect(temporary)
    connection.execute("PRAGMA journal_mode=DELETE")
    connection.execute("PRAGMA synchronous=NORMAL")
    loaded = []
    with manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
        for item in csv.DictReader(handle):
            source = (root / item["source_file"]).resolve()
            if root not in source.parents:
                raise RuntimeError(f"Manifest path escapes component root: {source}")
            if not source.exists():
                raise FileNotFoundError(source)
            rows = load_csv(connection, item["table_name"], source)
            expected = int(item["expected_rows"])
            if rows != expected:
                raise RuntimeError(f"{item['table_name']}: loaded {rows}, expected {expected}")
            loaded.append((item["table_name"], item["source_file"], rows))
    connection.execute(
        "CREATE TABLE public_build_manifest(table_name TEXT, source_file TEXT, row_count INTEGER)"
    )
    connection.executemany("INSERT INTO public_build_manifest VALUES (?,?,?)", loaded)
    indexes = {
        "physical_network_node": ["node_id"],
        "physical_network_link": ["link_id", "from_node_id", "to_node_id"],
        "assignment_baseline_corrected": ["link_id"],
        "assignment_stress_corrected": ["link_id"],
        "zone_model_summary": ["zone_id"],
        "zone_access_review": ["zone_id", "access_node_id"],
        "od_person": ["o_zone_id", "d_zone_id"],
        "od_mode_period": ["o_zone_id", "d_zone_id", "mode", "period"],
        "od_vehicle_period": ["o_zone_id", "d_zone_id", "mode", "period"],
        "assignment_od_crosswalk": ["o_zone_id", "d_zone_id", "o_node_id", "d_node_id"],
        "gps_segment_quality": ["segment_id", "quality_class"],
        "gps_point_progress": ["segment_id", "point_seq", "matched_link_id"],
        "gps_path_links": ["segment_id", "path_order", "link_id"],
        "transit_stop_route_relation": ["stop_id", "route_id"],
        "source_registry": ["source_id"],
        "parameter_registry": ["parameter_id", "model_id", "source_id"],
        "zonal_population_households": ["zone_id"],
        "trip_generation_by_purpose": ["zone_id", "purpose"],
        "validation_panel": ["od_id", "o_zone_id", "d_zone_id"],
        "od_multimodal_skims": ["od_id", "scenario_id", "mode", "departure_time"],
        "itinerary_legs": ["path_id", "leg_sequence", "trip_id", "route_id"],
        "transit_observations": ["observation_id", "segment_id", "trip_id"],
        "service_overlay": ["parameter_id", "route_id", "direction_id"],
        "od_mode_probabilities": ["od_id", "scenario_id", "mode"],
        "person_to_vehicle_crosswalk": ["od_id", "scenario_id", "mode"],
        "assignment_result_by_scenario": ["link_id"],
        "feedback_trace": ["trace_id", "observation_id", "overlay_parameter_id", "od_id", "assignment_link_id"],
        "feedback_scenario_registry": ["scenario_id", "parent_scenario_id"],
        "readiness": ["readiness_area"],
    }
    existing = {row[0] for row in connection.execute("SELECT table_name FROM public_build_manifest")}
    for table, columns in indexes.items():
        if table not in existing:
            continue
        actual = {row[1] for row in connection.execute(f"PRAGMA table_info({quote(table)})")}
        for column in columns:
            if column in actual:
                connection.execute(
                    f"CREATE INDEX {quote('idx_' + table + '_' + column)} "
                    f"ON {quote(table)}({quote(column)})"
                )
    unique_keys = {
        "source_registry": ["source_id"],
        "parameter_registry": ["parameter_id"],
        "zonal_population_households": ["zone_id"],
        "trip_generation_by_purpose": ["zone_id", "purpose"],
        "validation_panel": ["od_id"],
        "od_multimodal_skims": ["od_id", "departure_time", "scenario_id", "mode"],
        "itinerary_legs": ["scenario_id", "path_id", "leg_sequence"],
        "transit_observations": ["observation_id"],
        "service_overlay": ["parameter_id"],
        "od_mode_probabilities": ["od_id", "departure_time", "scenario_id", "mu_transit_sensitivity", "mode"],
        "feedback_trace": ["trace_id"],
        "feedback_scenario_registry": ["scenario_id"],
        "readiness": ["readiness_area"],
    }
    for table, columns in unique_keys.items():
        if table in existing:
            cols = ",".join(quote(x) for x in columns)
            connection.execute(f"CREATE UNIQUE INDEX {quote('uq_' + table)} ON {quote(table)}({cols})")
    if {"od_multimodal_skims", "od_mode_probabilities"} <= existing:
        connection.execute(
            "CREATE VIEW scenario_transit_response AS "
            "SELECT s.od_id,s.departure_time,s.scenario_id,s.total_min,p.mu_transit_sensitivity,p.probability "
            "FROM od_multimodal_skims s JOIN od_mode_probabilities p "
            "ON s.od_id=p.od_id AND s.departure_time=p.departure_time AND s.scenario_id=p.scenario_id "
            "WHERE s.mode='transit_walk_access' AND p.mode='TW'"
        )
    if "feedback_trace" in existing:
        connection.execute("CREATE VIEW end_to_end_feedback_trace AS SELECT * FROM feedback_trace")
    connection.commit()
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    count = connection.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
    ).fetchone()[0]
    connection.close()
    os.replace(temporary, output)
    result = {
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "database": str(output),
        "tables": count,
        "loaded_rows": sum(row[2] for row in loaded),
        "integrity_check": integrity,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if integrity == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
