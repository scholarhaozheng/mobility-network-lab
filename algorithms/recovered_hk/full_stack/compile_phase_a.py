"""Compile a graded, turn-aware Hong Kong R2 scenario from frozen R1 objects.

The graph adapter is city-specific; all assignment mathematics remains in the
accepted generic FW and Algorithm B implementations.
"""
from __future__ import annotations

import csv
import itertools
import json
import math
import shutil
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
R1 = HERE.parent / "hong_kong_gmns_pilot_r1"
OUT = HERE / "phase_a"
INST = OUT / "instance"
OUT.mkdir(exist_ok=True)
if not INST.exists():
    shutil.copytree(R1 / "instance", INST)


def read(name, root=INST):
    with (root / name).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write(name, rows, columns=None, root=OUT):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = columns or list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)


road_fields = {r["route_id"]: r for r in read("pilot_source_road_fields.csv", HERE / "raw")}
links_all = read("link.csv")
physical = [r for r in links_all if r["mcl_link_class"] == "physical"]
by_route = defaultdict(list)
incoming, outgoing = defaultdict(list), defaultdict(list)
for r in physical:
    by_route[r["source_link_id"]].append(r)
    incoming[r["to_node_id"]].append(r)
    outgoing[r["from_node_id"]].append(r)

# The official speed-limit layer covers posted exceptions; absent road routes
# use the TD's general 50 km/h limit as a legal ceiling, not measured free speed.
speed = defaultdict(list)
for _, elem in ET.iterparse(HERE / "raw/speed_limit.gml", events=("end",)):
    if not elem.tag.endswith("GenericCityObject"):
        continue
    item = {}
    for a in elem.iter():
        if a.tag.endswith(("intAttribute", "stringAttribute", "doubleAttribute")):
            item[a.attrib.get("name")] = next(
                (v.text for v in a if v.tag.endswith("value")), None
            )
    speed[item.get("ROAD_ROUTE_ID")].append(item)
    elem.clear()

speed_ev, lane_ev, cap_ev, speed_sens, lane_sens, cap_sens = [], [], [], [], [], []
for r in physical:
    rid = r["source_link_id"]
    spec = road_fields[rid]
    length = float(r["length"])
    srows = speed.get(rid, [])
    covered = min(length, sum(float(x.get("Shape_Length") or 0) for x in srows))
    fraction = covered / length
    limits = {int(x["SPEED_LIMIT"].split()[0]) for x in srows}
    if len(limits) > 1:
        raise ValueError(f"conflicting posted limits on route {rid}: {limits}")
    posted = next(iter(limits)) if limits else 50
    # Effective legal-limit time sums covered exception and general-limit
    # remainder. This is a transfer approximation when coverage is partial.
    legal_equivalent = length / (covered / posted + (length - covered) / 50)
    limit_grade = (
        "OFFICIAL_EXACT" if srows and abs(fraction - 1) <= 0.02
        else "OFFICIAL_SEGMENT_TRANSFER" if srows
        else "OFFICIAL_DEFAULT_RULE"
    )
    free_speed = legal_equivalent * 0.8  # declared engineering factor
    r.update(
        free_speed=f"{free_speed:.12g}",
        free_flow_time=f"{length / (free_speed * 1000 / 60):.12g}",
        capacity="", lanes="", vdf_alpha="0.15", vdf_beta="4",
        vdf_plf="1", free_speed_unit="km/h", capacity_unit="PCE/1h",
    )
    strategic = spec["route_num"] not in ("", "<Null>", "-99")
    lanes = 2 if strategic else 1
    cap_per_lane = 1500 if strategic else 500
    cap = lanes * cap_per_lane
    r["lanes"], r["capacity"] = str(lanes), str(cap)
    grade = "ENGINEERING_PROXY"
    speed_ev.append(dict(
        link_id=r["link_id"], source_route_id=rid,
        speed_value=free_speed, speed_unit="km/h",
        speed_source_id="TD_SPEED_LIMIT_GML" if srows else "TD_ROAD_USER_CODE_50_KMH",
        speed_source_type="posted_limit_scaled_engineering_free_speed",
        speed_match_method="source_route_id_and_length_coverage" if srows else "general_legal_limit",
        speed_match_distance_or_overlap=round(fraction, 6), speed_evidence_grade=grade,
        posted_limit_kmh=posted, posted_limit_grade=limit_grade,
        speed_limit_feature_ids="|".join(x.get("SPEED_LIMIT_ID", "") for x in srows),
        assumed_free_to_legal_speed_factor=0.8,
    ))
    lane_ev.append(dict(
        link_id=r["link_id"], source_route_id=rid,
        official_lane_count="", lanes_used=lanes, lane_evidence_grade=grade,
        lane_source_type="strategic_route_proxy" if strategic else "unclassified_urban_proxy",
        source_route_num=spec["route_num"], source_elevation=spec["elevation"],
        source_street_code=spec["street_code"],
    ))
    cap_ev.append(dict(
        link_id=r["link_id"], capacity_unit="PCE/1h", capacity_per_lane_per_hour=cap_per_lane,
        lanes_used=lanes, period_hours=1, period_capacity_pce=cap,
        capacity_source_type="TD_TPDM_design_flow_transferred_engineering_rule",
        capacity_evidence_grade=grade,
        vehicle_to_pce_assumption="1 model_vehicle=1 PCE; scenario assumption",
    ))
    for tier, factor in (("low", 0.65), ("base", 0.8), ("high", 0.95)):
        speed_sens.append(dict(link_id=r["link_id"], tier=tier, free_speed_kmh=legal_equivalent * factor))
    for tier, ln in (("low", 1), ("base", lanes), ("high", 3 if strategic else 2)):
        lane_sens.append(dict(link_id=r["link_id"], tier=tier, proxy_lanes=ln))
    for tier, cpl in (("low", 1000 if strategic else 400), ("base", cap_per_lane),
                      ("high", 1800 if strategic else 850)):
        cap_sens.append(dict(link_id=r["link_id"], tier=tier,
                             capacity_per_lane_pce_per_hour=cpl,
                             capacity_pce_per_hour=cpl * (1 if tier == "low" else lanes if tier == "base" else 3 if strategic else 2)))

