"""Exact, deterministic k-shortest pricing on an audited time-expanded DAG.

Only current graph arcs and current Phase-I duals enter this module.  The
topological audit is independent of edge weights, so negative dual-adjusted
weights are supported.  The extra labels allow existing pool paths to be
skipped without losing the first new path.
"""

from __future__ import annotations

import heapq
import math
from collections import defaultdict
from typing import Any


def audit_dag(arcs: list[dict[str, str]]) -> tuple[list[str], dict[str, Any]]:
    """Return a stable topological order or raise on a cycle/time reversal."""
    outgoing: dict[str, list[str]] = defaultdict(list)
    indegree: dict[str, int] = defaultdict(int)
    seen_ids: set[str] = set()
    for arc in arcs:
        arc_id = arc["arc_id"]
        if arc_id in seen_ids:
            raise ValueError(f"duplicate dynamic arc id: {arc_id}")
        seen_ids.add(arc_id)
        u, v = arc["from_node_time_id"], arc["to_node_time_id"]
        if not u or not v:
            raise ValueError(f"empty endpoint: {arc_id}")
        try:
            start, end = float(arc["from_time"]), float(arc["to_time"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"invalid arc time: {arc_id}") from exc
        if not math.isfinite(start) or not math.isfinite(end) or end < start:
            raise ValueError(f"time-reversing or nonfinite arc: {arc_id}")
        outgoing[u].append(v)
        indegree.setdefault(u, 0)
        indegree[v] += 1
    queue = [node for node, count in indegree.items() if count == 0]
    heapq.heapify(queue)
    order: list[str] = []
    while queue:
        node = heapq.heappop(queue)
        order.append(node)
        for next_node in outgoing.get(node, []):
            indegree[next_node] -= 1
            if indegree[next_node] == 0:
                heapq.heappush(queue, next_node)
    if len(order) != len(indegree):
        raise ValueError(f"pricing graph is not a DAG: {len(indegree) - len(order)} cyclic nodes")
    return order, {"dag_audit": "PASS", "node_count": len(order), "arc_count": len(arcs)}


def validate_duals(
    arcs: list[dict[str, str]],
    demands: list[dict[str, str]],
    dual_solution: dict[str, Any],
    cap_sign: float,
    eq_sign: float,
) -> tuple[dict[str, float], dict[str, float]]:
    if not math.isfinite(cap_sign) or not math.isfinite(eq_sign):
        raise ValueError("invalid dual sign convention")
    raw_caps = dual_solution.get("capacity_duals_by_dynamic_arc")
    raw_eqs = dual_solution.get("equality_duals_by_demand_constraint")
    if not isinstance(raw_caps, dict) or not isinstance(raw_eqs, dict):
        raise ValueError("missing capacity or equality dual map")
    caps: dict[str, float] = {}
    eqs: dict[str, float] = {}
    for arc in arcs:
        arc_id = arc["arc_id"]
        payload = raw_caps.get(arc_id)
        if not isinstance(payload, dict) or "raw_marginal" not in payload:
            raise ValueError(f"missing capacity dual: {arc_id}")
        try:
            value = float(payload["raw_marginal"])
            cost = float(arc["cost"])
        except (TypeError, ValueError, KeyError) as exc:
            raise ValueError(f"invalid capacity dual or cost: {arc_id}") from exc
        if not math.isfinite(value) or not math.isfinite(cost):
            raise ValueError(f"nonfinite capacity dual or cost: {arc_id}")
        caps[arc_id] = value
    for demand in demands:
        demand_id = demand["demand_id"]
        payload = raw_eqs.get(demand_id)
        if not isinstance(payload, dict) or "raw_marginal" not in payload:
            raise ValueError(f"missing equality dual: {demand_id}")
        try:
            value = float(payload["raw_marginal"])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"invalid equality dual: {demand_id}") from exc
        if not math.isfinite(value):
            raise ValueError(f"nonfinite equality dual: {demand_id}")
        eqs[demand_id] = value
    return caps, eqs


