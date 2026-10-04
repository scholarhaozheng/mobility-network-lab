"""Phase-I artificial RMP dual and schema audit.

This audit is intentionally bounded. It reruns the accepted Phase-I
artificial-demand-variable RMP preflight, reconstructs the same seven-variable
RMP, extracts raw SciPy/HiGHS marginals, and validates a stationarity
convention on existing variables only.

It does not generate candidate columns, run pricing, add real columns,
run add-resolve, run a controlled loop, transition to Phase II, run full
assignment, or run full CG.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from phase1_artificial_rmp_preflight import (
    ARTIFICIAL_PENALTY,
    OUTPUT_DIR as PREFLIGHT_OUTPUT_DIR,
    PHASE1_SCOPE_BOUNDARY,
    ROOT_DIR,
    TRUE_COST_TIE_BREAKER_EPSILON,
    run_preflight,
    sha256_file,
    status_from_linprog,
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


OUTPUT_DIR = ROOT_DIR / "outputs" / "phase1_artificial_dual_audit"
DUAL_TOL = 1e-7
STABILITY_TOL = 1e-6
EXPECTED_TOTAL_ARTIFICIAL_FLOW = 6287.557003
DUAL_SCOPE_BOUNDARY = (
    "This is a Phase-I dual/schema audit for the accepted artificial-demand "
    "RMP preflight. It extracts raw SciPy/HiGHS dual fields and validates "
    "stationarity on existing Phase-I variables only. It does not generate "
    "candidate columns, run pricing, add columns, run add-resolve, run a "
    "controlled loop, transition to Phase II, run full assignment, run full "
    "CG, or claim general convergence, production-scale solving, GTFS, "
    "railway, branch-and-price, RL, or exact arc-LP flow-pattern reproduction."
)


@dataclass(frozen=True)
class Phase1Variable:
    variable_id: str
    variable_type: str
    demand_id: str
    path_id: str
    column_id: str
    lower_bound: float
    upper_bound: float
    objective_coefficient: float
    is_artificial: bool
    has_dynamic_arc_incidence: bool
    arc_sequence: str


@dataclass(frozen=True)
class Phase1Model:
    variables: list[Phase1Variable]
    objective: list[float]
    bounds: list[tuple[float, float]]
    demand_ids: list[str]
    demand_rhs: list[float]
    arc_ids: list[str]
    capacity_rhs: list[float]
    eq_coefficients: list[list[float]]
    ub_coefficients: list[list[float]]


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def finite_or_none(value: Any) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if math.isfinite(numeric) else None


def all_finite(values: list[Any]) -> bool:
    return all(finite_or_none(value) is not None for value in values)


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def build_phase1_model(
    arcs: list[dict[str, str]],
    demands: list[dict[str, str]],
    real_columns: list[dict[str, str]],
) -> Phase1Model:
    demand_ids = [row["demand_id"] for row in demands]
    demand_rhs = [parse_float(row["volume"], 0.0) for row in demands]
    demand_volume = dict(zip(demand_ids, demand_rhs))
    arc_ids = [row["arc_id"] for row in arcs]
    arc_index = {arc_id: idx for idx, arc_id in enumerate(arc_ids)}
    capacity_rhs = [max(0.0, parse_float(row.get("capacity"), 0.0)) for row in arcs]

    variables: list[Phase1Variable] = []
    for column in real_columns:
        demand_id = column["demand_id"]
        variables.append(
            Phase1Variable(
                variable_id=column["column_id"],
                variable_type="real_column",
                demand_id=demand_id,
                path_id=column.get("path_id", ""),
                column_id=column.get("column_id", ""),
                lower_bound=0.0,
                upper_bound=demand_volume[demand_id],
                objective_coefficient=TRUE_COST_TIE_BREAKER_EPSILON
                * parse_float(column.get("generalized_cost"), 0.0),
                is_artificial=False,
                has_dynamic_arc_incidence=True,
                arc_sequence=column.get("arc_sequence", ""),
            )
        )
    for demand in demands:
        demand_id = demand["demand_id"]
        variables.append(
            Phase1Variable(
                variable_id=f"ARTIFICIAL_DEMAND_{demand_id}",
                variable_type="artificial_demand",
                demand_id=demand_id,
                path_id="",
                column_id="",
                lower_bound=0.0,
                upper_bound=demand_volume[demand_id],
                objective_coefficient=ARTIFICIAL_PENALTY,
                is_artificial=True,
                has_dynamic_arc_incidence=False,
                arc_sequence="",
            )
        )

    eq_coefficients = [[0.0 for _ in variables] for _ in demand_ids]
    demand_index = {demand_id: idx for idx, demand_id in enumerate(demand_ids)}
    for var_pos, variable in enumerate(variables):
        eq_coefficients[demand_index[variable.demand_id]][var_pos] = 1.0

    ub_coefficients = [[0.0 for _ in variables] for _ in arc_ids]
    for var_pos, variable in enumerate(variables):
        if variable.is_artificial:
            continue
        for arc_id in split_sequence(variable.arc_sequence):
            ub_coefficients[arc_index[arc_id]][var_pos] = 1.0

    return Phase1Model(
        variables=variables,
        objective=[variable.objective_coefficient for variable in variables],
        bounds=[(variable.lower_bound, variable.upper_bound) for variable in variables],
        demand_ids=demand_ids,
        demand_rhs=demand_rhs,
        arc_ids=arc_ids,
        capacity_rhs=capacity_rhs,
        eq_coefficients=eq_coefficients,
        ub_coefficients=ub_coefficients,
    )


def solve_model(model: Phase1Model) -> tuple[dict[str, Any], Any | None]:
    try:
        from scipy.optimize import linprog
        from scipy.sparse import csr_matrix
    except ImportError as exc:
        return {
            "solver_status": "solver_unavailable",
            "solver_message": f"scipy.optimize.linprog is unavailable: {exc}",
            "linprog_status_code": None,
            "objective_value": None,
        }, None

    result = linprog(
        c=model.objective,
        A_ub=csr_matrix(model.ub_coefficients),
        b_ub=model.capacity_rhs,
        A_eq=csr_matrix(model.eq_coefficients),
        b_eq=model.demand_rhs,
        bounds=model.bounds,
        method="highs",
    )
    return {
        "solver_status": status_from_linprog(result),
        "solver_message": result.message,
        "linprog_status_code": int(result.status),
        "objective_value": float(result.fun) if result.success else None,
    }, result


def dot_column(coefficients: list[list[float]], marginals: list[float], variable_index: int) -> float:
    return sum(row[variable_index] * marginal for row, marginal in zip(coefficients, marginals))


def model_arc_flow(model: Phase1Model, values: list[float]) -> list[float]:
    return [
        sum(row[var_pos] * values[var_pos] for var_pos in range(len(model.variables)))
        for row in model.ub_coefficients
    ]


def vector_from_result_field(result: Any, field_name: str, child_name: str) -> list[float] | None:
    child = getattr(result, field_name, None)
    if child is None or not hasattr(child, child_name):
        return None
    return [float(value) for value in getattr(child, child_name)]


def build_variable_catalog(model: Phase1Model, values: list[float]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for variable, value in zip(model.variables, values):
        active_lower = abs(value - variable.lower_bound) <= TOL
        active_upper = abs(value - variable.upper_bound) <= TOL
        positive_interior = value > TOL and not active_upper
        rows.append(
            {
                "variable_id": variable.variable_id,
                "variable_type": variable.variable_type,
                "demand_id": variable.demand_id,
                "path_id": variable.path_id,
                "column_id": variable.column_id,
                "lower_bound": variable.lower_bound,
                "upper_bound": variable.upper_bound,
                "primal_value": value,
                "objective_coefficient": variable.objective_coefficient,
                "is_artificial": bool_text(variable.is_artificial),
                "has_dynamic_arc_incidence": bool_text(variable.has_dynamic_arc_incidence),
                "arc_sequence": variable.arc_sequence,
                "active_lower_bound": bool_text(active_lower),
                "active_upper_bound": bool_text(active_upper),
                "positive_interior": bool_text(positive_interior),
            }
        )
    return rows


def convention_trials(
    model: Phase1Model,
    values: list[float],
    eq_marginals: list[float],
    ub_marginals: list[float],
    lower_marginals: list[float],
    upper_marginals: list[float],
) -> list[dict[str, Any]]:
    trials: list[dict[str, Any]] = []
    sign_options = [-1.0, 1.0]
    for eq_sign in sign_options:
        for ub_sign in sign_options:
            for lower_sign in sign_options:
                for upper_sign in sign_options:
                    residuals: list[float] = []
                    rows: list[dict[str, Any]] = []
                    bound_signal_ok = True
                    for idx, variable in enumerate(model.variables):
                        residual = (
                            variable.objective_coefficient
                            + eq_sign * dot_column(model.eq_coefficients, eq_marginals, idx)
                            + ub_sign * dot_column(model.ub_coefficients, ub_marginals, idx)
                            + lower_sign * lower_marginals[idx]
                            + upper_sign * upper_marginals[idx]
                        )
                        residuals.append(residual)
                        active_lower = abs(values[idx] - variable.lower_bound) <= TOL
                        active_upper = abs(values[idx] - variable.upper_bound) <= TOL
                        if active_lower and lower_marginals[idx] < -DUAL_TOL:
                            bound_signal_ok = False
                        if active_upper and upper_marginals[idx] > DUAL_TOL:
                            bound_signal_ok = False
                        rows.append(
                            {
                                "variable_id": variable.variable_id,
                                "variable_type": variable.variable_type,
                                "demand_id": variable.demand_id,
                                "primal_value": values[idx],
                                "lower_bound": variable.lower_bound,
                                "upper_bound": variable.upper_bound,
                                "objective_coefficient": variable.objective_coefficient,
                                "computed_reduced_cost_or_stationarity_residual": residual,
                                "solver_lower_marginal": lower_marginals[idx],
                                "solver_upper_marginal": upper_marginals[idx],
                                "kkt_status": "PASS" if abs(residual) <= DUAL_TOL else "FAIL",
                                "interpretation": interpretation_for_variable(
                                    variable,
                                    values[idx],
                                    residual,
                                    lower_marginals[idx],
                                    upper_marginals[idx],
                                ),
                            }
                        )
                    max_abs = max(abs(value) for value in residuals)
                    trials.append(
                        {
                            "convention_name": (
                                f"stationarity_c{eq_sign:+.0f}eq{ub_sign:+.0f}cap"
                                f"{lower_sign:+.0f}lower{upper_sign:+.0f}upper"
                            ),
                            "eq_marginal_sign": eq_sign,
                            "capacity_marginal_sign": ub_sign,
                            "lower_bound_marginal_sign": lower_sign,
                            "upper_bound_marginal_sign": upper_sign,
                            "max_abs_stationarity_residual": max_abs,
                            "stationarity_passed": max_abs <= DUAL_TOL,
                            "bound_signal_passed": bound_signal_ok,
                            "validation_passed": max_abs <= DUAL_TOL and bound_signal_ok,
                            "rows": rows,
                        }
                    )
    return sorted(trials, key=lambda item: (not item["validation_passed"], item["max_abs_stationarity_residual"]))


def interpretation_for_variable(
    variable: Phase1Variable,
    value: float,
    residual: float,
    lower_marginal: float,
    upper_marginal: float,
) -> str:
    active_lower = abs(value - variable.lower_bound) <= TOL
    active_upper = abs(value - variable.upper_bound) <= TOL
    if abs(residual) > DUAL_TOL:
        return "stationarity residual exceeds tolerance"
    if active_lower:
        return "active lower bound with nonnegative/no-improvement lower-bound signal"
    if active_upper:
        return "active upper bound with validated stationarity including upper-bound marginal"
    if variable.is_artificial:
        return "positive artificial demand variable satisfies stationarity under validated convention"
    return "positive real-column variable satisfies stationarity under validated convention"


def build_dual_solution(
    model: Phase1Model,
    result: Any,
    solver_info: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, list[float]]]:
    values = [float(value) for value in result.x]
    eq_marginals = vector_from_result_field(result, "eqlin", "marginals") or []
    eq_residuals = vector_from_result_field(result, "eqlin", "residual") or []
    ub_marginals = vector_from_result_field(result, "ineqlin", "marginals") or []
    ub_residuals = vector_from_result_field(result, "ineqlin", "residual") or []
    lower_marginals = vector_from_result_field(result, "lower", "marginals") or []
    lower_residuals = vector_from_result_field(result, "lower", "residual") or []
    upper_marginals = vector_from_result_field(result, "upper", "marginals") or []
    upper_residuals = vector_from_result_field(result, "upper", "residual") or []
    arc_flows = model_arc_flow(model, values)

    finite_values = [
        *values,
        *eq_marginals,
        *eq_residuals,
        *ub_marginals,
        *ub_residuals,
        *lower_marginals,
        *lower_residuals,
        *upper_marginals,
        *upper_residuals,
    ]
    dual_fields_present = all(
        [
            eq_marginals,
            eq_residuals,
            ub_marginals,
            ub_residuals,
            lower_marginals,
            lower_residuals,
            upper_marginals,
            upper_residuals,
        ]
    )
    payload = {
        "solver": "scipy.optimize.linprog / HiGHS",
        "dual_convention": "raw SciPy/HiGHS marginals",
        "solver_status": solver_info["solver_status"],
        "solver_message": solver_info["solver_message"],
        "linprog_status_code": solver_info["linprog_status_code"],
        "objective_value_artificial_penalty_units": solver_info["objective_value"],
        "dual_fields_present": dual_fields_present,
        "dual_fields_finite": all_finite(finite_values),
        "variable_values": {
            variable.variable_id: values[idx] for idx, variable in enumerate(model.variables)
        },
        "equality_duals_by_demand_constraint": {
            demand_id: {
                "raw_marginal": eq_marginals[idx],
                "residual": eq_residuals[idx],
                "rhs": model.demand_rhs[idx],
            }
            for idx, demand_id in enumerate(model.demand_ids)
        },
        "capacity_duals_by_dynamic_arc": {
            arc_id: {
                "raw_marginal": ub_marginals[idx],
                "residual_slack": ub_residuals[idx],
                "rhs_capacity": model.capacity_rhs[idx],
                "capacity_consuming_flow": arc_flows[idx],
            }
            for idx, arc_id in enumerate(model.arc_ids)
        },
        "variable_bound_marginals_by_variable": {
            variable.variable_id: {
                "lower_marginal": lower_marginals[idx],
                "lower_residual": lower_residuals[idx],
                "upper_marginal": upper_marginals[idx],
                "upper_residual": upper_residuals[idx],
                "lower_bound": variable.lower_bound,
                "upper_bound": variable.upper_bound,
                "primal_value": values[idx],
            }
            for idx, variable in enumerate(model.variables)
        },
        "constraint_residuals": {
            "demand_equalities": dict(zip(model.demand_ids, eq_residuals)),
            "capacity_inequalities": dict(zip(model.arc_ids, ub_residuals)),
        },
    }
    raw_vectors = {
        "values": values,
        "eq_marginals": eq_marginals,
        "ub_marginals": ub_marginals,
        "lower_marginals": lower_marginals,
        "upper_marginals": upper_marginals,
    }
    return payload, raw_vectors


def preflight_stability_checks(summary: dict[str, Any], baseline_hash_before: str) -> list[str]:
    blockers: list[str] = []
    if summary.get("solver_status") != "optimal":
        blockers.append(f"preflight solver status changed: {summary.get('solver_status')}")
    total_artificial = parse_float(summary.get("total_artificial_flow"), math.nan)
    if abs(total_artificial - EXPECTED_TOTAL_ARTIFICIAL_FLOW) > STABILITY_TOL:
        blockers.append(f"total artificial flow changed materially: {total_artificial}")
    artificial_by_demand = summary.get("artificial_flow_by_demand", {})
    if parse_float(artificial_by_demand.get("D3"), 0.0) <= TOL:
        blockers.append("D3 artificial flow is no longer positive")
    if abs(parse_float(artificial_by_demand.get("D4"), 0.0)) > TOL:
        blockers.append(f"D4 artificial flow is no longer zero: {artificial_by_demand.get('D4')}")
    if int(summary.get("capacity_violation_count")) != 0:
        blockers.append(f"capacity violation count changed: {summary.get('capacity_violation_count')}")
    if summary.get("baseline_dynamic_columns_mutated") is not False:
        blockers.append("preflight reports baseline dynamic_columns.csv mutation")
    if summary.get("phase2_transition_allowed") is not False:
        blockers.append("Phase-II transition is no longer blocked")
    if summary.get("baseline_dynamic_columns_hash_after") != baseline_hash_before:
        blockers.append("baseline dynamic_columns.csv hash changed during preflight rerun")
    return blockers


def write_report(
    path: Path,
    summary: dict[str, Any],
    catalog_rows: list[dict[str, Any]],
    audit_rows: list[dict[str, Any]],
) -> None:
    positive = [row for row in catalog_rows if row["positive_interior"] == "true"]
    lower = [row for row in catalog_rows if row["active_lower_bound"] == "true"]
    upper = [row for row in catalog_rows if row["active_upper_bound"] == "true"]
    lines = [
        "# Phase-I Dual Validation Report",
        "",
        DUAL_SCOPE_BOUNDARY,
        "",
        "## Summary",
        "",
        f"- Preflight stability status: {summary['preflight_stability_status']}",
        f"- Dual extraction status: {summary['dual_extraction_status']}",
        f"- Reduced-cost/stationarity validation status: {summary['reduced_cost_convention_validation_status']}",
        f"- Validated convention: {summary.get('validated_stationarity_convention')}",
        f"- Pricing safe to implement next: {summary['phase1_pricing_candidate_diagnostics_safe_next']}",
        f"- Total artificial flow: {summary['preflight_total_artificial_flow']}",
        f"- Phase-II transition allowed: {summary['phase2_transition_allowed']}",
        "",
        "## Variable Sets",
        "",
        f"- Positive/interior variables: {', '.join(row['variable_id'] for row in positive) if positive else 'None'}",
        f"- Active lower-bound variables: {', '.join(row['variable_id'] for row in lower) if lower else 'None'}",
        f"- Active upper-bound variables: {', '.join(row['variable_id'] for row in upper) if upper else 'None'}",
        "",
        "## Artificial Variable Behavior",
        "",
    ]
    for row in catalog_rows:
        if row["variable_type"] == "artificial_demand":
            audit = next((item for item in audit_rows if item["variable_id"] == row["variable_id"]), {})
            lines.append(
                f"- {row['variable_id']}: value={row['primal_value']}, active_lower={row['active_lower_bound']}, "
                f"has_arc_incidence={row['has_dynamic_arc_incidence']}, kkt={audit.get('kkt_status')}"
            )
    lines.extend(
        [
            "",
            "## Out Of Scope",
            "",
            "- No candidate generation was run.",
            "- No Phase-I pricing over a candidate space was run.",
            "- No columns were added.",
            "- No add-resolve, controlled loop, Phase-II transition, full assignment, or full CG was run.",
        ]
    )
    if summary.get("safe_blockers"):
        lines.extend(["", "## Safe Blockers", ""])
        lines.extend(f"- {item}" for item in summary["safe_blockers"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_outputs(
    output_dir: Path,
    dual_solution: dict[str, Any],
    catalog_rows: list[dict[str, Any]],
    audit_rows: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "phase1_dual_solution.json").write_text(
        json.dumps(dual_solution, indent=2), encoding="utf-8"
    )
    (output_dir / "phase1_dual_audit_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    write_csv(
        output_dir / "phase1_variable_catalog.csv",
        catalog_rows,
        [
            "variable_id",
            "variable_type",
            "demand_id",
            "path_id",
            "column_id",
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
        ],
    )
    write_csv(
        output_dir / "phase1_reduced_cost_audit.csv",
        audit_rows,
        [
            "variable_id",
            "variable_type",
            "demand_id",
            "primal_value",
            "lower_bound",
            "upper_bound",
            "objective_coefficient",
            "computed_reduced_cost_or_stationarity_residual",
            "solver_lower_marginal",
            "solver_upper_marginal",
            "kkt_status",
            "interpretation",
        ],
    )
    write_report(output_dir / "phase1_dual_validation_report.md", summary, catalog_rows, audit_rows)


def run_audit(
    config_path: str | Path = DEFAULT_CURRENT_POOL_CONFIG,
    output_dir: Path = OUTPUT_DIR,
    preflight_output_dir: Path | None = None,
) -> dict[str, Any]:
    config = load_config(config_path)
    data_dir = input_data_dir(config)
    baseline_columns_path = data_dir / "dynamic_columns.csv"
    baseline_hash_before = sha256_file(baseline_columns_path)

    preflight_dir = preflight_output_dir or PREFLIGHT_OUTPUT_DIR
    preflight_summary = run_preflight(config_path, preflight_dir)
    stability_blockers = preflight_stability_checks(preflight_summary, baseline_hash_before)

    arcs = read_csv(data_dir / "dynamic_arc.csv")
    demands = read_csv(data_dir / "dynamic_demand.csv")
    all_columns = read_csv(baseline_columns_path)
    candidates = read_csv(data_dir / "candidate_paths.csv")
    real_columns, selection_blockers = selected_candidate_columns(config, all_columns, candidates)
    model = build_phase1_model(arcs, demands, real_columns)
    solver_info, result = solve_model(model)

    safe_blockers = [*stability_blockers, *selection_blockers]
    if result is None or solver_info.get("solver_status") != "optimal":
        safe_blockers.append(f"dual audit RMP solve did not return optimal: {solver_info.get('solver_status')}")
        values = [0.0 for _ in model.variables]
        catalog_rows = build_variable_catalog(model, values)
        dual_solution = {
            "solver": "scipy.optimize.linprog / HiGHS",
            "dual_convention": "raw SciPy/HiGHS marginals",
            "solver_status": solver_info.get("solver_status"),
            "solver_message": solver_info.get("solver_message"),
            "objective_value_artificial_penalty_units": solver_info.get("objective_value"),
            "dual_fields_present": False,
            "dual_fields_finite": False,
            "safe_blocker": safe_blockers,
        }
        audit_rows: list[dict[str, Any]] = []
        validation_status = "SAFE_BLOCKED"
        convention = None
    else:
        dual_solution, raw_vectors = build_dual_solution(model, result, solver_info)
        values = raw_vectors["values"]
        catalog_rows = build_variable_catalog(model, values)
        if not dual_solution["dual_fields_present"] or not dual_solution["dual_fields_finite"]:
            safe_blockers.append("SciPy/HiGHS dual fields are missing or nonfinite")
            audit_rows = []
            validation_status = "SAFE_BLOCKED"
            convention = None
        else:
            trials = convention_trials(
                model,
                values,
                raw_vectors["eq_marginals"],
                raw_vectors["ub_marginals"],
                raw_vectors["lower_marginals"],
                raw_vectors["upper_marginals"],
            )
            selected = next((trial for trial in trials if trial["validation_passed"]), None)
            dual_solution["stationarity_convention_trials"] = [
                {key: value for key, value in trial.items() if key != "rows"}
                for trial in trials
            ]
            if selected is None:
                safe_blockers.append("No reduced-cost/stationarity convention validated on existing variables")
                audit_rows = trials[0]["rows"] if trials else []
                validation_status = "SAFE_BLOCKED"
                convention = None
            else:
                audit_rows = selected["rows"]
                validation_status = "PASS"
                convention = selected["convention_name"]
                dual_solution["validated_stationarity_convention"] = selected

    baseline_hash_after = sha256_file(baseline_columns_path)
    if baseline_hash_after != baseline_hash_before:
        safe_blockers.append("baseline dynamic_columns.csv hash changed during dual audit")

    artificial_catalog_rows = [row for row in catalog_rows if row["variable_type"] == "artificial_demand"]
    artificial_has_arc = any(row["has_dynamic_arc_incidence"] == "true" for row in artificial_catalog_rows)
    phase2_blocked = preflight_summary.get("phase2_transition_allowed") is False
    pricing_safe_next = validation_status == "PASS" and not safe_blockers
    summary = {
        "dual_audit_status": "PASS" if pricing_safe_next else "SAFE_BLOCKED",
        "preflight_stability_status": "PASS" if not stability_blockers else "SAFE_BLOCKED",
        "dual_extraction_status": "PASS"
        if dual_solution.get("dual_fields_present") and dual_solution.get("dual_fields_finite")
        else "SAFE_BLOCKED",
        "reduced_cost_convention_validation_status": validation_status,
        "validated_stationarity_convention": convention,
        "safe_blockers": safe_blockers,
        "solver_status": solver_info.get("solver_status"),
        "objective_value_artificial_penalty_units": solver_info.get("objective_value"),
        "preflight_total_artificial_flow": preflight_summary.get("total_artificial_flow"),
        "preflight_artificial_flow_by_demand": preflight_summary.get("artificial_flow_by_demand"),
        "preflight_capacity_violation_count": preflight_summary.get("capacity_violation_count"),
        "baseline_dynamic_columns_path": str(baseline_columns_path.relative_to(ROOT_DIR)).replace("\\", "/"),
        "baseline_dynamic_columns_hash_before": baseline_hash_before,
        "baseline_dynamic_columns_hash_after": baseline_hash_after,
        "baseline_dynamic_columns_mutated": baseline_hash_before != baseline_hash_after,
        "phase2_transition_allowed": preflight_summary.get("phase2_transition_allowed"),
        "phase2_transition_executed": False,
        "artificial_variables_have_dynamic_arc_incidence": artificial_has_arc,
        "variable_count": len(catalog_rows),
        "real_variable_count": len([row for row in catalog_rows if row["variable_type"] == "real_column"]),
        "artificial_variable_count": len(artificial_catalog_rows),
        "candidate_generation_run": False,
        "phase1_pricing_run": False,
        "generated_real_columns_added": False,
        "add_resolve_run": False,
        "controlled_loop_run": False,
        "full_assignment_run": False,
        "full_cg_run": False,
        "phase1_pricing_candidate_diagnostics_safe_next": pricing_safe_next,
        "scope": DUAL_SCOPE_BOUNDARY,
    }
    write_outputs(output_dir, dual_solution, catalog_rows, audit_rows, summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase-I artificial RMP dual/schema audit.")
    parser.add_argument("--config", default=DEFAULT_CURRENT_POOL_CONFIG)
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--preflight-output-dir", default=None)
    parser.add_argument("--benchmark-id", default="second_controlled_benchmark_link55")
    parser.add_argument("--no-mutate-accepted-outputs", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.benchmark_id != "second_controlled_benchmark_link55":
        print(f"Unsupported benchmark id: {args.benchmark_id}")
        return 1
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = ROOT_DIR / output_dir
    preflight_output_dir = Path(args.preflight_output_dir) if args.preflight_output_dir else None
    if preflight_output_dir is not None and not preflight_output_dir.is_absolute():
        preflight_output_dir = ROOT_DIR / preflight_output_dir
    if args.no_mutate_accepted_outputs:
        if output_dir.resolve() == OUTPUT_DIR.resolve():
            print("Refusing to write to accepted default dual-audit folder with --no-mutate-accepted-outputs.")
            return 1
        if preflight_output_dir is None or preflight_output_dir.resolve() == PREFLIGHT_OUTPUT_DIR.resolve():
            print("Refusing to write to accepted default Phase-I preflight folder with --no-mutate-accepted-outputs.")
            return 1
    summary = run_audit(args.config, output_dir, preflight_output_dir=preflight_output_dir)
    print(f"Phase-I dual audit status: {summary['dual_audit_status']}")
    print(f"Dual extraction status: {summary['dual_extraction_status']}")
    print(f"Stationarity validation status: {summary['reduced_cost_convention_validation_status']}")
    print(f"Validated convention: {summary['validated_stationarity_convention']}")
    print(f"Preflight total artificial flow: {summary['preflight_total_artificial_flow']}")
    print(f"Phase-II transition allowed: {summary['phase2_transition_allowed']}")
    print(f"Pricing candidate diagnostics safe next: {summary['phase1_pricing_candidate_diagnostics_safe_next']}")
    print(f"Report: {output_dir / 'phase1_dual_validation_report.md'}")
    return 0 if summary["dual_audit_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