write("link_speed_evidence.csv", speed_ev)
write("link_lane_evidence.csv", lane_ev)
write("link_capacity_evidence.csv", cap_ev)
write("SPEED_POLICY_SENSITIVITY.csv", speed_sens)
write("LANE_POLICY_SENSITIVITY.csv", lane_sens)
write("CAPACITY_POLICY_SENSITIVITY.csv", cap_sens)

# Current official intersection relationships guard all potential transitions,
# including exact-coordinate mixed-elevation endpoints in R1.
intersections = json.loads((HERE / "raw/pilot_intersections.json").read_text(encoding="utf-8"))
official_pairs = defaultdict(list)
for item in intersections:
    for a, b in itertools.combinations(item["route_ids"], 2):
        official_pairs[tuple(sorted((a, b)))].append(item["INT_ID"])

turns = [json.loads(s) for s in (R1 / "candidate_extract/TST_Jordan_turns.jsonl").open(encoding="utf-8")]
resolved, quarantine = [], []
blocked = set()
for turn in turns:
    p = turn["properties"]
    seq = [p.get(f"Edge{i}FID", "") for i in range(1, 9)]
    seq = [x for x in seq if x and x not in ("<Null>", "-1")]
    tid = p.get("TURN_ID", "")
    candidates = [
        (a, b) for left, right in zip(seq, seq[1:])
        for a in by_route[left] for b in by_route[right]
        if a["to_node_id"] == b["from_node_id"]
    ]
    if candidates:
        for a, b in candidates:
            blocked.add((a["link_id"], b["link_id"]))
            resolved.append(dict(source_turn_id=tid, source_edge_sequence="|".join(seq),
                                 from_link_id=a["link_id"], to_link_id=b["link_id"],
                                 via_node_id=a["to_node_id"], classification="RESOLVED_PROHIBITED",
                                 resolution="source NO_TURN=-1; all-day or conservative passenger-car block",
                                 source_no_turn=p.get("NO_TURN", ""),
                                 included_vehicle_types=p.get("INC_VEH_TYPE", "")))
    else:
        missing = any(x not in by_route for x in seq)
        endpoint_shared = any(
            {a["from_node_id"], a["to_node_id"]} & {b["from_node_id"], b["to_node_id"]}
            for left, right in zip(seq, seq[1:]) for a in by_route[left] for b in by_route[right]
        )
        status = "OUTSIDE_MODEL_BOUNDARY" if missing else (
            "RESOLVED_PROHIBITED" if endpoint_shared else "INSUFFICIENT_EVIDENCE_QUARANTINED"
        )
        row = dict(source_turn_id=tid, source_edge_sequence="|".join(seq),
                   classification=status, source_no_turn=p.get("NO_TURN", ""),
                   resolution="no legal directed adjacent movement" if endpoint_shared else
                   "source edge absent from accepted core" if missing else
                   "source turn has no exact adjacent model endpoints; no routable movement to ban")
        if status == "RESOLVED_PROHIBITED":
            resolved.append(dict(row, from_link_id="", to_link_id="", via_node_id="",
                                 included_vehicle_types=p.get("INC_VEH_TYPE", "")))
        else:
            quarantine.append(row)
