"""General Phase-I pricing oracle prototype.

This module builds a time-expanded graph from the controlled benchmark dynamic
network and searches for Phase-I real-column candidates with a reduced-cost
style entry signal. It is a prototype: it is benchmark-runner scoped and
auditable, but it is not a production full-CG pricing oracle.
"""

from __future__ import annotations

import argparse
import csv
import heapq
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from build_sioux_harder_bounded_stage2 import ROOT_DIR
from phase1_artificial_rmp_preflight import TRUE_COST_TIE_BREAKER_EPSILON, run_preflight, sha256_file
from phase1_pricing_candidate_diagnostic import (
    capacity_dual_maps,
    demand_dual_map,
    evaluate_candidates,
    structural_validation,
    validated_signs,
)
from precheck_second_controlled_benchmark_current_pool_rmp import (
    DEFAULT_CONFIG as DEFAULT_CURRENT_POOL_CONFIG,
    TOL,
    input_data_dir,
    load_config,
    parse_float,
    read_csv,
    split_sequence,
)


DEFAULT_OUTPUT_DIR = ROOT_DIR / "outputs" / "phase_i_general_pricing_oracle_gate"
ORACLE_ID = "general_phase_i_reduced_cost_time_expanded_pricing_oracle_prototype"
SUPPORTED_BENCHMARK = "second_controlled_benchmark_link55"
SMOKE_ADAPTER_ID = "general_phase_i_oracle_smoke_adapter"
BOUNDED_REFERENCE_CANDIDATES = (
    ROOT_DIR / "outputs" / "phase_i_candidate_generation_and_true_fresh_v3_attempt" / "generated_phase_i_candidates.csv"
)
HISTORICAL_REPAIRED_SEED = (
    ROOT_DIR / "outputs" / "second_controlled_benchmark_link55_seed_pool_repair" / "repaired_seed_columns.csv"
)
SCOPE_BOUNDARY = (
    "This is a general Phase-I reduced-cost/entry-signal pricing oracle prototype "
    "over the controlled benchmark time-expanded dynamic network. It does not "
    "read repaired_seed_columns.csv or REPAIR_SPECS operationally, does not run "
    "a large benchmark, full assignment, production-scale solve, branch-and-price, "
    "reinforcement learning, GTFS/railway instantiation, or claim full CG/global "
    "convergence or exact arc-flow reproduction."
)


@dataclass(frozen=True)
class Edge:
    arc_id: str
    from_node: str
    to_node: str
    arc_type: str
    weight: float


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_path(value: str | Path | None) -> Path | None:
    if value is None or value == "":
        return None
    path = Path(value)
    return path if path.is_absolute() else ROOT_DIR / path


def read_input_manifest(path: str | Path | None) -> dict[str, Any]:
    manifest_path = resolve_path(path)
    if manifest_path is None:
        return {}
    if not manifest_path.exists():
        raise FileNotFoundError(f"input manifest not found: {manifest_path}")
    payload = read_json(manifest_path)
    return payload.get("artifacts", payload)


