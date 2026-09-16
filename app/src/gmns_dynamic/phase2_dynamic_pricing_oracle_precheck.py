"""Phase-II dynamic-network pricing-oracle precheck.

This diagnostic inspects whether the accepted second controlled benchmark
time-expanded network can support a demand-specific Phase-II reduced-cost
pricing oracle. It validates schema, known-column cost reconstruction, and
known-candidate reduced-cost reconstruction before optionally running a
diagnostic shortest-path probe.

It does not add columns, re-solve an RMP, run add-resolve, run a CG loop, run
full assignment, or claim full CG/general convergence.
"""

from __future__ import annotations

import csv
import argparse
import heapq
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from build_sioux_harder_bounded_stage2 import ROOT_DIR
from phase1_artificial_rmp_preflight import sha256_file
from phase2_rmp_initialization_diagnostic import rel, write_csv, write_json
from precheck_second_controlled_benchmark_current_pool_rmp import TOL, parse_float


OUTPUT_DIR = ROOT_DIR / "outputs" / "phase2_dynamic_pricing_oracle_precheck"
DEFAULT_OUTPUT_DIR = OUTPUT_DIR
DATA_DIR = ROOT_DIR / "data" / "second_controlled_benchmark_link55"
LOOP_DIR = ROOT_DIR / "outputs" / "phase2_bounded_loop_diagnostic"
CLOSURE_DIR = ROOT_DIR / "outputs" / "phase2_fixed_source_closure_audit"
PHASE2_POOL = ROOT_DIR / "outputs" / "phase1_closure_phase2_handoff_precheck" / "phase2_initial_column_pool.csv"
FIXED_SOURCE = ROOT_DIR / "outputs" / "second_controlled_benchmark_link55_seed_pool_repair" / "repaired_seed_columns.csv"
BASELINE_COLUMNS = DATA_DIR / "dynamic_columns.csv"
PRIOR_CONVENTION = ROOT_DIR / "outputs" / "phase2_pricing_candidate_diagnostic" / "phase2_dual_convention_validation.json"

DYNAMIC_NODE = DATA_DIR / "dynamic_node.csv"
DYNAMIC_ARC = DATA_DIR / "dynamic_arc.csv"
DYNAMIC_DEMAND = DATA_DIR / "dynamic_demand.csv"

COST_RECONSTRUCTION_TOLERANCE = 1e-5
REDUCED_COST_TOLERANCE = 1e-5

REQUIRED_INPUTS = [
    LOOP_DIR / "phase2_bounded_loop_summary.json",
    LOOP_DIR / "phase2_loop_dual_solution_final.json",
    LOOP_DIR / "phase2_loop_solution_by_column_final.csv",
    LOOP_DIR / "phase2_loop_capacity_usage_final.csv",
    LOOP_DIR / "phase2_loop_candidate_scores_by_round.csv",
    CLOSURE_DIR / "phase2_fixed_source_closure_summary.json",
    CLOSURE_DIR / "phase2_pricing_oracle_design_prememo.md",
    PHASE2_POOL,
    FIXED_SOURCE,
    DYNAMIC_NODE,
    DYNAMIC_ARC,
    DYNAMIC_DEMAND,
]

