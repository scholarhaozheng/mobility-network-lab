"""Strict external finite-network input normalization and deterministic seeds.

The implementation is standard-library only so the RC3 private runtime needs
no pandas/NetworkX addition.  It adapts the finite K-shortest-path idea from
``extras/traffic_assignment_ampl/generate_routes_v2.py`` while fixing that
script's simple-DiGraph parallel-edge loss, integer ID coercion, implicit
zone=node assumption, default demand, silent unreachable handling, and writes
into the input directory.
"""

from __future__ import annotations

import csv
import hashlib
import heapq
import json
import math
from collections import deque
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "gmns_external_finite_network_v1"
SEED_FIELDS = [
    "column_id",
    "demand_id",
    "path_rank",
    "link_sequence",
    "node_sequence",
    "travel_time",
    "generalized_cost",
    "arrival_time",
    "seed_mode",
    "ranking_rule",
    "search_states",
    "shortage_reason",
]


class InputContractError(ValueError):
    pass


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise InputContractError(f"CSV has no header: {path}")
        return list(reader)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def signature(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _id(value: Any, field: str, *, demand: bool = False) -> str:
    text = "" if value is None else str(value)
    if not text or text != text.strip():
        raise InputContractError(f"{field} must be a nonempty string without surrounding whitespace")
    if any(char in text for char in "|;\r\n"):
        raise InputContractError(f"{field} contains a reserved path delimiter")
    if demand and "_" in text:
        raise InputContractError(f"{field} contains '_' which is unsupported by the existing demand-specific arc ID parser")
    return text


def _finite(value: Any, field: str, *, minimum: float | None = None, allow_zero: bool = True) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise InputContractError(f"{field} must be numeric; got {value!r}") from exc
    if not math.isfinite(number):
        raise InputContractError(f"{field} must be finite")
    if minimum is not None and (number < minimum or (not allow_zero and number == minimum)):
        comparator = ">" if not allow_zero else ">="
        raise InputContractError(f"{field} must be {comparator} {minimum}")
    return number


def _positive_integer(value: Any, field: str) -> int:
    number = _finite(value, field, minimum=0.0, allow_zero=False)
    if not number.is_integer():
        raise InputContractError(f"{field} must be a positive integer number of minutes; got {value!r}")
    return int(number)


def _config_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InputContractError(f"config field {field} must be an object")
    return value


def _relative_input_file(input_root: Path, raw: Any, label: str) -> Path:
    text = str(raw or "")
    candidate = Path(text)
    if not text or candidate.is_absolute() or ".." in candidate.parts:
        raise InputContractError(f"config file path {label} must be a nonempty relative path inside --input")
    resolved = (input_root / candidate).resolve()
    try:
        resolved.relative_to(input_root)
    except ValueError as exc:
        raise InputContractError(f"config file path escapes --input: {label}={text}") from exc
    if not resolved.is_file():
        raise FileNotFoundError(f"required input file missing: {resolved}")
    return resolved


def load_case_config(config_path: Path, input_root: Path) -> tuple[dict[str, Any], dict[str, Path]]:
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise InputContractError("case config must be a JSON object")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise InputContractError(f"schema_version must be {SCHEMA_VERSION}")
    files = _config_object(payload.get("files"), "files")
    paths = {
        name: _relative_input_file(input_root, files.get(name), name)
        for name in ("node", "link", "demand")
    }
    endpoint_type = payload.get("demand_endpoint_type")
    if endpoint_type not in {"node", "zone"}:
        raise InputContractError("demand_endpoint_type must be 'node' or 'zone'")
    if endpoint_type == "zone":
        paths["zone_access"] = _relative_input_file(input_root, files.get("zone_access"), "zone_access")
    _config_object(payload.get("field_mapping"), "field_mapping")
    _config_object(payload.get("model"), "model")
    _config_object(payload.get("cg"), "cg")
    _config_object(payload.get("limits"), "limits")
    return payload, paths


def _mapped(row: dict[str, Any], mapping: dict[str, Any], canonical: str, kind: str) -> Any:
    source = str(mapping.get(canonical, ""))
    if not source:
        raise InputContractError(f"field_mapping.{kind}.{canonical} is required")
    if source not in row:
        raise InputContractError(f"{kind} CSV is missing mapped column {source!r} for {canonical}")
    return row[source]


def normalize_inputs(config: dict[str, Any], paths: dict[str, Path]) -> dict[str, Any]:
    mapping = _config_object(config["field_mapping"], "field_mapping")
    node_map = _config_object(mapping.get("node"), "field_mapping.node")
    link_map = _config_object(mapping.get("link"), "field_mapping.link")
    demand_map = _config_object(mapping.get("demand"), "field_mapping.demand")
    raw_nodes = read_csv(paths["node"])
    raw_links = read_csv(paths["link"])
    raw_demands = read_csv(paths["demand"])
    nodes = [{"node_id": _id(_mapped(row, node_map, "node_id", "node"), "node_id")} for row in raw_nodes]
    node_ids = [row["node_id"] for row in nodes]
    if not nodes or len(node_ids) != len(set(node_ids)):
        raise InputContractError("node_id values must be nonempty and unique")
    node_set = set(node_ids)

    all_links: list[dict[str, Any]] = []
    link_ids: set[str] = set()
    for row in raw_links:
        link_id = _id(_mapped(row, link_map, "link_id", "link"), "link_id")
        if link_id in link_ids:
            raise InputContractError(f"duplicate link_id: {link_id}")
        link_ids.add(link_id)
        start = _id(_mapped(row, link_map, "from_node_id", "link"), f"link {link_id} from_node_id")
        end = _id(_mapped(row, link_map, "to_node_id", "link"), f"link {link_id} to_node_id")
        if start not in node_set or end not in node_set:
            raise InputContractError(f"link {link_id} references missing endpoint {start}->{end}")
        all_links.append(
            {
                "link_id": link_id,
                "from_node_id": start,
                "to_node_id": end,
                "travel_time": _positive_integer(_mapped(row, link_map, "travel_time", "link"), f"link {link_id} travel_time"),
                "cost": _finite(_mapped(row, link_map, "cost", "link"), f"link {link_id} cost", minimum=0.0),
                "capacity": _finite(
                    _mapped(row, link_map, "capacity", "link"), f"link {link_id} capacity", minimum=0.0, allow_zero=False
                ),
            }
        )
    allowed_raw = config.get("allowed_link_ids")
    if allowed_raw is None:
        links = all_links
    else:
        if not isinstance(allowed_raw, list) or not allowed_raw:
            raise InputContractError("allowed_link_ids must be a nonempty list when provided")
        allowed = [_id(item, "allowed_link_id") for item in allowed_raw]
        if len(allowed) != len(set(allowed)):
            raise InputContractError("allowed_link_ids contains duplicates")
        missing = [item for item in allowed if item not in link_ids]
        if missing:
            raise InputContractError(f"allowed_link_ids reference unknown links: {missing}")
        allowed_set = set(allowed)
        links = [row for row in all_links if row["link_id"] in allowed_set]
    if not links:
        raise InputContractError("allowed physical network has no links")

    zone_access: dict[str, str] = {}
    if config["demand_endpoint_type"] == "zone":
        zone_map = _config_object(mapping.get("zone_access"), "field_mapping.zone_access")
        for row in read_csv(paths["zone_access"]):
            zone = _id(_mapped(row, zone_map, "zone_id", "zone_access"), "zone_id")
            node = _id(_mapped(row, zone_map, "node_id", "zone_access"), f"zone {zone} node_id")
            if zone in zone_access:
                raise InputContractError(f"duplicate zone access mapping for {zone}")
            if node not in node_set:
                raise InputContractError(f"zone {zone} maps to missing node {node}")
            zone_access[zone] = node

    model = config["model"]
    declared_departure = int(_finite(model.get("departure_time"), "model.departure_time", minimum=0.0))
    if float(model.get("departure_time")) != declared_departure:
        raise InputContractError("model.departure_time must be an integer")
    demands: list[dict[str, Any]] = []
    excluded_zero: list[dict[str, Any]] = []
    seen_demands: set[str] = set()
    for row in raw_demands:
        demand_id = _id(_mapped(row, demand_map, "demand_id", "demand"), "demand_id", demand=True)
        if demand_id in seen_demands:
            raise InputContractError(f"duplicate demand_id: {demand_id}")
        seen_demands.add(demand_id)
        raw_origin = _id(_mapped(row, demand_map, "origin", "demand"), f"demand {demand_id} origin")
        raw_destination = _id(_mapped(row, demand_map, "destination", "demand"), f"demand {demand_id} destination")
        if config["demand_endpoint_type"] == "zone":
            if raw_origin not in zone_access or raw_destination not in zone_access:
                raise InputContractError(f"demand {demand_id} has an endpoint without zone_access mapping")
            origin, destination = zone_access[raw_origin], zone_access[raw_destination]
        else:
            origin, destination = raw_origin, raw_destination
        if origin not in node_set or destination not in node_set:
            raise InputContractError(f"demand {demand_id} references missing node endpoint {origin}->{destination}")
        if origin == destination:
            raise InputContractError(f"demand {demand_id} has same origin/destination; unsupported in v1")
        volume = _finite(_mapped(row, demand_map, "volume", "demand"), f"demand {demand_id} volume", minimum=0.0)
        departure_number = _finite(
            _mapped(row, demand_map, "departure_time", "demand"), f"demand {demand_id} departure_time", minimum=0.0
        )
        if not departure_number.is_integer() or int(departure_number) != declared_departure:
            raise InputContractError(f"demand {demand_id} departure_time differs from the one declared model departure")
        normalized = {
            "demand_id": demand_id,
            "origin_node_id": origin,
            "destination_node_id": destination,
            "departure_time": declared_departure,
            "volume": volume,
            "source_origin_id": raw_origin,
            "source_destination_id": raw_destination,
            "source_endpoint_type": config["demand_endpoint_type"],
        }
        if volume == 0:
            excluded_zero.append(normalized)
        else:
            demands.append(normalized)
    if not demands:
        raise InputContractError("no positive demands remain after the declared zero-demand exclusion rule")
    return {
        "nodes": nodes,
        "links": links,
        "demands": demands,
        "excluded_zero_demands": excluded_zero,
        "zone_access": [{"zone_id": zone, "node_id": node} for zone, node in sorted(zone_access.items())],
        "input_files": {
            name: {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}
            for name, path in paths.items()
        },
    }


def size_estimate(nodes: list[dict[str, Any]], links: list[dict[str, Any]], demands: list[dict[str, Any]], model: dict[str, Any]) -> dict[str, int]:
    departure = int(model["departure_time"])
    horizon = int(model["horizon"])
    layers = horizon - departure + 1
    waiting = len(nodes) * max(0, layers - 1)
    movement = sum(max(0, horizon - departure - int(link["travel_time"]) + 1) for link in links)
    sinks_per_demand = layers
    dynamic_nodes = len(nodes) * layers + 2 * len(demands)
    dynamic_arcs = waiting + movement + len(demands) * (1 + sinks_per_demand)
    reference_variables = len(demands) * (waiting + movement + 1 + sinks_per_demand)
    return {
        "physical_nodes": len(nodes),
        "physical_links": len(links),
        "positive_demands": len(demands),
        "time_layers": layers,
        "estimated_dynamic_nodes": dynamic_nodes,
        "estimated_dynamic_arcs": dynamic_arcs,
        "estimated_reference_variables": reference_variables,
    }


def enforce_limits(estimate: dict[str, int], limits: dict[str, Any], seed_k: int) -> dict[str, int]:
    required = {
        "physical_nodes": "max_physical_nodes",
        "physical_links": "max_physical_links",
        "positive_demands": "max_positive_demands",
        "estimated_dynamic_nodes": "max_dynamic_nodes",
        "estimated_dynamic_arcs": "max_dynamic_arcs",
        "estimated_reference_variables": "max_reference_variables",
    }
    resolved: dict[str, int] = {}
    blockers = []
    for metric, config_name in required.items():
        limit = _positive_integer(limits.get(config_name), f"limits.{config_name}")
        resolved[config_name] = limit
        if estimate[metric] > limit:
            blockers.append(f"{metric}={estimate[metric]} exceeds {config_name}={limit}")
    max_seed_k = _positive_integer(limits.get("max_seed_k"), "limits.max_seed_k")
    max_states = _positive_integer(
        limits.get("max_seed_search_states_per_demand"), "limits.max_seed_search_states_per_demand"
    )
    resolved.update({"max_seed_k": max_seed_k, "max_seed_search_states_per_demand": max_states})
    if seed_k < 1 or seed_k > max_seed_k:
        blockers.append(f"seed_k={seed_k} is outside 1..max_seed_k={max_seed_k}")
    if blockers:
        raise InputContractError("size/seed budget blocked: " + "; ".join(blockers))
    return resolved


def _graph(links: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    graph: dict[str, list[dict[str, Any]]] = {}
    for link in links:
        graph.setdefault(str(link["from_node_id"]), []).append(link)
    for outgoing in graph.values():
        outgoing.sort(key=lambda row: str(row["link_id"]))
    return graph


def _reachable(graph: dict[str, list[dict[str, Any]]], origin: str, destination: str) -> bool:
    queue = deque([origin])
    seen = {origin}
    while queue:
        node = queue.popleft()
        if node == destination:
            return True
        for link in graph.get(node, []):
            nxt = str(link["to_node_id"])
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return False


def _shortest_travel_time(graph: dict[str, list[dict[str, Any]]], origin: str, destination: str) -> int | None:
    heap: list[tuple[int, str]] = [(0, origin)]
    best = {origin: 0}
    while heap:
        elapsed, node = heapq.heappop(heap)
        if elapsed != best[node]:
            continue
        if node == destination:
            return elapsed
        for link in graph.get(node, []):
            nxt = str(link["to_node_id"])
            candidate = elapsed + int(link["travel_time"])
            if candidate < best.get(nxt, 2**63 - 1):
                best[nxt] = candidate
                heapq.heappush(heap, (candidate, nxt))
    return None


def _enumerate_simple_paths(
    graph: dict[str, list[dict[str, Any]]],
    origin: str,
    destination: str,
    k: int,
    max_travel_time: int,
    max_states: int,
) -> tuple[list[dict[str, Any]], int, bool]:
    heap: list[tuple[int, tuple[str, ...], str, tuple[str, ...], tuple[str, ...], float]] = [
        (0, (), origin, (origin,), (), 0.0)
    ]
    results: list[dict[str, Any]] = []
    states = 0
    while heap and len(results) < k and states < max_states:
        elapsed, link_key, node, node_sequence, link_sequence, cost = heapq.heappop(heap)
        states += 1
        if node == destination and link_sequence:
            results.append(
                {
                    "link_sequence": list(link_sequence),
                    "node_sequence": list(node_sequence),
                    "travel_time": elapsed,
                    "generalized_cost": cost,
                }
            )
            continue
        visited = set(node_sequence)
        for link in graph.get(node, []):
            nxt = str(link["to_node_id"])
            if nxt in visited:
                continue
            new_elapsed = elapsed + int(link["travel_time"])
            if new_elapsed > max_travel_time:
                continue
            link_id = str(link["link_id"])
            new_links = (*link_sequence, link_id)
            heapq.heappush(
                heap,
                (
                    new_elapsed,
                    new_links,
                    nxt,
                    (*node_sequence, nxt),
                    new_links,
                    cost + float(link["cost"]),
                ),
            )
    return results, states, bool(heap and states >= max_states)


def generate_auto_seeds(
    links: list[dict[str, Any]],
    demands: list[dict[str, Any]],
    *,
    departure_time: int,
    horizon: int,
    seed_k: int,
    max_states_per_demand: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    graph = _graph(links)
    seeds: list[dict[str, Any]] = []
    report: list[dict[str, Any]] = []
    blockers: list[str] = []
    travel_budget = horizon - departure_time
    for demand in demands:
        demand_id = str(demand["demand_id"])
        origin = str(demand["origin_node_id"])
        destination = str(demand["destination_node_id"])
        topology_reachable = _reachable(graph, origin, destination)
        shortest = _shortest_travel_time(graph, origin, destination) if topology_reachable else None
        if not topology_reachable:
            status, reason, paths, states, exhausted = "FAIL", "topology_unreachable", [], 0, False
        elif shortest is not None and shortest > travel_budget:
            status, reason, paths, states, exhausted = "FAIL", "shortest_path_exceeds_fixed_horizon", [], 0, False
        else:
            paths, states, exhausted = _enumerate_simple_paths(
                graph, origin, destination, seed_k, travel_budget, max_states_per_demand
            )
            if not paths:
                status = "FAIL"
                reason = "search_budget_exhausted" if exhausted else "no_in_horizon_simple_path_found"
            else:
                status = "PASS"
                reason = "search_budget_exhausted_after_partial_results" if exhausted else (
                    "fewer_than_k_simple_paths" if len(paths) < seed_k else "requested_k_reached"
                )
        for rank, path in enumerate(paths, 1):
            column_id = f"auto_{hashlib.sha256(demand_id.encode('utf-8')).hexdigest()[:10]}_{rank:03d}"
            seeds.append(
                {
                    "column_id": column_id,
                    "demand_id": demand_id,
                    "path_rank": rank,
                    "link_sequence": ";".join(path["link_sequence"]),
                    "node_sequence": ";".join(path["node_sequence"]),
                    "travel_time": path["travel_time"],
                    "generalized_cost": path["generalized_cost"],
                    "arrival_time": departure_time + int(path["travel_time"]),
                    "seed_mode": "auto",
                    "ranking_rule": "travel_time_then_link_id_sequence",
                    "search_states": states,
                    "shortage_reason": reason,
                }
            )
        report.append(
            {
                "demand_id": demand_id,
                "origin_node_id": origin,
                "destination_node_id": destination,
                "requested_k": seed_k,
                "generated_count": len(paths),
                "status": status,
                "reason": reason,
                "topology_reachable": topology_reachable,
                "shortest_travel_time": shortest if shortest is not None else "",
                "fixed_horizon_travel_budget": travel_budget,
                "search_states": states,
                "search_budget": max_states_per_demand,
            }
        )
        if not paths:
            blockers.append(f"positive demand {demand_id} has no seed: {reason}")
    return seeds, report, blockers


def validate_supplied_seeds(
    raw_seeds: list[dict[str, Any]],
    links: list[dict[str, Any]],
    demands: list[dict[str, Any]],
    *,
    departure_time: int,
    horizon: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    if not raw_seeds:
        raise InputContractError("supplied seed CSV is empty")
    link_by_id = {str(row["link_id"]): row for row in links}
    demand_by_id = {str(row["demand_id"]): row for row in demands}
    seen: set[str] = set()
    counts = {demand_id: 0 for demand_id in demand_by_id}
    seeds: list[dict[str, Any]] = []
    blockers: list[str] = []
    for raw in raw_seeds:
        column_id = _id(raw.get("column_id"), "supplied column_id")
        demand_id = _id(raw.get("demand_id"), f"seed {column_id} demand_id", demand=True)
        if column_id in seen:
            blockers.append(f"duplicate supplied column_id {column_id}")
            continue
        seen.add(column_id)
        if demand_id not in demand_by_id:
            blockers.append(f"seed {column_id} references unknown demand {demand_id}")
            continue
        raw_sequence = str(raw.get("link_sequence", ""))
        sequence = [item.strip() for item in raw_sequence.replace("|", ";").split(";") if item.strip()]
        if not sequence:
            blockers.append(f"seed {column_id} has empty link_sequence")
            continue
        missing = [item for item in sequence if item not in link_by_id]
        if missing:
            blockers.append(f"seed {column_id} references disallowed/missing links {missing}")
            continue
        path_links = [link_by_id[item] for item in sequence]
        demand = demand_by_id[demand_id]
        if path_links[0]["from_node_id"] != demand["origin_node_id"] or path_links[-1]["to_node_id"] != demand["destination_node_id"]:
            blockers.append(f"seed {column_id} endpoints do not match demand {demand_id}")
            continue
        if any(left["to_node_id"] != right["from_node_id"] for left, right in zip(path_links, path_links[1:])):
            blockers.append(f"seed {column_id} is not a directed continuous path")
            continue
        travel_time = sum(int(link["travel_time"]) for link in path_links)
        if departure_time + travel_time > horizon:
            blockers.append(f"seed {column_id} exceeds fixed horizon")
            continue
        counts[demand_id] += 1
        seeds.append(
            {
                "column_id": column_id,
                "demand_id": demand_id,
                "path_rank": counts[demand_id],
                "link_sequence": ";".join(sequence),
                "node_sequence": ";".join(
                    [str(path_links[0]["from_node_id"]), *[str(link["to_node_id"]) for link in path_links]]
                ),
                "travel_time": travel_time,
                "generalized_cost": sum(float(link["cost"]) for link in path_links),
                "arrival_time": departure_time + travel_time,
                "seed_mode": "supplied",
                "ranking_rule": "supplied_file_order_per_demand",
                "search_states": 0,
                "shortage_reason": "supplied",
            }
        )
    for demand_id, count in counts.items():
        if count == 0:
            blockers.append(f"positive demand {demand_id} has no valid supplied seed")
    report = [
        {
            "demand_id": demand_id,
            "requested_k": "SUPPLIED",
            "generated_count": count,
            "status": "PASS" if count else "FAIL",
            "reason": "supplied" if count else "no_valid_supplied_seed",
        }
        for demand_id, count in counts.items()
    ]
    return seeds, report, blockers
