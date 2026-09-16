"""Phase-II RMP initialization diagnostic.

This diagnostic uses the output-only ten-column Phase-II initial pool prepared
by a Phase-I closure/handoff precheck. It solves one real-only,
cost-minimizing restricted master problem and exports primal feasibility,
capacity usage, objective, and raw SciPy/HiGHS dual availability.

It does not run Phase-II pricing, generate columns, add columns, run
add-resolve, run a loop, run full assignment, run full CG, or claim general
convergence or exact arc-LP flow-pattern reproduction.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

from phase1_artificial_dual_audit import vector_from_result_field
from phase1_artificial_rmp_preflight import sha256_file, status_from_linprog
from phase1_closure_phase2_handoff_precheck import read_json, write_json
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


OUTPUT_DIR = ROOT_DIR / "outputs" / "phase2_rmp_initialization_diagnostic"
DEFAULT_OUTPUT_DIR = OUTPUT_DIR
HANDOFF_DIR = ROOT_DIR / "outputs" / "phase1_closure_phase2_handoff_precheck"
ARC_LP_REFERENCE = ROOT_DIR / "outputs" / "second_controlled_benchmark_link55_arc_lp" / "arc_lp_summary.json"
SEED_POOL_RMP_REFERENCE = (
    ROOT_DIR / "outputs" / "second_controlled_benchmark_link55_seed_pool_repair" / "seed_pool_rmp_summary.json"
)
SEED_POOL_COMPARISON = (
    ROOT_DIR
    / "outputs"
    / "second_controlled_benchmark_link55_seed_pool_repair"
    / "seed_pool_rmp_vs_arc_lp_summary.json"
)
CURRENT_POOL_REFERENCE = (
    ROOT_DIR / "outputs" / "second_controlled_benchmark_link55_current_pool_rmp" / "rmp_summary.json"
)
ALLOW_VARIABLE_INITIAL_POOL_COLUMN_COUNT = False
REQUIRED_INPUTS = [
    HANDOFF_DIR / "phase2_initial_column_pool.csv",
    HANDOFF_DIR / "phase2_initial_pool_manifest.json",
    HANDOFF_DIR / "phase1_real_only_feasibility_summary.json",
    HANDOFF_DIR / "phase2_handoff_hash_audit.json",
]
SCOPE_BOUNDARY = (
    "This is a Phase-II RMP initialization diagnostic only. It solves the "
    "real-only restricted master once using the output-only ten-column Phase-II "
    "initial pool from a Phase-I handoff. It does not run Phase-II "
    "pricing, generate new columns, add columns, run add-resolve, run a loop, "
    "run full assignment, run full CG, or claim general convergence, "
    "production-scale solving, GTFS, railway, branch-and-price, reinforcement "
    "learning, or exact arc-LP flow-pattern reproduction."
)


def resolve_artifact_path(value: Any) -> Path | None:
    if not value:
        return None
    path = Path(str(value))
    if path.is_absolute():
        return path
    return ROOT_DIR / path


def refresh_required_inputs() -> None:
    global REQUIRED_INPUTS
    REQUIRED_INPUTS = [
        HANDOFF_DIR / "phase2_initial_column_pool.csv",
        HANDOFF_DIR / "phase2_initial_pool_manifest.json",
        HANDOFF_DIR / "phase1_real_only_feasibility_summary.json",
        HANDOFF_DIR / "phase2_handoff_hash_audit.json",
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
    global HANDOFF_DIR, ALLOW_VARIABLE_INITIAL_POOL_COLUMN_COUNT
    HANDOFF_DIR = resolve_artifact_path(artifacts.get("handoff_dir")) or HANDOFF_DIR
    allow_variable_count = artifacts.get("allow_variable_initial_pool_column_count")
    if allow_variable_count is not None:
        ALLOW_VARIABLE_INITIAL_POOL_COLUMN_COUNT = bool(allow_variable_count)
    refresh_required_inputs()
    return artifacts


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT_DIR)).replace("\\", "/")


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def finite_or_none(value: Any) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if math.isfinite(numeric) else None


def all_finite(values: list[Any] | None, expected_count: int) -> bool:
    return (
        values is not None
        and len(values) == expected_count
        and all(finite_or_none(value) is not None for value in values)
    )


def required_input_blockers() -> list[str]:
    blockers: list[str] = []
    for path in REQUIRED_INPUTS:
        if not path.exists() or path.stat().st_size == 0:
            blockers.append(f"missing or empty required handoff input: {rel(path)}")
    return blockers


def choose_cost_field(pool_rows: list[dict[str, str]]) -> tuple[str, list[float], list[str]]:
    candidate_fields = ["generalized_cost", "true_generalized_cost", "cost"]
    blockers: list[str] = []
    for field in candidate_fields:
        if not all(field in row for row in pool_rows):
            continue
        costs = [finite_or_none(row.get(field)) for row in pool_rows]
        if all(cost is not None for cost in costs):
            return field, [float(cost) for cost in costs if cost is not None], []
        blockers.append(f"cost field {field} exists but contains non-finite values")
    blockers.append("no valid numeric generalized/true cost field found in Phase-II initial pool")
    return "", [], blockers


def validate_handoff_inputs(
    pool_rows: list[dict[str, str]],
    manifest: dict[str, Any],
    real_only: dict[str, Any],
    handoff_hash: dict[str, Any],
    baseline_hash_before: str,
    allow_variable_initial_pool_column_count: bool = False,
) -> list[str]:
    blockers: list[str] = []
    artificial_rows = [
        row
        for row in pool_rows
        if row.get("column_id", "").startswith("ARTIFICIAL_DEMAND_")
        or row.get("phase2_pool_column_type", "").lower().startswith("artificial")
        or row.get("is_artificial", "").lower() == "true"
    ]
    if manifest.get("safe_for_phase2_rmp_initialization") is not True:
        blockers.append("handoff manifest is not marked safe_for_phase2_rmp_initialization")
    if manifest.get("phase2_execution_performed") is not False:
        blockers.append("handoff manifest unexpectedly reports prior Phase-II execution")
    if manifest.get("phase2_pricing_performed") is not False:
        blockers.append("handoff manifest unexpectedly reports Phase-II pricing")
    if real_only.get("real_only_feasibility_status") != "PASS":
        blockers.append("handoff real-only feasibility summary is not PASS")
    if not allow_variable_initial_pool_column_count and len(pool_rows) != 10:
        blockers.append(f"Phase-II initial pool has {len(pool_rows)} columns, expected 10")
    if artificial_rows:
        blockers.append("Phase-II initial pool contains artificial variables")
    if not all(row.get("output_only_phase2_initial_pool") == "true" for row in pool_rows):
        blockers.append("one or more Phase-II initial pool rows are not marked output-only")
    if not all(row.get("written_to_baseline_dynamic_columns") == "false" for row in pool_rows):
        blockers.append("one or more Phase-II initial pool rows are marked as written to baseline")
    if handoff_hash.get("baseline_dynamic_columns_hash_before") != handoff_hash.get(
        "baseline_dynamic_columns_hash_after"
    ):
        blockers.append("handoff hash audit reports baseline mutation")
    if baseline_hash_before != ACCEPTED_BASELINE_HASH:
        blockers.append(f"baseline dynamic_columns.csv hash differs from accepted hash: {baseline_hash_before}")
    if handoff_hash.get("baseline_dynamic_columns_hash_after") != baseline_hash_before:
        blockers.append("current baseline hash differs from handoff hash audit")
    return blockers


def solve_phase2_rmp(
    arcs: list[dict[str, str]],
    demands: list[dict[str, str]],
    pool_rows: list[dict[str, str]],
    costs: list[float],
) -> tuple[dict[str, Any], Any | None, list[str]]:
    try:
        from scipy.optimize import linprog
        from scipy.sparse import coo_matrix
    except ImportError as exc:
        return {
            "solver_status": "solver_unavailable",
            "solver_message": f"scipy.optimize.linprog is unavailable: {exc}",
            "linprog_status_code": None,
            "objective_value": None,
        }, None, [f"scipy.optimize.linprog unavailable: {exc}"]

    demand_ids = [row["demand_id"] for row in demands]
    demand_index = {demand_id: idx for idx, demand_id in enumerate(demand_ids)}
    demand_volume = {row["demand_id"]: parse_float(row["volume"], 0.0) for row in demands}
    arc_ids = [row["arc_id"] for row in arcs]
    arc_index = {arc_id: idx for idx, arc_id in enumerate(arc_ids)}

    blockers: list[str] = []
    eq_rows: list[int] = []
    eq_cols: list[int] = []
    eq_data: list[float] = []
    ub_rows: list[int] = []
    ub_cols: list[int] = []
    ub_data: list[float] = []
    bounds: list[tuple[float, float]] = []

    for col_pos, column in enumerate(pool_rows):
        demand_id = column.get("demand_id", "")
        if demand_id not in demand_index:
            blockers.append(f"column {column.get('column_id')} references unknown demand {demand_id}")
            continue
        eq_rows.append(demand_index[demand_id])
        eq_cols.append(col_pos)
        eq_data.append(1.0)
        bounds.append((0.0, demand_volume[demand_id]))
        for arc_id in split_sequence(column.get("arc_sequence")):
            if arc_id not in arc_index:
                blockers.append(f"column {column.get('column_id')} references missing arc {arc_id}")
                continue
            ub_rows.append(arc_index[arc_id])
            ub_cols.append(col_pos)
            ub_data.append(1.0)

    if blockers:
        return {
            "solver_status": "precheck_blocked",
            "solver_message": "; ".join(blockers),
            "linprog_status_code": None,
            "objective_value": None,
        }, None, blockers

    a_eq = coo_matrix(
        (eq_data, (eq_rows, eq_cols)), shape=(len(demands), len(pool_rows))
    ).tocsr()
    a_ub = coo_matrix(
        (ub_data, (ub_rows, ub_cols)), shape=(len(arcs), len(pool_rows))
    ).tocsr()
    result = linprog(
        c=costs,
        A_ub=a_ub,
        b_ub=[max(0.0, parse_float(row.get("capacity"), 0.0)) for row in arcs],
        A_eq=a_eq,
        b_eq=[demand_volume[demand_id] for demand_id in demand_ids],
        bounds=bounds,
        method="highs",
    )
    return {
        "solver_status": status_from_linprog(result),
        "solver_message": result.message,
        "linprog_status_code": int(result.status),
        "objective_value": float(result.fun) if result.success else None,
    }, result, []


def build_solution_outputs(
    arcs: list[dict[str, str]],
    demands: list[dict[str, str]],
    pool_rows: list[dict[str, str]],
    costs: list[float],
    values: list[float],
    cost_field: str,
) -> dict[str, Any]:
    demand_volume = {row["demand_id"]: parse_float(row.get("volume"), 0.0) for row in demands}
    flow_by_demand = {demand_id: 0.0 for demand_id in demand_volume}
    cost_by_demand = {demand_id: 0.0 for demand_id in demand_volume}
    arc_flow = {row["arc_id"]: 0.0 for row in arcs}
    columns_by_arc: dict[str, list[str]] = defaultdict(list)
    demands_by_arc: dict[str, set[str]] = defaultdict(set)

    column_rows: list[dict[str, Any]] = []
    for column, cost, flow in zip(pool_rows, costs, values):
        demand_id = column.get("demand_id", "")
        flow_by_demand[demand_id] = flow_by_demand.get(demand_id, 0.0) + flow
        cost_by_demand[demand_id] = cost_by_demand.get(demand_id, 0.0) + cost * flow
        for arc_id in split_sequence(column.get("arc_sequence")):
            arc_flow[arc_id] += flow
            if flow > TOL:
                columns_by_arc[arc_id].append(column.get("column_id", ""))
                demands_by_arc[arc_id].add(demand_id)
        column_rows.append(
            {
                "column_id": column.get("column_id", ""),
                "path_id": column.get("path_id", ""),
                "demand_id": demand_id,
                "phase2_pool_column_type": column.get("phase2_pool_column_type", ""),
                "source_metadata": column.get("source_metadata", ""),
                "added_in_phase1_round": column.get("added_in_phase1_round", ""),
                "lower_bound": 0.0,
                "upper_bound": demand_volume[demand_id],
                "flow": flow,
                "positive_flow": bool_text(flow > TOL),
                "cost_field_used": cost_field,
                "objective_coefficient": cost,
                "objective_contribution": cost * flow,
                "arc_sequence": column.get("arc_sequence", ""),
            }
        )

    demand_rows: list[dict[str, Any]] = []
    demand_residual_max = 0.0
    for demand_id, volume in demand_volume.items():
        real_flow = flow_by_demand.get(demand_id, 0.0)
        residual = real_flow - volume
        demand_residual_max = max(demand_residual_max, abs(residual))
        demand_rows.append(
            {
                "demand_id": demand_id,
                "demand_volume": volume,
                "real_column_flow": real_flow,
                "demand_residual": residual,
                "status": "PASS" if abs(residual) <= TOL else "FAIL",
            }
        )

    capacity_rows: list[dict[str, Any]] = []
    violation_count = 0
    max_violation = 0.0
    for arc in arcs:
        arc_id = arc["arc_id"]
        flow = arc_flow[arc_id]
        capacity = max(0.0, parse_float(arc.get("capacity"), 0.0))
        slack = capacity - flow
        violation = max(0.0, flow - capacity)
        if violation > TOL:
            violation_count += 1
            max_violation = max(max_violation, violation)
        capacity_rows.append(
            {
                "arc_id": arc_id,
                "arc_type": arc.get("arc_type", ""),
                "physical_link_id": arc.get("physical_link_id", ""),
                "from_time": arc.get("from_time", ""),
                "to_time": arc.get("to_time", ""),
                "flow": flow,
                "capacity": capacity,
                "slack": slack,
                "capacity_violation": violation,
                "is_binding": bool_text(abs(slack) <= TOL),
                "columns_using_arc": "|".join(columns_by_arc[arc_id]),
                "demand_ids_using_arc": "|".join(sorted(demands_by_arc[arc_id])),
                "status": "PASS" if violation <= TOL else "FAIL",
            }
        )

    cost_rows = [
        {
            "breakdown_id": f"demand_{demand_id}",
            "demand_id": demand_id,
            "cost_field_used": cost_field,
            "flow": flow_by_demand.get(demand_id, 0.0),
            "objective_contribution": cost_by_demand.get(demand_id, 0.0),
            "scope": "real-only Phase-II initial RMP",
        }
        for demand_id in demand_volume
    ]
    cost_rows.append(
        {
            "breakdown_id": "total",
            "demand_id": "",
            "cost_field_used": cost_field,
            "flow": sum(flow_by_demand.values()),
            "objective_contribution": sum(cost_by_demand.values()),
            "scope": "real-only Phase-II initial RMP",
        }
    )
    return {
        "solution_by_column": column_rows,
        "demand_balance": demand_rows,
        "capacity_usage": capacity_rows,
        "cost_breakdown": cost_rows,
        "positive_flow_by_demand": flow_by_demand,
        "positive_flow_column_count": sum(1 for value in values if value > TOL),
        "demand_residual_max": demand_residual_max,
        "capacity_violation_count": violation_count,
        "max_capacity_violation": max_violation,
    }


def build_dual_solution(
    result: Any,
    arcs: list[dict[str, str]],
    demands: list[dict[str, str]],
    pool_rows: list[dict[str, str]],
) -> dict[str, Any]:
    eq_marginals = vector_from_result_field(result, "eqlin", "marginals")
    eq_residuals = vector_from_result_field(result, "eqlin", "residual")
    cap_marginals = vector_from_result_field(result, "ineqlin", "marginals")
    cap_residuals = vector_from_result_field(result, "ineqlin", "residual")
    lower_marginals = vector_from_result_field(result, "lower", "marginals")
    upper_marginals = vector_from_result_field(result, "upper", "marginals")

    demand_ids = [row["demand_id"] for row in demands]
    arc_ids = [row["arc_id"] for row in arcs]
    variable_ids = [row.get("column_id", "") for row in pool_rows]
    fields_present = all(
        field is not None
        for field in [eq_marginals, eq_residuals, cap_marginals, cap_residuals, lower_marginals, upper_marginals]
    )
    fields_finite = (
        all_finite(eq_marginals, len(demand_ids))
        and all_finite(eq_residuals, len(demand_ids))
        and all_finite(cap_marginals, len(arc_ids))
        and all_finite(cap_residuals, len(arc_ids))
        and all_finite(lower_marginals, len(variable_ids))
        and all_finite(upper_marginals, len(variable_ids))
    )
    return {
        "solver": "scipy.optimize.linprog / HiGHS",
        "dual_convention": "raw SciPy/HiGHS marginals; Phase-II pricing sign convention is not validated by this task",
        "dual_fields_present": fields_present,
        "dual_fields_finite": fields_finite,
        "demand_equality_duals": {
            demand_id: {
                "marginal": (eq_marginals or [None] * len(demand_ids))[idx],
                "residual": (eq_residuals or [None] * len(demand_ids))[idx],
            }
            for idx, demand_id in enumerate(demand_ids)
        },
        "capacity_inequality_duals": {
            arc_id: {
                "marginal": (cap_marginals or [None] * len(arc_ids))[idx],
                "slack": (cap_residuals or [None] * len(arc_ids))[idx],
            }
            for idx, arc_id in enumerate(arc_ids)
        },
        "lower_bound_marginals": {
            variable_id: (lower_marginals or [None] * len(variable_ids))[idx]
            for idx, variable_id in enumerate(variable_ids)
        },
        "upper_bound_marginals": {
            variable_id: (upper_marginals or [None] * len(variable_ids))[idx]
            for idx, variable_id in enumerate(variable_ids)
        },
    }


def build_reference_comparison(phase2_objective: float | None) -> dict[str, Any]:
    arc_lp = read_json(ARC_LP_REFERENCE) if ARC_LP_REFERENCE.exists() else {}
    seed_rmp = read_json(SEED_POOL_RMP_REFERENCE) if SEED_POOL_RMP_REFERENCE.exists() else {}
    seed_comparison = read_json(SEED_POOL_COMPARISON) if SEED_POOL_COMPARISON.exists() else {}
    current_pool = read_json(CURRENT_POOL_REFERENCE) if CURRENT_POOL_REFERENCE.exists() else {}

    arc_lp_objective = finite_or_none(arc_lp.get("objective_value"))
    seed_objective = finite_or_none(seed_rmp.get("rmp_objective"))
    comparison = {
        "comparison_scope": "diagnostic comparison only; this is a restricted master over 10 real columns",
        "phase2_initial_rmp_objective": phase2_objective,
        "phase2_initial_rmp_objective_comparable_to_column_rmp_costs": phase2_objective is not None,
        "arc_lp_reference_source": rel(ARC_LP_REFERENCE),
        "arc_lp_reference_status": arc_lp.get("solver_status"),
        "arc_lp_reference_objective": arc_lp_objective,
        "phase2_gap_vs_arc_lp_reference": phase2_objective - arc_lp_objective
        if phase2_objective is not None and arc_lp_objective is not None
        else None,
        "repaired_seed_pool_rmp_source": rel(SEED_POOL_RMP_REFERENCE),
        "repaired_seed_pool_rmp_status": seed_rmp.get("rmp_solver_status"),
        "repaired_seed_pool_rmp_objective": seed_objective,
        "phase2_gap_vs_repaired_seed_pool_rmp": phase2_objective - seed_objective
        if phase2_objective is not None and seed_objective is not None
        else None,
        "accepted_seed_pool_gap_vs_arc_lp": seed_comparison.get("objective_gap_vs_arc_lp"),
        "current_pool_rmp_source": rel(CURRENT_POOL_REFERENCE),
        "current_pool_rmp_status": current_pool.get("rmp_solver_status"),
        "current_pool_rmp_objective": current_pool.get("rmp_objective"),
        "objective_optimality_claim_vs_arc_lp": False,
        "exact_arc_lp_flow_pattern_reproduction_claimed": False,
    }
    return comparison


def build_reports(output_dir: Path, summary: dict[str, Any], reference: dict[str, Any]) -> None:
    lines = [
        "# Phase-II RMP Initialization Diagnostic",
        "",
        SCOPE_BOUNDARY,
        "",
        "## Status",
        "",
        f"- Diagnostic status: {summary['diagnostic_status']}",
        f"- Solver status: {summary.get('solver_status')}",
        f"- Objective value: {summary.get('objective_value')}",
        f"- Cost field used: {summary.get('objective_units_or_cost_field_used')}",
        f"- Demand residual max: {summary.get('demand_residual_max')}",
        f"- Capacity violation count: {summary.get('capacity_violation_count')}",
        f"- Positive-flow column count: {summary.get('positive_flow_column_count')}",
        f"- Artificial variables present: {summary.get('artificial_variables_present')}",
        f"- Baseline dynamic_columns.csv mutated: {summary.get('baseline_dynamic_columns_mutated')}",
        "",
        "## Scope Guardrails",
        "",
        f"- Phase-II pricing performed: {summary.get('phase2_pricing_performed')}",
        f"- New columns generated: {summary.get('new_columns_generated')}",
        f"- Columns added: {summary.get('columns_added')}",
        f"- Add-resolve run: {summary.get('add_resolve_run')}",
        f"- CG loop run: {summary.get('cg_loop_run')}",
        f"- Full assignment run: {summary.get('full_assignment_run')}",
        f"- Full CG run: {summary.get('full_cg_run')}",
        "",
        "## Reference Comparison",
        "",
        "Diagnostic comparison only; this is a restricted master over 10 real columns.",
        f"- Arc-LP reference objective: {reference.get('arc_lp_reference_objective')}",
        f"- Repaired seed-pool RMP objective: {reference.get('repaired_seed_pool_rmp_objective')}",
        f"- Gap vs arc-LP reference: {reference.get('phase2_gap_vs_arc_lp_reference')}",
        f"- Gap vs repaired seed-pool RMP: {reference.get('phase2_gap_vs_repaired_seed_pool_rmp')}",
        "",
        "## Next Safe Step",
        "",
        summary.get("next_safe_step", ""),
    ]
    (output_dir / "phase2_rmp_initialization_report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def write_safe_blocker_outputs(output_dir: Path, blockers: list[str], baseline_hash_before: str | None) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "diagnostic_status": "SAFE_BLOCKED",
        "solver_status": "not_run",
        "phase2_initial_pool_column_count": None,
        "artificial_variables_present": None,
        "objective_value": None,
        "objective_units_or_cost_field_used": None,
        "demand_residual_max": None,
        "capacity_violation_count": None,
        "max_capacity_violation": None,
        "positive_flow_column_count": None,
        "positive_flow_by_demand": {},
        "baseline_dynamic_columns_hash_before": baseline_hash_before,
        "baseline_dynamic_columns_hash_after": baseline_hash_before,
        "baseline_dynamic_columns_mutated": False,
        "phase2_pricing_performed": False,
        "new_columns_generated": False,
        "columns_added": False,
        "add_resolve_run": False,
        "cg_loop_run": False,
        "full_assignment_run": False,
        "full_cg_run": False,
        "safe_for_phase2_pricing_diagnostic_next": False,
        "safe_blockers": blockers,
        "scope": SCOPE_BOUNDARY,
        "next_safe_step": "resolve Phase-II RMP initialization blockers before pricing diagnostics",
    }
    write_json(output_dir / "phase2_rmp_initialization_summary.json", summary)
    write_json(output_dir / "phase2_rmp_dual_solution.json", {"dual_fields_present": False, "safe_blockers": blockers})
    write_json(output_dir / "phase2_rmp_reference_comparison.json", build_reference_comparison(None))
    write_json(
        output_dir / "phase2_rmp_hash_audit.json",
        {
            "baseline_dynamic_columns_hash_before": baseline_hash_before,
            "baseline_dynamic_columns_hash_after": baseline_hash_before,
            "baseline_dynamic_columns_mutated": False,
            "safe_blockers": blockers,
        },
    )
    write_json(output_dir / "phase2_rmp_input_manifest.json", {"safe_blockers": blockers})
    write_csv(output_dir / "phase2_rmp_solution_by_column.csv", [], ["column_id"])
    write_csv(output_dir / "phase2_rmp_demand_balance.csv", [], ["demand_id"])
    write_csv(output_dir / "phase2_rmp_capacity_usage.csv", [], ["arc_id"])
    write_csv(output_dir / "phase2_rmp_cost_breakdown.csv", [], ["breakdown_id"])
    build_reports(output_dir, summary, build_reference_comparison(None))
    return summary


def run_diagnostic(config_path: str | Path = DEFAULT_CURRENT_POOL_CONFIG, output_dir: Path = OUTPUT_DIR) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    config = load_config(config_path)
    data_dir = input_data_dir(config)
    baseline_path = data_dir / "dynamic_columns.csv"
    baseline_hash_before = sha256_file(baseline_path)

    input_blockers = required_input_blockers()
    if input_blockers:
        return write_safe_blocker_outputs(output_dir, input_blockers, baseline_hash_before)

    pool_rows = read_csv(HANDOFF_DIR / "phase2_initial_column_pool.csv")
    manifest = read_json(HANDOFF_DIR / "phase2_initial_pool_manifest.json")
    real_only = read_json(HANDOFF_DIR / "phase1_real_only_feasibility_summary.json")
    handoff_hash = read_json(HANDOFF_DIR / "phase2_handoff_hash_audit.json")
    arcs = read_csv(data_dir / "dynamic_arc.csv")
    demands = read_csv(data_dir / "dynamic_demand.csv")
    handoff_blockers = validate_handoff_inputs(
        pool_rows,
        manifest,
        real_only,
        handoff_hash,
        baseline_hash_before,
        ALLOW_VARIABLE_INITIAL_POOL_COLUMN_COUNT,
    )
    cost_field, costs, cost_blockers = choose_cost_field(pool_rows)
    blockers = handoff_blockers + cost_blockers
    if blockers:
        return write_safe_blocker_outputs(output_dir, blockers, baseline_hash_before)

    solver_info, result, solve_blockers = solve_phase2_rmp(arcs, demands, pool_rows, costs)
    if solve_blockers or result is None or not getattr(result, "success", False):
        blockers = solve_blockers or [f"Phase-II initial RMP solve failed: {solver_info.get('solver_status')}"]
        return write_safe_blocker_outputs(output_dir, blockers, baseline_hash_before)

    values = [float(value) for value in result.x]
    solution_outputs = build_solution_outputs(arcs, demands, pool_rows, costs, values, cost_field)
    dual_solution = build_dual_solution(result, arcs, demands, pool_rows)
    baseline_hash_after = sha256_file(baseline_path)
    reference = build_reference_comparison(solver_info.get("objective_value"))

    safe_for_pricing_next = (
        solver_info["solver_status"] == "optimal"
        and solution_outputs["demand_residual_max"] <= TOL
        and solution_outputs["max_capacity_violation"] <= TOL
        and solution_outputs["capacity_violation_count"] == 0
        and dual_solution["dual_fields_present"]
        and dual_solution["dual_fields_finite"]
        and baseline_hash_before == baseline_hash_after
    )
    summary = {
        "diagnostic_status": "PASS" if safe_for_pricing_next else "SAFE_BLOCKED",
        "solver_status": solver_info["solver_status"],
        "solver_message": solver_info["solver_message"],
        "linprog_status_code": solver_info["linprog_status_code"],
        "phase2_initial_pool_column_count": len(pool_rows),
        "allow_variable_initial_pool_column_count": ALLOW_VARIABLE_INITIAL_POOL_COLUMN_COUNT,
        "artificial_variables_present": False,
        "objective_value": solver_info["objective_value"],
        "objective_units_or_cost_field_used": cost_field,
        "demand_residual_max": solution_outputs["demand_residual_max"],
        "capacity_violation_count": solution_outputs["capacity_violation_count"],
        "max_capacity_violation": solution_outputs["max_capacity_violation"],
        "positive_flow_column_count": solution_outputs["positive_flow_column_count"],
        "positive_flow_by_demand": solution_outputs["positive_flow_by_demand"],
        "baseline_dynamic_columns_hash_before": baseline_hash_before,
        "baseline_dynamic_columns_hash_after": baseline_hash_after,
        "baseline_dynamic_columns_mutated": baseline_hash_before != baseline_hash_after,
        "phase2_pricing_performed": False,
        "new_columns_generated": False,
        "columns_added": False,
        "add_resolve_run": False,
        "cg_loop_run": False,
        "full_assignment_run": False,
        "full_cg_run": False,
        "general_convergence_claimed": False,
        "exact_arc_lp_flow_pattern_reproduction_claimed": False,
        "dual_fields_present": dual_solution["dual_fields_present"],
        "dual_fields_finite": dual_solution["dual_fields_finite"],
        "safe_for_phase2_pricing_diagnostic_next": safe_for_pricing_next,
        "safe_blockers": [] if safe_for_pricing_next else ["dual/feasibility/hash gate failed"],
        "scope": SCOPE_BOUNDARY,
        "next_safe_step": "separately scoped Phase-II pricing candidate diagnostic"
        if safe_for_pricing_next
        else "review Phase-II initial RMP blockers before pricing diagnostics",
    }
    input_manifest = {
        "config_path": rel(Path(config_path) if Path(config_path).is_absolute() else ROOT_DIR / config_path),
        "data_dir": rel(data_dir),
        "phase2_initial_column_pool": rel(HANDOFF_DIR / "phase2_initial_column_pool.csv"),
        "phase2_initial_pool_manifest": rel(HANDOFF_DIR / "phase2_initial_pool_manifest.json"),
        "phase1_real_only_feasibility_summary": rel(
            HANDOFF_DIR / "phase1_real_only_feasibility_summary.json"
        ),
        "phase2_handoff_hash_audit": rel(HANDOFF_DIR / "phase2_handoff_hash_audit.json"),
        "baseline_dynamic_columns": rel(baseline_path),
        "phase2_initial_pool_column_count": len(pool_rows),
        "cost_field_used": cost_field,
        "artificial_variables_present": False,
        "phase2_pricing_performed": False,
        "new_columns_generated": False,
        "columns_added": False,
    }
    hash_audit = {
        "baseline_dynamic_columns_path": rel(baseline_path),
        "baseline_dynamic_columns_hash_before": baseline_hash_before,
        "baseline_dynamic_columns_hash_after": baseline_hash_after,
        "accepted_baseline_dynamic_columns_hash": ACCEPTED_BASELINE_HASH,
        "baseline_dynamic_columns_mutated": baseline_hash_before != baseline_hash_after,
        "phase2_initial_column_pool_path": rel(HANDOFF_DIR / "phase2_initial_column_pool.csv"),
        "phase2_initial_column_pool_sha256": sha256_file(HANDOFF_DIR / "phase2_initial_column_pool.csv"),
        "phase2_handoff_manifest_sha256": sha256_file(HANDOFF_DIR / "phase2_initial_pool_manifest.json"),
        "phase2_pricing_performed": False,
        "new_columns_generated": False,
        "columns_added": False,
    }

    write_json(output_dir / "phase2_rmp_initialization_summary.json", summary)
    write_json(output_dir / "phase2_rmp_dual_solution.json", dual_solution)
    write_json(output_dir / "phase2_rmp_input_manifest.json", input_manifest)
    write_json(output_dir / "phase2_rmp_hash_audit.json", hash_audit)
    write_json(output_dir / "phase2_rmp_reference_comparison.json", reference)
    write_csv(
        output_dir / "phase2_rmp_solution_by_column.csv",
        solution_outputs["solution_by_column"],
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
        output_dir / "phase2_rmp_demand_balance.csv",
        solution_outputs["demand_balance"],
        ["demand_id", "demand_volume", "real_column_flow", "demand_residual", "status"],
    )
    write_csv(
        output_dir / "phase2_rmp_capacity_usage.csv",
        solution_outputs["capacity_usage"],
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
        output_dir / "phase2_rmp_cost_breakdown.csv",
        solution_outputs["cost_breakdown"],
        ["breakdown_id", "demand_id", "cost_field_used", "flow", "objective_contribution", "scope"],
    )
    build_reports(output_dir, summary, reference)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase-II RMP initialization diagnostic.")
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
    summary = run_diagnostic(config_path, output_dir)
    print(f"Phase-II RMP initialization diagnostic status: {summary['diagnostic_status']}")
    print(f"Solver status: {summary.get('solver_status')}")
    print(f"Objective value: {summary.get('objective_value')}")
    print(f"Cost field used: {summary.get('objective_units_or_cost_field_used')}")
    print(f"Demand residual max: {summary.get('demand_residual_max')}")
    print(f"Capacity violation count: {summary.get('capacity_violation_count')}")
    print(f"Positive-flow column count: {summary.get('positive_flow_column_count')}")
    print(f"Baseline dynamic_columns.csv mutated: {summary.get('baseline_dynamic_columns_mutated')}")
    print(f"Phase-II pricing performed: {summary.get('phase2_pricing_performed')}")
    print(f"New columns generated: {summary.get('new_columns_generated')}")
    print(f"CG loop run: {summary.get('cg_loop_run')}")
    print(f"Report: {output_dir / 'phase2_rmp_initialization_report.md'}")
    return 0 if summary["diagnostic_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
