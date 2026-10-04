"""Compute OD-specific road, same-trip GTFS transit, and walk costs."""
from __future__ import annotations

import csv
import heapq
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
A = HERE / "phase_a"
B = HERE / "phase_b"


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write(name, data):
    with (B / name).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(data[0]))
        w.writeheader()
        w.writerows(data)


zone_nodes = {r["zone_id"]: r for r in rows(A / "static_input/zone_to_expanded_node.csv")}
road_arcs = rows(A / "static_input/turn_expanded_links.csv")
crosswalk = {r["expanded_link_id"]: r for r in rows(A / "static_input/expanded_network_crosswalk.csv")}
road_adjacency = defaultdict(list)
for r in road_arcs:
    road_adjacency[int(r["from_node_id"])].append(
        (int(r["to_node_id"]), float(r["vdf_fftt"]), r["link_id"])
    )
physical_length = {r["link_id"]: float(r["length"]) for r in rows(A / "instance/link.csv")
                   if r["mcl_link_class"] == "physical"}
walk_zz = {(r["o_zone_id"], r["d_zone_id"]): r for r in rows(B / "walk_zone_zone.csv")}
walk_zs = defaultdict(list)
for r in rows(B / "walk_zone_stop.csv"):
    walk_zs[r["zone_id"]].append(r)


def road_dijkstra(origin):
    distance = {origin: 0.0}
    prev = {}
    heap = [(0.0, origin)]
    while heap:
        du, u = heapq.heappop(heap)
        if du > distance[u] + 1e-12:
            continue
        for v, weight, lid in road_adjacency[u]:
            nd = du + weight
            if nd < distance.get(v, math.inf) - 1e-12:
                distance[v] = nd
                prev[v] = (u, lid)
                heapq.heappush(heap, (nd, v))
    return distance, prev


headway = {r["route_id"]: r for r in rows(B / "gtfs_route_headway.csv")}
direct = rows(B / "gtfs_direct_ride_pairs.csv")
transit_adj = defaultdict(list)
for r in direct:
    route, sa, sb = r["route_id"], r["from_stop_id"], r["to_stop_id"]
    ride, fare = float(r["median_in_vehicle_min"]), float(r["fare_hkd"])
    wait = float(headway[route]["expected_wait_min"])
    # All costs are nonnegative generalized minutes. Fare uses an engineering
    # value of time of HKD 30/hour (2 minutes/HKD), not a calibrated coefficient.
    for board_state in (0, 1):
        transfer = 2.0 if board_state else 0.0
        transit_adj[(sa, board_state)].append(
            ((sb, 1), ride + wait + 2 * fare + transfer,
             dict(route_id=route, from_stop_id=sa, to_stop_id=sb,
                  in_vehicle_min=ride, wait_min=wait, fare_hkd=fare,
                  transfer_penalty_min=transfer, fare_grade=r["fare_grade"],
                  headway_grade=headway[route]["grade"]))
        )


def transit_dijkstra(zone):
    access_candidates = sorted(walk_zs[zone], key=lambda r: (float(r["walk_time_min"]), int(r["stop_id"])))
    access_candidates = [r for r in access_candidates if float(r["walk_distance_m"]) <= 600][:12] or access_candidates[:3]
    distance, prev, source = {}, {}, {}
    heap = []
    for r in access_candidates:
        key = (r["stop_id"], 0)
        val = float(r["walk_time_min"])
        if val < distance.get(key, math.inf):
            distance[key] = val
            source[key] = r
            heapq.heappush(heap, (val, key))
    while heap:
        du, u = heapq.heappop(heap)
        if du > distance[u] + 1e-12:
            continue
        for v, weight, detail in transit_adj[u]:
            nd = du + weight
            if nd < distance.get(v, math.inf) - 1e-12:
                distance[v] = nd
                prev[v] = (u, detail)
                heapq.heappush(heap, (nd, v))
    return distance, prev, source, len(access_candidates)


