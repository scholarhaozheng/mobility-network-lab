"""Absolute OD-attribute choice sensitivity on the accepted fixed Boston panel.

All paths are arguments. No source tree is written, and no old probability is
used to construct a utility or intercept. The output is a conditional research
sensitivity, not a TDM23 reproduction or calibrated local choice model.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

MODES = ("DA", "S2", "S3", "TW")
NEST = {"DA": "Auto", "S2": "Auto", "S3": "Auto", "TW": "Transit"}
SCENARIO = {"S1_planned_service": "ABS_PLANNED", "S2_exploratory_gps_overlay": "ABS_OBS_EXPLORATORY", "Srestore_overlay_off_recomputed": "ABS_RESTORE"}
OCC = {"DA": 1.0, "S2": 2.0, "S3": 3.627}

def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))

def write_csv(path: Path, rows: list[dict], fields: list[str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

def number(value, label):
    if value in (None, ""):
        raise ValueError(f"missing {label}")
    x = float(value)
    if not math.isfinite(x):
        raise ValueError(f"nonfinite {label}")
    return x

def logsumexp(values):
    if not values:
        raise ValueError("empty logsumexp")
    peak = max(values)
    return peak + math.log(sum(math.exp(x - peak) for x in values))

def nested_probabilities(utilities: dict[str, float], scales: dict[str, float]):
    if not utilities:
        raise ValueError("no feasible alternatives")
    if any(not (0 < mu <= 1) for mu in scales.values()):
        raise ValueError("nested scales must be in (0,1] under this convention")
    by_nest = defaultdict(list)
    for mode, utility in utilities.items():
        if mode not in NEST or not math.isfinite(utility):
            raise ValueError("unknown alternative or nonfinite utility")
        by_nest[NEST[mode]].append((mode, utility))
    inclusive = {nest: scales[nest] * logsumexp([u / scales[nest] for _, u in items]) for nest, items in by_nest.items()}
    root = logsumexp(list(inclusive.values()))
    result = {}
    for nest, items in by_nest.items():
        denom = logsumexp([u / scales[nest] for _, u in items])
        for mode, utility in items:
            result[mode] = math.exp(inclusive[nest] - root) * math.exp(utility / scales[nest] - denom)
    return result, inclusive, root

def utility_components(mode: str, source: dict, spec: dict):
    if source["availability_status"] != "available":
        raise ValueError("unknown_or_unavailable_path:" + source["availability_status"])
    beta = spec["beta"]
    ivtt = number(source["in_vehicle_min"], "ivtt")
    if mode == "TW":
        if number(source["ride_segment_count"], "ride_segment_count") < 1 or number(source["boardings"], "boardings") < 1:
            raise ValueError("no_permitted_ride")
        walk = number(source["walk_min"], "walk_min")
        wait = number(source["wait_min"], "wait_min")
        ovtt = walk + wait
        if int(number(source["fare_price_year"], "fare_price_year")) != 2026:
            raise ValueError("unknown_fare_price_year")
        fare = number(source["fare_usd"], "selected_itinerary_fare")
        cost = fare * spec["fare_2026_to_2010_cpi_u_factor"]
        distance_m = ""
        context = "fare_CPI_converted_once"
    else:
        ovtt = 0.0  # Explicit zero-terminal-time research context.
        distance_m = number(source["distance_m"], "drive_distance_m")
        cost = distance_m / 1609.344 * spec["auto_operating_cost_2010_usd_per_mile_assumed"]
        context = "zero_terminal_parking_toll_sensitivity"
    terms = {
        "constant": spec["constant"][mode],
        "sufficient_vehicle": spec["sufficient_vehicle_term"][mode],
        "ivtt": beta["ivtt_min"] * ivtt,
        "ovtt": beta["ovtt_min"] * ovtt,
        "cost": beta["cost_2010_usd"] * cost,
    }
    return terms, {"ivtt_min": ivtt, "ovtt_min": ovtt, "cost_2010_usd": cost, "distance_m": distance_m, "context": context}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", required=True, type=Path)
    ap.add_argument("--spec", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    snapshot, out = args.snapshot.resolve(), args.out.resolve()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    out.mkdir(parents=True, exist_ok=True)
    panel = read_csv(snapshot / "derived/validation_panel.csv")
    if len(panel) != 36 or len({r["od_id"] for r in panel}) != 36:
        raise ValueError("fixed 36-OD panel contract failed")
    skim_rows = read_csv(snapshot / "derived/mode_specific_od_costs.csv")
    index = {}
    for row in skim_rows:
        key = (row["scenario_id"], row["od_id"], row["departure_time"], row["mode"])
        if key in index:
            raise ValueError("duplicate skim key")
        index[key] = row
    pivot = read_csv(snapshot / "derived/od_mode_probabilities.csv")
    pivot_index = {(r["scenario_id"], r["od_id"], r["departure_time"], r["mode"], r["mu_transit_sensitivity"]): r for r in pivot}
    node_rows = read_csv(snapshot / "derived/person_to_vehicle_crosswalk.csv")
    node_index = {}
    for r in node_rows:
        if r["scenario_id"] == "S1_planned_service" and r["mode"] == "DA" and r["mu_transit_sensitivity"] == "1.0" and r["assignment_inclusion"] == "True":
            node_index[(r["od_id"], r["departure_time"])] = (r["o_node_id"], r["d_node_id"])
    attributes, components, nest_rows, probs, ledger, demand_rows, comparator = [], [], [], [], [], [], []
    times = ("12:30:00", "12:40:00", "12:50:00")
    for od in panel:
        for departure in times:
            mass = number(od["person_trips_midday_od"], "panel_mass") / 3.0
            for source_scenario, scenario in SCENARIO.items():
                source_rows = {m: index.get((source_scenario, od["od_id"], departure, "drive" if m != "TW" else "transit_walk_access")) for m in MODES}
                if any(v is None for v in source_rows.values()):
                    raise ValueError("missing skim key")
                utility = {}
                failed = []
                for mode, source in source_rows.items():
                    base = {"od_id": od["od_id"], "o_zone_id": od["o_zone_id"], "d_zone_id": od["d_zone_id"], "departure_time": departure, "service_date": source["service_date"], "scenario_id": scenario, "source_scenario_id": source_scenario, "mode_id": mode, "nest_id": NEST[mode], "path_id": source["path_id"], "network_version": source["network_version"], "feed_id": source["feed_id"], "feed_version": source["feed_version"], "source_availability": source["availability_status"], "person_trips_panel": mass}
                    try:
                        terms, attrs = utility_components(mode, source, spec)
                        u = sum(terms.values())
                        utility[mode] = u
                        attributes.append({**base, **attrs, "input_status": "modeled", "source_cost_status": source["cost_status"], "overlay_applied": source["overlay_applied"]})
                        for term, val in terms.items():
                            components.append({**base, "component": term, "contribution": val, "utility_total": u})
                    except ValueError as exc:
                        failed.append(f"{mode}:{exc}")
                        attributes.append({**base, "ivtt_min": "", "ovtt_min": "", "cost_2010_usd": "", "distance_m": source["distance_m"], "context": "", "input_status": str(exc), "source_cost_status": source["cost_status"], "overlay_applied": source["overlay_applied"]})
                complete = len(utility) == len(MODES)
                ledger.append({"od_id": od["od_id"], "departure_time": departure, "scenario_id": scenario, "person_trips_panel": mass, "full_four_mode_case": complete, "status": "EVALUATED_CONDITIONAL" if complete else "UNKNOWN_CONDITIONAL_SCOPE", "reason": ";".join(failed), "assignment_node_available": (od["od_id"], departure) in node_index})
                for scale_id, scales in spec["scale_vectors"].items():
                    if not complete:
                        continue
                    p, inclusive, root = nested_probabilities(utility, scales)
                    for nest, iv in inclusive.items():
                        nest_rows.append({"od_id": od["od_id"], "departure_time": departure, "scenario_id": scenario, "scale_id": scale_id, "nest_id": nest, "mu": scales[nest], "inclusive_value": iv, "root_logsum": root})
                    for mode in MODES:
                        common = {"od_id": od["od_id"], "departure_time": departure, "scenario_id": scenario, "scale_id": scale_id, "mode_id": mode, "nest_id": NEST[mode], "probability_conditional": p[mode], "person_trips_conditional_engineering_mass": p[mode] * mass, "person_trips_panel": mass}
                        probs.append(common)
                        if scale_id == spec["primary_scale_id"]:
                            if mode in OCC:
                                vehicle = p[mode] * mass / OCC[mode]
                                nodes = node_index.get((od["od_id"], departure), ("", ""))
                                demand_rows.append({**common, "occupancy": OCC[mode], "vehicle_trips": vehicle, "o_node_id": nodes[0], "d_node_id": nodes[1], "assignment_eligible": bool(nodes[0] and nodes[1])})
                            if scenario == "ABS_PLANNED":
                                old = pivot_index.get(("S1_planned_service", od["od_id"], departure, mode, "1.0"))
                                if old is not None:
                                    comparator.append({**common, "reference_pivot_unconditional": number(old["probability"], "old_probability")})
    # Normalize the accepted comparator only within the declared four-mode subset.
    comp_groups = defaultdict(list)
    for row in comparator:
        comp_groups[(row["od_id"], row["departure_time"])].append(row)
    for rows in comp_groups.values():
        denominator = sum(x["reference_pivot_unconditional"] for x in rows)
        for row in rows:
            row["reference_pivot_four_mode_conditional"] = row["reference_pivot_unconditional"] / denominator
            row["specification_change_probability"] = row["probability_conditional"] - row["reference_pivot_four_mode_conditional"]
    cases = len(panel) * len(times)
    if len([r for r in ledger if r["scenario_id"] == "ABS_PLANNED"]) != cases:
        raise ValueError("panel ledger incomplete")
    fields = {
        "model_inputs/od_choice_attributes.csv": (attributes, ["od_id","o_zone_id","d_zone_id","departure_time","service_date","scenario_id","source_scenario_id","mode_id","nest_id","path_id","network_version","feed_id","feed_version","source_availability","person_trips_panel","ivtt_min","ovtt_min","cost_2010_usd","distance_m","context","input_status","source_cost_status","overlay_applied"]),
        "utility_components.csv": (components, ["od_id","departure_time","scenario_id","mode_id","nest_id","component","contribution","utility_total","path_id"]),
        "nest_components.csv": (nest_rows, ["od_id","departure_time","scenario_id","scale_id","nest_id","mu","inclusive_value","root_logsum"]),
        "od_baseline_probabilities.csv": (probs, ["od_id","departure_time","scenario_id","scale_id","mode_id","nest_id","probability_conditional","person_trips_conditional_engineering_mass","person_trips_panel"]),
        "exclusion_ledger.csv": (ledger, ["od_id","departure_time","scenario_id","person_trips_panel","full_four_mode_case","status","reason","assignment_node_available"]),
        "person_to_vehicle_ledger.csv": (demand_rows, ["od_id","departure_time","scenario_id","scale_id","mode_id","probability_conditional","person_trips_conditional_engineering_mass","occupancy","vehicle_trips","o_node_id","d_node_id","assignment_eligible"]),
        "reference_pivot_comparison.csv": (comparator, ["od_id","departure_time","mode_id","probability_conditional","reference_pivot_unconditional","reference_pivot_four_mode_conditional","specification_change_probability"]),
    }
    for name, (rows, columns) in fields.items():
        write_csv(out / name, rows, columns)
    summary = {"model_id": spec["model_id"], "fixed_panel_objects": cases, "fixed_panel_person_trips": sum(number(x["person_trips_midday_od"], "mass") for x in panel), "scenario": {}, "primary_scale_id": spec["primary_scale_id"], "source_snapshot_sha256": hashlib.sha256((snapshot.parent / "SOURCE_SNAPSHOT_MANIFEST.json").read_bytes()).hexdigest()}
    for scenario in SCENARIO.values():
        selected = [r for r in ledger if r["scenario_id"] == scenario]
        eligible = [r for r in selected if r["full_four_mode_case"]]
        summary["scenario"][scenario] = {"evaluated_objects": len(eligible), "evaluated_engineering_person_trips": sum(r["person_trips_panel"] for r in eligible), "unknown_objects": len(selected)-len(eligible), "unknown_person_trips": sum(r["person_trips_panel"] for r in selected if not r["full_four_mode_case"])}
    (out / "evidence.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
