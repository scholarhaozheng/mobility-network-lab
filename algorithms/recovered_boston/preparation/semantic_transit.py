"""Bounded GTFS semantics used by the Boston behavior-feedback correction.

This is a thin scheduled-service adapter for the fixed validation panel.  It is
not a general-purpose journey planner.  Its contracts are deliberately explicit:

* a transit result must contain at least one permitted ride;
* access-only labels cannot dominate slower labels that have ridden;
* pickup/drop-off restrictions are honored while same-vehicle continuation is
  preserved;
* transfers.txt specificity, type 2 minimum time, type 3 prohibition, and type
  4 in-seat continuation are represented;
* MBTA's min_walk_time extension is physical walk time, whereas the standard
  min_transfer_time is the total connection allowance.  They are not added;
* Fare v2 is evaluated for adult CharlieCard legs when the feed contains an
  unambiguous generic rule.  Unsupported fares remain unknown, never zero.
"""

from __future__ import annotations

import json
import math
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import networkx as nx
import pandas as pd


WALK_MPS = 3.0 * 1609.344 / 3600.0
DEFAULT_PARENT_TRANSFER_SECONDS = 120.0
STAIR_SECONDS_PER_STEP = 1.5


def gtfs_seconds(value: str) -> int:
    """Parse GTFS service-day time, including values at or beyond 24:00:00."""
    h, m, s = (int(x) for x in str(value).split(":"))
    if h < 0 or not 0 <= m < 60 or not 0 <= s < 60:
        raise ValueError(f"Invalid GTFS time: {value}")
    return h * 3600 + m * 60 + s


