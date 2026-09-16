"""Solver-free independent verification for one external finite-network run."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
from typing import Any


TOL = 1e-6


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def signature(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def split_sequence(value: Any) -> list[str]:
    return [item.strip() for item in str(value or "").replace(";", "|").split("|") if item.strip()]


def _safe_artifact(run_root: Path, relative: str) -> Path:
    pure = PurePosixPath(relative)
    if pure.is_absolute() or not pure.parts or any(part in {"", ".", ".."} for part in pure.parts):
        raise ValueError(f"unsafe artifact path in run manifest: {relative}")
    path = (run_root / Path(*pure.parts)).resolve()
    path.relative_to(run_root)
    return path


def _compare_json_to_csv(json_rows: list[dict[str, Any]], csv_rows: list[dict[str, str]], label: str, blockers: list[str]) -> None:
    if len(json_rows) != len(csv_rows):
        blockers.append(f"{label} JSON/CSV row counts differ")
        return
    for index, (left, right) in enumerate(zip(json_rows, csv_rows, strict=True)):
        for key, value in right.items():
            expected = "" if left.get(key) is None else str(left.get(key, ""))
            if str(value) != expected:
                blockers.append(f"{label} JSON/CSV mismatch at row {index} field {key}")
                return


def verify_external_run(run_root: Path, core: dict[str, Any]) -> dict[str, Any]:
    run_root = run_root.resolve()
    required = {
        "manifest": run_root / "external_run_manifest.json",
        "result": run_root / "external_run_result.json",
        "normalized": run_root / "normalized_inputs" / "normalized_input.json",
        "nodes": run_root / "normalized_inputs" / "node.csv",
        "links": run_root / "normalized_inputs" / "link.csv",
        "demands": run_root / "normalized_inputs" / "demand.csv",
        "seeds_json": run_root / "seeds" / "static_seed_candidates.json",
        "seeds_csv": run_root / "seeds" / "static_seed_candidates.csv",
        "seed_report": run_root / "seeds" / "seed_report.json",
        "model": run_root / "explicit_model_summary.json",
        "reference": run_root / "arc_lp_reference_summary.json",
        "dynamic_nodes": run_root / "dynamic_inputs" / "dynamic_node.csv",
        "dynamic_arcs": run_root / "dynamic_inputs" / "dynamic_arc.csv",
        "dynamic_demands": run_root / "dynamic_inputs" / "dynamic_demand.csv",
        "initial_columns": run_root / "dynamic_inputs" / "dynamic_columns.csv",
        "final_pool": run_root / "full_cg_v1_run" / "full_cg_v1_phase_ii_final_pool.csv",
        "final_solution": run_root / "full_cg_v1_run" / "full_cg_v1_phase_ii_final_solution_by_column.csv",
        "final_dual": run_root / "full_cg_v1_run" / "full_cg_v1_phase_ii_final_dual_solution.json",
        "cg_summary": run_root / "full_cg_v1_run" / "full_cg_v1_run_summary.json",
    }
    missing = [str(path) for path in required.values() if not path.is_file()]
    if missing:
        return {"status": "FAIL", "blockers": ["missing required external artifact: " + path for path in missing]}
    manifest = read_json(required["manifest"])
    result = read_json(required["result"])
    normalized = read_json(required["normalized"])
    seed_payload = read_json(required["seeds_json"])
    seed_report = read_json(required["seed_report"])
    model = read_json(required["model"])
    reference = read_json(required["reference"])
    cg_summary = read_json(required["cg_summary"])
    final_dual = read_json(required["final_dual"])
    blockers = list(core.get("blockers", []))

    if manifest.get("schema") != "gmns_external_run_manifest_v1" or manifest.get("status") != "PASS":
        blockers.append("external run manifest schema/status is not PASS")
    if result.get("status") != "PASS" or seed_report.get("status") != "PASS":
        blockers.append("external result or seed preparation did not report PASS")
    artifacts = manifest.get("artifacts", {})
    if not isinstance(artifacts, dict) or not artifacts:
        blockers.append("run manifest has no artifact hash map")
    else:
        for name, record in artifacts.items():
            try:
                path = _safe_artifact(run_root, str(record.get("path", "")))
            except Exception as exc:
                blockers.append(f"artifact {name} has unsafe path: {exc}")
                continue
            if not path.is_file():
                blockers.append(f"artifact {name} is missing")
            elif path.stat().st_size != int(record.get("bytes", -1)) or sha256_file(path) != record.get("sha256"):
                blockers.append(f"artifact {name} hash/size mismatch")

    nodes = normalized.get("nodes", [])
    links = normalized.get("links", [])
    demands = normalized.get("demands", [])
    seeds = seed_payload.get("seeds", [])
    if not all(isinstance(rows, list) for rows in [nodes, links, demands, seeds]):
        blockers.append("normalized input or seed JSON rows are malformed")
        nodes, links, demands, seeds = [], [], [], []
    _compare_json_to_csv(nodes, read_csv(required["nodes"]), "nodes", blockers)
    _compare_json_to_csv(links, read_csv(required["links"]), "links", blockers)
    _compare_json_to_csv(demands, read_csv(required["demands"]), "demands", blockers)
    _compare_json_to_csv(seeds, read_csv(required["seeds_csv"]), "seeds", blockers)

    expected_input_signature = signature(
        {"nodes": nodes, "links": links, "demands": demands, "model": normalized.get("model")}
    )
    if manifest.get("input_signature") != expected_input_signature:
        blockers.append("normalized input signature mismatch")
    if manifest.get("static_seed_signature") != signature(seeds):
        blockers.append("static seed signature mismatch")
    model_payload = {
        "model_schema_version": model.get("model_schema_version"),
        "network_mode": model.get("network_mode"),
        "model_config": {
            "time_step_minutes": model.get("config", {}).get("time_step_minutes"),
            "departure_time": model.get("config", {}).get("departure_time"),
            "horizon": model.get("config", {}).get("horizon"),
            "waiting_cost": model.get("config", {}).get("waiting_cost"),
            "waiting_capacity": model.get("config", {}).get("waiting_capacity"),
        },
        "dynamic_nodes": model.get("dynamic_nodes"),
        "dynamic_arcs": model.get("dynamic_arcs"),
        "dynamic_demands": model.get("dynamic_demands"),
    }
    recalculated_model_signature = signature(model_payload)
    if recalculated_model_signature != model.get("model_signature") or recalculated_model_signature != manifest.get("model_signature"):
        blockers.append("model signature does not recompute or propagate")
    recalculated_seed_pool_signature = signature(model.get("dynamic_columns", []))
    if recalculated_seed_pool_signature != model.get("seed_pool_signature") or recalculated_seed_pool_signature != manifest.get(
        "seed_pool_signature"
    ):
        blockers.append("initial dynamic seed-pool signature does not recompute or propagate")
    if manifest.get("model_signature") != core.get("model_signature"):
        blockers.append("final RMP solution model signature differs from external model")

    if manifest.get("seed_mode") == "auto":
        if manifest.get("auto_preexisting_seed_route_assignment_columns_read") is not False:
            blockers.append("auto run does not certify that pre-existing route artifacts were unread")
        if manifest.get("route_artifact_sources_read") != []:
            blockers.append("auto run lists a pre-existing route artifact source")
    elif manifest.get("seed_mode") == "supplied":
        if len(manifest.get("route_artifact_sources_read", [])) != 1:
            blockers.append("supplied run does not identify exactly one supplied seed source")
    else:
        blockers.append("unknown seed_mode in external manifest")

    node_ids = [str(row.get("node_id", "")) for row in nodes]
    link_ids = [str(row.get("link_id", "")) for row in links]
    demand_ids = [str(row.get("demand_id", "")) for row in demands]
    if not node_ids or len(node_ids) != len(set(node_ids)):
        blockers.append("normalized node IDs are empty/duplicate")
    if not link_ids or len(link_ids) != len(set(link_ids)):
        blockers.append("normalized link IDs are empty/duplicate")
    if not demand_ids or len(demand_ids) != len(set(demand_ids)):
        blockers.append("normalized positive demand IDs are empty/duplicate")
    link_by_id = {str(row["link_id"]): row for row in links}
    demand_by_id = {str(row["demand_id"]): row for row in demands}
    seeds_by_demand = {demand_id: 0 for demand_id in demand_ids}
    seed_ids: set[str] = set()
    for seed in seeds:
        column_id = str(seed.get("column_id", ""))
        demand_id = str(seed.get("demand_id", ""))
        if not column_id or column_id in seed_ids:
            blockers.append("static seed column IDs are empty/duplicate")
            continue
        seed_ids.add(column_id)
        if demand_id not in demand_by_id:
            blockers.append(f"static seed {column_id} references unknown demand")
            continue
        sequence = split_sequence(seed.get("link_sequence"))
        if not sequence or any(item not in link_by_id for item in sequence):
            blockers.append(f"static seed {column_id} has missing/disallowed link")
            continue
        path_links = [link_by_id[item] for item in sequence]
        demand = demand_by_id[demand_id]
        if path_links[0]["from_node_id"] != demand["origin_node_id"] or path_links[-1]["to_node_id"] != demand["destination_node_id"]:
            blockers.append(f"static seed {column_id} endpoints mismatch")
        if any(left["to_node_id"] != right["from_node_id"] for left, right in zip(path_links, path_links[1:])):
            blockers.append(f"static seed {column_id} chain is broken")
        travel = sum(int(link["travel_time"]) for link in path_links)
        cost = sum(float(link["cost"]) for link in path_links)
        reported_travel = finite(seed.get("travel_time"))
        reported_cost = finite(seed.get("generalized_cost"))
        if reported_travel != travel or reported_cost is None or not math.isclose(reported_cost, cost, abs_tol=TOL):
            blockers.append(f"static seed {column_id} travel time/cost does not recompute")
        if int(demand["departure_time"]) + travel > int(normalized["model"]["horizon"]):
            blockers.append(f"static seed {column_id} exceeds horizon")
        seeds_by_demand[demand_id] += 1
    if any(count == 0 for count in seeds_by_demand.values()):
        blockers.append("one or more positive demands have no static seed")

    dynamic_nodes = read_csv(required["dynamic_nodes"])
    dynamic_arcs = read_csv(required["dynamic_arcs"])
    dynamic_demands = read_csv(required["dynamic_demands"])
    initial_columns = read_csv(required["initial_columns"])
    _compare_json_to_csv(model.get("dynamic_nodes", []), dynamic_nodes, "dynamic nodes", blockers)
    _compare_json_to_csv(model.get("dynamic_arcs", []), dynamic_arcs, "dynamic arcs", blockers)
    _compare_json_to_csv(model.get("dynamic_demands", []), dynamic_demands, "dynamic demands", blockers)
    _compare_json_to_csv(model.get("dynamic_columns", []), initial_columns, "initial dynamic columns", blockers)
    dynamic_node_ids = {row.get("node_time_id", "") for row in dynamic_nodes}
    arc_by_id = {row.get("arc_id", ""): row for row in dynamic_arcs}
    if len(arc_by_id) != len(dynamic_arcs):
        blockers.append("dynamic arc IDs are duplicate")
    for arc_id, arc in arc_by_id.items():
        if arc.get("from_node_time_id") not in dynamic_node_ids or arc.get("to_node_time_id") not in dynamic_node_ids:
            blockers.append(f"dynamic arc {arc_id} has missing endpoint")
        start, end = finite(arc.get("from_time")), finite(arc.get("to_time"))
        if start is None or end is None or end < start:
            blockers.append(f"dynamic arc {arc_id} has invalid time direction")
        if finite(arc.get("cost")) is None or finite(arc.get("capacity")) is None:
            blockers.append(f"dynamic arc {arc_id} has nonfinite cost/capacity")

    final_pool = read_csv(required["final_pool"])
    final_solution = read_csv(required["final_solution"])
    solution_by_id = {row.get("column_id", ""): row for row in final_solution}
    demand_flow = {str(row["demand_id"]): 0.0 for row in dynamic_demands}
    arc_flow = {arc_id: 0.0 for arc_id in arc_by_id}
    recomputed_objective = 0.0
    for column in final_pool:
        column_id = column.get("column_id", "")
        demand_id = column.get("demand_id", "")
        flow = finite(solution_by_id.get(column_id, {}).get("flow"))
        if flow is None or flow < -TOL:
            blockers.append(f"final column {column_id} has invalid flow")
            continue
        flow = max(0.0, flow)
        sequence = split_sequence(column.get("arc_sequence"))
        if not sequence or any(arc_id not in arc_by_id for arc_id in sequence):
            blockers.append(f"final column {column_id} references missing dynamic arc")
            continue
        current = None
        for position, arc_id in enumerate(sequence):
            arc = arc_by_id[arc_id]
            if position and arc.get("from_node_time_id") != current:
                blockers.append(f"final column {column_id} has broken dynamic chain")
                break
            current = arc.get("to_node_time_id")
            arc_flow[arc_id] += flow
        cost = sum(float(arc_by_id[arc_id]["cost"]) for arc_id in sequence)
        declared_cost = finite(column.get("generalized_cost"))
        if declared_cost is None or not math.isclose(cost, declared_cost, abs_tol=TOL):
            blockers.append(f"final column {column_id} cost does not recompute")
        recomputed_objective += cost * flow
        if demand_id not in demand_flow:
            blockers.append(f"final column {column_id} references unknown demand")
        else:
            demand_flow[demand_id] += flow
    for demand in dynamic_demands:
        demand_id = str(demand["demand_id"])
        if not math.isclose(demand_flow[demand_id], float(demand["volume"]), abs_tol=TOL):
            blockers.append(f"final demand balance mismatch for {demand_id}")
    for arc_id, value in arc_flow.items():
        if value > float(arc_by_id[arc_id]["capacity"]) + TOL:
            blockers.append(f"final dynamic capacity exceeded for {arc_id}")
    reported_objective = finite(cg_summary.get("phase_ii_final_objective"))
    reference_objective = finite(reference.get("objective_value"))
    reported_matches_recomputed = reported_objective is not None and math.isclose(
        recomputed_objective, reported_objective, abs_tol=TOL
    )
    reported_matches_reference = (
        reference_objective is not None
        and reported_objective is not None
        and math.isclose(reference_objective, reported_objective, abs_tol=TOL)
    )
    recomputed_matches_reference = reference_objective is not None and math.isclose(
        recomputed_objective, reference_objective, abs_tol=TOL
    )
    reference_lp_valid = (
        reference.get("reference_status") == "REFERENCE_GENERATED"
        and reference.get("capacity_violation_count") == 0
        and finite(reference.get("max_flow_balance_residual")) is not None
        and abs(float(reference["max_flow_balance_residual"])) <= TOL
    )
    if not reported_matches_recomputed:
        blockers.append("final objective does not recompute from dynamic arc costs and all column flows")
    if reference.get("reference_status") != "REFERENCE_GENERATED" or reference.get("capacity_violation_count") != 0:
        blockers.append("same-model reference LP result is missing or infeasible")
    if finite(reference.get("max_flow_balance_residual")) is None or abs(float(reference["max_flow_balance_residual"])) > TOL:
        blockers.append("reference LP flow-balance residual failed")
    if not reported_matches_reference:
        blockers.append("external CG objective does not match the same explicit-network reference objective")
    if not recomputed_matches_reference:
        blockers.append("independently recomputed flow objective does not match the same explicit-network reference objective")

    zero_count = sum(abs(finite(row.get("flow")) or 0.0) <= TOL for row in final_solution)
    if int(core.get("zero_flow_row_count", -1)) != zero_count:
        blockers.append("zero-flow row count differs between independent checks")
    if final_dual.get("model_signature") != manifest.get("model_signature"):
        blockers.append("final dual model signature differs from external model")
    stop_reason = cg_summary.get("stop_reason")
    independent_pricing_closed_reasons = {
        "all_demands_priced_no_improving_candidate",
        "no_improving_nonduplicate_candidate",
    }
    independent_pricing_certificate_present = stop_reason in independent_pricing_closed_reasons
    if independent_pricing_certificate_present:
        pricing_closure_reason = "stop reason records completed pricing with no improving nonduplicate candidate"
    elif stop_reason == "objective_level_reference_match":
        pricing_closure_reason = (
            "not claimed: the independently recomputed objective matches the same-model reference LP, "
            "but no independent missing-column pricing certificate was completed"
        )
    else:
        pricing_closure_reason = "not claimed: the recorded stop reason is not an independent pricing-closure certificate"
    return {
        "status": "PASS" if not blockers else "FAIL",
        "blockers": blockers,
        "verification_scope": "external finite explicit-allowed-network run; solver-free",
        "input_signature": expected_input_signature,
        "model_signature": recalculated_model_signature,
        "seed_pool_signature": recalculated_seed_pool_signature,
        "seed_mode": manifest.get("seed_mode"),
        "seed_count": len(seeds),
        "positive_demand_count": len(demands),
        "dynamic_node_count": len(dynamic_nodes),
        "dynamic_arc_count": len(dynamic_arcs),
        "final_pool_count": len(final_pool),
        "final_solution_count": len(final_solution),
        "zero_flow_column_count": zero_count,
        "recomputed_objective": recomputed_objective,
        "reference_objective": reference_objective,
        "reported_cg_objective": reported_objective,
        "reported_cg_objective_matches_recomputed": reported_matches_recomputed,
        "reported_cg_objective_matches_reference": reported_matches_reference,
        "recomputed_objective_matches_reference": recomputed_matches_reference,
        "reference_match": reported_matches_reference,
        "reference_match_basis": "reported_cg_objective_vs_same_model_reference_lp",
        "objective_optimality_certificate_source": "reference_lp"
        if reference_lp_valid and recomputed_matches_reference
        else None,
        "final_rmp_primal_and_export_checks": core.get("status") == "PASS",
        "independent_pricing_certificate_present": independent_pricing_certificate_present,
        "pricing_closure_claim": independent_pricing_certificate_present,
        "pricing_closure_proven": independent_pricing_certificate_present,
        "pricing_closure_reason": pricing_closure_reason,
        "pricing_stop_reason": stop_reason,
        "duals_cover": "final successfully solved RMP rows and variable bounds; not a separate proof of complete path pricing",
        "optimization_invocations_during_verify": 0,
    }
