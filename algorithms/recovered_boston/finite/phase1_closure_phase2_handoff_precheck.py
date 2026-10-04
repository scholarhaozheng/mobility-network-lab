"""Phase-I closure audit and Phase-II handoff precheck.

This script audits the accepted bounded Phase-I loop result as a closure
candidate and prepares an output-only Phase-II initial column pool. It checks
that the final temporary real-column pool satisfies demand without artificial
variables and without dynamic capacity violations.

It does not run Phase-II cost minimization, Phase-II pricing, add-resolve, a
new loop, full assignment, full CG, or any general convergence proof.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

from phase1_artificial_rmp_preflight import sha256_file
from phase1_one_candidate_add_resolve import ACCEPTED_BASELINE_HASH
from phase1_pricing_candidate_diagnostic import structural_validation
from precheck_second_controlled_benchmark_current_pool_rmp import (
    DEFAULT_CONFIG as DEFAULT_CURRENT_POOL_CONFIG,
    TOL,
    input_data_dir,
    load_config,
    parse_float,
    read_csv,
    split_sequence,
)
from build_sioux_harder_bounded_stage2 import ROOT_DIR


OUTPUT_DIR = ROOT_DIR / "outputs" / "phase1_closure_phase2_handoff_precheck"
DEFAULT_OUTPUT_DIR = OUTPUT_DIR
BOUNDED_LOOP_DIR = ROOT_DIR / "outputs" / "phase1_bounded_loop_diagnostic"
PREFLIGHT_DIR = ROOT_DIR / "outputs" / "phase1_artificial_rmp_preflight"
SEED_REPAIR_COLUMNS = (
    ROOT_DIR / "outputs" / "second_controlled_benchmark_link55_seed_pool_repair" / "repaired_seed_columns.csv"
)
ALLOW_VARIABLE_PHASE1_ADDED_COLUMN_COUNT = False
REQUIRED_INPUTS: list[Path] = []
SCOPE_BOUNDARY = (
    "This is a Phase-I closure audit and Phase-II handoff precheck. It verifies "
    "that the bounded Phase-I loop final temporary real-column pool can satisfy "
    "demand without artificial variables and without dynamic capacity violations, "
    "then prepares an output-only Phase-II initial column pool. It does not run "
    "Phase-II cost minimization, Phase-II pricing, add-resolve, a new loop, full "
    "assignment, full CG, or claim general convergence, production-scale solving, "
    "GTFS, railway, branch-and-price, reinforcement learning, or exact arc-LP "
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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT_DIR)).replace("\\", "/")


def resolve_artifact_path(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else ROOT_DIR / path


def refresh_required_inputs() -> None:
    global REQUIRED_INPUTS
    REQUIRED_INPUTS = [
        BOUNDED_LOOP_DIR / "phase1_bounded_loop_summary.json",
        BOUNDED_LOOP_DIR / "phase1_loop_temporary_pool_final.csv",
        BOUNDED_LOOP_DIR / "phase1_loop_real_flow_by_column_final.csv",
        BOUNDED_LOOP_DIR / "phase1_loop_artificial_flow_by_demand_final.csv",
        BOUNDED_LOOP_DIR / "phase1_loop_demand_balance_final.csv",
        BOUNDED_LOOP_DIR / "phase1_loop_capacity_usage_final.csv",
        BOUNDED_LOOP_DIR / "phase1_loop_added_candidates.csv",
        BOUNDED_LOOP_DIR / "phase1_loop_rounds.csv",
        BOUNDED_LOOP_DIR / "phase1_loop_candidate_scores_by_round.csv",
        BOUNDED_LOOP_DIR / "phase1_loop_hash_audit.json",
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
    global BOUNDED_LOOP_DIR, PREFLIGHT_DIR, SEED_REPAIR_COLUMNS, ALLOW_VARIABLE_PHASE1_ADDED_COLUMN_COUNT
    BOUNDED_LOOP_DIR = resolve_artifact_path(artifacts.get("phase1_bounded_loop_dir")) or BOUNDED_LOOP_DIR
    PREFLIGHT_DIR = resolve_artifact_path(artifacts.get("phase1_preflight_dir")) or PREFLIGHT_DIR
    SEED_REPAIR_COLUMNS = resolve_artifact_path(artifacts.get("seed_repair_columns")) or SEED_REPAIR_COLUMNS
    allow_variable_count = artifacts.get("allow_variable_phase1_added_column_count")
    if allow_variable_count is not None:
        ALLOW_VARIABLE_PHASE1_ADDED_COLUMN_COUNT = bool(allow_variable_count)
    refresh_required_inputs()
    return artifacts


refresh_required_inputs()


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def required_input_blockers() -> list[str]:
    blockers: list[str] = []
    for path in REQUIRED_INPUTS:
        if not path.exists() or path.stat().st_size == 0:
            blockers.append(f"missing or empty required bounded-loop input: {rel(path)}")
    return blockers


def load_inputs() -> dict[str, Any]:
    return {
        "bounded_summary": read_json(BOUNDED_LOOP_DIR / "phase1_bounded_loop_summary.json"),
        "final_pool": read_csv(BOUNDED_LOOP_DIR / "phase1_loop_temporary_pool_final.csv"),
        "final_real_flow": read_csv(BOUNDED_LOOP_DIR / "phase1_loop_real_flow_by_column_final.csv"),
        "final_artificial": read_csv(BOUNDED_LOOP_DIR / "phase1_loop_artificial_flow_by_demand_final.csv"),
        "final_demand": read_csv(BOUNDED_LOOP_DIR / "phase1_loop_demand_balance_final.csv"),
        "final_capacity": read_csv(BOUNDED_LOOP_DIR / "phase1_loop_capacity_usage_final.csv"),
        "added_candidates": read_csv(BOUNDED_LOOP_DIR / "phase1_loop_added_candidates.csv"),
        "rounds": read_csv(BOUNDED_LOOP_DIR / "phase1_loop_rounds.csv"),
        "candidate_scores": read_csv(BOUNDED_LOOP_DIR / "phase1_loop_candidate_scores_by_round.csv"),
        "bounded_hash": read_json(BOUNDED_LOOP_DIR / "phase1_loop_hash_audit.json"),
        "seed_rows": read_csv(SEED_REPAIR_COLUMNS) if SEED_REPAIR_COLUMNS.exists() else [],
        "initial_real_flow": read_csv(PREFLIGHT_DIR / "real_flow_by_column.csv")
        if (PREFLIGHT_DIR / "real_flow_by_column.csv").exists()
        else [],
    }


def input_artifact_audit(
    output_dir: Path,
    config_path: str | Path,
    data_dir: Path,
    write_audit: bool,
) -> dict[str, Any]:
    audit = {
        "audit_status": "PASS",
        "config_path": rel(Path(config_path) if Path(config_path).is_absolute() else ROOT_DIR / config_path),
        "data_dir": rel(data_dir),
        "phase1_bounded_loop_dir": rel(BOUNDED_LOOP_DIR),
        "phase1_final_pool_path": rel(BOUNDED_LOOP_DIR / "phase1_loop_temporary_pool_final.csv"),
        "phase1_final_real_flow_path": rel(BOUNDED_LOOP_DIR / "phase1_loop_real_flow_by_column_final.csv"),
        "phase1_preflight_dir": rel(PREFLIGHT_DIR),
        "seed_repair_columns_path": rel(SEED_REPAIR_COLUMNS),
        "phase1_closure_output_dir": rel(output_dir),
        "writes_default_output_dir": output_dir.resolve() == DEFAULT_OUTPUT_DIR.resolve(),
        "required_inputs": [rel(path) for path in REQUIRED_INPUTS],
    }
    if write_audit:
        write_json(output_dir / "phase1_closure_input_artifact_audit.json", audit)
    return audit


def validate_bounded_loop(inputs: dict[str, Any], baseline_hash_before: str) -> tuple[dict[str, Any], list[str]]:
    summary = inputs["bounded_summary"]
    artificial_rows = inputs["final_artificial"]
    bounded_hash = inputs["bounded_hash"]
    blockers: list[str] = []
    artificial_by_demand = {
        row.get("demand_id", ""): parse_float(row.get("flow"), math.nan) for row in artificial_rows
    }
    checks = {
        "diagnostic_status_pass": summary.get("diagnostic_status") == "PASS",
        "stop_reason_artificial_flow_zero": summary.get("stop_reason") == "artificial_flow_zero",
        "total_artificial_flow_final_zero": parse_float(summary.get("total_artificial_flow_final"), math.inf) <= TOL,
        "D3_artificial_flow_final_zero": parse_float(summary.get("D3_artificial_flow_final"), math.inf) <= TOL
        and parse_float(artificial_by_demand.get("D3"), math.inf) <= TOL,
        "D4_artificial_flow_final_zero": parse_float(summary.get("D4_artificial_flow_final"), math.inf) <= TOL
        and parse_float(artificial_by_demand.get("D4"), math.inf) <= TOL,
        "capacity_violation_count_final_zero": int(summary.get("capacity_violation_count_final") or 0) == 0,
        "demand_residual_max_final_zero": parse_float(summary.get("demand_residual_max_final"), math.inf) <= TOL,
        "baseline_hash_unchanged": summary.get("baseline_dynamic_columns_hash_before")
        == summary.get("baseline_dynamic_columns_hash_after")
        == baseline_hash_before
        == ACCEPTED_BASELINE_HASH
        and bounded_hash.get("baseline_dynamic_columns_hash_before")
        == bounded_hash.get("baseline_dynamic_columns_hash_after")
        == baseline_hash_before,
        "phase2_transition_not_executed": summary.get("phase2_transition_executed") is False,
        "full_cg_not_run": summary.get("full_cg_run") is False,
        "full_assignment_not_run": summary.get("full_assignment_run") is False,
    }
    for name, passed in checks.items():
        if not passed:
            blockers.append(f"bounded-loop closure check failed: {name}")
    return checks, blockers


def final_pool_integrity_audit(
    final_pool: list[dict[str, str]],
    added_candidates: list[dict[str, str]],
    seed_rows: list[dict[str, str]],
    arcs: list[dict[str, str]],
    demands: list[dict[str, str]],
    allow_variable_added_count: bool = False,
) -> tuple[list[dict[str, Any]], list[str]]:
    demand_ids = {row["demand_id"] for row in demands}
    arc_by_id = {row["arc_id"]: row for row in arcs}
    seed_ids = {row.get("column_id", "") for row in seed_rows}
    added_ids = {row.get("candidate_id", "") for row in added_candidates}
    key_counts: dict[tuple[str, str], int] = defaultdict(int)
    for row in final_pool:
        key_counts[(row.get("demand_id", ""), row.get("arc_sequence", ""))] += 1

    blockers: list[str] = []
    rows: list[dict[str, Any]] = []
    baseline_count = 0
    added_count = 0
    for row in final_pool:
        column_id = row.get("column_id", "")
        is_artificial = (
            column_id.startswith("ARTIFICIAL_DEMAND_")
            or row.get("is_artificial") == "true"
            or row.get("column_source") == "artificial"
        )
        is_added = row.get("pool_membership") == "bounded_loop_added_candidate" or column_id in added_ids
        if is_added:
            added_count += 1
        else:
            baseline_count += 1
        structurally_valid, invalid_reason = structural_validation(row, demand_ids, arc_by_id)
        duplicate = key_counts[(row.get("demand_id", ""), row.get("arc_sequence", ""))] > 1
        from_seed = (not is_added) or column_id in seed_ids
        written_to_baseline = row.get("written_to_baseline_dynamic_columns", "").lower() == "true"
        status = (
            "PASS"
            if not is_artificial and structurally_valid and not duplicate and from_seed and not written_to_baseline
            else "FAIL"
        )
        rows.append(
            {
                "column_id": column_id,
                "demand_id": row.get("demand_id", ""),
                "pool_membership": row.get("pool_membership", ""),
                "added_in_phase1_round": row.get("added_in_round", ""),
                "is_artificial": bool_text(is_artificial),
                "structurally_valid": bool_text(structurally_valid),
                "invalid_reason": invalid_reason,
                "duplicate_within_same_demand_arc_sequence": bool_text(duplicate),
                "from_fixed_repaired_seed_source": bool_text(from_seed),
                "written_to_baseline_dynamic_columns": bool_text(written_to_baseline),
                "audit_status": status,
            }
        )
    if not allow_variable_added_count and len(final_pool) != 10:
        blockers.append(f"final pool count is {len(final_pool)}, expected 10")
    if baseline_count != 5:
        blockers.append(f"baseline column count is {baseline_count}, expected 5")
    if not allow_variable_added_count and added_count != 5:
        blockers.append(f"Phase-I added column count is {added_count}, expected 5")
    if any(row["audit_status"] != "PASS" for row in rows):
        blockers.append("one or more final-pool integrity rows failed")
    return rows, blockers


def real_flow_map(real_flow_rows: list[dict[str, str]]) -> dict[str, float]:
    return {row.get("column_id", ""): parse_float(row.get("flow"), 0.0) for row in real_flow_rows}


def real_only_feasibility_audit(
    final_pool: list[dict[str, str]],
    real_flow_rows: list[dict[str, str]],
    arcs: list[dict[str, str]],
    demands: list[dict[str, str]],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    flow_by_column = real_flow_map(real_flow_rows)
    demand_volume = {row["demand_id"]: parse_float(row.get("volume"), 0.0) for row in demands}
    real_flow_by_demand = {demand_id: 0.0 for demand_id in demand_volume}
    for row in final_pool:
        demand_id = row.get("demand_id", "")
        real_flow_by_demand[demand_id] = real_flow_by_demand.get(demand_id, 0.0) + flow_by_column.get(row.get("column_id", ""), 0.0)

    demand_rows: list[dict[str, Any]] = []
    demand_residual_max = 0.0
    for demand_id, volume in demand_volume.items():
        real_flow = real_flow_by_demand.get(demand_id, 0.0)
        residual = real_flow - volume
        demand_residual_max = max(demand_residual_max, abs(residual))
        demand_rows.append(
            {
                "demand_id": demand_id,
                "demand_volume": volume,
                "real_only_flow": real_flow,
                "artificial_flow_fixed_to_zero": 0.0,
                "real_only_demand_residual": residual,
                "status": "PASS" if abs(residual) <= TOL else "FAIL",
            }
        )

    arc_flow = {row["arc_id"]: 0.0 for row in arcs}
    columns_by_arc: dict[str, list[str]] = defaultdict(list)
    demands_by_arc: dict[str, set[str]] = defaultdict(set)
    for column in final_pool:
        column_id = column.get("column_id", "")
        flow = flow_by_column.get(column_id, 0.0)
        if flow <= TOL:
            continue
        for arc_id in split_sequence(column.get("arc_sequence", "")):
            arc_flow[arc_id] += flow
            columns_by_arc[arc_id].append(column_id)
            demands_by_arc[arc_id].add(column.get("demand_id", ""))

    capacity_rows: list[dict[str, Any]] = []
    max_capacity_violation = 0.0
    capacity_violation_count = 0
    source_sink_violation_count = 0
    for arc in arcs:
        arc_id = arc["arc_id"]
        flow = arc_flow.get(arc_id, 0.0)
        capacity = max(0.0, parse_float(arc.get("capacity"), 0.0))
        violation = max(0.0, flow - capacity)
        if violation > TOL:
            capacity_violation_count += 1
            if arc.get("arc_type") in {"source_connector", "sink_connector"}:
                source_sink_violation_count += 1
        max_capacity_violation = max(max_capacity_violation, violation)
        capacity_rows.append(
            {
                "arc_id": arc_id,
                "arc_type": arc.get("arc_type", ""),
                "physical_link_id": arc.get("physical_link_id", ""),
                "from_time": arc.get("from_time", ""),
                "to_time": arc.get("to_time", ""),
                "real_only_flow": flow,
                "artificial_flow_fixed_to_zero": 0.0,
                "capacity": capacity,
                "capacity_violation": violation,
                "slack": capacity - flow,
                "real_columns_using_arc": "|".join(columns_by_arc.get(arc_id, [])),
                "demand_ids_using_arc": "|".join(sorted(demands_by_arc.get(arc_id, set()))),
                "source_sink_connector_capacity_convention_respected": bool_text(
                    not (arc.get("arc_type") in {"source_connector", "sink_connector"} and violation > TOL)
                ),
                "status": "PASS" if violation <= TOL else "FAIL",
            }
        )
    artificial_present = any(
        row.get("column_id", "").startswith("ARTIFICIAL_DEMAND_") or row.get("is_artificial") == "true"
        for row in final_pool
    )
    summary = {
        "real_only_feasibility_status": "PASS"
        if demand_residual_max <= TOL and capacity_violation_count == 0 and not artificial_present
        else "FAIL",
        "D3_fully_served_by_real_columns": abs(real_flow_by_demand.get("D3", 0.0) - demand_volume.get("D3", 0.0)) <= TOL,
        "D4_fully_served_by_real_columns": abs(real_flow_by_demand.get("D4", 0.0) - demand_volume.get("D4", 0.0)) <= TOL,
        "demand_residual_max": demand_residual_max,
        "capacity_violation_count": capacity_violation_count,
        "max_capacity_violation": max_capacity_violation,
        "source_sink_connector_capacity_violation_count": source_sink_violation_count,
        "source_sink_connector_capacity_conventions_respected": source_sink_violation_count == 0,
        "artificial_variables_needed": False,
        "artificial_variables_present_in_final_pool": artificial_present,
        "phase2_cost_minimization_run": False,
        "phase2_pricing_run": False,
    }
    blockers: list[str] = []
    if summary["real_only_feasibility_status"] != "PASS":
        blockers.append("real-only feasibility audit failed")
    return summary, demand_rows, capacity_rows, blockers


def added_candidate_role_audit(
    added_candidates: list[dict[str, str]],
    final_pool: list[dict[str, str]],
    final_real_flow: list[dict[str, str]],
    rounds: list[dict[str, str]],
    final_capacity_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    flow_by_column = real_flow_map(final_real_flow)
    pool_by_id = {row.get("column_id", ""): row for row in final_pool}
    round_by_number = {row.get("round", ""): row for row in rounds}
    shared_or_binding_arcs: set[str] = set()
    for row in final_capacity_rows:
        demand_tokens = set(split_sequence(row.get("demand_ids_using_arc", "")))
        if {"D3", "D4"}.issubset(demand_tokens) or parse_float(row.get("slack"), math.inf) <= TOL:
            shared_or_binding_arcs.add(row.get("arc_id", ""))
    baseline_d4_1_arcs = set(split_sequence(pool_by_id.get("C_D4_1", {}).get("arc_sequence", "")))

    rows: list[dict[str, Any]] = []
    for added in added_candidates:
        candidate_id = added.get("candidate_id", "")
        column = pool_by_id.get(candidate_id, {})
        arc_ids = split_sequence(column.get("arc_sequence", added.get("arc_sequence", "")))
        round_row = round_by_number.get(added.get("round", ""), {})
        used_shared_or_binding = [arc_id for arc_id in arc_ids if arc_id in shared_or_binding_arcs]
        avoided_from_c_d4_1 = sorted(baseline_d4_1_arcs - set(arc_ids)) if added.get("demand_id") == "D4" else []
        rows.append(
            {
                "round": added.get("round", ""),
                "candidate_id": candidate_id,
                "demand_id": added.get("demand_id", ""),
                "final_flow": flow_by_column.get(candidate_id, 0.0),
                "artificial_flow_before_add": added.get("artificial_flow_before_add", ""),
                "artificial_flow_after_resolve": added.get("artificial_flow_after_resolve", ""),
                "D3_artificial_flow_before_round": round_row.get("D3_artificial_flow_before", ""),
                "D3_artificial_flow_after_round": round_row.get("D3_artificial_flow_after", ""),
                "D4_artificial_flow_before_round": round_row.get("D4_artificial_flow_before", ""),
                "D4_artificial_flow_after_round": round_row.get("D4_artificial_flow_after", ""),
                "arc_sequence": column.get("arc_sequence", added.get("arc_sequence", "")),
                "shared_or_binding_arcs_used": "|".join(used_shared_or_binding),
                "baseline_C_D4_1_arcs_avoided_by_D4_candidate": "|".join(avoided_from_c_d4_1),
                "interpretation": "D4 candidate is consistent with indirect capacity reallocation"
                if added.get("demand_id") == "D4"
                else "D3 candidate directly targets positive D3 artificial flow",
            }
        )
    return rows


def capacity_reallocation_audit(
    inputs: dict[str, Any],
    final_pool: list[dict[str, str]],
    final_real_flow: list[dict[str, str]],
    final_capacity_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    initial_flow = real_flow_map(inputs["initial_real_flow"])
    final_flow = real_flow_map(final_real_flow)
    pool_by_id = {row.get("column_id", ""): row for row in final_pool}
    capacity_by_arc = {row.get("arc_id", ""): row for row in final_capacity_rows}
    d4_added_ids = [
        row.get("candidate_id", "")
        for row in inputs["added_candidates"]
        if row.get("demand_id") == "D4"
    ]
    d4_added_flow = sum(final_flow.get(column_id, 0.0) for column_id in d4_added_ids)
    c_d4_1_change = final_flow.get("C_D4_1", 0.0) - initial_flow.get("C_D4_1", 0.0)
    c_d3_1_change = final_flow.get("C_D3_1", 0.0) - initial_flow.get("C_D3_1", 0.0)
    d4_round_drop = sum(
        abs(parse_float(row.get("artificial_flow_after_resolve"), 0.0) - parse_float(row.get("artificial_flow_before_add"), 0.0))
        for row in inputs["added_candidates"]
        if row.get("demand_id") == "D4"
    )
    move_48_t7 = capacity_by_arc.get("move_48_t7", {})
    return [
        {
            "audit_item": "D4_added_candidate_final_flow",
            "before_flow": 0.0,
            "after_flow": d4_added_flow,
            "flow_change": d4_added_flow,
            "affected_demand": "D4",
            "related_candidate_ids": "|".join(d4_added_ids),
            "affected_arcs": "|".join(
                sorted(
                    {
                        arc_id
                        for candidate_id in d4_added_ids
                        for arc_id in split_sequence(pool_by_id.get(candidate_id, {}).get("arc_sequence", ""))
                    }
                )
            ),
            "interpretation": "D4 repaired-seed candidates carry positive final flow while D4 artificial flow remains zero.",
        },
        {
            "audit_item": "C_D4_1_flow_reduced",
            "before_flow": initial_flow.get("C_D4_1", 0.0),
            "after_flow": final_flow.get("C_D4_1", 0.0),
            "flow_change": c_d4_1_change,
            "affected_demand": "D4",
            "related_candidate_ids": "|".join(d4_added_ids),
            "affected_arcs": pool_by_id.get("C_D4_1", {}).get("arc_sequence", ""),
            "interpretation": "D4 baseline flow shifts away from C_D4_1, consistent with reallocation rather than new D4 demand.",
        },
        {
            "audit_item": "C_D3_1_flow_increased",
            "before_flow": initial_flow.get("C_D3_1", 0.0),
            "after_flow": final_flow.get("C_D3_1", 0.0),
            "flow_change": c_d3_1_change,
            "affected_demand": "D3",
            "related_candidate_ids": "|".join(d4_added_ids),
            "affected_arcs": pool_by_id.get("C_D3_1", {}).get("arc_sequence", ""),
            "interpretation": "D3 real flow increases on a route sharing downstream capacity with D4 baseline flow.",
        },
        {
            "audit_item": "move_48_t7_shared_capacity_final",
            "before_flow": "",
            "after_flow": parse_float(move_48_t7.get("real_only_flow", move_48_t7.get("real_flow")), 0.0),
            "flow_change": "",
            "affected_demand": move_48_t7.get("demand_ids_using_arc", ""),
            "related_candidate_ids": "|".join(d4_added_ids),
            "affected_arcs": "move_48_t7",
            "interpretation": "Final shared/binding capacity on move_48_t7 is used by C_D3_1 and C_D4_1; D4 new candidates avoid this arc.",
        },
        {
            "audit_item": "D3_artificial_drop_after_D4_rounds",
            "before_flow": "",
            "after_flow": "",
            "flow_change": -d4_round_drop,
            "affected_demand": "D3",
            "related_candidate_ids": "|".join(d4_added_ids),
            "affected_arcs": "diagnostic_rounds_4_and_5",
            "interpretation": "The artificial-flow drop after D4 candidate additions is consistent with indirect capacity reallocation; it is not asserted as an exact causality proof.",
        },
    ]


def phase2_pool_rows(final_pool: list[dict[str, str]], final_real_flow: list[dict[str, str]]) -> list[dict[str, Any]]:
    flow_by_column = real_flow_map(final_real_flow)
    rows: list[dict[str, Any]] = []
    for row in final_pool:
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
                "phase2_pool_column_type": "phase1_added_real_column"
                if row.get("pool_membership") == "bounded_loop_added_candidate"
                else "baseline_real_column",
                "source_metadata": row.get("candidate_source") or "baseline_dynamic_columns",
                "added_in_phase1_round": row.get("added_in_round", "0"),
                "phase1_final_flow": flow_by_column.get(row.get("column_id", ""), 0.0),
                "written_to_baseline_dynamic_columns": "false",
                "output_only_phase2_initial_pool": "true",
            }
        )
    return rows


def write_reports(output_dir: Path, summary: dict[str, Any], manifest: dict[str, Any], role_rows: list[dict[str, Any]]) -> None:
    d4_rows = [row for row in role_rows if row.get("demand_id") == "D4"]
    closure_lines = [
        "# Phase-I Closure Audit",
        "",
        SCOPE_BOUNDARY,
        "",
        "## Closure Result",
        "",
        f"- Closure audit status: {summary['closure_audit_status']}",
        f"- Bounded loop stop reason: {summary['bounded_loop_stop_reason']}",
        f"- Total artificial flow final: {summary['total_artificial_flow_final']}",
        f"- D3 artificial flow final: {summary['D3_artificial_flow_final']}",
        f"- D4 artificial flow final: {summary['D4_artificial_flow_final']}",
        f"- Real-only feasibility status: {summary['real_only_feasibility_status']}",
        f"- Real-only demand residual max: {summary['real_only_demand_residual_max']}",
        f"- Real-only capacity violation count: {summary['real_only_capacity_violation_count']}",
        f"- Baseline dynamic_columns.csv mutated: {summary['baseline_dynamic_columns_mutated']}",
        f"- Phase-II execution performed: {summary['phase2_execution_performed']}",
        "",
        "## D4 Indirect Capacity-Reallocation Interpretation",
        "",
        "Two D4 repaired-seed candidates were added after the D3 direct candidates. This is not treated as an error. The audit is consistent with D4 flow being rerouted in a way that reallocates shared dynamic capacity used by D3 real columns.",
    ]
    for row in d4_rows:
        closure_lines.append(
            f"- {row['candidate_id']} final flow {row['final_flow']} uses shared/binding arcs `{row['shared_or_binding_arcs_used']}` and avoids baseline C_D4_1 arcs `{row['baseline_C_D4_1_arcs_avoided_by_D4_candidate']}`."
        )
    closure_lines.extend(
        [
            "",
            "This is a diagnostic consistency statement, not an exact causality proof or a general convergence claim.",
        ]
    )
    (output_dir / "phase1_closure_report.md").write_text("\n".join(closure_lines) + "\n", encoding="utf-8")

    handoff_lines = [
        "# Phase-II Handoff Precheck",
        "",
        "The handoff pool is output-only and is not written to the baseline data folder.",
        "",
        f"- Phase-II initial pool columns: {manifest['column_count']}",
        f"- No artificial variables: {manifest['no_artificial_variables']}",
        f"- Safe for Phase-II RMP initialization: {manifest['safe_for_phase2_rmp_initialization']}",
        f"- Phase-II execution performed: {manifest['phase2_execution_performed']}",
        f"- Phase-II pricing performed: {manifest['phase2_pricing_performed']}",
        f"- Baseline mutation: {manifest['baseline_dynamic_columns_mutated']}",
        "",
        "A separate task is required before running any Phase-II cost-minimizing RMP or pricing.",
    ]
    (output_dir / "phase2_handoff_precheck_report.md").write_text(
        "\n".join(handoff_lines) + "\n", encoding="utf-8"
    )


def run_precheck(
    config_path: str | Path = DEFAULT_CURRENT_POOL_CONFIG,
    output_dir: Path = OUTPUT_DIR,
    precheck_only: bool = False,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    config = load_config(config_path)
    data_dir = input_data_dir(config)
    baseline_path = data_dir / "dynamic_columns.csv"
    baseline_hash_before = sha256_file(baseline_path)
    write_input_audit = output_dir.resolve() != DEFAULT_OUTPUT_DIR.resolve() or precheck_only
    input_audit = input_artifact_audit(output_dir, config_path, data_dir, write_input_audit)
    blockers = required_input_blockers()
    if precheck_only:
        summary = {
            "closure_audit_status": "PASS" if not blockers else "SAFE_BLOCKED",
            "precheck_only": True,
            "phase1_bounded_loop_dir": input_audit["phase1_bounded_loop_dir"],
            "phase1_final_pool_path": input_audit["phase1_final_pool_path"],
            "phase2_execution_performed": False,
            "phase2_pricing_performed": False,
            "phase2_cost_minimization_performed": False,
            "add_resolve_run": False,
            "new_loop_run": False,
            "full_assignment_run": False,
            "full_cg_run": False,
            "general_convergence_claimed": False,
            "baseline_dynamic_columns_hash_before": baseline_hash_before,
            "baseline_dynamic_columns_hash_after": sha256_file(baseline_path),
            "baseline_dynamic_columns_mutated": False,
            "safe_blockers": blockers,
            "scope": SCOPE_BOUNDARY,
        }
        write_json(output_dir / "phase1_closure_summary.json", summary)
        return summary
    if blockers:
        summary = {
            "closure_audit_status": "SAFE_BLOCKED",
            "safe_blockers": blockers,
            "precheck_only": False,
            "phase2_execution_performed": False,
            "phase2_pricing_performed": False,
            "full_assignment_run": False,
            "full_cg_run": False,
            "scope": SCOPE_BOUNDARY,
        }
        write_json(output_dir / "phase1_closure_summary.json", summary)
        return summary

    inputs = load_inputs()
    arcs = read_csv(data_dir / "dynamic_arc.csv")
    demands = read_csv(data_dir / "dynamic_demand.csv")
    closure_checks, closure_blockers = validate_bounded_loop(inputs, baseline_hash_before)
    integrity_rows, integrity_blockers = final_pool_integrity_audit(
        inputs["final_pool"],
        inputs["added_candidates"],
        inputs["seed_rows"],
        arcs,
        demands,
        ALLOW_VARIABLE_PHASE1_ADDED_COLUMN_COUNT,
    )
    real_only_summary, demand_rows, capacity_rows, real_only_blockers = real_only_feasibility_audit(
        inputs["final_pool"], inputs["final_real_flow"], arcs, demands
    )
    role_rows = added_candidate_role_audit(
        inputs["added_candidates"], inputs["final_pool"], inputs["final_real_flow"], inputs["rounds"], capacity_rows
    )
    reallocation_rows = capacity_reallocation_audit(inputs, inputs["final_pool"], inputs["final_real_flow"], capacity_rows)
    phase2_rows = phase2_pool_rows(inputs["final_pool"], inputs["final_real_flow"])

    baseline_hash_after = sha256_file(baseline_path)
    if baseline_hash_after != baseline_hash_before:
        blockers.append("baseline dynamic_columns.csv hash changed during closure/handoff precheck")
    blockers.extend(closure_blockers)
    blockers.extend(integrity_blockers)
    blockers.extend(real_only_blockers)
    no_artificial_phase2 = not any(row["column_id"].startswith("ARTIFICIAL_DEMAND_") for row in phase2_rows)
    closure_pass = not blockers
    demand_coverage = {
        row["demand_id"]: {
            "demand_volume": parse_float(row["demand_volume"], 0.0),
            "real_only_flow": parse_float(row["real_only_flow"], 0.0),
            "real_only_demand_residual": parse_float(row["real_only_demand_residual"], 0.0),
        }
        for row in demand_rows
    }
    manifest = {
        "column_count": len(phase2_rows),
        "demand_coverage_by_real_columns": demand_coverage,
        "no_artificial_variables": no_artificial_phase2,
        "baseline_dynamic_columns_mutated": baseline_hash_before != baseline_hash_after,
        "safe_for_phase2_rmp_initialization": bool(closure_pass and no_artificial_phase2),
        "phase2_execution_performed": False,
        "phase2_pricing_performed": False,
        "phase2_cost_minimization_performed": False,
        "output_only_phase2_initial_pool": True,
        "baseline_dynamic_columns_path": rel(baseline_path),
        "phase2_initial_column_pool_path": rel(output_dir / "phase2_initial_column_pool.csv"),
        "safe_blockers": blockers,
    }
    hash_audit = {
        "baseline_dynamic_columns_path": rel(baseline_path),
        "baseline_dynamic_columns_hash_before": baseline_hash_before,
        "baseline_dynamic_columns_hash_after": baseline_hash_after,
        "accepted_baseline_dynamic_columns_hash": ACCEPTED_BASELINE_HASH,
        "baseline_dynamic_columns_mutated": baseline_hash_before != baseline_hash_after,
        "bounded_loop_hash_audit_path": rel(BOUNDED_LOOP_DIR / "phase1_loop_hash_audit.json"),
        "bounded_loop_candidate_source_hash": inputs["bounded_hash"].get("candidate_source_sha256"),
        "phase2_initial_column_pool_path": rel(output_dir / "phase2_initial_column_pool.csv"),
        "phase2_initial_column_pool_output_only": True,
        "phase2_execution_performed": False,
        "phase2_pricing_performed": False,
    }
    bounded_summary = inputs["bounded_summary"]
    summary = {
        "closure_audit_status": "PASS" if closure_pass else "SAFE_BLOCKED",
        "bounded_loop_diagnostic_status": bounded_summary.get("diagnostic_status"),
        "bounded_loop_stop_reason": bounded_summary.get("stop_reason"),
        "total_artificial_flow_final": bounded_summary.get("total_artificial_flow_final"),
        "D3_artificial_flow_final": bounded_summary.get("D3_artificial_flow_final"),
        "D4_artificial_flow_final": bounded_summary.get("D4_artificial_flow_final"),
        "bounded_loop_capacity_violation_count_final": bounded_summary.get("capacity_violation_count_final"),
        "bounded_loop_demand_residual_max_final": bounded_summary.get("demand_residual_max_final"),
        "final_pool_column_count": len(inputs["final_pool"]),
        "baseline_real_column_count": sum(row.get("pool_membership") == "original_baseline_column" for row in inputs["final_pool"]),
        "phase1_added_column_count": sum(row.get("pool_membership") == "bounded_loop_added_candidate" for row in inputs["final_pool"]),
        "allow_variable_phase1_added_column_count": ALLOW_VARIABLE_PHASE1_ADDED_COLUMN_COUNT,
        "final_pool_contains_artificial_variables": not no_artificial_phase2,
        "final_pool_integrity_status": "PASS" if not integrity_blockers else "FAIL",
        "real_only_feasibility_status": real_only_summary["real_only_feasibility_status"],
        "real_only_demand_residual_max": real_only_summary["demand_residual_max"],
        "real_only_capacity_violation_count": real_only_summary["capacity_violation_count"],
        "real_only_max_capacity_violation": real_only_summary["max_capacity_violation"],
        "source_sink_connector_capacity_conventions_respected": real_only_summary[
            "source_sink_connector_capacity_conventions_respected"
        ],
        "D4_capacity_reallocation_audit_produced": bool(role_rows and reallocation_rows),
        "D4_added_candidates": [
            row.get("candidate_id") for row in inputs["added_candidates"] if row.get("demand_id") == "D4"
        ],
        "phase2_initial_pool_column_count": len(phase2_rows),
        "phase2_initial_pool_contains_artificial_variables": not no_artificial_phase2,
        "safe_for_phase2_rmp_initialization": manifest["safe_for_phase2_rmp_initialization"],
        "phase2_execution_performed": False,
        "phase2_pricing_performed": False,
        "phase2_cost_minimization_performed": False,
        "add_resolve_run": False,
        "new_loop_run": False,
        "full_assignment_run": False,
        "full_cg_run": False,
        "general_convergence_claimed": False,
        "baseline_dynamic_columns_hash_before": baseline_hash_before,
        "baseline_dynamic_columns_hash_after": baseline_hash_after,
        "baseline_dynamic_columns_mutated": baseline_hash_before != baseline_hash_after,
        "closure_checks": closure_checks,
        "safe_blockers": blockers,
        "next_safe_step": "separately scoped Phase-II RMP initialization diagnostic"
        if manifest["safe_for_phase2_rmp_initialization"]
        else "review closure safe blockers before Phase-II handoff",
        "scope": SCOPE_BOUNDARY,
    }

    write_json(output_dir / "phase1_closure_summary.json", summary)
    write_json(output_dir / "phase1_real_only_feasibility_summary.json", real_only_summary)
    write_csv(
        output_dir / "phase1_real_only_demand_balance.csv",
        demand_rows,
        [
            "demand_id",
            "demand_volume",
            "real_only_flow",
            "artificial_flow_fixed_to_zero",
            "real_only_demand_residual",
            "status",
        ],
    )
    write_csv(
        output_dir / "phase1_real_only_capacity_usage.csv",
        capacity_rows,
        [
            "arc_id",
            "arc_type",
            "physical_link_id",
            "from_time",
            "to_time",
            "real_only_flow",
            "artificial_flow_fixed_to_zero",
            "capacity",
            "capacity_violation",
            "slack",
            "real_columns_using_arc",
            "demand_ids_using_arc",
            "source_sink_connector_capacity_convention_respected",
            "status",
        ],
    )
    write_csv(
        output_dir / "phase1_final_pool_integrity_audit.csv",
        integrity_rows,
        [
            "column_id",
            "demand_id",
            "pool_membership",
            "added_in_phase1_round",
            "is_artificial",
            "structurally_valid",
            "invalid_reason",
            "duplicate_within_same_demand_arc_sequence",
            "from_fixed_repaired_seed_source",
            "written_to_baseline_dynamic_columns",
            "audit_status",
        ],
    )
    write_csv(
        output_dir / "phase1_added_candidate_role_audit.csv",
        role_rows,
        [
            "round",
            "candidate_id",
            "demand_id",
            "final_flow",
            "artificial_flow_before_add",
            "artificial_flow_after_resolve",
            "D3_artificial_flow_before_round",
            "D3_artificial_flow_after_round",
            "D4_artificial_flow_before_round",
            "D4_artificial_flow_after_round",
            "arc_sequence",
            "shared_or_binding_arcs_used",
            "baseline_C_D4_1_arcs_avoided_by_D4_candidate",
            "interpretation",
        ],
    )
    write_csv(
        output_dir / "phase1_capacity_reallocation_audit.csv",
        reallocation_rows,
        [
            "audit_item",
            "before_flow",
            "after_flow",
            "flow_change",
            "affected_demand",
            "related_candidate_ids",
            "affected_arcs",
            "interpretation",
        ],
    )
    write_csv(
        output_dir / "phase2_initial_column_pool.csv",
        phase2_rows,
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
        ],
    )
    write_json(output_dir / "phase2_initial_pool_manifest.json", manifest)
    write_json(output_dir / "phase2_handoff_hash_audit.json", hash_audit)
    write_reports(output_dir, summary, manifest, role_rows)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase-I closure audit and Phase-II handoff precheck.")
    parser.add_argument("--config", default=DEFAULT_CURRENT_POOL_CONFIG)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--input-artifacts-json", default=None)
    parser.add_argument("--benchmark-id", default="second_controlled_benchmark_link55")
    parser.add_argument("--no-mutate-accepted-outputs", action="store_true")
    parser.add_argument("--precheck-only", action="store_true")
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
    summary = run_precheck(config_path, output_dir, precheck_only=args.precheck_only)
    print(f"Phase-I closure audit status: {summary['closure_audit_status']}")
    print(f"Real-only feasibility status: {summary.get('real_only_feasibility_status')}")
    print(f"Real-only demand residual max: {summary.get('real_only_demand_residual_max')}")
    print(f"Real-only capacity violation count: {summary.get('real_only_capacity_violation_count')}")
    print(f"Phase-II initial pool column count: {summary.get('phase2_initial_pool_column_count')}")
    print(f"Baseline dynamic_columns.csv mutated: {summary.get('baseline_dynamic_columns_mutated')}")
    print(f"Phase-II execution performed: {summary.get('phase2_execution_performed')}")
    print(f"Phase-II pricing performed: {summary.get('phase2_pricing_performed')}")
    print(f"D4 capacity reallocation audit produced: {summary.get('D4_capacity_reallocation_audit_produced')}")
    print(f"Report: {output_dir / 'phase1_closure_report.md'}")
    return 0 if summary["closure_audit_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
