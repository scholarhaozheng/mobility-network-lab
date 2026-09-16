"""Run one user-supplied finite network through auto/supplied seeds and existing CG."""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

from explicit_network_workflow import ExplicitWorkflowSettings, run_explicit_workflow
from external_network_input import (
    SEED_FIELDS,
    InputContractError,
    enforce_limits,
    generate_auto_seeds,
    load_case_config,
    normalize_inputs,
    read_csv,
    sha256_file,
    signature,
    size_estimate,
    validate_supplied_seeds,
    write_csv,
    write_json,
)
from external_sioux_static_to_dynamic import ExplicitAllowedNetworkConfig


SEED_REPORT_FIELDS = [
    "demand_id",
    "origin_node_id",
    "destination_node_id",
    "requested_k",
    "generated_count",
    "status",
    "reason",
    "topology_reachable",
    "shortest_travel_time",
    "fixed_horizon_travel_budget",
    "search_states",
    "search_budget",
]


def _integer(value: Any, field: str, *, minimum: int = 0, maximum: int | None = None) -> int:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise InputContractError(f"{field} must be an integer") from exc
    if not math.isfinite(number) or not number.is_integer() or number < minimum:
        raise InputContractError(f"{field} must be an integer >= {minimum}")
    result = int(number)
    if maximum is not None and result > maximum:
        raise InputContractError(f"{field} must be <= {maximum}")
    return result