def rel(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT_DIR.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def arc_lookup(arcs: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["arc_id"]: row for row in arcs}


def graph_adjacency(
    arcs: list[dict[str, str]],
    capacity_duals: dict[str, float],
    cap_sign: float,
) -> dict[str, list[Edge]]:
    adjacency: dict[str, list[Edge]] = {}
    for arc in arcs:
        arc_id = arc["arc_id"]
        cost = parse_float(arc.get("cost"), 0.0)
        raw_capacity_dual = capacity_duals.get(arc_id, 0.0)
        weight = TRUE_COST_TIE_BREAKER_EPSILON * cost + cap_sign * raw_capacity_dual
        edge = Edge(
            arc_id=arc_id,
            from_node=arc["from_node_time_id"],
            to_node=arc["to_node_time_id"],
            arc_type=arc.get("arc_type", ""),
            weight=weight,
        )
        adjacency.setdefault(edge.from_node, []).append(edge)
    for edges in adjacency.values():
        edges.sort(key=lambda edge: (edge.weight, edge.arc_id))
    return adjacency


def source_node_for_demand(demand_id: str, arcs_by_id: dict[str, dict[str, str]]) -> str | None:
    source = arcs_by_id.get(f"source_{demand_id}")
    return source.get("from_node_time_id") if source else None


def terminal_node_for_demand(demand_id: str, arcs: list[dict[str, str]]) -> str | None:
    for arc in arcs:
        if arc.get("arc_type") == "sink_connector" and arc.get("to_physical_node_id") == f"sink_{demand_id}":
            return arc.get("to_node_time_id")
    return None


def edge_allowed_for_demand(edge: Edge, demand: dict[str, str], arcs_by_id: dict[str, dict[str, str]]) -> bool:
    arc = arcs_by_id[edge.arc_id]
    demand_id = demand["demand_id"]
    if edge.arc_type == "source_connector":
        return edge.arc_id == f"source_{demand_id}"
    if edge.arc_type == "sink_connector":
        return (
            arc.get("to_physical_node_id") == f"sink_{demand_id}"
            and arc.get("from_physical_node_id") == str(demand["destination_node_id"])
        )
    return True


def enumerate_k_shortest_paths(
    demand: dict[str, str],
    arcs: list[dict[str, str]],
    adjacency: dict[str, list[Edge]],
    max_candidates: int,
    expansion_limit: int = 50000,
) -> tuple[list[list[str]], dict[str, Any]]:
    arcs_by_id = arc_lookup(arcs)
    start = source_node_for_demand(demand["demand_id"], arcs_by_id)
    terminal = terminal_node_for_demand(demand["demand_id"], arcs)
    if not start or not terminal:
        return [], {
            "demand_id": demand["demand_id"],
            "start_node_time_id": start,
            "terminal_node_time_id": terminal,
            "paths_found": 0,
            "states_expanded": 0,
            "blocker": "missing source or terminal node",
        }

    heap: list[tuple[float, int, str, tuple[str, ...]]] = [(0.0, 0, start, tuple())]
    sequence = 0
    expansions = 0
    paths: list[list[str]] = []
    signatures: set[tuple[str, ...]] = set()
    arrivals_per_node: dict[str, int] = {}

    while heap and len(paths) < max_candidates and expansions < expansion_limit:
        weight, _, node, path = heapq.heappop(heap)
        expansions += 1
        if node == terminal and path:
            if path not in signatures:
                signatures.add(path)
                paths.append(list(path))
            continue
        arrivals_per_node[node] = arrivals_per_node.get(node, 0) + 1
        if arrivals_per_node[node] > max(50, max_candidates * 4):
            continue
        for edge in adjacency.get(node, []):
            if edge.arc_id in path:
                continue
            if not edge_allowed_for_demand(edge, demand, arcs_by_id):
                continue
            if edge.arc_type == "source_connector" and path:
                continue
            if any(arcs_by_id[arc_id].get("arc_type") == "sink_connector" for arc_id in path):
                continue
            sequence += 1
            heapq.heappush(heap, (weight + edge.weight, sequence, edge.to_node, (*path, edge.arc_id)))

    return paths, {
        "demand_id": demand["demand_id"],
        "start_node_time_id": start,
        "terminal_node_time_id": terminal,
        "paths_found": len(paths),
        "states_expanded": expansions,
        "expansion_limit": expansion_limit,
        "blocker": "" if paths else "no path found",
    }


def generalized_cost(arc_ids: list[str], arcs_by_id: dict[str, dict[str, str]]) -> float:
    return sum(parse_float(arcs_by_id[arc_id].get("cost"), 0.0) for arc_id in arc_ids if arc_id in arcs_by_id)


def path_times(arc_ids: list[str], arcs_by_id: dict[str, dict[str, str]]) -> tuple[float, float]:
    if not arc_ids:
        return math.nan, math.nan
    first = arcs_by_id[arc_ids[0]]
    sink = arcs_by_id[arc_ids[-1]]
    return parse_float(first.get("from_time"), math.nan), parse_float(sink.get("from_time"), math.nan)


def node_sequence(arc_ids: list[str], arcs_by_id: dict[str, dict[str, str]]) -> str:
    nodes: list[str] = []
    for arc_id in arc_ids:
        arc = arcs_by_id[arc_id]
        if arc.get("arc_type") == "source_connector":
            target = arc.get("to_physical_node_id", "")
            if target and (not nodes or nodes[-1] != target):
                nodes.append(target)
            continue
        if arc.get("arc_type") == "sink_connector":
            continue
        if not nodes and arc.get("from_physical_node_id"):
            nodes.append(arc["from_physical_node_id"])
        target = arc.get("to_physical_node_id", "")
        if target and (not nodes or nodes[-1] != target):
            nodes.append(target)
    return "|".join(nodes)


def link_sequence(arc_ids: list[str], arcs_by_id: dict[str, dict[str, str]]) -> str:
    return "|".join(
        arcs_by_id[arc_id].get("physical_link_id", "")
        for arc_id in arc_ids
        if arcs_by_id[arc_id].get("arc_type") == "movement"
    )


def time_sequence(arc_ids: list[str], arcs_by_id: dict[str, dict[str, str]]) -> str:
    times: list[str] = []
    for arc_id in arc_ids:
        arc = arcs_by_id[arc_id]
        if arc.get("arc_type") == "source_connector":
            times.append(str(int(parse_float(arc.get("to_time"), 0.0))))
        elif arc.get("arc_type") == "movement":
            times.append(str(int(parse_float(arc.get("from_time"), 0.0))))
        elif arc.get("arc_type") == "sink_connector":
            times.append(str(int(parse_float(arc.get("from_time"), 0.0))))
    compact: list[str] = []
    for value in times:
        if not compact or compact[-1] != value:
            compact.append(value)
    return "|".join(compact)


def candidate_rows_from_paths(
    paths_by_demand: dict[str, list[list[str]]],
    demands: list[dict[str, str]],
    arcs_by_id: dict[str, dict[str, str]],
    oracle_id: str = ORACLE_ID,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    demand_by_id = {row["demand_id"]: row for row in demands}
    for demand_id, paths in paths_by_demand.items():
        demand = demand_by_id[demand_id]
        for index, arc_ids in enumerate(paths, start=1):
            departure, arrival = path_times(arc_ids, arcs_by_id)
            rows.append(
                {
                    "column_id": f"GEN_{demand_id}_{index:03d}",
                    "path_id": f"GEN_{demand_id}_{index:03d}",
                    "demand_id": demand_id,
                    "origin_node_id": demand["origin_node_id"],
                    "destination_node_id": demand["destination_node_id"],
                    "departure_time": departure,
                    "arrival_time": arrival,
                    "travel_time": arrival - departure if math.isfinite(arrival) and math.isfinite(departure) else "",
                    "generalized_cost": generalized_cost(arc_ids, arcs_by_id),
                    "node_sequence": node_sequence(arc_ids, arcs_by_id),
                    "link_sequence": link_sequence(arc_ids, arcs_by_id),
                    "time_sequence": time_sequence(arc_ids, arcs_by_id),
                    "arc_sequence": "|".join(arc_ids),
                    "column_source": oracle_id,
                    "candidate_generation_method": oracle_id,
                    "repair_reason": "",
                    "derived_from": "time_expanded_shortest_path_search",
                }
            )
    return rows


def cost_audit_rows(rows: list[dict[str, Any]], arcs_by_id: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    audit: list[dict[str, Any]] = []
    for row in rows:
        arc_ids = split_sequence(str(row.get("arc_sequence", "")))
        reconstructed = generalized_cost(arc_ids, arcs_by_id)
        listed = parse_float(row.get("generalized_cost"), math.nan)
        audit.append(
            {
                "candidate_id": row.get("column_id", ""),
                "demand_id": row.get("demand_id", ""),
                "listed_generalized_cost": listed,
                "reconstructed_generalized_cost": reconstructed,
                "absolute_difference": abs(listed - reconstructed) if math.isfinite(listed) else "",
                "status": "PASS" if math.isfinite(listed) and abs(listed - reconstructed) <= TOL else "FAIL",
            }
        )
    return audit


def path_validity_rows(
    rows: list[dict[str, Any]],
    demands: list[dict[str, str]],
    arcs_by_id: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    demand_ids = {row["demand_id"] for row in demands}
    output: list[dict[str, Any]] = []
    for row in rows:
        valid, reason = structural_validation({key: str(value) for key, value in row.items()}, demand_ids, arcs_by_id)
        arc_ids = split_sequence(str(row.get("arc_sequence", "")))
        output.append(
            {
                "candidate_id": row.get("column_id", ""),
                "demand_id": row.get("demand_id", ""),
                "structurally_valid": bool_text(valid),
                "invalid_reason": reason,
                "uses_waiting_arc": bool_text(any(arcs_by_id[arc].get("arc_type") == "waiting" for arc in arc_ids)),
                "movement_link_sequence": link_sequence(arc_ids, arcs_by_id),
                "arc_sequence": row.get("arc_sequence", ""),
            }
        )
    return output


def duplicate_rows(score_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": row.get("candidate_id", ""),
            "demand_id": row.get("demand_id", ""),
            "canonical_path_signature": row.get("arc_sequence", ""),
            "duplicate_existing_phase1_column": row.get("duplicate_existing_phase1_column", ""),
            "duplicate_of_column_id": row.get("duplicate_of_column_id", ""),
            "classification": row.get("classification", ""),
        }
        for row in score_rows
    ]


def compare_with_bounded(
    output_dir: Path,
    general_rows: list[dict[str, Any]],
    score_rows: list[dict[str, Any]],
    bounded_reference_candidates: Path = BOUNDED_REFERENCE_CANDIDATES,
) -> dict[str, Any]:
    bounded_rows = read_csv(bounded_reference_candidates) if bounded_reference_candidates.exists() else []
    bounded_signatures = {row.get("arc_sequence", ""): row for row in bounded_rows}
    general_score_by_id = {row.get("candidate_id", ""): row for row in score_rows}
    comparison_rows: list[dict[str, Any]] = []
    for row in general_rows:
        signature = row.get("arc_sequence", "")
        bounded = bounded_signatures.get(signature)
        score = general_score_by_id.get(row.get("column_id", ""), {})
        comparison_rows.append(
            {
                "general_candidate_id": row.get("column_id", ""),
                "demand_id": row.get("demand_id", ""),
                "arc_sequence": signature,
                "classification": score.get("classification", ""),
                "phase1_entry_signal": score.get("phase1_entry_signal", ""),
                "overlaps_bounded_generator_signature": bool_text(bounded is not None),
                "bounded_candidate_id": bounded.get("column_id", "") if bounded else "",
            }
        )
    write_csv(
        output_dir / "general_vs_bounded_phase_i_candidate_comparison.csv",
        comparison_rows,
        [
            "general_candidate_id",
            "demand_id",
            "arc_sequence",
            "classification",
            "phase1_entry_signal",
            "overlaps_bounded_generator_signature",
            "bounded_candidate_id",
        ],
    )
    improving = [row for row in score_rows if row.get("classification") == "improving_new_candidate"]
    path_rows = path_validity_rows(general_rows, [], {}) if False else []
    d3_waiting = any(
        row.get("demand_id") == "D3" and "wait_" in row.get("arc_sequence", "")
        for row in general_rows
    )
    d4_waiting_or_alt = any(
        row.get("demand_id") == "D4"
        and ("wait_" in row.get("arc_sequence", "") or row.get("arc_sequence", "") not in bounded_signatures)
        for row in general_rows
    )
    overlap_count = sum(row["overlaps_bounded_generator_signature"] == "true" for row in comparison_rows)
    summary = {
        "comparison_status": "PASS",
        "bounded_reference_path": rel(bounded_reference_candidates),
        "bounded_reference_used_operationally": False,
        "general_candidate_count": len(general_rows),
        "general_improving_nonduplicate_count": len(improving),
        "d3_waiting_time_shift_behavior_present": d3_waiting,
        "d4_waiting_or_alternate_behavior_present": d4_waiting_or_alt,
        "overlap_with_bounded_generator_signature_count": overlap_count,
        "overlap_with_bounded_generator_signature_fraction": overlap_count / len(general_rows) if general_rows else 0.0,
        "likely_to_clear_artificial_flow": bool(improving),
    }
    write_json(output_dir / "general_oracle_recovery_summary.json", summary)
    lines = [
        "# General vs Bounded Phase-I Candidate Comparison",
        "",
        "The bounded generator is used here only as a reference comparison, not as an operational input.",
        "",
        f"- General candidates: {summary['general_candidate_count']}",
        f"- Improving non-duplicates: {summary['general_improving_nonduplicate_count']}",
        f"- D3 waiting/time-shift behavior present: {summary['d3_waiting_time_shift_behavior_present']}",
        f"- D4 waiting/alternate behavior present: {summary['d4_waiting_or_alternate_behavior_present']}",
        f"- Overlapping bounded signatures: {summary['overlap_with_bounded_generator_signature_count']}",
        f"- Likely to clear artificial flow: {summary['likely_to_clear_artificial_flow']}",
    ]
    (output_dir / "general_vs_bounded_phase_i_candidate_comparison.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    return summary


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Phase-I General Pricing Oracle Prototype Report",
        "",
        SCOPE_BOUNDARY,
        "",
        f"- Oracle status: {summary['oracle_status']}",
        f"- Oracle type: {summary['oracle_type']}",
        f"- Benchmark: {summary['benchmark']}",
        f"- General candidate count: {summary['general_candidate_count']}",
        f"- Structurally valid candidates: {summary['structurally_valid_candidate_count']}",
        f"- Improving non-duplicate candidates: {summary['improving_nonduplicate_candidate_count']}",
        f"- Waiting-arc candidates: {summary['waiting_arc_candidate_count']}",
        f"- Demands with generated candidates: {', '.join(summary['demand_ids_with_generated_candidates'])}",
        f"- D3 waiting/time-shift behavior present: {summary['d3_waiting_time_shift_behavior_present']}",
        f"- D4 waiting/alternate behavior present: {summary['d4_waiting_or_alternate_behavior_present']}",
        f"- repaired_seed_columns.csv operational use: {summary['repaired_seed_columns_used_operationally']}",
        f"- REPAIR_SPECS operational use: {summary['repair_specs_used_operationally']}",
        f"- Baseline dynamic_columns.csv mutated: {summary['baseline_dynamic_columns_mutated']}",
        "",
        "## Prototype Boundary",
        "",
        "The oracle constructs paths from the dynamic network graph and scores them against an in-run Phase-I dual solution. "
        "It is still a prototype because it uses bounded k-shortest enumeration, controlled-benchmark input conventions, "
        "and review-scale stopping limits.",
    ]
    if summary.get("safe_blockers"):
        lines.extend(["", "## Safe Blockers", ""])
        lines.extend(f"- {item}" for item in summary["safe_blockers"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_oracle(
    output_dir: Path,
    benchmark_id: str,
    phase1_dual_solution: Path,
    candidate_pool: Path,
    max_candidates_per_demand: int,
    config_path: str | Path = DEFAULT_CURRENT_POOL_CONFIG,
    dynamic_data_dir: Path | None = None,
    dynamic_arc_file: Path | None = None,
    dynamic_demand_file: Path | None = None,
    phase1_preflight_summary: Path | None = None,
    baseline_dynamic_columns: Path | None = None,
    bounded_reference_candidates: Path | None = BOUNDED_REFERENCE_CANDIDATES,
    require_improving_candidate: bool = True,
    oracle_id: str = ORACLE_ID,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    blockers: list[str] = []
    if dynamic_data_dir is None:
        config = load_config(config_path)
        data_dir = input_data_dir(config)
    else:
        config = None
        data_dir = dynamic_data_dir
    if not data_dir.exists():
        blockers.append(f"missing dynamic data dir: {rel(data_dir)}")
    baseline_path = baseline_dynamic_columns or data_dir / "dynamic_columns.csv"
    if not baseline_path.exists():
        blockers.append(f"missing baseline dynamic_columns.csv: {rel(baseline_path)}")
    baseline_hash_before = sha256_file(baseline_path) if baseline_path.exists() else ""
    if not phase1_dual_solution.exists():
        blockers.append(f"missing Phase-I dual solution: {rel(phase1_dual_solution)}")
        dual_solution: dict[str, Any] = {}
        convention_name, eq_sign, cap_sign = "", math.nan, math.nan
    else:
        dual_solution = read_json(phase1_dual_solution)
        convention_name, eq_sign, cap_sign, sign_blockers = validated_signs(dual_solution)
        blockers.extend(sign_blockers)
    if not candidate_pool.exists():
        blockers.append(f"missing candidate pool: {rel(candidate_pool)}")
        candidate_pool_rows: list[dict[str, str]] = []
    else:
        candidate_pool_rows = read_csv(candidate_pool)

    arc_path = dynamic_arc_file or data_dir / "dynamic_arc.csv"
    demand_path = dynamic_demand_file or data_dir / "dynamic_demand.csv"
    arcs = read_csv(arc_path) if arc_path.exists() else []
    demands = read_csv(demand_path) if demand_path.exists() else []
    if not arcs:
        blockers.append(f"missing or empty dynamic arc file: {rel(arc_path)}")
    if not demands:
        blockers.append(f"missing or empty dynamic demand file: {rel(demand_path)}")
    if phase1_preflight_summary is not None:
        preflight = read_json(phase1_preflight_summary)
    elif config is not None:
        preflight = run_preflight(config_path, output_dir / "nested_phase1_artificial_rmp_preflight")
    else:
        preflight = {
            "preflight_status": "NOT_RUN",
            "artificial_flow_by_demand": {},
            "total_artificial_flow": None,
        }
    capacity_duals, _ = capacity_dual_maps(dual_solution)
    adjacency = graph_adjacency(arcs, capacity_duals, cap_sign)
    arcs_by_id = arc_lookup(arcs)

    paths_by_demand: dict[str, list[list[str]]] = {}
    graph_demand_audit: list[dict[str, Any]] = []
    if not blockers:
        for demand in demands:
            paths, audit = enumerate_k_shortest_paths(
                demand,
                arcs,
                adjacency,
                max_candidates=max_candidates_per_demand,
            )
            paths_by_demand[demand["demand_id"]] = paths
            graph_demand_audit.append(audit)
            if not paths:
                blockers.append(f"no candidate path found for demand {demand['demand_id']}")

    general_rows = candidate_rows_from_paths(paths_by_demand, demands, arcs_by_id, oracle_id) if not blockers else []
    score_rows: list[dict[str, Any]]
    if blockers:
        score_rows = []
    else:
        score_rows, _ = evaluate_candidates(
            general_rows,
            candidate_pool_rows,
            demands,
            arcs,
            preflight,
            dual_solution,
            convention_name,
            eq_sign,
            cap_sign,
        )
    path_rows = path_validity_rows(general_rows, demands, arcs_by_id)
    cost_rows = cost_audit_rows(general_rows, arcs_by_id)
    dup_rows = duplicate_rows(score_rows)
    improving = [row for row in score_rows if row.get("classification") == "improving_new_candidate"]
    valid_count = sum(row.get("structurally_valid") == "true" for row in path_rows)
    d3_wait = any(row.get("demand_id") == "D3" and row.get("uses_waiting_arc") == "true" for row in path_rows)
    d4_wait_or_alt = any(
        row.get("demand_id") == "D4"
        and (row.get("uses_waiting_arc") == "true" or row.get("classification") == "improving_new_candidate")
        for row in score_rows
    )
    if not blockers and require_improving_candidate and not improving:
        blockers.append("general oracle produced no improving non-duplicate Phase-I candidate")

    baseline_hash_after = sha256_file(baseline_path) if baseline_path.exists() else ""
    if baseline_hash_before != baseline_hash_after:
        blockers.append("baseline dynamic_columns.csv hash changed during general oracle run")

    candidate_fields = [
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
        "column_source",
        "candidate_generation_method",
        "repair_reason",
        "derived_from",
    ]
    write_csv(output_dir / "phase_i_general_oracle_candidates.csv", general_rows, candidate_fields)
    write_csv(
        output_dir / "phase_i_general_oracle_candidate_scores.csv",
        score_rows,
        list(score_rows[0].keys()) if score_rows else ["candidate_id", "demand_id", "classification"],
    )
    write_csv(
        output_dir / "phase_i_general_oracle_path_validity_audit.csv",
        path_rows,
        [
            "candidate_id",
            "demand_id",
            "structurally_valid",
            "invalid_reason",
            "uses_waiting_arc",
            "movement_link_sequence",
            "arc_sequence",
        ],
    )
    write_csv(
        output_dir / "phase_i_general_oracle_duplicate_audit.csv",
        dup_rows,
        [
            "candidate_id",
            "demand_id",
            "canonical_path_signature",
            "duplicate_existing_phase1_column",
            "duplicate_of_column_id",
            "classification",
        ],
    )
    write_csv(
        output_dir / "phase_i_general_oracle_cost_reconstruction_audit.csv",
        cost_rows,
        [
            "candidate_id",
            "demand_id",
            "listed_generalized_cost",
            "reconstructed_generalized_cost",
            "absolute_difference",
            "status",
        ],
    )
    graph_audit = {
        "graph_status": "PASS" if graph_demand_audit and not [row for row in graph_demand_audit if row["blocker"]] else "SAFE_BLOCKED",
        "node_count": len({arc["from_node_time_id"] for arc in arcs} | {arc["to_node_time_id"] for arc in arcs}),
        "arc_count": len(arcs),
        "movement_arc_count": sum(arc.get("arc_type") == "movement" for arc in arcs),
        "waiting_arc_count": sum(arc.get("arc_type") == "waiting" for arc in arcs),
        "source_connector_count": sum(arc.get("arc_type") == "source_connector" for arc in arcs),
        "sink_connector_count": sum(arc.get("arc_type") == "sink_connector" for arc in arcs),
        "demands": graph_demand_audit,
        "edge_weight_formula": "TRUE_COST_TIE_BREAKER_EPSILON * arc_cost + validated_capacity_sign * capacity_dual_raw",
        "oracle_id": oracle_id,
        "benchmark_id": benchmark_id,
        "dynamic_data_dir": rel(data_dir),
        "dynamic_arc_file": rel(arc_path),
        "dynamic_demand_file": rel(demand_path),
    }
    write_json(output_dir / "phase_i_general_oracle_graph_audit.json", graph_audit)
    bounded_comparison_applicable = (
        general_rows
        and benchmark_id == SUPPORTED_BENCHMARK
        and bounded_reference_candidates is not None
    )
    comparison = compare_with_bounded(
        output_dir,
        general_rows,
        score_rows,
        bounded_reference_candidates,
    ) if bounded_comparison_applicable else {
        "comparison_status": "SAFE_BLOCKED",
        "bounded_reference_used_operationally": False,
        "comparison_reason": "bounded link55 reference comparison is not applicable for this benchmark",
    }

    status = "PASS" if not blockers else "SAFE_BLOCKED"
    waiting_candidate_count = sum(row.get("uses_waiting_arc") == "true" for row in path_rows)
    demand_ids_with_generated_candidates = sorted({str(row.get("demand_id", "")) for row in general_rows})
    demand_ids_with_improving_candidates = sorted({str(row.get("demand_id", "")) for row in improving})
    demand_ids_with_waiting_candidates = sorted(
        {str(row.get("demand_id", "")) for row in path_rows if row.get("uses_waiting_arc") == "true"}
    )
    summary = {
        "oracle_status": status,
        "oracle_type": oracle_id,
        "benchmark": benchmark_id,
        "dynamic_data_dir": rel(data_dir),
        "dynamic_arc_file": rel(arc_path),
        "dynamic_demand_file": rel(demand_path),
        "candidate_source_path": rel(output_dir / "phase_i_general_oracle_candidates.csv"),
        "general_candidate_count": len(general_rows),
        "structurally_valid_candidate_count": valid_count,
        "duplicate_candidate_count": sum(row.get("duplicate_existing_phase1_column") == "true" for row in score_rows),
        "improving_nonduplicate_candidate_count": len(improving),
        "improving_nonduplicate_candidate_ids": [row.get("candidate_id") for row in improving],
        "waiting_arc_candidate_count": waiting_candidate_count,
        "demand_ids_with_generated_candidates": demand_ids_with_generated_candidates,
        "demand_ids_with_improving_candidates": demand_ids_with_improving_candidates,
        "demand_ids_with_waiting_candidates": demand_ids_with_waiting_candidates,
        "hardcoded_d3_d4_requirement_for_success": False,
        "hardcoded_link55_or_link48_requirement_for_success": False,
        "d3_waiting_time_shift_behavior_present": d3_wait,
        "d4_waiting_or_alternate_behavior_present": d4_wait_or_alt,
        "phase1_dual_solution_path": rel(phase1_dual_solution),
        "candidate_pool_path": rel(candidate_pool),
        "validated_stationarity_convention": convention_name,
        "validated_eq_sign": eq_sign,
        "validated_capacity_sign": cap_sign,
        "repaired_seed_columns_used_operationally": False,
        "repair_specs_used_operationally": False,
        "bounded_generator_candidates_used_operationally": False,
        "bounded_generator_reference_comparison_used": bool(bounded_comparison_applicable),
        "bounded_generator_reference_path": rel(bounded_reference_candidates)
        if bounded_reference_candidates is not None
        else "",
        "bounded_generator_reference_comparison_applicable": bool(bounded_comparison_applicable),
        "baseline_dynamic_columns_mutated": baseline_hash_before != baseline_hash_after,
        "safe_blockers": blockers,
        "full_assignment_run": False,
        "full_cg_run": False,
        "general_convergence_claimed": False,
        "production_scale_claimed": False,
        "exact_arc_flow_reproduction_claimed": False,
        "scope": SCOPE_BOUNDARY,
        "comparison": comparison,
    }
    write_json(output_dir / "phase_i_general_pricing_oracle_summary.json", summary)
    write_report(output_dir / "phase_i_general_pricing_oracle_report.md", summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Phase-I general pricing oracle prototype.")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--benchmark-id", default=SUPPORTED_BENCHMARK)
    parser.add_argument("--input-manifest", default=None)
    parser.add_argument("--dynamic-data-dir", default=None)
    parser.add_argument("--phase1-preflight-summary", default=None)
    parser.add_argument("--baseline-dynamic-columns", default=None)
    parser.add_argument("--phase1-dual-solution", required=False)
    parser.add_argument("--candidate-pool", required=False)
    parser.add_argument("--max-candidates-per-demand", type=int, default=40)
    parser.add_argument("--allow-no-improving-candidates", action="store_true")
    parser.add_argument("--oracle-id", default=ORACLE_ID)
    parser.add_argument("--no-mutate-accepted-outputs", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = read_input_manifest(args.input_manifest)
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = ROOT_DIR / output_dir
    benchmark_id = str(manifest.get("benchmark_id") or args.benchmark_id)
    dual_value = args.phase1_dual_solution or manifest.get("phase1_dual_solution")
    candidate_value = args.candidate_pool or manifest.get("candidate_pool")
    if not dual_value:
        print("Missing --phase1-dual-solution or manifest phase1_dual_solution")
        return 1
    if not candidate_value:
        print("Missing --candidate-pool or manifest candidate_pool")
        return 1
    dual_path = Path(dual_value)
    if not dual_path.is_absolute():
        dual_path = ROOT_DIR / dual_path
    candidate_pool = Path(candidate_value)
    if not candidate_pool.is_absolute():
        candidate_pool = ROOT_DIR / candidate_pool
    dynamic_data_dir = resolve_path(args.dynamic_data_dir or manifest.get("dynamic_data_dir"))
    dynamic_arc_file = resolve_path(manifest.get("dynamic_arc_file"))
    dynamic_demand_file = resolve_path(manifest.get("demand_file") or manifest.get("dynamic_demand_file"))
    phase1_preflight_summary = resolve_path(args.phase1_preflight_summary or manifest.get("phase1_preflight_summary"))
    baseline_dynamic_columns = resolve_path(args.baseline_dynamic_columns or manifest.get("baseline_dynamic_columns"))
    max_candidates = int(manifest.get("max_candidates_per_demand") or args.max_candidates_per_demand)
    require_improving = not args.allow_no_improving_candidates and bool(
        manifest.get("require_improving_candidate", True)
    )
    summary = run_oracle(
        output_dir=output_dir,
        benchmark_id=benchmark_id,
        phase1_dual_solution=dual_path,
        candidate_pool=candidate_pool,
        max_candidates_per_demand=max(1, max_candidates),
        dynamic_data_dir=dynamic_data_dir,
        dynamic_arc_file=dynamic_arc_file,
        dynamic_demand_file=dynamic_demand_file,
        phase1_preflight_summary=phase1_preflight_summary,
        baseline_dynamic_columns=baseline_dynamic_columns,
        bounded_reference_candidates=BOUNDED_REFERENCE_CANDIDATES if benchmark_id == SUPPORTED_BENCHMARK else None,
        require_improving_candidate=require_improving,
        oracle_id=str(manifest.get("oracle_id") or args.oracle_id),
    )
    print(f"Phase-I general pricing oracle status: {summary['oracle_status']}")
    print(f"General candidates: {summary['general_candidate_count']}")
    print(f"Improving non-duplicates: {summary['improving_nonduplicate_candidate_count']}")
    print(f"repaired_seed_columns.csv operational use: {summary['repaired_seed_columns_used_operationally']}")
    print(f"REPAIR_SPECS operational use: {summary['repair_specs_used_operationally']}")
    print(f"Report: {output_dir / 'phase_i_general_pricing_oracle_report.md'}")
    return 0 if summary["oracle_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
