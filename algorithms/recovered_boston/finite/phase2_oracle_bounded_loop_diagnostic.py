"""Bounded oracle Phase-II loop diagnostic.

This diagnostic starts from the accepted fixed-source Phase-II final pool,
re-solves the real-only RMP, runs demand-specific dynamic-network reduced-cost
shortest-path probes, and adds at most one negative reduced-cost non-duplicate
oracle path per round to a temporary pool.

It does not mutate baseline data, mutate accepted pools, run full assignment,
run full CG, claim global convergence, or prove global pricing closure.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from build_sioux_harder_bounded_stage2 import ROOT_DIR
from phase1_artificial_rmp_preflight import sha256_file
from phase1_one_candidate_add_resolve import ACCEPTED_BASELINE_HASH
from phase2_dynamic_pricing_oracle_precheck import (
    build_connectivity_audit,
    build_cost_reconstruction_audit,
    build_known_candidate_comparison,
    build_schema_inventory,
    convention_from_candidate_scores,
    demand_dual,
    raw_capacity_dual_sum,
    reconstruct_path_cost,
    unique_known_rows,
)
from phase2_oracle_one_candidate_add_resolve import (
    EXPECTED_OBJECTIVE_BEFORE,
    FIXED_SOURCE_OUTPUTS,
)
from phase2_pricing_candidate_diagnostic import validate_convention, variable_catalog_rows
from phase2_rmp_initialization_diagnostic import (
    build_dual_solution,
    build_solution_outputs,
    choose_cost_field,
    rel,
    solve_phase2_rmp,
    write_csv,
    write_json,
)
from precheck_second_controlled_benchmark_current_pool_rmp import (
    DEFAULT_CONFIG as DEFAULT_CURRENT_POOL_CONFIG,
    TOL,
    input_data_dir,
    load_config,
    parse_float,
    read_csv,
    split_sequence,
)


OUTPUT_DIR = ROOT_DIR / "outputs" / "phase2_oracle_bounded_loop_diagnostic"
DEFAULT_OUTPUT_DIR = OUTPUT_DIR
DATA_DIR = ROOT_DIR / "data" / "second_controlled_benchmark_link55"
ORACLE_PRECHECK_DIR = ROOT_DIR / "outputs" / "phase2_dynamic_pricing_oracle_precheck"
ORACLE_ONE_CANDIDATE_DIR = ROOT_DIR / "outputs" / "phase2_oracle_one_candidate_add_resolve"
FIXED_SOURCE_LOOP_DIR = ROOT_DIR / "outputs" / "phase2_bounded_loop_diagnostic"
FIXED_SOURCE_CLOSURE_DIR = ROOT_DIR / "outputs" / "phase2_fixed_source_closure_audit"
HANDOFF_DIR = ROOT_DIR / "outputs" / "phase1_closure_phase2_handoff_precheck"
PHASE2_INITIAL_POOL = HANDOFF_DIR / "phase2_initial_column_pool.csv"
FIXED_SOURCE_FINAL_POOL = FIXED_SOURCE_LOOP_DIR / "phase2_loop_temporary_pool_final.csv"
FIXED_SOURCE = ROOT_DIR / "outputs" / "second_controlled_benchmark_link55_seed_pool_repair" / "repaired_seed_columns.csv"
BASELINE_COLUMNS = DATA_DIR / "dynamic_columns.csv"
DYNAMIC_NODE = DATA_DIR / "dynamic_node.csv"
DYNAMIC_ARC = DATA_DIR / "dynamic_arc.csv"
DYNAMIC_DEMAND = DATA_DIR / "dynamic_demand.csv"

DEFAULT_MAX_ROUNDS = 8
ARC_LP_REFERENCE_OBJECTIVE = 387035720.2902111
FIXED_SOURCE_FINAL_OBJECTIVE_REFERENCE = 393772231.32911855
ALLOW_VARIABLE_FIXED_SOURCE_BASE = False
ALLOW_VARIABLE_ORACLE_CANDIDATE = False
ALLOW_VARIABLE_INITIAL_ORACLE_LOOP_OBJECTIVE = False
STOP_NO_NEGATIVE = "no_negative_reduced_cost_nondeduplicate_oracle_path"
ALLOWED_STOP_REASONS = {STOP_NO_NEGATIVE, "max_rounds_reached", "safe_blocker"}
REDUCED_COST_TOLERANCE = 1e-5
ARC_LP_COMPARISON_TOLERANCE = 1e-5

REQUIRED_INPUTS: list[Path] = []

SCOPE_BOUNDARY = (
    "This is a bounded oracle Phase-II loop diagnostic. It repeatedly solves "
    "the real-only RMP, runs demand-specific dynamic-network reduced-cost "
    "shortest-path probes, and adds at most one negative reduced-cost "
    "non-duplicate oracle path per round to a temporary pool. It does not "
    "mutate baseline data or accepted pools, run full assignment, run full CG, "
    "claim general convergence, claim global optimality, or prove exact "
    "arc-LP flow-pattern reproduction."
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def resolve_artifact_path(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else ROOT_DIR / path


def refresh_required_inputs() -> None:
    global REQUIRED_INPUTS
    REQUIRED_INPUTS = [
        ORACLE_ONE_CANDIDATE_DIR / "phase2_oracle_one_candidate_add_resolve_summary.json",
        ORACLE_PRECHECK_DIR / "phase2_pricing_oracle_precheck_summary.json",
        ORACLE_PRECHECK_DIR / "phase2_oracle_shortest_path_probe.csv",
        FIXED_SOURCE_LOOP_DIR / "phase2_bounded_loop_summary.json",
        FIXED_SOURCE_LOOP_DIR / "phase2_loop_dual_solution_final.json",
        FIXED_SOURCE_LOOP_DIR / "phase2_loop_solution_by_column_final.csv",
        FIXED_SOURCE_LOOP_DIR / "phase2_loop_capacity_usage_final.csv",
        FIXED_SOURCE_LOOP_DIR / "phase2_loop_candidate_scores_by_round.csv",
        FIXED_SOURCE_LOOP_DIR / "phase2_loop_temporary_pool_final.csv",
        FIXED_SOURCE_CLOSURE_DIR / "phase2_fixed_source_closure_summary.json",
        PHASE2_INITIAL_POOL,
        FIXED_SOURCE,
        BASELINE_COLUMNS,
        DYNAMIC_NODE,
        DYNAMIC_ARC,
        DYNAMIC_DEMAND,
    ]


def apply_input_manifest(path: str | None) -> dict[str, Any]:
    if not path:
        refresh_required_inputs()
        return {}
    manifest_path = resolve_artifact_path(path)
    if manifest_path is None or not manifest_path.exists():
        raise FileNotFoundError(f"input artifact manifest not found: {path}")
    manifest = read_json(manifest_path)
    artifacts = manifest.get("artifacts", manifest)
    global DATA_DIR, ORACLE_PRECHECK_DIR, ORACLE_ONE_CANDIDATE_DIR, FIXED_SOURCE_LOOP_DIR
    global FIXED_SOURCE_CLOSURE_DIR, HANDOFF_DIR, PHASE2_INITIAL_POOL, FIXED_SOURCE_FINAL_POOL
    global FIXED_SOURCE, BASELINE_COLUMNS, DYNAMIC_NODE, DYNAMIC_ARC, DYNAMIC_DEMAND
    global ALLOW_VARIABLE_FIXED_SOURCE_BASE, ALLOW_VARIABLE_ORACLE_CANDIDATE
    global ALLOW_VARIABLE_INITIAL_ORACLE_LOOP_OBJECTIVE

    DATA_DIR = resolve_artifact_path(artifacts.get("data_dir")) or DATA_DIR
    ORACLE_PRECHECK_DIR = resolve_artifact_path(artifacts.get("oracle_precheck_dir")) or ORACLE_PRECHECK_DIR
    ORACLE_ONE_CANDIDATE_DIR = (
        resolve_artifact_path(artifacts.get("oracle_one_candidate_dir")) or ORACLE_ONE_CANDIDATE_DIR
    )
    FIXED_SOURCE_LOOP_DIR = resolve_artifact_path(artifacts.get("fixed_source_loop_dir")) or FIXED_SOURCE_LOOP_DIR
    FIXED_SOURCE_CLOSURE_DIR = (
        resolve_artifact_path(artifacts.get("fixed_source_closure_dir")) or FIXED_SOURCE_CLOSURE_DIR
    )
    HANDOFF_DIR = resolve_artifact_path(artifacts.get("handoff_dir")) or HANDOFF_DIR
    PHASE2_INITIAL_POOL = resolve_artifact_path(artifacts.get("phase2_initial_pool")) or PHASE2_INITIAL_POOL
    FIXED_SOURCE_FINAL_POOL = (
        resolve_artifact_path(artifacts.get("fixed_source_final_pool"))
        or resolve_artifact_path(artifacts.get("phase2_base_pool"))
        or FIXED_SOURCE_FINAL_POOL
    )
    FIXED_SOURCE = resolve_artifact_path(artifacts.get("fixed_source")) or FIXED_SOURCE
    BASELINE_COLUMNS = resolve_artifact_path(artifacts.get("baseline_columns")) or BASELINE_COLUMNS
    DYNAMIC_NODE = resolve_artifact_path(artifacts.get("dynamic_node")) or (DATA_DIR / "dynamic_node.csv")
    DYNAMIC_ARC = resolve_artifact_path(artifacts.get("dynamic_arc")) or (DATA_DIR / "dynamic_arc.csv")
    DYNAMIC_DEMAND = resolve_artifact_path(artifacts.get("dynamic_demand")) or (DATA_DIR / "dynamic_demand.csv")
    ALLOW_VARIABLE_FIXED_SOURCE_BASE = bool(artifacts.get("allow_variable_fixed_source_base", False))
    ALLOW_VARIABLE_ORACLE_CANDIDATE = bool(artifacts.get("allow_variable_oracle_candidate", False))
    ALLOW_VARIABLE_INITIAL_ORACLE_LOOP_OBJECTIVE = bool(
        artifacts.get("allow_variable_initial_oracle_loop_objective", False)
    )
    refresh_required_inputs()
    return artifacts


refresh_required_inputs()


def fixed_source_output_hashes() -> dict[str, str]:
    paths = [
        FIXED_SOURCE_LOOP_DIR / "phase2_bounded_loop_summary.json",
        FIXED_SOURCE_LOOP_DIR / "phase2_loop_solution_by_column_final.csv",
        FIXED_SOURCE_LOOP_DIR / "phase2_loop_capacity_usage_final.csv",
        FIXED_SOURCE_LOOP_DIR / "phase2_loop_hash_audit.json",
        FIXED_SOURCE_LOOP_DIR / "phase2_loop_temporary_pool_final.csv",
        FIXED_SOURCE_CLOSURE_DIR / "phase2_fixed_source_closure_summary.json",
    ]
    return {rel(path): sha256_file(path) for path in paths if path.exists()}


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def required_input_blockers() -> list[str]:
    blockers: list[str] = []
    for path in REQUIRED_INPUTS:
        if not path.exists() or path.stat().st_size == 0:
            blockers.append(f"missing or empty required input: {rel(path)}")
    return blockers


def empty_solution_outputs() -> dict[str, Any]:
    return {
        "solution_by_column": [],
        "demand_balance": [],
        "capacity_usage": [],
        "cost_breakdown": [],
        "positive_flow_by_demand": {},
        "positive_flow_column_count": None,
        "demand_residual_max": math.nan,
        "capacity_violation_count": None,
        "max_capacity_violation": math.nan,
    }


def solve_current_pool(
    arcs: list[dict[str, str]],
    demands: list[dict[str, str]],
    pool: list[dict[str, str]],
) -> dict[str, Any]:
    cost_field, costs, cost_blockers = choose_cost_field(pool)
    if cost_blockers:
        return {
            "solver_info": {"solver_status": "precheck_blocked", "objective_value": None},
            "solution_outputs": empty_solution_outputs(),
            "dual_solution": {"dual_fields_present": False, "safe_blockers": cost_blockers},
            "validation": {"validation_status": "SAFE_BLOCKED", "safe_blockers": cost_blockers},
            "stationarity_rows": [],
            "safe_blocker": "; ".join(cost_blockers),
        }

    solver_info, result, solve_blockers = solve_phase2_rmp(arcs, demands, pool, costs)
    if solve_blockers or result is None or not getattr(result, "success", False):
        blockers = solve_blockers or [f"Phase-II RMP solve failed: {solver_info.get('solver_status')}"]
        return {
            "solver_info": solver_info,
            "solution_outputs": empty_solution_outputs(),
            "dual_solution": {"dual_fields_present": False, "safe_blockers": blockers},
            "validation": {"validation_status": "SAFE_BLOCKED", "safe_blockers": blockers},
            "stationarity_rows": [],
            "safe_blocker": "; ".join(blockers),
        }

    values = [float(value) for value in result.x]
    solution_outputs = build_solution_outputs(arcs, demands, pool, costs, values, cost_field)
    dual_solution = build_dual_solution(result, arcs, demands, pool)
    catalog_rows = variable_catalog_rows(pool, solution_outputs["solution_by_column"], dual_solution)
    validation, stationarity_rows, validation_blockers = validate_convention(catalog_rows, dual_solution)
    return {
        "solver_info": solver_info,
        "solution_outputs": solution_outputs,
        "dual_solution": dual_solution,
        "validation": validation,
        "stationarity_rows": stationarity_rows,
        "safe_blocker": "; ".join(validation_blockers),
    }


def objective_snapshot(
    solution_index: int,
    added_count: int,
    candidate_id: str,
    solve: dict[str, Any],
    previous_objective: float | None,
) -> dict[str, Any]:
    objective = parse_float(solve["solver_info"].get("objective_value"), math.nan)
    return {
        "solution_index": solution_index,
        "added_oracle_candidate_count": added_count,
        "selected_oracle_candidate_added_to_reach_solution": candidate_id,
        "solver_status": solve["solver_info"].get("solver_status"),
        "objective_value": objective,
        "objective_change_from_previous": objective - previous_objective
        if previous_objective is not None and math.isfinite(objective)
        else "",
        "demand_residual_max": solve["solution_outputs"].get("demand_residual_max"),
        "capacity_violation_count": solve["solution_outputs"].get("capacity_violation_count"),
        "max_capacity_violation": solve["solution_outputs"].get("max_capacity_violation"),
        "positive_flow_column_count": solve["solution_outputs"].get("positive_flow_column_count"),
    }


def parse_node_id(node_time_id: str) -> str:
    if node_time_id.startswith("source_") or node_time_id.startswith("sink_"):
        return ""
    if node_time_id.startswith("n") and "_t" in node_time_id:
        return node_time_id[1:].split("_t", 1)[0]
    return ""


def build_sequence_metadata(arc_ids: list[str], arc_by_id: dict[str, dict[str, str]]) -> dict[str, str]:
    physical_nodes: list[str] = []
    physical_links: list[str] = []
    times: list[str] = []
    arrival_time = ""
    for arc_id in arc_ids:
        arc = arc_by_id.get(arc_id, {})
        from_node = parse_node_id(arc.get("from_node_time_id", ""))
        to_node = parse_node_id(arc.get("to_node_time_id", ""))
        if from_node and not physical_nodes:
            physical_nodes.append(from_node)
        if to_node and (not physical_nodes or physical_nodes[-1] != to_node):
            physical_nodes.append(to_node)
        if arc.get("arc_type") == "movement":
            physical_links.append(arc.get("physical_link_id", ""))
        if arc.get("from_time", "") and not times:
            times.append(arc.get("from_time", ""))
        if arc.get("to_time", "") and (not times or times[-1] != arc.get("to_time", "")):
            times.append(arc.get("to_time", ""))
        if arc.get("arc_type") == "sink_connector":
            arrival_time = arc.get("from_time", "")
    return {
        "node_sequence": "|".join(physical_nodes),
        "link_sequence": "|".join(link for link in physical_links if link),
        "time_sequence": "|".join(times),
        "arrival_time": arrival_time,
    }


def validation_convention(validation: dict[str, Any]) -> dict[str, Any]:
    details = validation.get("validated_convention_details", {})
    eq_sign = parse_float(details.get("eq_marginal_sign"), math.nan)
    cap_sign = parse_float(details.get("capacity_marginal_sign"), math.nan)
    return {
        "validated_convention": validation.get("validated_convention"),
        "eq_sign": eq_sign,
        "capacity_sign": cap_sign,
        "convention_source": "current round stationarity validation",
    }


def source_sink_maps(arcs: list[dict[str, str]]) -> tuple[dict[str, dict[str, str]], dict[str, set[str]]]:
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
    return source_connectors, sink_targets


def shortest_path_bellman_ford(
    arcs: list[dict[str, str]],
    start_node: str,
    target_nodes: set[str],
    dual_solution: dict[str, Any],
    capacity_sign: float,
) -> tuple[float, list[str], str | None, str]:
    nodes: set[str] = {start_node}
    edge_rows: list[tuple[str, str, str, float]] = []
    capacity_duals = dual_solution.get("capacity_inequality_duals", {})
    for arc in arcs:
        arc_id = arc.get("arc_id", "")
        from_node = arc.get("from_node_time_id", "")
        to_node = arc.get("to_node_time_id", "")
        cost = parse_float(arc.get("cost"), math.inf)
        if not from_node or not to_node or not math.isfinite(cost):
            continue
        cap_dual = parse_float(capacity_duals.get(arc_id, {}).get("marginal"), 0.0)
        weight = cost + capacity_sign * cap_dual
        nodes.add(from_node)
        nodes.add(to_node)
        edge_rows.append((from_node, to_node, arc_id, weight))

    distance: dict[str, float] = {node: math.inf for node in nodes}
    predecessor: dict[str, tuple[str, str]] = {}
    distance[start_node] = 0.0
    for _ in range(max(0, len(nodes) - 1)):
        changed = False
        for from_node, to_node, arc_id, weight in edge_rows:
            if not math.isfinite(distance.get(from_node, math.inf)):
                continue
            new_distance = distance[from_node] + weight
            if new_distance + 1e-10 < distance.get(to_node, math.inf):
                distance[to_node] = new_distance
                predecessor[to_node] = (from_node, arc_id)
                changed = True
        if not changed:
            break

    for from_node, to_node, _arc_id, weight in edge_rows:
        if math.isfinite(distance.get(from_node, math.inf)) and distance[from_node] + weight < distance.get(
            to_node, math.inf
        ) - 1e-8:
            return math.inf, [], None, "negative reduced-cost cycle detected in diagnostic graph"

    best_target = min(target_nodes, key=lambda node: distance.get(node, math.inf), default=None)
    if best_target is None or not math.isfinite(distance.get(best_target, math.inf)):
        return math.inf, [], None, "shortest path could not be found"

    path_arcs: list[str] = []
    node = best_target
    while node != start_node:
        if node not in predecessor:
            return math.inf, [], None, "shortest path predecessor chain is incomplete"
        prev_node, arc_id = predecessor[node]
        path_arcs.append(arc_id)
        node = prev_node
    path_arcs.reverse()
    return distance[best_target], path_arcs, best_target, ""


def classify_oracle_candidate(
    demand_id: str,
    arc_ids: list[str],
    entry_signal: float,
    current_pool: list[dict[str, str]],
) -> tuple[str, str, bool]:
    sequence = "|".join(arc_ids)
    for row in current_pool:
        if row.get("demand_id") == demand_id and row.get("arc_sequence") == sequence:
            return "duplicate_existing_phase2_column", row.get("column_id", ""), True
    if math.isfinite(entry_signal) and entry_signal < -REDUCED_COST_TOLERANCE:
        return "improving_new_candidate", "", True
    if math.isfinite(entry_signal):
        return "nonimproving_new_candidate", "", True
    return "invalid_oracle_candidate", "", False


def run_oracle_probes(
    arcs: list[dict[str, str]],
    demands: list[dict[str, str]],
    current_pool: list[dict[str, str]],
    dual_solution: dict[str, Any],
    convention: dict[str, Any],
    round_number: int,
) -> list[dict[str, Any]]:
    arc_by_id = {arc.get("arc_id", ""): arc for arc in arcs}
    source_connectors, sink_targets = source_sink_maps(arcs)
    probe_rows: list[dict[str, Any]] = []
    for demand in demands:
        demand_id = demand.get("demand_id", "")
        source = source_connectors.get(demand_id)
        targets = sink_targets.get(demand_id, set())
        if source is None or not targets:
            probe_rows.append(
                {
                    "round": round_number,
                    "candidate_id": f"ORACLE_R{round_number}_{demand_id}",
                    "demand_id": demand_id,
                    "probe_status": "SAFE_BLOCKED",
                    "start_node": source.get("from_node_time_id", "") if source else "",
                    "target_node": "",
                    "arc_sequence": "",
                    "structurally_valid": "false",
                    "invalid_reason": "missing source or sink connector",
                    "reconstructed_generalized_cost": "",
                    "capacity_dual_sum_raw": "",
                    "demand_equality_dual_raw": "",
                    "validated_stationarity_convention": convention.get("validated_convention"),
                    "validated_eq_sign": convention.get("eq_sign"),
                    "validated_capacity_sign": convention.get("capacity_sign"),
                    "oracle_entry_signal": "",
                    "classification": "invalid_oracle_candidate",
                    "duplicate_existing_phase2_column": "false",
                    "duplicate_of_column_id": "",
                    "oracle_generated": "true",
                    "diagnostic_only": "true",
                    "would_be_added_this_round": "false",
                    "would_be_added_in_future_task": "false",
                    "matched_known_fixed_source_candidate_id": "",
                    "blocker": "missing source or sink connector",
                }
            )
            continue

        start_node = source.get("from_node_time_id", "")
        _path_weight, path_arcs, target_node, blocker = shortest_path_bellman_ford(
            arcs, start_node, targets, dual_solution, parse_float(convention.get("capacity_sign"), math.nan)
        )
        if blocker or not path_arcs:
            probe_rows.append(
                {
                    "round": round_number,
                    "candidate_id": f"ORACLE_R{round_number}_{demand_id}",
                    "demand_id": demand_id,
                    "probe_status": "SAFE_BLOCKED",
                    "start_node": start_node,
                    "target_node": target_node or "",
                    "arc_sequence": "|".join(path_arcs),
                    "structurally_valid": "false",
                    "invalid_reason": blocker or "shortest path could not be found",
                    "reconstructed_generalized_cost": "",
                    "capacity_dual_sum_raw": "",
                    "demand_equality_dual_raw": "",
                    "validated_stationarity_convention": convention.get("validated_convention"),
                    "validated_eq_sign": convention.get("eq_sign"),
                    "validated_capacity_sign": convention.get("capacity_sign"),
                    "oracle_entry_signal": "",
                    "classification": "invalid_oracle_candidate",
                    "duplicate_existing_phase2_column": "false",
                    "duplicate_of_column_id": "",
                    "oracle_generated": "true",
                    "diagnostic_only": "true",
                    "would_be_added_this_round": "false",
                    "would_be_added_in_future_task": "false",
                    "matched_known_fixed_source_candidate_id": "",
                    "blocker": blocker or "shortest path could not be found",
                }
            )
            continue

        path_row = {"arc_sequence": "|".join(path_arcs), "demand_id": demand_id}
        reconstructed, missing, nonfinite = reconstruct_path_cost(path_row, arc_by_id)
        cap_sum = raw_capacity_dual_sum(path_arcs, dual_solution)
        eq_dual = demand_dual(demand_id, dual_solution)
        entry_signal = reconstructed + convention["eq_sign"] * eq_dual + convention["capacity_sign"] * cap_sum
        classification, duplicate_of, structurally_valid = classify_oracle_candidate(
            demand_id, path_arcs, entry_signal, current_pool
        )
        if missing or nonfinite:
            classification = "invalid_oracle_candidate"
            structurally_valid = False
        candidate_id = f"ORACLE_R{round_number}_{demand_id}"
        if (
            round_number == 1
            and demand_id == "D4"
            and "|".join(path_arcs)
            == "source_D4|wait_7_t2|move_18_t3|move_55_t5|move_48_t8|sink_D4_10_t12"
        ):
            candidate_id = "ORACLE_PROBE_D4"
        probe_rows.append(
            {
                "round": round_number,
                "candidate_id": candidate_id,
                "demand_id": demand_id,
                "probe_status": "PASS" if structurally_valid else "SAFE_BLOCKED",
                "start_node": start_node,
                "target_node": target_node or "",
                "arc_sequence": "|".join(path_arcs),
                "structurally_valid": bool_text(structurally_valid),
                "invalid_reason": "|".join(missing + nonfinite),
                "reconstructed_generalized_cost": reconstructed,
                "capacity_dual_sum_raw": cap_sum,
                "demand_equality_dual_raw": eq_dual,
                "validated_stationarity_convention": convention.get("validated_convention"),
                "validated_eq_sign": convention.get("eq_sign"),
                "validated_capacity_sign": convention.get("capacity_sign"),
                "oracle_entry_signal": entry_signal,
                "classification": classification,
                "duplicate_existing_phase2_column": bool_text(bool(duplicate_of)),
                "duplicate_of_column_id": duplicate_of,
                "oracle_generated": "true",
                "diagnostic_only": "true",
                "would_be_added_this_round": "false",
                "would_be_added_in_future_task": "false",
                "matched_known_fixed_source_candidate_id": "",
                "blocker": "",
            }
        )
    return probe_rows


def best_oracle_candidate(probes: list[dict[str, Any]]) -> dict[str, Any] | None:
    improving = [
        row
        for row in probes
        if row.get("classification") == "improving_new_candidate"
        and parse_float(row.get("oracle_entry_signal"), math.inf) < -REDUCED_COST_TOLERANCE
    ]
    return min(improving, key=lambda row: parse_float(row.get("oracle_entry_signal"), math.inf), default=None)


def selected_flow(solution_outputs: dict[str, Any], candidate_id: str) -> float:
    for row in solution_outputs.get("solution_by_column", []):
        if row.get("column_id") == candidate_id:
            return parse_float(row.get("flow"), 0.0)
    return 0.0


def build_oracle_candidate_row(
    probe: dict[str, Any],
    demands: list[dict[str, str]],
    arcs: list[dict[str, str]],
    round_number: int,
) -> dict[str, str]:
    demand = next(row for row in demands if row.get("demand_id") == probe.get("demand_id"))
    arc_ids = split_sequence(str(probe.get("arc_sequence", "")))
    arc_by_id = {row.get("arc_id", ""): row for row in arcs}
    metadata = build_sequence_metadata(arc_ids, arc_by_id)
    departure = demand.get("departure_time", "")
    arrival = metadata["arrival_time"]
    travel_time = ""
    if arrival != "":
        travel_time = str(parse_float(arrival, 0.0) - parse_float(departure, 0.0))
    return {
        "column_id": str(probe.get("candidate_id", "")),
        "path_id": f"ORACLE_SHORTEST_PATH_R{round_number}_{probe.get('demand_id')}",
        "demand_id": str(probe.get("demand_id", "")),
        "origin_node_id": demand.get("origin_node_id", ""),
        "destination_node_id": demand.get("destination_node_id", ""),
        "departure_time": departure,
        "arrival_time": arrival,
        "travel_time": travel_time,
        "generalized_cost": str(parse_float(probe.get("reconstructed_generalized_cost"), math.nan)),
        "node_sequence": metadata["node_sequence"],
        "link_sequence": metadata["link_sequence"],
        "time_sequence": metadata["time_sequence"],
        "arc_sequence": str(probe.get("arc_sequence", "")),
        "phase2_pool_column_type": "phase2_oracle_loop_added_candidate",
        "source_metadata": "dynamic_network_pricing_oracle",
        "added_in_phase1_round": "",
        "phase1_final_flow": "",
        "written_to_baseline_dynamic_columns": "false",
        "output_only_phase2_initial_pool": "false",
        "output_only_phase2_loop_pool": "false",
        "output_only_phase2_oracle_loop_pool": "true",
        "pool_membership": "oracle_loop_added_candidate",
        "candidate_source": "dynamic_network_pricing_oracle",
        "added_in_phase2_round": str(round_number),
        "oracle_entry_signal_at_addition": str(parse_float(probe.get("oracle_entry_signal"), math.nan)),
        "written_to_phase2_initial_pool": "false",
        "written_to_fixed_source_outputs": "false",
    }


def pool_output_rows(pool: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in pool:
        rows.append(
            {
                "column_id": row.get("column_id", ""),
                "path_id": row.get("path_id", ""),
                "demand_id": row.get("demand_id", ""),
                "origin_node_id": row.get("origin_node_id", ""),
                "destination_node_id": row.get("destination_node_id", ""),
                "departure_time": row.get("departure_time", ""),
                "arrival_time": row.get("arrival_time", ""),
                "travel_time": row.get("travel_time", ""),
                "generalized_cost": row.get("generalized_cost", ""),
                "node_sequence": row.get("node_sequence", ""),
                "link_sequence": row.get("link_sequence", ""),
                "time_sequence": row.get("time_sequence", ""),
                "arc_sequence": row.get("arc_sequence", ""),
                "phase2_pool_column_type": row.get("phase2_pool_column_type", ""),
                "source_metadata": row.get("source_metadata", ""),
                "added_in_phase1_round": row.get("added_in_phase1_round", ""),
                "phase1_final_flow": row.get("phase1_final_flow", ""),
                "written_to_baseline_dynamic_columns": row.get("written_to_baseline_dynamic_columns", "false"),
                "output_only_phase2_initial_pool": row.get("output_only_phase2_initial_pool", "false"),
                "output_only_phase2_loop_pool": row.get("output_only_phase2_loop_pool", "false"),
                "output_only_phase2_oracle_loop_pool": row.get("output_only_phase2_oracle_loop_pool", "true"),
                "pool_membership": row.get("pool_membership", ""),
                "candidate_source": row.get("candidate_source", ""),
                "added_in_phase2_round": row.get("added_in_phase2_round", ""),
                "oracle_entry_signal_at_addition": row.get("oracle_entry_signal_at_addition", ""),
                "written_to_phase2_initial_pool": row.get("written_to_phase2_initial_pool", "false"),
                "written_to_fixed_source_outputs": row.get("written_to_fixed_source_outputs", "false"),
            }
        )
    return rows


def duplicate_audit_rows(pool: list[dict[str, str]]) -> list[dict[str, Any]]:
    seen: dict[tuple[str, str], str] = {}
    rows: list[dict[str, Any]] = []
    for row in pool:
        key = (row.get("demand_id", ""), row.get("arc_sequence", ""))
        duplicate_of = seen.get(key, "")
        rows.append(
            {
                "column_id": row.get("column_id", ""),
                "demand_id": row.get("demand_id", ""),
                "arc_sequence": row.get("arc_sequence", ""),
                "duplicate_same_demand_arc_sequence": bool_text(bool(duplicate_of)),
                "duplicate_of_column_id": duplicate_of,
                "pool_membership": row.get("pool_membership", ""),
                "candidate_source": row.get("candidate_source", ""),
            }
        )
        if key not in seen:
            seen[key] = row.get("column_id", "")
    return rows


def fixed_source_rows_with_flags(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for row in rows:
        copy = dict(row)
        copy["output_only_phase2_oracle_loop_pool"] = "true"
        copy["pool_membership"] = copy.get("pool_membership") or "fixed_source_final_pool_column"
        copy["candidate_source"] = copy.get("candidate_source") or copy.get("source_metadata", "")
        copy["oracle_entry_signal_at_addition"] = ""
        copy["written_to_baseline_dynamic_columns"] = copy.get("written_to_baseline_dynamic_columns", "false")
        copy["written_to_phase2_initial_pool"] = "false"
        copy["written_to_fixed_source_outputs"] = "false"
        out.append(copy)
    return out


def precheck_gate_blockers(
    nodes: list[dict[str, str]],
    arcs: list[dict[str, str]],
    demands: list[dict[str, str]],
    starting_pool: list[dict[str, str]],
    source_rows: list[dict[str, str]],
    candidate_scores: list[dict[str, str]],
    accepted_loop_dual: dict[str, Any],
    output_dir: Path,
) -> tuple[list[str], dict[str, Any]]:
    arc_by_id = {arc.get("arc_id", ""): arc for arc in arcs}
    schema_inventory, arc_cost_rows, schema_blockers = build_schema_inventory(nodes, arcs, demands)
    connectivity_audit, connectivity_blockers = build_connectivity_audit(arcs, demands, starting_pool, source_rows)
    known_rows = unique_known_rows(starting_pool, source_rows)
    cost_rows, cost_blockers = build_cost_reconstruction_audit(known_rows, arc_by_id)
    convention, convention_blockers = convention_from_candidate_scores(candidate_scores)
    final_round = max((int(row.get("round") or 0) for row in candidate_scores), default=0)
    comparison_rows, rc_blockers = build_known_candidate_comparison(
        source_rows, candidate_scores, final_round, arc_by_id, accepted_loop_dual, convention
    )
    write_json(output_dir / "phase2_oracle_loop_schema_gate_inventory.json", schema_inventory)
    write_csv(
        output_dir / "phase2_oracle_loop_arc_cost_gate_audit.csv",
        arc_cost_rows,
        [
            "audit_item",
            "field_or_arc_type",
            "present",
            "row_count",
            "finite_value_count",
            "min_value",
            "max_value",
            "details",
        ],
    )
    write_json(output_dir / "phase2_oracle_loop_connectivity_gate_audit.json", connectivity_audit)
    write_csv(
        output_dir / "phase2_oracle_loop_known_column_reconstruction_gate.csv",
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
        output_dir / "phase2_oracle_loop_reduced_cost_reconstruction_gate.csv",
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
    gate_blockers = schema_blockers + connectivity_blockers + cost_blockers + convention_blockers + rc_blockers
    gate_summary = {
        "schema_gate_status": "PASS" if not schema_blockers else "SAFE_BLOCKED",
        "connectivity_gate_status": "PASS" if not connectivity_blockers else "SAFE_BLOCKED",
        "known_column_cost_reconstruction_gate_status": "PASS" if not cost_blockers else "SAFE_BLOCKED",
        "known_candidate_reduced_cost_reconstruction_gate_status": "PASS" if not rc_blockers else "SAFE_BLOCKED",
        "prior_convention_gate_status": "PASS" if not convention_blockers else "SAFE_BLOCKED",
        "validated_convention": convention.get("validated_convention"),
        "validated_eq_sign": convention.get("eq_sign"),
        "validated_capacity_sign": convention.get("capacity_sign"),
        "safe_blockers": gate_blockers,
    }
    return gate_blockers, gate_summary


def one_candidate_blockers(summary: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if summary.get("diagnostic_status") != "PASS":
        blockers.append(f"accepted oracle one-candidate status changed: {summary.get('diagnostic_status')}")
    if not ALLOW_VARIABLE_ORACLE_CANDIDATE and summary.get("selected_candidate_id") != "ORACLE_PROBE_D4":
        blockers.append(f"accepted oracle one-candidate selected candidate changed: {summary.get('selected_candidate_id')}")
    if (
        not ALLOW_VARIABLE_FIXED_SOURCE_BASE
        and abs(parse_float(summary.get("objective_before"), math.inf) - EXPECTED_OBJECTIVE_BEFORE) > 1e-5
    ):
        blockers.append(f"accepted oracle one-candidate objective_before changed: {summary.get('objective_before')}")
    if (
        not ALLOW_VARIABLE_ORACLE_CANDIDATE
        and abs(parse_float(summary.get("objective_after"), math.inf) - 387812930.6993559) > 1e-5
    ):
        blockers.append(f"accepted oracle one-candidate objective_after changed: {summary.get('objective_after')}")
    if summary.get("objective_decreased") is not True:
        blockers.append("accepted oracle one-candidate no longer reports objective_decreased")
    if parse_float(summary.get("demand_residual_max_after"), math.inf) > TOL:
        blockers.append("accepted oracle one-candidate demand residual changed")
    if int(summary.get("capacity_violation_count_after") if summary.get("capacity_violation_count_after") is not None else -1) != 0:
        blockers.append("accepted oracle one-candidate capacity violation changed")
    if summary.get("phase2_initial_pool_mutated") is not False or summary.get("baseline_dynamic_columns_mutated") is not False:
        blockers.append("accepted oracle one-candidate reports baseline or Phase-II initial pool mutation")
    if summary.get("cg_loop_run") is not False or summary.get("full_cg_run") is not False:
        blockers.append("accepted oracle one-candidate unexpectedly reports loop or full CG")
    return blockers


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Bounded Oracle Phase-II Loop Diagnostic",
        "",
        SCOPE_BOUNDARY,
        "",
        "## Summary",
        "",
        f"- Diagnostic status: {summary.get('diagnostic_status')}",
        f"- Max rounds: {summary.get('max_rounds')}",
        f"- Rounds attempted: {summary.get('rounds_attempted')}",
        f"- Rounds with candidate added: {summary.get('rounds_with_candidate_added')}",
        f"- Objective initial: {summary.get('objective_initial')}",
        f"- Objective final: {summary.get('objective_final')}",
        f"- Objective change total: {summary.get('objective_change_total')}",
        f"- Gap to arc-LP reference final: {summary.get('gap_to_arc_lp_reference_final')}",
        f"- Stop reason: {summary.get('stop_reason')}",
        f"- Demand residual max final: {summary.get('demand_residual_max_final')}",
        f"- Capacity violation count final: {summary.get('capacity_violation_count_final')}",
        "",
        "## Selected Oracle Candidates",
        "",
    ]
    for row in summary.get("selected_oracle_candidates_by_round", []):
        lines.append(
            f"- R{row['round']}: {row['candidate_id']} ({row['demand_id']}), "
            f"entry signal {row['oracle_entry_signal']}, final flow {row['candidate_flow_final_solution']}"
        )
    if not summary.get("selected_oracle_candidates_by_round"):
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            summary.get("interpretation", ""),
            "",
            "The arc-LP objective comparison is diagnostic only. This task does not claim exact arc-LP flow-pattern reproduction.",
            "",
            "## Scope Guardrails",
            "",
            f"- Phase-II initial pool mutated: {summary.get('phase2_initial_pool_mutated')}",
            f"- Fixed-source final pool mutated: {summary.get('fixed_source_final_pool_mutated')}",
            f"- Baseline dynamic_columns.csv mutated: {summary.get('baseline_dynamic_columns_mutated')}",
            f"- Full assignment run: {summary.get('full_assignment_run')}",
            f"- Full CG run: {summary.get('full_cg_run')}",
            f"- General convergence claimed: {summary.get('general_convergence_claimed')}",
            f"- Global optimality claimed: {summary.get('global_optimality_claimed')}",
            "",
            "## Next Safe Step",
            "",
            summary.get("next_safe_step", ""),
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_outputs(
    output_dir: Path,
    summary: dict[str, Any],
    rounds: list[dict[str, Any]],
    objective_by_round: list[dict[str, Any]],
    added_candidates: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
    final_outputs: dict[str, Any],
    final_dual_solution: dict[str, Any],
    duplicate_rows: list[dict[str, Any]],
    hash_audit: dict[str, Any],
    stop_payload: dict[str, Any],
    gap_payload: dict[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_report(output_dir / "phase2_oracle_bounded_loop_report.md", summary)
    write_json(output_dir / "phase2_oracle_bounded_loop_summary.json", summary)
    write_csv(
        output_dir / "phase2_oracle_loop_rounds.csv",
        rounds,
        [
            "round",
            "pool_column_count_before",
            "solver_status_before",
            "objective_before",
            "dual_validation_status",
            "validated_convention",
            "dual_revalidated_after_solve",
            "oracle_probe_run_after_solve",
            "probe_candidate_count",
            "negative_reduced_cost_nondeduplicate_candidate_count",
            "selected_candidate_id",
            "selected_candidate_demand",
            "selected_candidate_reduced_cost",
            "candidate_added",
            "pool_column_count_after_add",
            "rmp_resolved_after_candidate_add",
            "solver_status_after_add",
            "objective_after",
            "objective_change",
            "selected_candidate_flow_after_resolve",
            "demand_residual_max_after",
            "capacity_violation_count_after",
            "stop_reason_if_stopped",
        ],
    )
    write_csv(
        output_dir / "phase2_oracle_loop_objective_by_round.csv",
        objective_by_round,
        [
            "solution_index",
            "added_oracle_candidate_count",
            "selected_oracle_candidate_added_to_reach_solution",
            "solver_status",
            "objective_value",
            "objective_change_from_previous",
            "demand_residual_max",
            "capacity_violation_count",
            "max_capacity_violation",
            "positive_flow_column_count",
        ],
    )
    write_csv(
        output_dir / "phase2_oracle_loop_added_candidates.csv",
        added_candidates,
        [
            "round",
            "candidate_id",
            "demand_id",
            "candidate_source",
            "path_id",
            "arc_sequence",
            "oracle_entry_signal",
            "classification_at_addition",
            "structurally_valid_at_addition",
            "duplicate_at_addition",
            "candidate_flow_after_resolve",
            "candidate_flow_final_solution",
            "objective_before_add",
            "objective_after_resolve",
            "objective_change_after_resolve",
            "written_to_phase2_initial_pool",
            "written_to_baseline_dynamic_columns",
            "written_to_fixed_source_outputs",
        ],
    )
    write_csv(
        output_dir / "phase2_oracle_loop_probe_candidates_by_round.csv",
        probe_rows,
        [
            "round",
            "candidate_id",
            "demand_id",
            "probe_status",
            "start_node",
            "target_node",
            "arc_sequence",
            "structurally_valid",
            "invalid_reason",
            "reconstructed_generalized_cost",
            "capacity_dual_sum_raw",
            "demand_equality_dual_raw",
            "validated_stationarity_convention",
            "validated_eq_sign",
            "validated_capacity_sign",
            "oracle_entry_signal",
            "classification",
            "duplicate_existing_phase2_column",
            "duplicate_of_column_id",
            "oracle_generated",
            "diagnostic_only",
            "would_be_added_this_round",
            "would_be_added_in_future_task",
            "matched_known_fixed_source_candidate_id",
            "blocker",
        ],
    )
    write_csv(
        output_dir / "phase2_oracle_loop_solution_by_column_final.csv",
        final_outputs.get("solution_by_column", []),
        [
            "column_id",
            "path_id",
            "demand_id",
            "phase2_pool_column_type",
            "source_metadata",
            "added_in_phase1_round",
            "lower_bound",
            "upper_bound",
            "flow",
            "positive_flow",
            "cost_field_used",
            "objective_coefficient",
            "objective_contribution",
            "arc_sequence",
        ],
    )
    write_csv(
        output_dir / "phase2_oracle_loop_demand_balance_final.csv",
        final_outputs.get("demand_balance", []),
        ["demand_id", "demand_volume", "real_column_flow", "demand_residual", "status"],
    )
    write_csv(
        output_dir / "phase2_oracle_loop_capacity_usage_final.csv",
        final_outputs.get("capacity_usage", []),
        [
            "arc_id",
            "arc_type",
            "physical_link_id",
            "from_time",
            "to_time",
            "flow",
            "capacity",
            "slack",
            "capacity_violation",
            "is_binding",
            "columns_using_arc",
            "demand_ids_using_arc",
            "status",
        ],
    )
    write_csv(
        output_dir / "phase2_oracle_loop_cost_breakdown_final.csv",
        final_outputs.get("cost_breakdown", []),
        ["breakdown_id", "demand_id", "cost_field_used", "flow", "objective_contribution", "scope"],
    )
    write_json(output_dir / "phase2_oracle_loop_dual_solution_final.json", final_dual_solution)
    write_csv(
        output_dir / "phase2_oracle_loop_duplicate_audit_final.csv",
        duplicate_rows,
        [
            "column_id",
            "demand_id",
            "arc_sequence",
            "duplicate_same_demand_arc_sequence",
            "duplicate_of_column_id",
            "pool_membership",
            "candidate_source",
        ],
    )
    write_json(output_dir / "phase2_oracle_loop_hash_audit.json", hash_audit)
    write_json(output_dir / "phase2_oracle_loop_stop_reason.json", stop_payload)
    write_json(output_dir / "phase2_oracle_loop_gap_to_arc_lp.json", gap_payload)


def stop_interpretation(stop_reason: str, objective_change_total: float | None) -> str:
    if stop_reason == STOP_NO_NEGATIVE:
        return (
            "bounded oracle diagnostic found no negative reduced-cost non-duplicate path under the "
            "implemented dynamic-network oracle and current scope."
        )
    if stop_reason == "max_rounds_reached":
        return "bounded oracle diagnostic reached the finite max_rounds cap before pricing closure within this scope."
    if stop_reason == "safe_blocker":
        return "safe blocker encountered; review schema, cost, reduced-cost, solve, feasibility, or hash diagnostics."
    if objective_change_total is not None and objective_change_total < -TOL:
        return "bounded oracle diagnostic reduced the restricted master objective within the stated diagnostic scope."
    return "bounded oracle diagnostic completed within the stated scope."


def input_artifact_audit(
    output_dir: Path,
    config_path: str | Path,
    max_rounds: int,
    precheck_only: bool,
    write_audit: bool,
) -> dict[str, Any]:
    config_resolved = Path(config_path)
    if not config_resolved.is_absolute():
        config_resolved = ROOT_DIR / config_resolved
    audit = {
        "audit_status": "PASS",
        "config_path": rel(config_resolved),
        "phase2_oracle_loop_output_dir": rel(output_dir),
        "writes_default_output_dir": output_dir.resolve() == DEFAULT_OUTPUT_DIR.resolve(),
        "max_rounds": max_rounds,
        "precheck_only": precheck_only,
        "data_dir": rel(DATA_DIR),
        "dynamic_node_path": rel(DYNAMIC_NODE),
        "dynamic_arc_path": rel(DYNAMIC_ARC),
        "dynamic_demand_path": rel(DYNAMIC_DEMAND),
        "baseline_columns_path": rel(BASELINE_COLUMNS),
        "oracle_precheck_dir": rel(ORACLE_PRECHECK_DIR),
        "oracle_one_candidate_dir": rel(ORACLE_ONE_CANDIDATE_DIR),
        "fixed_source_loop_dir": rel(FIXED_SOURCE_LOOP_DIR),
        "fixed_source_closure_dir": rel(FIXED_SOURCE_CLOSURE_DIR),
        "phase2_initial_pool_path": rel(PHASE2_INITIAL_POOL),
        "phase2_base_pool_path": rel(FIXED_SOURCE_FINAL_POOL),
        "fixed_source_candidate_path": rel(FIXED_SOURCE),
        "required_inputs": [rel(path) for path in REQUIRED_INPUTS],
    }
    if write_audit:
        write_json(output_dir / "phase2_oracle_loop_input_artifact_audit.json", audit)
    return audit


def run_bounded_oracle_loop(
    config_path: str | Path = DEFAULT_CURRENT_POOL_CONFIG,
    output_dir: Path = OUTPUT_DIR,
    max_rounds: int = DEFAULT_MAX_ROUNDS,
    precheck_only: bool = False,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    max_rounds = max(0, int(max_rounds))
    write_input_audit = output_dir.resolve() != DEFAULT_OUTPUT_DIR.resolve() or precheck_only
    input_audit = input_artifact_audit(output_dir, config_path, max_rounds, precheck_only, write_input_audit)
    config = load_config(config_path)
    input_data_dir(config)
    baseline_path = BASELINE_COLUMNS
    baseline_hash_before = sha256_file(baseline_path) if baseline_path.exists() else ""
    phase2_initial_hash_before = sha256_file(PHASE2_INITIAL_POOL) if PHASE2_INITIAL_POOL.exists() else ""
    fixed_source_pool_hash_before = sha256_file(FIXED_SOURCE_FINAL_POOL) if FIXED_SOURCE_FINAL_POOL.exists() else ""
    fixed_source_outputs_hash_before = fixed_source_output_hashes()

    safe_blockers = required_input_blockers()
    if precheck_only:
        baseline_hash_after = sha256_file(baseline_path) if baseline_path.exists() else baseline_hash_before
        phase2_initial_hash_after = sha256_file(PHASE2_INITIAL_POOL) if PHASE2_INITIAL_POOL.exists() else phase2_initial_hash_before
        fixed_source_pool_hash_after = sha256_file(FIXED_SOURCE_FINAL_POOL) if FIXED_SOURCE_FINAL_POOL.exists() else fixed_source_pool_hash_before
        fixed_source_outputs_hash_after = fixed_source_output_hashes()
        summary = {
            "diagnostic_status": "PASS" if not safe_blockers else "SAFE_BLOCKED",
            "precheck_only": True,
            "max_rounds": max_rounds,
            "rounds_attempted": 0,
            "rounds_with_candidate_added": 0,
            "allow_variable_fixed_source_base": ALLOW_VARIABLE_FIXED_SOURCE_BASE,
            "allow_variable_oracle_candidate": ALLOW_VARIABLE_ORACLE_CANDIDATE,
            "allow_variable_initial_oracle_loop_objective": ALLOW_VARIABLE_INITIAL_ORACLE_LOOP_OBJECTIVE,
            "objective_initial": None,
            "objective_final": None,
            "objective_change_total": None,
            "gap_to_arc_lp_reference_final": None,
            "stop_reason": "precheck_only" if not safe_blockers else "safe_blocker",
            "demand_residual_max_final": None,
            "capacity_violation_count_final": None,
            "phase2_initial_pool_mutated": phase2_initial_hash_before != phase2_initial_hash_after,
            "fixed_source_final_pool_mutated": fixed_source_pool_hash_before != fixed_source_pool_hash_after,
            "baseline_dynamic_columns_mutated": baseline_hash_before != baseline_hash_after,
            "accepted_fixed_source_outputs_mutated": fixed_source_outputs_hash_before != fixed_source_outputs_hash_after,
            "oracle_candidates_written_to_baseline": False,
            "oracle_candidates_written_to_phase2_initial_pool": False,
            "oracle_candidates_written_to_fixed_source_outputs": False,
            "full_assignment_run": False,
            "full_cg_run": False,
            "general_convergence_claimed": False,
            "safe_blockers": safe_blockers,
            "input_artifact_audit_path": rel(output_dir / "phase2_oracle_loop_input_artifact_audit.json"),
            "scope": SCOPE_BOUNDARY,
        }
        hash_audit = {
            "phase2_initial_pool_path": rel(PHASE2_INITIAL_POOL),
            "phase2_initial_pool_hash_before": phase2_initial_hash_before,
            "phase2_initial_pool_hash_after": phase2_initial_hash_after,
            "phase2_initial_pool_mutated": phase2_initial_hash_before != phase2_initial_hash_after,
            "fixed_source_final_pool_path": rel(FIXED_SOURCE_FINAL_POOL),
            "fixed_source_final_pool_hash_before": fixed_source_pool_hash_before,
            "fixed_source_final_pool_hash_after": fixed_source_pool_hash_after,
            "fixed_source_final_pool_mutated": fixed_source_pool_hash_before != fixed_source_pool_hash_after,
            "baseline_dynamic_columns_path": rel(baseline_path),
            "baseline_dynamic_columns_hash_before": baseline_hash_before,
            "baseline_dynamic_columns_hash_after": baseline_hash_after,
            "baseline_dynamic_columns_mutated": baseline_hash_before != baseline_hash_after,
            "allow_variable_fixed_source_base": ALLOW_VARIABLE_FIXED_SOURCE_BASE,
            "allow_variable_oracle_candidate": ALLOW_VARIABLE_ORACLE_CANDIDATE,
            "allow_variable_initial_oracle_loop_objective": ALLOW_VARIABLE_INITIAL_ORACLE_LOOP_OBJECTIVE,
            "accepted_fixed_source_outputs_hash_before": fixed_source_outputs_hash_before,
            "accepted_fixed_source_outputs_hash_after": fixed_source_outputs_hash_after,
            "accepted_fixed_source_outputs_mutated": fixed_source_outputs_hash_before != fixed_source_outputs_hash_after,
            "full_assignment_run": False,
            "full_cg_run": False,
        }
        stop_payload = {
            "stop_reason": summary["stop_reason"],
            "allowed_stop_reasons": sorted(ALLOWED_STOP_REASONS | {"precheck_only"}),
            "interpretation": "precheck-only path verified input-artifact routing without running the oracle loop.",
            "safe_blockers": safe_blockers,
            "full_assignment_run": False,
            "full_cg_run": False,
            "general_convergence_claimed": False,
        }
        gap_payload = {
            "arc_lp_reference_objective": ARC_LP_REFERENCE_OBJECTIVE,
            "fixed_source_final_objective_reference": FIXED_SOURCE_FINAL_OBJECTIVE_REFERENCE,
            "oracle_loop_final_objective": None,
            "gap_to_arc_lp_reference_final": None,
            "diagnostic_comparison_only": True,
            "global_optimality_claimed": False,
            "exact_arc_lp_flow_pattern_reproduction_claimed": False,
        }
        write_outputs(
            output_dir,
            summary,
            [],
            [],
            [],
            [],
            empty_solution_outputs(),
            {},
            [],
            hash_audit,
            stop_payload,
            gap_payload,
        )
        return summary
    nodes = read_csv(DYNAMIC_NODE) if DYNAMIC_NODE.exists() else []
    arcs = read_csv(DYNAMIC_ARC) if DYNAMIC_ARC.exists() else []
    demands = read_csv(DYNAMIC_DEMAND) if DYNAMIC_DEMAND.exists() else []
    starting_pool_rows = read_csv(FIXED_SOURCE_FINAL_POOL) if FIXED_SOURCE_FINAL_POOL.exists() else []
    source_rows = read_csv(FIXED_SOURCE) if FIXED_SOURCE.exists() else []
    candidate_scores = read_csv(FIXED_SOURCE_LOOP_DIR / "phase2_loop_candidate_scores_by_round.csv") if not safe_blockers else []
    accepted_loop_dual = read_json(FIXED_SOURCE_LOOP_DIR / "phase2_loop_dual_solution_final.json") if not safe_blockers else {}
    oracle_one_summary = (
        read_json(ORACLE_ONE_CANDIDATE_DIR / "phase2_oracle_one_candidate_add_resolve_summary.json")
        if not safe_blockers
        else {}
    )
    oracle_precheck_summary = (
        read_json(ORACLE_PRECHECK_DIR / "phase2_pricing_oracle_precheck_summary.json") if not safe_blockers else {}
    )
    fixed_source_summary = read_json(FIXED_SOURCE_LOOP_DIR / "phase2_bounded_loop_summary.json") if not safe_blockers else {}
    closure_summary = read_json(FIXED_SOURCE_CLOSURE_DIR / "phase2_fixed_source_closure_summary.json") if not safe_blockers else {}

    if not safe_blockers:
        if not ALLOW_VARIABLE_FIXED_SOURCE_BASE and len(starting_pool_rows) != 13:
            safe_blockers.append(f"fixed-source final pool has {len(starting_pool_rows)} columns, expected 13")
        if oracle_precheck_summary.get("diagnostic_status") != "PASS":
            safe_blockers.append("accepted oracle precheck no longer reports PASS")
        if fixed_source_summary.get("diagnostic_status") != "PASS":
            safe_blockers.append("accepted fixed-source bounded loop no longer reports PASS")
        if closure_summary.get("diagnostic_status") != "PASS":
            safe_blockers.append("accepted fixed-source closure no longer reports PASS")
        if (
            not ALLOW_VARIABLE_FIXED_SOURCE_BASE
            and abs(parse_float(fixed_source_summary.get("objective_final"), math.inf) - EXPECTED_OBJECTIVE_BEFORE) > 1e-5
        ):
            safe_blockers.append(f"fixed-source objective changed: {fixed_source_summary.get('objective_final')}")
        safe_blockers.extend(one_candidate_blockers(oracle_one_summary))
        if baseline_hash_before != ACCEPTED_BASELINE_HASH:
            safe_blockers.append(f"baseline dynamic_columns.csv hash differs from accepted hash: {baseline_hash_before}")

    gate_summary: dict[str, Any] = {
        "schema_gate_status": "NOT_RUN",
        "connectivity_gate_status": "NOT_RUN",
        "known_column_cost_reconstruction_gate_status": "NOT_RUN",
        "known_candidate_reduced_cost_reconstruction_gate_status": "NOT_RUN",
        "prior_convention_gate_status": "NOT_RUN",
        "safe_blockers": [],
    }
    if not safe_blockers:
        gate_blockers, gate_summary = precheck_gate_blockers(
            nodes, arcs, demands, starting_pool_rows, source_rows, candidate_scores, accepted_loop_dual, output_dir
        )
        safe_blockers.extend(gate_blockers)

    pool = fixed_source_rows_with_flags(starting_pool_rows)
    rounds: list[dict[str, Any]] = []
    objective_by_round: list[dict[str, Any]] = []
    added_candidates: list[dict[str, Any]] = []
    probe_rows_all: list[dict[str, Any]] = []
    stop_reason = "safe_blocker" if safe_blockers else ""

    current_solve = solve_current_pool(arcs, demands, pool)
    if current_solve.get("safe_blocker"):
        safe_blockers.append(current_solve["safe_blocker"])
        stop_reason = "safe_blocker"
    initial_objective = parse_float(current_solve["solver_info"].get("objective_value"), math.nan)
    objective_by_round.append(objective_snapshot(0, 0, "", current_solve, None))
    if (
        not ALLOW_VARIABLE_INITIAL_ORACLE_LOOP_OBJECTIVE
        and math.isfinite(initial_objective)
        and abs(initial_objective - EXPECTED_OBJECTIVE_BEFORE) > 1e-5
    ):
        safe_blockers.append(f"initial oracle loop objective changed: {initial_objective}")
        stop_reason = "safe_blocker"

    rounds_attempted = 0
    for round_number in range(1, max_rounds + 1):
        if stop_reason:
            break
        rounds_attempted += 1
        before_objective = parse_float(current_solve["solver_info"].get("objective_value"), math.nan)
        before_outputs = current_solve["solution_outputs"]
        validation = current_solve["validation"]
        if validation.get("validation_status") != "PASS":
            safe_blockers.append("Phase-II dual/stationarity convention validation failed during oracle loop")
            stop_reason = "safe_blocker"
            break

        convention = validation_convention(validation)
        probes = run_oracle_probes(arcs, demands, pool, current_solve["dual_solution"], convention, round_number)
        best = best_oracle_candidate(probes)
        for probe in probes:
            probe["would_be_added_this_round"] = bool_text(best is not None and probe["candidate_id"] == best["candidate_id"])
        probe_rows_all.extend(probes)

        negative_count = sum(row.get("classification") == "improving_new_candidate" for row in probes)
        round_row = {
            "round": round_number,
            "pool_column_count_before": len(pool),
            "solver_status_before": current_solve["solver_info"].get("solver_status"),
            "objective_before": before_objective,
            "dual_validation_status": validation.get("validation_status"),
            "validated_convention": validation.get("validated_convention"),
            "dual_revalidated_after_solve": "true",
            "oracle_probe_run_after_solve": "true",
            "probe_candidate_count": len(probes),
            "negative_reduced_cost_nondeduplicate_candidate_count": negative_count,
            "selected_candidate_id": "",
            "selected_candidate_demand": "",
            "selected_candidate_reduced_cost": "",
            "candidate_added": "false",
            "pool_column_count_after_add": len(pool),
            "rmp_resolved_after_candidate_add": "false",
            "solver_status_after_add": "",
            "objective_after": before_objective,
            "objective_change": 0.0,
            "selected_candidate_flow_after_resolve": 0.0,
            "demand_residual_max_after": before_outputs.get("demand_residual_max"),
            "capacity_violation_count_after": before_outputs.get("capacity_violation_count"),
            "stop_reason_if_stopped": "",
        }

        if best is None:
            stop_reason = STOP_NO_NEGATIVE
            round_row["stop_reason_if_stopped"] = stop_reason
            rounds.append(round_row)
            break

        candidate_row = build_oracle_candidate_row(best, demands, arcs, round_number)
        pool.append(candidate_row)
        after_solve = solve_current_pool(arcs, demands, pool)
        after_outputs = after_solve["solution_outputs"]
        after_objective = parse_float(after_solve["solver_info"].get("objective_value"), math.nan)
        objective_change = after_objective - before_objective if math.isfinite(after_objective) else math.nan
        candidate_flow = selected_flow(after_outputs, candidate_row["column_id"])

        if after_solve.get("safe_blocker"):
            safe_blockers.append(after_solve["safe_blocker"])
            stop_reason = "safe_blocker"
        if not math.isfinite(objective_change) or objective_change >= -TOL:
            safe_blockers.append(
                f"objective did not decrease after adding {candidate_row['column_id']}: "
                f"{before_objective} -> {after_objective}"
            )
            stop_reason = "safe_blocker"
        if math.isfinite(after_objective) and after_objective < ARC_LP_REFERENCE_OBJECTIVE - ARC_LP_COMPARISON_TOLERANCE:
            safe_blockers.append(
                f"bounded oracle objective dropped below arc-LP reference: {after_objective} < {ARC_LP_REFERENCE_OBJECTIVE}"
            )
            stop_reason = "safe_blocker"
        if parse_float(after_outputs.get("demand_residual_max"), math.inf) > TOL:
            safe_blockers.append("demand residual exceeded tolerance after oracle candidate add")
            stop_reason = "safe_blocker"
        if int(after_outputs.get("capacity_violation_count") if after_outputs.get("capacity_violation_count") is not None else -1) != 0:
            safe_blockers.append("capacity violation detected after oracle candidate add")
            stop_reason = "safe_blocker"

        round_row.update(
            {
                "selected_candidate_id": candidate_row["column_id"],
                "selected_candidate_demand": candidate_row["demand_id"],
                "selected_candidate_reduced_cost": best["oracle_entry_signal"],
                "candidate_added": "true",
                "pool_column_count_after_add": len(pool),
                "rmp_resolved_after_candidate_add": "true",
                "solver_status_after_add": after_solve["solver_info"].get("solver_status"),
                "objective_after": after_objective,
                "objective_change": objective_change,
                "selected_candidate_flow_after_resolve": candidate_flow,
                "demand_residual_max_after": after_outputs.get("demand_residual_max"),
                "capacity_violation_count_after": after_outputs.get("capacity_violation_count"),
                "stop_reason_if_stopped": stop_reason,
            }
        )
        rounds.append(round_row)
        added_candidates.append(
            {
                "round": round_number,
                "candidate_id": candidate_row["column_id"],
                "demand_id": candidate_row["demand_id"],
                "candidate_source": "dynamic_network_pricing_oracle",
                "path_id": candidate_row["path_id"],
                "arc_sequence": candidate_row["arc_sequence"],
                "oracle_entry_signal": best["oracle_entry_signal"],
                "classification_at_addition": best["classification"],
                "structurally_valid_at_addition": best["structurally_valid"],
                "duplicate_at_addition": best["duplicate_existing_phase2_column"],
                "candidate_flow_after_resolve": candidate_flow,
                "candidate_flow_final_solution": "",
                "objective_before_add": before_objective,
                "objective_after_resolve": after_objective,
                "objective_change_after_resolve": objective_change,
                "written_to_phase2_initial_pool": "false",
                "written_to_baseline_dynamic_columns": "false",
                "written_to_fixed_source_outputs": "false",
            }
        )
        objective_by_round.append(
            objective_snapshot(
                len(objective_by_round),
                len(added_candidates),
                candidate_row["column_id"],
                after_solve,
                before_objective,
            )
        )
        current_solve = after_solve
        if stop_reason:
            break

    if not stop_reason:
        stop_reason = "max_rounds_reached"

    final_outputs = current_solve["solution_outputs"]
    final_dual_solution = current_solve["dual_solution"]
    final_objective = parse_float(current_solve["solver_info"].get("objective_value"), math.nan)
    objective_change_total = final_objective - initial_objective if math.isfinite(final_objective) else None
    for row in added_candidates:
        row["candidate_flow_final_solution"] = selected_flow(final_outputs, str(row["candidate_id"]))

    baseline_hash_after = sha256_file(baseline_path) if baseline_path.exists() else baseline_hash_before
    phase2_initial_hash_after = sha256_file(PHASE2_INITIAL_POOL) if PHASE2_INITIAL_POOL.exists() else phase2_initial_hash_before
    fixed_source_pool_hash_after = sha256_file(FIXED_SOURCE_FINAL_POOL) if FIXED_SOURCE_FINAL_POOL.exists() else fixed_source_pool_hash_before
    fixed_source_outputs_hash_after = fixed_source_output_hashes()
    if baseline_hash_before != baseline_hash_after:
        safe_blockers.append("baseline dynamic_columns.csv hash changed during bounded oracle loop")
        stop_reason = "safe_blocker"
    if phase2_initial_hash_before != phase2_initial_hash_after:
        safe_blockers.append("phase2_initial_column_pool.csv hash changed during bounded oracle loop")
        stop_reason = "safe_blocker"
    if fixed_source_pool_hash_before != fixed_source_pool_hash_after:
        safe_blockers.append("fixed-source final pool hash changed during bounded oracle loop")
        stop_reason = "safe_blocker"
    if fixed_source_outputs_hash_before != fixed_source_outputs_hash_after:
        safe_blockers.append("accepted fixed-source outputs changed during bounded oracle loop")
        stop_reason = "safe_blocker"
    if stop_reason not in ALLOWED_STOP_REASONS:
        safe_blockers.append(f"unexpected stop reason: {stop_reason}")
        stop_reason = "safe_blocker"

    gap = final_objective - ARC_LP_REFERENCE_OBJECTIVE if math.isfinite(final_objective) else None
    gap_ratio = gap / ARC_LP_REFERENCE_OBJECTIVE if gap is not None else None
    selected_by_round = [
        {
            "round": row["round"],
            "candidate_id": row["candidate_id"],
            "demand_id": row["demand_id"],
            "oracle_entry_signal": parse_float(row["oracle_entry_signal"], math.nan),
            "candidate_flow_after_resolve": parse_float(row["candidate_flow_after_resolve"], 0.0),
            "candidate_flow_final_solution": parse_float(row["candidate_flow_final_solution"], 0.0),
        }
        for row in added_candidates
    ]
    summary = {
        "diagnostic_status": "SAFE_BLOCKED" if safe_blockers else "PASS",
        "max_rounds": max_rounds,
        "rounds_attempted": rounds_attempted,
        "rounds_with_candidate_added": len(added_candidates),
        "allow_variable_fixed_source_base": ALLOW_VARIABLE_FIXED_SOURCE_BASE,
        "allow_variable_oracle_candidate": ALLOW_VARIABLE_ORACLE_CANDIDATE,
        "allow_variable_initial_oracle_loop_objective": ALLOW_VARIABLE_INITIAL_ORACLE_LOOP_OBJECTIVE,
        "objective_initial": initial_objective,
        "objective_final": final_objective,
        "objective_change_total": objective_change_total,
        "objective_decreased_total": objective_change_total is not None and objective_change_total < -TOL,
        "selected_oracle_candidates_by_round": selected_by_round,
        "selected_candidate_reduced_costs_by_round": {
            str(row["round"]): parse_float(row["oracle_entry_signal"], math.nan) for row in added_candidates
        },
        "selected_candidate_flows_in_final_solution": {
            row["candidate_id"]: parse_float(row["candidate_flow_final_solution"], 0.0) for row in added_candidates
        },
        "stop_reason": stop_reason,
        "demand_residual_max_final": final_outputs.get("demand_residual_max"),
        "capacity_violation_count_final": final_outputs.get("capacity_violation_count"),
        "max_capacity_violation_final": final_outputs.get("max_capacity_violation"),
        "positive_flow_column_count_final": final_outputs.get("positive_flow_column_count"),
        "gap_to_arc_lp_reference_final": gap,
        "gap_ratio_to_arc_lp_reference_final": gap_ratio,
        "arc_lp_reference_objective": ARC_LP_REFERENCE_OBJECTIVE,
        "fixed_source_final_objective_reference": FIXED_SOURCE_FINAL_OBJECTIVE_REFERENCE,
        "schema_gate_status": gate_summary.get("schema_gate_status"),
        "connectivity_gate_status": gate_summary.get("connectivity_gate_status"),
        "known_column_cost_reconstruction_gate_status": gate_summary.get("known_column_cost_reconstruction_gate_status"),
        "known_candidate_reduced_cost_reconstruction_gate_status": gate_summary.get(
            "known_candidate_reduced_cost_reconstruction_gate_status"
        ),
        "prior_convention_gate_status": gate_summary.get("prior_convention_gate_status"),
        "validated_convention": gate_summary.get("validated_convention"),
        "phase2_initial_pool_hash_before": phase2_initial_hash_before,
        "phase2_initial_pool_hash_after": phase2_initial_hash_after,
        "phase2_initial_pool_mutated": phase2_initial_hash_before != phase2_initial_hash_after,
        "fixed_source_final_pool_hash_before": fixed_source_pool_hash_before,
        "fixed_source_final_pool_hash_after": fixed_source_pool_hash_after,
        "fixed_source_final_pool_mutated": fixed_source_pool_hash_before != fixed_source_pool_hash_after,
        "baseline_dynamic_columns_hash_before": baseline_hash_before,
        "baseline_dynamic_columns_hash_after": baseline_hash_after,
        "baseline_dynamic_columns_mutated": baseline_hash_before != baseline_hash_after,
        "oracle_candidates_written_to_baseline": False,
        "oracle_candidates_written_to_phase2_initial_pool": False,
        "oracle_candidates_written_to_fixed_source_outputs": False,
        "temporary_pool_used": True,
        "final_temporary_pool_column_count": len(pool),
        "full_assignment_run": False,
        "full_cg_run": False,
        "general_convergence_claimed": False,
        "global_optimality_claimed": False,
        "global_pricing_closure_claimed": False,
        "exact_arc_lp_flow_pattern_reproduction_claimed": False,
        "safe_blockers": safe_blockers,
        "interpretation": stop_interpretation(stop_reason, objective_change_total),
        "scope": SCOPE_BOUNDARY,
        "next_safe_step": "oracle Phase-II closure/claim-boundary audit"
        if stop_reason == STOP_NO_NEGATIVE and not safe_blockers
        else "review bounded oracle loop blockers or max-round cap before further oracle diagnostics",
    }
    hash_audit = {
        "phase2_initial_pool_path": rel(PHASE2_INITIAL_POOL),
        "phase2_initial_pool_hash_before": phase2_initial_hash_before,
        "phase2_initial_pool_hash_after": phase2_initial_hash_after,
        "phase2_initial_pool_mutated": phase2_initial_hash_before != phase2_initial_hash_after,
        "fixed_source_final_pool_path": rel(FIXED_SOURCE_FINAL_POOL),
        "fixed_source_final_pool_hash_before": fixed_source_pool_hash_before,
        "fixed_source_final_pool_hash_after": fixed_source_pool_hash_after,
        "fixed_source_final_pool_mutated": fixed_source_pool_hash_before != fixed_source_pool_hash_after,
        "baseline_dynamic_columns_path": rel(baseline_path),
        "baseline_dynamic_columns_hash_before": baseline_hash_before,
        "baseline_dynamic_columns_hash_after": baseline_hash_after,
        "accepted_baseline_dynamic_columns_hash": ACCEPTED_BASELINE_HASH,
        "baseline_dynamic_columns_mutated": baseline_hash_before != baseline_hash_after,
        "allow_variable_fixed_source_base": ALLOW_VARIABLE_FIXED_SOURCE_BASE,
        "allow_variable_oracle_candidate": ALLOW_VARIABLE_ORACLE_CANDIDATE,
        "allow_variable_initial_oracle_loop_objective": ALLOW_VARIABLE_INITIAL_ORACLE_LOOP_OBJECTIVE,
        "accepted_fixed_source_outputs_hash_before": fixed_source_outputs_hash_before,
        "accepted_fixed_source_outputs_hash_after": fixed_source_outputs_hash_after,
        "accepted_fixed_source_outputs_mutated": fixed_source_outputs_hash_before != fixed_source_outputs_hash_after,
        "oracle_candidates_written_to_baseline": False,
        "oracle_candidates_written_to_phase2_initial_pool": False,
        "oracle_candidates_written_to_fixed_source_outputs": False,
        "temporary_pool_used": True,
        "full_assignment_run": False,
        "full_cg_run": False,
    }
    stop_payload = {
        "stop_reason": stop_reason,
        "allowed_stop_reasons": sorted(ALLOWED_STOP_REASONS),
        "interpretation": summary["interpretation"],
        "safe_blockers": safe_blockers,
        "full_assignment_run": False,
        "full_cg_run": False,
        "general_convergence_claimed": False,
    }
    gap_payload = {
        "arc_lp_reference_objective": ARC_LP_REFERENCE_OBJECTIVE,
        "fixed_source_final_objective_reference": FIXED_SOURCE_FINAL_OBJECTIVE_REFERENCE,
        "oracle_loop_final_objective": final_objective,
        "gap_to_arc_lp_reference_final": gap,
        "gap_ratio_to_arc_lp_reference_final": gap_ratio,
        "objective_below_arc_lp_reference": bool(gap is not None and gap < -ARC_LP_COMPARISON_TOLERANCE),
        "diagnostic_comparison_only": True,
        "global_optimality_claimed": False,
        "exact_arc_lp_flow_pattern_reproduction_claimed": False,
    }
    write_outputs(
        output_dir,
        summary,
        rounds,
        objective_by_round,
        added_candidates,
        probe_rows_all,
        final_outputs,
        final_dual_solution,
        duplicate_audit_rows(pool),
        hash_audit,
        stop_payload,
        gap_payload,
    )
    write_csv(
        output_dir / "phase2_oracle_loop_temporary_pool_final.csv",
        pool_output_rows(pool),
        [
            "column_id",
            "path_id",
            "demand_id",
            "origin_node_id",
            "destination_node_id",
            "departure_time",
            "arrival_time",
            "travel_time",
            "generalized_cost",
            "node_sequence",
            "link_sequence",
            "time_sequence",
            "arc_sequence",
            "phase2_pool_column_type",
            "source_metadata",
            "added_in_phase1_round",
            "phase1_final_flow",
            "written_to_baseline_dynamic_columns",
            "output_only_phase2_initial_pool",
            "output_only_phase2_loop_pool",
            "output_only_phase2_oracle_loop_pool",
            "pool_membership",
            "candidate_source",
            "added_in_phase2_round",
            "oracle_entry_signal_at_addition",
            "written_to_phase2_initial_pool",
            "written_to_fixed_source_outputs",
        ],
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run bounded oracle Phase-II loop diagnostic.")
    parser.add_argument("--config", default=DEFAULT_CURRENT_POOL_CONFIG)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--input-artifacts-json", default=None)
    parser.add_argument("--benchmark-id", default="second_controlled_benchmark_link55")
    parser.add_argument("--no-mutate-accepted-outputs", action="store_true")
    parser.add_argument("--precheck-only", action="store_true")
    parser.add_argument("--max-rounds", type=int, default=DEFAULT_MAX_ROUNDS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.benchmark_id != "second_controlled_benchmark_link55":
        print(f"Unsupported benchmark id: {args.benchmark_id}")
        return 1
    artifacts = apply_input_manifest(args.input_artifacts_json)
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = ROOT_DIR / output_dir
    if args.no_mutate_accepted_outputs and output_dir.resolve() == DEFAULT_OUTPUT_DIR.resolve():
        print("Refusing to write to accepted default output folder with --no-mutate-accepted-outputs.")
        return 1
    config_path = artifacts.get("config_path") or artifacts.get("config") or args.config
    summary = run_bounded_oracle_loop(
        config_path,
        output_dir,
        args.max_rounds,
        precheck_only=args.precheck_only,
    )
    print(f"Bounded oracle Phase-II loop diagnostic status: {summary['diagnostic_status']}")
    print(f"Max rounds: {summary['max_rounds']}")
    print(f"Rounds attempted: {summary['rounds_attempted']}")
    print(f"Oracle candidates added: {summary['rounds_with_candidate_added']}")
    print(f"Objective initial: {summary['objective_initial']}")
    print(f"Objective final: {summary['objective_final']}")
    print(f"Objective change total: {summary['objective_change_total']}")
    print(f"Gap to arc-LP reference final: {summary['gap_to_arc_lp_reference_final']}")
    print(f"Stop reason: {summary['stop_reason']}")
    print(f"Demand residual max final: {summary['demand_residual_max_final']}")
    print(f"Capacity violation count final: {summary['capacity_violation_count_final']}")
    print(f"Phase-II initial pool mutated: {summary['phase2_initial_pool_mutated']}")
    print(f"Fixed-source final pool mutated: {summary['fixed_source_final_pool_mutated']}")
    print(f"Baseline dynamic_columns.csv mutated: {summary['baseline_dynamic_columns_mutated']}")
    print(f"Full assignment run: {summary['full_assignment_run']}")
    print(f"Full CG run: {summary['full_cg_run']}")
    print(f"Report: {output_dir / 'phase2_oracle_bounded_loop_report.md'}")
    return 0 if summary["diagnostic_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