def _float(value: Any, field: str, *, minimum: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise InputContractError(f"{field} must be numeric") from exc
    if not math.isfinite(number) or number < minimum:
        raise InputContractError(f"{field} must be finite and >= {minimum}")
    return number


def model_config_from_spec(spec: dict[str, Any], total_volume: float) -> ExplicitAllowedNetworkConfig:
    model = spec["model"]
    time_step = _integer(model.get("time_step_minutes"), "model.time_step_minutes", minimum=1)
    if time_step != 1:
        raise InputContractError("model.time_step_minutes must be 1 in this release")
    departure = _integer(model.get("departure_time"), "model.departure_time")
    horizon = _integer(model.get("horizon"), "model.horizon", minimum=1)
    if horizon <= departure:
        raise InputContractError("model.horizon must be greater than departure_time")
    wait_cost = _float(model.get("waiting_cost"), "model.waiting_cost")
    raw_wait_capacity = model.get("waiting_capacity")
    wait_capacity = None if raw_wait_capacity is None else _float(raw_wait_capacity, "model.waiting_capacity")
    if wait_capacity is not None and wait_capacity < total_volume:
        raise InputContractError("model.waiting_capacity must be at least total positive demand volume")
    return ExplicitAllowedNetworkConfig(
        time_step_minutes=time_step,
        departure_time=departure,
        horizon=horizon,
        waiting_cost=wait_cost,
        waiting_capacity=wait_capacity,
        scope_label=str(spec.get("scope_label") or "USER_FINITE_EXPLICIT_ALLOWED_NETWORK"),
    )


def workflow_settings_from_spec(spec: dict[str, Any]) -> ExplicitWorkflowSettings:
    cg = spec["cg"]
    pricing = str(cg.get("phase_ii_pricing_mode"))
    if pricing not in {"one_probe", "k_shortest"}:
        raise InputContractError("cg.phase_ii_pricing_mode must be one_probe or k_shortest")
    add_policy = str(cg.get("phase_ii_add_policy"))
    if add_policy not in {"add_best_one_per_round", "add_best_one_per_demand"}:
        raise InputContractError("unsupported cg.phase_ii_add_policy")
    return ExplicitWorkflowSettings(
        max_phase_i_rounds=_integer(cg.get("max_phase_i_rounds"), "cg.max_phase_i_rounds"),
        max_phase_ii_rounds=_integer(cg.get("max_phase_ii_rounds"), "cg.max_phase_ii_rounds"),
        max_candidates_per_demand_per_round=_integer(
            cg.get("max_candidates_per_demand_per_round"), "cg.max_candidates_per_demand_per_round", minimum=1
        ),
        runtime_cap_seconds=_integer(cg.get("runtime_cap_seconds"), "cg.runtime_cap_seconds", minimum=1, maximum=300),
        phase_ii_pricing_mode=pricing,
        phase_ii_add_policy=add_policy,
        k_shortest_k=_integer(cg.get("k_shortest_k"), "cg.k_shortest_k", minimum=1),
        max_phase_ii_candidates_per_demand=_integer(
            cg.get("max_phase_ii_candidates_per_demand"), "cg.max_phase_ii_candidates_per_demand", minimum=1
        ),
        max_phase_ii_candidates_per_round=_integer(
            cg.get("max_phase_ii_candidates_per_round"), "cg.max_phase_ii_candidates_per_round", minimum=1
        ),
        strict_phase_ii_candidate_round_cap=bool(cg.get("strict_phase_ii_candidate_round_cap", False)),
    )


def _paths_overlap(left: Path, right: Path) -> bool:
    try:
        left.relative_to(right)
        return True
    except ValueError:
        pass
    try:
        right.relative_to(left)
        return True
    except ValueError:
        return False


def _write_normalized(output: Path, prepared: dict[str, Any]) -> None:
    normalized = output / "normalized_inputs"
    write_csv(normalized / "node.csv", prepared["nodes"], ["node_id"])
    write_csv(
        normalized / "link.csv",
        prepared["links"],
        ["link_id", "from_node_id", "to_node_id", "travel_time", "cost", "capacity"],
    )
    write_csv(
        normalized / "demand.csv",
        prepared["demands"],
        [
            "demand_id",
            "origin_node_id",
            "destination_node_id",
            "departure_time",
            "volume",
            "source_origin_id",
            "source_destination_id",
            "source_endpoint_type",
        ],
    )
    write_csv(
        normalized / "excluded_zero_demands.csv",
        prepared["excluded_zero_demands"],
        [
            "demand_id",
            "origin_node_id",
            "destination_node_id",
            "departure_time",
            "volume",
            "source_origin_id",
            "source_destination_id",
            "source_endpoint_type",
        ],
    )
    if prepared["zone_access"]:
        write_csv(normalized / "zone_access.csv", prepared["zone_access"], ["zone_id", "node_id"])


def _artifact_hashes(output: Path) -> dict[str, dict[str, Any]]:
    paths = {
        "normalized_nodes": output / "normalized_inputs" / "node.csv",
        "normalized_links": output / "normalized_inputs" / "link.csv",
        "normalized_demands": output / "normalized_inputs" / "demand.csv",
        "normalized_input_json": output / "normalized_inputs" / "normalized_input.json",
        "static_seeds": output / "seeds" / "static_seed_candidates.csv",
        "static_seeds_json": output / "seeds" / "static_seed_candidates.json",
        "dynamic_nodes": output / "dynamic_inputs" / "dynamic_node.csv",
        "dynamic_arcs": output / "dynamic_inputs" / "dynamic_arc.csv",
        "dynamic_demands": output / "dynamic_inputs" / "dynamic_demand.csv",
        "initial_dynamic_columns": output / "dynamic_inputs" / "dynamic_columns.csv",
        "final_pool": output / "full_cg_v1_run" / "full_cg_v1_phase_ii_final_pool.csv",
        "final_column_flows": output / "full_cg_v1_run" / "full_cg_v1_phase_ii_final_solution_by_column.csv",
        "final_duals": output / "full_cg_v1_run" / "full_cg_v1_phase_ii_final_dual_solution.json",
    }
    return {
        name: {
            "path": path.relative_to(output).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for name, path in paths.items()
        if path.is_file()
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    started = time.monotonic()
    input_root = Path(args.input).resolve()
    config_path = Path(args.config).resolve()
    output = Path(args.output).resolve()
    if not input_root.is_dir():
        raise FileNotFoundError(f"--input directory missing: {input_root}")
    if _paths_overlap(input_root, output):
        raise InputContractError("--input and --output must be separate non-overlapping directory trees")
    if args.seed_mode == "supplied":
        if not args.seeds:
            raise InputContractError("--seed-mode supplied requires --seeds")
        supplied_path = Path(args.seeds).resolve()
        if not supplied_path.is_file():
            raise FileNotFoundError(f"supplied seed file missing: {supplied_path}")
        if _paths_overlap(supplied_path, output):
            raise InputContractError("supplied seed file must be outside --output")
    else:
        if args.seeds:
            raise InputContractError("--seed-mode auto does not accept or read --seeds")
        if args.seed_k is None:
            raise InputContractError("--seed-mode auto requires --seed-k")

    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise FileExistsError(f"output directory already exists and is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)

    spec, source_paths = load_case_config(config_path, input_root)
    prepared = normalize_inputs(spec, source_paths)
    _write_normalized(output, prepared)
    write_json(
        output / "normalized_inputs" / "normalized_input.json",
        {
            "schema_version": spec["schema_version"],
            "nodes": prepared["nodes"],
            "links": prepared["links"],
            "demands": prepared["demands"],
            "excluded_zero_demands": prepared["excluded_zero_demands"],
            "zone_access": prepared["zone_access"],
            "model": spec["model"],
        },
    )
    model_config = model_config_from_spec(spec, sum(float(row["volume"]) for row in prepared["demands"]))
    requested_seed_k = int(args.seed_k) if args.seed_mode == "auto" else 1
    estimate = size_estimate(prepared["nodes"], prepared["links"], prepared["demands"], spec["model"])
    limits = enforce_limits(estimate, spec["limits"], requested_seed_k)

    if args.seed_mode == "auto":
        seeds, seed_report, blockers = generate_auto_seeds(
            prepared["links"],
            prepared["demands"],
            departure_time=model_config.departure_time,
            horizon=model_config.horizon,
            seed_k=requested_seed_k,
            max_states_per_demand=limits["max_seed_search_states_per_demand"],
        )
        route_sources_read: list[str] = []
    else:
        seeds, seed_report, blockers = validate_supplied_seeds(
            read_csv(supplied_path),
            prepared["links"],
            prepared["demands"],
            departure_time=model_config.departure_time,
            horizon=model_config.horizon,
        )
        route_sources_read = [str(supplied_path)]
    seed_dir = output / "seeds"
    write_csv(seed_dir / "static_seed_candidates.csv", seeds, SEED_FIELDS)
    write_json(seed_dir / "static_seed_candidates.json", {"seed_mode": args.seed_mode, "seeds": seeds})
    write_csv(seed_dir / "seed_report.csv", seed_report, SEED_REPORT_FIELDS)
    write_json(
        seed_dir / "seed_report.json",
        {
            "status": "PASS" if not blockers else "FAIL",
            "seed_mode": args.seed_mode,
            "requested_seed_k": args.seed_k if args.seed_mode == "auto" else None,
            "positive_demand_count": len(prepared["demands"]),
            "seed_count": len(seeds),
            "ranking_rule": "travel_time_then_link_id_sequence" if args.seed_mode == "auto" else "supplied_file_order_per_demand",
            "blockers": blockers,
            "per_demand": seed_report,
        },
    )
    if blockers:
        raise InputContractError("seed preparation blocked: " + "; ".join(blockers))

    workflow = run_explicit_workflow(
        nodes=prepared["nodes"],
        allowed_links=prepared["links"],
        demands=prepared["demands"],
        seed_columns=seeds,
        model_config=model_config,
        output_dir=output,
        benchmark_id=str(spec.get("benchmark_id") or "external_finite_network"),
        settings=workflow_settings_from_spec(spec),
        provenance={
            "external_input_schema_version": spec["schema_version"],
            "seed_mode": args.seed_mode,
            "seed_k": args.seed_k if args.seed_mode == "auto" else None,
            "route_artifact_sources_read": route_sources_read,
            "auto_preexisting_seed_route_assignment_columns_read": False,
        },
    )
    result = workflow["result"]
    manifest = {
        "schema": "gmns_external_run_manifest_v1",
        "status": result["status"],
        "benchmark_id": result["benchmark_id"],
        "input_root": str(input_root),
        "config_path": str(config_path),
        "config_sha256": sha256_file(config_path),
        "input_files": prepared["input_files"],
        "input_signature": signature(
            {"nodes": prepared["nodes"], "links": prepared["links"], "demands": prepared["demands"], "model": spec["model"]}
        ),
        "model_schema_version": workflow["model"]["model_schema_version"],
        "model_signature": workflow["model"]["model_signature"],
        "static_seed_signature": signature(seeds),
        "seed_pool_signature": workflow["model"]["seed_pool_signature"],
        "seed_mode": args.seed_mode,
        "seed_k": args.seed_k if args.seed_mode == "auto" else None,
        "seed_source": str(supplied_path) if args.seed_mode == "supplied" else "GENERATED_BY_EXTERNAL_NETWORK_INPUT",
        "auto_preexisting_seed_route_assignment_columns_read": False if args.seed_mode == "auto" else None,
        "route_artifact_sources_read": route_sources_read,
        "size_estimate": estimate,
        "enforced_limits": limits,
        "excluded_zero_demand_count": len(prepared["excluded_zero_demands"]),
        "reference_and_cg_share_exact_dynamic_graph": True,
        "seed_columns_define_network": False,
        "artifacts": _artifact_hashes(output),
        "artifact_roles": {
            "seeds/static_seed_candidates.csv": "static physical-link seeds; input/initialization only",
            "dynamic_inputs/dynamic_columns.csv": "time-expanded initial RMP columns",
            "full_cg_v1_run/full_cg_v1_phase_ii_candidate_log.csv": "pricing candidates including rejected/duplicates",
            "full_cg_v1_run/full_cg_v1_phase_ii_selected_columns.csv": "columns selected for addition",
            "full_cg_v1_run/full_cg_v1_phase_ii_final_pool.csv": "exact last successfully solved final pool",
            "full_cg_v1_run/full_cg_v1_phase_ii_final_solution_by_column.csv": "all final-pool column flows including genuine zero flows",
            "full_cg_v1_run/full_cg_v1_phase_ii_final_dual_solution.json": "final RMP row duals and variable-bound marginals",
            "offline_verification.json": "solver-free verification written by gmns verify/launcher",
        },
        "runtime": {
            "python_executable": str(Path(sys.executable).resolve()),
            "pipeline_module": str(Path(__file__).resolve()),
        },
        "elapsed_seconds_before_launcher_verification": round(time.monotonic() - started, 6),
        "claim_boundary": "bounded finite explicit-allowed-network model; not full DTA or city calibration",
    }
    write_json(output / "external_run_manifest.json", manifest)
    final = {
        "status": result["status"],
        "blockers": [] if result["status"] == "PASS" else ["existing explicit workflow did not finish with full export PASS"],
        "benchmark_id": result["benchmark_id"],
        "seed_mode": args.seed_mode,
        "seed_count": len(seeds),
        "model_signature": result["model_signature"],
        "seed_pool_signature": result["seed_pool_signature"],
        "reference_objective": result["reference_objective"],
        "cg_objective": result["cg_objective"],
        "stop_reason": result["stop_reason"],
        "phase_ii_candidates_added": result["phase_ii_candidates_added"],
        "full_solution_and_duals_present": result["full_solution_and_duals_present"],
        "elapsed_seconds": round(time.monotonic() - started, 6),
    }
    write_json(output / "external_run_result.json", final)
    return final


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--seed-mode", required=True, choices=["auto", "supplied"])
    parser.add_argument("--seed-k", type=int)
    parser.add_argument("--seeds")
    parser.add_argument("--output", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output = Path(args.output).resolve()
    output_initially_available = not output.exists() or (output.is_dir() and not any(output.iterdir()))
    input_output_safe = not _paths_overlap(Path(args.input).resolve(), output)
    seed_output_safe = not args.seeds or not _paths_overlap(Path(args.seeds).resolve(), output)
    try:
        result = run(args)
    except Exception as exc:
        result = {
            "status": "FAIL",
            "blockers": [f"{type(exc).__name__}: {exc}"],
            "seed_mode": args.seed_mode,
            "optimization_completed": False,
        }
        if output_initially_available and input_output_safe and seed_output_safe:
            output.mkdir(parents=True, exist_ok=True)
            write_json(output / "external_run_result.json", result)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
