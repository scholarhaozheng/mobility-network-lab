"""Build exact reachable finite-time subgraph from frozen R2 physical links."""
from __future__ import annotations
import csv
import hashlib
import heapq
import json
import math
import os
import shutil
from pathlib import Path

w = Path(__file__).resolve().parent
ident = json.loads((w / "INPUT_IDENTITY.json").read_text(encoding="utf-8"))
policy = json.loads((w / "T_POLICY.json").read_text(encoding="utf-8"))
pre = json.loads((w / "T_PREFLIGHT.json").read_text(encoding="utf-8"))
profile = pre["selected_profile"]
n = int(profile[1:])
H = pre[profile]["H_steps"]
dt = policy["time_step_seconds"]
dep = pre[profile]["departure_step"]
out = w / "runs/T_case"
if out.exists(): raise FileExistsError(out)
out.mkdir(parents=True)

def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

links = rows(w / "input/static/link.csv")
access = {r["zone_id"]: r["node_id"] for r in rows(w / "input/static/access.csv")}
ods = ident["selected_s_od"][:n]
nodes = sorted(set(r["from_node_id"] for r in links) | set(r["to_node_id"] for r in links))
adj = {x: [] for x in nodes}; rev = {x: [] for x in nodes}
physical = []
for r in links:
    u, v = r["from_node_id"], r["to_node_id"]
    tau = max(1, math.ceil(float(r["vdf_fftt"]) * 60 / dt))
    physical.append((u, v, tau, r))
    adj[u].append((v, tau)); rev[v].append((u, tau))

def dijkstra(start, graph):
    distance = {start: 0}; queue = [(0, start)]
    while queue:
        du, u = heapq.heappop(queue)
        if du != distance[u]: continue
        for v, weight in graph[u]:
            nd = du + weight
            if nd < distance.get(v, math.inf):
                distance[v] = nd; heapq.heappush(queue, (nd, v))
    return distance

reach = []
for r in ods:
    o, d = access[r["origin"]], access[r["destination"]]
    a, b = dijkstra(o, adj), dijkstra(d, rev)
    if d not in a: raise ValueError("unreachable selected OD")
    reach.append((o, d, a, b, a[d]))
arc_keys = set()
for o, d, do, dd, shortest in reach:
    for j, (u, v, tau, r) in enumerate(physical):
        if u not in do or v not in dd: continue
        lo, hi = dep + do[u], H - tau - dd[v]
        if hi >= lo: arc_keys.update(("m", j, t) for t in range(lo, hi + 1))
    for j, node in enumerate(nodes):
        if node not in do or node not in dd: continue
        lo, hi = dep + do[node], H - 1 - dd[node]
        if hi >= lo: arc_keys.update(("w", j, t) for t in range(lo, hi + 1))
arc_keys = sorted(arc_keys)
total_q = sum(float(r["volume_pce"]) / 12 for r in ods)
arc_path = out / "dynamic_arc.csv"
fields = ["arc_id", "from_node_time_id", "to_node_time_id", "from_physical_node_id", "to_physical_node_id", "from_time", "to_time", "arc_type", "physical_link_id", "cost", "capacity"]
node_time_ids = set()
count = {"movement": 0, "waiting": 0, "source_connector": 0, "sink_connector": 0}
with arc_path.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    def emit(arc_id, from_id, to_id, u, v, t, t2, kind, lid, cost, cap):
        writer.writerow(dict(zip(fields, (arc_id, from_id, to_id, u, v, t, t2, kind, lid, repr(cost), repr(cap)))))
        node_time_ids.add((from_id, u, t)); node_time_ids.add((to_id, v, t2))
        count[kind] += 1
    for kind, j, t in arc_keys:
        if kind == "m":
            u, v, tau, r = physical[j]
            emit(f"arc_{r['link_id']}_t{t}", f"n{u}_t{t}", f"n{v}_t{t+tau}", u, v, t, t+tau,
                 "movement", r["link_id"], float(r["vdf_fftt"]), float(r["capacity"]) * dt / 3600)
        else:
            node = nodes[j]
            emit(f"wait_{node}_t{t}", f"n{node}_t{t}", f"n{node}_t{t+1}", node, node, t, t+1,
                 "waiting", "", dt / 60, total_q)
    for i, (o, d, do, dd, shortest) in enumerate(reach, start=1):
        did = f"T{i:02d}"; q = float(ods[i-1]["volume_pce"]) / 12
        emit(f"source_{did}", f"source_{did}_t{dep}", f"n{o}_t{dep}", o, o, dep, dep,
             "source_connector", "", 0.0, q)
        for t in range(dep + shortest, H + 1):
            emit(f"sink_{did}_{d}_t{t}", f"n{d}_t{t}", f"sink_{did}_t{H}", d, d, t, H,
                 "sink_connector", "", 0.0, q)
