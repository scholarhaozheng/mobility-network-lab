"""Phase-I artificial-demand-variable RMP preflight.

This script builds and solves only a minimal Phase-I RMP for the accepted
second controlled benchmark current-pool case. It adds one artificial demand
variable per demand so the RMP can be represented as feasible even when the
real-only current pool is infeasible.

It does not implement pricing, add generated real columns, run add-resolve,
run a controlled loop, transition to Phase II, run full assignment, or run
full CG.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

from precheck_second_controlled_benchmark_current_pool_rmp import (
    DEFAULT_CONFIG as DEFAULT_CURRENT_POOL_CONFIG,
    SCOPE_BOUNDARY as CURRENT_POOL_SCOPE_BOUNDARY,
    TOL,
    input_data_dir,
    load_config,
    parse_float,
    read_csv,
    run_precheck,
    selected_candidate_columns,
    split_sequence,
)


ROOT_DIR = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT_DIR / "outputs" / "phase1_artificial_rmp_preflight"
ARTIFICIAL_PENALTY = 1.0
TRUE_COST_TIE_BREAKER_EPSILON = 1e-9
PHASE1_SCOPE_BOUNDARY = (
    "This is a Phase-I artificial-demand-variable RMP preflight for the second "
    "controlled benchmark current-pool case. It solves only the Phase-I "
    "feasibility skeleton with artificial demand variables. It does not run "
    "pricing, add generated real columns, run add-resolve, run a controlled "
    "loop, transition to Phase II, run full assignment, run full CG, or claim "
    "general convergence, production-scale solving, GTFS, railway, "
    "branch-and-price, RL, or exact arc-LP flow-pattern reproduction."
)


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_manifest(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(ROOT_DIR)).replace("\\", "/"),
        "exists": path.exists(),
        "bytes": path.stat().st_size if path.exists() else None,
        "sha256": sha256_file(path) if path.exists() else None,
    }


def status_from_linprog(result: Any) -> str:
    if result.success:
        return "optimal"
    if result.status == 2:
        return "infeasible"
    if result.status == 3:
        return "unbounded"
    return "not_optimal"


def solve_phase1_rmp(
    arcs: list[dict[str, str]],
    demands: list[dict[str, str]],
    real_columns: list[dict[str, str]],
) -> tuple[dict[str, Any], list[float] | None]:
    try:
        from scipy.optimize import linprog
        from scipy.sparse import coo_matrix
    except ImportError as exc:
        return {
            "solver_status": "solver_unavailable",
            "solver_message": f"scipy.optimize.linprog is unavailable: {exc}",
            "linprog_status_code": None,
            "objective_value_artificial_penalty_units": None,
        }, None

    demand_ids = [row["demand_id"] for row in demands]
    demand_index = {demand_id: idx for idx, demand_id in enumerate(demand_ids)}
    demand_volume = {row["demand_id"]: parse_float(row["volume"], 0.0) for row in demands}
    arc_ids = [row["arc_id"] for row in arcs]
    arc_index = {arc_id: idx for idx, arc_id in enumerate(arc_ids)}

    real_count = len(real_columns)
    artificial_count = len(demands)
    variable_count = real_count + artificial_count

    objective: list[float] = []
    for column in real_columns:
        objective.append(TRUE_COST_TIE_BREAKER_EPSILON * parse_float(column.get("generalized_cost"), 0.0))
    objective.extend([ARTIFICIAL_PENALTY for _ in demands])

    eq_rows: list[int] = []
    eq_cols: list[int] = []
    eq_data: list[float] = []
    for col_pos, column in enumerate(real_columns):
        demand_id = column["demand_id"]
        if demand_id not in demand_index:
            return {
                "solver_status": "precheck_blocked",
                "solver_message": f"real column {column.get('column_id')} references unknown demand {demand_id}",
                "linprog_status_code": None,
                "objective_value_artificial_penalty_units": None,
            }, None
        eq_rows.append(demand_index[demand_id])
        eq_cols.append(col_pos)
        eq_data.append(1.0)
    for artificial_pos, demand in enumerate(demands):
        eq_rows.append(demand_index[demand["demand_id"]])
        eq_cols.append(real_count + artificial_pos)
        eq_data.append(1.0)
    eq_rhs = [demand_volume[demand_id] for demand_id in demand_ids]

    ub_rows: list[int] = []
    ub_cols: list[int] = []
    ub_data: list[float] = []
    for col_pos, column in enumerate(real_columns):
        for arc_id in split_sequence(column.get("arc_sequence")):
            if arc_id not in arc_index:
                return {
                    "solver_status": "precheck_blocked",
                    "solver_message": f"real column {column.get('column_id')} references missing arc {arc_id}",
                    "linprog_status_code": None,
                    "objective_value_artificial_penalty_units": None,
                }, None
            ub_rows.append(arc_index[arc_id])
            ub_cols.append(col_pos)
            ub_data.append(1.0)
    ub_rhs = [max(0.0, parse_float(row.get("capacity"), 0.0)) for row in arcs]

    bounds: list[tuple[float, float]] = []
    for column in real_columns:
        bounds.append((0.0, demand_volume[column["demand_id"]]))
    for demand in demands:
        bounds.append((0.0, demand_volume[demand["demand_id"]]))

    a_eq = coo_matrix((eq_data, (eq_rows, eq_cols)), shape=(len(demands), variable_count)).tocsr()
    a_ub = coo_matrix((ub_data, (ub_rows, ub_cols)), shape=(len(arcs), variable_count)).tocsr()
    result = linprog(
        c=objective,
        A_ub=a_ub,
        b_ub=ub_rhs,
        A_eq=a_eq,
        b_eq=eq_rhs,
        bounds=bounds,
        method="highs",
    )
    return {
        "solver_status": status_from_linprog(result),
        "solver_message": result.message,
        "linprog_status_code": int(result.status),
        "objective_value_artificial_penalty_units": float(result.fun) if result.success else None,
    }, [float(value) for value in result.x] if result.success else None


def build_solution_outputs(
    arcs: list[dict[str, str]],
    demands: list[dict[str, str]],
    real_columns: list[dict[str, str]],
    solution: list[float],
) -> dict[str, Any]:
    real_count = len(real_columns)
    real_values = solution[:real_count]
    artificial_values = solution[real_count:]
    demand_volume = {row["demand_id"]: parse_float(row["volume"], 0.0) for row in demands}
    real_flow_by_demand = {demand_id: 0.0 for demand_id in demand_volume}
    artificial_flow_by_demand = {
        demand["demand_id"]: artificial_values[pos] for pos, demand in enumerate(demands)
    }

    arc_flow = {row["arc_id"]: 0.0 for row in arcs}
    columns_by_arc: dict[str, list[str]] = defaultdict(list)
    demands_by_arc: dict[str, set[str]] = defaultdict(set)
    real_flow_rows: list[dict[str, Any]] = []
    artificial_rows: list[dict[str, Any]] = []

    for column, value in zip(real_columns, real_values):
        demand_id = column["demand_id"]
        real_flow_by_demand[demand_id] += value
        for arc_id in split_sequence(column.get("arc_sequence")):
            arc_flow[arc_id] += value
            if value > TOL:
                columns_by_arc[arc_id].append(column.get("column_id", ""))
                demands_by_arc[arc_id].add(demand_id)
        real_flow_rows.append(
            {
                "column_id": column.get("column_id", ""),
                "path_id": column.get("path_id", ""),
                "demand_id": demand_id,
                "is_artificial": "false",
                "lower_bound": 0.0,
                "upper_bound": demand_volume[demand_id],
                "flow": value,
                "true_generalized_cost": parse_float(column.get("generalized_cost"), 0.0),
                "phase1_objective_coefficient": TRUE_COST_TIE_BREAKER_EPSILON
                * parse_float(column.get("generalized_cost"), 0.0),
                "arc_sequence": column.get("arc_sequence", ""),
            }
        )

    for pos, demand in enumerate(demands):
        demand_id = demand["demand_id"]
        artificial_rows.append(
            {
                "artificial_variable_id": f"ARTIFICIAL_DEMAND_{demand_id}",
                "demand_id": demand_id,
                "is_artificial": "true",
                "lower_bound": 0.0,
                "upper_bound": demand_volume[demand_id],
                "flow": artificial_flow_by_demand[demand_id],
                "has_dynamic_arc_incidence": "false",
                "arc_sequence": "",
                "phase1_objective_coefficient": ARTIFICIAL_PENALTY,
                "objective_units": "artificial_penalty_units",
            }
        )

    demand_rows: list[dict[str, Any]] = []
    max_demand_residual = 0.0
    for demand in demands:
        demand_id = demand["demand_id"]
        volume = demand_volume[demand_id]
        real_flow = real_flow_by_demand[demand_id]
        artificial_flow = artificial_flow_by_demand[demand_id]
        residual = real_flow + artificial_flow - volume
        max_demand_residual = max(max_demand_residual, abs(residual))
        demand_rows.append(
            {
                "demand_id": demand_id,
                "demand_volume": volume,
                "real_served_flow": real_flow,
                "artificial_flow": artificial_flow,
                "demand_residual_after_artificial": residual,
                "status": "PASS" if abs(residual) <= TOL else "FAIL",
            }
        )

    capacity_rows: list[dict[str, Any]] = []
    capacity_violation_count = 0
    max_capacity_violation = 0.0
    for arc in arcs:
        arc_id = arc["arc_id"]
        flow = arc_flow[arc_id]
        capacity = max(0.0, parse_float(arc.get("capacity"), 0.0))
        violation = max(0.0, flow - capacity)
        if violation > TOL:
            capacity_violation_count += 1
        max_capacity_violation = max(max_capacity_violation, violation)
        capacity_rows.append(
            {
                "arc_id": arc_id,
                "arc_type": arc.get("arc_type", ""),
                "physical_link_id": arc.get("physical_link_id", ""),
                "from_time": arc.get("from_time", ""),
                "to_time": arc.get("to_time", ""),
                "real_flow": flow,
                "artificial_flow": 0.0,
                "total_capacity_consuming_flow": flow,
                "capacity": capacity,
                "capacity_violation": violation,
                "slack": capacity - flow,
                "artificial_variable_ids_using_arc": "",
                "real_columns_using_arc": "|".join(sorted(set(columns_by_arc.get(arc_id, [])))),
                "demand_ids_using_arc": "|".join(sorted(demands_by_arc.get(arc_id, set()))),
                "status": "PASS" if violation <= TOL else "FAIL",
            }
        )

    total_artificial_flow = sum(artificial_flow_by_demand.values())
    total_real_flow = sum(real_flow_by_demand.values())
    artificial_zero = total_artificial_flow <= TOL
    demand_ok = max_demand_residual <= TOL
    capacity_ok = capacity_violation_count == 0 and max_capacity_violation <= TOL

    return {
        "real_flow_rows": real_flow_rows,
        "artificial_rows": artificial_rows,
        "demand_rows": demand_rows,
        "capacity_rows": capacity_rows,
        "real_flow_by_demand": real_flow_by_demand,
        "artificial_flow_by_demand": artificial_flow_by_demand,
        "total_real_served_flow": total_real_flow,
        "total_artificial_flow": total_artificial_flow,
        "max_demand_residual": max_demand_residual,
        "capacity_violation_count": capacity_violation_count,
        "max_capacity_violation": max_capacity_violation,
        "demand_constraints_satisfied": demand_ok,
        "capacity_constraints_satisfied": capacity_ok,
        "phase2_transition_allowed": artificial_zero and demand_ok and capacity_ok,
        "expected_phase2_transition_status": "allowed_by_zero_artificial_flow_gate"
        if artificial_zero and demand_ok and capacity_ok
        else "blocked_artificial_flow_positive",
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    artificial_lines = [
        f"- {demand_id}: artificial_flow={value}, real_served_flow={summary['real_served_flow_by_demand'].get(demand_id)}"
        for demand_id, value in summary["artificial_flow_by_demand"].items()
    ]
    lines = [
        "# Phase-I Artificial-Demand RMP Preflight",
        "",
        PHASE1_SCOPE_BOUNDARY,
        "",
        "## Status",
        "",
        f"- Solver status: {summary['solver_status']}",
        f"- Objective value: {summary['objective_value_artificial_penalty_units']} artificial penalty units",
        f"- Total artificial flow: {summary['total_artificial_flow']}",
        f"- Capacity violation count: {summary['capacity_violation_count']}",
        f"- Max capacity violation: {summary['max_capacity_violation']}",
        f"- Baseline dynamic_columns.csv mutated: {summary['baseline_dynamic_columns_mutated']}",
        f"- Phase-II transition allowed: {summary['phase2_transition_allowed']}",
        f"- Expected Phase-II transition status: {summary['expected_phase2_transition_status']}",
        f"- Phase-II transition executed: {summary['phase2_transition_executed']}",
        "",
        "## Artificial Flow By Demand",
        "",
        *artificial_lines,
        "",
        "## Objective Boundary",
        "",
        "The Phase-I objective is an artificial feasibility penalty with a tiny true-cost tie breaker. It is not a true travel cost, generalized cost, benchmark objective, or arc-LP objective.",
        "",
        "## Scope Boundary",
        "",
        PHASE1_SCOPE_BOUNDARY,
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_outputs(
    output_dir: Path,
    summary: dict[str, Any],
    inputs: dict[str, Any],
    hash_audit: dict[str, Any],
    outputs: dict[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "phase1_rmp_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (output_dir / "input_manifest.json").write_text(json.dumps(inputs, indent=2), encoding="utf-8")
    (output_dir / "hash_audit.json").write_text(json.dumps(hash_audit, indent=2), encoding="utf-8")
    write_csv(
        output_dir / "artificial_flow_by_demand.csv",
        outputs.get("artificial_rows", []),
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
        output_dir / "real_flow_by_column.csv",
        outputs.get("real_flow_rows", []),
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
        output_dir / "demand_balance.csv",
        outputs.get("demand_rows", []),
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
        output_dir / "capacity_usage.csv",
        outputs.get("capacity_rows", []),
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
    write_report(output_dir / "phase1_rmp_report.md", summary)


def run_preflight(
    config_path: str | Path = DEFAULT_CURRENT_POOL_CONFIG,
    output_dir: Path = OUTPUT_DIR,
) -> dict[str, Any]:
    config = load_config(config_path)
    data_dir = input_data_dir(config)
    baseline_columns_path = data_dir / "dynamic_columns.csv"
    hash_before = sha256_file(baseline_columns_path)

    current_pool_precheck = run_precheck(config_path)
    arcs = read_csv(data_dir / "dynamic_arc.csv")
    demands = read_csv(data_dir / "dynamic_demand.csv")
    all_columns = read_csv(baseline_columns_path)
    candidates = read_csv(data_dir / "candidate_paths.csv")
    real_columns, selection_blockers = selected_candidate_columns(config, all_columns, candidates)

    inputs = {
        "preflight_name": "phase1_artificial_rmp_preflight",
        "current_pool_config": str(Path(config_path).as_posix()),
        "current_pool_input_mapping": {
            "accepted_current_pool_config": "configs/second_controlled_benchmark_current_pool_rmp.yaml",
            "baseline_real_column_file": str(baseline_columns_path.relative_to(ROOT_DIR)).replace("\\", "/"),
            "selected_candidate_policy": config.get("candidate_pool_policy"),
            "selected_candidate_column_ids": config.get("candidate_column_ids", []),
            "output_dir": str(output_dir.relative_to(ROOT_DIR)).replace("\\", "/"),
        },
        "input_files": {
            "dynamic_arc": file_manifest(data_dir / "dynamic_arc.csv"),
            "dynamic_demand": file_manifest(data_dir / "dynamic_demand.csv"),
            "dynamic_columns": file_manifest(baseline_columns_path),
            "candidate_paths": file_manifest(data_dir / "candidate_paths.csv"),
            "current_pool_precheck_summary": file_manifest(
                ROOT_DIR / "outputs" / "second_controlled_benchmark_link55_current_pool_rmp" / "rmp_precheck_summary.json"
            ),
            "current_pool_rmp_summary": file_manifest(
                ROOT_DIR / "outputs" / "second_controlled_benchmark_link55_current_pool_rmp" / "rmp_summary.json"
            ),
        },
        "current_pool_precheck_status": current_pool_precheck.get("precheck_status"),
        "selection_blockers": selection_blockers,
        "scope": PHASE1_SCOPE_BOUNDARY,
    }

    if selection_blockers:
        solver_info = {
            "solver_status": "precheck_blocked",
            "solver_message": "selected current-pool columns could not be mapped",
            "linprog_status_code": None,
            "objective_value_artificial_penalty_units": None,
        }
        solution_outputs: dict[str, Any] = {
            "real_flow_rows": [],
            "artificial_rows": [],
            "demand_rows": [],
            "capacity_rows": [],
            "real_flow_by_demand": {},
            "artificial_flow_by_demand": {},
            "total_real_served_flow": None,
            "total_artificial_flow": None,
            "max_demand_residual": None,
            "capacity_violation_count": None,
            "max_capacity_violation": None,
            "demand_constraints_satisfied": False,
            "capacity_constraints_satisfied": False,
            "phase2_transition_allowed": False,
            "expected_phase2_transition_status": "blocked_precheck",
        }
    else:
        solver_info, solution = solve_phase1_rmp(arcs, demands, real_columns)
        solution_outputs = build_solution_outputs(arcs, demands, real_columns, solution) if solution else {
            "real_flow_rows": [],
            "artificial_rows": [],
            "demand_rows": [],
            "capacity_rows": [],
            "real_flow_by_demand": {},
            "artificial_flow_by_demand": {},
            "total_real_served_flow": None,
            "total_artificial_flow": None,
            "max_demand_residual": None,
            "capacity_violation_count": None,
            "max_capacity_violation": None,
            "demand_constraints_satisfied": False,
            "capacity_constraints_satisfied": False,
            "phase2_transition_allowed": False,
            "expected_phase2_transition_status": "blocked_solver_status",
        }

    hash_after = sha256_file(baseline_columns_path)
    baseline_mutated = hash_before != hash_after
    artificial_rows = solution_outputs.get("artificial_rows", [])
    real_rows = solution_outputs.get("real_flow_rows", [])
    artificial_by_demand = solution_outputs.get("artificial_flow_by_demand", {})
    real_by_demand = solution_outputs.get("real_flow_by_demand", {})

    summary = {
        **solver_info,
        "preflight_status": "PASS" if solver_info["solver_status"] == "optimal" and not baseline_mutated else "FAIL",
        "phase": "Phase-I artificial-demand-variable RMP preflight",
        "objective_units": "artificial_penalty_units",
        "artificial_penalty": ARTIFICIAL_PENALTY,
        "true_cost_tie_breaker_epsilon": TRUE_COST_TIE_BREAKER_EPSILON,
        "objective_is_true_transport_objective": False,
        "selected_real_column_count": len(real_columns),
        "selected_real_column_ids": [row.get("column_id", "") for row in real_columns],
        "demand_count": len(demands),
        "artificial_variable_count": len(artificial_rows),
        "artificial_variables_exist_for_every_demand": {row["demand_id"] for row in artificial_rows}
        == {row["demand_id"] for row in demands},
        "any_artificial_variable_has_dynamic_arc_incidence": any(
            str(row.get("has_dynamic_arc_incidence", "")).lower() == "true" or bool(row.get("arc_sequence"))
            for row in artificial_rows
        ),
        "artificial_variables_in_real_column_export": any(
            str(row.get("is_artificial", "")).lower() == "true" for row in real_rows
        ),
        "total_artificial_flow": solution_outputs.get("total_artificial_flow"),
        "artificial_flow_by_demand": artificial_by_demand,
        "total_real_served_flow": solution_outputs.get("total_real_served_flow"),
        "real_served_flow_by_demand": real_by_demand,
        "demand_residual_by_demand": {
            row["demand_id"]: row["demand_residual_after_artificial"]
            for row in solution_outputs.get("demand_rows", [])
        },
        "max_demand_residual": solution_outputs.get("max_demand_residual"),
        "capacity_violation_count": solution_outputs.get("capacity_violation_count"),
        "max_capacity_violation": solution_outputs.get("max_capacity_violation"),
        "demand_constraints_satisfied_after_artificial": solution_outputs.get("demand_constraints_satisfied"),
        "capacity_constraints_satisfied": solution_outputs.get("capacity_constraints_satisfied"),
        "baseline_dynamic_columns_path": str(baseline_columns_path.relative_to(ROOT_DIR)).replace("\\", "/"),
        "baseline_dynamic_columns_hash_before": hash_before,
        "baseline_dynamic_columns_hash_after": hash_after,
        "baseline_dynamic_columns_mutated": baseline_mutated,
        "phase2_transition_allowed": bool(solution_outputs.get("phase2_transition_allowed")),
        "expected_phase2_transition_status": solution_outputs.get("expected_phase2_transition_status"),
        "phase2_transition_executed": False,
        "pricing_run": False,
        "generated_real_columns_added": False,
        "add_resolve_run": False,
        "controlled_loop_run": False,
        "full_assignment_run": False,
        "full_cg_run": False,
        "current_pool_scope_boundary": CURRENT_POOL_SCOPE_BOUNDARY,
        "scope": PHASE1_SCOPE_BOUNDARY,
    }
    if summary["solver_status"] == "optimal" and summary["total_artificial_flow"] and summary["total_artificial_flow"] > TOL:
        summary["preflight_interpretation"] = (
            "Phase-I RMP feasible; Phase-II transition blocked because artificial flow remains positive."
        )
    elif summary["solver_status"] == "optimal":
        summary["preflight_interpretation"] = (
            "Phase-I RMP feasible with zero artificial flow observed in preflight; no Phase-II transition was run in this task."
        )
    else:
        summary["preflight_interpretation"] = "Phase-I RMP preflight did not reach an optimal feasible skeleton solution."

    hash_audit = {
        "hash_audit_status": "PASS" if not baseline_mutated else "FAIL",
        "baseline_dynamic_columns_path": summary["baseline_dynamic_columns_path"],
        "baseline_dynamic_columns_hash_before": hash_before,
        "baseline_dynamic_columns_hash_after": hash_after,
        "baseline_dynamic_columns_mutated": baseline_mutated,
        "artificial_columns_written_to_dynamic_columns_csv": False,
        "real_column_export_contains_artificial_variables": summary["artificial_variables_in_real_column_export"],
    }
    write_outputs(output_dir, summary, inputs, hash_audit, solution_outputs)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase-I artificial RMP preflight.")
    parser.add_argument("--config", default=DEFAULT_CURRENT_POOL_CONFIG)
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = ROOT_DIR / output_dir
    summary = run_preflight(args.config, output_dir)
    print(f"Phase-I artificial RMP preflight status: {summary['preflight_status']}")
    print(f"Solver status: {summary['solver_status']}")
    print(f"Objective value in artificial penalty units: {summary['objective_value_artificial_penalty_units']}")
    print(f"Total artificial flow: {summary['total_artificial_flow']}")
    print(f"Artificial flow by demand: {summary['artificial_flow_by_demand']}")
    print(f"Capacity violation count: {summary['capacity_violation_count']}")
    print(f"Baseline dynamic_columns.csv mutated: {summary['baseline_dynamic_columns_mutated']}")
    print(f"Phase-II transition allowed: {summary['phase2_transition_allowed']}")
    print(f"Report: {output_dir / 'phase1_rmp_report.md'}")
    return 0 if summary["preflight_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
