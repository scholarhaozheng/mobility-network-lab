"""Phase-II pricing candidate diagnostic.

This bounded diagnostic validates the Phase-II reduced-cost/stationarity
convention on the accepted ten-column real-only RMP solution, then evaluates
only the fixed repaired-seed candidate source if validation passes.

It does not add candidates, mutate the baseline dynamic_columns.csv, mutate
the Phase-II initial column pool, re-solve after candidate evaluation, run
add-resolve, run a loop, run full assignment, run full CG, or claim general
convergence.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

from phase1_artificial_rmp_preflight import sha256_file
from phase1_pricing_candidate_diagnostic import structural_validation
from phase2_rmp_initialization_diagnostic import (
    OUTPUT_DIR as PHASE2_RMP_DIR,
    SCOPE_BOUNDARY as PHASE2_RMP_SCOPE_BOUNDARY,
    rel,
    write_csv,
    write_json,
)
from phase1_one_candidate_add_resolve import ACCEPTED_BASELINE_HASH
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


OUTPUT_DIR = ROOT_DIR / "outputs" / "phase2_pricing_candidate_diagnostic"
HANDOFF_DIR = ROOT_DIR / "outputs" / "phase1_closure_phase2_handoff_precheck"
PHASE2_POOL = HANDOFF_DIR / "phase2_initial_column_pool.csv"
ALLOW_VARIABLE_PHASE2_INITIAL_POOL = False
ALLOW_VARIABLE_PHASE2_INITIAL_OBJECTIVE = False
REPAIRED_SEED_COLUMNS = (
    ROOT_DIR / "outputs" / "second_controlled_benchmark_link55_seed_pool_repair" / "repaired_seed_columns.csv"
)
REQUIRED_INPUTS = [
    PHASE2_RMP_DIR / "phase2_rmp_initialization_summary.json",
    PHASE2_RMP_DIR / "phase2_rmp_dual_solution.json",
    PHASE2_RMP_DIR / "phase2_rmp_solution_by_column.csv",
    PHASE2_RMP_DIR / "phase2_rmp_capacity_usage.csv",
    PHASE2_POOL,
    REPAIRED_SEED_COLUMNS,
]
DUAL_TOL = 1e-7
PHASE2_PRICING_SCOPE_BOUNDARY = (
    "This is a Phase-II pricing candidate diagnostic only. It validates the "
    "Phase-II reduced-cost/stationarity convention on existing real-only RMP "
    "variables, then evaluates a bounded repaired-seed candidate source using "
    "that validated convention. It does not add candidates, mutate baseline "
    "dynamic_columns.csv, mutate phase2_initial_column_pool.csv, re-solve after "
    "candidate evaluation, run add-resolve, run a loop, run full assignment, "
    "run full CG, or claim general convergence, production-scale solving, "
    "GTFS, railway, branch-and-price, reinforcement learning, or exact arc-LP "
    "flow-pattern reproduction."
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_artifact_path(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else ROOT_DIR / path


def refresh_required_inputs() -> None:
    global REQUIRED_INPUTS
    REQUIRED_INPUTS = [
        PHASE2_RMP_DIR / "phase2_rmp_initialization_summary.json",
        PHASE2_RMP_DIR / "phase2_rmp_dual_solution.json",
        PHASE2_RMP_DIR / "phase2_rmp_solution_by_column.csv",
        PHASE2_RMP_DIR / "phase2_rmp_capacity_usage.csv",
        PHASE2_POOL,
        REPAIRED_SEED_COLUMNS,
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
    global PHASE2_RMP_DIR, HANDOFF_DIR, PHASE2_POOL, REPAIRED_SEED_COLUMNS
    global ALLOW_VARIABLE_PHASE2_INITIAL_POOL, ALLOW_VARIABLE_PHASE2_INITIAL_OBJECTIVE
    PHASE2_RMP_DIR = resolve_artifact_path(artifacts.get("phase2_rmp_dir")) or PHASE2_RMP_DIR
    HANDOFF_DIR = resolve_artifact_path(artifacts.get("handoff_dir")) or HANDOFF_DIR
    PHASE2_POOL = (
        resolve_artifact_path(artifacts.get("phase2_initial_pool"))
        or resolve_artifact_path(artifacts.get("phase2_pool"))
        or (HANDOFF_DIR / "phase2_initial_column_pool.csv")
    )
    REPAIRED_SEED_COLUMNS = (
        resolve_artifact_path(artifacts.get("generated_candidate_source"))
        or resolve_artifact_path(artifacts.get("fixed_source"))
        or resolve_artifact_path(artifacts.get("seed_repair_columns"))
        or REPAIRED_SEED_COLUMNS
    )
    allow_variable_pool = artifacts.get("allow_variable_phase2_initial_pool")
    if allow_variable_pool is not None:
        ALLOW_VARIABLE_PHASE2_INITIAL_POOL = bool(allow_variable_pool)
    allow_variable_objective = artifacts.get("allow_variable_phase2_initial_objective")
    if allow_variable_objective is not None:
        ALLOW_VARIABLE_PHASE2_INITIAL_OBJECTIVE = bool(allow_variable_objective)
    refresh_required_inputs()
    return artifacts


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def required_input_blockers() -> list[str]:
    blockers: list[str] = []
    for path in REQUIRED_INPUTS:
        if not path.exists() or path.stat().st_size == 0:
            blockers.append(f"missing or empty required input: {rel(path)}")
    return blockers


def phase2_initialization_blockers(summary: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if summary.get("diagnostic_status") != "PASS":
        blockers.append(f"Phase-II RMP initialization diagnostic status is {summary.get('diagnostic_status')}")
    if summary.get("solver_status") != "optimal":
        blockers.append(f"Phase-II RMP solver status is {summary.get('solver_status')}")
    if (
        not ALLOW_VARIABLE_PHASE2_INITIAL_OBJECTIVE
        and abs(parse_float(summary.get("objective_value"), math.nan) - 397224431.7223479) > 1e-5
    ):
        blockers.append(f"Phase-II RMP objective changed: {summary.get('objective_value')}")
    if summary.get("objective_units_or_cost_field_used") != "generalized_cost":
        blockers.append(f"unexpected Phase-II cost field: {summary.get('objective_units_or_cost_field_used')}")
    if parse_float(summary.get("demand_residual_max"), math.inf) > TOL:
        blockers.append(f"demand residual max too large: {summary.get('demand_residual_max')}")
    if int(summary.get("capacity_violation_count") if summary.get("capacity_violation_count") is not None else -1) != 0:
        blockers.append(f"capacity violation count changed: {summary.get('capacity_violation_count')}")
    if summary.get("artificial_variables_present") is not False:
        blockers.append("Phase-II RMP initialization reports artificial variables present")
    if summary.get("baseline_dynamic_columns_mutated") is not False:
        blockers.append("Phase-II RMP initialization reports baseline mutation")
    if summary.get("phase2_pricing_performed") is not False:
        blockers.append("Phase-II RMP initialization unexpectedly reports pricing")
    if summary.get("new_columns_generated") is not False:
        blockers.append("Phase-II RMP initialization unexpectedly reports generated columns")
    if summary.get("add_resolve_run") is not False or summary.get("cg_loop_run") is not False:
        blockers.append("Phase-II RMP initialization unexpectedly reports add-resolve or loop")
    if summary.get("full_assignment_run") is not False or summary.get("full_cg_run") is not False:
        blockers.append("Phase-II RMP initialization unexpectedly reports full assignment or full CG")
    if summary.get("dual_fields_present") is not True or summary.get("dual_fields_finite") is not True:
        blockers.append("Phase-II RMP dual fields are missing or nonfinite")
    return blockers


def capacity_maps(dual_solution: dict[str, Any]) -> tuple[dict[str, float], dict[str, float]]:
    duals: dict[str, float] = {}
    slacks: dict[str, float] = {}
    for arc_id, payload in dual_solution.get("capacity_inequality_duals", {}).items():
        duals[arc_id] = parse_float(payload.get("marginal"), math.nan)
        slacks[arc_id] = parse_float(payload.get("slack"), math.nan)
    return duals, slacks


def demand_dual_map(dual_solution: dict[str, Any]) -> dict[str, float]:
    return {
        demand_id: parse_float(payload.get("marginal"), math.nan)
        for demand_id, payload in dual_solution.get("demand_equality_duals", {}).items()
    }


def variable_catalog_rows(
    phase2_pool_rows: list[dict[str, str]],
    solution_rows: list[dict[str, str]],
    dual_solution: dict[str, Any],
) -> list[dict[str, Any]]:
    solution_by_id = {row.get("column_id", ""): row for row in solution_rows}
    lower = dual_solution.get("lower_bound_marginals", {})
    upper = dual_solution.get("upper_bound_marginals", {})
    rows: list[dict[str, Any]] = []
    for pool_row in phase2_pool_rows:
        column_id = pool_row.get("column_id", "")
        solution = solution_by_id.get(column_id, {})
        value = parse_float(solution.get("flow"), 0.0)
        lower_bound = parse_float(solution.get("lower_bound"), 0.0)
        upper_bound = parse_float(solution.get("upper_bound"), 0.0)
        active_lower = abs(value - lower_bound) <= TOL
        active_upper = abs(value - upper_bound) <= TOL
        rows.append(
            {
                "variable_id": column_id,
                "variable_type": "real_column",
                "demand_id": pool_row.get("demand_id", ""),
                "path_id": pool_row.get("path_id", ""),
                "column_id": column_id,
                "phase2_pool_column_type": pool_row.get("phase2_pool_column_type", ""),
                "source_metadata": pool_row.get("source_metadata", ""),
                "added_in_phase1_round": pool_row.get("added_in_phase1_round", ""),
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
                "primal_value": value,
                "objective_coefficient": parse_float(solution.get("objective_coefficient"), math.nan),
                "is_artificial": "false",
                "has_dynamic_arc_incidence": "true",
                "arc_sequence": pool_row.get("arc_sequence", ""),
                "active_lower_bound": bool_text(active_lower),
                "active_upper_bound": bool_text(active_upper),
                "positive_interior": bool_text(value > TOL and not active_upper),
                "solver_lower_marginal": lower.get(column_id, ""),
                "solver_upper_marginal": upper.get(column_id, ""),
            }
        )
    return rows


def dot_capacity(
    arc_sequence: str,
    capacity_duals: dict[str, float],
) -> float:
    return sum(capacity_duals.get(arc_id, 0.0) for arc_id in split_sequence(arc_sequence))


def convention_trials(
    catalog_rows: list[dict[str, Any]],
    demand_duals: dict[str, float],
    capacity_duals: dict[str, float],
) -> list[dict[str, Any]]:
    sign_options = [-1.0, 1.0]
    trials: list[dict[str, Any]] = []
    for eq_sign in sign_options:
        for cap_sign in sign_options:
            for lower_sign in sign_options:
                for upper_sign in sign_options:
                    audit_rows: list[dict[str, Any]] = []
                    residuals: list[float] = []
                    bound_signal_ok = True
                    for row in catalog_rows:
                        variable_id = row["variable_id"]
                        demand_id = row["demand_id"]
                        objective = parse_float(row["objective_coefficient"], math.nan)
                        eq_dual = demand_duals.get(demand_id, math.nan)
                        cap_dual_sum = dot_capacity(row["arc_sequence"], capacity_duals)
                        lower = parse_float(row["solver_lower_marginal"], 0.0)
                        upper = parse_float(row["solver_upper_marginal"], 0.0)
                        residual = (
                            objective
                            + eq_sign * eq_dual
                            + cap_sign * cap_dual_sum
                            + lower_sign * lower
                            + upper_sign * upper
                        )
                        residuals.append(residual)
                        active_lower = row["active_lower_bound"] == "true"
                        active_upper = row["active_upper_bound"] == "true"
                        if active_lower and lower < -DUAL_TOL:
                            bound_signal_ok = False
                        if active_upper and upper > DUAL_TOL:
                            bound_signal_ok = False
                        if abs(residual) > DUAL_TOL:
                            kkt_status = "FAIL"
                            interpretation = "stationarity residual exceeds tolerance"
                        elif row["positive_interior"] == "true":
                            kkt_status = "PASS"
                            interpretation = "positive real-column variable satisfies stationarity under validated convention"
                        elif active_lower:
                            kkt_status = "PASS"
                            interpretation = "active lower-bound variable has nonnegative/no-improvement lower-bound signal"
                        elif active_upper:
                            kkt_status = "PASS"
                            interpretation = "active upper-bound variable satisfies stationarity including upper-bound marginal"
                        else:
                            kkt_status = "PASS"
                            interpretation = "real-column variable satisfies stationarity under validated convention"
                        audit_rows.append(
                            {
                                "variable_id": variable_id,
                                "variable_type": row["variable_type"],
                                "demand_id": demand_id,
                                "primal_value": row["primal_value"],
                                "lower_bound": row["lower_bound"],
                                "upper_bound": row["upper_bound"],
                                "objective_coefficient": objective,
                                "demand_equality_dual_raw": eq_dual,
                                "capacity_dual_sum_raw": cap_dual_sum,
                                "solver_lower_marginal": lower,
                                "solver_upper_marginal": upper,
                                "computed_reduced_cost_or_stationarity_residual": residual,
                                "kkt_status": kkt_status,
                                "interpretation": interpretation,
                            }
                        )
                    max_abs = max(abs(value) for value in residuals) if residuals else math.inf
                    trials.append(
                        {
                            "convention_name": (
                                f"stationarity_c{eq_sign:+.0f}eq{cap_sign:+.0f}cap"
                                f"{lower_sign:+.0f}lower{upper_sign:+.0f}upper"
                            ),
                            "eq_marginal_sign": eq_sign,
                            "capacity_marginal_sign": cap_sign,
                            "lower_bound_marginal_sign": lower_sign,
                            "upper_bound_marginal_sign": upper_sign,
                            "max_abs_stationarity_residual": max_abs,
                            "stationarity_passed": max_abs <= DUAL_TOL,
                            "bound_signal_passed": bound_signal_ok,
                            "validation_passed": max_abs <= DUAL_TOL and bound_signal_ok,
                            "rows": audit_rows,
                        }
                    )
    return sorted(trials, key=lambda item: (not item["validation_passed"], item["max_abs_stationarity_residual"]))


def validate_convention(
    catalog_rows: list[dict[str, Any]],
    dual_solution: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[str]]:
    blockers: list[str] = []
    demand_duals = demand_dual_map(dual_solution)
    capacity_duals, _capacity_slacks = capacity_maps(dual_solution)
    if dual_solution.get("dual_fields_present") is not True or dual_solution.get("dual_fields_finite") is not True:
        blockers.append("Phase-II dual fields are missing or nonfinite")
    if not demand_duals or not all(finite(value) for value in demand_duals.values()):
        blockers.append("demand equality duals are missing or nonfinite")
    if not capacity_duals or not all(finite(value) for value in capacity_duals.values()):
        blockers.append("capacity inequality duals are missing or nonfinite")
    if blockers:
        validation = {
            "validation_status": "SAFE_BLOCKED",
            "validated_convention": None,
            "safe_blockers": blockers,
            "stationarity_convention_trials": [],
        }
        return validation, [], blockers

    trials = convention_trials(catalog_rows, demand_duals, capacity_duals)
    selected = next((trial for trial in trials if trial["validation_passed"]), None)
    if selected is None:
        blockers.append("No Phase-II reduced-cost/stationarity convention validated on existing variables")
        selected_rows = trials[0]["rows"] if trials else []
        validation = {
            "validation_status": "SAFE_BLOCKED",
            "validated_convention": None,
            "safe_blockers": blockers,
            "stationarity_convention_trials": [
                {key: value for key, value in trial.items() if key != "rows"} for trial in trials
            ],
        }
        return validation, selected_rows, blockers

    lower_nonzero = any(abs(parse_float(row["solver_lower_marginal"], 0.0)) > DUAL_TOL for row in catalog_rows)
    upper_nonzero = any(abs(parse_float(row["solver_upper_marginal"], 0.0)) > DUAL_TOL for row in catalog_rows)
    selected_no_rows = {key: value for key, value in selected.items() if key != "rows"}
    selected_no_rows["bound_marginal_signs_informative"] = bool(lower_nonzero or upper_nonzero)
    selected_no_rows["candidate_entry_signal_formula"] = (
        "generalized_cost + eq_sign * demand_equality_dual + "
        "capacity_sign * sum(capacity_inequality_duals_on_candidate_arcs)"
    )
    validation = {
        "validation_status": "PASS",
        "validated_convention": selected["convention_name"],
        "validated_convention_details": selected_no_rows,
        "solver": "scipy.optimize.linprog / HiGHS",
        "dual_source": rel(PHASE2_RMP_DIR / "phase2_rmp_dual_solution.json"),
        "dual_convention_source_note": dual_solution.get("dual_convention"),
        "stationarity_convention_trials": [
            {key: value for key, value in trial.items() if key != "rows"} for trial in trials
        ],
        "safe_blockers": [],
    }
    return validation, selected["rows"], []


def candidate_generalized_cost(row: dict[str, str], arc_ids: list[str], arc_by_id: dict[str, dict[str, str]]) -> float:
    listed = parse_float(row.get("generalized_cost"), math.nan)
    if math.isfinite(listed):
        return listed
    return sum(parse_float(arc_by_id[arc_id].get("cost"), 0.0) for arc_id in arc_ids if arc_id in arc_by_id)


def dual_arc_flags(
    arc_ids: list[str],
    capacity_duals: dict[str, float],
    capacity_slacks: dict[str, float],
    cap_sign: float,
) -> list[str]:
    flagged: list[str] = []
    for arc_id in arc_ids:
        raw_dual = capacity_duals.get(arc_id, 0.0)
        signed_signal = cap_sign * raw_dual
        slack = capacity_slacks.get(arc_id, math.inf)
        if abs(raw_dual) > TOL or signed_signal > TOL or slack <= TOL:
            flagged.append(arc_id)
    return flagged


def evaluate_candidates(
    source_rows: list[dict[str, str]],
    phase2_pool_rows: list[dict[str, str]],
    demands: list[dict[str, str]],
    arcs: list[dict[str, str]],
    dual_solution: dict[str, Any],
    validation: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    details = validation["validated_convention_details"]
    eq_sign = parse_float(details.get("eq_marginal_sign"), math.nan)
    cap_sign = parse_float(details.get("capacity_marginal_sign"), math.nan)
    convention_name = validation["validated_convention"]
    demand_ids = {row["demand_id"] for row in demands}
    arc_by_id = {row["arc_id"]: row for row in arcs}
    existing_by_key = {
        (row.get("demand_id", ""), row.get("arc_sequence", "")): row for row in phase2_pool_rows
    }
    demand_duals = demand_dual_map(dual_solution)
    capacity_duals, capacity_slacks = capacity_maps(dual_solution)
    candidate_rows: list[dict[str, Any]] = []
    duplicate_rows: list[dict[str, Any]] = []
    for idx, candidate in enumerate(source_rows, start=1):
        candidate_id = candidate.get("column_id") or candidate.get("path_id") or f"candidate_{idx}"
        demand_id = candidate.get("demand_id", "")
        arc_sequence = candidate.get("arc_sequence", "")
        arc_ids = split_sequence(arc_sequence)
        structurally_valid, invalid_reason = structural_validation(candidate, demand_ids, arc_by_id)
        duplicate = False
        duplicate_of = ""
        if structurally_valid:
            duplicate_row = existing_by_key.get((demand_id, arc_sequence))
            duplicate = duplicate_row is not None
            duplicate_of = duplicate_row.get("column_id", "") if duplicate_row else ""
        cost = candidate_generalized_cost(candidate, arc_ids, arc_by_id) if structurally_valid else math.nan
        demand_dual = demand_duals.get(demand_id, math.nan)
        cap_sum = sum(capacity_duals.get(arc_id, 0.0) for arc_id in arc_ids)
        entry_signal = cost + eq_sign * demand_dual + cap_sign * cap_sum if structurally_valid else math.nan
        if not structurally_valid:
            classification = "invalid_candidate"
        elif duplicate:
            classification = "duplicate_existing_phase2_column"
        elif entry_signal < -TOL:
            classification = "improving_new_candidate"
        else:
            classification = "nonimproving_new_candidate"
        flagged_arcs = dual_arc_flags(arc_ids, capacity_duals, capacity_slacks, cap_sign)
        row = {
            "candidate_id": candidate_id,
            "demand_id": demand_id,
            "candidate_source": rel(REPAIRED_SEED_COLUMNS),
            "path_id": candidate.get("path_id", ""),
            "arc_sequence": arc_sequence,
            "structurally_valid": bool_text(structurally_valid),
            "invalid_reason": invalid_reason,
            "duplicate_existing_phase2_column": bool_text(duplicate),
            "duplicate_of_column_id": duplicate_of,
            "phase2_objective_coefficient": cost if math.isfinite(cost) else "",
            "generalized_cost": cost if math.isfinite(cost) else "",
            "equality_dual_raw": demand_dual if math.isfinite(demand_dual) else "",
            "capacity_dual_sum_raw": cap_sum,
            "validated_stationarity_convention": convention_name,
            "validated_eq_sign": eq_sign,
            "validated_capacity_sign": cap_sign,
            "phase2_entry_signal": entry_signal if math.isfinite(entry_signal) else "",
            "classification": classification,
            "uses_binding_or_nonzero_capacity_dual_arc": bool_text(bool(flagged_arcs)),
            "binding_or_nonzero_dual_arcs_used": "|".join(flagged_arcs),
            "currently_in_phase2_pool": bool_text(duplicate),
            "would_be_added_in_future_task": "false",
        }
        candidate_rows.append(row)
        duplicate_rows.append(
            {
                "candidate_id": candidate_id,
                "demand_id": demand_id,
                "arc_sequence": arc_sequence,
                "duplicate_existing_phase2_column": bool_text(duplicate),
                "duplicate_of_column_id": duplicate_of,
                "classification": classification,
            }
        )
    return candidate_rows, duplicate_rows


def write_reports(
    output_dir: Path,
    summary: dict[str, Any],
    validation: dict[str, Any],
) -> None:
    validation_lines = [
        "# Phase-II Dual Convention Validation",
        "",
        PHASE2_PRICING_SCOPE_BOUNDARY,
        "",
        f"- Validation status: {validation.get('validation_status')}",
        f"- Validated convention: {validation.get('validated_convention')}",
        f"- Solver: {validation.get('solver')}",
        f"- Dual source: {validation.get('dual_source')}",
        "- Bound marginal signs informative: "
        + str(validation.get("validated_convention_details", {}).get("bound_marginal_signs_informative")),
        "",
        "Candidate entry signals are only computed when validation passes.",
    ]
    (output_dir / "phase2_dual_validation_report.md").write_text(
        "\n".join(validation_lines) + "\n", encoding="utf-8"
    )
    report_lines = [
        "# Phase-II Pricing Candidate Diagnostic",
        "",
        PHASE2_PRICING_SCOPE_BOUNDARY,
        "",
        f"- Diagnostic status: {summary['diagnostic_status']}",
        f"- Phase-II dual convention validation status: {summary['phase2_dual_convention_validation_status']}",
        f"- Validated convention: {summary.get('validated_convention')}",
        f"- Candidate source: {summary.get('candidate_source')}",
        f"- Total candidates: {summary.get('total_candidate_count')}",
        f"- Structurally valid candidates: {summary.get('structurally_valid_candidate_count')}",
        f"- Duplicate candidates: {summary.get('duplicate_candidate_count')}",
        f"- Improving non-duplicate candidates: {summary.get('improving_new_candidate_count')}",
        f"- Best improving candidate: {summary.get('best_improving_candidate_id')}",
        f"- Best improving entry signal: {summary.get('best_improving_candidate_entry_signal')}",
        "",
        "## Scope Guardrails",
        "",
        f"- Candidates added: {summary.get('candidates_added')}",
        f"- RMP re-solved after candidate evaluation: {summary.get('rmp_resolved_after_pricing')}",
        f"- Add-resolve run: {summary.get('add_resolve_run')}",
        f"- CG loop run: {summary.get('cg_loop_run')}",
        f"- Full assignment run: {summary.get('full_assignment_run')}",
        f"- Full CG run: {summary.get('full_cg_run')}",
        "",
        "## Next Safe Step",
        "",
        summary.get("next_safe_step", ""),
    ]
    (output_dir / "phase2_pricing_report.md").write_text(
        "\n".join(report_lines) + "\n", encoding="utf-8"
    )


def write_safe_blocker_outputs(
    output_dir: Path,
    blockers: list[str],
    baseline_hash_before: str,
    phase2_pool_hash_before: str,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    validation = {
        "validation_status": "SAFE_BLOCKED",
        "validated_convention": None,
        "safe_blockers": blockers,
        "stationarity_convention_trials": [],
    }
    summary = {
        "diagnostic_status": "SAFE_BLOCKED",
        "phase2_dual_convention_validation_status": "SAFE_BLOCKED",
        "validated_convention": None,
        "candidate_source": rel(REPAIRED_SEED_COLUMNS),
        "total_candidate_count": 0,
        "structurally_valid_candidate_count": 0,
        "duplicate_candidate_count": 0,
        "improving_new_candidate_count": 0,
        "improving_new_candidate_count_by_demand": {},
        "best_improving_candidate_id": None,
        "best_improving_candidate_entry_signal": None,
        "baseline_dynamic_columns_hash_before": baseline_hash_before,
        "baseline_dynamic_columns_hash_after": baseline_hash_before,
        "baseline_dynamic_columns_mutated": False,
        "phase2_initial_pool_hash_before": phase2_pool_hash_before,
        "phase2_initial_pool_hash_after": phase2_pool_hash_before,
        "phase2_initial_pool_mutated": False,
        "candidates_added": False,
        "rmp_resolved_after_pricing": False,
        "add_resolve_run": False,
        "cg_loop_run": False,
        "full_assignment_run": False,
        "full_cg_run": False,
        "safe_blockers": blockers,
        "next_safe_step": "review safe blockers before Phase-II pricing candidate diagnostics",
        "scope": PHASE2_PRICING_SCOPE_BOUNDARY,
    }
    write_json(output_dir / "phase2_dual_convention_validation.json", validation)
    write_csv(output_dir / "phase2_variable_catalog.csv", [], ["variable_id"])
    write_csv(output_dir / "phase2_existing_variable_stationarity_audit.csv", [], ["variable_id"])
    write_csv(output_dir / "phase2_pricing_candidates.csv", [], ["candidate_id"])
    write_csv(output_dir / "phase2_candidate_duplicate_audit.csv", [], ["candidate_id"])
    write_json(output_dir / "phase2_candidate_source_manifest.json", {"safe_blockers": blockers})
    write_json(output_dir / "phase2_pricing_summary.json", summary)
    write_json(
        output_dir / "phase2_pricing_hash_audit.json",
        {
            "baseline_dynamic_columns_hash_before": baseline_hash_before,
            "baseline_dynamic_columns_hash_after": baseline_hash_before,
            "baseline_dynamic_columns_mutated": False,
            "phase2_initial_pool_hash_before": phase2_pool_hash_before,
            "phase2_initial_pool_hash_after": phase2_pool_hash_before,
            "phase2_initial_pool_mutated": False,
            "safe_blockers": blockers,
        },
    )
    write_reports(output_dir, summary, validation)
    return summary


def run_diagnostic(
    config_path: str | Path = DEFAULT_CURRENT_POOL_CONFIG,
    output_dir: Path = OUTPUT_DIR,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    config = load_config(config_path)
    data_dir = input_data_dir(config)
    baseline_path = data_dir / "dynamic_columns.csv"
    baseline_hash_before = sha256_file(baseline_path)
    phase2_pool_hash_before = sha256_file(PHASE2_POOL) if PHASE2_POOL.exists() else ""

    blockers = required_input_blockers()
    if blockers:
        return write_safe_blocker_outputs(output_dir, blockers, baseline_hash_before, phase2_pool_hash_before)

    phase2_summary = read_json(PHASE2_RMP_DIR / "phase2_rmp_initialization_summary.json")
    dual_solution = read_json(PHASE2_RMP_DIR / "phase2_rmp_dual_solution.json")
    solution_rows = read_csv(PHASE2_RMP_DIR / "phase2_rmp_solution_by_column.csv")
    phase2_pool_rows = read_csv(PHASE2_POOL)
    candidate_source_rows = read_csv(REPAIRED_SEED_COLUMNS)
    arcs = read_csv(data_dir / "dynamic_arc.csv")
    demands = read_csv(data_dir / "dynamic_demand.csv")
    blockers.extend(phase2_initialization_blockers(phase2_summary))
    if not ALLOW_VARIABLE_PHASE2_INITIAL_POOL and len(phase2_pool_rows) != 10:
        blockers.append(f"Phase-II initial pool count is {len(phase2_pool_rows)}, expected 10")
    if any(row.get("column_id", "").startswith("ARTIFICIAL_DEMAND_") for row in phase2_pool_rows):
        blockers.append("Phase-II initial pool contains artificial variables")
    if not candidate_source_rows:
        blockers.append("bounded candidate source is empty")
    if blockers:
        return write_safe_blocker_outputs(output_dir, blockers, baseline_hash_before, phase2_pool_hash_before)

    catalog_rows = variable_catalog_rows(phase2_pool_rows, solution_rows, dual_solution)
    validation, stationarity_rows, validation_blockers = validate_convention(catalog_rows, dual_solution)
    if validation_blockers:
        summary = write_safe_blocker_outputs(
            output_dir, validation_blockers, baseline_hash_before, phase2_pool_hash_before
        )
        write_json(output_dir / "phase2_dual_convention_validation.json", validation)
        write_csv(
            output_dir / "phase2_variable_catalog.csv",
            catalog_rows,
            [
                "variable_id",
                "variable_type",
                "demand_id",
                "path_id",
                "column_id",
                "phase2_pool_column_type",
                "source_metadata",
                "added_in_phase1_round",
                "lower_bound",
                "upper_bound",
                "primal_value",
                "objective_coefficient",
                "is_artificial",
                "has_dynamic_arc_incidence",
                "arc_sequence",
                "active_lower_bound",
                "active_upper_bound",
                "positive_interior",
                "solver_lower_marginal",
                "solver_upper_marginal",
            ],
        )
        write_csv(output_dir / "phase2_existing_variable_stationarity_audit.csv", stationarity_rows, [])
        return summary

    candidate_rows, duplicate_rows = evaluate_candidates(
        candidate_source_rows, phase2_pool_rows, demands, arcs, dual_solution, validation
    )
    baseline_hash_after = sha256_file(baseline_path)
    phase2_pool_hash_after = sha256_file(PHASE2_POOL)
    structurally_valid = [row for row in candidate_rows if row["structurally_valid"] == "true"]
    duplicates = [row for row in candidate_rows if row["duplicate_existing_phase2_column"] == "true"]
    improving = [row for row in candidate_rows if row["classification"] == "improving_new_candidate"]
    improving_by_demand: dict[str, int] = {}
    for row in improving:
        improving_by_demand[row["demand_id"]] = improving_by_demand.get(row["demand_id"], 0) + 1
    best = min(
        improving,
        key=lambda row: parse_float(row["phase2_entry_signal"], math.inf),
        default=None,
    )
    source_manifest = {
        "candidate_source_status": "PASS",
        "candidate_source": rel(REPAIRED_SEED_COLUMNS),
        "candidate_source_sha256": sha256_file(REPAIRED_SEED_COLUMNS),
        "candidate_source_row_count": len(candidate_source_rows),
        "bounded_reviewable_candidate_source": True,
        "broad_path_enumerator_run": False,
        "external_data_used": False,
        "phase2_current_pool_reference": rel(PHASE2_POOL),
        "phase2_current_pool_column_count": len(phase2_pool_rows),
    }
    summary = {
        "diagnostic_status": "PASS",
        "phase2_dual_convention_validation_status": validation["validation_status"],
        "validated_convention": validation["validated_convention"],
        "candidate_source": rel(REPAIRED_SEED_COLUMNS),
        "total_candidate_count": len(candidate_rows),
        "structurally_valid_candidate_count": len(structurally_valid),
        "duplicate_candidate_count": len(duplicates),
        "improving_new_candidate_count": len(improving),
        "improving_new_candidate_count_by_demand": improving_by_demand,
        "best_improving_candidate_id": best["candidate_id"] if best else None,
        "best_improving_candidate_entry_signal": parse_float(best["phase2_entry_signal"], math.nan)
        if best
        else None,
        "baseline_dynamic_columns_hash_before": baseline_hash_before,
        "baseline_dynamic_columns_hash_after": baseline_hash_after,
        "baseline_dynamic_columns_mutated": baseline_hash_before != baseline_hash_after,
        "phase2_initial_pool_hash_before": phase2_pool_hash_before,
        "phase2_initial_pool_hash_after": phase2_pool_hash_after,
        "phase2_initial_pool_mutated": phase2_pool_hash_before != phase2_pool_hash_after,
        "candidates_added": False,
        "rmp_resolved_after_pricing": False,
        "add_resolve_run": False,
        "cg_loop_run": False,
        "full_assignment_run": False,
        "full_cg_run": False,
        "general_convergence_claimed": False,
        "exact_arc_lp_flow_pattern_reproduction_claimed": False,
        "safe_blockers": [],
        "next_safe_step": "one-candidate Phase-II add-resolve diagnostic"
        if improving
        else "candidate source expansion or safe blocker review",
        "scope": PHASE2_PRICING_SCOPE_BOUNDARY,
    }
    hash_audit = {
        "baseline_dynamic_columns_path": rel(baseline_path),
        "baseline_dynamic_columns_hash_before": baseline_hash_before,
        "baseline_dynamic_columns_hash_after": baseline_hash_after,
        "accepted_baseline_dynamic_columns_hash": ACCEPTED_BASELINE_HASH,
        "baseline_dynamic_columns_mutated": baseline_hash_before != baseline_hash_after,
        "phase2_initial_pool_path": rel(PHASE2_POOL),
        "phase2_initial_pool_hash_before": phase2_pool_hash_before,
        "phase2_initial_pool_hash_after": phase2_pool_hash_after,
        "phase2_initial_pool_mutated": phase2_pool_hash_before != phase2_pool_hash_after,
        "candidate_source_path": rel(REPAIRED_SEED_COLUMNS),
        "candidate_source_sha256": sha256_file(REPAIRED_SEED_COLUMNS),
        "candidates_added": False,
        "rmp_resolved_after_pricing": False,
        "add_resolve_run": False,
        "cg_loop_run": False,
        "full_assignment_run": False,
        "full_cg_run": False,
    }

    write_json(output_dir / "phase2_dual_convention_validation.json", validation)
    write_csv(
        output_dir / "phase2_variable_catalog.csv",
        catalog_rows,
        [
            "variable_id",
            "variable_type",
            "demand_id",
            "path_id",
            "column_id",
            "phase2_pool_column_type",
            "source_metadata",
            "added_in_phase1_round",
            "lower_bound",
            "upper_bound",
            "primal_value",
            "objective_coefficient",
            "is_artificial",
            "has_dynamic_arc_incidence",
            "arc_sequence",
            "active_lower_bound",
            "active_upper_bound",
            "positive_interior",
            "solver_lower_marginal",
            "solver_upper_marginal",
        ],
    )
    write_csv(
        output_dir / "phase2_existing_variable_stationarity_audit.csv",
        stationarity_rows,
        [
            "variable_id",
            "variable_type",
            "demand_id",
            "primal_value",
            "lower_bound",
            "upper_bound",
            "objective_coefficient",
            "demand_equality_dual_raw",
            "capacity_dual_sum_raw",
            "solver_lower_marginal",
            "solver_upper_marginal",
            "computed_reduced_cost_or_stationarity_residual",
            "kkt_status",
            "interpretation",
        ],
    )
    write_csv(
        output_dir / "phase2_pricing_candidates.csv",
        candidate_rows,
        [
            "candidate_id",
            "demand_id",
            "candidate_source",
            "path_id",
            "arc_sequence",
            "structurally_valid",
            "invalid_reason",
            "duplicate_existing_phase2_column",
            "duplicate_of_column_id",
            "phase2_objective_coefficient",
            "generalized_cost",
            "equality_dual_raw",
            "capacity_dual_sum_raw",
            "validated_stationarity_convention",
            "validated_eq_sign",
            "validated_capacity_sign",
            "phase2_entry_signal",
            "classification",
            "uses_binding_or_nonzero_capacity_dual_arc",
            "binding_or_nonzero_dual_arcs_used",
            "currently_in_phase2_pool",
            "would_be_added_in_future_task",
        ],
    )
    write_csv(
        output_dir / "phase2_candidate_duplicate_audit.csv",
        duplicate_rows,
        [
            "candidate_id",
            "demand_id",
            "arc_sequence",
            "duplicate_existing_phase2_column",
            "duplicate_of_column_id",
            "classification",
        ],
    )
    write_json(output_dir / "phase2_candidate_source_manifest.json", source_manifest)
    write_json(output_dir / "phase2_pricing_summary.json", summary)
    write_json(output_dir / "phase2_pricing_hash_audit.json", hash_audit)
    write_json(output_dir / "phase2_pricing_precheck.json", {
        "precheck_status": "PASS",
        "phase2_initialization_scope": PHASE2_RMP_SCOPE_BOUNDARY,
        "phase2_initialization_stable": True,
        "candidate_source_status": "PASS",
        "candidate_source": rel(REPAIRED_SEED_COLUMNS),
        "convention_validation_required_before_candidate_evaluation": True,
        "convention_validation_passed": True,
        "candidates_added": False,
        "rmp_resolved_after_pricing": False,
    })
    write_reports(output_dir, summary, validation)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase-II pricing candidate diagnostic.")
    parser.add_argument("--config", default=DEFAULT_CURRENT_POOL_CONFIG)
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
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
    apply_input_manifest(args.input_artifacts_json)
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = ROOT_DIR / output_dir
    if args.no_mutate_accepted_outputs and output_dir.resolve() == OUTPUT_DIR.resolve():
        print("Refusing to write to accepted default Phase-II pricing folder with --no-mutate-accepted-outputs.")
        return 1
    summary = run_diagnostic(args.config, output_dir)
    print(f"Phase-II pricing candidate diagnostic status: {summary['diagnostic_status']}")
    print(f"Dual convention validation status: {summary.get('phase2_dual_convention_validation_status')}")
    print(f"Validated convention: {summary.get('validated_convention')}")
    print(f"Candidate source: {summary.get('candidate_source')}")
    print(f"Total candidates: {summary.get('total_candidate_count')}")
    print(f"Structurally valid candidates: {summary.get('structurally_valid_candidate_count')}")
    print(f"Duplicate candidates: {summary.get('duplicate_candidate_count')}")
    print(f"Improving new candidates: {summary.get('improving_new_candidate_count')}")
    print(f"Best improving candidate: {summary.get('best_improving_candidate_id')}")
    print(f"Baseline dynamic_columns.csv mutated: {summary.get('baseline_dynamic_columns_mutated')}")
    print(f"Phase-II initial pool mutated: {summary.get('phase2_initial_pool_mutated')}")
    print(f"Candidates added: {summary.get('candidates_added')}")
    print(f"RMP re-solved after candidate evaluation: {summary.get('rmp_resolved_after_pricing')}")
    print(f"Report: {output_dir / 'phase2_pricing_report.md'}")
    return 0 if summary["diagnostic_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
