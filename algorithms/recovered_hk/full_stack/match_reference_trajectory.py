"""Private Viterbi link-state map match of the bounded UrbanNav reference trace."""
import csv
import heapq
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

R = Path(__file__).resolve().parent
B = R / "phase_b"
PRIVATE = B / "private"
PRIVATE.mkdir(exist_ok=True)
R1 = R.parent / "hong_kong_gmns_pilot_r1/instance"


def rows(p):
    with p.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


old = rows(R1 / "trajectory_points.csv")
road = {r["link_id"]: r for r in rows(R / "phase_a/instance/link.csv")
        if r["mcl_link_class"] == "physical"}
allow = defaultdict(list)
for r in rows(R / "phase_a/turn_aware_movement_edges.csv"):
    allow[r["from_link_id"]].append(r["to_link_id"])
LON = 111320 * math.cos(math.radians(22.3035))
LAT = 111320
links = {}
grid = defaultdict(set)
cell = .001
for lid, r in road.items():
    xy = [tuple(map(float, q.split())) for q in r["geometry"][11:-1].split(",")]
    xy = [(x * LON, y * LAT) for x, y in xy]
    cumulative = [0.]
    for a, b in zip(xy, xy[1:]):
        cumulative.append(cumulative[-1] + math.dist(a, b))
    links[lid] = (xy, cumulative, float(r["length"]))
    longitudes = [x / LON for x, _ in xy]
    latitudes = [y / LAT for _, y in xy]
    for gx in range(math.floor((min(longitudes)-.0005)/cell), math.floor((max(longitudes)+.0005)/cell)+1):
        for gy in range(math.floor((min(latitudes)-.0005)/cell), math.floor((max(latitudes)+.0005)/cell)+1):
            grid[gx, gy].add(lid)


def project(px, py, lid):
    xy, cum, length = links[lid]
    best = (math.inf, 0., 0.)
    for k, (a, b) in enumerate(zip(xy, xy[1:])):
        dx, dy = b[0]-a[0], b[1]-a[1]
        sq = dx*dx + dy*dy
        t = max(0., min(1., ((px-a[0])*dx+(py-a[1])*dy)/sq)) if sq else 0.
        d = math.hypot(px-a[0]-t*dx, py-a[1]-t*dy)
        if d < best[0]:
            best = (d, (cum[k] + t*math.sqrt(sq)) / max(cum[-1], 1) * length,
                    math.atan2(dy, dx))
    return best


points = []
for p in old:
    x, y = float(p["longitude"])*LON, float(p["latitude"])*LAT
    gx, gy = math.floor(float(p["longitude"])/cell), math.floor(float(p["latitude"])/cell)
    near = set().union(*(grid.get((gx+dx, gy+dy), set()) for dx in (-1,0,1) for dy in (-1,0,1)))
    options = sorted(((project(x,y,lid), lid) for lid in near), key=lambda q:q[0][0])
    options = [(lid, d, along, angle) for (d,along,angle),lid in options if d<=40][:8]
    points.append({"source":p,"xy":(x,y),"candidates":options})

# Cache one bounded directed link-state search per candidate source. Each
# intermediate link length is counted once; target link offset is added later.
paths = {}
def between(a, b):
    if a == b:
        return (0., [])
    if a not in paths:
        best = {a: (0., [])}
        heap = [(0., a)]
        while heap:
            d, u = heapq.heappop(heap)
            if d != best[u][0]:
                continue
            for v in allow.get(u, ()):
                nd = d + (0 if u == a else links[u][2])
                if nd > 550:
                    continue
                if nd < best.get(v, (math.inf,))[0]:
                    best[v] = (nd, best[u][1] + ([] if u == a else [u]))
                    heapq.heappush(heap, (nd, v))
        paths[a] = best
    return paths[a].get(b)


layers = []
for i, pt in enumerate(points):
    p = pt["source"]
    xy = pt["xy"]
    prev = points[i-1] if i else None
    dt = float(p["utc_seconds"]) - float(prev["source"]["utc_seconds"]) if prev else 0.
    displacement = math.dist(xy, prev["xy"]) if prev else 0.
    prev_layer = layers[-1] if layers else {}
    states = {}
    for lid, d, along, angle in pt["candidates"]:
        emission = .5 * (d / 8.)**2
        if displacement > 2 and prev:
            heading = math.atan2(xy[1]-prev["xy"][1], xy[0]-prev["xy"][0])
            emission += 3 * max(0., -math.cos(heading-angle))
        if prev_layer:
            oldbest = min((s[0] for s in prev_layer.values()), default=0.)
            score, bp, route, chain = oldbest + 10. + emission, None, 0., []
        else:
            score, bp, route, chain = emission, None, 0., []
        if dt > 0 and dt <= 15:
            for oldlid, (prior, _, _, _, oldalong) in prev_layer.items():
                path = between(oldlid, lid)
                if path is None:
                    continue
                if oldlid == lid:
                    route_dist = along - oldalong
                    if route_dist < -8:
                        continue
                    route_dist = max(0., route_dist)
                else:
                    route_dist = links[oldlid][2] - oldalong + path[0] + along
                if route_dist > min(550., max(80., dt*40.+40.)):
                    continue
                penalty = abs(route_dist-displacement)/12. + max(0., route_dist/dt-30.)/2.
                candidate = prior + emission + penalty
                if candidate < score:
                    score, bp, route, chain = candidate, oldlid, route_dist, path[1]
        states[lid] = (score, bp, route, chain, along)
    layers.append(states)

