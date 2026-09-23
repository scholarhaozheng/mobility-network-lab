"""Deterministic Boston GMNS/GMNS Plus exchange; no model fitting or assignment.

Usage: python -B tools/gmns/boston_exchange.py --help
The input directory is the declared Boston GMNS source-input asset, never code.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
from collections import defaultdict
from pathlib import Path


SCENARIOS = ("S1", "S2")
MU_BY_SCENARIO = {"S1": "0.25", "S2": "1.0"}  # S2 accepted FW boundary variant.
INPUT_FILES = (
    "physical_node.csv", "zone.csv", "zone_hierarchy.csv", "zone_access.csv",
    "crosswalk.csv", "S1_link.csv", "S1_demand.csv", "S2_link.csv",
    "S2_demand.csv", "gps_path_links.csv", "corridor_link.csv",
    "assignment_result_by_scenario.csv", "transit_shape_conflation.csv",
    "transit_stop_route_relation.csv",
)
NODE_COLUMNS = ("node_id", "zone_id", "x_coord", "y_coord", "node_type", "source_node_id", "source_h3_zone_id", "mcl_source_taz_zone_id")
ZONE_COLUMNS = ("zone_id", "name", "boundary", "super_zone", "mcl_original_h3_id", "mcl_h3_resolution", "mcl_clipped_geometry_wkt", "mcl_boundary_status")
LINK_CORE = ("link_id", "from_node_id", "to_node_id", "directed", "dir_flag", "length", "free_speed", "capacity", "lanes", "link_type", "vdf_alpha", "vdf_beta", "vdf_plf", "geometry", "mcl_link_class", "source_link_id", "source_from_node_id", "source_to_node_id", "mcl_gps_match_allowed")
DEMAND_COLUMNS = ("o_zone_id", "d_zone_id", "volume")


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"Missing CSV header: {path}")
        return tuple(reader.fieldnames), list(reader)


def write_csv(path: Path, columns, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def fresh_output(source: Path, output: Path):
    source, output = source.resolve(), output.resolve()
    if source == output or source in output.parents or output in source.parents:
        raise ValueError("Input and output directories must not overlap")
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"Output is nonempty; refusing overwrite: {output}")
    output.mkdir(parents=True, exist_ok=True)


def is_true(value):
    return str(value).strip().lower() in ("true", "1", "yes")


def fmt(number):
    return format(float(number), ".17g")


def export(inputs: Path, output: Path):
    inputs = inputs.resolve()
    missing = [x for x in INPUT_FILES if not (inputs / x).is_file()]
    if missing:
        raise ValueError(f"Missing declared inputs: {missing}")
    fresh_output(inputs, output)
    output = output.resolve()

    _, all_zones = read_csv(inputs / "zone.csv")
    fine = [z for z in all_zones if z["zone_level"] == "fine"]
    parent_rows = {z["zone_id"]: z for z in all_zones if z["zone_level"] == "parent"}
    _, hierarchy = read_csv(inputs / "zone_hierarchy.csv")
    _, access = read_csv(inputs / "zone_access.csv")
    _, physical_nodes = read_csv(inputs / "physical_node.csv")
    solver_columns, solver_links = read_csv(inputs / "S1_link.csv")
    other_columns, other_links = read_csv(inputs / "S2_link.csv")
    if solver_columns != other_columns or solver_links != other_links:
        raise ValueError("Frozen S1/S2 physical link inputs differ; a single shared network is not valid")
    if len({x["zone_id"] for x in fine}) != len(fine):
        raise ValueError("Duplicate fine H3 zone")
    fine.sort(key=lambda x: x["zone_id"])
    parent_of = {x["child_zone_id"]: x["parent_zone_id"] for x in hierarchy}
    parents = sorted(set(parent_of.values()))
    if set(parent_rows) != set(parents):
        raise ValueError("Stored H3 parent geometry records do not match hierarchy")
    if set(parent_of) != {x["zone_id"] for x in fine}:
        raise ValueError("Fine-zone hierarchy incomplete or contains unknown zone")
    access_by_zone = {x["zone_id"]: x for x in access}
    if len(access_by_zone) != len(access) or set(access_by_zone) != set(parent_of):
        raise ValueError("Fine-zone access map incomplete or duplicated")
    zone_id = {z["zone_id"]: i + 1 for i, z in enumerate(fine)}
    parent_id = {p: 1001 + i for i, p in enumerate(parents)}
    physical_nodes = [n for n in physical_nodes if n["node_role"] == "physical"]
    physical_nodes.sort(key=lambda n: int(n["node_id"]))
    physical_id = {n["node_id"]: 10000 + int(n["node_id"]) for n in physical_nodes}
    if len(physical_id) != len(physical_nodes) or set(zone_id.values()) & set(physical_id.values()):
        raise ValueError("Node ID collision")
    if any(a["access_node_id"] not in physical_id for a in access):
        raise ValueError("Access node missing from physical node table")

    zone_rows = []
    for z in fine:
        zone_rows.append({
            "zone_id": zone_id[z["zone_id"]], "name": z["zone_id"],
            "boundary": z["full_geometry_wkt"], "super_zone": parent_id[parent_of[z["zone_id"]]],
            "mcl_original_h3_id": z["zone_id"], "mcl_h3_resolution": z["h3_resolution"],
            "mcl_clipped_geometry_wkt": z["clipped_geometry_wkt"],
            "mcl_boundary_status": "full_h3_cell; clipped_core_geometry_companion",
        })
    for p in parents:
        z = parent_rows[p]
        zone_rows.append({"zone_id": parent_id[p], "name": p, "boundary": z["full_geometry_wkt"], "super_zone": "",
                          "mcl_original_h3_id": p, "mcl_h3_resolution": "7",
                          "mcl_clipped_geometry_wkt": z["clipped_geometry_wkt"],
                          "mcl_boundary_status": "full_h3_parent_cell_aggregation_only_not_active_demand"})
    write_csv(output / "zone.csv", ZONE_COLUMNS, zone_rows)

    node_rows = []
    crosswalk = []
    for z in fine:
        a = access_by_zone[z["zone_id"]]
        zid = zone_id[z["zone_id"]]
        node_rows.append({"node_id": zid, "zone_id": zid, "x_coord": z["centroid_lon"],
                          "y_coord": z["centroid_lat"], "node_type": "model_centroid_nonphysical",
                          "source_node_id": "", "source_h3_zone_id": z["zone_id"], "mcl_source_taz_zone_id": ""})
        crosswalk.append({"original_h3_zone_id": z["zone_id"], "export_zone_id": zid,
                          "parent_h3_zone_id": parent_of[z["zone_id"]],
                          "export_parent_zone_id": parent_id[parent_of[z["zone_id"]]],
                          "centroid_node_id": zid, "physical_access_node_id": physical_id[a["access_node_id"]],
                          "source_physical_access_node_id": a["access_node_id"],
                          "source_connector_id": a["connector_id"], "access_distance_m": a["access_distance_m"],
                          "access_status": a["status"]})
    for n in physical_nodes:
        node_rows.append({"node_id": physical_id[n["node_id"]], "zone_id": "",
                          "x_coord": n["x_coord"], "y_coord": n["y_coord"], "node_type": "physical",
                          "source_node_id": n["node_id"], "source_h3_zone_id": "",
                          "mcl_source_taz_zone_id": n["zone_id"]})
    write_csv(output / "node.csv", NODE_COLUMNS, node_rows)
    write_csv(output / "id_crosswalk.csv", tuple(crosswalk[0]), crosswalk)

    link_columns = LINK_CORE + tuple("mcl_solver_" + c for c in solver_columns)
    link_rows = []
    physical_link_ids = set()
    for link in solver_links:
        lid = int(link["link_id"])
        if lid in physical_link_ids:
            raise ValueError("Duplicate physical link ID")
        physical_link_ids.add(lid)
        if link["from_node_id"] not in physical_id or link["to_node_id"] not in physical_id:
            raise ValueError(f"Physical link endpoint missing: {lid}")
        row = {"link_id": lid, "from_node_id": physical_id[link["from_node_id"]],
               "to_node_id": physical_id[link["to_node_id"]], "directed": "true",
               "dir_flag": link["dir_flag"], "length": link["length"],
               "free_speed": link["free_speed"], "capacity": link["capacity_source"],
               "lanes": link["lanes"], "link_type": link["link_type"],
               "vdf_alpha": link["vdf_alpha"], "vdf_beta": link["vdf_beta"], "vdf_plf": link["vdf_plf"],
               "geometry": link["geometry"], "mcl_link_class": "physical",
               "source_link_id": link["source_link_id"],
               "source_from_node_id": link["from_node_id"], "source_to_node_id": link["to_node_id"],
               "mcl_gps_match_allowed": link["gps_match_allowed"]}
        row.update({"mcl_solver_" + k: v for k, v in link.items()})
        link_rows.append(row)
    next_link_id = max(physical_link_ids) + 1000000
    for i, c in enumerate(crosswalk):
        for direction, source, target in (("out", c["centroid_node_id"], c["physical_access_node_id"]),
                                          ("in", c["physical_access_node_id"], c["centroid_node_id"])):
            link_rows.append({"link_id": next_link_id + i * 2 + (direction == "in"),
                              "from_node_id": source, "to_node_id": target, "directed": "true", "dir_flag": 0,
                              "length": "", "free_speed": "", "capacity": "", "lanes": "", "link_type": 0,
                              "vdf_alpha": "", "vdf_beta": "", "vdf_plf": "",
                              "geometry": "", "mcl_link_class": "nonphysical_zone_access_" + direction,
                              "source_link_id": "", "source_from_node_id": "", "source_to_node_id": "",
                              "mcl_gps_match_allowed": "false"})
    link_rows.sort(key=lambda r: (int(r["from_node_id"]), int(r["to_node_id"]), int(r["link_id"])))
    write_csv(output / "link.csv", link_columns, link_rows)

    config = {"dataset_name": "MCL Boston Central H3 GMNS exchange r1", "short_length": "meter",
              "long_length": "meter", "speed": "kilometer/hour", "crs": "EPSG:4326",
              "geometry_field_format": "WKT", "currency": "USD", "version_number": "0.96", "id_type": "integer"}
    write_csv(output / "config.csv", tuple(config), [config])

    _, ledger = read_csv(inputs / "crosswalk.csv")
    selected = []
    zonal_counts = {}
    for scenario in SCENARIOS:
        label = "S1_planned_service" if scenario == "S1" else "S2_exploratory_gps_overlay"
        branch = MU_BY_SCENARIO[scenario]
        subset = [r for r in ledger if r["scenario_id"] == label and float(r["mu_transit_sensitivity"]) == float(branch)]
        if not subset:
            raise ValueError(f"Missing frozen scenario/branch: {label}/{branch}")
        aggregated = defaultdict(float)
        for r in subset:
            if r["o_zone_id"] not in zone_id or r["d_zone_id"] not in zone_id:
                raise ValueError("Crosswalk H3 endpoint missing")
            a, b = zone_id[r["o_zone_id"]], zone_id[r["d_zone_id"]]
            include = is_true(r["assignment_inclusion"])
            vol = float(r["vehicle_trips"] or 0)
            if include:
                aggregated[(a, b)] += vol
            selected.append({"scenario": scenario, "od_id": r["od_id"], "departure_time": r["departure_time"],
                             "purpose": r["purpose"], "mode": r["mode"], "original_o_h3": r["o_zone_id"],
                             "original_d_h3": r["d_zone_id"], "export_o_zone_id": a, "export_d_zone_id": b,
                             "source_o_node_id": r["o_node_id"], "source_d_node_id": r["d_node_id"],
                             "vehicle_trips": r["vehicle_trips"], "assignment_inclusion": r["assignment_inclusion"],
                             "road_leg_status": r["road_leg_status"],
                             "same_access_node": str(r["o_node_id"] == r["d_node_id"]),
                             "intrazonal": str(a == b)})
        demand = [{"o_zone_id": a, "d_zone_id": b, "volume": fmt(v)}
                  for (a, b), v in sorted(aggregated.items()) if v > 0]
        write_csv(output / f"demand_{scenario}.csv", DEMAND_COLUMNS, demand)
        zonal_counts[scenario] = {"rows": len(demand), "vehicle_trips": sum(aggregated.values())}
    write_csv(output / "demand.csv", DEMAND_COLUMNS, read_csv(output / "demand_S1.csv")[1])
    write_csv(output / "selected_demand_ledger.csv", tuple(selected[0]), selected)

    for name in ("gps_path_links.csv", "corridor_link.csv", "assignment_result_by_scenario.csv",
                 "transit_shape_conflation.csv", "transit_stop_route_relation.csv"):
        shutil.copyfile(inputs / name, output / name)
    manifest = {
        "profile": "mcl-boston-gmns-plus-structural-r1", "source_inputs_sha256": {x: sha256(inputs / x) for x in INPUT_FILES},
        "semantic_counts": {"fine_zones": len(fine), "parent_zones": len(parents),
                            "centroids": len(fine), "physical_nodes": len(physical_nodes),
                            "physical_links": len(solver_links), "connector_arcs": len(access) * 2,
                            "distinct_access_nodes": len({x["access_node_id"] for x in access}),
                            "zonal_demand": zonal_counts},
        "capacity_policy": "GMNS capacity=source PCE/hour/lane; mcl_solver_capacity_effective=accepted 2-hour PCE in solver extensions",
        "connector_policy": "Nonphysical read/relationship representation only; no free speed/capacity/length invented; use collapse-to-access adapter for accepted physical solver",
        "source_taz_policy": "Original TAZ centroids/connectors remain in immutable source asset; absent from active H3 exchange graph",
        "standard_schema_commit": "4e51f4c7893f5df2c8c69ab21c5dc0abd9b69f48",
        "consumer_commit": "116447ab641cca1ed34797d019c8e704063393c3",
    }
    manifest["export_sha256"] = {p.name: sha256(p) for p in sorted(output.iterdir()) if p.is_file()}
    write_json(output / "manifest.json", manifest)
    return manifest


def roundtrip(exchange: Path, expected: Path, output: Path):
    fresh_output(exchange, output)
    _, links = read_csv(exchange / "link.csv")
    _, cw = read_csv(exchange / "id_crosswalk.csv")
    original_access = {x["export_zone_id"]: x["source_physical_access_node_id"] for x in cw}
    physical = [x for x in links if x["mcl_link_class"] == "physical"]
    reports = {}
    for scenario in SCENARIOS:
        cols, expected_links = read_csv(expected / f"{scenario}_link.csv")
        reconstructed = [{c: row["mcl_solver_" + c] for c in cols} for row in physical]
        reconstructed.sort(key=lambda x: int(x["link_id"]))
        target = output / scenario
        target.mkdir()
        write_csv(target / "link.csv", cols, reconstructed)
        exp_by_id = {x["link_id"]: x for x in expected_links}
        got_by_id = {x["link_id"]: x for x in reconstructed}
        link_keys_match = set(exp_by_id) == set(got_by_id)
        cell_errors = sum(exp_by_id[k] != got_by_id[k] for k in exp_by_id.keys() & got_by_id.keys())
        _, zonal = read_csv(exchange / f"demand_{scenario}.csv")
        node_demand = defaultdict(float)
        same_access = 0.0
        for r in zonal:
            o, d = original_access[r["o_zone_id"]], original_access[r["d_zone_id"]]
            v = float(r["volume"])
            if o == d:
                same_access += v
            else:
                node_demand[(o, d)] += v
        generated = [{"o_zone_id": o, "d_zone_id": d, "volume": fmt(v)}
                     for (o, d), v in sorted(node_demand.items())]
        write_csv(target / "demand.csv", DEMAND_COLUMNS, generated)
        _, expected_demand = read_csv(expected / f"{scenario}_demand.csv")
        exp_d = {(x["o_zone_id"], x["d_zone_id"]): float(x["volume"]) for x in expected_demand}
        got_d = {(x["o_zone_id"], x["d_zone_id"]): float(x["volume"]) for x in generated}
        demand_keys_match = set(exp_d) == set(got_d)
        max_demand_error = max((abs(exp_d[k] - got_d[k]) for k in exp_d.keys() & got_d.keys()), default=0.0)
        reports[scenario] = {"physical_link_ids_match": link_keys_match, "physical_link_row_errors": cell_errors,
                             "physical_link_rows": len(reconstructed), "zonal_od_rows": len(zonal),
                             "physical_od_ids_match": demand_keys_match, "physical_od_rows": len(generated),
                             "max_physical_od_abs_error": max_demand_error,
                             "same_access_vehicle_trips_excluded_from_road_injection": same_access,
                             "zonal_vehicle_trips": sum(float(x["volume"]) for x in zonal),
                             "physical_vehicle_trips": sum(got_d.values())}
    write_json(output / "roundtrip_results.json", reports)
    return reports


def validate(exchange: Path, schema: Path):
    checks = {}
    tables = {}
    for table in ("node", "link", "zone", "config"):
        fields, rows = read_csv(exchange / f"{table}.csv")
        definition = json.loads((schema / f"{table}.schema.json").read_text(encoding="utf-8"))
        required = {f["name"] for f in definition["fields"] if f.get("constraints", {}).get("required")}
        checks[f"{table}_required_fields"] = required.issubset(fields)
        checks[f"{table}_row_count"] = len(rows)
        tables[table] = rows
    nodes = {x["node_id"] for x in tables["node"]}
    zones = {x["zone_id"] for x in tables["zone"]}
    links = {x["link_id"] for x in tables["link"]}
    checks["node_unique"] = len(nodes) == len(tables["node"])
    checks["zone_unique"] = len(zones) == len(tables["zone"])
    checks["link_unique"] = len(links) == len(tables["link"])
    checks["link_endpoints"] = all(x["from_node_id"] in nodes and x["to_node_id"] in nodes for x in tables["link"])
    checks["zone_parent_fks"] = all(not x["super_zone"] or x["super_zone"] in zones for x in tables["zone"])
    checks["node_zone_fks"] = all(not x["zone_id"] or x["zone_id"] in zones for x in tables["node"])
    checks["config_exactly_one_row"] = len(tables["config"]) == 1
    cfg = tables["config"][0]
    checks["config_crs_units"] = (cfg["crs"], cfg["geometry_field_format"], cfg["long_length"], cfg["speed"], cfg["id_type"]) == ("EPSG:4326", "WKT", "meter", "kilometer/hour", "integer")
    checks["numeric_ids"] = all(x.isdecimal() for x in nodes | zones | links)
    checks["node_coordinates_numeric"] = all(math.isfinite(float(x[k])) for x in tables["node"] for k in ("x_coord", "y_coord"))
    checks["zone_hierarchy_acyclic"] = all(x["super_zone"] == "" for x in tables["zone"] if x["mcl_h3_resolution"] == "7") and all(x["super_zone"] for x in tables["zone"] if x["mcl_h3_resolution"] == "9")
    checks["centroid_id_equality"] = all(x["node_id"] == x["zone_id"] for x in tables["node"] if x["node_type"] == "model_centroid_nonphysical")
    checks["physical_standard_capacity_source"] = all(float(x["capacity"]) == float(x["mcl_solver_capacity_source"]) for x in tables["link"] if x["mcl_link_class"] == "physical")
    _, cw = read_csv(exchange / "id_crosswalk.csv")
    checks["access_count"] = len(cw)
    checks["access_fks"] = all(x["centroid_node_id"] in nodes and x["physical_access_node_id"] in nodes for x in cw)
    connectors = [x for x in tables["link"] if x["mcl_link_class"].startswith("nonphysical_zone_access_")]
    checks["connector_arcs_twice_access"] = len(connectors) == 2 * len(cw)
    checks["connector_nonphysical"] = all(x["mcl_gps_match_allowed"] == "false" and x["source_link_id"] == "" for x in connectors)
    checks["no_centroid_to_centroid_arc"] = not any(int(x["from_node_id"]) < 10000 and int(x["to_node_id"]) < 10000 for x in tables["link"])
    adjacency = defaultdict(set)
    for x in connectors:
        if int(x["from_node_id"]) < 10000:
            adjacency[x["from_node_id"]].add(x["to_node_id"])
        if int(x["to_node_id"]) < 10000:
            adjacency[x["to_node_id"]].add(x["from_node_id"])
    checks["one_access_neighbor_per_centroid"] = all(adjacency[x["centroid_node_id"]] == {x["physical_access_node_id"]} for x in cw)
    checks["bidirectional_access_pair"] = all(
        any(x["from_node_id"] == c["centroid_node_id"] and x["to_node_id"] == c["physical_access_node_id"] for x in connectors)
        and any(x["to_node_id"] == c["centroid_node_id"] and x["from_node_id"] == c["physical_access_node_id"] for x in connectors)
        for c in cw)
    checks["physical_travel_direction"] = all(x["directed"] == "true" and x["dir_flag"] == x["mcl_solver_dir_flag"] for x in tables["link"] if x["mcl_link_class"] == "physical")
    checks["effective_capacity_converted_once"] = all(
        abs(float(x["mcl_solver_capacity_effective"]) - float(x["capacity"]) * float(x["lanes"]) * float(x["mcl_solver_capacity_period_hours"]) * float(x["mcl_solver_vdf_plf"])) < 1e-9
        for x in tables["link"] if x["mcl_link_class"] == "physical")
    try:
        from shapely import wkt
        physical_geoms = [wkt.loads(x["geometry"]) for x in tables["link"] if x["mcl_link_class"] == "physical"]
        zone_geoms = [wkt.loads(x["boundary"]) for x in tables["zone"]]
        checks["physical_wkt_valid"] = all(g.is_valid and g.geom_type in ("LineString", "MultiLineString") for g in physical_geoms)
        checks["zone_wkt_valid"] = all(g.is_valid and g.geom_type in ("Polygon", "MultiPolygon") for g in zone_geoms)
    except ImportError:
        checks["physical_wkt_valid"] = "UNVERIFIED_SHAPELY_NOT_INSTALLED"
        checks["zone_wkt_valid"] = "UNVERIFIED_SHAPELY_NOT_INSTALLED"
    for scenario in SCENARIOS:
        fields, demand = read_csv(exchange / f"demand_{scenario}.csv")
        checks[f"{scenario}_demand_exact_columns"] = fields == DEMAND_COLUMNS
        checks[f"{scenario}_demand_zone_fks"] = all(x["o_zone_id"] in zones and x["d_zone_id"] in zones for x in demand)
        active_fine = {x["zone_id"] for x in tables["zone"] if x["mcl_h3_resolution"] == "9"}
        checks[f"{scenario}_demand_fine_only"] = all(x["o_zone_id"] in active_fine and x["d_zone_id"] in active_fine for x in demand)
        checks[f"{scenario}_demand_rows"] = len(demand)
    _, gps = read_csv(exchange / "gps_path_links.csv")
    _, shapes = read_csv(exchange / "transit_shape_conflation.csv")
    _, stops = read_csv(exchange / "transit_stop_route_relation.csv")
    _, corridors = read_csv(exchange / "corridor_link.csv")
    _, results = read_csv(exchange / "assignment_result_by_scenario.csv")
    physical_links = {x["link_id"] for x in tables["link"] if x["mcl_link_class"] == "physical"}
    checks["gps_link_fks"] = all(x["link_id"] in physical_links for x in gps)
    checks["planned_shape_link_fks"] = all(x["matched_link_id"] in physical_links for x in shapes)
    original_physical_node_ids = {x["source_node_id"] for x in tables["node"] if x["node_type"] == "physical"}
    checks["known_stop_access_node_fks"] = all(not x["access_node_id"] or x["access_node_id"] in original_physical_node_ids for x in stops)
    checks["corridor_link_fks"] = all(x["link_id"] in physical_links for x in corridors)
    checks["result_link_fks"] = all(x["link_id"] in physical_links for x in results)
    checks["gps_rows"] = len(gps)
    checks["planned_shape_rows"] = len(shapes)
    checks["stop_route_rows"] = len(stops)
    checks["known_stop_access_rows"] = sum(bool(x["access_node_id"]) for x in stops)
    checks["corridor_rows"] = len(corridors)
    checks["corridor_count"] = len({x["corridor_id"] for x in corridors})
    checks["result_rows"] = len(results)
    checks["pass"] = all(v for k, v in checks.items() if isinstance(v, bool)) and not any(str(v).startswith("UNVERIFIED") for v in checks.values())
    return checks


def trace(exchange: Path):
    _, cw = read_csv(exchange / "id_crosswalk.csv")
    _, demand = read_csv(exchange / "demand_S1.csv")
    _, links = read_csv(exchange / "link.csv")
    _, results = read_csv(exchange / "assignment_result_by_scenario.csv")
    _, gps = read_csv(exchange / "gps_path_links.csv")
    _, shapes = read_csv(exchange / "transit_shape_conflation.csv")
    _, stops = read_csv(exchange / "transit_stop_route_relation.csv")
    _, corridors = read_csv(exchange / "corridor_link.csv")
    c_by_zone = {x["export_zone_id"]: x for x in cw}
    od = demand[0]
    origin = c_by_zone[od["o_zone_id"]]
    destination = c_by_zone[od["d_zone_id"]]
    connector = next(x for x in links if x["mcl_link_class"] == "nonphysical_zone_access_out" and x["from_node_id"] == origin["centroid_node_id"])
    result_by_link = {x["link_id"]: x for x in results}
    incident = next((x for x in links if x["mcl_link_class"] == "physical" and
                     x["from_node_id"] == origin["physical_access_node_id"] and x["link_id"] in result_by_link), None)
    gps_example = next((x for x in gps if x["link_id"] in result_by_link), None)
    corridor_example = next((x for x in corridors if x["link_id"] in result_by_link), None)
    shape_example = next((x for x in shapes if x["matched_link_id"] in result_by_link), None)
    stop_example = next((x for x in stops if x["access_node_id"]), None)
    return {"zone_to_road": {"original_h3": origin["original_h3_zone_id"],
                              "parent_h3": origin["parent_h3_zone_id"],
                              "export_zone": origin["export_zone_id"], "centroid": origin["centroid_node_id"],
                              "connector": connector["link_id"], "physical_access_node": origin["physical_access_node_id"],
                              "source_physical_access_node": origin["source_physical_access_node_id"],
                              "example_zonal_od": od,
                              "aggregated_physical_od": {"source_o_node_id": origin["source_physical_access_node_id"],
                                                         "source_d_node_id": destination["source_physical_access_node_id"]},
                              "incident_physical_link": {"source_link_id": incident["source_link_id"],
                                                         "saved_s1_volume": result_by_link[incident["link_id"]]["s1_volume"]} if incident else None,
                              "relation": "modeled H3-to-access mapping, then shared-key incident road/result join; not an OD-specific assigned path"},
            "gps_to_road": {"trace_id": gps_example["trace_id"], "source_link_id": gps_example["link_id"],
                            "engine": gps_example["engine"], "quality": gps_example["evidence_status"],
                            "saved_s1_road_volume": result_by_link[gps_example["link_id"]]["s1_volume"],
                            "relation": "shared physical link ID; GPS points are not volume counts"} if gps_example else None,
            "corridor_to_road": {"corridor_id": corridor_example["corridor_id"],
                                 "member_order": corridor_example["member_order"],
                                 "source_link_id": corridor_example["link_id"],
                                 "saved_s1_road_volume": result_by_link[corridor_example["link_id"]]["s1_volume"],
                                 "relation": "ordered corridor membership and saved model result join by link ID"} if corridor_example else None,
            "planned_shape_to_road": {"feed_id": shape_example["feed_id"], "route_id": shape_example["route_id"],
                                      "source_link_id": shape_example["matched_link_id"],
                                      "observation_status": shape_example["observation_status"],
                                      "saved_s1_road_volume": result_by_link[shape_example["matched_link_id"]]["s1_volume"],
                                      "relation": "planned GTFS shape conflation, not live GPS observation"} if shape_example else None,
            "stop_to_access": {"feed_id": stop_example["feed_id"], "stop_id": stop_example["stop_id"],
                               "source_physical_access_node_id": stop_example["access_node_id"],
                               "status": stop_example["status"],
                               "relation": "candidate GTFS stop-to-physical-node access, not field-verified"} if stop_example else None}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    e = sub.add_parser("export", help="Create a fresh deterministic Boston exchange from declared CSV inputs")
    e.add_argument("--inputs", type=Path, required=True)
    e.add_argument("--output", type=Path, required=True)
    r = sub.add_parser("roundtrip", help="Reconstruct accepted S1/S2 physical solver inputs without solving")
    r.add_argument("--exchange", type=Path, required=True)
    r.add_argument("--expected", type=Path, required=True)
    r.add_argument("--output", type=Path, required=True)
    v = sub.add_parser("validate", help="Check pinned upstream schemas and Boston relationships")
    v.add_argument("--exchange", type=Path, required=True)
    v.add_argument("--schema", type=Path, required=True, help="Directory containing pinned upstream *.schema.json")
    t = sub.add_parser("trace", help="Print real zone, GPS, corridor and saved-result join examples")
    t.add_argument("--exchange", type=Path, required=True)
    args = p.parse_args()
    if args.command == "export":
        result = export(args.inputs, args.output)
    elif args.command == "roundtrip":
        result = roundtrip(args.exchange, args.expected, args.output)
    elif args.command == "validate":
        result = validate(args.exchange, args.schema)
    else:
        result = trace(args.exchange)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
