"""Exact multi-egress split of semantic_transit.transit_route.

Generated from that function by checks/build_semantic_batch.py. The label scan
is independent of the destination egress map; all terminal path/fare semantics
are the original source statements. Regression tests compare full outputs.
"""
from __future__ import annotations
import json
import math
from collections import defaultdict
from typing import Any
from semantic_transit import Connection, TransferPolicy, FarePolicy


def build_search(departure: int, connections: list[Connection], access: dict[str,float],
                 transfer_policy: TransferPolicy, *, search_end: int):
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

    return states,offboard


def finish_search(departure: int, access: dict[str,float], egress: dict[str,float],
                  fare_policy: FarePolicy | None, states, offboard):
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


def transit_route_many(departure: int, connections: list[Connection], access: dict[str,float],
                       egress_by_key: dict[str,dict[str,float]], transfer_policy: TransferPolicy,
                       fare_policy: FarePolicy | None, *, search_end: int):
    states,offboard=build_search(departure,connections,access,transfer_policy,search_end=search_end)
    return {key:finish_search(departure,access,egress,fare_policy,states,offboard)
            for key,egress in egress_by_key.items()}
