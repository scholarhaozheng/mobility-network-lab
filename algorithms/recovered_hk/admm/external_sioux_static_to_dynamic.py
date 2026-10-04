"""Tiny external Sioux static-to-dynamic subset conversion helpers.

The converter is intentionally scoped to small read-only subsets of the
external Sioux Falls GMNS+ dataset. It creates derived dynamic artifacts under
an output directory and does not write back to ``external_data``.
"""

from __future__ import annotations

import math
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from scipy.optimize import linprog
from scipy.sparse import lil_matrix

from external_sioux_ingest import (
    links_by_id,
    node_sequence_from_links,
    normalize_link_sequence,
    parse_float,
    parse_int,
    rel,
    split_semicolon_sequence,
)


SCOPE_LABEL = "EXTERNAL_SIOUX_SMALL_SUBSET_NOT_FULL_NETWORK"
NETWORK_MODE_LEGACY_ROUTE_UNION = "legacy_route_union"
NETWORK_MODE_EXPLICIT_ALLOWED_NETWORK = "explicit_allowed_network"
MODEL_SCHEMA_VERSION = "gmns_dynamic_explicit_allowed_network_v1"

DYNAMIC_NODE_FIELDS = ["node_time_id", "physical_node_id", "time", "node_type"]
DYNAMIC_ARC_FIELDS = [
    "arc_id",
    "from_node_time_id",
    "to_node_time_id",
    "from_physical_node_id",
    "to_physical_node_id",
    "from_time",
    "to_time",
    "arc_type",
    "physical_link_id",
    "cost",
    "capacity",
]
DYNAMIC_DEMAND_FIELDS = ["demand_id", "origin_node_id", "destination_node_id", "departure_time", "volume"]
DYNAMIC_COLUMN_FIELDS = [
    "column_id",
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
]


