"""Phase-I pricing candidate diagnostic.

This bounded diagnostic evaluates existing, reviewable real-column candidates
against the accepted Phase-I artificial-demand RMP duals. It reads the
validated stationarity convention from the dual audit output and computes
entry signals for candidate real columns.

It does not add candidates, mutate the baseline dynamic_columns.csv, re-solve
the RMP, run add-resolve, run a controlled loop, transition to Phase II, run
full assignment, or run full CG.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

from phase1_artificial_rmp_preflight import TRUE_COST_TIE_BREAKER_EPSILON, sha256_file
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


OUTPUT_DIR = ROOT_DIR / "outputs" / "phase1_pricing_candidate_diagnostic"
PREFLIGHT_DIR = ROOT_DIR / "outputs" / "phase1_artificial_rmp_preflight"
DUAL_AUDIT_DIR = ROOT_DIR / "outputs" / "phase1_artificial_dual_audit"
SEED_REPAIR_DIR = ROOT_DIR / "outputs" / "second_controlled_benchmark_link55_seed_pool_repair"
REPAIRED_SEED_COLUMNS = SEED_REPAIR_DIR / "repaired_seed_columns.csv"
PHASE1_PRICING_SCOPE_BOUNDARY = (
    "This is a Phase-I pricing candidate diagnostic only. It evaluates a "
    "bounded set of existing real-column candidates using the previously "
    "validated Phase-I dual convention. It does not add candidates, mutate "
    "the baseline dynamic_columns.csv, re-solve the RMP, run add-resolve, "
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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT_DIR)).replace("\\", "/")


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def load_phase1_inputs() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    preflight = read_json(PREFLIGHT_DIR / "phase1_rmp_summary.json")
    dual_solution = read_json(DUAL_AUDIT_DIR / "phase1_dual_solution.json")
    dual_summary = read_json(DUAL_AUDIT_DIR / "phase1_dual_audit_summary.json")
    return preflight, dual_solution, dual_summary


def validated_signs(dual_solution: dict[str, Any]) -> tuple[str, float, float, list[str]]:
    blockers: list[str] = []
    convention = dual_solution.get("validated_stationarity_convention")
    if not isinstance(convention, dict):
        return "", math.nan, math.nan, ["validated_stationarity_convention is missing or not an object"]
    if convention.get("validation_passed") is not True:
        blockers.append("validated_stationarity_convention.validation_passed is not true")
    convention_name = str(convention.get("convention_name", ""))
    eq_sign = parse_float(convention.get("eq_marginal_sign"), math.nan)
    cap_sign = parse_float(convention.get("capacity_marginal_sign"), math.nan)
    if not math.isfinite(eq_sign):
        blockers.append("eq_marginal_sign is missing or nonfinite")
    if not math.isfinite(cap_sign):
        blockers.append("capacity_marginal_sign is missing or nonfinite")
    return convention_name, eq_sign, cap_sign, blockers


def preflight_stable(preflight: dict[str, Any], dual_summary: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    artificial = preflight.get("artificial_flow_by_demand", {})
    if preflight.get("preflight_status") != "PASS":
        blockers.append(f"preflight_status changed: {preflight.get('preflight_status')}")
    if preflight.get("solver_status") != "optimal":
        blockers.append(f"preflight solver status changed: {preflight.get('solver_status')}")
    if abs(parse_float(preflight.get("total_artificial_flow"), math.nan) - 6287.557003) > TOL:
        blockers.append(f"total artificial flow changed: {preflight.get('total_artificial_flow')}")
    if parse_float(artificial.get("D3"), 0.0) <= TOL:
        blockers.append("D3 artificial flow is no longer positive")
    if abs(parse_float(artificial.get("D4"), 0.0)) > TOL:
        blockers.append(f"D4 artificial flow is no longer zero: {artificial.get('D4')}")
    if int(preflight.get("capacity_violation_count") or 0) != 0:
        blockers.append(f"capacity violation count changed: {preflight.get('capacity_violation_count')}")
    if preflight.get("baseline_dynamic_columns_mutated") is not False:
        blockers.append("preflight reports baseline dynamic_columns.csv mutation")
    if preflight.get("phase2_transition_allowed") is not False:
        blockers.append("Phase-II transition is no longer blocked")
    if dual_summary.get("dual_audit_status") != "PASS":
        blockers.append(f"dual audit status is not PASS: {dual_summary.get('dual_audit_status')}")
    if dual_summary.get("reduced_cost_convention_validation_status") != "PASS":
        blockers.append("dual convention validation is not PASS")
    return blockers


def arc_lookup(arcs: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["arc_id"]: row for row in arcs}


def existing_phase1_columns(columns: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    return {
        (row.get("demand_id", ""), row.get("arc_sequence", "")): row
        for row in columns
    }


def is_artificial_candidate(row: dict[str, str]) -> bool:
    return row.get("column_id", "").startswith("ARTIFICIAL_DEMAND_") or row.get("column_source") == "artificial"


def structural_validation(
    candidate: dict[str, str],
    demand_ids: set[str],
    arc_by_id: dict[str, dict[str, str]],
) -> tuple[bool, str]:
    if is_artificial_candidate(candidate):
        return False, "artificial_variables_are_not_real_column_candidates"
    demand_id = candidate.get("demand_id", "")
    if demand_id not in demand_ids:
        return False, "wrong_or_missing_demand_id"
    arc_ids = split_sequence(candidate.get("arc_sequence", ""))
    if not arc_ids:
        return False, "missing_arc_sequence"
    missing = [arc_id for arc_id in arc_ids if arc_id not in arc_by_id]
    if missing:
        return False, "missing_dynamic_arcs:" + "|".join(missing)
    first = arc_by_id[arc_ids[0]]
    last = arc_by_id[arc_ids[-1]]
    if first.get("arc_id") != f"source_{demand_id}":
        return False, "source_connector_does_not_match_demand"
    if last.get("arc_type") != "sink_connector" or last.get("to_physical_node_id") != f"sink_{demand_id}":
        return False, "sink_connector_does_not_match_demand"
    for prev_arc_id, next_arc_id in zip(arc_ids, arc_ids[1:]):
        prev_arc = arc_by_id[prev_arc_id]
        next_arc = arc_by_id[next_arc_id]
        if prev_arc.get("to_node_time_id") != next_arc.get("from_node_time_id"):
            return False, f"broken_source_sink_timing:{prev_arc_id}->{next_arc_id}"
    return True, ""


def capacity_dual_maps(dual_solution: dict[str, Any]) -> tuple[dict[str, float], dict[str, float]]:
    capacity_duals: dict[str, float] = {}
    capacity_slacks: dict[str, float] = {}
    for arc_id, payload in dual_solution.get("capacity_duals_by_dynamic_arc", {}).items():
        capacity_duals[arc_id] = parse_float(payload.get("raw_marginal"), 0.0)
        capacity_slacks[arc_id] = parse_float(payload.get("residual_slack"), math.inf)
    return capacity_duals, capacity_slacks


def demand_dual_map(dual_solution: dict[str, Any]) -> dict[str, float]:
    return {
        demand_id: parse_float(payload.get("raw_marginal"), math.nan)
        for demand_id, payload in dual_solution.get("equality_duals_by_demand_constraint", {}).items()
    }


def candidate_generalized_cost(row: dict[str, str], arc_ids: list[str], arc_by_id: dict[str, dict[str, str]]) -> float:
    listed = parse_float(row.get("generalized_cost"), math.nan)
    if math.isfinite(listed):
        return listed
    path_cost = parse_float(row.get("path_cost"), math.nan)
    if math.isfinite(path_cost):
        return path_cost
    return sum(parse_float(arc_by_id[arc_id].get("cost"), 0.0) for arc_id in arc_ids if arc_id in arc_by_id)


def binding_or_positive_arcs(
    arc_ids: list[str],
    capacity_duals: dict[str, float],
    capacity_slacks: dict[str, float],
    cap_sign: float,
) -> list[str]:
    flagged: list[str] = []
    for arc_id in arc_ids:
        raw = capacity_duals.get(arc_id, 0.0)
        signed_signal = cap_sign * raw if math.isfinite(cap_sign) else 0.0
        slack = capacity_slacks.get(arc_id, math.inf)
        if abs(raw) > TOL or signed_signal > TOL or slack <= TOL:
            flagged.append(arc_id)
    return flagged


def evaluate_candidates(
    source_rows: list[dict[str, str]],
    baseline_columns: list[dict[str, str]],
    demands: list[dict[str, str]],
    arcs: list[dict[str, str]],
    preflight: dict[str, Any],
    dual_solution: dict[str, Any],
    convention_name: str,
    eq_sign: float,
    cap_sign: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    demand_ids = {row["demand_id"] for row in demands}
    artificial_by_demand = preflight.get("artificial_flow_by_demand", {})
    positive_artificial_demands = {
        demand_id for demand_id, flow in artificial_by_demand.items() if parse_float(flow, 0.0) > TOL
    }
    arc_by_id = arc_lookup(arcs)
    existing_by_key = existing_phase1_columns(baseline_columns)
    demand_duals = demand_dual_map(dual_solution)
    capacity_duals, capacity_slacks = capacity_dual_maps(dual_solution)

    candidate_rows: list[dict[str, Any]] = []
    duplicate_rows: list[dict[str, Any]] = []
    seen_candidate_ids: set[str] = set()
    for idx, candidate in enumerate(source_rows, start=1):
        candidate_id = candidate.get("column_id") or candidate.get("path_id") or f"candidate_{idx}"
        if candidate_id in seen_candidate_ids:
            candidate_id = f"{candidate_id}_{idx}"
        seen_candidate_ids.add(candidate_id)
        demand_id = candidate.get("demand_id", "")
        arc_sequence = candidate.get("arc_sequence", "")
        arc_ids = split_sequence(arc_sequence)
        structurally_valid, invalid_reason = structural_validation(candidate, demand_ids, arc_by_id)
        duplicate = False
        duplicate_column_id = ""
        if structurally_valid:
            duplicate_column = existing_by_key.get((demand_id, arc_sequence))
            duplicate = duplicate_column is not None
            duplicate_column_id = duplicate_column.get("column_id", "") if duplicate_column else ""

        generalized_cost = candidate_generalized_cost(candidate, arc_ids, arc_by_id) if structurally_valid else math.nan
        phase1_objective = TRUE_COST_TIE_BREAKER_EPSILON * generalized_cost if math.isfinite(generalized_cost) else math.nan
        equality_dual = demand_duals.get(demand_id, math.nan)
        capacity_dual_sum = sum(capacity_duals.get(arc_id, 0.0) for arc_id in arc_ids)
        if structurally_valid and math.isfinite(phase1_objective) and math.isfinite(equality_dual):
            entry_signal = phase1_objective + eq_sign * equality_dual + cap_sign * capacity_dual_sum
        else:
            entry_signal = math.nan

        if not structurally_valid:
            classification = "invalid_candidate"
        elif duplicate:
            classification = "duplicate_existing_phase1_column"
        elif entry_signal < -TOL:
            classification = "improving_new_candidate"
        else:
            classification = "nonimproving_new_candidate"

        flagged_arcs = binding_or_positive_arcs(arc_ids, capacity_duals, capacity_slacks, cap_sign)
        row = {
            "candidate_id": candidate_id,
            "demand_id": demand_id,
            "candidate_source": candidate.get("column_source") or "accepted_seed_pool_repair_repaired_seed_columns",
            "path_id": candidate.get("path_id", ""),
            "arc_sequence": arc_sequence,
            "structurally_valid": bool_text(structurally_valid),
            "invalid_reason": invalid_reason,
            "duplicate_existing_phase1_column": bool_text(duplicate),
            "duplicate_of_column_id": duplicate_column_id,
            "phase1_objective_coefficient": phase1_objective if math.isfinite(phase1_objective) else "",
            "true_generalized_cost": generalized_cost if math.isfinite(generalized_cost) else "",
            "equality_dual_raw": equality_dual if math.isfinite(equality_dual) else "",
            "capacity_dual_sum_raw": capacity_dual_sum,
            "validated_stationarity_convention": convention_name,
            "validated_eq_sign": eq_sign,
            "validated_capacity_sign": cap_sign,
            "phase1_entry_signal": entry_signal if math.isfinite(entry_signal) else "",
            "classification": classification,
            "uses_binding_or_positive_capacity_dual_arc": bool_text(bool(flagged_arcs)),
            "binding_or_positive_dual_arcs_used": "|".join(flagged_arcs),
            "targets_positive_artificial_flow_demand": bool_text(demand_id in positive_artificial_demands),
            "artificial_flow_for_demand_before_pricing": parse_float(artificial_by_demand.get(demand_id), 0.0),
            "would_be_added_in_future_task": "false",
        }
        candidate_rows.append(row)
        duplicate_rows.append(
            {
                "candidate_id": candidate_id,
                "demand_id": demand_id,
                "arc_sequence": arc_sequence,
                "duplicate_existing_phase1_column": bool_text(duplicate),
                "duplicate_of_column_id": duplicate_column_id,
                "classification": classification,
            }
        )
    return candidate_rows, duplicate_rows


def write_precheck_report(path: Path, precheck: dict[str, Any]) -> None:
    lines = [
        "# Phase-I Pricing Candidate Precheck",
        "",
        PHASE1_PRICING_SCOPE_BOUNDARY,
        "",
        f"- Precheck status: {precheck['pricing_precheck_status']}",
        f"- Candidate source status: {precheck['candidate_source_status']}",
        f"- Candidate source: {precheck['candidate_source_path']}",
        f"- Validated convention source: {precheck['validated_convention_source']}",
        f"- Blockers: {', '.join(precheck['safe_blockers']) if precheck['safe_blockers'] else 'None'}",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_pricing_report(path: Path, summary: dict[str, Any], candidates: list[dict[str, Any]]) -> None:
    improving = [row for row in candidates if row["classification"] == "improving_new_candidate"]
    lines = [
        "# Phase-I Pricing Candidate Diagnostic Report",
        "",
        PHASE1_PRICING_SCOPE_BOUNDARY,
        "",
        "## Summary",
        "",
        f"- Diagnostic status: {summary['pricing_candidate_diagnostic_status']}",
        f"- Candidate source used: {summary['candidate_source_used']}",
        f"- Validated stationarity convention: {summary['validated_stationarity_convention']}",
        f"- Total candidates: {summary['total_candidate_count']}",
        f"- Structurally valid candidates: {summary['structurally_valid_candidate_count']}",
        f"- Duplicate candidates: {summary['duplicate_candidate_count']}",
        f"- Improving new candidates: {summary['improving_new_candidate_count']}",
        f"- Best improving candidate: {summary['best_improving_candidate_id'] or 'None'}",
        f"- Best improving entry signal: {summary['best_improving_candidate_entry_signal']}",
        f"- Positive artificial-flow demands before diagnostic: {', '.join(summary['positive_artificial_flow_demands']) or 'None'}",
        f"- Baseline dynamic_columns.csv mutated: {summary['baseline_dynamic_columns_mutated']}",
        f"- Candidate columns added: {summary['candidate_columns_added']}",
        f"- RMP re-solved after candidate evaluation: {summary['rmp_resolved_after_pricing']}",
        "",
        "## Improving Candidates",
        "",
    ]
    if improving:
        for row in improving:
            lines.append(
                f"- {row['candidate_id']} ({row['demand_id']}): entry_signal={row['phase1_entry_signal']}, "
                f"target_positive_artificial_flow={row['targets_positive_artificial_flow_demand']}, "
                f"arcs={row['arc_sequence']}"
            )
    else:
        lines.append("- None. Review whether the bounded candidate source is too narrow before expanding the source.")
    lines.extend(
        [
            "",
            "## Out Of Scope",
            "",
            "- No candidate was added to `dynamic_columns.csv`.",
            "- No post-candidate RMP solve was run.",
            "- Add-resolve, controlled-loop, Phase-II, assignment, and full-CG workflows were not run.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_diagnostic(
    config_path: str | Path = DEFAULT_CURRENT_POOL_CONFIG,
    output_dir: Path = OUTPUT_DIR,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    config = load_config(config_path)
    data_dir = input_data_dir(config)
    baseline_columns_path = data_dir / "dynamic_columns.csv"
    baseline_hash_before = sha256_file(baseline_columns_path)

    preflight, dual_solution, dual_summary = load_phase1_inputs()
    convention_name, eq_sign, cap_sign, sign_blockers = validated_signs(dual_solution)
    stability_blockers = preflight_stable(preflight, dual_summary)
    source_blockers: list[str] = []
    if not REPAIRED_SEED_COLUMNS.exists() or REPAIRED_SEED_COLUMNS.stat().st_size == 0:
        source_blockers.append(f"candidate source missing: {rel(REPAIRED_SEED_COLUMNS)}")
        source_rows: list[dict[str, str]] = []
    else:
        source_rows = read_csv(REPAIRED_SEED_COLUMNS)

    arcs = read_csv(data_dir / "dynamic_arc.csv")
    demands = read_csv(data_dir / "dynamic_demand.csv")
    baseline_columns = read_csv(baseline_columns_path)
    safe_blockers = [*stability_blockers, *sign_blockers, *source_blockers]

    if safe_blockers:
        candidate_rows: list[dict[str, Any]] = []
        duplicate_rows: list[dict[str, Any]] = []
    else:
        candidate_rows, duplicate_rows = evaluate_candidates(
            source_rows,
            baseline_columns,
            demands,
            arcs,
            preflight,
            dual_solution,
            convention_name,
            eq_sign,
            cap_sign,
        )

    baseline_hash_after = sha256_file(baseline_columns_path)
    if baseline_hash_after != baseline_hash_before:
        safe_blockers.append("baseline dynamic_columns.csv hash changed during diagnostic")

    valid_rows = [row for row in candidate_rows if row["structurally_valid"] == "true"]
    duplicate_rows_only = [row for row in candidate_rows if row["duplicate_existing_phase1_column"] == "true"]
    improving_rows = [row for row in candidate_rows if row["classification"] == "improving_new_candidate"]
    improving_by_demand: dict[str, int] = {}
    for row in improving_rows:
        improving_by_demand[row["demand_id"]] = improving_by_demand.get(row["demand_id"], 0) + 1
    best = min(
        improving_rows,
        key=lambda row: parse_float(row.get("phase1_entry_signal"), math.inf),
        default=None,
    )
    artificial = preflight.get("artificial_flow_by_demand", {})
    positive_artificial = [
        demand_id for demand_id, flow in artificial.items() if parse_float(flow, 0.0) > TOL
    ]
    if not safe_blockers and not valid_rows:
        safe_blockers.append("candidate source produced no structurally valid candidates")

    if safe_blockers:
        status = "SAFE_BLOCKED"
        next_safe_step = "Phase-I pricing source expansion or blocker review"
    elif improving_rows:
        status = "PASS"
        next_safe_step = "separately scoped one-candidate Phase-I add-resolve diagnostic"
    else:
        status = "SAFE_BLOCKED"
        safe_blockers.append("no improving non-duplicate candidate found in bounded source")
        next_safe_step = "Phase-I pricing source expansion or blocker review"

    precheck = {
        "pricing_precheck_status": "PASS" if not [*stability_blockers, *sign_blockers, *source_blockers] else "SAFE_BLOCKED",
        "candidate_source_status": "PASS" if source_rows and not source_blockers else "SAFE_BLOCKED",
        "candidate_source_path": rel(REPAIRED_SEED_COLUMNS),
        "candidate_source_strategy": "accepted repaired seed-pool columns: current real columns plus bounded waiting/time-shift repair candidates",
        "candidate_source_row_count": len(source_rows),
        "validated_convention_source": rel(DUAL_AUDIT_DIR / "phase1_dual_solution.json"),
        "validated_stationarity_convention": convention_name,
        "validated_eq_sign": eq_sign,
        "validated_capacity_sign": cap_sign,
        "safe_blockers": [*stability_blockers, *sign_blockers, *source_blockers],
        "scope": PHASE1_PRICING_SCOPE_BOUNDARY,
    }
    source_manifest = {
        "candidate_source_status": precheck["candidate_source_status"],
        "candidate_source_path": rel(REPAIRED_SEED_COLUMNS),
        "candidate_source_sha256": sha256_file(REPAIRED_SEED_COLUMNS) if REPAIRED_SEED_COLUMNS.exists() else None,
        "candidate_source_row_count": len(source_rows),
        "candidate_source_strategy": precheck["candidate_source_strategy"],
        "baseline_phase1_real_column_path": rel(baseline_columns_path),
        "baseline_phase1_real_column_count": len(baseline_columns),
        "broad_unconstrained_path_enumerator_run": False,
        "heavy_shortest_path_universe_expansion_run": False,
        "silently_fabricated_paths": False,
    }
    hash_audit = {
        "baseline_dynamic_columns_path": rel(baseline_columns_path),
        "baseline_dynamic_columns_hash_before": baseline_hash_before,
        "baseline_dynamic_columns_hash_after": baseline_hash_after,
        "baseline_dynamic_columns_mutated": baseline_hash_before != baseline_hash_after,
        "candidate_source_path": rel(REPAIRED_SEED_COLUMNS),
        "candidate_source_hash": sha256_file(REPAIRED_SEED_COLUMNS) if REPAIRED_SEED_COLUMNS.exists() else None,
    }
    summary = {
        "pricing_candidate_diagnostic_status": status,
        "candidate_source_status": precheck["candidate_source_status"],
        "candidate_source_used": rel(REPAIRED_SEED_COLUMNS),
        "validated_stationarity_convention": convention_name,
        "validated_convention_source": rel(DUAL_AUDIT_DIR / "phase1_dual_solution.json"),
        "validated_eq_sign": eq_sign,
        "validated_capacity_sign": cap_sign,
        "total_candidate_count": len(candidate_rows),
        "structurally_valid_candidate_count": len(valid_rows),
        "duplicate_candidate_count": len(duplicate_rows_only),
        "improving_new_candidate_count": len(improving_rows),
        "improving_new_candidate_count_by_demand": improving_by_demand,
        "best_improving_candidate_id": best["candidate_id"] if best else None,
        "best_improving_candidate_entry_signal": parse_float(best["phase1_entry_signal"], math.nan) if best else None,
        "D3_improving_new_candidate_count": improving_by_demand.get("D3", 0),
        "D4_improving_new_candidate_count": improving_by_demand.get("D4", 0),
        "positive_artificial_flow_demands": positive_artificial,
        "D3_artificial_flow_before_pricing": parse_float(artificial.get("D3"), 0.0),
        "D4_artificial_flow_before_pricing": parse_float(artificial.get("D4"), 0.0),
        "baseline_dynamic_columns_hash_before": baseline_hash_before,
        "baseline_dynamic_columns_hash_after": baseline_hash_after,
        "baseline_dynamic_columns_mutated": baseline_hash_before != baseline_hash_after,
        "candidate_columns_added": False,
        "rmp_resolved_after_pricing": False,
        "add_resolve_run": False,
        "controlled_loop_run": False,
        "phase2_transition_executed": False,
        "full_assignment_run": False,
        "full_cg_run": False,
        "safe_blockers": safe_blockers,
        "next_safe_step": next_safe_step,
        "scope": PHASE1_PRICING_SCOPE_BOUNDARY,
    }

    write_json(output_dir / "phase1_pricing_precheck.json", precheck)
    write_precheck_report(output_dir / "phase1_pricing_precheck_report.md", precheck)
    write_csv(
        output_dir / "phase1_pricing_candidates.csv",
        candidate_rows,
        [
            "candidate_id",
            "demand_id",
            "candidate_source",
            "path_id",
            "arc_sequence",
            "structurally_valid",
            "invalid_reason",
            "duplicate_existing_phase1_column",
            "duplicate_of_column_id",
            "phase1_objective_coefficient",
            "true_generalized_cost",
            "equality_dual_raw",
            "capacity_dual_sum_raw",
            "validated_stationarity_convention",
            "validated_eq_sign",
            "validated_capacity_sign",
            "phase1_entry_signal",
            "classification",
            "uses_binding_or_positive_capacity_dual_arc",
            "binding_or_positive_dual_arcs_used",
            "targets_positive_artificial_flow_demand",
            "artificial_flow_for_demand_before_pricing",
            "would_be_added_in_future_task",
        ],
    )
    write_json(output_dir / "phase1_pricing_summary.json", summary)
    write_pricing_report(output_dir / "phase1_pricing_report.md", summary, candidate_rows)
    write_csv(
        output_dir / "phase1_candidate_duplicate_audit.csv",
        duplicate_rows,
        [
            "candidate_id",
            "demand_id",
            "arc_sequence",
            "duplicate_existing_phase1_column",
            "duplicate_of_column_id",
            "classification",
        ],
    )
    write_json(output_dir / "phase1_candidate_source_manifest.json", source_manifest)
    write_json(output_dir / "phase1_pricing_hash_audit.json", hash_audit)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase-I pricing candidate diagnostic.")
    parser.add_argument("--config", default=DEFAULT_CURRENT_POOL_CONFIG)
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = ROOT_DIR / output_dir
    summary = run_diagnostic(args.config, output_dir)
    print(f"Phase-I pricing candidate diagnostic status: {summary['pricing_candidate_diagnostic_status']}")
    print(f"Candidate source status: {summary['candidate_source_status']}")
    print(f"Validated convention: {summary['validated_stationarity_convention']}")
    print(f"Total candidates: {summary['total_candidate_count']}")
    print(f"Structurally valid candidates: {summary['structurally_valid_candidate_count']}")
    print(f"Duplicate candidates: {summary['duplicate_candidate_count']}")
    print(f"Improving new candidates: {summary['improving_new_candidate_count']}")
    print(f"Best improving candidate: {summary['best_improving_candidate_id']}")
    print(f"D3 improving new candidates: {summary['D3_improving_new_candidate_count']}")
    print(f"Baseline dynamic_columns.csv mutated: {summary['baseline_dynamic_columns_mutated']}")
    print(f"Candidate columns added: {summary['candidate_columns_added']}")
    print(f"RMP re-solved after candidate evaluation: {summary['rmp_resolved_after_pricing']}")
    print(f"Report: {output_dir / 'phase1_pricing_report.md'}")
    return 0 if summary["pricing_candidate_diagnostic_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