write("movement_resolved.csv", resolved)
write("movement_quarantine.csv", quarantine)

grade_rows, allowed = [], defaultdict(list)
for node in sorted(set(incoming) & set(outgoing), key=int):
    for a in incoming[node]:
        for b in outgoing[node]:
            ra, rb = a["source_link_id"], b["source_link_id"]
            ix = official_pairs.get(tuple(sorted((ra, rb))), []) if ra != rb else []
            grade_ok = ra == rb or bool(ix)
            blocked_turn = (a["link_id"], b["link_id"]) in blocked
            grade_rows.append(dict(via_node_id=node, from_link_id=a["link_id"], to_link_id=b["link_id"],
                                   from_route_id=ra, to_route_id=rb,
                                   from_elevation=road_fields[ra]["elevation"],
                                   to_elevation=road_fields[rb]["elevation"],
                                   official_intersection_ids="|".join(ix),
                                   source_connection_supported=grade_ok,
                                   source_turn_prohibited=blocked_turn,
                                   routing_transition_allowed=grade_ok and not blocked_turn))
            if grade_ok and not blocked_turn:
                allowed[a["link_id"]].append(b["link_id"])
write("GRADE_SEPARATION_AUDIT.csv", grade_rows)
if any(x["routing_transition_allowed"] and not x["source_connection_supported"] for x in grade_rows):
    raise RuntimeError("unsupported grade connection accepted")
write("turn_aware_movement_edges.csv", [dict(from_link_id=a, to_link_id=b) for a, bs in allowed.items() for b in bs])

# SCC on link-state graph; all zone access proxies attach to this verified core.
ids = {r["link_id"] for r in physical}
reverse = defaultdict(list)
for a, bs in allowed.items():
    for b in bs:
        reverse[b].append(a)
seen, order = set(), []
for seed in ids:
    if seed in seen:
        continue
    stack = [(seed, 0)]
    seen.add(seed)
    while stack:
        u, index = stack[-1]
        adjacent = allowed[u]
        if index < len(adjacent):
            v = adjacent[index]
            stack[-1] = (u, index + 1)
            if v not in seen:
                seen.add(v)
                stack.append((v, 0))
        else:
            order.append(u)
            stack.pop()
seen, components = set(), []
for seed in reversed(order):
    if seed in seen:
        continue
    stack, component = [seed], []
    seen.add(seed)
    while stack:
        u = stack.pop()
        component.append(u)
        for v in reverse[u]:
            if v not in seen:
                seen.add(v)
                stack.append(v)
    components.append(component)
core = set(max(components, key=len))

nodes = {r["node_id"]: r for r in read("node.csv") if r["node_type"] == "physical_road"}
zones = [r for r in read("zone.csv") if r["super_zone"]]
old_access = {r["zone_id"]: r for r in read("zone_access.csv")}
core_nodes = [
    nid for nid in nodes
    if any(r["link_id"] in core and road_fields[r["source_link_id"]]["elevation"] == "0"
           for r in incoming[nid])
    and any(r["link_id"] in core and road_fields[r["source_link_id"]]["elevation"] == "0"
            for r in outgoing[nid])
]


def meters(lon1, lat1, lon2, lat2):
    return math.hypot((lon1 - lon2) * 103200, (lat1 - lat2) * 110850)


