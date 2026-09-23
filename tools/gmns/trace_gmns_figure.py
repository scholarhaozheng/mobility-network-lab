"""Read a specific published Boston zone and saved GPS segment relationship.

This command only reads the public exchange and saved derived GPS CSVs. It does
not infer an assigned OD route, rematch observations, or run an assignment.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def one(items: list[dict[str, str]], field: str, value: str, label: str) -> dict[str, str]:
    matches = [row for row in items if row[field] == value]
    if len(matches) != 1:
        raise ValueError(f"Expected one {label} for {field}={value!r}; found {len(matches)}")
    return matches[0]


def select(row: dict[str, str], *fields: str) -> dict[str, str]:
    return {field: row[field] for field in fields}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def trace(exchange: Path, gps_dir: Path, zone_id: str, segment_id: str) -> dict:
    zone_file = exchange / "zone.csv"
    node_file = exchange / "node.csv"
    link_file = exchange / "link.csv"
    crosswalk_file = exchange / "id_crosswalk.csv"
    demand_file = exchange / "demand_S1.csv"
    path_file = gps_dir / "gps_path_links.csv"
    point_file = gps_dir / "gps_point_progress.csv"
    quality_file = gps_dir / "gps_segment_quality.csv"
    result_file = exchange / "assignment_result_by_scenario.csv"

    zone = one(rows(zone_file), "zone_id", zone_id, "fine zone")
    crosswalk = one(rows(crosswalk_file), "export_zone_id", zone_id, "zone crosswalk")
    parent = one(rows(zone_file), "zone_id", zone["super_zone"], "parent zone")
    nodes = rows(node_file)
    centroid = one(nodes, "node_id", crosswalk["centroid_node_id"], "centroid")
    access = one(nodes, "node_id", crosswalk["physical_access_node_id"], "physical access node")
    links = rows(link_file)
    connector_rows = [row for row in links if row["from_node_id"] == centroid["node_id"]
                      and row["to_node_id"] == access["node_id"]
                      and row["mcl_link_class"] == "nonphysical_zone_access_out"]
    if len(connector_rows) != 1:
        raise ValueError(f"Expected one outbound nonphysical connector for zone {zone_id}")
    connector = connector_rows[0]
    incident = sorted((row for row in links if row["from_node_id"] == access["node_id"]
                       and row["mcl_link_class"] == "physical"), key=lambda row: int(row["link_id"]))
    if not incident:
        raise ValueError(f"No outgoing physical link at access node {access['node_id']}")
    demand = sorted((row for row in rows(demand_file) if row["o_zone_id"] == zone_id),
                    key=lambda row: int(row["d_zone_id"]))
    if not demand:
        raise ValueError(f"No S1 demand record for zone {zone_id}")
    chosen_demand = demand[0]
    dest = one(rows(crosswalk_file), "export_zone_id", chosen_demand["d_zone_id"], "destination crosswalk")

    quality = one(rows(quality_file), "segment_id", segment_id, "GPS segment quality")
    points = sorted((row for row in rows(point_file) if row["segment_id"] == segment_id),
                    key=lambda row: int(row["point_seq"]))
    paths = sorted((row for row in rows(path_file) if row["segment_id"] == segment_id),
                   key=lambda row: int(row["path_order"]))
    if not points or not paths:
        raise ValueError(f"Saved points or path missing for segment {segment_id!r}")
    if quality["observation_eligible"].lower() != "true":
        raise ValueError(f"Segment {segment_id!r} is not observation-eligible")
    first = paths[0]
    road = one(links, "link_id", first["link_id"], "matched physical link")
    if road["mcl_link_class"] != "physical" or road["mcl_gps_match_allowed"].lower() != "true":
        raise ValueError("Selected path references a nonphysical or unmatchable link")
    saved = one(rows(result_file), "link_id", first["link_id"], "saved S1/S2 road result")
    matched_points = [point for point in points if point["matched_link_id"] == first["link_id"]
                      and point["path_occurrence"] == first["path_occurrence"]]
    if not matched_points:
        raise ValueError("First path occurrence has no saved point association")

    return {
        "scope": "Two separate public relationships; shared links are not evidence of one observed trip.",
        "zone_branch": {
            "fine_zone": select(zone, "zone_id", "name", "super_zone", "boundary"),
            "parent_zone": select(parent, "zone_id", "name"),
            "crosswalk": select(crosswalk, "original_h3_zone_id", "export_zone_id", "parent_h3_zone_id",
                                "export_parent_zone_id", "centroid_node_id", "physical_access_node_id",
                                "source_physical_access_node_id", "source_connector_id", "access_distance_m"),
            "centroid": select(centroid, "node_id", "node_type", "x_coord", "y_coord"),
            "access_node": select(access, "node_id", "source_node_id", "node_type", "x_coord", "y_coord"),
            "outbound_connector": select(connector, "link_id", "from_node_id", "to_node_id", "mcl_link_class",
                                         "mcl_gps_match_allowed"),
            "incident_physical_link": select(incident[0], "link_id", "from_node_id", "to_node_id",
                                             "mcl_link_class", "mcl_gps_match_allowed"),
            "S1_zonal_OD": select(chosen_demand, "o_zone_id", "d_zone_id", "volume"),
            "destination_crosswalk": select(dest, "original_h3_zone_id", "export_zone_id",
                                            "physical_access_node_id", "source_physical_access_node_id"),
            "OD_note": "S1 volume is modeled panel vehicle trips. The incident physical link is not an assigned path for this OD.",
        },
        "gps_branch": {
            "quality": select(quality, "segment_id", "route_id", "observation_eligible", "quality_class",
                              "point_count", "path_occurrences", "start_censored", "end_censored"),
            "ordered_path": [select(row, "path_order", "path_occurrence", "link_id", "direction",
                                    "point_projection_count", "evidence_status") for row in paths],
            "saved_points": [select(row, "point_seq", "timestamp", "original_lon", "original_lat",
                                    "matched_link_id", "path_occurrence", "projected_lon", "projected_lat",
                                    "match_status") for row in points],
            "first_occurrence_point": select(matched_points[0], "point_seq", "timestamp", "matched_link_id",
                                             "path_occurrence", "match_status"),
            "physical_link": select(road, "link_id", "from_node_id", "to_node_id", "source_link_id",
                                    "mcl_link_class", "mcl_gps_match_allowed", "vdf_alpha", "vdf_beta",
                                    "mcl_solver_vdf_fftt"),
            "saved_road_result": select(saved, "link_id", "s1_volume", "s1_travel_time", "s1_vc_ratio",
                                        "delta_volume", "delta_status"),
            "result_units": {"s1_volume": "modeled panel vehicle trips", "s1_travel_time": "minutes",
                             "s1_vc_ratio": "dimensionless"},
            "caution": "Positions are source observations; path association and projections are saved algorithm-derived data. The S1 road result is a separately modeled aggregate, not this vehicle's count.",
        },
        "source_sha256": {"zone.csv": digest(zone_file), "node.csv": digest(node_file),
                          "link.csv": digest(link_file), "id_crosswalk.csv": digest(crosswalk_file),
                          "demand_S1.csv": digest(demand_file), "gps_point_progress.csv": digest(point_file),
                          "gps_path_links.csv": digest(path_file), "gps_segment_quality.csv": digest(quality_file),
                          "assignment_result_by_scenario.csv": digest(result_file)},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exchange", type=Path, required=True, help="Published Boston GMNS exchange data directory")
    parser.add_argument("--gps-dir", type=Path, required=True, help="Published saved derived GPS CSV directory")
    parser.add_argument("--zone-id", required=True, help="Exact exported fine-zone ID, for example 35")
    parser.add_argument("--segment-id", required=True, help="Exact eligible saved GPS segment ID")
    parser.add_argument("--output", type=Path, help="Optional JSON output file; default is standard output")
    args = parser.parse_args(argv)
    try:
        result = trace(args.exchange, args.gps_dir, args.zone_id, args.segment_id)
    except (OSError, KeyError, ValueError) as exc:
        parser.exit(2, f"Relationship lookup failed: {exc}\n")
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