def validate_path(path: tuple[str, ...] | list[str], demand: dict[str, str], by_id: dict[str, dict[str, str]]) -> None:
    demand_id = demand["demand_id"]
    if not path or path[0] != f"source_{demand_id}":
        raise ValueError(f"wrong source for {demand_id}")
    if len(path) != len(set(path)):
        raise ValueError(f"repeated arc for {demand_id}")
    if path[-1] not in by_id:
        raise ValueError(f"missing arc {path[-1]}")
    last = by_id[path[-1]]
    if last.get("arc_type") != "sink_connector" or last.get("to_physical_node_id") != f"sink_{demand_id}":
        raise ValueError(f"wrong sink for {demand_id}")
    if last.get("from_physical_node_id") != str(demand["destination_node_id"]):
        raise ValueError(f"wrong destination for {demand_id}")
    for index, arc_id in enumerate(path):
        if arc_id not in by_id:
            raise ValueError(f"missing arc {arc_id}")
        arc = by_id[arc_id]
        kind = arc.get("arc_type")
        if kind == "source_connector" and index != 0:
            raise ValueError(f"source connector misuse for {demand_id}")
        if kind == "sink_connector" and index != len(path) - 1:
            raise ValueError(f"sink connector misuse for {demand_id}")
        if float(arc["to_time"]) < float(arc["from_time"]):
            raise ValueError(f"time reversal at {arc_id}")
        if index:
            previous = by_id[path[index - 1]]
            if previous["to_node_time_id"] != arc["from_node_time_id"]:
                raise ValueError(f"discontinuous path at {arc_id}")
            if float(arc["from_time"]) < float(previous["to_time"]):
                raise ValueError(f"time reversal between arcs at {arc_id}")


def shortest_new_paths(
    demand: dict[str, str],
    arcs: list[dict[str, str]],
    adjacency: dict[str, list[Any]],
    order: list[str],
    capacity_duals: dict[str, float],
    equality_dual: float,
    cap_sign: float,
    eq_sign: float,
    epsilon: float,
    existing: set[tuple[str, ...]],
    max_candidates: int,
) -> tuple[list[list[str]], dict[str, Any]]:
    by_id = {arc["arc_id"]: arc for arc in arcs}
    demand_id = demand["demand_id"]
    source = by_id.get(f"source_{demand_id}")
    sinks = [arc for arc in arcs if arc.get("arc_type") == "sink_connector" and arc.get("to_physical_node_id") == f"sink_{demand_id}"]
    if source is None or not sinks:
        return [], {"demand_id": demand_id, "paths_found": 0, "topological_relaxations": 0, "blocker": "missing source or terminal", "outcome": "unreachable"}
    start = source["from_node_time_id"]
    terminal = sinks[0]["to_node_time_id"]
    if any(arc["to_node_time_id"] != terminal for arc in sinks):
        raise ValueError(f"inconsistent sink nodes for {demand_id}")
    keep = max(1, max_candidates) + len(existing)
    labels: dict[str, list[tuple[float, tuple[str, ...]]]] = {start: [(0.0, ())]}
    relaxations = 0
    for node in order:
        current = labels.pop(node, []) if node != terminal else labels.get(node, [])
        if not current or node == terminal:
            continue
        for edge in adjacency.get(node, []):
            arc = by_id[edge.arc_id]
            kind = edge.arc_type
            if kind == "source_connector" and edge.arc_id != f"source_{demand_id}":
                continue
            if kind == "sink_connector" and (arc.get("to_physical_node_id") != f"sink_{demand_id}" or arc.get("from_physical_node_id") != str(demand["destination_node_id"])):
                continue
            target_labels = labels.setdefault(edge.to_node, [])
            for weight, path in current:
                target_labels.append((weight + edge.weight, (*path, edge.arc_id)))
                relaxations += 1
            target_labels.sort(key=lambda item: (item[0], item[1]))
            if len(target_labels) > keep:
                del target_labels[keep:]
    all_terminal = labels.get(terminal, [])
    selected: list[list[str]] = []
    duplicates = 0
    audits: list[dict[str, Any]] = []
    for label, path in all_terminal:
        validate_path(path, demand, by_id)
        raw_cost = sum(float(by_id[arc_id]["cost"]) for arc_id in path)
        adjusted = epsilon * raw_cost + cap_sign * sum(capacity_duals[arc_id] for arc_id in path)
        if not math.isclose(adjusted, label, rel_tol=1e-10, abs_tol=1e-8):
            raise ValueError(f"shortest-path label disagrees with direct cost for {demand_id}")
        signal = adjusted + eq_sign * equality_dual
        audits.append({"arc_sequence": "|".join(path), "shortest_path_label": label, "raw_cost": raw_cost, "dual_adjusted_cost": adjusted, "phase1_entry_signal": signal, "duplicate": path in existing})
        if path in existing:
            duplicates += 1
            continue
        selected.append(list(path))
        if len(selected) >= max_candidates:
            break
    return selected, {
        "demand_id": demand_id, "start_node_time_id": start, "terminal_node_time_id": terminal,
        "paths_found": len(selected), "topological_relaxations": relaxations,
        "duplicate_paths_skipped": duplicates, "labels_kept_per_node": keep,
        "path_cost_audits": audits, "blocker": "" if selected else "no new path found",
        "outcome": "candidate" if selected else ("duplicate" if duplicates else "unreachable"),
    }