costs, statistics = [], Counter()
for oz in sorted(zone_nodes, key=int):
    o_node = int(zone_nodes[oz]["origin_node_id"])
    rd, rp = road_dijkstra(o_node)
    td, tp, ts, candidate_count = transit_dijkstra(oz)
    statistics["transit_access_candidates_total"] += candidate_count
    for dz in sorted(zone_nodes, key=int):
        if oz == dz:
            continue
        d_node = int(zone_nodes[dz]["destination_node_id"])
        if d_node not in rd:
            raise RuntimeError(f"turn-aware road OD unreachable {oz}->{dz}")
        drive_time = rd[d_node]
        path = []
        u = d_node
        while u != o_node:
            if u not in rp:
                raise RuntimeError("broken road predecessor")
            parent, lid = rp[u]
            path.append(lid)
            u = parent
        path.reverse()
        physical_path = [lid for lid in path if lid in physical_length]
        drive_distance = sum(physical_length[lid] for lid in physical_path)
        drive_generalized = drive_time + 6.0 + 0.004 * drive_distance
        walk = walk_zz[oz, dz]
        walk_time = float(walk["walk_time_min"])
        # Destination egress is a zone-to-stop cost on the undirected,
        # unrestricted pedestrian subset; its exact status is retained.
        best = None
        for r in walk_zs[dz]:
            key = (r["stop_id"], 1)
            if key not in td or float(r["walk_distance_m"]) > 600:
                continue
            value = td[key] + float(r["walk_time_min"])
            if best is None or value < best[0]:
                best = (value, key, r)
        if best is None:
            for r in sorted(walk_zs[dz], key=lambda q: float(q["walk_time_min"]))[:3]:
                key = (r["stop_id"], 1)
                if key in td:
                    value = td[key] + float(r["walk_time_min"])
                    if best is None or value < best[0]:
                        best = (value, key, r)
        if best is None:
            transit = dict(transit_generalized_min="", transit_in_vehicle_min="",
                           transit_wait_min="", transit_access_min="", transit_egress_min="",
                           transit_fare_hkd="", transit_transfers="", transit_boardings="",
                           transit_status="NO_PILOT_GTFS_PATH", transit_access_status="",
                           transit_egress_status="", transit_route_ids="")
            statistics["unserved_transit_pairs"] += 1
        else:
            generalized, end, egress = best
            legs = []
            u = end
            while u in tp:
                parent, detail = tp[u]
                legs.append(detail)
                u = parent
            legs.reverse()
            if not legs or u not in ts:
                raise RuntimeError("broken transit predecessor")
            access = ts[u]
            transit = dict(transit_generalized_min=generalized,
                           transit_in_vehicle_min=sum(x["in_vehicle_min"] for x in legs),
                           transit_wait_min=sum(x["wait_min"] for x in legs),
                           transit_access_min=access["walk_time_min"],
                           transit_egress_min=egress["walk_time_min"],
                           transit_fare_hkd=sum(x["fare_hkd"] for x in legs),
                           transit_transfers=len(legs) - 1, transit_boardings=len(legs),
                           transit_status="GTFS_SAME_TRIP_RIDE_PLUS_WALK_ACCESS_PROXY",
                           transit_access_status=access["status"],
                           transit_egress_status=egress["status"],
                           transit_route_ids="|".join(x["route_id"] for x in legs))
            statistics["served_transit_pairs"] += 1
            statistics["transit_transfer_pairs"] += len(legs) > 1
        costs.append(dict(o_zone_id=oz, d_zone_id=dz,
                          o_access_node_id=o_node, d_access_node_id=d_node,
                          drive_time_min=drive_time, drive_distance_m=drive_distance,
                          drive_physical_link_count=len(physical_path),
                          drive_generalized_min=drive_generalized,
                          drive_cost_status="TURN_AWARE_PROXY_FREE_SPEED_AND_PARKING_OPERATING_COST",
                          walk_time_min=walk_time, walk_distance_m=walk["walk_distance_m"],
                          walk_status=walk["status"], **transit))
write("mode_costs_by_od.csv", costs)
report = dict(
    od_pairs=len(costs), status_counts=dict(statistics),
    transit_direct_pairs=len(direct),
    drive_cost="free-flow turn-aware time + 6 min parking/approach + HKD 2/km at 2 min/HKD",
    transit_cost="same-GTFS-trip ride + half published/derived headway + per-leg exact published fare at 2 min/HKD + 2 min per transfer + walk access/egress",
    walk_cost="conservative pedestrian graph when routed; labeled 1.3x straight-line fallback otherwise; 75 m/min",
    limitation="No local choice calibration, crowding, parking observation, fare discount, empirical reliability, or published full walk-trip rate.",
)
(B / "MODE_COST_QUALITY.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