demands = []
for i, r in enumerate(ods, start=1):
    demands.append({"demand_id": f"T{i:02d}", "origin_node_id": access[r["origin"]],
                    "destination_node_id": access[r["destination"]], "departure_time": dep,
                    "volume": repr(float(r["volume_pce"]) / 12)})
with (out / "dynamic_demand.csv").open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(demands[0]), lineterminator="\n")
    writer.writeheader(); writer.writerows(demands)
with (out / "dynamic_node.csv").open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["node_time_id", "physical_node_id", "time"], lineterminator="\n")
    writer.writeheader()
    for node_id, physical_node, t in sorted(node_time_ids):
        writer.writerow({"node_time_id": node_id, "physical_node_id": physical_node, "time": t})
shutil.copyfile(w / "input/static/link.csv", out / "physical_link.csv")
model_signature = hashlib.sha256(arc_path.read_bytes() + b"\0" + (out / "dynamic_demand.csv").read_bytes()).hexdigest()
manifest = {
    "schema_version": "cross_city_lagrangian_case_v1", "adapter": "finite_dynamic_csv_v1",
    "case_id": f"Berkeley_R2_{profile}_first_5min_dt30", "city": "Berkeley",
    "arc_file": "dynamic_arc.csv", "demand_file": "dynamic_demand.csv",
    "arc_sha256": sha(arc_path), "demand_sha256": sha(out / "dynamic_demand.csv"),
    "physical_link_file": "physical_link.csv", "physical_link_sha256": sha(out / "physical_link.csv"),
    "physical_link_id_column": "link_id", "objective_unit": "pce_minutes",
    "capacity_unit": "pce_per_30sec_step", "time_step_seconds": dt,
}
(out / "case_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
receipt = {"profile": profile, "model_signature": model_signature, "H_steps": H, "H_minutes": H*dt/60,
           "dt_seconds": dt, "departure_step": dep, "departure_clock": "08:02:30 local",
           "demand_q_pce": total_q, "arc_counts": count, "dynamic_nodes": len(node_time_ids),
           "original_links": len(links), "original_nodes": len(nodes),
           "OD_rounded_shortest_steps": [x[4] for x in reach],
           "movement_semantics": "R2 physical link once, ceil(fftt/dt) temporal duration, original fftt cost, hourly cap*dt/3600",
           "wait_semantics": "30s time and 0.5min cost; no storage/spillback",
           "source_semantics": "uniform 1/12 of hourly OD, first five-minute bin only; engineering assumption",
           "exact_pruning": "union of arc-time states on some selected OD path within H by forward/reverse shortest duration; no K restriction",
           "unselected_hourly_od_count": 72-n,
           "unselected_hourly_pce": ident["total_pce_full"]-sum(float(r["volume_pce"]) for r in ods),
           "other_11_bins_selected_pce": 11 * total_q,
           "hashes": {x: sha(out/x) for x in ("dynamic_arc.csv", "dynamic_demand.csv", "dynamic_node.csv", "case_manifest.json", "physical_link.csv")}}
(out / "BUILD_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
print(json.dumps(receipt, indent=2))