FORBIDDEN_POSITIVE_CLAIMS = [
    "full cg implemented",
    "oracle-based cg converged",
    "global rmp/lp optimum reached",
    "exact arc-lp flow pattern reproduced",
    "full sioux falls assignment solved",
    "production-scale solver completed",
    "gtfs or railway instantiation performed",
    "branch-and-price implemented",
    "reinforcement learning used",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_artifact_path(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else ROOT_DIR / path


def apply_input_manifest(path: str | None) -> None:
    """Apply optional artifact overrides for isolated orchestrator runs."""
    if not path:
        return
    manifest_path = resolve_artifact_path(path)
    if manifest_path is None or not manifest_path.exists():
        raise FileNotFoundError(f"input artifact manifest not found: {path}")
    manifest = read_json(manifest_path)
    artifacts = manifest.get("artifacts", manifest)

    global DATA_DIR, LOOP_DIR, CLOSURE_DIR, PHASE2_POOL, FIXED_SOURCE
    global BASELINE_COLUMNS, PRIOR_CONVENTION, DYNAMIC_NODE, DYNAMIC_ARC, DYNAMIC_DEMAND
    global REQUIRED_INPUTS

    DATA_DIR = resolve_artifact_path(artifacts.get("data_dir")) or DATA_DIR
    LOOP_DIR = resolve_artifact_path(artifacts.get("loop_dir")) or LOOP_DIR
    CLOSURE_DIR = resolve_artifact_path(artifacts.get("closure_dir")) or CLOSURE_DIR
    PHASE2_POOL = resolve_artifact_path(artifacts.get("phase2_pool")) or PHASE2_POOL
    FIXED_SOURCE = resolve_artifact_path(artifacts.get("fixed_source")) or FIXED_SOURCE
    BASELINE_COLUMNS = resolve_artifact_path(artifacts.get("baseline_columns")) or BASELINE_COLUMNS
    PRIOR_CONVENTION = resolve_artifact_path(artifacts.get("prior_convention")) or PRIOR_CONVENTION
    DYNAMIC_NODE = resolve_artifact_path(artifacts.get("dynamic_node")) or DATA_DIR / "dynamic_node.csv"
    DYNAMIC_ARC = resolve_artifact_path(artifacts.get("dynamic_arc")) or DATA_DIR / "dynamic_arc.csv"
    DYNAMIC_DEMAND = resolve_artifact_path(artifacts.get("dynamic_demand")) or DATA_DIR / "dynamic_demand.csv"
    REQUIRED_INPUTS = [
        LOOP_DIR / "phase2_bounded_loop_summary.json",
        LOOP_DIR / "phase2_loop_dual_solution_final.json",
        LOOP_DIR / "phase2_loop_solution_by_column_final.csv",
        LOOP_DIR / "phase2_loop_capacity_usage_final.csv",
        LOOP_DIR / "phase2_loop_candidate_scores_by_round.csv",
        CLOSURE_DIR / "phase2_fixed_source_closure_summary.json",
        CLOSURE_DIR / "phase2_pricing_oracle_design_prememo.md",
        PHASE2_POOL,
        FIXED_SOURCE,
        DYNAMIC_NODE,
        DYNAMIC_ARC,
        DYNAMIC_DEMAND,
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase-II dynamic pricing oracle precheck.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--input-artifacts-json", default=None)
    parser.add_argument("--benchmark-id", default="second_controlled_benchmark_link55")
    parser.add_argument("--no-mutate-accepted-outputs", action="store_true")
    parser.add_argument("--precheck-only", action="store_true")
    return parser.parse_args()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def csv_fields(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        return next(reader)


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def required_input_blockers() -> list[str]:
    blockers: list[str] = []
    for path in REQUIRED_INPUTS:
        if not path.exists() or path.stat().st_size == 0:
            blockers.append(f"missing or empty required input: {rel(path)}")
    return blockers


def arc_sequence(row: dict[str, str]) -> list[str]:
    return [arc for arc in row.get("arc_sequence", "").split("|") if arc]


def finite_float(value: Any) -> float | None:
    number = parse_float(value, math.nan)
    return number if math.isfinite(number) else None


def classify_source_sink_conventions(arcs: list[dict[str, str]], demands: list[dict[str, str]]) -> dict[str, Any]:
    source_by_demand: dict[str, list[dict[str, str]]] = defaultdict(list)
    sink_by_demand: dict[str, list[dict[str, str]]] = defaultdict(list)
    for arc in arcs:
        if arc.get("arc_type") == "source_connector":
            demand_id = arc.get("arc_id", "").replace("source_", "")
            source_by_demand[demand_id].append(arc)
        if arc.get("arc_type") == "sink_connector":
            parts = arc.get("arc_id", "").split("_")
            if len(parts) >= 2:
                sink_by_demand[parts[1]].append(arc)

    demand_rows: list[dict[str, Any]] = []
    for demand in demands:
        demand_id = demand.get("demand_id", "")
        demand_rows.append(
            {
                "demand_id": demand_id,
                "origin_node_id": demand.get("origin_node_id", ""),
                "destination_node_id": demand.get("destination_node_id", ""),
                "departure_time": demand.get("departure_time", ""),
                "source_connector_count": len(source_by_demand.get(demand_id, [])),
                "sink_connector_count": len(sink_by_demand.get(demand_id, [])),
                "source_connector_ids": "|".join(arc.get("arc_id", "") for arc in source_by_demand.get(demand_id, [])),
                "sink_connector_ids_sample": "|".join(
                    arc.get("arc_id", "") for arc in sink_by_demand.get(demand_id, [])[:5]
                ),
            }
        )
    return {
        "source_connector_by_demand": {
            demand_id: [arc.get("arc_id", "") for arc in rows] for demand_id, rows in source_by_demand.items()
        },
        "sink_connector_count_by_demand": {
            demand_id: len(rows) for demand_id, rows in sink_by_demand.items()
        },
        "demand_connector_rows": demand_rows,
    }


def build_schema_inventory(
    nodes: list[dict[str, str]],
    arcs: list[dict[str, str]],
    demands: list[dict[str, str]],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[str]]:
    blockers: list[str] = []
    arc_fields = csv_fields(DYNAMIC_ARC)
    node_fields = csv_fields(DYNAMIC_NODE)
    demand_fields = csv_fields(DYNAMIC_DEMAND)
    arc_type_counts = Counter(arc.get("arc_type", "") for arc in arcs)

    cost_values = [finite_float(arc.get("cost")) for arc in arcs]
    capacity_values = [finite_float(arc.get("capacity")) for arc in arcs]
    if "cost" not in arc_fields or any(value is None for value in cost_values):
        blockers.append("dynamic_arc.csv does not provide finite arc-level cost for every arc")
    if "capacity" not in arc_fields or any(value is None for value in capacity_values):
        blockers.append("dynamic_arc.csv does not provide finite capacity for every arc")
    for field in ["arc_id", "from_node_time_id", "to_node_time_id", "from_time", "to_time", "arc_type"]:
        if field not in arc_fields:
            blockers.append(f"dynamic_arc.csv missing required field: {field}")
    if "physical_link_id" not in arc_fields:
        blockers.append("dynamic_arc.csv missing physical_link_id field")

    connector_info = classify_source_sink_conventions(arcs, demands)
    for row in connector_info["demand_connector_rows"]:
        if row["source_connector_count"] != 1:
            blockers.append(f"demand {row['demand_id']} source connector count is {row['source_connector_count']}")
        if row["sink_connector_count"] < 1:
            blockers.append(f"demand {row['demand_id']} has no sink connectors")

    inventory = {
        "dynamic_node_file": rel(DYNAMIC_NODE),
        "dynamic_arc_file": rel(DYNAMIC_ARC),
        "dynamic_demand_file": rel(DYNAMIC_DEMAND),
        "dynamic_node_row_count": len(nodes),
        "dynamic_arc_row_count": len(arcs),
        "dynamic_demand_row_count": len(demands),
        "dynamic_node_fields": node_fields,
        "dynamic_arc_fields": arc_fields,
        "dynamic_demand_fields": demand_fields,
        "capacity_field": "capacity" if "capacity" in arc_fields else None,
        "time_fields": [field for field in ["from_time", "to_time", "time"] if field in arc_fields or field in node_fields],
        "source_connector_convention": "arc_type=source_connector; arc_id=source_<demand_id>",
        "sink_connector_convention": "arc_type=sink_connector; arc_id=sink_<demand_id>_<destination>_t<time>",
        "waiting_arc_convention": "arc_type=waiting; arc_id=wait_<physical_node_id>_t<from_time>",
        "physical_link_id_field": "physical_link_id" if "physical_link_id" in arc_fields else None,
        "arc_id_format_examples": [arc.get("arc_id", "") for arc in arcs[:5]],
        "arc_type_counts": dict(arc_type_counts),
        "cost_fields_available_at_arc_level": ["cost"] if "cost" in arc_fields else [],
        "generalized_cost_reconstruction_rule": (
            "sum dynamic_arc.cost over the column arc_sequence, including waiting arcs "
            "and zero-cost source/sink connectors"
        ),
        "cost_reconstruction_possible": not blockers,
        "connector_inventory": connector_info["demand_connector_rows"],
        "safe_blockers": blockers,
    }

    cost_rows = [
        {
            "audit_item": "field_presence",
            "field_or_arc_type": "cost",
            "present": bool_text("cost" in arc_fields),
            "row_count": len(arcs),
            "finite_value_count": sum(value is not None for value in cost_values),
            "min_value": min(value for value in cost_values if value is not None) if cost_values else "",
            "max_value": max(value for value in cost_values if value is not None) if cost_values else "",
            "details": "arc-level generalized-cost component",
        },
        {
            "audit_item": "field_presence",
            "field_or_arc_type": "capacity",
            "present": bool_text("capacity" in arc_fields),
            "row_count": len(arcs),
            "finite_value_count": sum(value is not None for value in capacity_values),
            "min_value": min(value for value in capacity_values if value is not None) if capacity_values else "",
            "max_value": max(value for value in capacity_values if value is not None) if capacity_values else "",
            "details": "dynamic capacity field",
        },
    ]
    for arc_type, count in sorted(arc_type_counts.items()):
        values = [finite_float(arc.get("cost")) for arc in arcs if arc.get("arc_type") == arc_type]
        finite = [value for value in values if value is not None]
        cost_rows.append(
            {
                "audit_item": "arc_type_cost_profile",
                "field_or_arc_type": arc_type,
                "present": "true",
                "row_count": count,
                "finite_value_count": len(finite),
                "min_value": min(finite) if finite else "",
                "max_value": max(finite) if finite else "",
                "details": "cost profile by arc type",
            }
        )
    return inventory, cost_rows, blockers


def reconstruct_path_cost(row: dict[str, str], arc_by_id: dict[str, dict[str, str]]) -> tuple[float, list[str], list[str]]:
    missing: list[str] = []
    nonfinite: list[str] = []
    total = 0.0
    for arc_id in arc_sequence(row):
        arc = arc_by_id.get(arc_id)
        if arc is None:
            missing.append(arc_id)
            continue
        cost = finite_float(arc.get("cost"))
        if cost is None:
            nonfinite.append(arc_id)
            continue
        total += cost
    return total, missing, nonfinite


def build_connectivity_audit(
    arcs: list[dict[str, str]],
    demands: list[dict[str, str]],
    final_pool: list[dict[str, str]],
    source_rows: list[dict[str, str]],
) -> tuple[dict[str, Any], list[str]]:
    arc_by_id = {arc.get("arc_id", ""): arc for arc in arcs}
    connector_info = classify_source_sink_conventions(arcs, demands)
    waiting_arcs = [arc for arc in arcs if arc.get("arc_type") == "waiting"]
    movement_arcs = [arc for arc in arcs if arc.get("arc_type") == "movement"]
    source_connectors = [arc for arc in arcs if arc.get("arc_type") == "source_connector"]
    sink_connectors = [arc for arc in arcs if arc.get("arc_type") == "sink_connector"]

    missing_final: dict[str, list[str]] = {}
    missing_source: dict[str, list[str]] = {}
    for row in final_pool:
        missing = [arc_id for arc_id in arc_sequence(row) if arc_id not in arc_by_id]
        if missing:
            missing_final[row.get("column_id", "")] = missing
    for row in source_rows:
        missing = [arc_id for arc_id in arc_sequence(row) if arc_id not in arc_by_id]
        if missing:
            missing_source[row.get("column_id", "")] = missing

    blockers: list[str] = []
    if missing_final:
        blockers.append("accepted final Phase-II columns contain missing dynamic arcs")
    if missing_source:
        blockers.append("fixed repaired-seed candidates contain missing dynamic arcs")
    for demand in demands:
        demand_id = demand.get("demand_id", "")
        if not connector_info["source_connector_by_demand"].get(demand_id):
            blockers.append(f"demand {demand_id} source connector cannot be identified")
        if connector_info["sink_connector_count_by_demand"].get(demand_id, 0) < 1:
            blockers.append(f"demand {demand_id} sink connector cannot be identified")
    if not waiting_arcs:
        blockers.append("waiting arcs cannot be identified")

    audit = {
        "connectivity_status": "PASS" if not blockers else "SAFE_BLOCKED",
        "demand_connector_inventory": connector_info["demand_connector_rows"],
        "source_connector_count": len(source_connectors),
        "sink_connector_count": len(sink_connectors),
        "waiting_arc_count": len(waiting_arcs),
        "movement_arc_count": len(movement_arcs),
        "all_final_column_arcs_exist": not missing_final,
        "missing_arcs_by_final_column": missing_final,
        "all_fixed_source_candidate_arcs_exist": not missing_source,
        "missing_arcs_by_fixed_source_candidate": missing_source,
        "safe_blockers": blockers,
    }
    return audit, blockers


def unique_known_rows(final_pool: list[dict[str, str]], source_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for origin, candidates in [("phase2_final_pool", final_pool), ("fixed_repaired_seed_source", source_rows)]:
        for row in candidates:
            key = (row.get("demand_id", ""), row.get("arc_sequence", ""))
            if key in seen:
                continue
            copy = dict(row)
            copy["known_row_origin"] = origin
            rows.append(copy)
            seen.add(key)
    return rows


def build_cost_reconstruction_audit(
    known_rows: list[dict[str, str]], arc_by_id: dict[str, dict[str, str]]
) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    blockers: list[str] = []
    for row in known_rows:
        reconstructed, missing, nonfinite = reconstruct_path_cost(row, arc_by_id)
        expected = parse_float(row.get("generalized_cost"), math.nan)
        abs_diff = abs(reconstructed - expected) if math.isfinite(expected) else math.inf
        rel_diff = abs_diff / abs(expected) if expected not in [0.0, math.nan] and math.isfinite(expected) else math.inf
        status = "PASS" if not missing and not nonfinite and abs_diff <= COST_RECONSTRUCTION_TOLERANCE else "FAIL"
        if status == "FAIL":
            blockers.append(f"cost reconstruction failed for {row.get('column_id')}")
        rows.append(
            {
                "column_id": row.get("column_id", ""),
                "demand_id": row.get("demand_id", ""),
                "known_row_origin": row.get("known_row_origin", ""),
                "arc_sequence": row.get("arc_sequence", ""),
                "column_generalized_cost": expected,
                "reconstructed_generalized_cost": reconstructed,
                "absolute_difference": abs_diff,
                "relative_difference": rel_diff,
                "tolerance": COST_RECONSTRUCTION_TOLERANCE,
                "missing_arc_count": len(missing),
                "missing_arcs": "|".join(missing),
                "nonfinite_cost_arc_count": len(nonfinite),
                "nonfinite_cost_arcs": "|".join(nonfinite),
                "reconstruction_status": status,
            }
        )
    return rows, blockers


def convention_from_candidate_scores(scores: list[dict[str, str]]) -> tuple[dict[str, Any], list[str]]:
    blockers: list[str] = []
    conventions = {row.get("validated_stationarity_convention", "") for row in scores}
    conventions.discard("")
    eq_signs = {row.get("validated_eq_sign", "") for row in scores}
    eq_signs.discard("")
    capacity_signs = {row.get("validated_capacity_sign", "") for row in scores}
    capacity_signs.discard("")
    if len(conventions) != 1:
        blockers.append(f"candidate score table has inconsistent validated conventions: {sorted(conventions)}")
    if len(eq_signs) != 1 or len(capacity_signs) != 1:
        blockers.append("candidate score table has inconsistent reduced-cost signs")
    convention = next(iter(conventions), "")
    eq_sign = parse_float(next(iter(eq_signs), ""), math.nan)
    cap_sign = parse_float(next(iter(capacity_signs), ""), math.nan)
    if convention != "stationarity_c-1eq-1cap-1lower-1upper":
        blockers.append(f"unexpected convention: {convention}")
    if not math.isfinite(eq_sign) or not math.isfinite(cap_sign):
        blockers.append("validated signs could not be parsed")
    return {
        "validated_convention": convention,
        "eq_sign": eq_sign,
        "capacity_sign": cap_sign,
        "convention_source": rel(LOOP_DIR / "phase2_loop_candidate_scores_by_round.csv"),
    }, blockers


def raw_capacity_dual_sum(arc_ids: list[str], dual_solution: dict[str, Any]) -> float:
    capacity_duals = dual_solution.get("capacity_inequality_duals", {})
    total = 0.0
    for arc_id in arc_ids:
        total += parse_float(capacity_duals.get(arc_id, {}).get("marginal"), 0.0)
    return total


def demand_dual(demand_id: str, dual_solution: dict[str, Any]) -> float:
    return parse_float(dual_solution.get("demand_equality_duals", {}).get(demand_id, {}).get("marginal"), math.nan)


def build_reduced_cost_formula_doc(path: Path, convention: dict[str, Any]) -> None:
    text = f"""# Phase-II Oracle Reduced-Cost Formula

This precheck uses the validated Phase-II stationarity convention read from prior diagnostic outputs:

- convention: `{convention.get('validated_convention')}`
- equality sign: `{convention.get('eq_sign')}`
- capacity sign: `{convention.get('capacity_sign')}`
- source: `{convention.get('convention_source')}`

For a demand-specific candidate path `p` for demand `k`, the diagnostic entry signal is:

`generalized_cost(path) + eq_sign * demand_equality_dual[k] + capacity_sign * sum(capacity_dual[a] for a in path_arcs)`

With the currently validated signs this corresponds to the familiar form:

`generalized_cost(path) - demand_dual[k] - sum(raw_capacity_dual[a] for a in path_arcs)`

The shortest-path probe uses arc weight:

`arc_cost[a] + capacity_sign * raw_capacity_dual[a]`

and applies the demand equality term after path reconstruction. This is a diagnostic precheck formula only; it does not add columns, re-solve an RMP, or certify network-wide pricing closure.
"""
    path.write_text(text, encoding="utf-8")


def build_known_candidate_comparison(
    source_rows: list[dict[str, str]],
    scores: list[dict[str, str]],
    final_round: int,
    arc_by_id: dict[str, dict[str, str]],
    dual_solution: dict[str, Any],
    convention: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    final_scores = {row.get("candidate_id", ""): row for row in scores if int(row.get("round") or -1) == final_round}
    rows: list[dict[str, Any]] = []
    blockers: list[str] = []
    for source in source_rows:
        candidate_id = source.get("column_id", "")
        score = final_scores.get(candidate_id, {})
        reconstructed, missing, nonfinite = reconstruct_path_cost(source, arc_by_id)
        arcs = arc_sequence(source)
        cap_sum = raw_capacity_dual_sum(arcs, dual_solution)
        eq_dual = demand_dual(source.get("demand_id", ""), dual_solution)
        entry_signal = reconstructed + convention["eq_sign"] * eq_dual + convention["capacity_sign"] * cap_sum
        accepted_signal = parse_float(score.get("phase2_entry_signal"), math.nan)
        abs_diff = abs(entry_signal - accepted_signal) if math.isfinite(accepted_signal) else math.inf
        status = (
            "PASS"
            if not missing
            and not nonfinite
            and score
            and abs_diff <= REDUCED_COST_TOLERANCE
            else "FAIL"
        )
        if status == "FAIL":
            blockers.append(f"reduced-cost reconstruction failed for {candidate_id}")
        rows.append(
            {
                "candidate_origin": "fixed_repaired_seed_source",
                "candidate_id": candidate_id,
                "demand_id": source.get("demand_id", ""),
                "path_id": source.get("path_id", ""),
                "classification": score.get("classification", "missing_final_round_score"),
                "duplicate_existing_phase2_final_column": score.get("duplicate_existing_phase2_column", ""),
                "reconstructed_generalized_cost": reconstructed,
                "column_generalized_cost": parse_float(source.get("generalized_cost"), math.nan),
                "equality_dual_raw": eq_dual,
                "capacity_dual_sum_raw": cap_sum,
                "validated_eq_sign": convention["eq_sign"],
                "validated_capacity_sign": convention["capacity_sign"],
                "oracle_style_entry_signal": entry_signal,
                "accepted_final_round_entry_signal": accepted_signal,
                "entry_signal_absolute_difference": abs_diff,
                "tolerance": REDUCED_COST_TOLERANCE,
                "comparison_status": status,
                "missing_arc_count": len(missing),
                "missing_arcs": "|".join(missing),
                "arc_sequence": source.get("arc_sequence", ""),
            }
        )
    return rows, blockers


def dijkstra_shortest_path(
    arcs: list[dict[str, str]],
    start_node: str,
    target_nodes: set[str],
    dual_solution: dict[str, Any],
    capacity_sign: float,
) -> tuple[float, list[str], str | None]:
    adjacency: dict[str, list[tuple[str, str, float]]] = defaultdict(list)
    for arc in arcs:
        arc_id = arc.get("arc_id", "")
        cost = parse_float(arc.get("cost"), math.inf)
        if not math.isfinite(cost):
            continue
        cap_dual = parse_float(dual_solution.get("capacity_inequality_duals", {}).get(arc_id, {}).get("marginal"), 0.0)
        weight = cost + capacity_sign * cap_dual
        if weight < -1e-9:
            # The accepted data should not need negative edge handling; flag by making this edge unusable.
            continue
        adjacency[arc.get("from_node_time_id", "")].append((arc.get("to_node_time_id", ""), arc_id, weight))

    heap: list[tuple[float, str]] = [(0.0, start_node)]
    distances: dict[str, float] = {start_node: 0.0}
    predecessor: dict[str, tuple[str, str]] = {}
    best_target: str | None = None

    while heap:
        distance, node = heapq.heappop(heap)
        if distance > distances.get(node, math.inf) + 1e-12:
            continue
        if node in target_nodes:
            best_target = node
            break
        for to_node, arc_id, weight in adjacency.get(node, []):
            new_distance = distance + weight
            if new_distance + 1e-12 < distances.get(to_node, math.inf):
                distances[to_node] = new_distance
                predecessor[to_node] = (node, arc_id)
                heapq.heappush(heap, (new_distance, to_node))

    if best_target is None:
        return math.inf, [], None

    path_arcs: list[str] = []
    node = best_target
    while node != start_node:
        prev_node, arc_id = predecessor[node]
        path_arcs.append(arc_id)
        node = prev_node
    path_arcs.reverse()
    return distances[best_target], path_arcs, best_target


def classify_oracle_path(
    demand_id: str,
    path_arcs: list[str],
    reduced_cost: float,
    final_pool: list[dict[str, str]],
    source_rows: list[dict[str, str]],
) -> tuple[str, str]:
    sequence = "|".join(path_arcs)
    for row in final_pool:
        if row.get("demand_id") == demand_id and row.get("arc_sequence") == sequence:
            return "duplicate_existing_phase2_final_column", row.get("column_id", "")
    for row in source_rows:
        if row.get("demand_id") == demand_id and row.get("arc_sequence") == sequence:
            return "matches_known_fixed_source_candidate", row.get("column_id", "")
    if reduced_cost < -REDUCED_COST_TOLERANCE:
        return "new_oracle_candidate", ""
    if math.isfinite(reduced_cost):
        return "nonimproving_oracle_candidate", ""
    return "invalid_oracle_candidate", ""


def run_shortest_path_probe(
    arcs: list[dict[str, str]],
    demands: list[dict[str, str]],
    final_pool: list[dict[str, str]],
    source_rows: list[dict[str, str]],
    dual_solution: dict[str, Any],
    convention: dict[str, Any],
) -> list[dict[str, Any]]:
    source_connectors = {
        arc.get("arc_id", "").replace("source_", ""): arc
        for arc in arcs
        if arc.get("arc_type") == "source_connector"
    }
    sink_targets: dict[str, set[str]] = defaultdict(set)
    for arc in arcs:
        if arc.get("arc_type") != "sink_connector":
            continue
        parts = arc.get("arc_id", "").split("_")
        if len(parts) >= 2:
            sink_targets[parts[1]].add(arc.get("to_node_time_id", ""))

    probe_rows: list[dict[str, Any]] = []
    for demand in demands:
        demand_id = demand.get("demand_id", "")
        source = source_connectors.get(demand_id)
        targets = sink_targets.get(demand_id, set())
        if source is None or not targets:
            probe_rows.append(
                {
                    "demand_id": demand_id,
                    "probe_status": "SAFE_BLOCKED",
                    "start_node": source.get("from_node_time_id", "") if source else "",
                    "target_node": "",
                    "arc_sequence": "",
                    "reconstructed_generalized_cost": "",
                    "capacity_dual_sum_raw": "",
                    "demand_equality_dual_raw": "",
                    "validated_eq_sign": convention["eq_sign"],
                    "validated_capacity_sign": convention["capacity_sign"],
                    "oracle_entry_signal": "",
                    "classification": "invalid_oracle_candidate",
                    "matched_candidate_id": "",
                    "diagnostic_only": "true",
                    "would_be_added_in_future_task": "false",
                    "blocker": "missing source or sink connector",
                }
            )
            continue
        start_node = source.get("from_node_time_id", "")
        _, path_arcs, target_node = dijkstra_shortest_path(
            arcs, start_node, targets, dual_solution, convention["capacity_sign"]
        )
        if not path_arcs:
            probe_rows.append(
                {
                    "demand_id": demand_id,
                    "probe_status": "SAFE_BLOCKED",
                    "start_node": start_node,
                    "target_node": "",
                    "arc_sequence": "",
                    "reconstructed_generalized_cost": "",
                    "capacity_dual_sum_raw": "",
                    "demand_equality_dual_raw": "",
                    "validated_eq_sign": convention["eq_sign"],
                    "validated_capacity_sign": convention["capacity_sign"],
                    "oracle_entry_signal": "",
                    "classification": "invalid_oracle_candidate",
                    "matched_candidate_id": "",
                    "diagnostic_only": "true",
                    "would_be_added_in_future_task": "false",
                    "blocker": "shortest path could not be found",
                }
            )
            continue
        path_row = {"arc_sequence": "|".join(path_arcs), "demand_id": demand_id}
        arc_by_id = {arc.get("arc_id", ""): arc for arc in arcs}
        reconstructed, _, _ = reconstruct_path_cost(path_row, arc_by_id)
        cap_sum = raw_capacity_dual_sum(path_arcs, dual_solution)
        eq_dual = demand_dual(demand_id, dual_solution)
        entry_signal = reconstructed + convention["eq_sign"] * eq_dual + convention["capacity_sign"] * cap_sum
        classification, matched_id = classify_oracle_path(
            demand_id, path_arcs, entry_signal, final_pool, source_rows
        )
        probe_rows.append(
            {
                "demand_id": demand_id,
                "probe_status": "PASS",
                "start_node": start_node,
                "target_node": target_node or "",
                "arc_sequence": "|".join(path_arcs),
                "reconstructed_generalized_cost": reconstructed,
                "capacity_dual_sum_raw": cap_sum,
                "demand_equality_dual_raw": eq_dual,
                "validated_eq_sign": convention["eq_sign"],
                "validated_capacity_sign": convention["capacity_sign"],
                "oracle_entry_signal": entry_signal,
                "classification": classification,
                "matched_candidate_id": matched_id,
                "diagnostic_only": "true",
                "would_be_added_in_future_task": "false",
                "blocker": "",
            }
        )
    return probe_rows


def write_duplicate_filtering_plan(path: Path) -> None:
    path.write_text(
        """# Phase-II Oracle Duplicate Filtering Plan

The oracle precheck treats a diagnostic shortest-path result as a duplicate when the same demand and the exact dynamic arc sequence already exist in the current final Phase-II pool.

Planned future policy:

- compare `(demand_id, arc_sequence)` against the active Phase-II RMP pool before any add-resolve task;
- separately label paths that match the fixed repaired-seed source but are not yet in a future pool;
- reject artificial variables as pricing candidates;
- preserve output-only diagnostics until a separately scoped add-resolve task is accepted;
- never write oracle candidates into `phase2_initial_column_pool.csv` or baseline `dynamic_columns.csv` during a precheck.
""",
        encoding="utf-8",
    )


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Phase-II Dynamic Pricing Oracle Precheck",
        "",
        f"Diagnostic status: {summary['diagnostic_status']}",
        "",
        "This precheck audits the time-expanded network schema, known-column cost reconstruction, reduced-cost reconstruction, and a diagnostic shortest-path probe when all gates pass.",
        "",
        "It does not add columns, re-solve the RMP, run add-resolve, run a CG loop, run full assignment, or claim full CG/general convergence.",
        "",
        "## Gate Results",
        "",
        f"- Schema inventory: {summary['schema_inventory_status']}",
        f"- Connectivity audit: {summary['connectivity_audit_status']}",
        f"- Known-column cost reconstruction: {summary['known_column_cost_reconstruction_status']}",
        f"- Known-candidate reduced-cost reconstruction: {summary['known_candidate_reduced_cost_reconstruction_status']}",
        f"- Shortest-path probe run: {summary['shortest_path_probe_run']}",
        "",
        "## Probe Result",
        "",
        f"- Oracle-precheck negative reduced-cost non-duplicate found: {summary['oracle_precheck_negative_reduced_cost_nonduplicate_found']}",
        f"- Probe classifications: {summary['shortest_path_probe_classification_counts']}",
        "",
        "A negative non-duplicate probe result, if present, is only a candidate for a separately scoped one-candidate oracle add-resolve diagnostic.",
        "",
        "## Hash Guard",
        "",
        f"- Phase-II initial pool mutated: {summary['phase2_initial_pool_mutated']}",
        f"- Baseline dynamic columns mutated: {summary['baseline_dynamic_columns_mutated']}",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    if args.benchmark_id != "second_controlled_benchmark_link55":
        print(f"Unsupported benchmark id: {args.benchmark_id}")
        return 1
    global OUTPUT_DIR
    OUTPUT_DIR = resolve_artifact_path(args.output_dir) or DEFAULT_OUTPUT_DIR
    if args.no_mutate_accepted_outputs and OUTPUT_DIR.resolve() == DEFAULT_OUTPUT_DIR.resolve():
        print("Refusing to write to accepted default output folder with --no-mutate-accepted-outputs.")
        return 1
    apply_input_manifest(args.input_artifacts_json)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    phase2_pool_hash_before = sha256_file(PHASE2_POOL) if PHASE2_POOL.exists() else ""
    baseline_hash_before = sha256_file(BASELINE_COLUMNS) if BASELINE_COLUMNS.exists() else ""

    blockers = required_input_blockers()
    if blockers:
        summary = {
            "diagnostic_status": "SAFE_BLOCKED",
            "safe_blockers": blockers,
            "shortest_path_probe_run": False,
            "generated_columns_added_to_any_rmp": False,
            "add_resolve_run": False,
            "cg_loop_run": False,
            "full_assignment_run": False,
            "full_cg_run": False,
        }
        write_json(OUTPUT_DIR / "phase2_pricing_oracle_precheck_summary.json", summary)
        write_json(OUTPUT_DIR / "phase2_oracle_blockers.json", {"safe_blockers": blockers})
        print("Phase-II dynamic pricing oracle precheck status: SAFE_BLOCKED")
        return 1

    nodes = read_csv_rows(DYNAMIC_NODE)
    arcs = read_csv_rows(DYNAMIC_ARC)
    demands = read_csv_rows(DYNAMIC_DEMAND)
    final_pool = read_csv_rows(LOOP_DIR / "phase2_loop_temporary_pool_final.csv")
    source_rows = read_csv_rows(FIXED_SOURCE)
    candidate_scores = read_csv_rows(LOOP_DIR / "phase2_loop_candidate_scores_by_round.csv")
    dual_solution = read_json(LOOP_DIR / "phase2_loop_dual_solution_final.json")
    loop_summary = read_json(LOOP_DIR / "phase2_bounded_loop_summary.json")
    closure_summary = read_json(CLOSURE_DIR / "phase2_fixed_source_closure_summary.json")

    arc_by_id = {arc.get("arc_id", ""): arc for arc in arcs}
    schema_inventory, arc_cost_rows, schema_blockers = build_schema_inventory(nodes, arcs, demands)
    connectivity_audit, connectivity_blockers = build_connectivity_audit(arcs, demands, final_pool, source_rows)
    known_rows = unique_known_rows(final_pool, source_rows)
    cost_rows, cost_blockers = build_cost_reconstruction_audit(known_rows, arc_by_id)
    convention, convention_blockers = convention_from_candidate_scores(candidate_scores)
    final_round = max((int(row.get("round") or 0) for row in candidate_scores), default=0)
    comparison_rows, rc_blockers = build_known_candidate_comparison(
        source_rows, candidate_scores, final_round, arc_by_id, dual_solution, convention
    )

    gate_blockers = schema_blockers + connectivity_blockers + cost_blockers + convention_blockers + rc_blockers
    probe_run = not gate_blockers
    probe_rows: list[dict[str, Any]]
    if probe_run:
        probe_rows = run_shortest_path_probe(arcs, demands, final_pool, source_rows, dual_solution, convention)
    else:
        probe_rows = [
            {
                "demand_id": demand.get("demand_id", ""),
                "probe_status": "SAFE_BLOCKED",
                "start_node": "",
                "target_node": "",
                "arc_sequence": "",
                "reconstructed_generalized_cost": "",
                "capacity_dual_sum_raw": "",
                "demand_equality_dual_raw": "",
                "validated_eq_sign": convention.get("eq_sign", ""),
                "validated_capacity_sign": convention.get("capacity_sign", ""),
                "oracle_entry_signal": "",
                "classification": "blocked_schema_or_cost_mismatch",
                "matched_candidate_id": "",
                "diagnostic_only": "true",
                "would_be_added_in_future_task": "false",
                "blocker": "; ".join(gate_blockers),
            }
            for demand in demands
        ]

    for probe in probe_rows:
        comparison_rows.append(
            {
                "candidate_origin": "oracle_shortest_path_probe",
                "candidate_id": f"ORACLE_PROBE_{probe.get('demand_id')}",
                "demand_id": probe.get("demand_id", ""),
                "path_id": "",
                "classification": probe.get("classification", ""),
                "duplicate_existing_phase2_final_column": bool_text(
                    probe.get("classification") == "duplicate_existing_phase2_final_column"
                ),
                "reconstructed_generalized_cost": probe.get("reconstructed_generalized_cost", ""),
                "column_generalized_cost": "",
                "equality_dual_raw": probe.get("demand_equality_dual_raw", ""),
                "capacity_dual_sum_raw": probe.get("capacity_dual_sum_raw", ""),
                "validated_eq_sign": probe.get("validated_eq_sign", ""),
                "validated_capacity_sign": probe.get("validated_capacity_sign", ""),
                "oracle_style_entry_signal": probe.get("oracle_entry_signal", ""),
                "accepted_final_round_entry_signal": "",
                "entry_signal_absolute_difference": "",
                "tolerance": REDUCED_COST_TOLERANCE,
                "comparison_status": probe.get("probe_status", ""),
                "missing_arc_count": "",
                "missing_arcs": "",
                "arc_sequence": probe.get("arc_sequence", ""),
            }
        )

    phase2_pool_hash_after = sha256_file(PHASE2_POOL)
    baseline_hash_after = sha256_file(BASELINE_COLUMNS)
    phase2_pool_mutated = phase2_pool_hash_before != phase2_pool_hash_after
    baseline_mutated = baseline_hash_before != baseline_hash_after
    classification_counts = Counter(str(row.get("classification", "")) for row in probe_rows)
    negative_new_probe = any(
        row.get("classification") == "new_oracle_candidate"
        and parse_float(row.get("oracle_entry_signal"), math.inf) < -REDUCED_COST_TOLERANCE
        for row in probe_rows
    )

    summary_blockers = list(gate_blockers)
    if phase2_pool_mutated:
        summary_blockers.append("phase2_initial_column_pool.csv hash changed")
    if baseline_mutated:
        summary_blockers.append("baseline dynamic_columns.csv hash changed")
    if loop_summary.get("diagnostic_status") != "PASS":
        summary_blockers.append("accepted bounded loop summary no longer reports PASS")
    if closure_summary.get("diagnostic_status") != "PASS":
        summary_blockers.append("accepted fixed-source closure summary no longer reports PASS")

    diagnostic_status = "PASS" if not summary_blockers else "SAFE_BLOCKED"
    hash_audit = {
        "phase2_initial_pool_path": rel(PHASE2_POOL),
        "phase2_initial_pool_hash_before": phase2_pool_hash_before,
        "phase2_initial_pool_hash_after": phase2_pool_hash_after,
        "phase2_initial_pool_mutated": phase2_pool_mutated,
        "baseline_dynamic_columns_path": rel(BASELINE_COLUMNS),
        "baseline_dynamic_columns_hash_before": baseline_hash_before,
        "baseline_dynamic_columns_hash_after": baseline_hash_after,
        "baseline_dynamic_columns_mutated": baseline_mutated,
        "bounded_loop_outputs_mutated_by_this_precheck": False,
        "fixed_source_closure_outputs_mutated_by_this_precheck": False,
        "generated_columns_added_to_any_rmp": False,
        "add_resolve_run": False,
        "cg_loop_run": False,
        "full_assignment_run": False,
        "full_cg_run": False,
    }
    blockers_json = {
        "diagnostic_status": diagnostic_status,
        "schema_blockers": schema_blockers,
        "connectivity_blockers": connectivity_blockers,
        "cost_reconstruction_blockers": cost_blockers,
        "convention_blockers": convention_blockers,
        "reduced_cost_reconstruction_blockers": rc_blockers,
        "safe_blockers": summary_blockers,
        "shortest_path_probe_run": probe_run,
    }
    summary = {
        "diagnostic_status": diagnostic_status,
        "schema_inventory_status": "PASS" if not schema_blockers else "SAFE_BLOCKED",
        "connectivity_audit_status": connectivity_audit["connectivity_status"],
        "known_column_cost_reconstruction_status": "PASS" if not cost_blockers else "SAFE_BLOCKED",
        "known_candidate_reduced_cost_reconstruction_status": "PASS" if not rc_blockers else "SAFE_BLOCKED",
        "validated_convention": convention.get("validated_convention", ""),
        "validated_eq_sign": convention.get("eq_sign", ""),
        "validated_capacity_sign": convention.get("capacity_sign", ""),
        "shortest_path_probe_run": probe_run,
        "shortest_path_probe_classification_counts": dict(classification_counts),
        "oracle_precheck_negative_reduced_cost_nonduplicate_found": negative_new_probe,
        "oracle_precheck_candidate_found_requires_separate_add_resolve": negative_new_probe,
        "dynamic_network_data_dir": rel(DATA_DIR),
        "dynamic_arc_count": len(arcs),
        "dynamic_node_count": len(nodes),
        "dynamic_demand_count": len(demands),
        "known_column_reconstruction_row_count": len(cost_rows),
        "known_candidate_comparison_row_count": len(comparison_rows),
        "phase2_initial_pool_hash_before": phase2_pool_hash_before,
        "phase2_initial_pool_hash_after": phase2_pool_hash_after,
        "phase2_initial_pool_mutated": phase2_pool_mutated,
        "baseline_dynamic_columns_hash_before": baseline_hash_before,
        "baseline_dynamic_columns_hash_after": baseline_hash_after,
        "baseline_dynamic_columns_mutated": baseline_mutated,
        "generated_columns_added_to_any_rmp": False,
        "oracle_generated_columns_added_to_phase2_initial_pool": False,
        "oracle_generated_columns_added_to_baseline": False,
        "rmp_resolved_after_oracle_probe": False,
        "add_resolve_run": False,
        "cg_loop_run": False,
        "full_assignment_run": False,
        "full_cg_run": False,
        "general_convergence_claimed": False,
        "global_pricing_closure_claimed": False,
        "exact_arc_lp_flow_pattern_reproduction_claimed": False,
        "safe_blockers": summary_blockers,
        "next_safe_step": (
            "separately scoped one-candidate oracle add-resolve diagnostic"
            if negative_new_probe
            else "pricing-oracle design review or broader oracle validation precheck"
        ),
        "scope": (
            "Phase-II dynamic-network pricing-oracle precheck only. It audits schema, "
            "known cost and reduced-cost reconstruction, and a diagnostic shortest-path "
            "probe without adding columns, re-solving an RMP, running add-resolve, "
            "running a loop, full assignment, full CG, or making a general convergence claim."
        ),
    }

    write_json(OUTPUT_DIR / "phase2_dynamic_network_schema_inventory.json", schema_inventory)
    write_csv(
        OUTPUT_DIR / "phase2_dynamic_arc_cost_schema_audit.csv",
        arc_cost_rows,
        ["audit_item", "field_or_arc_type", "present", "row_count", "finite_value_count", "min_value", "max_value", "details"],
    )
    write_json(OUTPUT_DIR / "phase2_dynamic_node_arc_connectivity_audit.json", connectivity_audit)
    build_reduced_cost_formula_doc(OUTPUT_DIR / "phase2_oracle_reduced_cost_formula.md", convention)
    write_csv(
        OUTPUT_DIR / "phase2_oracle_known_column_reconstruction_audit.csv",
        cost_rows,
        [
            "column_id",
            "demand_id",
            "known_row_origin",
            "arc_sequence",
            "column_generalized_cost",
            "reconstructed_generalized_cost",
            "absolute_difference",
            "relative_difference",
            "tolerance",
            "missing_arc_count",
            "missing_arcs",
            "nonfinite_cost_arc_count",
            "nonfinite_cost_arcs",
            "reconstruction_status",
        ],
    )
    write_csv(
        OUTPUT_DIR / "phase2_oracle_known_candidate_comparison.csv",
        comparison_rows,
        [
            "candidate_origin",
            "candidate_id",
            "demand_id",
            "path_id",
            "classification",
            "duplicate_existing_phase2_final_column",
            "reconstructed_generalized_cost",
            "column_generalized_cost",
            "equality_dual_raw",
            "capacity_dual_sum_raw",
            "validated_eq_sign",
            "validated_capacity_sign",
            "oracle_style_entry_signal",
            "accepted_final_round_entry_signal",
            "entry_signal_absolute_difference",
            "tolerance",
            "comparison_status",
            "missing_arc_count",
            "missing_arcs",
            "arc_sequence",
        ],
    )
    write_csv(
        OUTPUT_DIR / "phase2_oracle_shortest_path_probe.csv",
        probe_rows,
        [
            "demand_id",
            "probe_status",
            "start_node",
            "target_node",
            "arc_sequence",
            "reconstructed_generalized_cost",
            "capacity_dual_sum_raw",
            "demand_equality_dual_raw",
            "validated_eq_sign",
            "validated_capacity_sign",
            "oracle_entry_signal",
            "classification",
            "matched_candidate_id",
            "diagnostic_only",
            "would_be_added_in_future_task",
            "blocker",
        ],
    )
    write_duplicate_filtering_plan(OUTPUT_DIR / "phase2_oracle_duplicate_filtering_plan.md")
    write_json(OUTPUT_DIR / "phase2_oracle_blockers.json", blockers_json)
    write_json(OUTPUT_DIR / "phase2_oracle_hash_audit.json", hash_audit)
    write_json(OUTPUT_DIR / "phase2_pricing_oracle_precheck_summary.json", summary)
    write_report(OUTPUT_DIR / "phase2_pricing_oracle_precheck_report.md", summary)

    print(f"Phase-II dynamic pricing oracle precheck status: {diagnostic_status}")
    print(f"Summary: {OUTPUT_DIR / 'phase2_pricing_oracle_precheck_summary.json'}")
    return 0 if diagnostic_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