access_rows = []
for z in zones:
    zid = z["zone_id"]
    lon, lat = float(z["centroid_lon"]), float(z["centroid_lat"])
    d, nid = min(
        (meters(lon, lat, float(nodes[n]["x_coord"]), float(nodes[n]["y_coord"])), n)
        for n in core_nodes
    )
    access_rows.append(dict(zone_id=zid, centroid_node_id=zid,
                            previous_physical_access_node_id=old_access[zid]["physical_access_node_id"],
                            physical_access_node_id=nid, access_distance_m=round(d, 3),
                            previous_access_distance_m=old_access[zid]["access_distance_m"],
                            elevation="0", directed_in_core=True, water_crossing_status="unverified",
                            barrier_status="straight_connector_proxy_not_walk_route",
                            access_evidence_grade="ENGINEERING_PROXY"))
    for row in links_all:
        if row["mcl_link_class"] == "nonphysical_zone_access_out" and row["from_node_id"] == zid:
            row["to_node_id"] = nid
            row["geometry"] = f'LINESTRING({lon} {lat},{nodes[nid]["x_coord"]} {nodes[nid]["y_coord"]})'
        elif row["mcl_link_class"] == "nonphysical_zone_access_in" and row["to_node_id"] == zid:
            row["from_node_id"] = nid
            row["geometry"] = f'LINESTRING({nodes[nid]["x_coord"]} {nodes[nid]["y_coord"]},{lon} {lat})'
write("zone_access_r2.csv", access_rows)
new_access = []
for a in access_rows:
    new_access.append(dict(zone_id=a["zone_id"], centroid_node_id=a["zone_id"],
                           physical_access_node_id=a["physical_access_node_id"],
                           access_distance_m=a["access_distance_m"],
                           access_status="r2_ground_core_proxy_barrier_unverified",
                           access_method="nearest level-0 node with inbound/outbound links in turn-aware SCC"))
write("zone_access.csv", new_access, root=INST)
write("link.csv", links_all, root=INST)

# Independent directed reachability, not a straight-line proxy. A destination
# is reached only through an incoming physical link at its access node.
acc = {a["zone_id"]: a["physical_access_node_id"] for a in access_rows}
reach_rows, ledger = [], []
for oz in sorted(acc, key=int):
    start = [x["link_id"] for x in outgoing[acc[oz]]]
    seen, stack = set(start), list(start)
    while stack:
        for nxt in allowed[stack.pop()]:
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    for dz in sorted(acc, key=int):
        if oz == dz:
            ledger.append(dict(o_zone_id=oz, d_zone_id=dz, reason="intrazonal_not_loaded", volume=""))
            continue
        reachable = any(x["link_id"] in seen for x in incoming[acc[dz]])
        reach_rows.append(dict(o_zone_id=oz, d_zone_id=dz,
                               o_access_node_id=acc[oz], d_access_node_id=acc[dz],
                               turn_aware_directed_reachable=reachable))
        if not reachable:
            ledger.append(dict(o_zone_id=oz, d_zone_id=dz, reason="unreachable", volume=""))
write("DIRECTED_REACHABILITY_BY_OD.csv", reach_rows)
write("UNREACHABLE_AND_INTRAZONAL_LEDGER.csv", ledger)

# Link-state split graph: each original physical link remains a unique BPR arc.
# A small declared positive movement/connector time avoids zero-cost cycles;
# high proxy capacity and zero alpha make these topology arcs non-congesting.
state = {r["link_id"]: (1_000_000_000 + 2 * i, 1_000_000_001 + 2 * i)
         for i, r in enumerate(sorted(physical, key=lambda x: int(x["link_id"]))) }
expanded, crosswalk = [], []
for r in physical:
    lid = r["link_id"]
    u, v = state[lid]
    expanded.append(dict(link_id=lid, from_node_id=u, to_node_id=v,
                         capacity=r["capacity"], vdf_fftt=r["free_flow_time"],
                         vdf_alpha="0.15", vdf_beta="4", length=r["length"]))
    crosswalk.append(dict(expanded_link_id=lid, link_class="physical",
                          physical_link_id=lid, source_route_id=r["source_link_id"],
                          from_physical_link_id="", to_physical_link_id="", zone_id=""))
next_id = 2_000_000_000
for a in sorted(allowed, key=int):
    for b in sorted(allowed[a], key=int):
        lid = str(next_id)
        next_id += 1
        expanded.append(dict(link_id=lid, from_node_id=state[a][1], to_node_id=state[b][0],
                             capacity="1000000000", vdf_fftt="0.0001", vdf_alpha="0",
                             vdf_beta="1", length="0.001"))
        crosswalk.append(dict(expanded_link_id=lid, link_class="nonphysical_allowed_movement",
                              physical_link_id="", source_route_id="", from_physical_link_id=a,
                              to_physical_link_id=b, zone_id=""))