chosen = [None] * len(points)
breaks = set()
i = len(points)-1
while i >= 0:
    if not layers[i]:
        breaks.add(i); i -= 1; continue
    lid = min(layers[i], key=lambda k: layers[i][k][0])
    while i >= 0 and lid is not None and lid in layers[i] and chosen[i] is None:
        chosen[i] = lid
        nxt = layers[i][lid][1]
        if nxt is None:
            breaks.add(i)
        i -= 1
        lid = nxt

output = []
valid_route_m = 0.
invalid_transitions = 0
direction_adverse = 0
for i, lid in enumerate(chosen):
    source = points[i]["source"]
    item = next(((d, a, h) for ll,d,a,h in points[i]["candidates"] if ll == lid), None)
    if lid is None or item is None:
        output.append({"point_index":i,"utc_iso":source["utc_iso"],"matched_link_id":"",
                       "distance_m":"","along_link_m":"","turn_validity":"UNMATCHED",
                       "route_distance_from_previous_m":"","break_before":True,
                       "r1_heuristic_link_id":source["gmns_link_id"]})
        continue
    d, along, angle = item
    if i>0 and chosen[i-1] is not None and i not in breaks:
        state = layers[i][lid]
        route = state[2]
        valid_route_m += route
        if lid != chosen[i-1] and between(chosen[i-1],lid) is None:
            invalid_transitions += 1
        validity = "DIRECTED_PATH_ALLOWED"
    else:
        route = None
        validity = "BREAK_OR_START"
    if i>0 and math.dist(points[i]["xy"],points[i-1]["xy"])>2:
        h = math.atan2(points[i]["xy"][1]-points[i-1]["xy"][1],points[i]["xy"][0]-points[i-1]["xy"][0])
        adverse = math.cos(h-angle)<0
        direction_adverse += adverse
    output.append({"point_index":i,"utc_iso":source["utc_iso"],"matched_link_id":lid,
                   "distance_m":round(d,3),"along_link_m":round(along,3),
                   "turn_validity":validity,"route_distance_from_previous_m":round(route,3) if route is not None else "",
                   "break_before":i in breaks,"r1_heuristic_link_id":source["gmns_link_id"]})
with (PRIVATE/"urban_nav_viterbi_points_PRIVATE.csv").open("w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(output[0]));w.writeheader();w.writerows(output)

res = [float(x["distance_m"]) for x in output if x["matched_link_id"]]
r1res = [float(x["link_distance_m"]) for x in old if x["link_distance_m"]]
time_span = float(old[-1]["utc_seconds"]) - float(old[0]["utc_seconds"])
summary = {"status":"PRIVATE_REFERENCE_TOPOLOGY_EVIDENCE_ONLY",
           "method":"Viterbi candidate link-state sequence with emission distance/direction, directed official turn graph transition, bounded shortest route, explicit restart; fixed engineering penalties",
           "input":"R1 private UrbanNav SPAN-CPT+IE reference positions (not raw GNSS)",
           "point_count":len(points),"matched_points":len(res),"unmatched_points":len(points)-len(res),
           "median_residual_m":statistics.median(res) if res else None,
           "p95_residual_m":sorted(res)[int(.95*(len(res)-1))] if res else None,
           "r1_heuristic_median_residual_m":statistics.median(r1res),
           "r1_heuristic_p95_residual_m":sorted(r1res)[int(.95*(len(r1res)-1))],
           "r1_heuristic_continuity_breaks":sum(x["continuity"]=="discontinuity" for x in old),
           "viterbi_breaks_or_starts":len(breaks),
           "direction_adverse_points_with_gt2m_motion":direction_adverse,
           "invalid_reconstructed_directed_transitions":invalid_transitions,
           "continuous_traversal_route_length_m":valid_route_m,
           "reference_time_span_s":time_span,
           "route_length_limit":"sum of directed traversals within matched segments; restarts excluded",
           "point_level_derivative":"PRIVATE; not in public candidates",
           "inference_limit":"One 2021 research-vehicle ground-truth trace; no representative speed, OD, mode share, or networkwide calibration claim"}
(B/"TRAJECTORY_MAP_MATCH_SUMMARY.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
print(json.dumps(summary,indent=2))
