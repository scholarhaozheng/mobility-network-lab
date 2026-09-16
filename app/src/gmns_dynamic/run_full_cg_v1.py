"""Manifest-driven bounded Full CG v1 orchestrator.

This runner consolidates the verified bounded Phase-I and Phase-II components
for selected finite fixtures. It is not a full assignment solver, not a
production-scale solver, not branch-and-price, and not a global convergence
proof.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import heapq
import json
import math
import time
from pathlib import Path
from typing import Any

from build_sioux_harder_bounded_stage2 import ROOT_DIR
from phase1_artificial_dual_audit import (
    build_dual_solution as build_phase1_dual_solution,
    build_phase1_model,
    convention_trials,
    solve_model as solve_phase1_model,
)
from phase1_artificial_rmp_preflight import build_solution_outputs as build_phase1_solution_outputs
from phase1_artificial_rmp_preflight import sha256_file
from phase1_pricing_candidate_diagnostic import validated_signs
from phase_i_general_pricing_oracle import run_oracle as run_phase_i_oracle
from phase2_dynamic_pricing_oracle_precheck import (
    demand_dual,
    raw_capacity_dual_sum,
    reconstruct_path_cost,
)
from phase2_oracle_bounded_loop_diagnostic import (
    REDUCED_COST_TOLERANCE,
    build_sequence_metadata,
    classify_oracle_candidate,
    duplicate_audit_rows,
    pool_output_rows,
    selected_flow,
    shortest_path_bellman_ford,
    solve_current_pool,
    source_sink_maps,
    validation_convention,
)
from precheck_second_controlled_benchmark_current_pool_rmp import TOL, parse_float, read_csv, split_sequence


TASK_NAME = "bounded_full_cg_v1_orchestrator"
REFERENCE_TOLERANCE = 1e-5
SCOPE_BOUNDARY = (
    "This is bounded Full CG v1 for selected finite fixtures. It is not full "
    "Sioux Falls assignment, not production-scale solving, not global "
    "convergence proof, not exact arc-flow-pattern reproduction, not "
    "branch-and-price, and not reinforcement learning."
)
ORACLE_ID_PHASE_I = "bounded_full_cg_v1_general_phase_i_oracle"
PHASE_II_CANDIDATE_SOURCE = "bounded_full_cg_v1_dynamic_network_phase_ii_oracle"
PHASE_II_PRICING_MODE_ONE_PROBE = "one_probe"
PHASE_II_PRICING_MODE_K_SHORTEST = "k_shortest"
PHASE_II_PRICING_MODES = {PHASE_II_PRICING_MODE_ONE_PROBE, PHASE_II_PRICING_MODE_K_SHORTEST}
PHASE_II_ADD_BEST_ONE_PER_ROUND = "add_best_one_per_round"
PHASE_II_ADD_BEST_ONE_PER_DEMAND = "add_best_one_per_demand"
PHASE_II_ADD_ALL_IMPROVING_UP_TO_CAP = "add_all_improving_nonduplicates_up_to_cap"
PHASE_II_ADD_POLICIES = {
    PHASE_II_ADD_BEST_ONE_PER_ROUND,
    PHASE_II_ADD_BEST_ONE_PER_DEMAND,
    PHASE_II_ADD_ALL_IMPROVING_UP_TO_CAP,
}
DEFAULT_PHASE_II_PRICING_MODE = PHASE_II_PRICING_MODE_ONE_PROBE
DEFAULT_PHASE_II_ADD_POLICY = PHASE_II_ADD_BEST_ONE_PER_ROUND
DEFAULT_K_SHORTEST_K = 1
PHASE_II_COVERAGE_ONE_PROBE = "one_probe_all_demands_one_candidate"
PHASE_II_COVERAGE_K_SHORTEST_FAIR = "fair_round_robin_by_path_rank"
PHASE_II_CAP_NOT_TRUNCATED = "NOT_TRUNCATED"
PHASE_II_CAP_TRUNCATED = "CAP_TRUNCATED_CANDIDATE_SEARCH"
EXECUTION_MODES = {
    "bounded_full_cg_v1_pass",
    "bounded_full_cg_v1_pass_no_reference",
    "bounded_full_cg_v1_reference_gap_reported",
    "bounded_full_cg_v1_phase_i_blocked",
    "bounded_full_cg_v1_phase_ii_initialization_blocked",
    "bounded_full_cg_v1_phase_ii_partial_progress",
    "bounded_full_cg_v1_no_improving_candidate",
    "bounded_full_cg_v1_safe_blocker",
}
REQUIRED_MANIFEST_KEYS = [
    "benchmark_id",
    "dynamic_data_dir",
    "demand_file",
    "dynamic_arc_file",
    "current_candidate_pool_file",
    "output_root",
    "max_phase_i_rounds",
    "max_phase_ii_rounds",
    "max_candidates_per_demand_per_round",
    "runtime_cap_seconds",
    "no_mutate",
    "reference_comparison_policy",
    "stop_certificate_policy",
    "claim_boundary_policy",
]
PHASE_I_TRACE_FIELDS = [
    "solution_index",
    "round",
    "added_candidate_count",
    "selected_candidate_added_to_reach_solution",
    "solver_status",
    "total_artificial_flow",
    "capacity_violation_count",
    "max_capacity_violation",
    "demand_residual_max",
]
PHASE_I_SELECTED_FIELDS = [
    "round",
    "pool_column_count_before",
    "total_artificial_flow_before",
    "generated_candidates",
    "improving_nonduplicate_candidate_count",
    "selected_candidate_id",
    "candidate_added",
    "pool_column_count_after",
    "total_artificial_flow_after",
    "capacity_violation_count_after",
    "demand_residual_max_after",
    "original_phase_i_oracle_candidate_id",
    "selected_candidate_demand",
    "selected_candidate_entry_signal",
    "arc_sequence",
    "written_to_baseline_dynamic_columns",
    "stop_reason_if_stopped",
]
PHASE_I_CANDIDATE_FIELDS = [
    "round",
    "candidate_id",
    "demand_id",
    "classification",
    "phase1_entry_signal",
    "arc_sequence",
    "duplicate_existing_phase1_column",
    "duplicate_of_column_id",
]
PHASE_II_SOLUTION_FIELDS = [
    "column_id",
    "path_id",
    "demand_id",
    "flow",
    "generalized_cost",
    "objective_contribution",
    "arc_sequence",
]
FINAL_PHASE_II_SOLUTION_FIELDS = [
    "model_id",
    "model_signature",
    "pool_id",
    "pool_signature",
    "solve_iteration",
    "phase_ii_round",
    "column_id",
    "path_id",
    "demand_id",
    "phase2_pool_column_type",
    "source_metadata",
    "added_in_phase1_round",
    "lower_bound",
    "upper_bound",
    "lower_bound_marginal",
    "upper_bound_marginal",
    "flow",
    "positive_flow",
    "cost_field_used",
    "objective_coefficient",
    "objective_contribution",
    "arc_sequence",
]
PHASE_II_AUDIT_FIELDS = [
    "demand_id",
    "demand_volume",
    "served_flow",
    "demand_residual",
    "status",
    "arc_id",
    "capacity",
    "flow",
    "capacity_slack",
    "capacity_violation",
]
PHASE_II_OBJECTIVE_TRACE_FIELDS = [
    "solution_index",
    "round",
    "selected_candidate_added_to_reach_solution",
    "pool_column_count",
    "solver_status",
    "objective_value",
    "objective_change_from_previous",
    "arc_lp_reference_objective",
    "gap_vs_reference",
    "objective_level_reference_match",
    "demand_residual_max",
    "capacity_violation_count",
]
PHASE_II_ROUND_LOG_FIELDS = [
    "round",
    "phase_ii_pricing_mode",
    "phase_ii_add_policy",
    "k_shortest_k",
    "max_phase_ii_candidates_per_demand",
    "max_phase_ii_candidates_per_round",
    "max_phase_ii_candidates_per_round_requested",
    "strict_phase_ii_candidate_round_cap",
    "demand_coverage_policy",
    "cap_truncation_status",
    "demand_count",
    "priced_demand_count",
    "unpriced_demand_count",
    "pool_column_count_before",
    "rmp_solver_status_before",
    "rmp_objective_before",
    "generated_candidates",
    "improving_nonduplicates",
    "duplicate_candidates",
    "invalid_candidates",
    "selected_candidate_id",
    "selected_candidate_count",
    "selected_candidate_demand",
    "selected_candidate_reduced_cost",
    "candidate_added",
    "pool_column_count_after",
    "rmp_solver_status_after",
    "rmp_objective_after",
    "objective_change",
    "selected_candidate_flow_after_resolve",
    "demand_residual_max",
    "capacity_violation_count",
    "stop_reason",
]
PHASE_II_SELECTED_FIELDS = [
    "round",
    "phase_ii_pricing_mode",
    "phase_ii_add_policy",
    "selected_round_rank",
    "candidate_id",
    "demand_id",
    "candidate_path_rank",
    "arc_sequence",
    "generalized_cost",
    "reduced_cost_entry_signal",
    "classification_at_addition",
    "candidate_flow_after_resolve",
    "candidate_flow_final_solution",
    "objective_before_add",
    "objective_after_resolve",
    "objective_change_after_resolve",
    "written_to_baseline_dynamic_columns",
    "written_to_phase2_initial_pool",
    "written_to_fixed_source_outputs",
]
PHASE_II_CANDIDATE_FIELDS = [
    "round",
    "phase_ii_pricing_mode",
    "phase_ii_add_policy",
    "k_shortest_k",
    "max_phase_ii_candidates_per_demand",
    "max_phase_ii_candidates_per_round",
    "max_phase_ii_candidates_per_round_requested",
    "strict_phase_ii_candidate_round_cap",
    "demand_coverage_policy",
    "cap_truncation_status",
    "candidate_path_rank",
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
    "duplicate_generated_this_round",
    "duplicate_of_column_id",
    "oracle_generated",
    "diagnostic_only",
    "would_be_added_this_round",
    "would_be_added_in_future_task",
    "selected_by_add_policy",
    "add_policy_limited",
    "generation_cap_limited",
    "demand_pricing_attempted",
    "demand_cap_limited",
    "round_cap_limited",
    "blocker",
]
PHASE_II_DUPLICATE_FIELDS = [
    "round",
    "candidate_id",
    "demand_id",
    "classification",
    "duplicate_existing_phase2_column",
    "duplicate_generated_this_round",
    "duplicate_of_column_id",
    "arc_sequence",
    "duplicate_audit_status",
]


def rel(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT_DIR.resolve())).replace("\\", "/")
    except ValueError:
        return str(resolved).replace("\\", "/")


def resolve_path(value: str | Path | None) -> Path | None:
    if value is None or value == "":
        return None
    path = Path(value)
    return path if path.is_absolute() else ROOT_DIR / path


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def manifest_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y"}:
            return True
        if normalized in {"false", "0", "no", "n"}:
            return False
    return default


def finite(value: Any) -> float | None:
    number = parse_float(value, math.nan)
    return number if math.isfinite(number) else None


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = sorted({key for row in rows for key in row.keys()})
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def path_hash(path: Path) -> str:
    return sha256_file(path) if path.exists() and path.is_file() else ""


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"input manifest not found: {path}")
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError("input manifest must be a JSON object")
    return payload


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    for key in REQUIRED_MANIFEST_KEYS:
        if key not in manifest:
            blockers.append(f"manifest missing required key: {key}")
    if manifest.get("no_mutate") is not True:
        blockers.append("manifest must set no_mutate: true")
    if manifest.get("reference_comparison_policy") not in {
        "objective_level_when_reference_available",
        "skip_when_reference_absent",
    }:
        blockers.append("manifest reference_comparison_policy is unsupported")
    if manifest.get("stop_certificate_policy") != "always_write":
        blockers.append("manifest stop_certificate_policy must be always_write")
    if manifest.get("claim_boundary_policy") != "bounded_finite_fixture_only":
        blockers.append("manifest claim_boundary_policy must be bounded_finite_fixture_only")
    if manifest.get("phase_ii_pricing_mode", DEFAULT_PHASE_II_PRICING_MODE) not in PHASE_II_PRICING_MODES:
        blockers.append("manifest phase_ii_pricing_mode is unsupported")
    if manifest.get("phase_ii_add_policy", DEFAULT_PHASE_II_ADD_POLICY) not in PHASE_II_ADD_POLICIES:
        blockers.append("manifest phase_ii_add_policy is unsupported")
    for key in ["max_phase_i_rounds", "max_phase_ii_rounds", "max_candidates_per_demand_per_round", "runtime_cap_seconds"]:
        try:
            if int(manifest.get(key, -1)) < (1 if key in {"max_candidates_per_demand_per_round", "runtime_cap_seconds"} else 0):
                blockers.append(f"manifest {key} is below the allowed minimum")
        except (TypeError, ValueError):
            blockers.append(f"manifest {key} must be an integer")
    for key in ["k_shortest_k", "max_phase_ii_candidates_per_demand", "max_phase_ii_candidates_per_round"]:
        if key not in manifest:
            continue
        try:
            if int(manifest.get(key, -1)) < 1:
                blockers.append(f"manifest {key} is below the allowed minimum")
        except (TypeError, ValueError):
            blockers.append(f"manifest {key} must be an integer")
    if (
        "max_phase_ii_candidates_per_demand" in manifest
        and "max_candidates_per_demand_per_round" in manifest
    ):
        try:
            if int(manifest["max_phase_ii_candidates_per_demand"]) > int(manifest["max_candidates_per_demand_per_round"]):
                blockers.append("manifest max_phase_ii_candidates_per_demand exceeds max_candidates_per_demand_per_round")
        except (TypeError, ValueError):
            pass
    return blockers


def resolved_manifest(manifest: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    resolved = dict(manifest)
    requested_mode = args.phase_ii_pricing_mode or str(
        manifest.get("phase_ii_pricing_mode", DEFAULT_PHASE_II_PRICING_MODE)
    )
    requested_k = int(args.k_shortest_k) if args.k_shortest_k is not None else int(
        manifest.get("k_shortest_k", DEFAULT_K_SHORTEST_K)
    )
    if args.phase_ii_add_policy:
        requested_add_policy = args.phase_ii_add_policy
    elif manifest.get("phase_ii_add_policy"):
        requested_add_policy = str(manifest["phase_ii_add_policy"])
    elif requested_mode == PHASE_II_PRICING_MODE_K_SHORTEST:
        requested_add_policy = PHASE_II_ADD_BEST_ONE_PER_DEMAND
    else:
        requested_add_policy = DEFAULT_PHASE_II_ADD_POLICY
    resolved["benchmark_id"] = args.benchmark_id
    resolved["output_root"] = rel(resolve_path(args.output_dir) or ROOT_DIR / args.output_dir)
    resolved["max_phase_i_rounds"] = int(args.max_phase_i_rounds)
    resolved["max_phase_ii_rounds"] = int(args.max_phase_ii_rounds)
    resolved["max_candidates_per_demand_per_round"] = int(args.max_candidates_per_demand)
    resolved["phase_ii_pricing_mode"] = requested_mode
    resolved["k_shortest_k"] = requested_k
    resolved["phase_ii_add_policy"] = requested_add_policy
    resolved["max_phase_ii_candidates_per_demand"] = int(
        args.max_phase_ii_candidates_per_demand
        if args.max_phase_ii_candidates_per_demand is not None
        else manifest.get("max_phase_ii_candidates_per_demand", min(int(args.max_candidates_per_demand), max(1, requested_k)))
    )
    resolved["max_phase_ii_candidates_per_round"] = int(
        args.max_phase_ii_candidates_per_round
        if args.max_phase_ii_candidates_per_round is not None
        else manifest.get("max_phase_ii_candidates_per_round", int(args.max_candidates_per_demand))
    )
    resolved["strict_phase_ii_candidate_round_cap"] = bool(
        args.strict_phase_ii_candidate_round_cap
        or manifest_bool(manifest.get("strict_phase_ii_candidate_round_cap"), False)
    )
    resolved["runtime_cap_seconds"] = int(args.runtime_cap_seconds)
    resolved["no_mutate"] = bool(args.no_mutate_accepted_outputs)
    if args.reference_objective is not None:
        resolved["arc_lp_reference_objective"] = float(args.reference_objective)
    if args.reference_summary:
        resolved["arc_lp_reference_summary_path"] = args.reference_summary
    resolved["cli"] = {
        "input_manifest": rel(resolve_path(args.input_manifest) or Path(args.input_manifest)),
        "output_dir": resolved["output_root"],
        "benchmark_id": args.benchmark_id,
        "preflight_only": bool(args.preflight_only),
        "skip_phase_ii": bool(args.skip_phase_ii),
        "write_review_artifacts": bool(args.write_review_artifacts),
        "phase_ii_pricing_mode": requested_mode,
        "k_shortest_k": requested_k,
        "phase_ii_add_policy": requested_add_policy,
        "max_phase_ii_candidates_per_demand": resolved["max_phase_ii_candidates_per_demand"],
        "max_phase_ii_candidates_per_round": resolved["max_phase_ii_candidates_per_round"],
        "strict_phase_ii_candidate_round_cap": resolved["strict_phase_ii_candidate_round_cap"],
    }
    return resolved


def manifest_paths(manifest: dict[str, Any]) -> dict[str, Path]:
    dynamic_data_dir = resolve_path(manifest.get("dynamic_data_dir")) or ROOT_DIR
    return {
        "dynamic_data_dir": dynamic_data_dir,
        "demand_file": resolve_path(manifest.get("demand_file")) or dynamic_data_dir / "dynamic_demand.csv",
        "dynamic_arc_file": resolve_path(manifest.get("dynamic_arc_file")) or dynamic_data_dir / "dynamic_arc.csv",
        "current_candidate_pool_file": resolve_path(manifest.get("current_candidate_pool_file"))
        or dynamic_data_dir / "dynamic_columns.csv",
        "reference_summary": resolve_path(manifest.get("arc_lp_reference_summary_path")),
    }


def protected_paths(manifest: dict[str, Any]) -> list[Path]:
    paths = manifest_paths(manifest)
    protected = [
        paths["demand_file"],
        paths["dynamic_arc_file"],
        paths["current_candidate_pool_file"],
    ]
    dynamic_node = paths["dynamic_data_dir"] / "dynamic_node.csv"
    if dynamic_node.exists():
        protected.append(dynamic_node)
    baseline = paths["dynamic_data_dir"] / "dynamic_columns.csv"
    if baseline not in protected:
        protected.append(baseline)
    if paths["reference_summary"] is not None:
        protected.append(paths["reference_summary"])
    return [path for path in protected if path.exists()]


def hash_manifest(paths: list[Path], when: str) -> dict[str, Any]:
    return {
        "hash_audit_status": "PASS",
        "when": when,
        "artifacts": {rel(path): path_hash(path) for path in paths},
    }


def runtime_cap_reached(deadline: float | None) -> bool:
    return deadline is not None and time.monotonic() > deadline


def runtime_cap_blocker(manifest: dict[str, Any]) -> str:
    return f"runtime_cap_seconds exceeded: {manifest['runtime_cap_seconds']}"


def empty_phase2_outputs() -> dict[str, Any]:
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


def solution_status_ok(solve: dict[str, Any]) -> bool:
    status = str(solve.get("solver_info", {}).get("solver_status", "")).lower()
    return "optimal" in status and solve.get("validation", {}).get("validation_status") == "PASS"


def objective_from_solve(solve: dict[str, Any]) -> float | None:
    return finite(solve.get("solver_info", {}).get("objective_value"))


def phase2_ready_row(row: dict[str, str], role: str) -> dict[str, str]:
    ready = dict(row)
    ready["phase2_pool_column_type"] = ready.get("phase2_pool_column_type") or role
    ready["source_metadata"] = ready.get("source_metadata") or ready.get("column_source", "") or role
    ready["pool_membership"] = ready.get("pool_membership") or role
    ready["candidate_source"] = ready.get("candidate_source") or ready.get("source_metadata", "")
    ready["written_to_baseline_dynamic_columns"] = "false"
    ready["written_to_phase2_initial_pool"] = "false"
    ready["written_to_fixed_source_outputs"] = "false"
    ready["output_only_phase2_initial_pool"] = "false"
    ready["output_only_phase2_loop_pool"] = "false"
    ready["output_only_phase2_oracle_loop_pool"] = "true"
    return ready


def materialize_operational_pool(output_dir: Path, manifest: dict[str, Any], pool_rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], dict[str, Any]]:
    adapter = manifest.get("restricted_pool_adapter") or {}
    if not adapter.get("enabled"):
        return [phase2_ready_row(row, "manifest_current_pool") for row in pool_rows], {
            "restricted_pool_adapter_used": False,
            "operational_pool_path": rel(manifest_paths(manifest)["current_candidate_pool_file"]),
            "operational_pool_column_count": len(pool_rows),
            "honest_scope_label": "manifest_current_pool",
        }
    retained = set(adapter.get("retained_column_ids", []))
    restricted = [dict(row) for row in pool_rows if row.get("column_id") in retained]
    for row in restricted:
        row["column_source"] = str(adapter.get("label") or "full_cg_v1_restricted_pool_adapter")
        row["restricted_pool_adapter"] = "true"
        row["written_to_baseline_dynamic_columns"] = "false"
    path = output_dir / "full_cg_v1_restricted_current_pool.csv"
    write_csv(path, restricted)
    summary = {
        "restricted_pool_adapter_used": True,
        "restricted_pool_path": rel(path),
        "restricted_pool_column_count": len(restricted),
        "baseline_candidate_pool_count": len(pool_rows),
        "retained_column_ids": [row.get("column_id", "") for row in restricted],
        "honest_scope_label": adapter.get("honest_scope_label", "restricted-pool acceptance case"),
        "written_to_baseline_dynamic_columns": False,
    }
    write_json(output_dir / "full_cg_v1_restricted_pool_adapter_summary.json", summary)
    return [phase2_ready_row(row, "restricted_pool_phase_i_adapter") for row in restricted], summary


def solve_phase1_pool(
    arcs: list[dict[str, str]],
    demands: list[dict[str, str]],
    pool_rows: list[dict[str, str]],
    work_dir: Path,
    label: str,
) -> dict[str, Any]:
    model = build_phase1_model(arcs, demands, pool_rows)
    solver_info, result = solve_phase1_model(model)
    if result is None or solver_info.get("solver_status") != "optimal":
        summary = {
            "phase1_status": "SAFE_BLOCKED",
            "label": label,
            "solver_status": solver_info.get("solver_status"),
            "total_artificial_flow": None,
            "safe_blockers": [f"Phase-I solve failed for {label}: {solver_info.get('solver_status')}"],
        }
        write_json(work_dir / f"{label}_phase1_summary.json", summary)
        return summary

    values = [float(value) for value in result.x]
    outputs = build_phase1_solution_outputs(arcs, demands, pool_rows, values)
    dual_solution, raw_vectors = build_phase1_dual_solution(model, result, solver_info)
    trials = convention_trials(
        model,
        raw_vectors["values"],
        raw_vectors["eq_marginals"],
        raw_vectors["ub_marginals"],
        raw_vectors["lower_marginals"],
        raw_vectors["upper_marginals"],
    )
    selected = next((trial for trial in trials if trial["validation_passed"]), None)
    safe_blockers: list[str] = []
    if selected is None:
        safe_blockers.append("No validated Phase-I stationarity convention for Full CG v1 pool")
    else:
        dual_solution["validated_stationarity_convention"] = selected
    dual_solution["stationarity_convention_trials"] = [
        {key: value for key, value in trial.items() if key != "rows"} for trial in trials
    ]
    summary = {
        "phase1_status": "PASS" if not safe_blockers else "SAFE_BLOCKED",
        "label": label,
        "solver_status": solver_info.get("solver_status"),
        "objective_value_artificial_penalty_units": solver_info.get("objective_value"),
        "total_artificial_flow": outputs.get("total_artificial_flow"),
        "artificial_flow_by_demand": outputs.get("artificial_flow_by_demand", {}),
        "capacity_violation_count": outputs.get("capacity_violation_count"),
        "max_capacity_violation": outputs.get("max_capacity_violation"),
        "max_demand_residual": outputs.get("max_demand_residual"),
        "demand_constraints_satisfied_after_artificial": outputs.get("demand_constraints_satisfied"),
        "capacity_constraints_satisfied": outputs.get("capacity_constraints_satisfied"),
        "phase2_transition_allowed": outputs.get("phase2_transition_allowed"),
        "validated_stationarity_convention": selected["convention_name"] if selected else "",
        "safe_blockers": safe_blockers,
        "scope": SCOPE_BOUNDARY,
    }
    write_json(work_dir / f"{label}_phase1_summary.json", summary)
    write_json(work_dir / f"{label}_phase1_dual_solution.json", dual_solution)
    write_csv(work_dir / f"{label}_phase1_demand_balance.csv", outputs.get("demand_rows", []))
    write_csv(work_dir / f"{label}_phase1_capacity_usage.csv", outputs.get("capacity_rows", []))
    return {
        **summary,
        "_solution_outputs": outputs,
        "_dual_solution": dual_solution,
        "_arcs": arcs,
        "_demands": demands,
    }


def best_phase_i_candidate(score_rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    improving = [
        row
        for row in score_rows
        if row.get("classification") == "improving_new_candidate"
        and parse_float(row.get("phase1_entry_signal"), math.inf) < -TOL
    ]
    return min(improving, key=lambda row: parse_float(row.get("phase1_entry_signal"), math.inf), default=None)


def artificial_trace_row(
    index: int,
    round_number: int,
    added_count: int,
    candidate_id: str,
    solve: dict[str, Any],
) -> dict[str, Any]:
    outputs = solve.get("_solution_outputs", {})
    row = {
        "solution_index": index,
        "round": round_number,
        "added_candidate_count": added_count,
        "selected_candidate_added_to_reach_solution": candidate_id,
        "solver_status": solve.get("solver_status", ""),
        "total_artificial_flow": outputs.get("total_artificial_flow", solve.get("total_artificial_flow")),
        "capacity_violation_count": outputs.get("capacity_violation_count", solve.get("capacity_violation_count")),
        "max_capacity_violation": outputs.get("max_capacity_violation", solve.get("max_capacity_violation")),
        "demand_residual_max": outputs.get("max_demand_residual", solve.get("max_demand_residual")),
    }
    for demand_id, value in (outputs.get("artificial_flow_by_demand") or solve.get("artificial_flow_by_demand", {})).items():
        row[f"{demand_id}_artificial_flow"] = value
    return row


def run_phase_i(
    output_dir: Path,
    manifest: dict[str, Any],
    operational_pool: list[dict[str, str]],
    real_only_solve: dict[str, Any],
    deadline: float | None = None,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    paths = manifest_paths(manifest)
    data_dir = paths["dynamic_data_dir"]
    arcs = read_csv_rows(paths["dynamic_arc_file"])
    demands = read_csv_rows(paths["demand_file"])
    work_dir = output_dir / "phase_i_work"
    work_dir.mkdir(parents=True, exist_ok=True)
    max_rounds = int(manifest["max_phase_i_rounds"])
    max_candidates = int(manifest["max_candidates_per_demand_per_round"])
    safe_blockers: list[str] = []
    selected_rows: list[dict[str, Any]] = []
    candidate_log_rows: list[dict[str, Any]] = []
    trace_rows: list[dict[str, Any]] = []
    pool = [dict(row) for row in operational_pool]

    if solution_status_ok(real_only_solve):
        trace_rows.append(
            {
                "solution_index": 0,
                "round": 0,
                "added_candidate_count": 0,
                "selected_candidate_added_to_reach_solution": "",
                "solver_status": real_only_solve["solver_info"].get("solver_status"),
                "total_artificial_flow": 0.0,
                "capacity_violation_count": real_only_solve["solution_outputs"].get("capacity_violation_count"),
                "max_capacity_violation": real_only_solve["solution_outputs"].get("max_capacity_violation"),
                "demand_residual_max": real_only_solve["solution_outputs"].get("demand_residual_max"),
            }
        )
        final_pool_path = output_dir / "full_cg_v1_phase_i_final_real_pool.csv"
        write_csv(final_pool_path, pool_output_rows(pool))
        summary = {
            "phase_i_status": "PASS",
            "phase_i_needed": False,
            "phase_i_loop_ran": False,
            "phase_i_artificial_flow_initial": 0.0,
            "phase_i_artificial_flow_final": 0.0,
            "artificial_flow_cleared": True,
            "max_phase_i_rounds": int(manifest["max_phase_i_rounds"]),
            "rounds_attempted": 0,
            "candidates_added": 0,
            "stop_reason": "real_only_current_pool_feasible",
            "phase_i_final_pool": rel(final_pool_path),
            "phase_i_final_pool_column_count": len(pool),
            "demand_residual_max_final": real_only_solve["solution_outputs"].get("demand_residual_max"),
            "capacity_violation_count_final": real_only_solve["solution_outputs"].get("capacity_violation_count"),
            "safe_blockers": [],
            "repaired_seed_columns_used_operationally": False,
            "repair_specs_used_operationally": False,
            "link55_d3_d4_success_hardcoding": False,
        }
        write_phase_i_outputs(output_dir, summary, trace_rows, selected_rows, candidate_log_rows)
        return summary, pool

    current = solve_phase1_pool(arcs, demands, pool, work_dir, "round_000_initial")
    trace_rows.append(artificial_trace_row(0, 0, 0, "", current))
    initial_total = finite(current.get("total_artificial_flow"))
    solution_outputs = current.get("_solution_outputs", {})
    stop_reason = ""
    if current.get("phase1_status") != "PASS":
        safe_blockers.extend(current.get("safe_blockers", []))
        stop_reason = "safe_blocker"

    for round_number in range(1, max_rounds + 1):
        before_total = finite(solution_outputs.get("total_artificial_flow"))
        if stop_reason:
            break
        if runtime_cap_reached(deadline):
            stop_reason = "runtime_cap_exceeded"
            safe_blockers.append(runtime_cap_blocker(manifest))
            break
        if before_total is not None and before_total <= TOL:
            stop_reason = "artificial_flow_zero_initial_or_previous_round"
            break
        dual_solution = current.get("_dual_solution", {})
        convention_name, eq_sign, cap_sign, sign_blockers = validated_signs(dual_solution)
        if sign_blockers:
            safe_blockers.extend(sign_blockers)
            stop_reason = "safe_blocker"
            break

        pool_path = work_dir / f"round_{round_number:03d}_current_pool.csv"
        write_csv(pool_path, pool_output_rows(pool))
        dual_path = work_dir / f"round_{round_number - 1:03d}_phase1_dual_solution.json"
        summary_path = work_dir / f"round_{round_number - 1:03d}_phase1_summary_for_oracle.json"
        write_json(dual_path, dual_solution)
        write_json(summary_path, {key: value for key, value in current.items() if not key.startswith("_")})
        oracle_dir = work_dir / f"round_{round_number:03d}_oracle"
        run_phase_i_oracle(
            output_dir=oracle_dir,
            benchmark_id=str(manifest["benchmark_id"]),
            phase1_dual_solution=dual_path,
            candidate_pool=pool_path,
            max_candidates_per_demand=max_candidates,
            dynamic_data_dir=data_dir,
            dynamic_arc_file=paths["dynamic_arc_file"],
            dynamic_demand_file=paths["demand_file"],
            phase1_preflight_summary=summary_path,
            baseline_dynamic_columns=paths["current_candidate_pool_file"],
            bounded_reference_candidates=None,
            require_improving_candidate=False,
            oracle_id=ORACLE_ID_PHASE_I,
        )
        scores = read_csv_rows(oracle_dir / "phase_i_general_oracle_candidate_scores.csv")
        candidates = read_csv_rows(oracle_dir / "phase_i_general_oracle_candidates.csv")
        for row in scores:
            log_row = dict(row)
            log_row["round"] = round_number
            candidate_log_rows.append(log_row)
        best = best_phase_i_candidate(scores)
        round_row = {
            "round": round_number,
            "pool_column_count_before": len(pool),
            "total_artificial_flow_before": before_total,
            "generated_candidates": len(candidates),
            "improving_nonduplicate_candidate_count": sum(
                row.get("classification") == "improving_new_candidate" for row in scores
            ),
            "selected_candidate_id": best.get("candidate_id", "") if best else "",
            "candidate_added": bool_text(best is not None),
        }
        if best is None:
            stop_reason = "no_improving_nonduplicate_phase_i_candidate"
            selected_rows.append({**round_row, "stop_reason_if_stopped": stop_reason})
            break
        source = next((row for row in candidates if row.get("column_id") == best.get("candidate_id")), None)
        if source is None:
            safe_blockers.append(f"selected Phase-I candidate missing from source: {best.get('candidate_id')}")
            stop_reason = "safe_blocker"
            selected_rows.append({**round_row, "stop_reason_if_stopped": stop_reason})
            break
        original_candidate_id = str(source.get("column_id", ""))
        in_run_candidate_id = f"PHASEI_R{round_number}_{original_candidate_id}"
        added = phase2_ready_row(dict(source), "phase_i_oracle_handoff_candidate")
        added["column_id"] = in_run_candidate_id
        added["path_id"] = f"PHASEI_R{round_number}_{source.get('path_id', original_candidate_id)}"
        added["column_source"] = ORACLE_ID_PHASE_I
        added["candidate_source"] = rel(oracle_dir / "phase_i_general_oracle_candidates.csv")
        added["added_in_phase_i_round"] = str(round_number)
        added["original_phase_i_oracle_candidate_id"] = original_candidate_id
        added["pool_membership"] = "full_cg_v1_phase_i_added_candidate"
        pool.append(added)
        current = solve_phase1_pool(arcs, demands, pool, work_dir, f"round_{round_number:03d}_after_add")
        solution_outputs = current.get("_solution_outputs", {})
        after_total = finite(solution_outputs.get("total_artificial_flow"))
        selected_rows.append(
            {
                **round_row,
                "pool_column_count_after": len(pool),
                "total_artificial_flow_after": after_total,
                "capacity_violation_count_after": solution_outputs.get("capacity_violation_count"),
                "demand_residual_max_after": solution_outputs.get("max_demand_residual"),
                "selected_candidate_id": in_run_candidate_id,
                "original_phase_i_oracle_candidate_id": original_candidate_id,
                "selected_candidate_demand": best.get("demand_id", ""),
                "selected_candidate_entry_signal": best.get("phase1_entry_signal", ""),
                "arc_sequence": best.get("arc_sequence", ""),
                "written_to_baseline_dynamic_columns": "false",
                "stop_reason_if_stopped": "artificial_flow_zero" if after_total is not None and after_total <= TOL else "",
            }
        )
        trace_rows.append(artificial_trace_row(len(trace_rows), round_number, len(selected_rows), in_run_candidate_id, current))
        if current.get("phase1_status") != "PASS":
            safe_blockers.extend(current.get("safe_blockers", []))
            stop_reason = "safe_blocker"
            break
        if runtime_cap_reached(deadline):
            stop_reason = "runtime_cap_exceeded"
            safe_blockers.append(runtime_cap_blocker(manifest))
            break
        if after_total is not None and after_total <= TOL:
            stop_reason = "artificial_flow_zero"
            break

    if not stop_reason:
        stop_reason = "max_phase_i_rounds_reached"
    final_total = finite(solution_outputs.get("total_artificial_flow"))
    artificial_cleared = final_total is not None and final_total <= TOL
    final_pool_path = output_dir / "full_cg_v1_phase_i_final_real_pool.csv"
    write_csv(final_pool_path, pool_output_rows(pool))
    summary = {
        "phase_i_status": "PASS" if artificial_cleared and not safe_blockers else "PHASE_I_BLOCKED",
        "phase_i_needed": True,
        "phase_i_loop_ran": True,
        "phase_i_artificial_flow_initial": initial_total,
        "phase_i_artificial_flow_final": final_total,
        "artificial_flow_cleared": artificial_cleared,
        "max_phase_i_rounds": max_rounds,
        "rounds_attempted": len([row for row in selected_rows if row.get("candidate_added")]),
        "candidates_generated": len(candidate_log_rows),
        "candidates_added": sum(row.get("candidate_added") == "true" for row in selected_rows),
        "stop_reason": stop_reason,
        "phase_i_final_pool": rel(final_pool_path),
        "phase_i_final_pool_column_count": len(pool),
        "demand_residual_max_final": solution_outputs.get("max_demand_residual"),
        "capacity_violation_count_final": solution_outputs.get("capacity_violation_count"),
        "max_capacity_violation_final": solution_outputs.get("max_capacity_violation"),
        "safe_blockers": safe_blockers,
        "repaired_seed_columns_used_operationally": False,
        "repair_specs_used_operationally": False,
        "link55_d3_d4_success_hardcoding": False,
    }
    write_phase_i_outputs(output_dir, summary, trace_rows, selected_rows, candidate_log_rows)
    return summary, pool


def write_phase_i_outputs(
    output_dir: Path,
    summary: dict[str, Any],
    trace_rows: list[dict[str, Any]],
    selected_rows: list[dict[str, Any]],
    candidate_log_rows: list[dict[str, Any]],
) -> None:
    write_json(output_dir / "full_cg_v1_phase_i_summary.json", summary)
    write_csv(output_dir / "full_cg_v1_phase_i_artificial_flow_trace.csv", trace_rows, PHASE_I_TRACE_FIELDS if not trace_rows else None)
    write_csv(output_dir / "full_cg_v1_phase_i_selected_columns.csv", selected_rows, PHASE_I_SELECTED_FIELDS if not selected_rows else None)
    write_csv(output_dir / "full_cg_v1_phase_i_candidate_log.csv", candidate_log_rows, PHASE_I_CANDIDATE_FIELDS if not candidate_log_rows else None)
    stop_certificate = {
        "stop_certificate_status": "PASS" if summary.get("phase_i_status") == "PASS" else summary.get("phase_i_status"),
        "stop_reason": summary.get("stop_reason"),
        "artificial_flow_cleared": summary.get("artificial_flow_cleared"),
        "bounded_round_cap": summary.get("max_phase_i_rounds"),
        "rounds_attempted": summary.get("rounds_attempted"),
        "candidates_added": summary.get("candidates_added"),
        "safe_blockers": summary.get("safe_blockers", []),
        "optimality_claimed": False,
    }
    write_json(output_dir / "full_cg_v1_phase_i_stop_certificate.json", stop_certificate)


def write_phase2_solution_outputs(output_dir: Path, prefix: str, solve: dict[str, Any]) -> None:
    outputs = solve.get("solution_outputs", empty_phase2_outputs())
    solution_rows = outputs.get("solution_by_column", [])
    capacity_rows = outputs.get("capacity_usage", [])
    demand_rows = outputs.get("demand_balance", [])
    write_csv(output_dir / f"{prefix}_solution_by_column.csv", solution_rows, PHASE_II_SOLUTION_FIELDS if not solution_rows else None)
    write_json(output_dir / f"{prefix}_dual_solution.json", solve.get("dual_solution", {}))
    write_csv(output_dir / f"{prefix}_capacity_audit.csv", capacity_rows, PHASE_II_AUDIT_FIELDS if not capacity_rows else None)
    write_csv(output_dir / f"{prefix}_demand_residual_audit.csv", demand_rows, PHASE_II_AUDIT_FIELDS if not demand_rows else None)


def _canonical_signature(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def model_signature_for_manifest(manifest: dict[str, Any]) -> str:
    declared = str(manifest.get("model_signature", "")).strip()
    if declared:
        return declared
    paths = manifest_paths(manifest)
    dynamic_dir = paths["dynamic_data_dir"]
    source_files = [
        dynamic_dir / "dynamic_node.csv",
        paths["dynamic_arc_file"],
        paths["demand_file"],
    ]
    identity = {
        "network_mode": manifest.get("network_mode", "legacy_route_union"),
        "files": [
            {"name": path.name, "bytes": path.stat().st_size, "sha256": sha256_file(path)}
            for path in source_files
        ],
    }
    return _canonical_signature(identity)


def write_final_phase2_solution_outputs(
    output_dir: Path,
    manifest: dict[str, Any],
    pool: list[dict[str, str]],
    solve: dict[str, Any],
    objective_trace: list[dict[str, Any]],
) -> dict[str, Any]:
    """Export the exact last successfully solved Phase-II RMP and its duals."""
    solution_rows = solve.get("solution_outputs", {}).get("solution_by_column", [])
    dual = dict(solve.get("dual_solution", {}))
    pool_ids = [str(row.get("column_id", "")) for row in pool]
    solution_ids = [str(row.get("column_id", "")) for row in solution_rows]
    lower = dual.get("lower_bound_marginals", {})
    upper = dual.get("upper_bound_marginals", {})
    last_trace = objective_trace[-1] if objective_trace else {}
    model_id = str(manifest.get("benchmark_id", ""))
    model_signature = model_signature_for_manifest(manifest)
    pool_signature = _canonical_signature(pool)
    pool_id = f"sha256:{pool_signature}"
    blockers: list[str] = []
    if not solution_status_ok(solve):
        blockers.append("last solve is not a validated successful Phase-II RMP")
    if len(pool_ids) != len(set(pool_ids)):
        blockers.append("last successfully solved pool has duplicate column_id values")
    if pool_ids != solution_ids:
        blockers.append("solution rows do not exactly match the last successfully solved pool in order")
    if set(lower) != set(pool_ids) or set(upper) != set(pool_ids):
        blockers.append("variable bound marginal keys do not exactly match the solved pool")
    if not dual.get("dual_fields_present") or not dual.get("dual_fields_finite"):
        blockers.append("final dual or bound-marginal fields are missing/nonfinite")
    export_rows = []
    for row in solution_rows:
        column_id = str(row.get("column_id", ""))
        export_rows.append(
            {
                "model_id": model_id,
                "model_signature": model_signature,
                "pool_id": pool_id,
                "pool_signature": pool_signature,
                "solve_iteration": last_trace.get("solution_index"),
                "phase_ii_round": last_trace.get("round"),
                **row,
                "lower_bound_marginal": lower.get(column_id),
                "upper_bound_marginal": upper.get(column_id),
            }
        )
    status = "PASS" if not blockers else "FULL_SOLUTION_EXPORT_BLOCKED"
    solution_path = output_dir / "full_cg_v1_phase_ii_final_solution_by_column.csv"
    dual_path = output_dir / "full_cg_v1_phase_ii_final_dual_solution.json"
    stationarity_path = output_dir / "full_cg_v1_phase_ii_final_stationarity.csv"
    metadata_path = output_dir / "full_cg_v1_phase_ii_final_solution_metadata.json"
    write_csv(solution_path, export_rows, FINAL_PHASE_II_SOLUTION_FIELDS)
    dual.update(
        {
            "export_status": status,
            "model_id": model_id,
            "model_signature": model_signature,
            "pool_id": pool_id,
            "pool_signature": pool_signature,
            "solve_iteration": last_trace.get("solution_index"),
            "phase_ii_round": last_trace.get("round"),
            "pool_column_ids": pool_ids,
            "stationarity_validation": solve.get("validation", {}),
        }
    )
    write_json(dual_path, dual)
    write_csv(stationarity_path, solve.get("stationarity_rows", []))
    metadata = {
        "export_status": status,
        "blockers": blockers,
        "model_id": model_id,
        "model_signature": model_signature,
        "pool_id": pool_id,
        "pool_signature": pool_signature,
        "last_successfully_solved_pool_column_count": len(pool_ids),
        "exported_solution_row_count": len(export_rows),
        "zero_flow_column_count": sum(parse_float(row.get("flow"), 0.0) <= TOL for row in export_rows),
        "positive_flow_column_count": sum(parse_float(row.get("flow"), 0.0) > TOL for row in export_rows),
        "solve_iteration": last_trace.get("solution_index"),
        "phase_ii_round": last_trace.get("round"),
        "solver_status": solve.get("solver_info", {}).get("solver_status"),
        "solution_path": rel(solution_path),
        "dual_path": rel(dual_path),
        "stationarity_path": rel(stationarity_path),
        "solution_is_exact_last_successful_rmp": not blockers,
        "unsolved_candidate_rows_defaulted_to_zero": False,
    }
    write_json(metadata_path, metadata)
    return metadata


def run_phase_ii_initialization(
    output_dir: Path,
    manifest: dict[str, Any],
    phase_i_pool: list[dict[str, str]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    paths = manifest_paths(manifest)
    arcs = read_csv_rows(paths["dynamic_arc_file"])
    demands = read_csv_rows(paths["demand_file"])
    solve = solve_current_pool(arcs, demands, phase_i_pool)
    outputs = solve.get("solution_outputs", empty_phase2_outputs())
    objective = objective_from_solve(solve)
    ref_obj = finite(manifest.get("arc_lp_reference_objective"))
    gap = objective - ref_obj if objective is not None and ref_obj is not None else None
    summary = {
        "phase_ii_initialization_status": "PASS" if solution_status_ok(solve) else "PHASE_II_INITIALIZATION_BLOCKED",
        "benchmark_id": manifest["benchmark_id"],
        "phase_i_handoff_pool_column_count": len(phase_i_pool),
        "rmp_solver_status": solve.get("solver_info", {}).get("solver_status"),
        "rmp_feasible_optimal": solution_status_ok(solve),
        "rmp_objective": objective,
        "arc_lp_reference_available": ref_obj is not None,
        "arc_lp_reference_objective": ref_obj,
        "objective_gap_vs_reference": gap,
        "objective_gap_reported": ref_obj is not None,
        "optimality_claimed": False,
        "demand_residual_max": outputs.get("demand_residual_max"),
        "capacity_violation_count": outputs.get("capacity_violation_count"),
        "max_capacity_violation": outputs.get("max_capacity_violation"),
        "dual_validation_status": solve.get("validation", {}).get("validation_status"),
        "validated_dual_convention": solve.get("validation", {}).get("validated_convention"),
        "dual_convention_validated_in_run": solve.get("validation", {}).get("validation_status") == "PASS",
        "safe_blocker": solve.get("safe_blocker", ""),
        "repaired_seed_columns_used_operationally": False,
        "repair_specs_used_operationally": False,
        "link55_d3_d4_success_hardcoding": False,
    }
    write_json(output_dir / "full_cg_v1_phase_ii_initialization_summary.json", summary)
    write_phase2_solution_outputs(output_dir, "full_cg_v1_phase_ii_initial", solve)
    return summary, solve


def phase_ii_pricing_config(manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    manifest = manifest or {}
    historical_cap = int(manifest.get("max_candidates_per_demand_per_round", 1) or 1)
    mode = str(manifest.get("phase_ii_pricing_mode", DEFAULT_PHASE_II_PRICING_MODE))
    k_value = int(manifest.get("k_shortest_k", DEFAULT_K_SHORTEST_K) or DEFAULT_K_SHORTEST_K)
    effective_round_cap = max(
        1, int(manifest.get("max_phase_ii_candidates_per_round", historical_cap) or historical_cap)
    )
    requested_round_cap = max(
        1,
        int(
            manifest.get(
                "max_phase_ii_candidates_per_round_requested",
                manifest.get("max_phase_ii_candidates_per_round", historical_cap),
            )
            or historical_cap
        ),
    )
    return {
        "phase_ii_pricing_mode": mode,
        "k_shortest_k": max(1, k_value),
        "phase_ii_add_policy": str(manifest.get("phase_ii_add_policy", DEFAULT_PHASE_II_ADD_POLICY)),
        "max_phase_ii_candidates_per_demand": max(
            1, int(manifest.get("max_phase_ii_candidates_per_demand", historical_cap) or historical_cap)
        ),
        "max_phase_ii_candidates_per_round": effective_round_cap,
        "max_phase_ii_candidates_per_round_requested": requested_round_cap,
        "strict_phase_ii_candidate_round_cap": manifest_bool(
            manifest.get("strict_phase_ii_candidate_round_cap"), False
        ),
        "demand_coverage_policy": str(
            manifest.get(
                "demand_coverage_policy",
                PHASE_II_COVERAGE_K_SHORTEST_FAIR
                if mode == PHASE_II_PRICING_MODE_K_SHORTEST
                else PHASE_II_COVERAGE_ONE_PROBE,
            )
        ),
        "cap_auto_expanded_for_demand_coverage": False,
    }


def demand_fair_phase_ii_pricing_config(config: dict[str, Any], demand_count: int) -> dict[str, Any]:
    adjusted = dict(config)
    adjusted["max_phase_ii_candidates_per_round_requested"] = int(
        adjusted.get("max_phase_ii_candidates_per_round_requested", adjusted["max_phase_ii_candidates_per_round"])
    )
    if adjusted["phase_ii_pricing_mode"] != PHASE_II_PRICING_MODE_K_SHORTEST:
        adjusted["cap_auto_expanded_for_demand_coverage"] = False
        return adjusted
    fair_candidate_count = max(
        1,
        int(demand_count)
        * min(int(adjusted["k_shortest_k"]), int(adjusted["max_phase_ii_candidates_per_demand"])),
    )
    if (
        not manifest_bool(adjusted.get("strict_phase_ii_candidate_round_cap"), False)
        and int(adjusted["max_phase_ii_candidates_per_round"]) < fair_candidate_count
    ):
        adjusted["max_phase_ii_candidates_per_round"] = fair_candidate_count
        adjusted["cap_auto_expanded_for_demand_coverage"] = True
    else:
        adjusted["cap_auto_expanded_for_demand_coverage"] = False
    adjusted["demand_coverage_policy"] = PHASE_II_COVERAGE_K_SHORTEST_FAIR
    return adjusted


def phase_ii_arc_weight(arc: dict[str, str], dual_solution: dict[str, Any], capacity_sign: float) -> float:
    cost = parse_float(arc.get("cost"), math.inf)
    if not math.isfinite(cost):
        return math.inf
    capacity_duals = dual_solution.get("capacity_inequality_duals", {})
    cap_dual = parse_float(capacity_duals.get(arc.get("arc_id", ""), {}).get("marginal"), 0.0)
    return cost + capacity_sign * cap_dual


def phase_ii_path_weight(
    path_arcs: list[str],
    arc_by_id: dict[str, dict[str, str]],
    dual_solution: dict[str, Any],
    capacity_sign: float,
) -> float:
    total = 0.0
    for arc_id in path_arcs:
        weight = phase_ii_arc_weight(arc_by_id.get(arc_id, {}), dual_solution, capacity_sign)
        if not math.isfinite(weight):
            return math.inf
        total += weight
    return total


def path_nodes_from_arcs(
    start_node: str,
    path_arcs: list[str],
    arc_by_id: dict[str, dict[str, str]],
) -> list[str]:
    nodes = [start_node]
    current = start_node
    for arc_id in path_arcs:
        arc = arc_by_id.get(arc_id)
        if arc is None:
            return []
        if arc.get("from_node_time_id", "") != current:
            return []
        current = arc.get("to_node_time_id", "")
        if not current:
            return []
        nodes.append(current)
    return nodes


def validate_phase_ii_candidate_path(
    demand_id: str,
    start_node: str,
    target_nodes: set[str],
    path_arcs: list[str],
    arc_by_id: dict[str, dict[str, str]],
) -> tuple[bool, str, str]:
    nodes = path_nodes_from_arcs(start_node, path_arcs, arc_by_id)
    if not nodes or len(nodes) != len(path_arcs) + 1:
        return False, "candidate path arc chain is invalid", ""
    for arc_id in path_arcs:
        arc = arc_by_id.get(arc_id, {})
        arc_type = arc.get("arc_type", "")
        if arc_type == "source_connector" and arc_id != f"source_{demand_id}":
            return False, "candidate uses source connector for another demand", nodes[-1]
        if arc_type == "sink_connector":
            parts = arc_id.split("_")
            if len(parts) >= 2 and parts[1] != demand_id:
                return False, "candidate uses sink connector for another demand", nodes[-1]
    if nodes[-1] not in target_nodes:
        return False, "candidate path does not terminate at a demand sink target", nodes[-1]
    return True, "", nodes[-1]


def shortest_path_bellman_ford_filtered(
    arcs: list[dict[str, str]],
    start_node: str,
    target_nodes: set[str],
    dual_solution: dict[str, Any],
    capacity_sign: float,
    banned_arc_ids: set[str] | None = None,
    banned_nodes: set[str] | None = None,
) -> tuple[float, list[str], str | None, str]:
    banned_arc_ids = banned_arc_ids or set()
    banned_nodes = banned_nodes or set()
    if start_node in banned_nodes:
        return math.inf, [], None, "spur start node is banned"
    targets = {node for node in target_nodes if node not in banned_nodes}
    if not targets:
        return math.inf, [], None, "all target nodes are banned"

    nodes: set[str] = {start_node}
    edge_rows: list[tuple[str, str, str, float]] = []
    for arc in arcs:
        arc_id = arc.get("arc_id", "")
        from_node = arc.get("from_node_time_id", "")
        to_node = arc.get("to_node_time_id", "")
        if not arc_id or arc_id in banned_arc_ids:
            continue
        if not from_node or not to_node or from_node in banned_nodes or to_node in banned_nodes:
            continue
        weight = phase_ii_arc_weight(arc, dual_solution, capacity_sign)
        if not math.isfinite(weight):
            continue
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

    best_target = min(targets, key=lambda node: (distance.get(node, math.inf), node), default=None)
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


def k_shortest_phase_ii_paths(
    arcs: list[dict[str, str]],
    start_node: str,
    target_nodes: set[str],
    dual_solution: dict[str, Any],
    capacity_sign: float,
    k_value: int,
) -> tuple[list[dict[str, Any]], str]:
    arc_by_id = {arc.get("arc_id", ""): arc for arc in arcs}
    first_weight, first_path, first_target, blocker = shortest_path_bellman_ford_filtered(
        arcs,
        start_node,
        target_nodes,
        dual_solution,
        capacity_sign,
    )
    if blocker or not first_path:
        return [], blocker or "shortest path could not be found"

    accepted: list[tuple[float, list[str], str | None]] = [(first_weight, first_path, first_target)]
    heap: list[tuple[float, int, list[str], str | None]] = []
    seen_paths: set[tuple[str, ...]] = {tuple(first_path)}
    sequence = 0
    while len(accepted) < max(1, k_value):
        previous_path = accepted[-1][1]
        previous_nodes = path_nodes_from_arcs(start_node, previous_path, arc_by_id)
        if not previous_nodes:
            break
        for spur_index in range(len(previous_path)):
            spur_node = previous_nodes[spur_index]
            root_path = previous_path[:spur_index]
            root_nodes = previous_nodes[: spur_index + 1]
            banned_edges: set[str] = set()
            for _weight, accepted_path, _target in accepted:
                if len(accepted_path) > spur_index and accepted_path[:spur_index] == root_path:
                    banned_edges.add(accepted_path[spur_index])
            banned_nodes = set(root_nodes[:-1])
            _spur_weight, spur_path, spur_target, spur_blocker = shortest_path_bellman_ford_filtered(
                arcs,
                spur_node,
                target_nodes,
                dual_solution,
                capacity_sign,
                banned_edges,
                banned_nodes,
            )
            if spur_blocker or not spur_path:
                continue
            total_path = root_path + spur_path
            path_key = tuple(total_path)
            if path_key in seen_paths:
                continue
            path_weight = phase_ii_path_weight(total_path, arc_by_id, dual_solution, capacity_sign)
            if not math.isfinite(path_weight):
                continue
            seen_paths.add(path_key)
            sequence += 1
            heapq.heappush(heap, (path_weight, sequence, total_path, spur_target))
        if not heap:
            break
        next_weight, _sequence, next_path, next_target = heapq.heappop(heap)
        accepted.append((next_weight, next_path, next_target))

    rows = [
        {"path_weight": weight, "path_arcs": path_arcs, "target_node": target_node, "candidate_path_rank": index}
        for index, (weight, path_arcs, target_node) in enumerate(accepted[: max(1, k_value)], start=1)
    ]
    return rows, ""


def phase_ii_probe_row_from_path(
    demand_id: str,
    candidate_id: str,
    round_number: int,
    start_node: str,
    target_nodes: set[str],
    path_arcs: list[str],
    target_node: str | None,
    candidate_path_rank: int,
    arcs: list[dict[str, str]],
    arc_by_id: dict[str, dict[str, str]],
    current_pool: list[dict[str, str]],
    dual_solution: dict[str, Any],
    convention: dict[str, Any],
    config: dict[str, Any],
    generated_this_round: dict[tuple[str, str], str],
) -> dict[str, Any]:
    reconstructed, missing, nonfinite = reconstruct_path_cost(
        {"arc_sequence": "|".join(path_arcs), "demand_id": demand_id},
        arc_by_id,
    )
    cap_sum = raw_capacity_dual_sum(path_arcs, dual_solution)
    eq_dual = demand_dual(demand_id, dual_solution)
    entry_signal = reconstructed + convention["eq_sign"] * eq_dual + convention["capacity_sign"] * cap_sum
    classification, duplicate_of, structurally_valid = classify_oracle_candidate(
        demand_id,
        path_arcs,
        entry_signal,
        current_pool,
    )
    valid_path, path_invalid_reason, validated_target = validate_phase_ii_candidate_path(
        demand_id,
        start_node,
        target_nodes,
        path_arcs,
        arc_by_id,
    )
    if missing or nonfinite or not valid_path:
        classification = "invalid_oracle_candidate"
        structurally_valid = False
    path_key = (demand_id, "|".join(path_arcs))
    duplicate_generated = False
    if classification != "duplicate_existing_phase2_column":
        earlier_candidate_id = generated_this_round.get(path_key)
        if earlier_candidate_id:
            classification = "duplicate_generated_this_round"
            duplicate_of = earlier_candidate_id
            duplicate_generated = True
            structurally_valid = True
        else:
            generated_this_round[path_key] = candidate_id
    return {
        "round": round_number,
        "phase_ii_pricing_mode": config["phase_ii_pricing_mode"],
        "phase_ii_add_policy": config["phase_ii_add_policy"],
        "k_shortest_k": config["k_shortest_k"],
        "max_phase_ii_candidates_per_demand": config["max_phase_ii_candidates_per_demand"],
        "max_phase_ii_candidates_per_round": config["max_phase_ii_candidates_per_round"],
        "max_phase_ii_candidates_per_round_requested": config.get(
            "max_phase_ii_candidates_per_round_requested", config["max_phase_ii_candidates_per_round"]
        ),
        "strict_phase_ii_candidate_round_cap": bool_text(
            manifest_bool(config.get("strict_phase_ii_candidate_round_cap"), False)
        ),
        "demand_coverage_policy": config.get("demand_coverage_policy", ""),
        "cap_truncation_status": config.get("cap_truncation_status", PHASE_II_CAP_NOT_TRUNCATED),
        "candidate_path_rank": candidate_path_rank,
        "candidate_id": candidate_id,
        "demand_id": demand_id,
        "probe_status": "PASS" if structurally_valid else "SAFE_BLOCKED",
        "start_node": start_node,
        "target_node": target_node or validated_target or "",
        "arc_sequence": "|".join(path_arcs),
        "structurally_valid": bool_text(structurally_valid),
        "invalid_reason": "|".join(missing + nonfinite + ([path_invalid_reason] if path_invalid_reason else [])),
        "reconstructed_generalized_cost": reconstructed,
        "capacity_dual_sum_raw": cap_sum,
        "demand_equality_dual_raw": eq_dual,
        "validated_stationarity_convention": convention.get("validated_convention"),
        "validated_eq_sign": convention.get("eq_sign"),
        "validated_capacity_sign": convention.get("capacity_sign"),
        "oracle_entry_signal": entry_signal,
        "classification": classification,
        "duplicate_existing_phase2_column": bool_text(classification == "duplicate_existing_phase2_column"),
        "duplicate_generated_this_round": bool_text(duplicate_generated),
        "duplicate_of_column_id": duplicate_of,
        "oracle_generated": "true",
        "diagnostic_only": "false",
        "would_be_added_this_round": "false",
        "would_be_added_in_future_task": "false",
        "selected_by_add_policy": "false",
        "add_policy_limited": "false",
        "generation_cap_limited": "false",
        "demand_pricing_attempted": "true",
        "demand_cap_limited": "false",
        "round_cap_limited": "false",
        "blocker": "",
    }


def run_phase_ii_oracle_probes(
    arcs: list[dict[str, str]],
    demands: list[dict[str, str]],
    current_pool: list[dict[str, str]],
    dual_solution: dict[str, Any],
    convention: dict[str, Any],
    round_number: int,
    pricing_config: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    config = phase_ii_pricing_config(pricing_config)
    arc_by_id = {arc.get("arc_id", ""): arc for arc in arcs}
    source_connectors, sink_targets = source_sink_maps(arcs)
    rows: list[dict[str, Any]] = []
    generated_this_round: dict[tuple[str, str], str] = {}
    round_limit = config["max_phase_ii_candidates_per_round"]
    generated_count = 0

    def blocked_row(
        demand_id: str,
        candidate_id: str,
        candidate_path_rank: int,
        blocker: str,
        *,
        start_node: str = "",
        target_node: str = "",
        classification: str = "invalid_oracle_candidate",
        cap_limited: bool = False,
    ) -> dict[str, Any]:
        return {
            "round": round_number,
            "phase_ii_pricing_mode": config["phase_ii_pricing_mode"],
            "phase_ii_add_policy": config["phase_ii_add_policy"],
            "k_shortest_k": config["k_shortest_k"],
            "max_phase_ii_candidates_per_demand": config["max_phase_ii_candidates_per_demand"],
            "max_phase_ii_candidates_per_round": config["max_phase_ii_candidates_per_round"],
            "max_phase_ii_candidates_per_round_requested": config.get(
                "max_phase_ii_candidates_per_round_requested", config["max_phase_ii_candidates_per_round"]
            ),
            "strict_phase_ii_candidate_round_cap": bool_text(
                manifest_bool(config.get("strict_phase_ii_candidate_round_cap"), False)
            ),
            "demand_coverage_policy": config.get("demand_coverage_policy", ""),
            "cap_truncation_status": PHASE_II_CAP_TRUNCATED if cap_limited else PHASE_II_CAP_NOT_TRUNCATED,
            "candidate_path_rank": candidate_path_rank,
            "candidate_id": candidate_id,
            "demand_id": demand_id,
            "probe_status": "CAP_TRUNCATED" if cap_limited else "SAFE_BLOCKED",
            "start_node": start_node,
            "target_node": target_node,
            "arc_sequence": "",
            "structurally_valid": "false",
            "invalid_reason": blocker,
            "oracle_entry_signal": "",
            "classification": classification,
            "duplicate_existing_phase2_column": "false",
            "duplicate_generated_this_round": "false",
            "duplicate_of_column_id": "",
            "oracle_generated": "false",
            "diagnostic_only": bool_text(cap_limited),
            "would_be_added_this_round": "false",
            "would_be_added_in_future_task": "false",
            "selected_by_add_policy": "false",
            "add_policy_limited": "false",
            "generation_cap_limited": bool_text(cap_limited),
            "demand_pricing_attempted": "true",
            "demand_cap_limited": "false",
            "round_cap_limited": bool_text(cap_limited),
            "blocker": blocker,
        }

    if config["phase_ii_pricing_mode"] == PHASE_II_PRICING_MODE_K_SHORTEST:
        demand_entries: list[dict[str, Any]] = []
        for demand in demands:
            demand_id = demand.get("demand_id", "")
            source = source_connectors.get(demand_id)
            targets = sink_targets.get(demand_id, set())
            if source is None or not targets:
                rows.append(
                    blocked_row(
                        demand_id,
                        f"ORACLE_R{round_number}_{demand_id}_K1",
                        1,
                        "missing source or sink connector",
                    )
                )
                continue
            start_node = source.get("from_node_time_id", "")
            per_demand_limit = min(config["k_shortest_k"], config["max_phase_ii_candidates_per_demand"])
            path_rows, blocker = k_shortest_phase_ii_paths(
                arcs,
                start_node,
                targets,
                dual_solution,
                parse_float(convention.get("capacity_sign"), math.nan),
                per_demand_limit,
            )
            if not path_rows:
                rows.append(
                    blocked_row(
                        demand_id,
                        f"ORACLE_R{round_number}_{demand_id}_K1",
                        1,
                        blocker or "shortest path could not be found",
                        start_node=start_node,
                    )
                )
                continue
            demand_entries.append(
                {
                    "demand_id": demand_id,
                    "start_node": start_node,
                    "targets": targets,
                    "path_rows": path_rows,
                    "per_demand_limit": per_demand_limit,
                }
            )

        max_rank = max((len(entry["path_rows"]) for entry in demand_entries), default=0)
        cap_truncated = False
        generated_by_demand: set[str] = set()
        truncated_by_demand: dict[str, int] = {}
        for rank in range(1, max_rank + 1):
            for entry in demand_entries:
                path_row = next(
                    (
                        row
                        for row in entry["path_rows"]
                        if int(row.get("candidate_path_rank", 0)) == rank
                    ),
                    None,
                )
                if path_row is None:
                    continue
                demand_id = entry["demand_id"]
                if generated_count >= round_limit:
                    cap_truncated = True
                    truncated_by_demand.setdefault(demand_id, rank)
                    continue
                candidate_id = f"ORACLE_R{round_number}_{demand_id}_K{rank}"
                row = phase_ii_probe_row_from_path(
                    demand_id,
                    candidate_id,
                    round_number,
                    entry["start_node"],
                    entry["targets"],
                    list(path_row["path_arcs"]),
                    path_row.get("target_node"),
                    rank,
                    arcs,
                    arc_by_id,
                    current_pool,
                    dual_solution,
                    convention,
                    config,
                    generated_this_round,
                )
                row["demand_cap_limited"] = bool_text(len(entry["path_rows"]) >= entry["per_demand_limit"])
                rows.append(row)
                generated_by_demand.add(demand_id)
                generated_count += 1

        for demand_id, rank in truncated_by_demand.items():
            rows.append(
                blocked_row(
                    demand_id,
                    f"ORACLE_R{round_number}_{demand_id}_K{rank}_CAP_TRUNCATED",
                    rank,
                    "max_phase_ii_candidates_per_round reached before this candidate could be logged",
                    classification="cap_truncated_candidate_search",
                    cap_limited=True,
                )
            )

        cap_status = PHASE_II_CAP_TRUNCATED if cap_truncated else PHASE_II_CAP_NOT_TRUNCATED
        for row in rows:
            if row.get("round") == round_number:
                row["cap_truncation_status"] = cap_status
                if cap_truncated and row.get("oracle_generated") == "true":
                    row["generation_cap_limited"] = "true"
                    row["round_cap_limited"] = "true"
        return rows

    for demand in demands:
        if generated_count >= round_limit:
            break
        demand_id = demand.get("demand_id", "")
        source = source_connectors.get(demand_id)
        targets = sink_targets.get(demand_id, set())
        candidate_id = f"ORACLE_R{round_number}_{demand_id}"
        if source is None or not targets:
            rows.append(blocked_row(demand_id, candidate_id, 1, "missing source or sink connector"))
            continue
        start_node = source.get("from_node_time_id", "")
        per_demand_limit = min(config["max_phase_ii_candidates_per_demand"], round_limit - generated_count)
        _weight, path_arcs, target_node, blocker = shortest_path_bellman_ford(
            arcs,
            start_node,
            targets,
            dual_solution,
            parse_float(convention.get("capacity_sign"), math.nan),
        )
        if blocker or not path_arcs:
            rows.append(
                blocked_row(
                    demand_id,
                    candidate_id,
                    1,
                    blocker or "shortest path could not be found",
                    start_node=start_node,
                    target_node=target_node or "",
                )
            )
            continue
        rows.append(
            phase_ii_probe_row_from_path(
                demand_id,
                candidate_id,
                round_number,
                start_node,
                targets,
                path_arcs,
                target_node,
                1,
                arcs,
                arc_by_id,
                current_pool,
                dual_solution,
                convention,
                config,
                generated_this_round,
            )
        )
        generated_count += 1
        if per_demand_limit <= 0 or generated_count >= round_limit:
            for row in rows:
                if row.get("round") == round_number and row.get("demand_id") == demand_id:
                    row["generation_cap_limited"] = bool_text(generated_count >= round_limit)
    return rows


def improving_phase_ii_candidates(probes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in probes
        if row.get("classification") == "improving_new_candidate"
        and parse_float(row.get("oracle_entry_signal"), math.inf) < -REDUCED_COST_TOLERANCE
    ]


def phase_ii_candidate_sort_key(row: dict[str, Any]) -> tuple[float, str, int, str]:
    return (
        parse_float(row.get("oracle_entry_signal"), math.inf),
        str(row.get("demand_id", "")),
        int(parse_float(row.get("candidate_path_rank"), math.inf)),
        str(row.get("candidate_id", "")),
    )


def best_phase_ii_candidate(probes: list[dict[str, Any]]) -> dict[str, Any] | None:
    return min(
        improving_phase_ii_candidates(probes),
        key=lambda row: parse_float(row.get("oracle_entry_signal"), math.inf),
        default=None,
    )


def select_phase_ii_candidates(
    probes: list[dict[str, Any]],
    add_policy: str,
    max_candidates_per_round: int,
) -> list[dict[str, Any]]:
    improving = sorted(improving_phase_ii_candidates(probes), key=phase_ii_candidate_sort_key)
    if not improving:
        return []
    if add_policy == PHASE_II_ADD_BEST_ONE_PER_ROUND:
        best = best_phase_ii_candidate(probes)
        return [best] if best is not None else []
    if add_policy == PHASE_II_ADD_BEST_ONE_PER_DEMAND:
        selected_by_demand: dict[str, dict[str, Any]] = {}
        for row in improving:
            demand_id = str(row.get("demand_id", ""))
            if demand_id not in selected_by_demand:
                selected_by_demand[demand_id] = row
        return sorted(selected_by_demand.values(), key=phase_ii_candidate_sort_key)[:max_candidates_per_round]
    if add_policy == PHASE_II_ADD_ALL_IMPROVING_UP_TO_CAP:
        return improving[:max_candidates_per_round]
    return improving[:1]


def build_phase_ii_candidate_row(
    probe: dict[str, Any],
    demands: list[dict[str, str]],
    arcs: list[dict[str, str]],
    round_number: int,
) -> dict[str, str]:
    demand = next(row for row in demands if row.get("demand_id") == probe.get("demand_id"))
    arc_ids = split_sequence(str(probe.get("arc_sequence", "")))
    metadata = build_sequence_metadata(arc_ids, {row.get("arc_id", ""): row for row in arcs})
    departure = demand.get("departure_time", "")
    arrival = metadata["arrival_time"]
    travel_time = str(parse_float(arrival, 0.0) - parse_float(departure, 0.0)) if arrival else ""
    candidate_id = str(probe.get("candidate_id", ""))
    path_id = (
        f"FULL_CG_V1_{candidate_id}"
        if probe.get("phase_ii_pricing_mode") == PHASE_II_PRICING_MODE_K_SHORTEST
        else f"FULL_CG_V1_ORACLE_R{round_number}_{probe.get('demand_id')}"
    )
    return {
        "column_id": candidate_id,
        "path_id": path_id,
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
        "phase2_pool_column_type": "bounded_full_cg_v1_phase2_oracle_candidate",
        "source_metadata": PHASE_II_CANDIDATE_SOURCE,
        "added_in_phase1_round": "",
        "phase1_final_flow": "",
        "written_to_baseline_dynamic_columns": "false",
        "output_only_phase2_initial_pool": "false",
        "output_only_phase2_loop_pool": "false",
        "output_only_phase2_oracle_loop_pool": "true",
        "pool_membership": "full_cg_v1_phase_ii_added_candidate",
        "candidate_source": PHASE_II_CANDIDATE_SOURCE,
        "added_in_phase2_round": str(round_number),
        "oracle_entry_signal_at_addition": str(parse_float(probe.get("oracle_entry_signal"), math.nan)),
        "written_to_phase2_initial_pool": "false",
        "written_to_fixed_source_outputs": "false",
    }


def duplicate_probe_rows(probes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "round": row.get("round", ""),
            "candidate_id": row.get("candidate_id", ""),
            "demand_id": row.get("demand_id", ""),
            "classification": row.get("classification", ""),
            "duplicate_existing_phase2_column": row.get("duplicate_existing_phase2_column", ""),
            "duplicate_generated_this_round": row.get("duplicate_generated_this_round", ""),
            "duplicate_of_column_id": row.get("duplicate_of_column_id", ""),
            "arc_sequence": row.get("arc_sequence", ""),
            "duplicate_audit_status": "PASS",
        }
        for row in probes
    ]


def phase_ii_round_coverage(
    probes: list[dict[str, Any]],
    demands: list[dict[str, str]],
    pricing_config: dict[str, Any],
) -> dict[str, Any]:
    demand_ids = {str(row.get("demand_id", "")) for row in demands if row.get("demand_id", "")}
    generated_demand_ids = {
        str(row.get("demand_id", ""))
        for row in probes
        if row.get("oracle_generated") == "true" and row.get("demand_id", "")
    }
    cap_truncated = any(
        row.get("round_cap_limited") == "true"
        or row.get("cap_truncation_status") == PHASE_II_CAP_TRUNCATED
        for row in probes
    )
    unpriced = sorted(demand_ids - generated_demand_ids)
    if not probes:
        cap_status = PHASE_II_CAP_NOT_TRUNCATED
    elif cap_truncated:
        cap_status = PHASE_II_CAP_TRUNCATED
    else:
        cap_status = PHASE_II_CAP_NOT_TRUNCATED
    if pricing_config["phase_ii_pricing_mode"] == PHASE_II_PRICING_MODE_K_SHORTEST:
        coverage_policy = PHASE_II_COVERAGE_K_SHORTEST_FAIR
    else:
        coverage_policy = PHASE_II_COVERAGE_ONE_PROBE
    return {
        "demand_count": len(demand_ids),
        "priced_demand_count": len(generated_demand_ids),
        "unpriced_demand_count": len(unpriced),
        "unpriced_demands": "|".join(unpriced),
        "all_demands_priced": generated_demand_ids >= demand_ids if demand_ids else True,
        "cap_truncation_status": cap_status,
        "demand_coverage_policy": coverage_policy,
        "max_phase_ii_candidates_per_round_requested": pricing_config.get(
            "max_phase_ii_candidates_per_round_requested",
            pricing_config["max_phase_ii_candidates_per_round"],
        ),
        "strict_phase_ii_candidate_round_cap": bool_text(
            manifest_bool(pricing_config.get("strict_phase_ii_candidate_round_cap"), False)
        ),
    }


def round_log_coverage_fields(coverage: dict[str, Any]) -> dict[str, Any]:
    return {
        "max_phase_ii_candidates_per_round_requested": coverage.get(
            "max_phase_ii_candidates_per_round_requested", ""
        ),
        "strict_phase_ii_candidate_round_cap": coverage.get("strict_phase_ii_candidate_round_cap", ""),
        "demand_coverage_policy": coverage.get("demand_coverage_policy", ""),
        "cap_truncation_status": coverage.get("cap_truncation_status", ""),
        "demand_count": coverage.get("demand_count", ""),
        "priced_demand_count": coverage.get("priced_demand_count", ""),
        "unpriced_demand_count": coverage.get("unpriced_demand_count", ""),
    }


def run_phase_ii_loop(
    output_dir: Path,
    manifest: dict[str, Any],
    phase_i_pool: list[dict[str, str]],
    skip_phase_ii: bool,
    deadline: float | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    paths = manifest_paths(manifest)
    arcs = read_csv_rows(paths["dynamic_arc_file"])
    demands = read_csv_rows(paths["demand_file"])
    current_pool = [dict(row) for row in phase_i_pool]
    ref_obj = finite(manifest.get("arc_lp_reference_objective"))
    max_rounds = int(manifest["max_phase_ii_rounds"])
    pricing_config = demand_fair_phase_ii_pricing_config(phase_ii_pricing_config(manifest), len(demands))
    objective_trace: list[dict[str, Any]] = []
    round_rows: list[dict[str, Any]] = []
    selected_rows: list[dict[str, Any]] = []
    probe_rows_all: list[dict[str, Any]] = []
    safe_blockers: list[str] = []
    unsolved_trial_pool: list[dict[str, str]] = []
    unsolved_trial_metadata: dict[str, Any] = {}
    stop_reason = "phase_ii_skipped" if skip_phase_ii else "max_rounds_reached"

    current_solve = solve_current_pool(arcs, demands, current_pool)
    current_obj = objective_from_solve(current_solve)
    objective_trace.append(
        {
            "solution_index": 0,
            "round": 0,
            "selected_candidate_added_to_reach_solution": "",
            "pool_column_count": len(current_pool),
            "solver_status": current_solve.get("solver_info", {}).get("solver_status"),
            "objective_value": current_obj,
            "objective_change_from_previous": "",
            "arc_lp_reference_objective": ref_obj if ref_obj is not None else "",
            "gap_vs_reference": current_obj - ref_obj if current_obj is not None and ref_obj is not None else "",
            "objective_level_reference_match": False,
            "demand_residual_max": current_solve.get("solution_outputs", {}).get("demand_residual_max"),
            "capacity_violation_count": current_solve.get("solution_outputs", {}).get("capacity_violation_count"),
        }
    )
    if skip_phase_ii or max_rounds == 0:
        stop_reason = "phase_ii_skipped"
    elif runtime_cap_reached(deadline):
        stop_reason = "runtime_cap_exceeded"
        safe_blockers.append(runtime_cap_blocker(manifest))
    elif not solution_status_ok(current_solve):
        stop_reason = "solver_failure"
        safe_blockers.append("initial Phase-II loop RMP solve failed")
    else:
        for round_number in range(1, max_rounds + 1):
            if runtime_cap_reached(deadline):
                stop_reason = "runtime_cap_exceeded"
                safe_blockers.append(runtime_cap_blocker(manifest))
                break
            before_solve = solve_current_pool(arcs, demands, current_pool)
            before_outputs = before_solve.get("solution_outputs", empty_phase2_outputs())
            before_obj = objective_from_solve(before_solve)
            if not solution_status_ok(before_solve):
                stop_reason = "solver_failure"
                safe_blockers.append(f"RMP solve failed before Phase-II round {round_number}")
                current_solve = before_solve
                break
            if (
                pricing_config["phase_ii_pricing_mode"] != PHASE_II_PRICING_MODE_ONE_PROBE
                and ref_obj is not None
                and before_obj is not None
                and abs(before_obj - ref_obj) <= REFERENCE_TOLERANCE
            ):
                stop_reason = "objective_level_reference_match"
                round_rows.append(
                    {
                        "round": round_number,
                        "phase_ii_pricing_mode": pricing_config["phase_ii_pricing_mode"],
                        "phase_ii_add_policy": pricing_config["phase_ii_add_policy"],
                        "k_shortest_k": pricing_config["k_shortest_k"],
                        "max_phase_ii_candidates_per_demand": pricing_config["max_phase_ii_candidates_per_demand"],
                        "max_phase_ii_candidates_per_round": pricing_config["max_phase_ii_candidates_per_round"],
                        "max_phase_ii_candidates_per_round_requested": pricing_config.get(
                            "max_phase_ii_candidates_per_round_requested",
                            pricing_config["max_phase_ii_candidates_per_round"],
                        ),
                        "strict_phase_ii_candidate_round_cap": bool_text(
                            manifest_bool(pricing_config.get("strict_phase_ii_candidate_round_cap"), False)
                        ),
                        "demand_coverage_policy": pricing_config.get("demand_coverage_policy", ""),
                        "cap_truncation_status": PHASE_II_CAP_NOT_TRUNCATED,
                        "demand_count": len(demands),
                        "priced_demand_count": 0,
                        "unpriced_demand_count": 0,
                        "pool_column_count_before": len(current_pool),
                        "rmp_solver_status_before": before_solve["solver_info"].get("solver_status"),
                        "rmp_objective_before": before_obj,
                        "generated_candidates": 0,
                        "improving_nonduplicates": 0,
                        "duplicate_candidates": 0,
                        "invalid_candidates": 0,
                        "selected_candidate_id": "",
                        "selected_candidate_count": 0,
                        "candidate_added": "false",
                        "pool_column_count_after": len(current_pool),
                        "rmp_solver_status_after": before_solve["solver_info"].get("solver_status"),
                        "rmp_objective_after": before_obj,
                        "objective_change": 0.0,
                        "demand_residual_max": before_outputs.get("demand_residual_max"),
                        "capacity_violation_count": before_outputs.get("capacity_violation_count"),
                        "stop_reason": stop_reason,
                    }
                )
                current_solve = before_solve
                break
            convention = validation_convention(before_solve["validation"])
            probes = run_phase_ii_oracle_probes(
                arcs,
                demands,
                current_pool,
                before_solve["dual_solution"],
                convention,
                round_number,
                pricing_config,
            )
            coverage = phase_ii_round_coverage(probes, demands, pricing_config)
            selected_candidates = select_phase_ii_candidates(
                probes,
                pricing_config["phase_ii_add_policy"],
                pricing_config["max_phase_ii_candidates_per_round"],
            )
            selected_ids = {str(row.get("candidate_id", "")) for row in selected_candidates}
            selection_limited = len(improving_phase_ii_candidates(probes)) > len(selected_candidates)
            for rank, probe in enumerate(selected_candidates, start=1):
                probe["selected_round_rank"] = rank
            for probe in probes:
                selected_now = str(probe.get("candidate_id", "")) in selected_ids
                is_improving = probe.get("classification") == "improving_new_candidate" and parse_float(
                    probe.get("oracle_entry_signal"), math.inf
                ) < -REDUCED_COST_TOLERANCE
                probe["would_be_added_this_round"] = bool_text(selected_now)
                probe["selected_by_add_policy"] = bool_text(selected_now)
                probe["would_be_added_in_future_task"] = bool_text(is_improving and not selected_now)
                probe["add_policy_limited"] = bool_text(selection_limited and is_improving and not selected_now)
            probe_rows_all.extend(probes)
            improving = improving_phase_ii_candidates(probes)
            duplicate_count = sum(
                row.get("classification") in {"duplicate_existing_phase2_column", "duplicate_generated_this_round"}
                for row in probes
            )
            invalid_count = sum(row.get("classification") == "invalid_oracle_candidate" for row in probes)
            generated_count = sum(row.get("oracle_generated") == "true" for row in probes)
            if not selected_candidates:
                if coverage["cap_truncation_status"] == PHASE_II_CAP_TRUNCATED:
                    stop_reason = "cap_truncated_candidate_search"
                    safe_blockers.append(
                        "Phase-II candidate search was truncated by max_phase_ii_candidates_per_round before closure could be certified"
                    )
                elif generated_count == 0:
                    stop_reason = "no_candidate_generated"
                elif duplicate_count == len(probes):
                    stop_reason = "duplicate_only_candidate_set"
                elif improving:
                    stop_reason = "improving_nonduplicate_candidate_unselected_by_add_policy_or_cap"
                    safe_blockers.append("improving Phase-II candidates were generated but none were selected")
                elif (
                    pricing_config["phase_ii_pricing_mode"] == PHASE_II_PRICING_MODE_K_SHORTEST
                    and coverage["all_demands_priced"]
                ):
                    stop_reason = "all_demands_priced_no_improving"
                else:
                    stop_reason = "no_improving_nonduplicate_candidate"
                round_rows.append(
                    {
                        "round": round_number,
                        "phase_ii_pricing_mode": pricing_config["phase_ii_pricing_mode"],
                        "phase_ii_add_policy": pricing_config["phase_ii_add_policy"],
                        "k_shortest_k": pricing_config["k_shortest_k"],
                        "max_phase_ii_candidates_per_demand": pricing_config["max_phase_ii_candidates_per_demand"],
                        "max_phase_ii_candidates_per_round": pricing_config["max_phase_ii_candidates_per_round"],
                        **round_log_coverage_fields(coverage),
                        "pool_column_count_before": len(current_pool),
                        "rmp_solver_status_before": before_solve["solver_info"].get("solver_status"),
                        "rmp_objective_before": before_obj,
                        "generated_candidates": generated_count,
                        "improving_nonduplicates": len(improving),
                        "duplicate_candidates": duplicate_count,
                        "invalid_candidates": invalid_count,
                        "selected_candidate_id": "",
                        "selected_candidate_count": 0,
                        "candidate_added": "false",
                        "pool_column_count_after": len(current_pool),
                        "rmp_objective_after": before_obj,
                        "objective_change": 0.0,
                        "demand_residual_max": before_outputs.get("demand_residual_max"),
                        "capacity_violation_count": before_outputs.get("capacity_violation_count"),
                        "stop_reason": stop_reason,
                    }
                )
                current_solve = before_solve
                break
            pool_count_before = len(current_pool)
            candidates = [
                build_phase_ii_candidate_row(selected, demands, arcs, round_number)
                for selected in selected_candidates
            ]
            trial_pool = [*current_pool, *candidates]
            after_solve = solve_current_pool(arcs, demands, trial_pool)
            after_outputs = after_solve.get("solution_outputs", empty_phase2_outputs())
            after_obj = objective_from_solve(after_solve)
            objective_change = after_obj - before_obj if after_obj is not None and before_obj is not None else math.nan
            candidate_flows = [selected_flow(after_outputs, candidate["column_id"]) for candidate in candidates]
            selected_candidate_ids = "|".join(candidate["column_id"] for candidate in candidates)
            selected_candidate_demands = "|".join(candidate["demand_id"] for candidate in candidates)
            selected_candidate_signals = "|".join(str(selected.get("oracle_entry_signal", "")) for selected in selected_candidates)
            if not solution_status_ok(after_solve):
                stop_reason = "solver_failure"
                safe_blockers.append(f"RMP solve failed after adding {selected_candidate_ids}")
            elif not math.isfinite(objective_change) or objective_change >= -TOL:
                stop_reason = "solver_failure"
                safe_blockers.append(f"objective did not decrease after adding {selected_candidate_ids}")
            elif ref_obj is not None and after_obj is not None and after_obj < ref_obj - REFERENCE_TOLERANCE:
                stop_reason = "objective_below_reference_tolerance"
                safe_blockers.append("objective dropped below reference beyond tolerance")
            else:
                stop_reason = ""
            trial_committed = not stop_reason
            round_rows.append(
                    {
                        "round": round_number,
                        "phase_ii_pricing_mode": pricing_config["phase_ii_pricing_mode"],
                        "phase_ii_add_policy": pricing_config["phase_ii_add_policy"],
                        "k_shortest_k": pricing_config["k_shortest_k"],
                        "max_phase_ii_candidates_per_demand": pricing_config["max_phase_ii_candidates_per_demand"],
                        "max_phase_ii_candidates_per_round": pricing_config["max_phase_ii_candidates_per_round"],
                        **round_log_coverage_fields(coverage),
                        "pool_column_count_before": pool_count_before,
                        "rmp_solver_status_before": before_solve["solver_info"].get("solver_status"),
                        "rmp_objective_before": before_obj,
                        "generated_candidates": generated_count,
                        "improving_nonduplicates": len(improving),
                        "duplicate_candidates": duplicate_count,
                        "invalid_candidates": invalid_count,
                        "selected_candidate_id": selected_candidate_ids,
                        "selected_candidate_count": len(candidates),
                        "selected_candidate_demand": selected_candidate_demands,
                        "selected_candidate_reduced_cost": selected_candidate_signals,
                        "candidate_added": bool_text(trial_committed),
                        "pool_column_count_after": len(trial_pool) if trial_committed else len(current_pool),
                        "rmp_solver_status_after": after_solve["solver_info"].get("solver_status"),
                        "rmp_objective_after": after_obj,
                        "objective_change": objective_change if math.isfinite(objective_change) else "",
                        "selected_candidate_flow_after_resolve": "|".join(str(flow) for flow in candidate_flows)
                        if trial_committed
                        else "",
                        "demand_residual_max": after_outputs.get("demand_residual_max"),
                        "capacity_violation_count": after_outputs.get("capacity_violation_count"),
                        "stop_reason": stop_reason,
                    }
                )
            if trial_committed:
                current_pool = trial_pool
                for selected_rank, (selected, candidate, candidate_flow) in enumerate(
                    zip(selected_candidates, candidates, candidate_flows),
                    start=1,
                ):
                    selected_rows.append(
                        {
                            "round": round_number,
                            "phase_ii_pricing_mode": pricing_config["phase_ii_pricing_mode"],
                            "phase_ii_add_policy": pricing_config["phase_ii_add_policy"],
                            "selected_round_rank": selected_rank,
                            "candidate_id": candidate["column_id"],
                            "demand_id": candidate["demand_id"],
                            "candidate_path_rank": selected.get("candidate_path_rank", ""),
                            "arc_sequence": candidate["arc_sequence"],
                            "generalized_cost": candidate["generalized_cost"],
                            "reduced_cost_entry_signal": selected.get("oracle_entry_signal", ""),
                            "classification_at_addition": selected.get("classification", ""),
                            "candidate_flow_after_resolve": candidate_flow,
                            "candidate_flow_final_solution": "",
                            "objective_before_add": before_obj,
                            "objective_after_resolve": after_obj,
                            "objective_change_after_resolve": objective_change
                            if math.isfinite(objective_change)
                            else "",
                            "written_to_baseline_dynamic_columns": "false",
                            "written_to_phase2_initial_pool": "false",
                            "written_to_fixed_source_outputs": "false",
                        }
                    )
                objective_trace.append(
                    {
                        "solution_index": len(objective_trace),
                        "round": round_number,
                        "selected_candidate_added_to_reach_solution": selected_candidate_ids,
                        "pool_column_count": len(current_pool),
                        "solver_status": after_solve["solver_info"].get("solver_status"),
                        "objective_value": after_obj,
                        "objective_change_from_previous": objective_change if math.isfinite(objective_change) else "",
                        "arc_lp_reference_objective": ref_obj if ref_obj is not None else "",
                        "gap_vs_reference": after_obj - ref_obj
                        if after_obj is not None and ref_obj is not None
                        else "",
                        "objective_level_reference_match": (
                            abs(after_obj - ref_obj) <= REFERENCE_TOLERANCE
                            if after_obj is not None and ref_obj is not None
                            else False
                        ),
                        "demand_residual_max": after_outputs.get("demand_residual_max"),
                        "capacity_violation_count": after_outputs.get("capacity_violation_count"),
                    }
                )
                current_solve = after_solve
            else:
                unsolved_trial_pool = trial_pool
                unsolved_trial_metadata = {
                    "round": round_number,
                    "stop_reason": stop_reason,
                    "last_successfully_solved_pool_column_count": len(current_pool),
                    "unsolved_trial_pool_column_count": len(trial_pool),
                    "candidate_ids": [row["column_id"] for row in candidates],
                    "solver_status": after_solve.get("solver_info", {}).get("solver_status"),
                    "candidate_rows_defaulted_to_zero_in_final_solution": False,
                }
            if runtime_cap_reached(deadline):
                stop_reason = "runtime_cap_exceeded"
                safe_blockers.append(runtime_cap_blocker(manifest))
                break
            if stop_reason:
                break
        else:
            stop_reason = "max_rounds_reached"

    final_outputs = current_solve.get("solution_outputs", empty_phase2_outputs())
    final_obj = objective_from_solve(current_solve)
    final_gap = final_obj - ref_obj if final_obj is not None and ref_obj is not None else None
    for row in selected_rows:
        row["candidate_flow_final_solution"] = selected_flow(final_outputs, str(row["candidate_id"]))
    feasible_final = (
        finite(final_outputs.get("demand_residual_max")) is not None
        and finite(final_outputs.get("demand_residual_max")) <= TOL
        and int(final_outputs.get("capacity_violation_count") or 0) == 0
    )
    reference_match = abs(final_gap) <= REFERENCE_TOLERANCE if final_gap is not None else False
    pricing_round_rows = [
        row
        for row in round_rows
        if int(parse_float(row.get("generated_candidates"), 0.0)) > 0
        or row.get("stop_reason") not in {"objective_level_reference_match", "phase_ii_skipped"}
    ]
    if safe_blockers:
        loop_status = "SAFE_BLOCKER"
    elif stop_reason == "phase_ii_skipped":
        loop_status = "SKIPPED"
    elif selected_rows or stop_reason in {
        "no_improving_nonduplicate_candidate",
        "all_demands_priced_no_improving",
        "duplicate_only_candidate_set",
    }:
        loop_status = "PASS" if feasible_final else "SAFE_BLOCKER"
    else:
        loop_status = "PHASE_II_NO_IMPROVING_CANDIDATE"
    summary = {
        "phase_ii_loop_status": loop_status,
        "benchmark_id": manifest["benchmark_id"],
        "phase_ii_pricing_mode": pricing_config["phase_ii_pricing_mode"],
        "k_shortest_k": pricing_config["k_shortest_k"],
        "phase_ii_add_policy": pricing_config["phase_ii_add_policy"],
        "max_phase_ii_rounds": max_rounds,
        "max_candidates_per_demand_per_round": manifest["max_candidates_per_demand_per_round"],
        "max_phase_ii_candidates_per_demand": pricing_config["max_phase_ii_candidates_per_demand"],
        "max_phase_ii_candidates_per_round": pricing_config["max_phase_ii_candidates_per_round"],
        "max_phase_ii_candidates_per_round_requested": pricing_config.get(
            "max_phase_ii_candidates_per_round_requested",
            pricing_config["max_phase_ii_candidates_per_round"],
        ),
        "strict_phase_ii_candidate_round_cap": manifest_bool(
            pricing_config.get("strict_phase_ii_candidate_round_cap"), False
        ),
        "demand_coverage_policy": pricing_config.get("demand_coverage_policy", ""),
        "cap_auto_expanded_for_demand_coverage": pricing_config.get("cap_auto_expanded_for_demand_coverage", False),
        "cap_truncation_status": PHASE_II_CAP_TRUNCATED
        if any(row.get("cap_truncation_status") == PHASE_II_CAP_TRUNCATED for row in round_rows)
        else PHASE_II_CAP_NOT_TRUNCATED,
        "rounds_cap_truncated": sum(
            row.get("cap_truncation_status") == PHASE_II_CAP_TRUNCATED for row in round_rows
        ),
        "min_priced_demand_count": min(
            (
                int(parse_float(row.get("priced_demand_count"), 0.0))
                for row in pricing_round_rows
                if row.get("priced_demand_count") not in {"", None}
            ),
            default=0,
        ),
        "max_unpriced_demand_count": max(
            (
                int(parse_float(row.get("unpriced_demand_count"), 0.0))
                for row in pricing_round_rows
                if row.get("unpriced_demand_count") not in {"", None}
            ),
            default=0,
        ),
        "rounds_attempted": len(round_rows),
        "rounds_with_candidate_added": sum(row.get("candidate_added") == "true" for row in round_rows),
        "candidates_added": len(selected_rows),
        "total_generated_candidates": sum(row.get("oracle_generated") == "true" for row in probe_rows_all),
        "total_improving_nonduplicate_candidates": sum(
            row.get("classification") == "improving_new_candidate" for row in probe_rows_all
        ),
        "total_duplicate_candidates": sum(
            row.get("classification") in {"duplicate_existing_phase2_column", "duplicate_generated_this_round"}
            for row in probe_rows_all
        ),
        "total_nonselected_improving_candidates": sum(
            row.get("would_be_added_in_future_task") == "true" for row in probe_rows_all
        ),
        "total_add_policy_limited_improving_candidates": sum(
            row.get("add_policy_limited") == "true" for row in probe_rows_all
        ),
        "objective_initial": objective_trace[0].get("objective_value"),
        "objective_final": final_obj,
        "objective_change_total": final_obj - objective_trace[0].get("objective_value")
        if final_obj is not None and objective_trace[0].get("objective_value") is not None
        else None,
        "arc_lp_reference_available": ref_obj is not None,
        "arc_lp_reference_objective": ref_obj,
        "objective_gap_vs_reference_final": final_gap,
        "objective_gap_reported": ref_obj is not None,
        "objective_level_reference_match": reference_match,
        "optimality_claimed": False,
        "stop_reason": stop_reason,
        "demand_residual_max_final": final_outputs.get("demand_residual_max"),
        "capacity_violation_count_final": final_outputs.get("capacity_violation_count"),
        "max_capacity_violation_final": final_outputs.get("max_capacity_violation"),
        "safe_blockers": safe_blockers,
        "repaired_seed_columns_used_operationally": False,
        "repair_specs_used_operationally": False,
        "link55_d3_d4_success_hardcoding": False,
        "full_assignment_run": False,
        "full_cg_global_convergence_claimed": False,
        "production_scale_solving_run": False,
    }
    final_export = write_final_phase2_solution_outputs(
        output_dir,
        manifest,
        current_pool,
        current_solve,
        objective_trace,
    )
    summary["final_solution_export_status"] = final_export["export_status"]
    summary["full_solution_and_duals_present"] = final_export["export_status"] == "PASS"
    summary["last_successfully_solved_pool_column_count"] = final_export[
        "last_successfully_solved_pool_column_count"
    ]
    summary["unsolved_trial_pool_column_count"] = len(unsolved_trial_pool)
    if final_export["export_status"] != "PASS":
        safe_blockers.extend(final_export["blockers"])
        loop_status = "SAFE_BLOCKER"
        summary["safe_blockers"] = safe_blockers
        summary["phase_ii_loop_status"] = "SAFE_BLOCKER"
    write_json(output_dir / "full_cg_v1_phase_ii_loop_summary.json", summary)
    write_csv(output_dir / "full_cg_v1_phase_ii_objective_trace.csv", objective_trace, PHASE_II_OBJECTIVE_TRACE_FIELDS if not objective_trace else None)
    write_csv(output_dir / "full_cg_v1_phase_ii_round_log.csv", round_rows, PHASE_II_ROUND_LOG_FIELDS if not round_rows else None)
    write_csv(output_dir / "full_cg_v1_phase_ii_selected_columns.csv", selected_rows, PHASE_II_SELECTED_FIELDS if not selected_rows else None)
    write_csv(output_dir / "full_cg_v1_phase_ii_candidate_log.csv", probe_rows_all, PHASE_II_CANDIDATE_FIELDS if not probe_rows_all else None)
    write_csv(output_dir / "full_cg_v1_final_capacity_audit.csv", final_outputs.get("capacity_usage", []), PHASE_II_AUDIT_FIELDS if not final_outputs.get("capacity_usage", []) else None)
    write_csv(output_dir / "full_cg_v1_final_demand_residual_audit.csv", final_outputs.get("demand_balance", []), PHASE_II_AUDIT_FIELDS if not final_outputs.get("demand_balance", []) else None)
    duplicate_rows = duplicate_probe_rows(probe_rows_all)
    write_csv(output_dir / "full_cg_v1_phase_ii_duplicate_audit.csv", duplicate_rows, PHASE_II_DUPLICATE_FIELDS if not duplicate_rows else None)
    write_csv(output_dir / "full_cg_v1_phase_ii_final_pool.csv", pool_output_rows(current_pool))
    write_csv(output_dir / "full_cg_v1_phase_ii_final_pool_duplicate_audit.csv", duplicate_audit_rows(current_pool))
    write_csv(
        output_dir / "full_cg_v1_phase_ii_unsolved_trial_pool.csv",
        pool_output_rows(unsolved_trial_pool),
    )
    write_json(
        output_dir / "full_cg_v1_phase_ii_unsolved_trial_metadata.json",
        unsolved_trial_metadata
        or {
            "status": "NO_UNSOLVED_TRIAL_POOL",
            "last_successfully_solved_pool_column_count": len(current_pool),
            "unsolved_trial_pool_column_count": 0,
            "candidate_rows_defaulted_to_zero_in_final_solution": False,
        },
    )
    stop_certificate = {
        "stop_certificate_status": "PASS" if loop_status == "PASS" else loop_status,
        "stop_reason": stop_reason,
        "phase_ii_pricing_mode": pricing_config["phase_ii_pricing_mode"],
        "k_shortest_k": pricing_config["k_shortest_k"],
        "phase_ii_add_policy": pricing_config["phase_ii_add_policy"],
        "max_phase_ii_candidates_per_demand": pricing_config["max_phase_ii_candidates_per_demand"],
        "max_phase_ii_candidates_per_round": pricing_config["max_phase_ii_candidates_per_round"],
        "max_phase_ii_candidates_per_round_requested": pricing_config.get(
            "max_phase_ii_candidates_per_round_requested",
            pricing_config["max_phase_ii_candidates_per_round"],
        ),
        "strict_phase_ii_candidate_round_cap": manifest_bool(
            pricing_config.get("strict_phase_ii_candidate_round_cap"), False
        ),
        "demand_coverage_policy": pricing_config.get("demand_coverage_policy", ""),
        "cap_truncation_status": PHASE_II_CAP_TRUNCATED
        if any(row.get("cap_truncation_status") == PHASE_II_CAP_TRUNCATED for row in round_rows)
        else PHASE_II_CAP_NOT_TRUNCATED,
        "bounded_round_cap": max_rounds,
        "rounds_attempted": len(round_rows),
        "candidates_added": len(selected_rows),
        "no_improving_nonduplicate_candidate_at_final_round": stop_reason
        in {
            "no_candidate_generated",
            "no_improving_nonduplicate_candidate",
            "all_demands_priced_no_improving",
            "duplicate_only_candidate_set",
        },
        "cap_truncated_candidate_search_at_final_round": stop_reason == "cap_truncated_candidate_search",
        "candidate_add_policy_limited_at_final_round": stop_reason
        == "improving_nonduplicate_candidate_unselected_by_add_policy_or_cap",
        "objective_trace_valid": all(row.get("solver_status") for row in objective_trace),
        "arc_lp_reference_available": ref_obj is not None,
        "objective_gap_to_reference_reported": ref_obj is not None,
        "objective_level_reference_match": reference_match,
        "final_solution_export_status": final_export["export_status"],
        "full_solution_and_duals_present": final_export["export_status"] == "PASS",
        "last_successfully_solved_pool_column_count": len(current_pool),
        "unsolved_trial_pool_column_count": len(unsolved_trial_pool),
        "optimality_claimed": False,
        "safe_blockers": safe_blockers,
    }
    write_json(output_dir / "full_cg_v1_phase_ii_stop_certificate.json", stop_certificate)
    return summary, {"final_solve": current_solve, "objective_trace": objective_trace, "final_pool": current_pool}


def write_reference_comparison(output_dir: Path, manifest: dict[str, Any], phase2_summary: dict[str, Any]) -> dict[str, Any]:
    ref_obj = finite(manifest.get("arc_lp_reference_objective"))
    final_obj = finite(phase2_summary.get("objective_final"))
    gap = final_obj - ref_obj if final_obj is not None and ref_obj is not None else None
    if ref_obj is None:
        status = "NO_REFERENCE_AVAILABLE"
    elif gap is not None and gap < -REFERENCE_TOLERANCE:
        status = "OBJECTIVE_BELOW_REFERENCE_TOLERANCE"
    elif gap is not None and abs(gap) <= REFERENCE_TOLERANCE:
        status = "PASS"
    else:
        status = "REFERENCE_GAP_REPORTED"
    comparison = {
        "reference_comparison_status": status,
        "benchmark_id": manifest["benchmark_id"],
        "reference_available": ref_obj is not None,
        "reference_summary_path": manifest.get("arc_lp_reference_summary_path"),
        "reference_objective": ref_obj,
        "phase_ii_final_objective": final_obj,
        "gap_vs_reference": gap,
        "absolute_gap_vs_reference": abs(gap) if gap is not None else None,
        "objective_level_reference_match": abs(gap) <= REFERENCE_TOLERANCE if gap is not None else False,
        "objective_below_reference_tolerance": bool(gap is not None and gap < -REFERENCE_TOLERANCE),
        "comparison_policy": manifest.get("reference_comparison_policy"),
        "exact_flow_pattern_reproduction_claimed": False,
        "optimality_claimed": False,
    }
    write_json(output_dir / "full_cg_v1_reference_comparison.json", comparison)
    return comparison


def write_claim_file(output_dir: Path) -> None:
    lines = [
        "# Full CG v1 Safe Claims And Forbidden Claims",
        "",
        "## Safe Claims",
        "",
        "- The runner executed the manifest-specified finite fixture under explicit Phase-I and Phase-II caps.",
        "- It wrote Phase-I and Phase-II stop certificates, objective traces, feasibility audits, and mutation audits.",
        "- If a reference objective is present, it reports only an objective-level numerical comparison.",
        "",
        "## Forbidden Claims",
        "",
        "- Full CG globally converged.",
        "- General convergence established.",
        "- Full Sioux Falls assignment solved.",
        "- Production-scale solver completed.",
        "- Exact arc-LP flow-pattern reproduction.",
        "- Branch-and-price implemented.",
        "- Reinforcement learning used.",
        "- GTFS/railway instantiation.",
        "- Optimality without reference.",
        "- Arbitrary benchmark support.",
    ]
    (output_dir / "full_cg_v1_safe_claims_and_forbidden_claims.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def write_report(output_dir: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Bounded Full CG v1 Run Report",
        "",
        SCOPE_BOUNDARY,
        "",
        f"- Benchmark id: `{summary['benchmark_id']}`",
        f"- Execution mode: `{summary['execution_mode']}`",
        f"- Phase-I status: {summary['phase_i_status']}",
        f"- Phase-I artificial flow: {summary['phase_i_artificial_flow_initial']} -> {summary['phase_i_artificial_flow_final']}",
        f"- Phase-II initial objective: {summary['phase_ii_initial_objective']}",
        f"- Phase-II final objective: {summary['phase_ii_final_objective']}",
        f"- Reference objective: {summary['reference_objective']}",
        f"- Gap vs reference: {summary['objective_gap_vs_reference_final']}",
        f"- Phase-II rounds: {summary['phase_ii_rounds_attempted']}",
        f"- Phase-II candidates added: {summary['phase_ii_candidates_added']}",
        f"- Stop reason: {summary['stop_reason']}",
        f"- Demand residual max: {summary['demand_residual_max_final']}",
        f"- Capacity violation count: {summary['capacity_violation_count_final']}",
        f"- Mutation audit: {summary['mutation_audit_status']}",
        "",
        "The reference comparison is objective-level only. The run does not claim exact arc-flow-pattern reproduction or global convergence.",
    ]
    if summary.get("safe_blockers"):
        lines.extend(["", "## Safe Blockers", ""])
        lines.extend(f"- {item}" for item in summary["safe_blockers"])
    (output_dir / "full_cg_v1_run_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def execution_mode(
    phase_i_summary: dict[str, Any],
    init_summary: dict[str, Any],
    phase2_summary: dict[str, Any],
    reference: dict[str, Any],
    mutation: dict[str, Any],
    preflight_only: bool,
) -> str:
    if preflight_only:
        return "bounded_full_cg_v1_safe_blocker"
    if mutation.get("mutation_audit_status") != "PASS":
        return "bounded_full_cg_v1_safe_blocker"
    if phase_i_summary.get("phase_i_status") != "PASS":
        return "bounded_full_cg_v1_phase_i_blocked"
    if init_summary.get("phase_ii_initialization_status") != "PASS":
        return "bounded_full_cg_v1_phase_ii_initialization_blocked"
    if phase2_summary.get("safe_blockers"):
        return "bounded_full_cg_v1_safe_blocker"
    if reference.get("objective_below_reference_tolerance"):
        return "bounded_full_cg_v1_safe_blocker"
    if phase2_summary.get("phase_ii_loop_status") == "SKIPPED":
        return "bounded_full_cg_v1_phase_ii_partial_progress"
    if reference.get("reference_available") and reference.get("objective_level_reference_match"):
        return "bounded_full_cg_v1_pass"
    if reference.get("reference_available"):
        return "bounded_full_cg_v1_reference_gap_reported"
    if phase2_summary.get("phase_ii_loop_status") == "PASS":
        return "bounded_full_cg_v1_pass_no_reference"
    if phase2_summary.get("candidates_added", 0) > 0:
        return "bounded_full_cg_v1_phase_ii_partial_progress"
    if phase2_summary.get("stop_reason") == "no_improving_nonduplicate_candidate":
        return "bounded_full_cg_v1_no_improving_candidate"
    return "bounded_full_cg_v1_phase_ii_partial_progress"


def run_status_from_execution_mode(mode: str, safe_blockers: list[Any]) -> str:
    if mode == "bounded_full_cg_v1_pass":
        return "PASS"
    if mode == "bounded_full_cg_v1_reference_gap_reported":
        return "REFERENCE_GAP_REPORTED"
    if mode == "bounded_full_cg_v1_pass_no_reference":
        return "NO_REFERENCE_AVAILABLE"
    if mode == "bounded_full_cg_v1_phase_ii_partial_progress":
        return "PARTIAL_PROGRESS"
    if mode == "bounded_full_cg_v1_no_improving_candidate":
        return "NO_IMPROVING_CANDIDATE"
    if mode == "bounded_full_cg_v1_phase_i_blocked":
        return "PHASE_I_BLOCKED"
    if mode == "bounded_full_cg_v1_phase_ii_initialization_blocked":
        return "PHASE_II_INITIALIZATION_BLOCKED"
    if safe_blockers or mode == "bounded_full_cg_v1_safe_blocker":
        return "SAFE_BLOCKER"
    return "REVIEW_REQUIRED"


def write_mutation_audit(output_dir: Path, before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    mutated = {
        key: {"before": value, "after": after.get("artifacts", {}).get(key, "")}
        for key, value in before.get("artifacts", {}).items()
        if after.get("artifacts", {}).get(key, "") != value
    }
    mutation = {
        "mutation_audit_status": "PASS" if not mutated else "FAIL",
        "protected_artifacts_mutated": bool(mutated),
        "mutated_artifacts": mutated,
        "baseline_dynamic_columns_mutated": any(path.endswith("dynamic_columns.csv") for path in mutated),
        "accepted_outputs_mutated": any(path.startswith("outputs/") for path in mutated),
        "selected_fixture_raw_inputs_mutated": any(path.startswith("data/") for path in mutated),
        "repaired_seed_columns_used_operationally": False,
        "repair_specs_used_operationally": False,
        "link55_d3_d4_success_hardcoding": False,
        "external_data_staged": False,
    }
    write_json(output_dir / "full_cg_v1_mutation_audit.json", mutation)
    return mutation


def run_full_cg_v1(args: argparse.Namespace) -> dict[str, Any]:
    start = time.monotonic()
    manifest_path = resolve_path(args.input_manifest) or Path(args.input_manifest)
    output_dir = resolve_path(args.output_dir) or ROOT_DIR / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_manifest = load_manifest(manifest_path)
    manifest = resolved_manifest(raw_manifest, args)
    deadline = start + int(manifest["runtime_cap_seconds"])
    blockers = validate_manifest(manifest)
    paths = manifest_paths(manifest)
    for key in ["dynamic_data_dir", "demand_file", "dynamic_arc_file", "current_candidate_pool_file"]:
        if not paths[key].exists():
            blockers.append(f"missing required input path for {key}: {paths[key]}")
    write_json(output_dir / "full_cg_v1_input_manifest_resolved.json", manifest)
    protected = protected_paths(manifest)
    before_hashes = hash_manifest(protected, "before_full_cg_v1_run")
    write_json(output_dir / "full_cg_v1_protected_artifact_hash_before.json", before_hashes)
    if blockers or args.preflight_only:
        safe_blockers = blockers or ["preflight-only requested; optimization stages not run"]
        empty_phase_i = {
            "phase_i_status": "SAFE_BLOCKER",
            "phase_i_needed": None,
            "phase_i_loop_ran": False,
            "phase_i_artificial_flow_initial": None,
            "phase_i_artificial_flow_final": None,
            "artificial_flow_cleared": False,
            "max_phase_i_rounds": int(manifest.get("max_phase_i_rounds", 0) or 0),
            "rounds_attempted": 0,
            "candidates_added": 0,
            "stop_reason": "preflight_only" if args.preflight_only else "manifest_validation_blocked",
            "safe_blockers": safe_blockers,
        }
        write_phase_i_outputs(output_dir, empty_phase_i, [], [], [])
        init_summary = {"phase_ii_initialization_status": "NOT_RUN", "safe_blocker": "; ".join(safe_blockers)}
        phase2_summary = {"phase_ii_loop_status": "NOT_RUN", "safe_blockers": safe_blockers, "stop_reason": "not_run"}
        phase2_summary.update(phase_ii_pricing_config(manifest))
        write_json(output_dir / "full_cg_v1_phase_ii_initialization_summary.json", init_summary)
        write_phase2_solution_outputs(output_dir, "full_cg_v1_phase_ii_initial", {})
        write_json(output_dir / "full_cg_v1_phase_ii_loop_summary.json", phase2_summary)
        write_csv(output_dir / "full_cg_v1_phase_ii_objective_trace.csv", [], PHASE_II_OBJECTIVE_TRACE_FIELDS)
        write_csv(output_dir / "full_cg_v1_phase_ii_round_log.csv", [], PHASE_II_ROUND_LOG_FIELDS)
        write_csv(output_dir / "full_cg_v1_phase_ii_selected_columns.csv", [], PHASE_II_SELECTED_FIELDS)
        write_csv(output_dir / "full_cg_v1_phase_ii_candidate_log.csv", [], PHASE_II_CANDIDATE_FIELDS)
        write_csv(output_dir / "full_cg_v1_final_capacity_audit.csv", [], PHASE_II_AUDIT_FIELDS)
        write_csv(output_dir / "full_cg_v1_final_demand_residual_audit.csv", [], PHASE_II_AUDIT_FIELDS)
        write_json(output_dir / "full_cg_v1_phase_ii_stop_certificate.json", {"stop_certificate_status": "NOT_RUN", "safe_blockers": safe_blockers})
        reference = write_reference_comparison(output_dir, manifest, phase2_summary)
        after_hashes = hash_manifest(protected, "after_full_cg_v1_run")
        write_json(output_dir / "full_cg_v1_protected_artifact_hash_after.json", after_hashes)
        mutation = write_mutation_audit(output_dir, before_hashes, after_hashes)
        write_claim_file(output_dir)
        mode = execution_mode(empty_phase_i, init_summary, phase2_summary, reference, mutation, bool(args.preflight_only))
        summary = {
            "run_status": "SAFE_BLOCKER",
            "execution_mode": mode,
            "benchmark_id": manifest["benchmark_id"],
            "safe_blockers": safe_blockers,
            "phase_i_status": empty_phase_i["phase_i_status"],
            "phase_i_artificial_flow_initial": None,
            "phase_i_artificial_flow_final": None,
            "phase_ii_initial_objective": None,
            "phase_ii_final_objective": None,
            "phase_ii_pricing_mode": manifest.get("phase_ii_pricing_mode"),
            "k_shortest_k": manifest.get("k_shortest_k"),
            "phase_ii_add_policy": manifest.get("phase_ii_add_policy"),
            "reference_objective": finite(manifest.get("arc_lp_reference_objective")),
            "objective_gap_vs_reference_final": None,
            "phase_ii_rounds_attempted": 0,
            "phase_ii_candidates_added": 0,
            "stop_reason": "preflight_only" if args.preflight_only else "manifest_validation_blocked",
            "demand_residual_max_final": None,
            "capacity_violation_count_final": None,
            "mutation_audit_status": mutation["mutation_audit_status"],
            "runtime_seconds": time.monotonic() - start,
        }
        write_json(output_dir / "full_cg_v1_run_summary.json", summary)
        write_report(output_dir, summary)
        return summary

    arcs = read_csv_rows(paths["dynamic_arc_file"])
    demands = read_csv_rows(paths["demand_file"])
    original_pool = read_csv_rows(paths["current_candidate_pool_file"])
    operational_pool, pool_summary = materialize_operational_pool(output_dir, manifest, original_pool)
    real_only_solve = solve_current_pool(arcs, demands, operational_pool)
    phase_i_summary, phase_i_pool = run_phase_i(output_dir, manifest, operational_pool, real_only_solve, deadline)
    if phase_i_summary.get("phase_i_status") == "PASS":
        if runtime_cap_reached(deadline):
            init_summary = {
                "phase_ii_initialization_status": "NOT_RUN_RUNTIME_CAP",
                "safe_blocker": runtime_cap_blocker(manifest),
            }
            write_json(output_dir / "full_cg_v1_phase_ii_initialization_summary.json", init_summary)
            write_phase2_solution_outputs(output_dir, "full_cg_v1_phase_ii_initial", {})
        else:
            init_summary, _init_solve = run_phase_ii_initialization(output_dir, manifest, phase_i_pool)
    else:
        init_summary = {
            "phase_ii_initialization_status": "NOT_RUN_PHASE_I_BLOCKED",
            "safe_blocker": "Phase-I artificial flow did not clear",
        }
        write_json(output_dir / "full_cg_v1_phase_ii_initialization_summary.json", init_summary)
        write_phase2_solution_outputs(output_dir, "full_cg_v1_phase_ii_initial", {})
    if init_summary.get("phase_ii_initialization_status") == "PASS":
        phase2_summary, _phase2_details = run_phase_ii_loop(output_dir, manifest, phase_i_pool, bool(args.skip_phase_ii), deadline)
    else:
        phase2_summary = {
            "phase_ii_loop_status": "NOT_RUN",
            **phase_ii_pricing_config(manifest),
            "safe_blockers": [init_summary.get("safe_blocker", "Phase-II initialization blocked")],
            "stop_reason": "phase_ii_initialization_blocked",
            "objective_initial": None,
            "objective_final": None,
            "rounds_attempted": 0,
            "candidates_added": 0,
            "demand_residual_max_final": None,
            "capacity_violation_count_final": None,
        }
        write_json(output_dir / "full_cg_v1_phase_ii_loop_summary.json", phase2_summary)
        write_csv(output_dir / "full_cg_v1_phase_ii_objective_trace.csv", [], PHASE_II_OBJECTIVE_TRACE_FIELDS)
        write_csv(output_dir / "full_cg_v1_phase_ii_round_log.csv", [], PHASE_II_ROUND_LOG_FIELDS)
        write_csv(output_dir / "full_cg_v1_phase_ii_selected_columns.csv", [], PHASE_II_SELECTED_FIELDS)
        write_csv(output_dir / "full_cg_v1_phase_ii_candidate_log.csv", [], PHASE_II_CANDIDATE_FIELDS)
        write_csv(output_dir / "full_cg_v1_final_capacity_audit.csv", [], PHASE_II_AUDIT_FIELDS)
        write_csv(output_dir / "full_cg_v1_final_demand_residual_audit.csv", [], PHASE_II_AUDIT_FIELDS)
        write_json(output_dir / "full_cg_v1_phase_ii_stop_certificate.json", {"stop_certificate_status": "NOT_RUN", "safe_blockers": phase2_summary["safe_blockers"]})
    reference = write_reference_comparison(output_dir, manifest, phase2_summary)
    after_hashes = hash_manifest(protected, "after_full_cg_v1_run")
    write_json(output_dir / "full_cg_v1_protected_artifact_hash_after.json", after_hashes)
    mutation = write_mutation_audit(output_dir, before_hashes, after_hashes)
    write_claim_file(output_dir)
    safe_blockers = [
        *phase_i_summary.get("safe_blockers", []),
        *([init_summary.get("safe_blocker")] if init_summary.get("safe_blocker") else []),
        *phase2_summary.get("safe_blockers", []),
    ]
    if reference.get("objective_below_reference_tolerance"):
        safe_blockers.append("objective dropped below reference beyond tolerance")
    mode = execution_mode(phase_i_summary, init_summary, phase2_summary, reference, mutation, False)
    if mode not in EXECUTION_MODES:
        mode = "bounded_full_cg_v1_safe_blocker"
        safe_blockers.append("internal execution mode outside allowed set")
    summary = {
        "run_status": run_status_from_execution_mode(mode, safe_blockers),
        "execution_mode": mode,
        "benchmark_id": manifest["benchmark_id"],
        "dynamic_data_dir": manifest["dynamic_data_dir"],
        "operational_pool_summary": pool_summary,
        "phase_i_status": phase_i_summary.get("phase_i_status"),
        "phase_i_needed": phase_i_summary.get("phase_i_needed"),
        "phase_i_loop_ran": phase_i_summary.get("phase_i_loop_ran"),
        "phase_i_artificial_flow_initial": phase_i_summary.get("phase_i_artificial_flow_initial"),
        "phase_i_artificial_flow_final": phase_i_summary.get("phase_i_artificial_flow_final"),
        "phase_i_rounds_attempted": phase_i_summary.get("rounds_attempted"),
        "phase_i_candidates_added": phase_i_summary.get("candidates_added"),
        "phase_ii_initialization_status": init_summary.get("phase_ii_initialization_status"),
        "phase_ii_initial_objective": init_summary.get("rmp_objective"),
        "phase_ii_loop_status": phase2_summary.get("phase_ii_loop_status"),
        "phase_ii_pricing_mode": phase2_summary.get("phase_ii_pricing_mode"),
        "k_shortest_k": phase2_summary.get("k_shortest_k"),
        "phase_ii_add_policy": phase2_summary.get("phase_ii_add_policy"),
        "max_phase_ii_candidates_per_demand": phase2_summary.get("max_phase_ii_candidates_per_demand"),
        "max_phase_ii_candidates_per_round": phase2_summary.get("max_phase_ii_candidates_per_round"),
        "max_phase_ii_candidates_per_round_requested": phase2_summary.get(
            "max_phase_ii_candidates_per_round_requested"
        ),
        "strict_phase_ii_candidate_round_cap": phase2_summary.get("strict_phase_ii_candidate_round_cap"),
        "demand_coverage_policy": phase2_summary.get("demand_coverage_policy"),
        "cap_auto_expanded_for_demand_coverage": phase2_summary.get("cap_auto_expanded_for_demand_coverage"),
        "cap_truncation_status": phase2_summary.get("cap_truncation_status"),
        "rounds_cap_truncated": phase2_summary.get("rounds_cap_truncated"),
        "min_priced_demand_count": phase2_summary.get("min_priced_demand_count"),
        "max_unpriced_demand_count": phase2_summary.get("max_unpriced_demand_count"),
        "phase_ii_rounds_attempted": phase2_summary.get("rounds_attempted"),
        "phase_ii_candidates_generated": phase2_summary.get("total_generated_candidates"),
        "phase_ii_improving_nonduplicates": phase2_summary.get("total_improving_nonduplicate_candidates"),
        "phase_ii_candidates_added": phase2_summary.get("candidates_added"),
        "phase_ii_final_objective": phase2_summary.get("objective_final"),
        "phase_ii_objective_change_total": phase2_summary.get("objective_change_total"),
        "final_solution_export_status": phase2_summary.get("final_solution_export_status"),
        "full_solution_and_duals_present": phase2_summary.get("full_solution_and_duals_present"),
        "last_successfully_solved_pool_column_count": phase2_summary.get(
            "last_successfully_solved_pool_column_count"
        ),
        "unsolved_trial_pool_column_count": phase2_summary.get("unsolved_trial_pool_column_count"),
        "reference_objective": reference.get("reference_objective"),
        "objective_gap_vs_reference_final": reference.get("gap_vs_reference"),
        "objective_level_reference_match": reference.get("objective_level_reference_match"),
        "stop_reason": phase2_summary.get("stop_reason") or phase_i_summary.get("stop_reason"),
        "demand_residual_max_final": phase2_summary.get("demand_residual_max_final"),
        "capacity_violation_count_final": phase2_summary.get("capacity_violation_count_final"),
        "mutation_audit_status": mutation.get("mutation_audit_status"),
        "protected_artifacts_mutated": mutation.get("protected_artifacts_mutated"),
        "safe_blockers": safe_blockers,
        "full_assignment_run": False,
        "full_cg_global_convergence_claimed": False,
        "production_scale_solving_run": False,
        "optimality_claimed": False,
        "exact_arc_flow_pattern_reproduction_claimed": False,
        "repaired_seed_columns_used_operationally": False,
        "repair_specs_used_operationally": False,
        "link55_d3_d4_success_hardcoding": False,
        "runtime_seconds": time.monotonic() - start,
    }
    write_json(output_dir / "full_cg_v1_run_summary.json", summary)
    write_report(output_dir, summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-manifest", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--benchmark-id", required=True)
    parser.add_argument("--max-phase-i-rounds", type=int, required=True)
    parser.add_argument("--max-phase-ii-rounds", type=int, required=True)
    parser.add_argument("--max-candidates-per-demand", type=int, required=True)
    parser.add_argument("--phase-ii-pricing-mode", choices=sorted(PHASE_II_PRICING_MODES))
    parser.add_argument("--k-shortest-k", type=int)
    parser.add_argument("--phase-ii-add-policy", choices=sorted(PHASE_II_ADD_POLICIES))
    parser.add_argument("--max-phase-ii-candidates-per-demand", type=int)
    parser.add_argument("--max-phase-ii-candidates-per-round", type=int)
    parser.add_argument("--strict-phase-ii-candidate-round-cap", action="store_true")
    parser.add_argument("--runtime-cap-seconds", type=int, required=True)
    parser.add_argument("--no-mutate-accepted-outputs", action="store_true", required=True)
    parser.add_argument("--write-review-artifacts", action="store_true")
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--skip-phase-ii", action="store_true")
    parser.add_argument("--reference-objective", type=float)
    parser.add_argument("--reference-summary")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = run_full_cg_v1(args)
    print(json.dumps({"execution_mode": summary.get("execution_mode"), "run_status": summary.get("run_status")}))
    if args.preflight_only:
        return 0
    return 0 if summary.get("execution_mode") != "bounded_full_cg_v1_safe_blocker" else 1


if __name__ == "__main__":
    raise SystemExit(main())
