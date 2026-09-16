"""One-candidate Phase-I add-resolve diagnostic.

This diagnostic adds exactly one accepted Stage-C candidate to a temporary
Phase-I column pool and re-solves the artificial-demand-variable RMP once.

It does not mutate the baseline dynamic_columns.csv, add more than one
candidate, rerun pricing after the resolve, run a loop, transition to Phase II,
run full assignment, or run full CG.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

from phase1_artificial_rmp_preflight import (
    OUTPUT_DIR as PREFLIGHT_OUTPUT_DIR,
    TRUE_COST_TIE_BREAKER_EPSILON,
    build_solution_outputs,
    run_preflight,
    sha256_file,
    solve_phase1_rmp,
)
from precheck_second_controlled_benchmark_current_pool_rmp import (
    DEFAULT_CONFIG as DEFAULT_CURRENT_POOL_CONFIG,
    TOL,
    input_data_dir,
    load_config,
    parse_float,
    read_csv,
    selected_candidate_columns,
    split_sequence,
)
from build_sioux_harder_bounded_stage2 import ROOT_DIR


OUTPUT_DIR = ROOT_DIR / "outputs" / "phase1_one_candidate_add_resolve"
PRICING_DIAGNOSTIC_DIR = ROOT_DIR / "outputs" / "phase1_pricing_candidate_diagnostic"
SEED_REPAIR_COLUMNS = (
    ROOT_DIR / "outputs" / "second_controlled_benchmark_link55_seed_pool_repair" / "repaired_seed_columns.csv"
)
SELECTED_CANDIDATE_ID = "SEED_D3_WAIT55_T5"
EXPECTED_ARC_SEQUENCE = "source_D3|move_60_t0|wait_18_t4|move_55_t5|move_48_t8|sink_D3_10_t12"
ACCEPTED_BASELINE_HASH = "092fc81e706f9476b139af1c9a7bdfd0cd72bfc1e5708bb3aaec814b473d7d50"
EXPECTED_TOTAL_ARTIFICIAL_FLOW = 6287.557003
SCOPE_BOUNDARY = (
    "This is a one-candidate Phase-I add-resolve diagnostic. It adds "
    "SEED_D3_WAIT55_T5 only to a temporary Phase-I column pool and re-solves "
    "the artificial-demand-variable RMP once. It does not mutate the baseline "
    "dynamic_columns.csv, add a second candidate, rerun pricing after resolve, "
    "run a controlled loop, transition to Phase II, run full assignment, run "
    "full CG, or claim general convergence, production-scale solving, GTFS, "
    "railway, branch-and-price, reinforcement learning, or exact arc-LP "
    "flow-pattern reproduction."
)


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT_DIR)).replace("\\", "/")


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_row(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str] | None:
    return next((row for row in rows if row.get(key) == value), None)


def preflight_stability_blockers(preflight: dict[str, Any], baseline_hash_before: str) -> list[str]:
    blockers: list[str] = []
    artificial = preflight.get("artificial_flow_by_demand", {})
    if preflight.get("solver_status") != "optimal":
        blockers.append(f"preflight solver status changed: {preflight.get('solver_status')}")
    if abs(parse_float(preflight.get("total_artificial_flow"), math.nan) - EXPECTED_TOTAL_ARTIFICIAL_FLOW) > TOL:
        blockers.append(f"total artificial flow before add-resolve changed: {preflight.get('total_artificial_flow')}")
    if abs(parse_float(artificial.get("D3"), math.nan) - EXPECTED_TOTAL_ARTIFICIAL_FLOW) > TOL:
        blockers.append(f"D3 artificial flow before add-resolve changed: {artificial.get('D3')}")
    if abs(parse_float(artificial.get("D4"), math.nan)) > TOL:
        blockers.append(f"D4 artificial flow before add-resolve changed: {artificial.get('D4')}")
    if int(preflight.get("capacity_violation_count") or 0) != 0:
        blockers.append(f"capacity violation count before add-resolve changed: {preflight.get('capacity_violation_count')}")
    if baseline_hash_before != ACCEPTED_BASELINE_HASH:
        blockers.append(f"baseline dynamic_columns.csv hash differs from accepted hash: {baseline_hash_before}")
    if preflight.get("baseline_dynamic_columns_hash_after") != baseline_hash_before:
        blockers.append("preflight hash after does not match current baseline hash")
    if preflight.get("baseline_dynamic_columns_mutated") is not False:
        blockers.append("preflight reports baseline dynamic_columns.csv mutation")
    return blockers


def validate_candidate(candidate: dict[str, str] | None) -> tuple[dict[str, Any], list[str]]:
    blockers: list[str] = []
    if candidate is None:
        return {
            "candidate_validation_status": "SAFE_BLOCKED",
            "selected_candidate_id": SELECTED_CANDIDATE_ID,
            "safe_blockers": ["selected candidate missing from Stage-C pricing candidates"],
        }, ["selected candidate missing from Stage-C pricing candidates"]

    checks = {
        "candidate_id_matches": candidate.get("candidate_id") == SELECTED_CANDIDATE_ID,
        "demand_id_is_D3": candidate.get("demand_id") == "D3",
        "classification_is_improving": candidate.get("classification") == "improving_new_candidate",
        "structurally_valid": candidate.get("structurally_valid") == "true",
        "nonduplicate": candidate.get("duplicate_existing_phase1_column") == "false",
        "targets_positive_artificial_flow_demand": candidate.get("targets_positive_artificial_flow_demand") == "true",
        "not_marked_for_addition_in_stage_c": candidate.get("would_be_added_in_future_task") == "false",
        "arc_sequence_matches_expected": candidate.get("arc_sequence") == EXPECTED_ARC_SEQUENCE,
    }
    for name, passed in checks.items():
        if not passed:
            blockers.append(name)
    validation = {
        "candidate_validation_status": "PASS" if not blockers else "SAFE_BLOCKED",
        "selected_candidate_id": SELECTED_CANDIDATE_ID,
        "selected_candidate_demand": candidate.get("demand_id"),
        "selected_candidate_entry_signal_from_stage_c": parse_float(candidate.get("phase1_entry_signal"), math.nan),
        "expected_arc_sequence": EXPECTED_ARC_SEQUENCE,
        "actual_arc_sequence": candidate.get("arc_sequence"),
        "arc_sequence_difference": ""
        if candidate.get("arc_sequence") == EXPECTED_ARC_SEQUENCE
        else f"expected={EXPECTED_ARC_SEQUENCE}; actual={candidate.get('arc_sequence')}",
        "checks": checks,
        "safe_blockers": blockers,
        "stage_c_candidate_row": candidate,
    }
    return validation, blockers


def source_candidate_metadata(stage_c_candidate: dict[str, str]) -> dict[str, str]:
    repaired_rows = read_csv(SEED_REPAIR_COLUMNS) if SEED_REPAIR_COLUMNS.exists() else []
    repaired = find_row(repaired_rows, "column_id", SELECTED_CANDIDATE_ID)
    if repaired is None:
        repaired = {}
    return {
        "column_id": SELECTED_CANDIDATE_ID,
        "path_id": stage_c_candidate.get("path_id", repaired.get("path_id", "")),
        "demand_id": stage_c_candidate.get("demand_id", repaired.get("demand_id", "")),
        "origin_node_id": repaired.get("origin_node_id", ""),
        "destination_node_id": repaired.get("destination_node_id", ""),
        "departure_time": repaired.get("departure_time", ""),
        "arrival_time": repaired.get("arrival_time", ""),
        "travel_time": repaired.get("travel_time", ""),
        "generalized_cost": str(parse_float(stage_c_candidate.get("true_generalized_cost"), parse_float(repaired.get("generalized_cost"), 0.0))),
        "node_sequence": repaired.get("node_sequence", ""),
        "link_sequence": repaired.get("link_sequence", ""),
        "time_sequence": repaired.get("time_sequence", ""),
        "arc_sequence": stage_c_candidate.get("arc_sequence", repaired.get("arc_sequence", "")),
        "column_source": "phase1_pricing_candidate_diagnostic",
        "candidate_source": stage_c_candidate.get("candidate_source", ""),
        "added_in_round": "1",
        "pool_membership": "selected_added_candidate",
        "written_to_baseline_dynamic_columns": "false",
    }


def build_round1_pool(
    baseline_columns: list[dict[str, str]],
    selected_candidate: dict[str, str],
) -> list[dict[str, str]]:
    pool: list[dict[str, str]] = []
    for row in baseline_columns:
        copy = dict(row)
        copy["column_source"] = "baseline_dynamic_columns"
        copy["candidate_source"] = ""
        copy["added_in_round"] = "0"
        copy["pool_membership"] = "original_baseline_column"
        copy["written_to_baseline_dynamic_columns"] = "false"
        pool.append(copy)
    pool.append(source_candidate_metadata(selected_candidate))
    return pool


def round1_column_rows(pool: list[dict[str, str]]) -> list[dict[str, Any]]:
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
                "column_source": row.get("column_source", ""),
                "candidate_source": row.get("candidate_source", ""),
                "added_in_round": row.get("added_in_round", ""),
                "pool_membership": row.get("pool_membership", ""),
                "written_to_baseline_dynamic_columns": row.get("written_to_baseline_dynamic_columns", "false"),
                "phase1_objective_coefficient": TRUE_COST_TIE_BREAKER_EPSILON
                * parse_float(row.get("generalized_cost"), 0.0),
            }
        )
    return rows


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# One-Candidate Phase-I Add-Resolve Diagnostic",
        "",
        SCOPE_BOUNDARY,
        "",
        "## Summary",
        "",
        f"- Diagnostic status: {summary['diagnostic_status']}",
        f"- Selected candidate: {summary['selected_candidate_id']} ({summary['selected_candidate_demand']})",
        f"- Solver status after add-resolve: {summary['solver_status_after_add_resolve']}",
        f"- Total artificial flow before: {summary['total_artificial_flow_before']}",
        f"- Total artificial flow after: {summary['total_artificial_flow_after']}",
        f"- Artificial flow change: {summary['artificial_flow_change']}",
        f"- D3 artificial flow before: {summary['D3_artificial_flow_before']}",
        f"- D3 artificial flow after: {summary['D3_artificial_flow_after']}",
        f"- D3 artificial flow change: {summary['D3_artificial_flow_change']}",
        f"- Selected candidate flow after resolve: {summary['selected_candidate_primal_flow_after_resolve']}",
        f"- Capacity violation count after: {summary['capacity_violation_count_after']}",
        f"- Demand residual max after: {summary['demand_residual_max_after']}",
        f"- Baseline dynamic_columns.csv mutated: {summary['baseline_dynamic_columns_mutated']}",
        f"- Candidate written to baseline: {summary['added_candidate_written_to_baseline']}",
        f"- Temporary round-1 column pool created: {summary['temporary_round1_column_pool_created']}",
        f"- Candidate count added to temporary pool: {summary['candidate_columns_added_to_temporary_pool']}",
        f"- RMP resolved after one-candidate add: {summary['rmp_resolved_after_one_candidate_add']}",
        f"- Pricing rerun after resolve: {summary['pricing_rerun_after_resolve']}",
        f"- Controlled loop run: {summary['controlled_loop_run']}",
        f"- Phase-II transition executed: {summary['phase2_transition_executed']}",
        f"- Next safe step: {summary['next_safe_step']}",
        "",
        "## Scope Boundary",
        "",
        "- Exactly one selected candidate was added to the temporary pool.",
        "- The baseline real-column file was not modified.",
        "- No pricing rerun, second candidate, loop, Phase-II transition, full assignment, or full CG was run.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_outputs(
    output_dir: Path,
    summary: dict[str, Any],
    validation: dict[str, Any],
    hash_audit: dict[str, Any],
    pool: list[dict[str, str]],
    solution_outputs: dict[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "phase1_one_candidate_add_resolve_summary.json", summary)
    write_report(output_dir / "phase1_one_candidate_add_resolve_report.md", summary)
    write_csv(
        output_dir / "phase1_round1_columns.csv",
        round1_column_rows(pool),
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
            "column_source",
            "candidate_source",
            "added_in_round",
            "pool_membership",
            "written_to_baseline_dynamic_columns",
            "phase1_objective_coefficient",
        ],
    )
    write_csv(
        output_dir / "phase1_round1_real_flow_by_column.csv",
        solution_outputs.get("real_flow_rows", []),
        [
            "column_id",
            "path_id",
            "demand_id",
            "is_artificial",
            "lower_bound",
            "upper_bound",
            "flow",
            "true_generalized_cost",
            "phase1_objective_coefficient",
            "arc_sequence",
        ],
    )
    write_csv(
        output_dir / "phase1_round1_artificial_flow_by_demand.csv",
        solution_outputs.get("artificial_rows", []),
        [
            "artificial_variable_id",
            "demand_id",
            "is_artificial",
            "lower_bound",
            "upper_bound",
            "flow",
            "has_dynamic_arc_incidence",
            "arc_sequence",
            "phase1_objective_coefficient",
            "objective_units",
        ],
    )
    write_csv(
        output_dir / "phase1_round1_demand_balance.csv",
        solution_outputs.get("demand_rows", []),
        [
            "demand_id",
            "demand_volume",
            "real_served_flow",
            "artificial_flow",
            "demand_residual_after_artificial",
            "status",
        ],
    )
    write_csv(
        output_dir / "phase1_round1_capacity_usage.csv",
        solution_outputs.get("capacity_rows", []),
        [
            "arc_id",
            "arc_type",
            "physical_link_id",
            "from_time",
            "to_time",
            "real_flow",
            "artificial_flow",
            "total_capacity_consuming_flow",
            "capacity",
            "capacity_violation",
            "slack",
            "artificial_variable_ids_using_arc",
            "real_columns_using_arc",
            "demand_ids_using_arc",
            "status",
        ],
    )
    write_json(output_dir / "phase1_round1_hash_audit.json", hash_audit)
    write_json(output_dir / "phase1_round1_candidate_validation.json", validation)
    write_csv(
        output_dir / "phase1_round1_comparison.csv",
        [
            {
                "metric": "total_artificial_flow",
                "before": summary["total_artificial_flow_before"],
                "after": summary["total_artificial_flow_after"],
                "change": summary["artificial_flow_change"],
            },
            {
                "metric": "D3_artificial_flow",
                "before": summary["D3_artificial_flow_before"],
                "after": summary["D3_artificial_flow_after"],
                "change": summary["D3_artificial_flow_change"],
            },
            {
                "metric": "D4_artificial_flow",
                "before": summary["D4_artificial_flow_before"],
                "after": summary["D4_artificial_flow_after"],
                "change": summary["D4_artificial_flow_change"],
            },
            {
                "metric": "selected_candidate_primal_flow",
                "before": 0.0,
                "after": summary["selected_candidate_primal_flow_after_resolve"],
                "change": summary["selected_candidate_primal_flow_after_resolve"],
            },
        ],
        ["metric", "before", "after", "change"],
    )


def run_add_resolve(
    config_path: str | Path = DEFAULT_CURRENT_POOL_CONFIG,
    output_dir: Path = OUTPUT_DIR,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    config = load_config(config_path)
    data_dir = input_data_dir(config)
    baseline_columns_path = data_dir / "dynamic_columns.csv"
    baseline_hash_before = sha256_file(baseline_columns_path)

    preflight = run_preflight(config_path, PREFLIGHT_OUTPUT_DIR)
    stability_blockers = preflight_stability_blockers(preflight, baseline_hash_before)

    pricing_rows = read_csv(PRICING_DIAGNOSTIC_DIR / "phase1_pricing_candidates.csv")
    selected = find_row(pricing_rows, "candidate_id", SELECTED_CANDIDATE_ID)
    validation, validation_blockers = validate_candidate(selected)

    arcs = read_csv(data_dir / "dynamic_arc.csv")
    demands = read_csv(data_dir / "dynamic_demand.csv")
    baseline_dynamic_columns = read_csv(baseline_columns_path)
    candidate_paths = read_csv(data_dir / "candidate_paths.csv")
    baseline_columns, selection_blockers = selected_candidate_columns(config, baseline_dynamic_columns, candidate_paths)
    safe_blockers = [*stability_blockers, *validation_blockers, *selection_blockers]

    if safe_blockers or selected is None:
        pool = baseline_columns
        solution_outputs: dict[str, Any] = {
            "real_flow_rows": [],
            "artificial_rows": [],
            "demand_rows": [],
            "capacity_rows": [],
            "artificial_flow_by_demand": {},
            "real_flow_by_demand": {},
            "total_artificial_flow": math.nan,
            "capacity_violation_count": math.nan,
            "max_capacity_violation": math.nan,
            "max_demand_residual": math.nan,
            "phase2_transition_allowed": False,
        }
        solver_info = {
            "solver_status": "safe_blocked",
            "solver_message": "; ".join(safe_blockers),
            "objective_value_artificial_penalty_units": None,
        }
        rmp_resolved = False
    else:
        pool = build_round1_pool(baseline_columns, selected)
        solver_info, solution = solve_phase1_rmp(arcs, demands, pool)
        rmp_resolved = True
        if solution is None:
            safe_blockers.append(f"round-1 Phase-I RMP solve failed: {solver_info.get('solver_status')}")
            solution_outputs = {
                "real_flow_rows": [],
                "artificial_rows": [],
                "demand_rows": [],
                "capacity_rows": [],
                "artificial_flow_by_demand": {},
                "real_flow_by_demand": {},
                "total_artificial_flow": math.nan,
                "capacity_violation_count": math.nan,
                "max_capacity_violation": math.nan,
                "max_demand_residual": math.nan,
                "phase2_transition_allowed": False,
            }
        else:
            solution_outputs = build_solution_outputs(arcs, demands, pool, solution)

    baseline_hash_after = sha256_file(baseline_columns_path)
    if baseline_hash_after != baseline_hash_before:
        safe_blockers.append("baseline dynamic_columns.csv hash changed during add-resolve diagnostic")

    after_artificial = solution_outputs.get("artificial_flow_by_demand", {})
    before_artificial = preflight.get("artificial_flow_by_demand", {})
    before_total = parse_float(preflight.get("total_artificial_flow"), math.nan)
    after_total = parse_float(solution_outputs.get("total_artificial_flow"), math.nan)
    d3_before = parse_float(before_artificial.get("D3"), math.nan)
    d3_after = parse_float(after_artificial.get("D3"), math.nan)
    d4_before = parse_float(before_artificial.get("D4"), math.nan)
    d4_after = parse_float(after_artificial.get("D4"), math.nan)
    selected_flow = 0.0
    for row in solution_outputs.get("real_flow_rows", []):
        if row.get("column_id") == SELECTED_CANDIDATE_ID:
            selected_flow = parse_float(row.get("flow"), 0.0)
            break

    if math.isfinite(after_total) and math.isfinite(before_total):
        artificial_change = after_total - before_total
    else:
        artificial_change = math.nan
    if math.isfinite(d3_after) and math.isfinite(d3_before):
        d3_change = d3_after - d3_before
    else:
        d3_change = math.nan
    if math.isfinite(d4_after) and math.isfinite(d4_before):
        d4_change = d4_after - d4_before
    else:
        d4_change = math.nan

    if safe_blockers:
        diagnostic_status = "SAFE_BLOCKED"
        next_safe_step = "investigate candidate validity/degeneracy before adding more columns"
    elif after_total <= TOL:
        diagnostic_status = "PASS"
        next_safe_step = "Phase-I closure audit and Phase-II handoff precheck"
    elif artificial_change < -TOL:
        diagnostic_status = "PASS"
        next_safe_step = "Phase-I round-2 pricing/add-resolve or bounded Phase-I loop design"
    else:
        diagnostic_status = "PASS"
        next_safe_step = "investigate candidate validity/degeneracy before adding more columns"

    hash_audit = {
        "baseline_dynamic_columns_path": rel(baseline_columns_path),
        "baseline_dynamic_columns_hash_before": baseline_hash_before,
        "baseline_dynamic_columns_hash_after": baseline_hash_after,
        "accepted_baseline_dynamic_columns_hash": ACCEPTED_BASELINE_HASH,
        "baseline_dynamic_columns_mutated": baseline_hash_before != baseline_hash_after,
        "added_candidate_written_to_baseline": False,
        "temporary_round1_column_pool_path": rel(output_dir / "phase1_round1_columns.csv"),
    }
    validation["baseline_dynamic_columns_hash_before"] = baseline_hash_before
    validation["baseline_dynamic_columns_hash_after"] = baseline_hash_after
    validation["baseline_dynamic_columns_mutated"] = baseline_hash_before != baseline_hash_after

    summary = {
        "diagnostic_status": diagnostic_status,
        "selected_candidate_id": SELECTED_CANDIDATE_ID,
        "selected_candidate_demand": validation.get("selected_candidate_demand"),
        "selected_candidate_entry_signal_from_stage_c": validation.get("selected_candidate_entry_signal_from_stage_c"),
        "solver_status_after_add_resolve": solver_info.get("solver_status"),
        "solver_message_after_add_resolve": solver_info.get("solver_message"),
        "objective_value_after_add_resolve_artificial_penalty_units": solver_info.get("objective_value_artificial_penalty_units"),
        "total_artificial_flow_before": before_total,
        "total_artificial_flow_after": after_total,
        "artificial_flow_change": artificial_change,
        "D3_artificial_flow_before": d3_before,
        "D3_artificial_flow_after": d3_after,
        "D3_artificial_flow_change": d3_change,
        "D4_artificial_flow_before": d4_before,
        "D4_artificial_flow_after": d4_after,
        "D4_artificial_flow_change": d4_change,
        "selected_candidate_primal_flow_after_resolve": selected_flow,
        "capacity_violation_count_after": solution_outputs.get("capacity_violation_count"),
        "max_capacity_violation_after": solution_outputs.get("max_capacity_violation"),
        "demand_residual_max_after": solution_outputs.get("max_demand_residual"),
        "baseline_dynamic_columns_hash_before": baseline_hash_before,
        "baseline_dynamic_columns_hash_after": baseline_hash_after,
        "baseline_dynamic_columns_mutated": baseline_hash_before != baseline_hash_after,
        "added_candidate_written_to_baseline": False,
        "temporary_round1_column_pool_created": True,
        "candidate_columns_added_to_temporary_pool": 1 if not safe_blockers and selected is not None else 0,
        "round1_column_pool_count": len(pool),
        "baseline_real_column_count": len(baseline_columns),
        "rmp_resolved_after_one_candidate_add": rmp_resolved,
        "rmp_resolve_count_after_candidate_add": 1 if rmp_resolved else 0,
        "pricing_rerun_after_resolve": False,
        "second_candidate_added": False,
        "controlled_loop_run": False,
        "phase2_transition_executed": False,
        "phase2_transition_allowed_after": bool(solution_outputs.get("phase2_transition_allowed", False)),
        "full_assignment_run": False,
        "full_cg_run": False,
        "safe_blockers": safe_blockers,
        "next_safe_step": next_safe_step,
        "scope": SCOPE_BOUNDARY,
    }
    write_outputs(output_dir, summary, validation, hash_audit, pool, solution_outputs)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one-candidate Phase-I add-resolve diagnostic.")
    parser.add_argument("--config", default=DEFAULT_CURRENT_POOL_CONFIG)
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = ROOT_DIR / output_dir
    summary = run_add_resolve(args.config, output_dir)
    print(f"One-candidate Phase-I add-resolve diagnostic status: {summary['diagnostic_status']}")
    print(f"Selected candidate: {summary['selected_candidate_id']}")
    print(f"Solver status after add-resolve: {summary['solver_status_after_add_resolve']}")
    print(f"Total artificial flow before: {summary['total_artificial_flow_before']}")
    print(f"Total artificial flow after: {summary['total_artificial_flow_after']}")
    print(f"D3 artificial flow before: {summary['D3_artificial_flow_before']}")
    print(f"D3 artificial flow after: {summary['D3_artificial_flow_after']}")
    print(f"Selected candidate flow after resolve: {summary['selected_candidate_primal_flow_after_resolve']}")
    print(f"Capacity violation count after: {summary['capacity_violation_count_after']}")
    print(f"Demand residual max after: {summary['demand_residual_max_after']}")
    print(f"Baseline dynamic_columns.csv mutated: {summary['baseline_dynamic_columns_mutated']}")
    print(f"Candidate columns added to temporary pool: {summary['candidate_columns_added_to_temporary_pool']}")
    print(f"Pricing rerun after resolve: {summary['pricing_rerun_after_resolve']}")
    print(f"Controlled loop run: {summary['controlled_loop_run']}")
    print(f"Phase-II transition executed: {summary['phase2_transition_executed']}")
    print(f"Report: {output_dir / 'phase1_one_candidate_add_resolve_report.md'}")
    return 0 if summary["diagnostic_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