@dataclass(frozen=True)
class ExternalSiouxSubsetConfig:
    selected_od_pairs: tuple[tuple[str, str], ...] = (("1", "2"), ("1", "3"), ("1", "4"))
    time_step_minutes: int = 1
    departure_time: int = 0
    initial_wait_minutes: int = 1
    waiting_cost: float = 1.0
    horizon_padding_minutes: int = 1
    capacity_scaling: float = 1.0
    movement_cost_field: str = "vdf_fftt"
    initial_column_policy: str = "one_delayed_route_assignment_column_per_selected_od"
    scope_label: str = SCOPE_LABEL

    def jsonable(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["selected_od_pairs"] = [list(pair) for pair in self.selected_od_pairs]
        return payload


def _demand_id(index: int) -> str:
    return f"XS{index}"


def _node_time(node_id: str, time_value: int) -> str:
    return f"n{node_id}_t{time_value}"


def _source_node(demand_id: str, departure_time: int) -> str:
    return f"source_{demand_id}_t{departure_time}"


def _sink_node(demand_id: str, horizon: int) -> str:
    return f"sink_{demand_id}_t{horizon}"


def _movement_arc_id(link_id: str, time_value: int) -> str:
    return f"xs_link{link_id}_t{time_value}"


def _waiting_arc_id(node_id: str, time_value: int) -> str:
    return f"wait_{node_id}_t{time_value}"


def _sink_arc_id(demand_id: str, destination: str, time_value: int) -> str:
    return f"sink_{demand_id}_{destination}_t{time_value}"


def _route_lookup(routes: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    lookup: dict[tuple[str, str], dict[str, str]] = {}
    for row in routes:
        key = (str(row.get("origin", "")).strip(), str(row.get("destination", "")).strip())
        if key[0] and key[1] and key not in lookup:
            lookup[key] = row
    return lookup


def _demand_lookup(demands: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    return {
        (str(row.get("o_zone_id", "")).strip(), str(row.get("d_zone_id", "")).strip()): row
        for row in demands
    }


def _link_cost(link: dict[str, str], config: ExternalSiouxSubsetConfig) -> int:
    value = link.get(config.movement_cost_field)
    if value in (None, ""):
        value = link.get("vdf_fftt")
    return max(1, parse_int(value, 1))


def select_positive_od_routes(
    tables: dict[str, list[dict[str, str]]],
    config: ExternalSiouxSubsetConfig,
) -> list[dict[str, Any]]:
    link_lookup = links_by_id(tables["links"])
    demands = _demand_lookup(tables["demands"])
    routes = _route_lookup(tables["routes"])
    selected: list[dict[str, Any]] = []
    blockers: list[str] = []
    for index, (origin, destination) in enumerate(config.selected_od_pairs, start=1):
        demand = demands.get((origin, destination))
        route = routes.get((origin, destination))
        if demand is None:
            blockers.append(f"missing demand row for {origin}->{destination}")
            continue
        if route is None:
            blockers.append(f"missing route_assignment row for {origin}->{destination}")
            continue
        volume = parse_float(demand.get("volume"), 0.0)
        if volume <= 0:
            blockers.append(f"nonpositive demand volume for {origin}->{destination}: {volume}")
            continue
        raw_link_ids = split_semicolon_sequence(route.get("link_ids", ""))
        try:
            link_ids, normalization = normalize_link_sequence(origin, destination, raw_link_ids, link_lookup)
            node_ids = node_sequence_from_links(origin, link_ids, link_lookup)
        except ValueError as exc:
            blockers.append(str(exc))
            continue
        travel_times = [_link_cost(link_lookup[link_id], config) for link_id in link_ids]
        selected.append(
            {
                "selection_index": index,
                "demand_id": _demand_id(index),
                "origin": origin,
                "destination": destination,
                "volume": volume,
                "raw_route_link_ids": raw_link_ids,
                "normalized_link_ids": link_ids,
                "normalization": normalization,
                "node_ids": node_ids,
                "movement_cost": float(sum(travel_times)),
                "movement_time": int(sum(travel_times)),
                "travel_times_by_link": dict(zip(link_ids, travel_times, strict=True)),
                "external_route_total_free_flow_time": route.get("total_free_flow_travel_time", ""),
                "external_route_total_travel_time": route.get("total_travel_time", ""),
            }
        )
    if blockers:
        raise ValueError("; ".join(blockers))
    return selected


def build_external_sioux_subset(
    tables: dict[str, list[dict[str, str]]],
    config: ExternalSiouxSubsetConfig | None = None,
) -> dict[str, Any]:
    config = config or ExternalSiouxSubsetConfig()
    selected = select_positive_od_routes(tables, config)
    link_lookup = links_by_id(tables["links"])
    node_lookup = {row.get("node_id", ""): row for row in tables["nodes"] if row.get("node_id", "")}
    selected_link_ids = sorted({link_id for route in selected for link_id in route["normalized_link_ids"]}, key=parse_int)
    selected_node_ids = sorted({node for route in selected for node in route["node_ids"]}, key=parse_int)
    max_initial_arrival = max(
        config.departure_time + config.initial_wait_minutes + route["movement_time"] for route in selected
    )
    horizon = max_initial_arrival + max(0, config.horizon_padding_minutes)

    dynamic_nodes: list[dict[str, Any]] = []
    for node_id in selected_node_ids:
        for time_value in range(config.departure_time, horizon + 1):
            dynamic_nodes.append(
                {
                    "node_time_id": _node_time(node_id, time_value),
                    "physical_node_id": node_id,
                    "time": time_value,
                    "node_type": "physical",
                }
            )
    for route in selected:
        demand_id = route["demand_id"]
        dynamic_nodes.append(
            {
                "node_time_id": _source_node(demand_id, config.departure_time),
                "physical_node_id": f"source_{demand_id}",
                "time": config.departure_time,
                "node_type": "source",
            }
        )
        dynamic_nodes.append(
            {
                "node_time_id": _sink_node(demand_id, horizon),
                "physical_node_id": f"sink_{demand_id}",
                "time": horizon,
                "node_type": "sink",
            }
        )

    dynamic_arcs: list[dict[str, Any]] = []
    for route in selected:
        demand_id = route["demand_id"]
        origin = route["origin"]
        destination = route["destination"]
        volume = route["volume"]
        dynamic_arcs.append(
            {
                "arc_id": f"source_{demand_id}",
                "from_node_time_id": _source_node(demand_id, config.departure_time),
                "to_node_time_id": _node_time(origin, config.departure_time),
                "from_physical_node_id": f"source_{demand_id}",
                "to_physical_node_id": origin,
                "from_time": config.departure_time,
                "to_time": config.departure_time,
                "arc_type": "source_connector",
                "physical_link_id": "",
                "cost": 0.0,
                "capacity": volume,
            }
        )
        for time_value in range(config.departure_time, horizon + 1):
            dynamic_arcs.append(
                {
                    "arc_id": _sink_arc_id(demand_id, destination, time_value),
                    "from_node_time_id": _node_time(destination, time_value),
                    "to_node_time_id": _sink_node(demand_id, horizon),
                    "from_physical_node_id": destination,
                    "to_physical_node_id": f"sink_{demand_id}",
                    "from_time": time_value,
                    "to_time": horizon,
                    "arc_type": "sink_connector",
                    "physical_link_id": "",
                    "cost": 0.0,
                    "capacity": max(volume, sum(r["volume"] for r in selected)),
                }
            )
    for node_id in selected_node_ids:
        for time_value in range(config.departure_time, horizon):
            dynamic_arcs.append(
                {
                    "arc_id": _waiting_arc_id(node_id, time_value),
                    "from_node_time_id": _node_time(node_id, time_value),
                    "to_node_time_id": _node_time(node_id, time_value + config.time_step_minutes),
                    "from_physical_node_id": node_id,
                    "to_physical_node_id": node_id,
                    "from_time": time_value,
                    "to_time": time_value + config.time_step_minutes,
                    "arc_type": "waiting",
                    "physical_link_id": "",
                    "cost": config.waiting_cost,
                    "capacity": sum(r["volume"] for r in selected),
                }
            )
    for link_id in selected_link_ids:
        link = link_lookup[link_id]
        travel_time = _link_cost(link, config)
        for time_value in range(config.departure_time, horizon - travel_time + 1):
            dynamic_arcs.append(
                {
                    "arc_id": _movement_arc_id(link_id, time_value),
                    "from_node_time_id": _node_time(link["from_node_id"], time_value),
                    "to_node_time_id": _node_time(link["to_node_id"], time_value + travel_time),
                    "from_physical_node_id": link["from_node_id"],
                    "to_physical_node_id": link["to_node_id"],
                    "from_time": time_value,
                    "to_time": time_value + travel_time,
                    "arc_type": "movement",
                    "physical_link_id": link_id,
                    "cost": float(travel_time),
                    "capacity": parse_float(link.get("capacity"), 0.0) * config.capacity_scaling,
                }
            )

    dynamic_demands: list[dict[str, Any]] = [
        {
            "demand_id": route["demand_id"],
            "origin_node_id": route["origin"],
            "destination_node_id": route["destination"],
            "departure_time": config.departure_time,
            "volume": route["volume"],
        }
        for route in selected
    ]

    dynamic_columns: list[dict[str, Any]] = []
    for route in selected:
        time_value = config.departure_time
        arc_sequence = [f"source_{route['demand_id']}"]
        arc_sequence.extend(_waiting_arc_id(route["origin"], t) for t in range(time_value, time_value + config.initial_wait_minutes))
        time_value += config.initial_wait_minutes
        link_sequence: list[str] = []
        time_sequence = [str(config.departure_time)]
        for link_id in route["normalized_link_ids"]:
            link_time = route["travel_times_by_link"][link_id]
            arc_id = _movement_arc_id(link_id, time_value)
            arc_sequence.append(arc_id)
            link_sequence.append(arc_id)
            time_value += link_time
            time_sequence.append(str(time_value))
        arc_sequence.append(_sink_arc_id(route["demand_id"], route["destination"], time_value))
        dynamic_columns.append(
            {
                "column_id": f"EXTSIOUX_CUR_{route['demand_id']}_DELAYED",
                "demand_id": route["demand_id"],
                "origin_node_id": route["origin"],
                "destination_node_id": route["destination"],
                "departure_time": config.departure_time,
                "arrival_time": time_value,
                "travel_time": time_value - config.departure_time,
                "generalized_cost": float(route["movement_cost"] + config.initial_wait_minutes * config.waiting_cost),
                "node_sequence": "|".join(route["node_ids"]),
                "link_sequence": "|".join(link_sequence),
                "time_sequence": "|".join(time_sequence),
                "arc_sequence": "|".join(arc_sequence),
            }
        )

    validation = validate_dynamic_subset(dynamic_nodes, dynamic_arcs, dynamic_demands, dynamic_columns)
    counts = {
        "selected_od_count": len(selected),
        "selected_static_node_count": len(selected_node_ids),
        "selected_static_link_count": len(selected_link_ids),
        "dynamic_node_count": len(dynamic_nodes),
        "dynamic_arc_count": len(dynamic_arcs),
        "dynamic_demand_count": len(dynamic_demands),
        "dynamic_column_count": len(dynamic_columns),
        "source_connector_count": sum(1 for row in dynamic_arcs if row["arc_type"] == "source_connector"),
        "sink_connector_count": sum(1 for row in dynamic_arcs if row["arc_type"] == "sink_connector"),
        "waiting_arc_count": sum(1 for row in dynamic_arcs if row["arc_type"] == "waiting"),
        "movement_arc_count": sum(1 for row in dynamic_arcs if row["arc_type"] == "movement"),
        "horizon": horizon,
    }
    initial_objective = sum(parse_float(row["generalized_cost"]) * parse_float(d["volume"]) for row, d in zip(dynamic_columns, dynamic_demands, strict=True))
    return {
        "network_mode": NETWORK_MODE_LEGACY_ROUTE_UNION,
        "model_schema_version": MODEL_SCHEMA_VERSION,
        "scope_label": config.scope_label,
        "config": config.jsonable(),
        "selected_routes": selected,
        "selected_static_node_ids": selected_node_ids,
        "selected_static_link_ids": selected_link_ids,
        "dynamic_nodes": dynamic_nodes,
        "dynamic_arcs": dynamic_arcs,
        "dynamic_demands": dynamic_demands,
        "dynamic_columns": dynamic_columns,
        "validation": validation,
        "counts": counts,
        "initial_column_objective": initial_objective,
        "assumptions": assumptions(config),
    }


def assumptions(config: ExternalSiouxSubsetConfig) -> dict[str, Any]:
    return {
        "scope_label": config.scope_label,
        "time_step_minutes": config.time_step_minutes,
        "horizon_policy": "max selected delayed route arrival plus padding",
        "departure_time": config.departure_time,
        "waiting_cost": config.waiting_cost,
        "movement_cost": f"integer minutes from external link.{config.movement_cost_field}",
        "capacity_scaling": config.capacity_scaling,
        "initial_column_policy": config.initial_column_policy,
        "od_selection": "fixed positive subset from demand.csv specified by ExternalSiouxSubsetConfig.selected_od_pairs",
        "route_assignment_link_order": "accepted as-provided when chained, otherwise reversed and recorded",
        "claim_boundary": "bounded selected subset only; not full external Sioux Falls",
    }


@dataclass(frozen=True)
class ExplicitAllowedNetworkConfig:
    time_step_minutes: int = 1
    departure_time: int = 0
    horizon: int = 8
    waiting_cost: float = 1.0
    waiting_capacity: float | None = None
    scope_label: str = "EXPLICIT_ALLOWED_NETWORK_MICRO_REGRESSION"
    network_mode: str = NETWORK_MODE_EXPLICIT_ALLOWED_NETWORK
    model_schema_version: str = MODEL_SCHEMA_VERSION

    def jsonable(self) -> dict[str, Any]:
        return asdict(self)


def _signature(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _explicit_link_arc_id(link_id: str, time_value: int) -> str:
    return f"explicit_link_{link_id}_t{time_value}"


def _required(row: dict[str, Any], field: str, kind: str) -> str:
    value = str(row.get(field, "")).strip()
    if not value:
        raise ValueError(f"{kind} missing required field {field}")
    return value


def _positive_integer(value: Any, field: str, identity: str) -> int:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{identity} has nonnumeric {field}: {value}") from exc
    if not math.isfinite(numeric) or numeric <= 0 or not numeric.is_integer():
        raise ValueError(f"{identity} requires positive integer {field}: {value}")
    return int(numeric)


def build_explicit_allowed_network(
    nodes: list[dict[str, Any]],
    allowed_links: list[dict[str, Any]],
    demands: list[dict[str, Any]],
    seed_columns: list[dict[str, Any]],
    config: ExplicitAllowedNetworkConfig | None = None,
) -> dict[str, Any]:
    """Build a fixed time-expanded model whose network is independent of seeds.

    ``allowed_links`` defines every movement arc made available to both the
    reference LP and CG pricing. ``seed_columns`` only initializes the RMP.
    Link identity is never collapsed, including parallel links.
    """
    config = config or ExplicitAllowedNetworkConfig()
    if config.network_mode != NETWORK_MODE_EXPLICIT_ALLOWED_NETWORK:
        raise ValueError(f"unsupported explicit network_mode: {config.network_mode}")
    if config.time_step_minutes != 1:
        raise ValueError("explicit_allowed_network currently requires a 1-minute time step")
    if config.departure_time < 0 or config.horizon <= config.departure_time:
        raise ValueError("explicit_allowed_network requires horizon > nonnegative departure_time")
    if not math.isfinite(config.waiting_cost) or config.waiting_cost < 0:
        raise ValueError("waiting_cost must be finite and nonnegative")

    node_ids = [_required(row, "node_id", "node") for row in nodes]
    if len(node_ids) != len(set(node_ids)):
        raise ValueError("duplicate node_id in explicit allowed network")
    if not node_ids:
        raise ValueError("explicit allowed network requires at least one node")
    node_set = set(node_ids)

    link_ids = [_required(row, "link_id", "allowed link") for row in allowed_links]
    if len(link_ids) != len(set(link_ids)):
        raise ValueError("duplicate link_id in explicit allowed network")
    if not link_ids:
        raise ValueError("explicit allowed network requires at least one link")
    normalized_links: list[dict[str, Any]] = []
    for row, link_id in zip(allowed_links, link_ids, strict=True):
        start = _required(row, "from_node_id", f"link {link_id}")
        end = _required(row, "to_node_id", f"link {link_id}")
        if start not in node_set or end not in node_set:
            raise ValueError(f"link {link_id} references nonexistent endpoint {start}->{end}")
        travel_time = _positive_integer(row.get("travel_time"), "travel_time", f"link {link_id}")
        try:
            cost = float(row.get("cost"))
            capacity = float(row.get("capacity"))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"link {link_id} has nonnumeric cost/capacity") from exc
        if not math.isfinite(cost) or cost < 0:
            raise ValueError(f"link {link_id} requires finite nonnegative cost")
        if not math.isfinite(capacity) or capacity <= 0:
            raise ValueError(f"link {link_id} requires finite positive capacity")
        normalized_links.append(
            {
                "link_id": link_id,
                "from_node_id": start,
                "to_node_id": end,
                "travel_time": travel_time,
                "cost": cost,
                "capacity": capacity,
            }
        )
    link_by_id = {row["link_id"]: row for row in normalized_links}

    demand_ids = [_required(row, "demand_id", "demand") for row in demands]
    if len(demand_ids) != len(set(demand_ids)):
        raise ValueError("duplicate demand_id in explicit allowed network")
    if not demand_ids:
        raise ValueError("explicit allowed network requires at least one demand")
    normalized_demands: list[dict[str, Any]] = []
    for row, demand_id in zip(demands, demand_ids, strict=True):
        origin = _required(row, "origin_node_id", f"demand {demand_id}")
        destination = _required(row, "destination_node_id", f"demand {demand_id}")
        if origin not in node_set or destination not in node_set:
            raise ValueError(f"demand {demand_id} references nonexistent endpoint {origin}->{destination}")
        departure = int(float(row.get("departure_time", config.departure_time)))
        if departure != config.departure_time:
            raise ValueError(f"demand {demand_id} departure_time differs from declared model departure")
        try:
            volume = float(row.get("volume"))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"demand {demand_id} has nonnumeric volume") from exc
        if not math.isfinite(volume) or volume <= 0:
            raise ValueError(f"demand {demand_id} requires finite positive volume")
        normalized_demands.append(
            {
                "demand_id": demand_id,
                "origin_node_id": origin,
                "destination_node_id": destination,
                "departure_time": departure,
                "volume": volume,
            }
        )
    demand_by_id = {row["demand_id"]: row for row in normalized_demands}
    total_volume = sum(row["volume"] for row in normalized_demands)
    wait_capacity = config.waiting_capacity if config.waiting_capacity is not None else total_volume
    if not math.isfinite(wait_capacity) or wait_capacity < total_volume:
        raise ValueError("waiting_capacity must be finite and at least total demand volume")

    dynamic_nodes: list[dict[str, Any]] = []
    for node_id in node_ids:
        for time_value in range(config.departure_time, config.horizon + 1, config.time_step_minutes):
            dynamic_nodes.append(
                {
                    "node_time_id": _node_time(node_id, time_value),
                    "physical_node_id": node_id,
                    "time": time_value,
                    "node_type": "physical",
                }
            )
    for demand in normalized_demands:
        demand_id = demand["demand_id"]
        dynamic_nodes.extend(
            [
                {
                    "node_time_id": _source_node(demand_id, config.departure_time),
                    "physical_node_id": f"source_{demand_id}",
                    "time": config.departure_time,
                    "node_type": "source",
                },
                {
                    "node_time_id": _sink_node(demand_id, config.horizon),
                    "physical_node_id": f"sink_{demand_id}",
                    "time": config.horizon,
                    "node_type": "sink",
                },
            ]
        )

    dynamic_arcs: list[dict[str, Any]] = []
    for demand in normalized_demands:
        demand_id = demand["demand_id"]
        origin = demand["origin_node_id"]
        destination = demand["destination_node_id"]
        dynamic_arcs.append(
            {
                "arc_id": f"source_{demand_id}",
                "from_node_time_id": _source_node(demand_id, config.departure_time),
                "to_node_time_id": _node_time(origin, config.departure_time),
                "from_physical_node_id": f"source_{demand_id}",
                "to_physical_node_id": origin,
                "from_time": config.departure_time,
                "to_time": config.departure_time,
                "arc_type": "source_connector",
                "physical_link_id": "",
                "cost": 0.0,
                "capacity": demand["volume"],
            }
        )
        for time_value in range(config.departure_time, config.horizon + 1, config.time_step_minutes):
            dynamic_arcs.append(
                {
                    "arc_id": _sink_arc_id(demand_id, destination, time_value),
                    "from_node_time_id": _node_time(destination, time_value),
                    "to_node_time_id": _sink_node(demand_id, config.horizon),
                    "from_physical_node_id": destination,
                    "to_physical_node_id": f"sink_{demand_id}",
                    "from_time": time_value,
                    "to_time": config.horizon,
                    "arc_type": "sink_connector",
                    "physical_link_id": "",
                    "cost": 0.0,
                    "capacity": total_volume,
                }
            )
    for node_id in node_ids:
        for time_value in range(config.departure_time, config.horizon, config.time_step_minutes):
            dynamic_arcs.append(
                {
                    "arc_id": _waiting_arc_id(node_id, time_value),
                    "from_node_time_id": _node_time(node_id, time_value),
                    "to_node_time_id": _node_time(node_id, time_value + config.time_step_minutes),
                    "from_physical_node_id": node_id,
                    "to_physical_node_id": node_id,
                    "from_time": time_value,
                    "to_time": time_value + config.time_step_minutes,
                    "arc_type": "waiting",
                    "physical_link_id": "",
                    "cost": config.waiting_cost,
                    "capacity": wait_capacity,
                }
            )
    for link in normalized_links:
        travel_time = link["travel_time"]
        for time_value in range(
            config.departure_time,
            config.horizon - travel_time + 1,
            config.time_step_minutes,
        ):
            dynamic_arcs.append(
                {
                    "arc_id": _explicit_link_arc_id(link["link_id"], time_value),
                    "from_node_time_id": _node_time(link["from_node_id"], time_value),
                    "to_node_time_id": _node_time(link["to_node_id"], time_value + travel_time),
                    "from_physical_node_id": link["from_node_id"],
                    "to_physical_node_id": link["to_node_id"],
                    "from_time": time_value,
                    "to_time": time_value + travel_time,
                    "arc_type": "movement",
                    "physical_link_id": link["link_id"],
                    "cost": link["cost"],
                    "capacity": link["capacity"],
                }
            )
    arc_by_id = {str(row["arc_id"]): row for row in dynamic_arcs}

    seed_ids = [_required(row, "column_id", "seed column") for row in seed_columns]
    if len(seed_ids) != len(set(seed_ids)):
        raise ValueError("duplicate column_id in explicit seed pool")
    dynamic_columns: list[dict[str, Any]] = []
    for seed, seed_id in zip(seed_columns, seed_ids, strict=True):
        demand_id = _required(seed, "demand_id", f"seed {seed_id}")
        if demand_id not in demand_by_id:
            raise ValueError(f"seed {seed_id} references unknown demand {demand_id}")
        raw_sequence = str(seed.get("link_sequence", "")).replace("|", ";")
        link_sequence = [item.strip() for item in raw_sequence.split(";") if item.strip()]
        if not link_sequence:
            raise ValueError(f"seed {seed_id} has empty link_sequence")
        if any(link_id not in link_by_id for link_id in link_sequence):
            missing = [link_id for link_id in link_sequence if link_id not in link_by_id]
            raise ValueError(f"seed {seed_id} references disallowed/missing links: {missing}")
        links = [link_by_id[link_id] for link_id in link_sequence]
        demand = demand_by_id[demand_id]
        if links[0]["from_node_id"] != demand["origin_node_id"] or links[-1]["to_node_id"] != demand["destination_node_id"]:
            raise ValueError(f"seed {seed_id} endpoints do not match demand {demand_id}")
        if any(left["to_node_id"] != right["from_node_id"] for left, right in zip(links, links[1:])):
            raise ValueError(f"seed {seed_id} link sequence is not a directed chain")
        time_value = demand["departure_time"]
        arc_sequence = [f"source_{demand_id}"]
        dynamic_link_sequence: list[str] = []
        time_sequence = [str(time_value)]
        physical_nodes = [demand["origin_node_id"]]
        for link in links:
            arc_id = _explicit_link_arc_id(link["link_id"], time_value)
            if arc_id not in arc_by_id:
                raise ValueError(f"seed {seed_id} exceeds fixed horizon at {arc_id}")
            arc_sequence.append(arc_id)
            dynamic_link_sequence.append(arc_id)
            time_value += link["travel_time"]
            time_sequence.append(str(time_value))
            physical_nodes.append(link["to_node_id"])
        arc_sequence.append(_sink_arc_id(demand_id, demand["destination_node_id"], time_value))
        dynamic_columns.append(
            {
                "column_id": seed_id,
                "demand_id": demand_id,
                "origin_node_id": demand["origin_node_id"],
                "destination_node_id": demand["destination_node_id"],
                "departure_time": demand["departure_time"],
                "arrival_time": time_value,
                "travel_time": time_value - demand["departure_time"],
                "generalized_cost": sum(link["cost"] for link in links),
                "node_sequence": "|".join(physical_nodes),
                "link_sequence": "|".join(dynamic_link_sequence),
                "time_sequence": "|".join(time_sequence),
                "arc_sequence": "|".join(arc_sequence),
            }
        )

    validation = validate_dynamic_subset(dynamic_nodes, dynamic_arcs, normalized_demands, dynamic_columns)
    if validation["validation_status"] != "PASS":
        raise ValueError("; ".join(validation["blockers"]))
    model_payload = {
        "model_schema_version": config.model_schema_version,
        "network_mode": config.network_mode,
        "model_config": {
            "time_step_minutes": config.time_step_minutes,
            "departure_time": config.departure_time,
            "horizon": config.horizon,
            "waiting_cost": config.waiting_cost,
            "waiting_capacity": config.waiting_capacity,
        },
        "dynamic_nodes": dynamic_nodes,
        "dynamic_arcs": dynamic_arcs,
        "dynamic_demands": normalized_demands,
    }
    model_signature = _signature(model_payload)
    return {
        "network_mode": config.network_mode,
        "model_schema_version": config.model_schema_version,
        "scope_label": config.scope_label,
        "config": config.jsonable(),
        "allowed_nodes": [{"node_id": node_id} for node_id in node_ids],
        "allowed_links": normalized_links,
        "dynamic_nodes": dynamic_nodes,
        "dynamic_arcs": dynamic_arcs,
        "dynamic_demands": normalized_demands,
        "dynamic_columns": dynamic_columns,
        "validation": validation,
        "model_signature": model_signature,
        "seed_pool_signature": _signature(dynamic_columns),
        "counts": {
            "physical_node_count": len(node_ids),
            "allowed_physical_link_count": len(normalized_links),
            "dynamic_node_count": len(dynamic_nodes),
            "dynamic_arc_count": len(dynamic_arcs),
            "dynamic_demand_count": len(normalized_demands),
            "initial_column_count": len(dynamic_columns),
            "horizon": config.horizon,
        },
        "assumptions": {
            "network_definition": "explicit allowed nodes/links; independent of seed columns",
            "time_step_minutes": config.time_step_minutes,
            "movement_travel_time": "positive integer minutes",
            "movement_capacity": "vehicles per time-indexed dynamic arc",
            "demand_volume": "vehicles injected once at declared departure_time",
            "waiting_cost": config.waiting_cost,
            "seed_role": "initial RMP columns only; never defines allowed movement arcs",
            "parallel_link_identity": "preserved by required unique link_id in every dynamic arc id",
        },
    }


def validate_dynamic_subset(
    nodes: list[dict[str, Any]],
    arcs: list[dict[str, Any]],
    demands: list[dict[str, Any]],
    columns: list[dict[str, Any]],
) -> dict[str, Any]:
    blockers: list[str] = []
    node_ids = {str(row["node_time_id"]) for row in nodes}
    arc_by_id = {str(row["arc_id"]): row for row in arcs}
    if len(arc_by_id) != len(arcs):
        blockers.append("duplicate dynamic arc ids detected")
    if len(node_ids) != len(nodes):
        blockers.append("duplicate dynamic node ids detected")
    for arc in arcs:
        if arc.get("from_node_time_id") not in node_ids:
            blockers.append(f"arc {arc.get('arc_id')} missing from node {arc.get('from_node_time_id')}")
        if arc.get("to_node_time_id") not in node_ids:
            blockers.append(f"arc {arc.get('arc_id')} missing to node {arc.get('to_node_time_id')}")
        if not math.isfinite(parse_float(arc.get("cost"), math.nan)):
            blockers.append(f"arc {arc.get('arc_id')} has nonnumeric cost")
        if not math.isfinite(parse_float(arc.get("capacity"), math.nan)):
            blockers.append(f"arc {arc.get('arc_id')} has nonnumeric capacity")
    for demand in demands:
        demand_id = str(demand["demand_id"])
        source = f"source_{demand_id}"
        if source not in arc_by_id:
            blockers.append(f"demand {demand_id} missing source connector")
        if not any(str(row.get("arc_id", "")).startswith(f"sink_{demand_id}_") for row in arcs):
            blockers.append(f"demand {demand_id} missing sink connector")
        if parse_float(demand.get("volume"), 0.0) <= 0:
            blockers.append(f"demand {demand_id} has nonpositive volume")
    for column in columns:
        current_node = None
        for position, arc_id in enumerate(str(column.get("arc_sequence", "")).split("|")):
            arc = arc_by_id.get(arc_id)
            if arc is None:
                blockers.append(f"column {column.get('column_id')} references missing arc {arc_id}")
                continue
            if position == 0:
                current_node = arc.get("to_node_time_id")
                continue
            if arc.get("from_node_time_id") != current_node:
                blockers.append(f"column {column.get('column_id')} has broken chain at arc {arc_id}")
            current_node = arc.get("to_node_time_id")
        if not str(column.get("arc_sequence", "")).startswith(f"source_{column.get('demand_id')}|"):
            blockers.append(f"column {column.get('column_id')} does not start with own source connector")
        if f"|sink_{column.get('demand_id')}_" not in f"|{column.get('arc_sequence')}":
            blockers.append(f"column {column.get('column_id')} does not end with own sink connector")
    return {
        "validation_status": "PASS" if not blockers else "CONVERTER_BLOCKED",
        "blocker_count": len(blockers),
        "blockers": blockers,
        "ids_consistent": not blockers,
        "all_arc_endpoints_exist": not any("missing from node" in item or "missing to node" in item for item in blockers),
        "all_column_path_arcs_exist": not any("references missing arc" in item for item in blockers),
        "all_column_paths_chain": not any("broken chain" in item for item in blockers),
        "all_demands_have_source_sink_connectors": not any("source connector" in item or "sink connector" in item for item in blockers),
        "numeric_costs_and_capacities": not any("nonnumeric" in item for item in blockers),
    }


def solve_small_subset_arc_lp(
    arcs: list[dict[str, Any]],
    demands: list[dict[str, Any]],
) -> dict[str, Any]:
    nodes = sorted({str(arc["from_node_time_id"]) for arc in arcs} | {str(arc["to_node_time_id"]) for arc in arcs})
    node_index = {node: index for index, node in enumerate(nodes)}
    variables: list[dict[str, Any]] = []
    costs: list[float] = []
    for demand in demands:
        demand_id = str(demand["demand_id"])
        for arc in arcs:
            arc_id = str(arc["arc_id"])
            arc_type = str(arc.get("arc_type", ""))
            if arc_type == "source_connector" and arc_id != f"source_{demand_id}":
                continue
            if arc_type == "sink_connector":
                parts = arc_id.split("_")
                if len(parts) < 2 or parts[1] != demand_id:
                    continue
            variables.append({"demand_id": demand_id, "arc_id": arc_id, "arc": arc})
            costs.append(parse_float(arc.get("cost"), 0.0))
    if not variables:
        return {"reference_status": "REFERENCE_GENERATION_BLOCKED", "blockers": ["no arc-flow variables built"]}

    row_count = len(demands) * len(nodes)
    a_eq = lil_matrix((row_count, len(variables)), dtype=float)
    b_eq = [0.0 for _ in range(row_count)]
    demand_index = {str(d["demand_id"]): index for index, d in enumerate(demands)}
    sink_targets: dict[str, str] = {}
    for arc in arcs:
        if arc.get("arc_type") != "sink_connector":
            continue
        parts = str(arc.get("arc_id", "")).split("_")
        if len(parts) >= 2:
            sink_targets.setdefault(parts[1], str(arc.get("to_node_time_id", "")))
    for demand in demands:
        demand_id = str(demand["demand_id"])
        volume = parse_float(demand.get("volume"), 0.0)
        source_node = f"source_{demand_id}_t{demand.get('departure_time', 0)}"
        sink_node = sink_targets.get(demand_id, "")
        if source_node not in node_index or sink_node not in node_index:
            return {
                "reference_status": "REFERENCE_GENERATION_BLOCKED",
                "blockers": [f"missing source/sink balance node for {demand_id}"],
            }
        base = demand_index[demand_id] * len(nodes)
        b_eq[base + node_index[source_node]] = volume
        b_eq[base + node_index[sink_node]] = -volume
    for var_index, var in enumerate(variables):
        demand_id = var["demand_id"]
        arc = var["arc"]
        base = demand_index[demand_id] * len(nodes)
        a_eq[base + node_index[str(arc["from_node_time_id"])], var_index] = 1.0
        a_eq[base + node_index[str(arc["to_node_time_id"])], var_index] = -1.0

    arc_variable_indices: dict[str, list[int]] = {}
    for var_index, var in enumerate(variables):
        arc_variable_indices.setdefault(str(var["arc_id"]), []).append(var_index)
    capacity_rows: list[dict[str, Any]] = []
    b_ub: list[float] = []
    for arc in arcs:
        capacity = parse_float(arc.get("capacity"), math.inf)
        if not math.isfinite(capacity):
            continue
        capacity_rows.append(arc)
        b_ub.append(capacity)
    a_ub = lil_matrix((len(capacity_rows), len(variables)), dtype=float)
    for row_index, arc in enumerate(capacity_rows):
        for var_index in arc_variable_indices.get(str(arc["arc_id"]), []):
            a_ub[row_index, var_index] = 1.0
    a_eq_csr = a_eq.tocsr()
    a_ub_csr = a_ub.tocsr()

    result = linprog(
        c=costs,
        A_ub=a_ub_csr,
        b_ub=b_ub,
        A_eq=a_eq_csr,
        b_eq=b_eq,
        bounds=[(0.0, None) for _ in variables],
        method="highs",
    )
    if not result.success:
        return {
            "reference_status": "REFERENCE_GENERATION_BLOCKED",
            "solver_status": str(result.message),
            "linprog_status": int(result.status),
            "blockers": [str(result.message)],
            "variable_count": len(variables),
        }

    positive_flows = [
        {
            "demand_id": variables[index]["demand_id"],
            "arc_id": variables[index]["arc_id"],
            "flow": float(value),
            "unit_cost": costs[index],
            "objective_contribution": float(value) * costs[index],
        }
        for index, value in enumerate(result.x)
        if float(value) > 1e-8
    ]
    capacity_violations = []
    for row_index, arc in enumerate(capacity_rows):
        flow = sum(float(result.x[col]) for col in arc_variable_indices.get(str(arc["arc_id"]), []))
        capacity = b_ub[row_index]
        if flow > capacity + 1e-7:
            capacity_violations.append({"arc_id": arc["arc_id"], "flow": flow, "capacity": capacity})
    max_balance_residual = 0.0
    balance_lhs = a_eq_csr.dot(result.x)
    for row_index, lhs in enumerate(balance_lhs):
        max_balance_residual = max(max_balance_residual, abs(lhs - b_eq[row_index]))
    return {
        "reference_status": "REFERENCE_GENERATED",
        "solver_status": "optimal",
        "linprog_status": int(result.status),
        "objective_value": float(result.fun),
        "variable_count": len(variables),
        "positive_flow_arc_count": len(positive_flows),
        "positive_flows": positive_flows,
        "capacity_violation_count": len(capacity_violations),
        "capacity_violations": capacity_violations,
        "max_flow_balance_residual": max_balance_residual,
        "objective_gap_allowed": True,
        "optimality_claim_allowed": False,
        "claim_boundary": "arc-LP objective reference for this tiny converted subset only",
    }


def manifest_for_subset(output_dir: Path, reference_summary: dict[str, Any] | None = None) -> dict[str, Any]:
    reference_summary = reference_summary or {}
    reference_objective = reference_summary.get("objective_value")
    def output_path(path: Path) -> str:
        try:
            return rel(path)
        except ValueError:
            return path.as_posix()

    manifest = {
        "benchmark_id": "external_sioux_small_subset_one_probe",
        "scope_label": SCOPE_LABEL,
        "dynamic_data_dir": output_path(output_dir),
        "demand_file": output_path(output_dir / "dynamic_demand.csv"),
        "dynamic_arc_file": output_path(output_dir / "dynamic_arc.csv"),
        "current_candidate_pool_file": output_path(output_dir / "dynamic_columns.csv"),
        "output_root": output_path(output_dir / "full_cg_v1_run"),
        "max_phase_i_rounds": 10,
        "max_phase_ii_rounds": 10,
        "max_candidates_per_demand_per_round": 10,
        "runtime_cap_seconds": 300,
        "no_mutate": True,
        "reference_comparison_policy": "objective_level_when_reference_available",
        "stop_certificate_policy": "always_write",
        "claim_boundary_policy": "bounded_finite_fixture_only",
        "phase_ii_pricing_mode": "one_probe",
        "phase_ii_add_policy": "add_best_one_per_round",
        "k_shortest_k": 1,
        "max_phase_ii_candidates_per_demand": 1,
        "max_phase_ii_candidates_per_round": 10,
        "no_full_assignment_claim": True,
        "no_global_convergence_claim": True,
        "no_exact_flow_pattern_reproduction_claim": True,
    }
    if reference_objective is not None:
        manifest["arc_lp_reference_objective"] = reference_objective
        manifest["arc_lp_reference_summary_path"] = output_path(output_dir / "small_subset_arc_lp_reference_summary.json")
    else:
        manifest["objective_gap_allowed"] = False
        manifest["optimality_claim_allowed"] = False
    return manifest
