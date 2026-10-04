"""Route walk access on a conservative, unrestricted subset of official 3D links."""
from __future__ import annotations

import csv
import heapq
import json
import math
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
R1 = HERE.parent / "hong_kong_gmns_pilot_r1"
OUT = HERE / "phase_b"


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write(name, data):
    with (OUT / name).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(data[0]))
        w.writeheader()
        w.writerows(data)


def meters(p, q):
    return math.hypot((p[0] - q[0]) * 103200, (p[1] - q[1]) * 110850)


features = []
for i in range(4):
    features += json.loads((R1 / f"raw/pedestrian_{i}.json").read_text(encoding="utf-8"))["features"]
allowed = [
    x for x in features
    if x["attributes"].get("Enabled") == 1
    and x["attributes"].get("Direction") == 0
    and x["attributes"].get("AccessTimeID") is None
    and x["attributes"].get("FloorID") is None
]
adj = defaultdict(list)
for x in allowed:
    length = float(x["attributes"].get("Shape__Length") or 0)
    paths = x["geometry"].get("paths", [])
    for path in paths:
        if len(path) < 2 or length <= 0:
            continue
        a = tuple(round(v, 9) for v in path[0][:2])
        b = tuple(round(v, 9) for v in path[-1][:2])
        if a == b:
            continue
        adj[a].append((b, length))
        adj[b].append((a, length))
nodes = list(adj)
zones = [r for r in rows(R1 / "instance/zone.csv") if r["super_zone"]]
stops = rows(R1 / "instance/transit_stops.csv")
zpoints = {z["zone_id"]: (float(z["centroid_lon"]), float(z["centroid_lat"])) for z in zones}
spoints = {s["stop_id"]: (float(s["stop_lon"]), float(s["stop_lat"])) for s in stops}


def snap(points):
    out = {}
    for key, p in points.items():
        distance, node = min((meters(p, q), q) for q in nodes)
        out[key] = (node, distance)
    return out


zs, ss = snap(zpoints), snap(spoints)


def dijkstra(source):
    distance = {source: 0.0}
    heap = [(0.0, source)]
    while heap:
        du, u = heapq.heappop(heap)
        if du > distance[u] + 1e-9:
            continue
        for v, length in adj[u]:
            nd = du + length
            if nd < distance.get(v, math.inf):
                distance[v] = nd
                heapq.heappush(heap, (nd, v))
    return distance


zz, zstop = [], []
status = defaultdict(int)
for oz in sorted(zpoints, key=int):
    start, start_snap = zs[oz]
    distance = dijkstra(start)
    for dz in sorted(zpoints, key=int):
        if oz == dz:
            continue
        end, end_snap = zs[dz]
        route = distance.get(end)
        if route is not None and max(start_snap, end_snap) <= 100:
            length, kind = start_snap + route + end_snap, "ROUTED_OFFICIAL_UNRESTRICTED_SUBGRAPH"
        else:
            length, kind = meters(zpoints[oz], zpoints[dz]) * 1.3, "LABELED_STRAIGHT_LINE_FALLBACK_1_3"
        status[kind] += 1
        zz.append(dict(o_zone_id=oz, d_zone_id=dz, walk_distance_m=length,
                       walk_time_min=length / 75, status=kind,
                       origin_snap_m=start_snap, destination_snap_m=end_snap))
    for sid in sorted(spoints, key=int):
        end, end_snap = ss[sid]
        route = distance.get(end)
        if route is not None and max(start_snap, end_snap) <= 100:
            length, kind = start_snap + route + end_snap, "ROUTED_OFFICIAL_UNRESTRICTED_SUBGRAPH"
        else:
            length, kind = meters(zpoints[oz], spoints[sid]) * 1.3, "LABELED_STRAIGHT_LINE_FALLBACK_1_3"
        status[kind] += 1
        zstop.append(dict(zone_id=oz, stop_id=sid, walk_distance_m=length,
                          walk_time_min=length / 75, status=kind,
                          zone_snap_m=start_snap, stop_snap_m=end_snap))
write("walk_zone_zone.csv", zz)
write("walk_zone_stop.csv", zstop)
report = {
    "official_pedestrian_features_queried": len(features),
    "conservative_unrestricted_features_used": len(allowed),
    "pedestrian_endpoint_nodes": len(nodes),
    "zone_zone_pairs": len(zz), "zone_stop_pairs": len(zstop),
    "status_counts": dict(status),
    "walking_speed_m_per_min": 75,
    "straight_line_fallback_detour_factor": 1.3,
    "snap_limit_m": 100,
    "exclusions": "Disabled, direction-coded, time-restricted, and floor-coded features excluded because the present cost model cannot verify their direction, opening hours, or vertical access.",
    "limitation": "The first/last snap remains a straight connector; graph paths are not proof of legal or barrier-free access. Fallback costs are explicitly labeled.",
}
(OUT / "WALK_ROUTING_QUALITY.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
