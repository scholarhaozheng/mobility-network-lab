"""One-candidate oracle Phase-II add-resolve diagnostic.

This diagnostic validates the D4 path found by the dynamic-network pricing
oracle precheck, adds it only to a temporary real-column pool based on the
accepted fixed-source Phase-II closure pool, and re-solves the real-only
Phase-II RMP once.

It does not mutate the Phase-II initial pool, mutate the baseline
dynamic_columns.csv, mutate accepted fixed-source closure outputs, rerun oracle
pricing after the resolve, run a loop, run full assignment, run full CG, or
claim general convergence.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

from build_sioux_harder_bounded_stage2 import ROOT_DIR
from phase1_artificial_rmp_preflight import sha256_file
from phase1_one_candidate_add_resolve import ACCEPTED_BASELINE_HASH
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
)


OUTPUT_DIR = ROOT_DIR / "outputs" / "phase2_oracle_one_candidate_add_resolve"
ORACLE_PRECHECK_DIR = ROOT_DIR / "outputs" / "phase2_dynamic_pricing_oracle_precheck"
LOOP_DIR = ROOT_DIR / "outputs" / "phase2_bounded_loop_diagnostic"
CLOSURE_DIR = ROOT_DIR / "outputs" / "phase2_fixed_source_closure_audit"
HANDOFF_DIR = ROOT_DIR / "outputs" / "phase1_closure_phase2_handoff_precheck"
PHASE2_INITIAL_POOL = HANDOFF_DIR / "phase2_initial_column_pool.csv"
FIXED_SOURCE_FINAL_POOL = LOOP_DIR / "phase2_loop_temporary_pool_final.csv"
BASELINE_COLUMNS = ROOT_DIR / "data" / "second_controlled_benchmark_link55" / "dynamic_columns.csv"
SELECTED_CANDIDATE_ID = "ORACLE_PROBE_D4"
EXPECTED_ARC_SEQUENCE = "source_D4|wait_7_t2|move_18_t3|move_55_t5|move_48_t8|sink_D4_10_t12"
EXPECTED_ENTRY_SIGNAL = -6435.800000000001
EXPECTED_OBJECTIVE_BEFORE = 393772231.32911855
EXPECTED_BASE_POOL_COUNT = 13
ROUND1_POOL_COUNT = 14
ALLOW_VARIABLE_FIXED_SOURCE_BASE = False
ALLOW_VARIABLE_ORACLE_CANDIDATE = False
USE_BEST_NEW_ORACLE_CANDIDATE_FROM_PRECHECK = False
REQUIRED_INPUTS = [
    ORACLE_PRECHECK_DIR / "phase2_pricing_oracle_precheck_summary.json",
    ORACLE_PRECHECK_DIR / "phase2_oracle_shortest_path_probe.csv",
    ORACLE_PRECHECK_DIR / "phase2_oracle_known_candidate_comparison.csv",
    ORACLE_PRECHECK_DIR / "phase2_oracle_hash_audit.json",
    LOOP_DIR / "phase2_bounded_loop_summary.json",
    LOOP_DIR / "phase2_loop_solution_by_column_final.csv",
    LOOP_DIR / "phase2_loop_capacity_usage_final.csv",
    LOOP_DIR / "phase2_loop_hash_audit.json",
    LOOP_DIR / "phase2_loop_temporary_pool_final.csv",
    CLOSURE_DIR / "phase2_fixed_source_closure_summary.json",
    PHASE2_INITIAL_POOL,
]
FIXED_SOURCE_OUTPUTS = [
    LOOP_DIR / "phase2_bounded_loop_summary.json",
    LOOP_DIR / "phase2_loop_solution_by_column_final.csv",
    LOOP_DIR / "phase2_loop_capacity_usage_final.csv",
    LOOP_DIR / "phase2_loop_hash_audit.json",
    LOOP_DIR / "phase2_loop_temporary_pool_final.csv",
    CLOSURE_DIR / "phase2_fixed_source_closure_summary.json",
]
SCOPE_BOUNDARY = (
    "This is a one-candidate oracle add-resolve diagnostic. It adds the "
    "selected oracle probe path only to a temporary real-column pool based on the "
    "manifest-selected Phase-II closure pool and re-solves the Phase-II "
    "RMP once. It does not mutate phase2_initial_column_pool.csv, mutate "
    "baseline dynamic_columns.csv, mutate accepted fixed-source closure "
    "outputs, rerun oracle pricing after resolve, run a loop, run full "
    "assignment, run full CG, or claim general convergence, production-scale "
    "solving, GTFS, railway, branch-and-price, reinforcement learning, or "
    "exact arc-LP flow-pattern reproduction."
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_artifact_path(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else ROOT_DIR / path


def refresh_required_inputs() -> None:
    global REQUIRED_INPUTS, FIXED_SOURCE_OUTPUTS
    REQUIRED_INPUTS = [
        ORACLE_PRECHECK_DIR / "phase2_pricing_oracle_precheck_summary.json",
        ORACLE_PRECHECK_DIR / "phase2_oracle_shortest_path_probe.csv",
        ORACLE_PRECHECK_DIR / "phase2_oracle_known_candidate_comparison.csv",
        ORACLE_PRECHECK_DIR / "phase2_oracle_hash_audit.json",
        LOOP_DIR / "phase2_bounded_loop_summary.json",
        LOOP_DIR / "phase2_loop_solution_by_column_final.csv",
        LOOP_DIR / "phase2_loop_capacity_usage_final.csv",
        LOOP_DIR / "phase2_loop_hash_audit.json",
        LOOP_DIR / "phase2_loop_temporary_pool_final.csv",
        CLOSURE_DIR / "phase2_fixed_source_closure_summary.json",
        PHASE2_INITIAL_POOL,
    ]
    FIXED_SOURCE_OUTPUTS = [
        LOOP_DIR / "phase2_bounded_loop_summary.json",
        LOOP_DIR / "phase2_loop_solution_by_column_final.csv",
        LOOP_DIR / "phase2_loop_capacity_usage_final.csv",
        LOOP_DIR / "phase2_loop_hash_audit.json",
        LOOP_DIR / "phase2_loop_temporary_pool_final.csv",
        CLOSURE_DIR / "phase2_fixed_source_closure_summary.json",
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
    global ORACLE_PRECHECK_DIR, LOOP_DIR, CLOSURE_DIR, HANDOFF_DIR, PHASE2_INITIAL_POOL
    global FIXED_SOURCE_FINAL_POOL, BASELINE_COLUMNS
    global ALLOW_VARIABLE_FIXED_SOURCE_BASE, ALLOW_VARIABLE_ORACLE_CANDIDATE
    global USE_BEST_NEW_ORACLE_CANDIDATE_FROM_PRECHECK
    ORACLE_PRECHECK_DIR = resolve_artifact_path(artifacts.get("oracle_precheck_dir")) or ORACLE_PRECHECK_DIR
    LOOP_DIR = resolve_artifact_path(artifacts.get("fixed_source_loop_dir")) or resolve_artifact_path(artifacts.get("loop_dir")) or LOOP_DIR
    CLOSURE_DIR = (
        resolve_artifact_path(artifacts.get("fixed_source_closure_dir"))
        or resolve_artifact_path(artifacts.get("closure_dir"))
        or CLOSURE_DIR
    )
    HANDOFF_DIR = resolve_artifact_path(artifacts.get("handoff_dir")) or HANDOFF_DIR
    PHASE2_INITIAL_POOL = (
        resolve_artifact_path(artifacts.get("phase2_initial_pool"))
        or resolve_artifact_path(artifacts.get("phase2_pool"))
        or (HANDOFF_DIR / "phase2_initial_column_pool.csv")
    )
    FIXED_SOURCE_FINAL_POOL = (
        resolve_artifact_path(artifacts.get("fixed_source_final_pool"))
        or resolve_artifact_path(artifacts.get("phase2_base_pool"))
        or (LOOP_DIR / "phase2_loop_temporary_pool_final.csv")
    )
    BASELINE_COLUMNS = resolve_artifact_path(artifacts.get("baseline_columns")) or BASELINE_COLUMNS
    ALLOW_VARIABLE_FIXED_SOURCE_BASE = bool(artifacts.get("allow_variable_fixed_source_base", False))
    ALLOW_VARIABLE_ORACLE_CANDIDATE = bool(artifacts.get("allow_variable_oracle_candidate", False))
    USE_BEST_NEW_ORACLE_CANDIDATE_FROM_PRECHECK = bool(
        artifacts.get("use_best_new_oracle_candidate_from_precheck", False)
    )
    refresh_required_inputs()
    return artifacts


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def split_sequence(value: str) -> list[str]:
    return [part for part in value.split("|") if part]


def required_input_blockers() -> list[str]:
    blockers: list[str] = []
    for path in REQUIRED_INPUTS:
        if not path.exists() or path.stat().st_size == 0:
            blockers.append(f"missing or empty required input: {rel(path)}")
    return blockers


def find_probe_row(rows: list[dict[str, str]]) -> dict[str, str] | None:
    if USE_BEST_NEW_ORACLE_CANDIDATE_FROM_PRECHECK:
        candidates = [
            row
            for row in rows
            if row.get("classification") == "new_oracle_candidate"
            and parse_float(row.get("oracle_entry_signal"), math.inf) < -TOL
        ]
        return min(candidates, key=lambda row: parse_float(row.get("oracle_entry_signal"), math.inf), default=None)
    return next(
        (
            row
            for row in rows
            if row.get("demand_id") == "D4"
            and row.get("arc_sequence") == EXPECTED_ARC_SEQUENCE
            and row.get("classification") == "new_oracle_candidate"
        ),
        None,
    )


def find_comparison_row(rows: list[dict[str, str]]) -> dict[str, str] | None:
    return next((row for row in rows if row.get("candidate_id") == SELECTED_CANDIDATE_ID), None)


def fixed_source_output_hashes() -> dict[str, str]:
    return {rel(path): sha256_file(path) for path in FIXED_SOURCE_OUTPUTS if path.exists()}


def oracle_precheck_blockers(summary: dict[str, Any], hash_audit: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if summary.get("diagnostic_status") != "PASS":
        blockers.append(f"oracle precheck status changed: {summary.get('diagnostic_status')}")
    if summary.get("shortest_path_probe_run") is not True:
        blockers.append("oracle precheck did not run shortest-path probe")
    if summary.get("oracle_precheck_negative_reduced_cost_nonduplicate_found") is not True:
        blockers.append("oracle precheck no longer reports a negative reduced-cost non-duplicate")
    if summary.get("validated_convention") != "stationarity_c-1eq-1cap-1lower-1upper":
        blockers.append(f"oracle precheck convention changed: {summary.get('validated_convention')}")
    if summary.get("generated_columns_added_to_any_rmp") is not False:
        blockers.append("oracle precheck unexpectedly reports generated columns added to an RMP")
    if summary.get("rmp_resolved_after_oracle_probe") is not False:
        blockers.append("oracle precheck unexpectedly reports RMP re-solve")
    if summary.get("add_resolve_run") is not False or summary.get("cg_loop_run") is not False:
        blockers.append("oracle precheck unexpectedly reports add-resolve or loop")
    if summary.get("full_assignment_run") is not False or summary.get("full_cg_run") is not False:
        blockers.append("oracle precheck unexpectedly reports full assignment or full CG")
    if hash_audit.get("phase2_initial_pool_mutated") is not False:
        blockers.append("oracle precheck hash audit reports Phase-II initial pool mutation")
    if hash_audit.get("baseline_dynamic_columns_mutated") is not False:
        blockers.append("oracle precheck hash audit reports baseline mutation")
    return blockers


def fixed_source_blockers(loop_summary: dict[str, Any], closure_summary: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if loop_summary.get("diagnostic_status") != "PASS":
        blockers.append(f"bounded Phase-II loop status changed: {loop_summary.get('diagnostic_status')}")
    if (
        not ALLOW_VARIABLE_FIXED_SOURCE_BASE
        and abs(parse_float(loop_summary.get("objective_final"), math.inf) - EXPECTED_OBJECTIVE_BEFORE) > 1e-5
    ):
        blockers.append(f"bounded Phase-II loop final objective changed: {loop_summary.get('objective_final')}")
    if (
        not ALLOW_VARIABLE_FIXED_SOURCE_BASE
        and int(loop_summary.get("final_temporary_pool_column_count") or -1) != EXPECTED_BASE_POOL_COUNT
    ):
        blockers.append(f"bounded Phase-II final pool count changed: {loop_summary.get('final_temporary_pool_column_count')}")
    if loop_summary.get("phase2_initial_pool_mutated") is not False:
        blockers.append("bounded Phase-II loop reports Phase-II initial pool mutation")
    if loop_summary.get("baseline_dynamic_columns_mutated") is not False:
        blockers.append("bounded Phase-II loop reports baseline mutation")
    if loop_summary.get("full_assignment_run") is not False or loop_summary.get("full_cg_run") is not False:
        blockers.append("bounded Phase-II loop unexpectedly reports full assignment or full CG")
    if closure_summary.get("diagnostic_status") != "PASS":
        blockers.append(f"fixed-source closure status changed: {closure_summary.get('diagnostic_status')}")
    if (
        not ALLOW_VARIABLE_FIXED_SOURCE_BASE
        and abs(parse_float(closure_summary.get("phase2_bounded_loop_final_objective"), math.inf) - EXPECTED_OBJECTIVE_BEFORE) > 1e-5
    ):
        blockers.append(
            "fixed-source closure objective changed: "
            f"{closure_summary.get('phase2_bounded_loop_final_objective')}"
        )
    if closure_summary.get("fixed_source_exhausted") is not True:
        blockers.append("fixed-source closure no longer reports fixed-source exhaustion")
    return blockers


def validate_candidate(
    probe: dict[str, str] | None,
    comparison: dict[str, str] | None,
    base_pool: list[dict[str, str]],
    arcs: list[dict[str, str]],
) -> tuple[dict[str, Any], list[str]]:
    blockers: list[str] = []
    if probe is None:
        blockers.append("selected oracle probe row is missing")
        probe = {}
    if comparison is None and not ALLOW_VARIABLE_ORACLE_CANDIDATE:
        blockers.append("ORACLE_PROBE_D4 comparison row is missing")
        comparison = {}

    entry_signal = parse_float(probe.get("oracle_entry_signal"), math.nan)
    reconstructed_cost = parse_float(probe.get("reconstructed_generalized_cost"), math.nan)
    arc_sequence = probe.get("arc_sequence") if ALLOW_VARIABLE_ORACLE_CANDIDATE else EXPECTED_ARC_SEQUENCE
    arc_ids = {row.get("arc_id", "") for row in arcs}
    missing_arcs = [arc_id for arc_id in split_sequence(arc_sequence or "") if arc_id not in arc_ids]
    duplicate_rows = [
        row
        for row in base_pool
        if row.get("demand_id") == probe.get("demand_id") and row.get("arc_sequence") == arc_sequence
    ]

    checks = {
        "demand_id_is_D4": ALLOW_VARIABLE_ORACLE_CANDIDATE or probe.get("demand_id") == "D4",
        "classification_is_new_oracle_candidate": probe.get("classification") == "new_oracle_candidate",
        "entry_signal_matches_precheck": (ALLOW_VARIABLE_ORACLE_CANDIDATE and entry_signal < -TOL)
        or abs(entry_signal - EXPECTED_ENTRY_SIGNAL) <= 1e-7,
        "arc_sequence_matches_expected": ALLOW_VARIABLE_ORACLE_CANDIDATE
        or probe.get("arc_sequence") == EXPECTED_ARC_SEQUENCE,
        "diagnostic_only": probe.get("diagnostic_only") == "true",
        "not_marked_for_addition_in_precheck": probe.get("would_be_added_in_future_task") == "false",
        "nonduplicate_against_final_pool": not duplicate_rows,
        "all_arcs_exist": not missing_arcs,
        "reconstructed_generalized_cost_available": math.isfinite(reconstructed_cost),
        "comparison_candidate_id_matches": ALLOW_VARIABLE_ORACLE_CANDIDATE
        or comparison.get("candidate_id") == SELECTED_CANDIDATE_ID,
        "comparison_status_passes": ALLOW_VARIABLE_ORACLE_CANDIDATE
        or comparison.get("comparison_status") == "PASS",
        "comparison_nonduplicate": ALLOW_VARIABLE_ORACLE_CANDIDATE
        or comparison.get("duplicate_existing_phase2_final_column") == "false",
    }
    blockers.extend(name for name, passed in checks.items() if not passed)
    validation = {
        "candidate_validation_status": "PASS" if not blockers else "SAFE_BLOCKED",
        "selected_candidate_id": SELECTED_CANDIDATE_ID,
        "selected_candidate_demand": probe.get("demand_id"),
        "selected_candidate_entry_signal_from_oracle_precheck": entry_signal,
        "expected_arc_sequence": arc_sequence,
        "actual_arc_sequence": probe.get("arc_sequence"),
        "reconstructed_generalized_cost": reconstructed_cost if math.isfinite(reconstructed_cost) else None,
        "missing_dynamic_arc_count": len(missing_arcs),
        "missing_dynamic_arcs": "|".join(missing_arcs),
        "duplicate_against_final_pool_count": len(duplicate_rows),
        "checks": checks,
        "safe_blockers": blockers,
        "oracle_probe_row": probe,
        "oracle_comparison_row": comparison,
    }
    return validation, blockers


def parse_node_id(node_time_id: str) -> str:
    if node_time_id.startswith("source_") or node_time_id.startswith("sink_"):
        return ""
    if node_time_id.startswith("n") and "_t" in node_time_id:
        return node_time_id[1:].split("_t", 1)[0]
    return ""


def build_sequence_metadata(arc_sequence: str, arc_by_id: dict[str, dict[str, str]]) -> dict[str, str]:
    physical_nodes: list[str] = []
    physical_links: list[str] = []
    times: list[str] = []
    arrival_time = ""
    for arc_id in split_sequence(arc_sequence):
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


def build_oracle_candidate_row(
    probe: dict[str, str],
    demands: list[dict[str, str]],
    arcs: list[dict[str, str]],
) -> dict[str, str]:
    demand_id = probe.get("demand_id", "")
    arc_sequence = probe.get("arc_sequence", EXPECTED_ARC_SEQUENCE)
    demand = next(row for row in demands if row.get("demand_id") == demand_id)
    arc_by_id = {row.get("arc_id", ""): row for row in arcs}
    metadata = build_sequence_metadata(arc_sequence, arc_by_id)
    departure = demand.get("departure_time", "")
    arrival = metadata["arrival_time"]
    travel_time = ""
    if arrival != "":
        travel_time = str(parse_float(arrival, 0.0) - parse_float(departure, 0.0))
    return {
        "column_id": SELECTED_CANDIDATE_ID,
        "path_id": SELECTED_CANDIDATE_ID,
        "demand_id": demand_id,
        "origin_node_id": demand.get("origin_node_id", ""),
        "destination_node_id": demand.get("destination_node_id", ""),
        "departure_time": departure,
        "arrival_time": arrival,
        "travel_time": travel_time,
        "generalized_cost": str(parse_float(probe.get("reconstructed_generalized_cost"), math.nan)),
        "node_sequence": metadata["node_sequence"],
        "link_sequence": metadata["link_sequence"],
        "time_sequence": metadata["time_sequence"],
        "arc_sequence": arc_sequence,
        "phase2_pool_column_type": "phase2_oracle_round1_added_candidate",
        "source_metadata": rel(ORACLE_PRECHECK_DIR / "phase2_oracle_shortest_path_probe.csv"),
        "added_in_phase1_round": "",
        "phase1_final_flow": "",
        "written_to_baseline_dynamic_columns": "false",
        "output_only_phase2_initial_pool": "false",
        "output_only_phase2_loop_pool": "false",
        "output_only_phase2_oracle_round1_pool": "true",
        "pool_membership": "oracle_round1_added_candidate",
        "candidate_source": rel(ORACLE_PRECHECK_DIR / "phase2_oracle_shortest_path_probe.csv"),
        "added_in_phase2_round": "oracle_round_1",
        "oracle_entry_signal_from_precheck": str(parse_float(probe.get("oracle_entry_signal"), math.nan)),
        "written_to_phase2_initial_pool": "false",
        "written_to_fixed_source_outputs": "false",
    }


def build_round1_pool(
    base_pool: list[dict[str, str]],
    probe: dict[str, str],
    demands: list[dict[str, str]],
    arcs: list[dict[str, str]],
) -> list[dict[str, str]]:
    pool: list[dict[str, str]] = []
    for row in base_pool:
        copy = dict(row)
        copy["output_only_phase2_oracle_round1_pool"] = "true"
        copy["pool_membership"] = copy.get("pool_membership") or "fixed_source_final_pool_column"
        copy["oracle_entry_signal_from_precheck"] = ""
        copy["written_to_fixed_source_outputs"] = "false"
        copy["written_to_phase2_initial_pool"] = "false"
        pool.append(copy)
    pool.append(build_oracle_candidate_row(probe, demands, arcs))
    return pool


def oracle_round1_column_rows(pool: list[dict[str, str]]) -> list[dict[str, Any]]:
    field_defaults = {
        "output_only_phase2_oracle_round1_pool": "true",
        "written_to_fixed_source_outputs": "false",
        "written_to_phase2_initial_pool": "false",
        "written_to_baseline_dynamic_columns": "false",
    }
    rows: list[dict[str, Any]] = []
    for row in pool:
        out = {
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
            "written_to_baseline_dynamic_columns": row.get("written_to_baseline_dynamic_columns", ""),
            "output_only_phase2_initial_pool": row.get("output_only_phase2_initial_pool", ""),
            "output_only_phase2_loop_pool": row.get("output_only_phase2_loop_pool", ""),
            "output_only_phase2_oracle_round1_pool": row.get("output_only_phase2_oracle_round1_pool", ""),
            "pool_membership": row.get("pool_membership", ""),
            "candidate_source": row.get("candidate_source", ""),
            "added_in_phase2_round": row.get("added_in_phase2_round", ""),
            "oracle_entry_signal_from_precheck": row.get("oracle_entry_signal_from_precheck", ""),
            "written_to_phase2_initial_pool": row.get("written_to_phase2_initial_pool", ""),
            "written_to_fixed_source_outputs": row.get("written_to_fixed_source_outputs", ""),
        }
        for key, default in field_defaults.items():
            if out.get(key) == "":
                out[key] = default
        rows.append(out)
    return rows


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


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# One-Candidate Oracle Add-Resolve Diagnostic",
        "",
        SCOPE_BOUNDARY,
        "",
        "## Summary",
        "",
        f"- Diagnostic status: {summary['diagnostic_status']}",
        f"- Selected oracle candidate: {summary['selected_candidate_id']} ({summary['selected_candidate_demand']})",
        f"- Solver status before: {summary['solver_status_before']}",
        f"- Solver status after: {summary['solver_status_after']}",
        f"- Objective before: {summary['objective_before']}",
        f"- Objective after: {summary['objective_after']}",
        f"- Objective change: {summary['objective_change']}",
        f"- Objective decreased: {summary['objective_decreased']}",
        f"- Selected candidate flow after resolve: {summary['selected_candidate_primal_flow_after_resolve']}",
        f"- Demand residual max after: {summary['demand_residual_max_after']}",
        f"- Capacity violation count after: {summary['capacity_violation_count_after']}",
        "",
        "## Scope Guardrails",
        "",
        f"- Phase-II initial pool mutated: {summary['phase2_initial_pool_mutated']}",
        f"- Baseline dynamic_columns.csv mutated: {summary['baseline_dynamic_columns_mutated']}",
        f"- Fixed-source outputs mutated: {summary['fixed_source_outputs_mutated']}",
        f"- Oracle candidate added to temporary pool: {summary['oracle_candidate_added_to_temporary_pool']}",
        f"- Candidate columns added to temporary pool: {summary['candidate_columns_added_to_temporary_pool']}",
        f"- Oracle pricing rerun after resolve: {summary['oracle_pricing_rerun_after_resolve']}",
        f"- Second candidate added: {summary['second_candidate_added']}",
        f"- CG loop run: {summary['cg_loop_run']}",
        f"- Full assignment run: {summary['full_assignment_run']}",
        f"- Full CG run: {summary['full_cg_run']}",
        "",
        "## Interpretation",
        "",
        (
            "One-candidate oracle add-resolve diagnostic succeeded."
            if summary.get("diagnostic_status") == "PASS" and summary.get("objective_decreased") is True
            else "The diagnostic is safely blocked or did not pass the objective/feasibility gates."
        ),
        "",
        "## Next Safe Step",
        "",
        summary.get("next_safe_step", ""),
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_outputs(
    output_dir: Path,
    summary: dict[str, Any],
    validation: dict[str, Any],
    hash_audit: dict[str, Any],
    pool: list[dict[str, str]],
    solution_outputs: dict[str, Any],
    dual_solution: dict[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "phase2_oracle_one_candidate_add_resolve_summary.json", summary)
    write_report(output_dir / "phase2_oracle_one_candidate_add_resolve_report.md", summary)
    write_csv(
        output_dir / "phase2_oracle_round1_columns.csv",
        oracle_round1_column_rows(pool),
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
            "output_only_phase2_oracle_round1_pool",
            "pool_membership",
            "candidate_source",
            "added_in_phase2_round",
            "oracle_entry_signal_from_precheck",
            "written_to_phase2_initial_pool",
            "written_to_fixed_source_outputs",
        ],
    )
    write_csv(
        output_dir / "phase2_oracle_round1_solution_by_column.csv",
        solution_outputs.get("solution_by_column", []),
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
        output_dir / "phase2_oracle_round1_demand_balance.csv",
        solution_outputs.get("demand_balance", []),
        ["demand_id", "demand_volume", "real_column_flow", "demand_residual", "status"],
    )
    write_csv(
        output_dir / "phase2_oracle_round1_capacity_usage.csv",
        solution_outputs.get("capacity_usage", []),
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
        output_dir / "phase2_oracle_round1_cost_breakdown.csv",
        solution_outputs.get("cost_breakdown", []),
        ["breakdown_id", "demand_id", "cost_field_used", "flow", "objective_contribution", "scope"],
    )
    write_json(output_dir / "phase2_oracle_round1_dual_solution.json", dual_solution)
    write_json(output_dir / "phase2_oracle_round1_candidate_validation.json", validation)
    write_csv(
        output_dir / "phase2_oracle_round1_comparison.csv",
        [
            {
                "metric": "objective",
                "before": summary.get("objective_before"),
                "after": summary.get("objective_after"),
                "change": summary.get("objective_change"),
            },
            {
                "metric": "selected_candidate_flow",
                "before": 0.0,
                "after": summary.get("selected_candidate_primal_flow_after_resolve"),
                "change": summary.get("selected_candidate_primal_flow_after_resolve"),
            },
            {
                "metric": "demand_residual_max",
                "before": 0.0,
                "after": summary.get("demand_residual_max_after"),
                "change": summary.get("demand_residual_max_after"),
            },
            {
                "metric": "capacity_violation_count",
                "before": 0,
                "after": summary.get("capacity_violation_count_after"),
                "change": summary.get("capacity_violation_count_after"),
            },
        ],
        ["metric", "before", "after", "change"],
    )
    write_json(output_dir / "phase2_oracle_round1_hash_audit.json", hash_audit)


def safe_blocker_summary(
    blockers: list[str],
    closure_summary: dict[str, Any],
    validation: dict[str, Any],
    baseline_hash_before: str,
    baseline_hash_after: str,
    phase2_initial_hash_before: str,
    phase2_initial_hash_after: str,
    fixed_hashes_before: dict[str, str],
    fixed_hashes_after: dict[str, str],
) -> dict[str, Any]:
    fixed_mutated = fixed_hashes_before != fixed_hashes_after
    return {
        "diagnostic_status": "SAFE_BLOCKED",
        "selected_candidate_id": SELECTED_CANDIDATE_ID,
        "selected_candidate_demand": validation.get("selected_candidate_demand"),
        "selected_candidate_entry_signal_from_oracle_precheck": validation.get(
            "selected_candidate_entry_signal_from_oracle_precheck"
        ),
        "solver_status_before": "optimal" if closure_summary.get("diagnostic_status") == "PASS" else "not_confirmed",
        "solver_status_after": "not_run",
        "objective_before": closure_summary.get("phase2_bounded_loop_final_objective"),
        "objective_after": None,
        "objective_change": None,
        "objective_decreased": False,
        "selected_candidate_primal_flow_after_resolve": None,
        "demand_residual_max_after": None,
        "capacity_violation_count_after": None,
        "max_capacity_violation_after": None,
        "positive_flow_column_count_after": None,
        "phase2_initial_pool_hash_before": phase2_initial_hash_before,
        "phase2_initial_pool_hash_after": phase2_initial_hash_after,
        "phase2_initial_pool_mutated": phase2_initial_hash_before != phase2_initial_hash_after,
        "baseline_dynamic_columns_hash_before": baseline_hash_before,
        "baseline_dynamic_columns_hash_after": baseline_hash_after,
        "baseline_dynamic_columns_mutated": baseline_hash_before != baseline_hash_after,
        "fixed_source_outputs_hash_before": fixed_hashes_before,
        "fixed_source_outputs_hash_after": fixed_hashes_after,
        "fixed_source_outputs_mutated": fixed_mutated,
        "oracle_candidate_added_to_temporary_pool": False,
        "candidate_columns_added_to_temporary_pool": 0,
        "allow_variable_fixed_source_base": ALLOW_VARIABLE_FIXED_SOURCE_BASE,
        "allow_variable_oracle_candidate": ALLOW_VARIABLE_ORACLE_CANDIDATE,
        "use_best_new_oracle_candidate_from_precheck": USE_BEST_NEW_ORACLE_CANDIDATE_FROM_PRECHECK,
        "selected_candidate_written_to_phase2_initial_pool": False,
        "selected_candidate_written_to_baseline": False,
        "oracle_pricing_rerun_after_resolve": False,
        "second_candidate_added": False,
        "add_resolve_run": False,
        "rmp_resolve_count_after_oracle_candidate_add": 0,
        "cg_loop_run": False,
        "full_assignment_run": False,
        "full_cg_run": False,
        "general_convergence_claimed": False,
        "exact_arc_lp_flow_pattern_reproduction_claimed": False,
        "safe_blockers": blockers,
        "scope": SCOPE_BOUNDARY,
        "next_safe_step": "resolve one-candidate oracle add-resolve safe blockers before any loop",
    }


def run_add_resolve(
    config_path: str | Path = DEFAULT_CURRENT_POOL_CONFIG,
    output_dir: Path = OUTPUT_DIR,
) -> dict[str, Any]:
    global SELECTED_CANDIDATE_ID
    output_dir.mkdir(parents=True, exist_ok=True)
    config = load_config(config_path)
    data_dir = input_data_dir(config)
    baseline_path = data_dir / "dynamic_columns.csv"
    baseline_hash_before = sha256_file(baseline_path)
    phase2_initial_hash_before = sha256_file(PHASE2_INITIAL_POOL) if PHASE2_INITIAL_POOL.exists() else ""
    fixed_hashes_before = fixed_source_output_hashes()

    blockers = required_input_blockers()
    oracle_summary = read_json(ORACLE_PRECHECK_DIR / "phase2_pricing_oracle_precheck_summary.json") if not blockers else {}
    oracle_hash = read_json(ORACLE_PRECHECK_DIR / "phase2_oracle_hash_audit.json") if not blockers else {}
    loop_summary = read_json(LOOP_DIR / "phase2_bounded_loop_summary.json") if not blockers else {}
    closure_summary = read_json(CLOSURE_DIR / "phase2_fixed_source_closure_summary.json") if not blockers else {}
    probe_rows = read_csv_rows(ORACLE_PRECHECK_DIR / "phase2_oracle_shortest_path_probe.csv") if not blockers else []
    comparison_rows = (
        read_csv_rows(ORACLE_PRECHECK_DIR / "phase2_oracle_known_candidate_comparison.csv") if not blockers else []
    )
    base_pool = read_csv_rows(FIXED_SOURCE_FINAL_POOL) if FIXED_SOURCE_FINAL_POOL.exists() else []
    arcs = read_csv_rows(data_dir / "dynamic_arc.csv") if data_dir.exists() else []
    demands = read_csv_rows(data_dir / "dynamic_demand.csv") if data_dir.exists() else []

    selected_probe = find_probe_row(probe_rows)
    if USE_BEST_NEW_ORACLE_CANDIDATE_FROM_PRECHECK and selected_probe is not None:
        SELECTED_CANDIDATE_ID = f"ORACLE_PROBE_{selected_probe.get('demand_id', 'UNKNOWN')}"
    selected_comparison = find_comparison_row(comparison_rows)
    validation, validation_blockers = validate_candidate(selected_probe, selected_comparison, base_pool, arcs)

    if not blockers:
        blockers.extend(oracle_precheck_blockers(oracle_summary, oracle_hash))
        blockers.extend(fixed_source_blockers(loop_summary, closure_summary))
        if not ALLOW_VARIABLE_FIXED_SOURCE_BASE and len(base_pool) != EXPECTED_BASE_POOL_COUNT:
            blockers.append(f"fixed-source final pool has {len(base_pool)} columns, expected 13")
        if any(
            row.get("column_id", "").startswith("ARTIFICIAL_DEMAND_")
            or "artificial" in row.get("phase2_pool_column_type", "").lower()
            for row in base_pool
        ):
            blockers.append("fixed-source final pool contains artificial variables")
        if baseline_hash_before != ACCEPTED_BASELINE_HASH:
            blockers.append(f"baseline dynamic_columns.csv hash differs from accepted hash: {baseline_hash_before}")
    blockers.extend(validation_blockers)

    pool = base_pool
    solution_outputs = empty_solution_outputs()
    dual_solution: dict[str, Any] = {"dual_fields_present": False, "safe_blockers": blockers}
    solver_info: dict[str, Any] = {
        "solver_status": "not_run",
        "solver_message": "; ".join(blockers),
        "objective_value": None,
    }
    rmp_resolved = False

    if not blockers and selected_probe is not None:
        pool = build_round1_pool(base_pool, selected_probe, demands, arcs)
        cost_field, costs, cost_blockers = choose_cost_field(pool)
        if cost_blockers:
            blockers.extend(cost_blockers)
        elif not ALLOW_VARIABLE_FIXED_SOURCE_BASE and len(pool) != ROUND1_POOL_COUNT:
            blockers.append(f"temporary oracle round-1 pool has {len(pool)} columns, expected 14")
        else:
            solver_info, result, solve_blockers = solve_phase2_rmp(arcs, demands, pool, costs)
            rmp_resolved = True
            if solve_blockers or result is None or not getattr(result, "success", False):
                blockers.extend(solve_blockers or [f"oracle round-1 Phase-II RMP solve failed: {solver_info.get('solver_status')}"])
            else:
                values = [float(value) for value in result.x]
                solution_outputs = build_solution_outputs(arcs, demands, pool, costs, values, cost_field)
                dual_solution = build_dual_solution(result, arcs, demands, pool)

    baseline_hash_after = sha256_file(baseline_path)
    phase2_initial_hash_after = sha256_file(PHASE2_INITIAL_POOL) if PHASE2_INITIAL_POOL.exists() else phase2_initial_hash_before
    fixed_hashes_after = fixed_source_output_hashes()
    if baseline_hash_before != baseline_hash_after:
        blockers.append("baseline dynamic_columns.csv hash changed during diagnostic")
    if phase2_initial_hash_before != phase2_initial_hash_after:
        blockers.append("Phase-II initial pool hash changed during diagnostic")
    if fixed_hashes_before != fixed_hashes_after:
        blockers.append("accepted fixed-source output hash changed during diagnostic")

    objective_before = parse_float(closure_summary.get("phase2_bounded_loop_final_objective"), math.nan)
    objective_after = parse_float(solver_info.get("objective_value"), math.nan)
    objective_change = objective_after - objective_before if math.isfinite(objective_after) and math.isfinite(objective_before) else None
    objective_decreased = objective_change is not None and objective_change < -TOL
    selected_flow = 0.0
    for row in solution_outputs.get("solution_by_column", []):
        if row.get("column_id") == SELECTED_CANDIDATE_ID:
            selected_flow = parse_float(row.get("flow"), 0.0)
            break

    if (
        not blockers
        and (
            solver_info.get("solver_status") != "optimal"
            or (
                not ALLOW_VARIABLE_FIXED_SOURCE_BASE
                and abs(objective_before - EXPECTED_OBJECTIVE_BEFORE) > 1e-5
            )
            or not objective_decreased
            or selected_flow <= TOL
            or parse_float(solution_outputs.get("demand_residual_max"), math.inf) > TOL
            or int(
                solution_outputs.get("capacity_violation_count")
                if solution_outputs.get("capacity_violation_count") is not None
                else -1
            )
            != 0
            or parse_float(solution_outputs.get("max_capacity_violation"), math.inf) > TOL
        )
    ):
        blockers.append("one-candidate oracle add-resolve did not meet objective/feasibility success gates")

    if blockers:
        summary = safe_blocker_summary(
            blockers,
            closure_summary,
            validation,
            baseline_hash_before,
            baseline_hash_after,
            phase2_initial_hash_before,
            phase2_initial_hash_after,
            fixed_hashes_before,
            fixed_hashes_after,
        )
        if rmp_resolved:
            summary.update(
                {
                    "solver_status_after": solver_info.get("solver_status"),
                    "objective_after": solver_info.get("objective_value"),
                    "objective_change": objective_change,
                    "objective_decreased": objective_decreased,
                    "selected_candidate_primal_flow_after_resolve": selected_flow,
                    "demand_residual_max_after": solution_outputs.get("demand_residual_max"),
                    "capacity_violation_count_after": solution_outputs.get("capacity_violation_count"),
                    "max_capacity_violation_after": solution_outputs.get("max_capacity_violation"),
                    "positive_flow_column_count_after": solution_outputs.get("positive_flow_column_count"),
                    "oracle_candidate_added_to_temporary_pool": selected_probe is not None,
                    "candidate_columns_added_to_temporary_pool": 1 if selected_probe is not None else 0,
                    "add_resolve_run": True,
                    "rmp_resolve_count_after_oracle_candidate_add": 1,
                }
            )
    else:
        summary = {
            "diagnostic_status": "PASS",
            "selected_candidate_id": SELECTED_CANDIDATE_ID,
            "selected_candidate_demand": validation.get("selected_candidate_demand"),
            "selected_candidate_entry_signal_from_oracle_precheck": validation.get(
                "selected_candidate_entry_signal_from_oracle_precheck"
            ),
            "solver_status_before": "optimal",
            "solver_status_after": solver_info.get("solver_status"),
            "solver_message_after": solver_info.get("solver_message"),
            "objective_before": objective_before,
            "objective_after": objective_after,
            "objective_change": objective_change,
            "objective_decreased": objective_decreased,
            "selected_candidate_primal_flow_after_resolve": selected_flow,
            "demand_residual_max_after": solution_outputs.get("demand_residual_max"),
            "capacity_violation_count_after": solution_outputs.get("capacity_violation_count"),
            "max_capacity_violation_after": solution_outputs.get("max_capacity_violation"),
            "positive_flow_column_count_after": solution_outputs.get("positive_flow_column_count"),
            "phase2_initial_pool_hash_before": phase2_initial_hash_before,
            "phase2_initial_pool_hash_after": phase2_initial_hash_after,
            "phase2_initial_pool_mutated": phase2_initial_hash_before != phase2_initial_hash_after,
            "baseline_dynamic_columns_hash_before": baseline_hash_before,
            "baseline_dynamic_columns_hash_after": baseline_hash_after,
            "baseline_dynamic_columns_mutated": baseline_hash_before != baseline_hash_after,
            "fixed_source_outputs_hash_before": fixed_hashes_before,
            "fixed_source_outputs_hash_after": fixed_hashes_after,
            "fixed_source_outputs_mutated": fixed_hashes_before != fixed_hashes_after,
            "oracle_candidate_added_to_temporary_pool": True,
            "candidate_columns_added_to_temporary_pool": 1,
            "allow_variable_fixed_source_base": ALLOW_VARIABLE_FIXED_SOURCE_BASE,
            "allow_variable_oracle_candidate": ALLOW_VARIABLE_ORACLE_CANDIDATE,
            "use_best_new_oracle_candidate_from_precheck": USE_BEST_NEW_ORACLE_CANDIDATE_FROM_PRECHECK,
            "selected_candidate_written_to_phase2_initial_pool": False,
            "selected_candidate_written_to_baseline": False,
            "oracle_pricing_rerun_after_resolve": False,
            "second_candidate_added": False,
            "add_resolve_run": True,
            "rmp_resolve_count_after_oracle_candidate_add": 1,
            "cg_loop_run": False,
            "full_assignment_run": False,
            "full_cg_run": False,
            "general_convergence_claimed": False,
            "exact_arc_lp_flow_pattern_reproduction_claimed": False,
            "safe_blockers": [],
            "scope": SCOPE_BOUNDARY,
            "next_safe_step": "bounded oracle Phase-II loop diagnostic"
            if objective_decreased
            else "investigate oracle reduced-cost/add-resolve mismatch before loop",
        }

    hash_audit = {
        "baseline_dynamic_columns_path": rel(baseline_path),
        "baseline_dynamic_columns_hash_before": baseline_hash_before,
        "baseline_dynamic_columns_hash_after": baseline_hash_after,
        "accepted_baseline_dynamic_columns_hash": ACCEPTED_BASELINE_HASH,
        "baseline_dynamic_columns_mutated": baseline_hash_before != baseline_hash_after,
        "phase2_initial_pool_path": rel(PHASE2_INITIAL_POOL),
        "phase2_initial_pool_hash_before": phase2_initial_hash_before,
        "phase2_initial_pool_hash_after": phase2_initial_hash_after,
        "phase2_initial_pool_mutated": phase2_initial_hash_before != phase2_initial_hash_after,
        "fixed_source_outputs_hash_before": fixed_hashes_before,
        "fixed_source_outputs_hash_after": fixed_hashes_after,
        "fixed_source_outputs_mutated": fixed_hashes_before != fixed_hashes_after,
        "temporary_oracle_round1_column_pool_path": rel(output_dir / "phase2_oracle_round1_columns.csv"),
        "allow_variable_fixed_source_base": ALLOW_VARIABLE_FIXED_SOURCE_BASE,
        "allow_variable_oracle_candidate": ALLOW_VARIABLE_ORACLE_CANDIDATE,
        "use_best_new_oracle_candidate_from_precheck": USE_BEST_NEW_ORACLE_CANDIDATE_FROM_PRECHECK,
        "selected_candidate_written_to_phase2_initial_pool": False,
        "selected_candidate_written_to_baseline": False,
        "oracle_pricing_rerun_after_resolve": False,
        "second_candidate_added": False,
        "cg_loop_run": False,
        "full_assignment_run": False,
        "full_cg_run": False,
    }
    validation["baseline_dynamic_columns_hash_before"] = baseline_hash_before
    validation["baseline_dynamic_columns_hash_after"] = baseline_hash_after
    validation["phase2_initial_pool_hash_before"] = phase2_initial_hash_before
    validation["phase2_initial_pool_hash_after"] = phase2_initial_hash_after
    validation["fixed_source_outputs_hash_before"] = fixed_hashes_before
    validation["fixed_source_outputs_hash_after"] = fixed_hashes_after
    validation["baseline_dynamic_columns_mutated"] = baseline_hash_before != baseline_hash_after
    validation["phase2_initial_pool_mutated"] = phase2_initial_hash_before != phase2_initial_hash_after
    validation["fixed_source_outputs_mutated"] = fixed_hashes_before != fixed_hashes_after
    write_outputs(output_dir, summary, validation, hash_audit, pool, solution_outputs, dual_solution)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one-candidate oracle Phase-II add-resolve diagnostic.")
    parser.add_argument("--config", default=DEFAULT_CURRENT_POOL_CONFIG)
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--input-artifacts-json", default=None)
    parser.add_argument("--benchmark-id", default="second_controlled_benchmark_link55")
    parser.add_argument("--no-mutate-accepted-outputs", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.benchmark_id != "second_controlled_benchmark_link55":
        print(f"Unsupported benchmark id: {args.benchmark_id}")
        return 1
    apply_input_manifest(args.input_artifacts_json)
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = ROOT_DIR / output_dir
    if args.no_mutate_accepted_outputs and output_dir.resolve() == OUTPUT_DIR.resolve():
        print("Refusing to write to accepted default oracle one-candidate folder with --no-mutate-accepted-outputs.")
        return 1
    summary = run_add_resolve(args.config, output_dir)
    print(f"One-candidate oracle add-resolve diagnostic status: {summary['diagnostic_status']}")
    print(f"Selected candidate: {summary['selected_candidate_id']}")
    print(f"Solver status before: {summary['solver_status_before']}")
    print(f"Solver status after: {summary['solver_status_after']}")
    print(f"Objective before: {summary['objective_before']}")
    print(f"Objective after: {summary['objective_after']}")
    print(f"Objective change: {summary['objective_change']}")
    print(f"Objective decreased: {summary['objective_decreased']}")
    print(f"Selected candidate flow after resolve: {summary['selected_candidate_primal_flow_after_resolve']}")
    print(f"Demand residual max after: {summary['demand_residual_max_after']}")
    print(f"Capacity violation count after: {summary['capacity_violation_count_after']}")
    print(f"Phase-II initial pool mutated: {summary['phase2_initial_pool_mutated']}")
    print(f"Baseline dynamic_columns.csv mutated: {summary['baseline_dynamic_columns_mutated']}")
    print(f"Fixed-source outputs mutated: {summary['fixed_source_outputs_mutated']}")
    print(f"Oracle pricing rerun after resolve: {summary['oracle_pricing_rerun_after_resolve']}")
    print(f"CG loop run: {summary['cg_loop_run']}")
    print(f"Full CG run: {summary['full_cg_run']}")
    print(f"Report: {output_dir / 'phase2_oracle_one_candidate_add_resolve_report.md'}")
    return 0 if summary["diagnostic_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