next_id = 3_000_000_000
for zid in sorted(acc, key=int):
    access_node = acc[zid]
    origin_node, dest_node = 4_000_000_000 + int(zid), 4_100_000_000 + int(zid)
    for x in outgoing[access_node]:
        lid = str(next_id)
        next_id += 1
        expanded.append(dict(link_id=lid, from_node_id=origin_node, to_node_id=state[x["link_id"]][0],
                             capacity="1000000000", vdf_fftt="0.0001", vdf_alpha="0",
                             vdf_beta="1", length="0.001"))
        crosswalk.append(dict(expanded_link_id=lid, link_class="nonphysical_zone_origin",
                              physical_link_id="", source_route_id="", from_physical_link_id="",
                              to_physical_link_id=x["link_id"], zone_id=zid))
    for x in incoming[access_node]:
        lid = str(next_id)
        next_id += 1
        expanded.append(dict(link_id=lid, from_node_id=state[x["link_id"]][1], to_node_id=dest_node,
                             capacity="1000000000", vdf_fftt="0.0001", vdf_alpha="0",
                             vdf_beta="1", length="0.001"))
        crosswalk.append(dict(expanded_link_id=lid, link_class="nonphysical_zone_destination",
                              physical_link_id="", source_route_id="", from_physical_link_id=x["link_id"],
                              to_physical_link_id="", zone_id=zid))
write("static_input/turn_expanded_links.csv", expanded)
write("static_input/expanded_network_crosswalk.csv", crosswalk)
write("static_input/zone_to_expanded_node.csv", [dict(zone_id=z,
                                                     origin_node_id=4_000_000_000 + int(z),
                                                     destination_node_id=4_100_000_000 + int(z))
                                                 for z in sorted(acc, key=int)])
seed = read("demand_seed_vehicle.csv")
for tier in ("smoke", "pilot"):
    ds = [dict(o_zone_id=4_000_000_000 + int(r["o_zone_id"]),
               d_zone_id=4_100_000_000 + int(r["d_zone_id"]),
               volume=r["volume"], source_o_zone_id=r["o_zone_id"],
               source_d_zone_id=r["d_zone_id"], scenario_tier=tier)
          for r in seed if r["tier"] == tier]
    write(f"static_input/r1_{tier}_demand.csv", ds)

gate = {
    "assignment_ready": all(
        math.isfinite(float(r["free_speed"])) and float(r["free_speed"]) > 0
        and int(r["lanes"]) > 0 and float(r["capacity"]) > 0 for r in physical
    ) and all(r["source_connection_supported"] for r in grade_rows)
      and all(r["turn_aware_directed_reachable"] for r in reach_rows)
      and all((a, b) not in blocked for a, bs in allowed.items() for b in bs),
    "physical_links": len(physical), "movement_arcs": sum(map(len, allowed.values())),
    "source_turn_features": len(turns), "mapped_prohibited_movement_rows": len(blocked),
    "unresolved_classification_counts": dict(Counter(x["classification"] for x in quarantine)),
    "turn_aware_core_links": len(core), "core_access_nodes": len(core_nodes),
    "zones": len(acc), "directed_zone_pairs": len(reach_rows),
    "unreachable_zone_pairs": sum(not r["turn_aware_directed_reachable"] for r in reach_rows),
    "max_access_distance_m": max(r["access_distance_m"] for r in access_rows),
    "source_supported_transition_checks": len(grade_rows),
    "unsupported_source_connection_count": sum(not r["source_connection_supported"] for r in grade_rows),
    "official_full_limit_link_count": sum(r["posted_limit_grade"] == "OFFICIAL_EXACT" for r in speed_ev),
    "free_speed_grade": "ENGINEERING_PROXY_for_all_links",
    "lane_and_capacity_grade": "ENGINEERING_PROXY_for_all_links",
    "period_hours": 1,
    "limits": ["straight-line zone access barrier/water audit incomplete",
               "capacities and lanes are engineering proxies, not observed",
               "turn connector cost is 0.0001 minute per traversal"],
}
(OUT / "ASSIGNMENT_READY_GATE_R2.json").write_text(json.dumps(gate, indent=2) + "\n", encoding="utf-8")
print(json.dumps(gate, indent=2))
if not gate["assignment_ready"]:
    raise SystemExit(1)