def _optional(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _number(value: Any) -> float | None:
    text = _optional(value)
    if text is None:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _permitted(value: Any) -> bool:
    """GTFS value 1 forbids pickup/drop-off; 0, 2, and 3 remain possible."""
    text = _optional(value)
    return text != "1"


@dataclass(frozen=True)
class Connection:
    from_stop: str
    to_stop: str
    dep: int
    arr: int
    trip_id: str
    route_id: str
    route_type: str
    network_id: str
    direction_id: str
    service_id: str
    block_id: str | None
    from_seq: int
    to_seq: int
    pickup_allowed: bool
    dropoff_allowed: bool
    pickup_type: str | None
    drop_off_type: str | None
    overlay_parameter_id: str | None


def build_connections(
    stop_times: pd.DataFrame,
    trip_meta: pd.DataFrame,
    overlay: pd.DataFrame | None,
    *,
    search_end: int,
    earliest_departure: int,
    max_access_seconds: int,
) -> list[Connection]:
    lookup: dict[tuple[str, str, str, str], tuple[float, str]] = {}
    if overlay is not None:
        for row in overlay.itertuples(index=False):
            key = (str(row.route_id), str(row.direction_id), str(row.from_stop_id), str(row.to_stop_id))
            lookup[key] = (float(row.mean_factor), str(row.parameter_id))

    merged = stop_times.merge(trip_meta, on="trip_id", how="inner", validate="many_to_one")
    merged["seq"] = pd.to_numeric(merged["stop_sequence"], errors="raise").astype(int)
    if merged.duplicated(["trip_id", "seq"]).any():
        raise ValueError("GTFS active stop_times has duplicate (trip_id, stop_sequence)")

    out: list[Connection] = []
    for trip_id, group in merged.groupby("trip_id", sort=False):
        rows = list(group.sort_values("seq", kind="stable").itertuples(index=False))
        cumulative_delta = 0.0
        cumulative_parameters: list[str] = []
        for a, b in zip(rows[:-1], rows[1:]):
            dep_base = gtfs_seconds(a.departure_time)
            arr_base = gtfs_seconds(b.arrival_time)
            if int(b.seq) <= int(a.seq):
                raise ValueError(f"Non-increasing stop_sequence on trip {trip_id}")
            base_run = arr_base - dep_base
            if base_run < 0:
                raise ValueError(f"Negative service-day running time on trip {trip_id}: {a.stop_id}->{b.stop_id}")
            key = (str(a.route_id), str(a.direction_id), str(a.stop_id), str(b.stop_id))
            parameter_id = None
            segment_delta = 0.0
            if key in lookup and 12 * 3600 + 30 * 60 <= dep_base <= 13 * 3600 + 15 * 60:
                factor, parameter_id = lookup[key]
                segment_delta = max(1.0, base_run * factor) - base_run
            applied_parameters = list(cumulative_parameters)
            if parameter_id is not None:
                applied_parameters.append(parameter_id)
            dep = int(round(dep_base + cumulative_delta))
            arr = int(round(arr_base + cumulative_delta + segment_delta))
            cumulative_delta += segment_delta
            if dep <= search_end and arr >= earliest_departure - max_access_seconds:
                out.append(
                    Connection(
                        from_stop=str(a.stop_id),
                        to_stop=str(b.stop_id),
                        dep=dep,
                        arr=arr,
                        trip_id=str(trip_id),
                        route_id=str(a.route_id),
                        route_type=str(a.route_type),
                        network_id=str(a.network_id),
                        direction_id=str(a.direction_id),
                        service_id=str(a.service_id),
                        block_id=_optional(getattr(a, "block_id", None)),
                        from_seq=int(a.seq),
                        to_seq=int(b.seq),
                        pickup_allowed=_permitted(getattr(a, "pickup_type", None)),
                        dropoff_allowed=_permitted(getattr(b, "drop_off_type", None)),
                        pickup_type=_optional(getattr(a, "pickup_type", None)),
                        drop_off_type=_optional(getattr(b, "drop_off_type", None)),
                        overlay_parameter_id=";".join(applied_parameters) if applied_parameters else None,
                    )
                )
            if parameter_id is not None:
                cumulative_parameters.append(parameter_id)
    out.sort(key=lambda x: (x.dep, x.arr, x.trip_id, x.from_seq))
    return out


@dataclass(frozen=True)
class TransferRule:
    from_stop: str
    to_stop: str
    transfer_type: str
    min_transfer_time: float | None
    min_walk_time: float | None
    from_trip_id: str | None
    to_trip_id: str | None
    from_route_id: str | None
    to_route_id: str | None
    row_number: int

    def applies(self, from_trip: str, from_route: str, to_trip: str, to_route: str) -> bool:
        return (
            (self.from_trip_id is None or self.from_trip_id == from_trip)
            and (self.to_trip_id is None or self.to_trip_id == to_trip)
            and (self.from_route_id is None or self.from_route_id == from_route)
            and (self.to_route_id is None or self.to_route_id == to_route)
        )

    @property
    def specificity(self) -> int:
        ft, tt = self.from_trip_id is not None, self.to_trip_id is not None
        fr, tr = self.from_route_id is not None, self.to_route_id is not None
        if ft and tt:
            return 6
        if (ft and tr) or (fr and tt):
            return 5
        if ft or tt:
            return 4
        if fr and tr:
            return 3
        if fr or tr:
            return 2
        return 1


class TransferPolicy:
    def __init__(
        self,
        pair_rules: dict[tuple[str, str], list[TransferRule]],
        physical_seconds: dict[tuple[str, str], float],
        type4_to_trip: dict[str, list[tuple[str, str, TransferRule]]],
        stats: dict[str, Any],
    ) -> None:
        self.pair_rules = pair_rules
        self.physical_seconds = physical_seconds
        self.type4_to_trip = type4_to_trip
        incoming: dict[str, set[str]] = defaultdict(set)
        for origin, destination in set(pair_rules) | set(physical_seconds):
            incoming[destination].add(origin)
        self.incoming = {key: tuple(sorted(value)) for key, value in incoming.items()}
        self.stats = stats

    @classmethod
    def build(
        cls,
        stops: pd.DataFrame,
        transfers: pd.DataFrame,
        pathways: pd.DataFrame | None,
    ) -> "TransferPolicy":
        stops = stops.copy()
        stops["stop_id"] = stops["stop_id"].astype(str)
        parent_of = {
            str(row.stop_id): _optional(getattr(row, "parent_station", None))
            for row in stops.itertuples(index=False)
        }
        children_by_parent: dict[str, list[str]] = defaultdict(list)
        for stop_id, parent in parent_of.items():
            if parent:
                children_by_parent[parent].append(stop_id)

        pathway_graph = nx.DiGraph()
        pathway_edges_used = 0
        if pathways is not None and not pathways.empty:
            known = set(stops["stop_id"])
            for row in pathways.itertuples(index=False):
                a = str(row.from_stop_id)
                b = str(row.to_stop_id)
                if a not in known or b not in known:
                    continue
                sec = _number(getattr(row, "traversal_time", None))
                if sec is None:
                    length = _number(getattr(row, "length", None))
                    stairs = _number(getattr(row, "stair_count", None))
                    if length is not None:
                        sec = max(0.0, length / WALK_MPS)
                    elif stairs is not None:
                        sec = abs(stairs) * STAIR_SECONDS_PER_STEP
                if sec is None:
                    continue
                old = pathway_graph.get_edge_data(a, b)
                if old is None or sec < old["seconds"]:
                    pathway_graph.add_edge(a, b, seconds=sec)
                if str(getattr(row, "is_bidirectional", "0")) == "1":
                    old = pathway_graph.get_edge_data(b, a)
                    if old is None or sec < old["seconds"]:
                        pathway_graph.add_edge(b, a, seconds=sec)
                pathway_edges_used += 1

        path_cache: dict[tuple[str, str], float | None] = {}

        def pathway_time(a: str, b: str) -> float | None:
            key = (a, b)
            if key not in path_cache:
                try:
                    path_cache[key] = float(nx.shortest_path_length(pathway_graph, a, b, weight="seconds"))
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    path_cache[key] = None
            return path_cache[key]

        physical: dict[tuple[str, str], float] = {}
        pathway_parent_pairs = 0
        default_parent_pairs = 0
        for children in children_by_parent.values():
            for a in children:
                for b in children:
                    if a == b:
                        continue
                    sec = pathway_time(a, b)
                    if sec is None:
                        sec = DEFAULT_PARENT_TRANSFER_SECONDS
                        default_parent_pairs += 1
                    else:
                        pathway_parent_pairs += 1
                    physical[(a, b)] = min(physical.get((a, b), math.inf), sec)

        def actual_stops(rule_stop: str) -> list[str]:
            return children_by_parent.get(rule_stop, [rule_stop])

        pair_rules: dict[tuple[str, str], list[TransferRule]] = defaultdict(list)
        type4_to_trip: dict[str, list[tuple[str, str, TransferRule]]] = defaultdict(list)
        cross_stop_rules_without_physical = 0
        for index, row in enumerate(transfers.itertuples(index=False), start=2):
            from_stop = str(row.from_stop_id)
            to_stop = str(row.to_stop_id)
            rule = TransferRule(
                from_stop=from_stop,
                to_stop=to_stop,
                transfer_type=_optional(getattr(row, "transfer_type", None)) or "0",
                min_transfer_time=_number(getattr(row, "min_transfer_time", None)),
                min_walk_time=_number(getattr(row, "min_walk_time", None)),
                from_trip_id=_optional(getattr(row, "from_trip_id", None)),
                to_trip_id=_optional(getattr(row, "to_trip_id", None)),
                from_route_id=_optional(getattr(row, "from_route_id", None)),
                to_route_id=_optional(getattr(row, "to_route_id", None)),
                row_number=index,
            )
            for a in actual_stops(from_stop):
                for b in actual_stops(to_stop):
                    pair_rules[(a, b)].append(rule)
                    if rule.min_walk_time is not None:
                        physical[(a, b)] = min(physical.get((a, b), math.inf), rule.min_walk_time)
                    elif a != b and (a, b) not in physical:
                        sec = pathway_time(a, b)
                        if sec is not None:
                            physical[(a, b)] = sec
                        elif rule.transfer_type not in {"3", "4"}:
                            cross_stop_rules_without_physical += 1
                    if rule.transfer_type == "4" and rule.to_trip_id:
                        type4_to_trip[rule.to_trip_id].append((a, b, rule))

        for rules in pair_rules.values():
            rules.sort(key=lambda rule: (-rule.specificity, rule.row_number))

        stats = {
            "transfer_rule_rows": int(len(transfers)),
            "transfer_type_counts": {
                str(k): int(v) for k, v in transfers["transfer_type"].fillna("0").value_counts().items()
            },
            "trip_specific_transfer_rows": int(
                transfers.get("from_trip_id", pd.Series(dtype=str)).notna().sum()
                + transfers.get("to_trip_id", pd.Series(dtype=str)).notna().sum()
                - (
                    transfers.get("from_trip_id", pd.Series(dtype=str)).notna()
                    & transfers.get("to_trip_id", pd.Series(dtype=str)).notna()
                ).sum()
            ),
            "pathway_rows": 0 if pathways is None else int(len(pathways)),
            "pathway_edges_with_usable_time": int(pathway_edges_used),
            "pathway_parent_pairs": int(pathway_parent_pairs),
            "default_120s_parent_pairs": int(default_parent_pairs),
            "cross_stop_rules_without_physical_path_skipped": int(cross_stop_rules_without_physical),
            "min_walk_time_semantics": "MBTA_EXTENSION_PHYSICAL_WALK_SECONDS",
            "min_transfer_time_semantics": "GTFS_STANDARD_TOTAL_CONNECTION_ALLOWANCE_NOT_ADDED_TO_WALK",
        }
        return cls(dict(pair_rules), physical, dict(type4_to_trip), stats)

    def rule_for(
        self,
        from_stop: str,
        to_stop: str,
        from_trip: str,
        from_route: str,
        to_trip: str,
        to_route: str,
    ) -> TransferRule | None:
        applicable = [
            rule
            for rule in self.pair_rules.get((from_stop, to_stop), [])
            if rule.applies(from_trip, from_route, to_trip, to_route)
        ]
        if not applicable:
            return None
        best = max(rule.specificity for rule in applicable)
        return min((rule for rule in applicable if rule.specificity == best), key=lambda rule: rule.row_number)

    def candidate_origins(self, destination: str) -> tuple[str, ...]:
        return tuple(sorted(set(self.incoming.get(destination, ())) | {destination}))

    def physical_time(self, origin: str, destination: str, rule: TransferRule | None) -> float | None:
        if origin == destination:
            return 0.0
        if rule is not None and rule.min_walk_time is not None:
            return float(rule.min_walk_time)
        value = self.physical_seconds.get((origin, destination))
        return None if value is None or not math.isfinite(value) else float(value)

    def in_seat_sources(self, connection: Connection) -> Iterable[tuple[str, TransferRule]]:
        for origin, destination, rule in self.type4_to_trip.get(connection.trip_id, []):
            if destination == connection.from_stop and rule.to_trip_id == connection.trip_id:
                yield origin, rule


class FarePolicy:
    """Small Fare v2 evaluator for unambiguous generic adult CharlieCard legs."""

    def __init__(
        self,
        products: pd.DataFrame,
        leg_rules: pd.DataFrame,
        transfer_rules: pd.DataFrame,
    ) -> None:
        self.medium = "charliecard"
        p = products[products["fare_media_id"].eq(self.medium)].copy()
        p["amount"] = pd.to_numeric(p["amount"], errors="coerce")
        self.product_amount = p.groupby("fare_product_id")["amount"].first().to_dict()
        self.product_currency = p.groupby("fare_product_id")["currency"].first().to_dict()
        eligible = leg_rules[leg_rules["fare_product_id"].isin(self.product_amount)].copy()
        eligible = eligible[~eligible.get("transfer_only", pd.Series(index=eligible.index, dtype=str)).eq("1")]
        self.network_leg: dict[str, tuple[str, str]] = {}
        for network, group in eligible.groupby("network_id", dropna=True):
            if group.empty:
                continue
            rank_cols = [
                col for col in ("from_area_id", "to_area_id", "from_timeframe_group_id", "to_timeframe_group_id")
                if col in group
            ]
            group = group.assign(_specific=group[rank_cols].notna().sum(axis=1))
            min_specific = int(group["_specific"].min())
            generic = group[group["_specific"].eq(min_specific)].sort_values(["leg_group_id", "fare_product_id"])
            pairs = generic[["leg_group_id", "fare_product_id"]].drop_duplicates()
            if len(pairs) == 1:
                row = pairs.iloc[0]
                self.network_leg[str(network)] = (str(row.leg_group_id), str(row.fare_product_id))
        self.transfer_rules = transfer_rules.copy()
        self.stats = {
            "fare_medium": self.medium,
            "generic_network_leg_mappings": {
                key: {"leg_group_id": value[0], "fare_product_id": value[1]}
                for key, value in sorted(self.network_leg.items())
            },
            "fare_transfer_rule_rows": int(len(transfer_rules)),
        }

    @classmethod
    def from_gtfs_zip(cls, path: Path) -> "FarePolicy":
        with zipfile.ZipFile(path) as zf:
            products = pd.read_csv(zf.open("fare_products.txt"), dtype=str)
            leg_rules = pd.read_csv(zf.open("fare_leg_rules.txt"), dtype=str)
            transfer_rules = pd.read_csv(zf.open("fare_transfer_rules.txt"), dtype=str)
        return cls(products, leg_rules, transfer_rules)

    @staticmethod
    def _duration_seconds(rule: pd.Series, previous: dict, current: dict) -> float:
        kind = _optional(rule.get("duration_limit_type"))
        if kind == "0":
            return current["arrival"] - previous["departure"]
        if kind == "1":
            return current["departure"] - previous["departure"]
        if kind == "2":
            return current["departure"] - previous["arrival"]
        if kind == "3":
            return current["arrival"] - previous["arrival"]
        return 0.0

    def _transfer_rule(self, previous: dict, current: dict) -> pd.Series | None:
        candidates = self.transfer_rules[
            self.transfer_rules["from_leg_group_id"].eq(previous["leg_group_id"])
            & self.transfer_rules["to_leg_group_id"].eq(current["leg_group_id"])
        ].copy()
        if candidates.empty:
            return None
        held = previous["fare_product_id"]
        candidates = candidates[
            candidates["filter_fare_product_id"].isna()
            | candidates["filter_fare_product_id"].eq(held)
        ]
        valid = []
        for _, rule in candidates.iterrows():
            limit = _number(rule.get("duration_limit"))
            if limit is None or self._duration_seconds(rule, previous, current) <= limit:
                valid.append(rule)
        if not valid:
            return None
        valid.sort(
            key=lambda row: (
                0 if _optional(row.get("filter_fare_product_id")) else 1,
                float("inf") if _number(row.get("duration_limit")) is None else _number(row.get("duration_limit")),
            )
        )
        return valid[0]

    def price(self, chain: list[dict]) -> dict[str, Any]:
        rides = [state for state in chain if state["kind"] == "ride"]
        boarding_rides = [state for state in rides if state.get("new_boarding")]
        legs: list[dict[str, Any]] = []
        for state in boarding_rides:
            c: Connection = state["connection"]
            mapping = self.network_leg.get(c.network_id)
            if mapping is None:
                return {
                    "fare_usd": math.nan,
                    "fare_rule": "unknown_no_unambiguous_gtfs_fares_v2_charliecard_leg",
                    "fare_trace": json.dumps({"unsupported_network_id": c.network_id}, sort_keys=True),
                    "fare_product_ids": "",
                    "fare_medium": self.medium,
                }
            leg_group, product = mapping
            amount = self.product_amount.get(product)
            if amount is None or self.product_currency.get(product) != "USD":
                return {
                    "fare_usd": math.nan,
                    "fare_rule": "unknown_non_usd_or_missing_fare_product",
                    "fare_trace": json.dumps({"fare_product_id": product}, sort_keys=True),
                    "fare_product_ids": product,
                    "fare_medium": self.medium,
                }
            legs.append(
                {
                    "leg_group_id": leg_group,
                    "fare_product_id": product,
                    "amount": float(amount),
                    "departure": c.dep,
                    "arrival": c.arr,
                    "network_id": c.network_id,
                }
            )
        if not legs:
            return {
                "fare_usd": math.nan,
                "fare_rule": "unknown_no_boarding_fare_leg",
                "fare_trace": "[]",
                "fare_product_ids": "",
                "fare_medium": self.medium,
            }

        total = legs[0]["amount"]
        trace: list[dict[str, Any]] = [{"action": "initial_leg", **legs[0], "running_total": total}]
        products = [legs[0]["fare_product_id"]]
        for previous, current in zip(legs[:-1], legs[1:]):
            rule = self._transfer_rule(previous, current)
            if rule is None:
                total += current["amount"]
                trace.append({"action": "no_transfer_rule_add_to_leg", **current, "running_total": total})
                products.append(current["fare_product_id"])
                continue
            transfer_product = _optional(rule.get("fare_product_id"))
            transfer_amount = 0.0 if transfer_product is None else self.product_amount.get(transfer_product)
            if transfer_amount is None:
                return {
                    "fare_usd": math.nan,
                    "fare_rule": "unknown_transfer_product_not_available_for_charliecard",
                    "fare_trace": json.dumps(trace, sort_keys=True),
                    "fare_product_ids": ";".join(products),
                    "fare_medium": self.medium,
                }
            fare_transfer_type = str(rule["fare_transfer_type"])
            if fare_transfer_type == "0":
                total += float(transfer_amount)
            elif fare_transfer_type == "1":
                total += float(transfer_amount) + current["amount"]
            elif fare_transfer_type == "2":
                total = float(transfer_amount)
            else:
                return {
                    "fare_usd": math.nan,
                    "fare_rule": "unknown_unsupported_fare_transfer_type",
                    "fare_trace": json.dumps(trace, sort_keys=True),
                    "fare_product_ids": ";".join(products),
                    "fare_medium": self.medium,
                }
            if transfer_product:
                products.append(transfer_product)
            trace.append(
                {
                    "action": f"fare_transfer_type_{fare_transfer_type}",
                    "from_leg_group_id": previous["leg_group_id"],
                    "to_leg_group_id": current["leg_group_id"],
                    "transfer_product": transfer_product,
                    "transfer_amount": transfer_amount,
                    "running_total": total,
                }
            )
        return {
            "fare_usd": float(total),
            "fare_rule": "gtfs_fares_v2_adult_charliecard_selected_itinerary",
            "fare_trace": json.dumps(trace, sort_keys=True, separators=(",", ":")),
            "fare_product_ids": ";".join(products),
            "fare_medium": self.medium,
        }


def transit_route(
    departure: int,
    connections: list[Connection],
    access: dict[str, float],
    egress: dict[str, float],
    transfer_policy: TransferPolicy,
    fare_policy: FarePolicy | None,
    *,
    search_end: int,
) -> dict[str, Any]:
    """Earliest-arrival search that retains ridden state separately from access."""
    states: list[dict[str, Any]] = []
    offboard: dict[str, dict[str | None, int]] = defaultdict(dict)
    onboard: dict[tuple[str, str, int], int] = {}
    onboard_trip_stop: dict[tuple[str, str], list[int]] = defaultdict(list)

    def add_state(
        stop: str,
        at: float,
        kind: str,
        prev: int | None,
        *,
        walk_cum: float,
        boardings: int,
        **payload: Any,
    ) -> int:
        sid = len(states)
        states.append(
            {
                "stop": stop,
                "at": float(at),
                "kind": kind,
                "prev": prev,
                "walk_seconds_cum": float(walk_cum),
                "boardings": int(boardings),
                **payload,
            }
        )
        return sid

    def keep_offboard(stop: str, last_trip: str | None, sid: int) -> None:
        old = offboard[stop].get(last_trip)
        score = (states[sid]["at"], states[sid]["boardings"], states[sid]["walk_seconds_cum"])
        if old is None:
            offboard[stop][last_trip] = sid
        else:
            old_score = (states[old]["at"], states[old]["boardings"], states[old]["walk_seconds_cum"])
            if score < old_score:
                offboard[stop][last_trip] = sid

    for stop, sec in access.items():
        if not math.isfinite(float(sec)) or sec < 0:
            continue
        sid = add_state(
            stop,
            departure + float(sec),
            "access_walk",
            None,
            walk_cum=float(sec),
            boardings=0,
            seconds=float(sec),
            has_ridden=False,
            last_trip=None,
            last_route=None,
        )
        keep_offboard(stop, None, sid)

    for c in connections:
        if c.dep < departure or c.dep > search_end:
            continue
        candidates: list[tuple[tuple[float, ...], int, bool, float, bool, int | None]] = []

        # Stay on the same scheduled trip, including through stops where boarding
        # or alighting is prohibited.
        same_sid = onboard.get((c.trip_id, c.from_stop, c.from_seq))
        if same_sid is not None and states[same_sid]["at"] <= c.dep:
            s = states[same_sid]
            candidates.append(
                ((s["boardings"], s["walk_seconds_cum"], s["at"], 0.0), same_sid, False, 0.0, True, None)
            )

        # GTFS type 4 explicitly links two trips as an in-seat continuation.
        for origin, rule in transfer_policy.in_seat_sources(c):
            if not rule.from_trip_id:
                continue
            for sid in onboard_trip_stop.get((rule.from_trip_id, origin), []):
                s = states[sid]
                if s["at"] <= c.dep:
                    candidates.append(
                        ((s["boardings"], s["walk_seconds_cum"], s["at"], 1.0), sid, False, 0.0, True, rule.row_number)
                    )

        # New boarding.  Access labels are only considered at their exact stop;
        # transfer walking is available only after at least one real ride.
        if c.pickup_allowed:
            for origin in transfer_policy.candidate_origins(c.from_stop):
                for last_trip, sid in offboard.get(origin, {}).items():
                    s = states[sid]
                    if last_trip is None:
                        if origin != c.from_stop:
                            continue
                        rule = None
                        physical = 0.0
                        last_route = ""
                    else:
                        last_route = str(s.get("last_route") or "")
                        rule = transfer_policy.rule_for(
                            origin,
                            c.from_stop,
                            str(last_trip),
                            last_route,
                            c.trip_id,
                            c.route_id,
                        )
                        if rule is not None and rule.transfer_type in {"3", "4"}:
                            continue
                        physical_value = transfer_policy.physical_time(origin, c.from_stop, rule)
                        if physical_value is None:
                            continue
                        physical = float(physical_value)
                    ready_after_walk = s["at"] + physical
                    minimum_ready = ready_after_walk
                    if rule is not None and rule.transfer_type == "2":
                        minimum_ready = max(minimum_ready, s["at"] + float(rule.min_transfer_time or 0.0))
                    if c.dep < minimum_ready:
                        continue
                    score = (
                        s["boardings"] + 1,
                        s["walk_seconds_cum"] + physical,
                        s["at"],
                        float(rule.row_number) if rule is not None else -1.0,
                    )
                    candidates.append((score, sid, True, physical, False, None if rule is None else rule.row_number))

        if not candidates:
            continue
        _, prev_sid, new_boarding, physical, in_seat, transfer_rule_row = min(candidates, key=lambda item: item[0])
        prev_state = states[prev_sid]
        ride_prev = prev_sid
        if new_boarding and physical > 0:
            ride_prev = add_state(
                c.from_stop,
                prev_state["at"] + physical,
                "transfer_walk",
                prev_sid,
                walk_cum=prev_state["walk_seconds_cum"] + physical,
                boardings=prev_state["boardings"],
                seconds=physical,
                from_stop=prev_state["stop"],
                transfer_rule_row=transfer_rule_row,
            )
        ready_at = states[ride_prev]["at"]
        wait_seconds = float(c.dep - ready_at) if new_boarding else 0.0
        same_vehicle_dwell = float(max(0, c.dep - prev_state["at"])) if in_seat else 0.0
        ride_sid = add_state(
            c.to_stop,
            c.arr,
            "ride",
            ride_prev,
            walk_cum=states[ride_prev]["walk_seconds_cum"],
            boardings=states[ride_prev]["boardings"] + (1 if new_boarding else 0),
            connection=c,
            wait_seconds=wait_seconds,
            new_boarding=new_boarding,
            in_seat_continuation=in_seat and not new_boarding,
            same_vehicle_dwell_seconds=same_vehicle_dwell,
            transfer_rule_row=transfer_rule_row,
        )
        key = (c.trip_id, c.to_stop, c.to_seq)
        old = onboard.get(key)
        if old is None or (
            states[ride_sid]["boardings"], states[ride_sid]["walk_seconds_cum"]
        ) < (
            states[old]["boardings"], states[old]["walk_seconds_cum"]
        ):
            onboard[key] = ride_sid
            onboard_trip_stop[(c.trip_id, c.to_stop)].append(ride_sid)
        if c.dropoff_allowed:
            states[ride_sid]["has_ridden"] = True
            states[ride_sid]["last_trip"] = c.trip_id
            states[ride_sid]["last_route"] = c.route_id
            keep_offboard(c.to_stop, c.trip_id, ride_sid)

    if not access or not egress:
        return {
            "status": "unknown_network_disconnected_or_unsnapped",
            "status_evidence": "empty_access_or_egress_stop_set",
        }

    destinations: list[tuple[tuple[float, ...], int, float]] = []
    for stop, sec in egress.items():
        if not math.isfinite(float(sec)) or sec < 0:
            continue
        for last_trip, sid in offboard.get(stop, {}).items():
            if last_trip is None:
                continue
            s = states[sid]
            destinations.append(
                ((s["at"] + float(sec), s["boardings"], s["walk_seconds_cum"] + float(sec)), sid, float(sec))
            )
    if not destinations:
        return {
            "status": "confirmed_unavailable_within_declared_search_limits",
            "status_evidence": "access_and_egress_exist_but_no_permitted_ride_chain_reaches_egress",
        }

    (end, _, _), sid, egress_sec = min(destinations, key=lambda item: item[0])
    chain: list[dict[str, Any]] = []
    cursor: int | None = sid
    while cursor is not None:
        chain.append(states[cursor])
        cursor = states[cursor]["prev"]
    chain.reverse()
    rides = [state for state in chain if state["kind"] == "ride"]
    if not rides:
        raise AssertionError("Available transit itinerary contains no ride")

    access_sec = sum(float(state["seconds"]) for state in chain if state["kind"] == "access_walk")
    transfer_walk_sec = sum(float(state["seconds"]) for state in chain if state["kind"] == "transfer_walk")
    wait_sec = sum(float(state.get("wait_seconds", 0.0)) for state in rides)
    in_vehicle_sec = sum(
        float(state["connection"].arr - state["connection"].dep)
        + float(state.get("same_vehicle_dwell_seconds", 0.0))
        for state in rides
    )
    boardings = sum(1 for state in rides if state.get("new_boarding"))
    overlay_ids = sorted(
        {
            item
            for state in rides
            if state["connection"].overlay_parameter_id
            for item in str(state["connection"].overlay_parameter_id).split(";")
        }
    )
    fare = (
        fare_policy.price(chain)
        if fare_policy is not None
        else {
            "fare_usd": math.nan,
            "fare_rule": "unknown_no_fare_policy",
            "fare_trace": "[]",
            "fare_product_ids": "",
            "fare_medium": "unknown",
        }
    )
    result = {
        "status": "available",
        "status_evidence": "at_least_one_permitted_gtfs_ride_and_egress",
        "arrival": int(round(end)),
        "total_seconds": float(end - departure),
        "walk_seconds": access_sec + transfer_walk_sec + egress_sec,
        "access_walk_seconds": access_sec,
        "transfer_walk_seconds": transfer_walk_sec,
        "egress_walk_seconds": egress_sec,
        "wait_seconds": wait_sec,
        "in_vehicle_seconds": in_vehicle_sec,
        "boardings": int(boardings),
        "transfers": max(0, int(boardings) - 1),
        "ride_segment_count": int(len(rides)),
        "overlay_parameter_ids": overlay_ids,
        "chain": chain,
        **fare,
    }
    account_error = abs(
        result["total_seconds"]
        - (result["walk_seconds"] + result["wait_seconds"] + result["in_vehicle_seconds"])
    )
    result["time_account_error_seconds"] = float(account_error)
    return result
