"""Precheck the second controlled benchmark current candidate-pool RMP.

This verifies that the accepted second-benchmark structural columns and
arc-LP reference are available before solving the five-column RMP. It does not
run pricing, add-resolve, a controlled CG loop, full assignment, or full CG.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

import yaml

from build_sioux_harder_bounded_stage2 import ROOT_DIR, resolve_path


DEFAULT_CONFIG = "configs/second_controlled_benchmark_current_pool_rmp.yaml"
TOL = 1e-6
SCOPE_BOUNDARY = (
    "This is the second controlled benchmark current candidate-pool RMP "
    "reference only. It uses the five accepted structural candidate paths and "
    "does not run pricing, add-resolve, controlled loop, full assignment, full "
    "CG, production-scale solving, GTFS, railway, branch-and-price, or RL. It "
    "does not claim CG validation, general convergence, or exact arc-LP "
    "flow-pattern reproduction."
)
REQUIRED_DATA_FILES = [
    "dynamic_node.csv",
    "dynamic_arc.csv",
    "dynamic_demand.csv",
    "dynamic_columns.csv",
    "candidate_paths.csv",
]
EXPECTED_DEMANDS = {
    "D3": {"origin_node_id": "20", "destination_node_id": "10", "departure_time": 0, "volume": 12000.0},
    "D4": {"origin_node_id": "7", "destination_node_id": "10", "departure_time": 2, "volume": 9000.0},
}
EXPECTED_PATHS = {
    "D3_P1": {
        "demand_id": "D3",
        "arc_sequence": "source_D3|move_60_t0|move_55_t4|move_48_t7|sink_D3_10_t11",
        "role": "intended_pressure_route",
    },
    "D3_P2": {
        "demand_id": "D3",
        "arc_sequence": "source_D3|move_61_t0|move_58_t4|move_52_t6|move_48_t8|sink_D3_10_t12",
        "role": "alternate_avoids_link55",
    },
    "D3_P3": {
        "demand_id": "D3",
        "arc_sequence": "source_D3|move_61_t0|move_57_t4|move_43_t7|sink_D3_10_t13",
        "role": "longer_alternate_avoids_link55_and_link48",
    },
    "D4_P1": {
        "demand_id": "D4",
        "arc_sequence": "source_D4|move_18_t2|move_55_t4|move_48_t7|sink_D4_10_t11",
        "role": "intended_pressure_route",
    },
    "D4_P2": {
        "demand_id": "D4",
        "arc_sequence": "source_D4|move_17_t2|move_22_t5|move_48_t10|sink_D4_10_t14",
        "role": "alternate_avoids_link55",
    },
}


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    resolved = resolve_path(path)
    with resolved.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    if not isinstance(config, dict):
        raise ValueError(f"Config must be a mapping: {resolved}")
    if config.get("stage") != "current_candidate_pool_rmp_reference":
        raise ValueError("Current-pool RMP config must set stage: current_candidate_pool_rmp_reference")
    if config.get("run_rmp_now") is not True:
        raise ValueError("Current-pool RMP config must set run_rmp_now: true")
    for key in [
        "run_pricing_now",
        "run_add_resolve_now",
        "run_controlled_loop_now",
        "run_full_assignment_now",
        "claim_cg_validation",
        "claim_full_cg",
        "claim_general_convergence",
        "claim_exact_flow_pattern_reproduction",
    ]:
        if config.get(key) is not False:
            raise ValueError(f"Current-pool RMP config must set {key}: false")
    return config


def input_data_dir(config: dict[str, Any]) -> Path:
    return resolve_path(config["input_dynamic_data_dir"])


def structural_output_dir(config: dict[str, Any]) -> Path:
    return resolve_path(config["structural_output_dir"])


def arc_lp_output_dir(config: dict[str, Any]) -> Path:
    return resolve_path(config["arc_lp_output_dir"])


def output_dir(config: dict[str, Any] | None = None) -> Path:
    cfg = config or load_config()
    return resolve_path(cfg["output_dir"])


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_float(value: Any, default: float = math.nan) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def split_sequence(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split("|") if item.strip()]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def selected_candidate_columns(
    config: dict[str, Any],
    columns: list[dict[str, str]],
    candidate_paths: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[str]]:
    """Return structural dynamic columns annotated with D3_P1-style path ids."""
    blockers: list[str] = []
    candidate_by_path_id = {row.get("path_id", ""): row for row in candidate_paths}
    column_by_key = {
        (row.get("demand_id", ""), row.get("node_sequence", ""), row.get("link_sequence", "")): row
        for row in columns
    }
    selected: list[dict[str, str]] = []
    for path_id in config["candidate_column_ids"]:
        candidate = candidate_by_path_id.get(path_id)
        expected = EXPECTED_PATHS.get(path_id)
        if candidate is None:
            blockers.append(f"{path_id} missing from candidate_paths.csv")
            continue
        key = (candidate.get("demand_id", ""), candidate.get("node_sequence", ""), candidate.get("link_sequence", ""))
        column = column_by_key.get(key)
        if column is None:
            blockers.append(f"{path_id} has no matching dynamic column for key={key}")
            continue
        annotated = dict(column)
        annotated["path_id"] = path_id
        annotated["route_role"] = expected["role"] if expected else ""
        selected.append(annotated)
    return selected, blockers


def column_cost_check(column: dict[str, str], arc_by_id: dict[str, dict[str, str]]) -> tuple[bool, float]:
    movement_cost = sum(parse_float(arc_by_id[arc_id].get("cost"), 0.0) for arc_id in split_sequence(column.get("arc_sequence")) if arc_id in arc_by_id)
    listed = parse_float(column.get("generalized_cost"), 0.0)
    return abs(movement_cost - listed) <= TOL, movement_cost


def write_outputs(out_dir: Path, summary: dict[str, Any], selected_columns: list[dict[str, str]]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "rmp_precheck_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_report(out_dir / "rmp_precheck_report.md", summary)
    write_csv(
        out_dir / "rmp_candidate_pool_audit.csv",
        [
            {
                "path_id": row.get("path_id", ""),
                "column_id": row.get("column_id", ""),
                "demand_id": row.get("demand_id", ""),
                "route_role": row.get("route_role", ""),
                "generalized_cost": row.get("generalized_cost", ""),
                "uses_target_arc": str(summary.get("target_dynamic_arc_id") in split_sequence(row.get("arc_sequence"))).lower(),
                "arc_sequence": row.get("arc_sequence", ""),
            }
            for row in selected_columns
        ],
        ["path_id", "column_id", "demand_id", "route_role", "generalized_cost", "uses_target_arc", "arc_sequence"],
    )


def run_precheck(config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    dat_dir = input_data_dir(config)
    struct_dir = structural_output_dir(config)
    arc_dir = arc_lp_output_dir(config)
    out_dir = output_dir(config)
    out_dir.mkdir(parents=True, exist_ok=True)

    checks: list[dict[str, Any]] = []
    blockers: list[str] = []
    warnings: list[str] = []

    def check(name: str, passed: bool, details: str) -> None:
        checks.append({"check_name": name, "status": "PASS" if passed else "FAIL", "details": details})
        if not passed:
            blockers.append(f"{name}: {details}")

    required_paths = {name: dat_dir / name for name in REQUIRED_DATA_FILES}
    required_paths["structural_summary"] = struct_dir / "structural_summary.json"
    required_paths["arc_lp_summary"] = arc_dir / "arc_lp_summary.json"
    required_paths["arc_lp_behavior_diagnosis"] = arc_dir / "arc_lp_behavior_diagnosis.json"
    missing = [name for name, path in required_paths.items() if not path.exists() or path.stat().st_size == 0]
    check("required structural and arc-LP files exist", not missing, "none" if not missing else ", ".join(missing))
    if missing:
        summary = {
            "precheck_status": "BLOCKED",
            "obvious_blockers": blockers,
            "warnings": warnings,
            "checks": checks,
            "scope": SCOPE_BOUNDARY,
        }
        write_outputs(out_dir, summary, [])
        return summary

    structural = load_json(required_paths["structural_summary"])
    arc_lp_summary = load_json(required_paths["arc_lp_summary"])
    arc_lp_diag = load_json(required_paths["arc_lp_behavior_diagnosis"])
    arcs = read_csv(dat_dir / "dynamic_arc.csv")
    demands = read_csv(dat_dir / "dynamic_demand.csv")
    columns = read_csv(dat_dir / "dynamic_columns.csv")
    candidates = read_csv(dat_dir / "candidate_paths.csv")
    arc_by_id = {row["arc_id"]: row for row in arcs}
    demand_by_id = {row["demand_id"]: row for row in demands}
    selected, selection_blockers = selected_candidate_columns(config, columns, candidates)
    blockers.extend(selection_blockers)
    target_arc_id = str(config["target_dynamic_arc_id"])
    target_arc = arc_by_id.get(target_arc_id)

    check("structural build was accepted", structural.get("structural_status") == "PASS", f"structural_status={structural.get('structural_status')}")
    check("arc-LP reference is optimal", arc_lp_summary.get("solver_status") == "optimal", f"solver_status={arc_lp_summary.get('solver_status')}")
    check(
        "arc-LP reference objective matches config",
        abs(parse_float(arc_lp_summary.get("objective_value")) - parse_float(config["arc_lp_reference_objective"])) <= TOL,
        f"arc_lp_objective={arc_lp_summary.get('objective_value')}",
    )
    check("target arc move_55_t4 exists", target_arc is not None, target_arc_id)
    if target_arc is not None:
        check(
            "target arc maps to physical link 55",
            str(target_arc.get("physical_link_id")) == str(config["target_physical_link_id"]),
            f"physical_link_id={target_arc.get('physical_link_id')}",
        )

    for demand_id, expected in EXPECTED_DEMANDS.items():
        row = demand_by_id.get(demand_id)
        demand_ok = (
            row is not None
            and row.get("origin_node_id") == expected["origin_node_id"]
            and row.get("destination_node_id") == expected["destination_node_id"]
            and parse_int(row.get("departure_time")) == expected["departure_time"]
            and abs(parse_float(row.get("volume")) - expected["volume"]) <= TOL
        )
        check(f"{demand_id} demand row matches expected", demand_ok, str(row) if row else "missing")

    expected_ids = list(config["candidate_column_ids"])
    selected_ids = [row.get("path_id") for row in selected]
    check("exactly the intended five candidate paths are selected", selected_ids == expected_ids, f"selected={selected_ids}")
    check(
        "candidate paths cover D3 and D4",
        {row.get("path_id") for row in selected if row.get("demand_id") == "D3"} == {"D3_P1", "D3_P2", "D3_P3"}
        and {row.get("path_id") for row in selected if row.get("demand_id") == "D4"} == {"D4_P1", "D4_P2"},
        f"selected_by_demand={selected_ids}",
    )

    cost_checks: list[dict[str, Any]] = []
    sequence_checks_ok = True
    costs_ok = True
    for column in selected:
        path_id = column.get("path_id", "")
        expected_sequence = EXPECTED_PATHS[path_id]["arc_sequence"]
        sequence_ok = column.get("arc_sequence") == expected_sequence
        sequence_checks_ok = sequence_checks_ok and sequence_ok
        missing_arcs = [arc_id for arc_id in split_sequence(column.get("arc_sequence")) if arc_id not in arc_by_id]
        cost_ok, computed_cost = column_cost_check(column, arc_by_id)
        costs_ok = costs_ok and cost_ok
        cost_checks.append(
            {
                "path_id": path_id,
                "column_id": column.get("column_id", ""),
                "expected_sequence_match": sequence_ok,
                "missing_arcs": missing_arcs,
                "listed_cost": parse_float(column.get("generalized_cost"), 0.0),
                "computed_cost": computed_cost,
                "cost_status": "PASS" if cost_ok else "FAIL",
            }
        )
        if missing_arcs:
            blockers.append(f"{path_id} references missing arcs: {missing_arcs}")
    check("candidate paths match expected dynamic arc sequences", sequence_checks_ok, "all sequences checked")
    check("candidate path costs can be computed from arcs", costs_ok, json.dumps(cost_checks, sort_keys=True))

    target_intended_demand = sum(
        parse_float(demand_by_id[row["demand_id"]]["volume"], 0.0)
        for row in selected
        if row.get("path_id") in {"D3_P1", "D4_P1"} and target_arc_id in split_sequence(row.get("arc_sequence"))
    )
    target_capacity = parse_float(target_arc.get("capacity")) if target_arc else math.nan
    pressure_ratio = target_intended_demand / target_capacity if target_capacity else math.nan
    check(
        "structural intended target demand exceeds target capacity",
        target_intended_demand > target_capacity,
        f"target_intended_demand={target_intended_demand}, capacity={target_capacity}, ratio={pressure_ratio}",
    )
    for arc_id in config["downstream_dynamic_arc_ids"]:
        check(f"downstream arc {arc_id} exists", arc_id in arc_by_id, arc_id)

    summary = {
        "precheck_status": "PASS" if not blockers else "BLOCKED",
        "experiment_name": config["experiment_name"],
        "stage": "current_candidate_pool_rmp_precheck",
        "structural_status": structural.get("structural_status"),
        "arc_lp_solver_status": arc_lp_summary.get("solver_status"),
        "arc_lp_reference_objective": arc_lp_summary.get("objective_value"),
        "arc_lp_target_arc": arc_lp_diag.get("target_arc", {}),
        "dynamic_arc_count": len(arcs),
        "demand_count": len(demands),
        "dynamic_column_count": len(columns),
        "selected_candidate_path_ids": selected_ids,
        "selected_dynamic_column_ids": [row.get("column_id") for row in selected],
        "selected_candidate_count": len(selected),
        "columns_per_demand": {
            demand_id: len([row for row in selected if row.get("demand_id") == demand_id])
            for demand_id in EXPECTED_DEMANDS
        },
        "candidate_cost_checks": cost_checks,
        "target_dynamic_arc_id": target_arc_id,
        "target_physical_link_id": str(config["target_physical_link_id"]),
        "target_capacity": target_capacity,
        "structural_intended_target_demand": target_intended_demand,
        "structural_intended_pressure_ratio": pressure_ratio,
        "pricing_outputs_required": False,
        "add_resolve_outputs_required": False,
        "controlled_loop_outputs_required": False,
        "checks": checks,
        "obvious_blockers": blockers,
        "warnings": warnings,
        "scope": SCOPE_BOUNDARY,
    }
    write_outputs(out_dir, summary, selected)
    return summary


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Second Controlled Benchmark Current-Pool RMP Precheck",
        "",
        SCOPE_BOUNDARY,
        "",
        f"- Precheck status: {summary['precheck_status']}",
        f"- Structural status: {summary.get('structural_status')}",
        f"- Arc-LP solver status: {summary.get('arc_lp_solver_status')}",
        f"- Arc-LP reference objective: {summary.get('arc_lp_reference_objective')}",
        f"- Selected candidate paths: {', '.join(summary.get('selected_candidate_path_ids', []))}",
        f"- Selected dynamic columns: {', '.join(summary.get('selected_dynamic_column_ids', []))}",
        f"- Target arc: {summary.get('target_dynamic_arc_id')}",
        f"- Target capacity: {summary.get('target_capacity')}",
        f"- Structural intended target demand: {summary.get('structural_intended_target_demand')}",
        f"- Structural intended pressure ratio: {summary.get('structural_intended_pressure_ratio')}",
        "",
        "## Checks",
        "",
    ]
    lines.extend(f"- {row['status']} - {row['check_name']}: {row['details']}" for row in summary.get("checks", []))
    lines.extend(["", "## Obvious Blockers", ""])
    lines.extend(f"- {item}" for item in summary.get("obvious_blockers", [])) if summary.get("obvious_blockers") else lines.append("- None")
    lines.extend(["", "## Scope Boundary", "", SCOPE_BOUNDARY])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Precheck second controlled benchmark current-pool RMP.")
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = run_precheck(args.config)
    print(f"Second benchmark current-pool RMP precheck status: {summary['precheck_status']}")
    print(f"Arc-LP status: {summary.get('arc_lp_solver_status')}")
    print(f"Selected candidates: {summary.get('selected_candidate_path_ids')}")
    print(f"Obvious blockers: {len(summary.get('obvious_blockers', []))}")
    print(f"Report: {output_dir(load_config(args.config)) / 'rmp_precheck_report.md'}")
    return 0 if summary["precheck_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
