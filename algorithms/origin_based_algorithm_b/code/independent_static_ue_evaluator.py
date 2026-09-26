"""Independent static UE certificate. No imports/calls into the solver adapter.

Reads immutable source CSVs and returned link/path CSVs; recomputes every
metric and exits nonzero when any locked acceptance gate fails.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import heapq
import json
import math
import sys
from collections import defaultdict, deque
from pathlib import Path


def digest(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def rows(p):
    with open(p, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def iter_rows(p):
    with open(p, newline="", encoding="utf-8-sig") as f:
        yield from csv.DictReader(f)


def shortest(origin, adjacency, cost):
    d = {origin: 0.0}
    pq = [(0.0, origin)]
    while pq:
        du, u = heapq.heappop(pq)
        if du > d[u] + 1e-13:
            continue
        for v, lid in adjacency[u]:
            nd = du + cost[lid]
            if nd < d.get(v, math.inf) - 1e-13:
                d[v] = nd
                heapq.heappush(pq, (nd, v))
    return d


def acyclic(edges):
    outgoing, degree, nodes = defaultdict(list), defaultdict(int), set()
    for u, v in edges:
        outgoing[u].append(v); degree[v] += 1; nodes.update((u, v))
    q = deque(n for n in nodes if degree[n] == 0)
    seen = 0
    while q:
        u = q.popleft(); seen += 1
        for v in outgoing[u]:
            degree[v] -= 1
            if degree[v] == 0:
                q.append(v)
    return seen == len(nodes)


def evaluate(link_path, demand_path, run_dir, expected_exe_sha=None):
    work = Path(run_dir)
    policy = json.loads((work / "input_lock.json").read_text(encoding="utf-8"))["policy"]
    lock = json.loads((work / "input_lock.json").read_text(encoding="utf-8"))
    mapping = json.loads((work / "mapping.json").read_text(encoding="utf-8"))
    process = json.loads((work / "process.json").read_text(encoding="utf-8"))
    issues = []
    if process["exit_code"] != 0:
        issues.append("solver_exit_nonzero")
    if expected_exe_sha and process["executable_sha256"].lower() != expected_exe_sha.lower():
        issues.append("stale_or_changed_executable")
    if digest(link_path) != lock["source_link_sha256"] or digest(demand_path) != lock["source_demand_sha256"]:
        issues.append("source_input_identity_changed")
    if digest(work / "net" / "r2_net.txt") != lock["converted"]["net"] or digest(work / "net" / "r2_trips.txt") != lock["converted"]["trips"]:
        issues.append("converted_input_identity_changed")
    if digest(work / "mapping.json") != lock["mapping_sha256"] or digest(work / "params.txt") != lock["params_sha256"]:
        issues.append("adapter_mapping_or_policy_changed")
    links = {}
    pair_to_id = {}
    adjacency = defaultdict(list)
    for r in rows(link_path):
        lid, u, v = str(r["link_id"]), int(r["from_node_id"]), int(r["to_node_id"])
        if lid in links or (u, v) in pair_to_id:
            issues.append("duplicate_physical_link_identity")
        cap, t0, alpha, beta = (float(r[k]) for k in ("capacity", "vdf_fftt", "vdf_alpha", "vdf_beta"))
        if min(cap, t0) <= 0 or alpha < 0 or beta < 1:
            issues.append("invalid_BPR_units")
        links[lid] = dict(u=u, v=v, cap=cap, t0=t0, alpha=alpha, beta=beta)
        pair_to_id[u, v] = lid
        adjacency[u].append((v, lid))
    od = defaultdict(float)
    for r in rows(demand_path):
        o = int(r.get("o_zone_id") or r.get("o_node_id"))
        d = int(r.get("d_zone_id") or r.get("d_node_id"))
        q = float(r["volume"])
        if q < 0 or not math.isfinite(q):
            issues.append("invalid_demand")
        if q > 0 and o != d:
            od[o, d] += q
    demand_total = sum(od.values())
    balance_tol = policy["balance_abs"] + policy["balance_rel_total"] * demand_total
    if len(links) != mapping["link_count"] or len(od) != mapping["od_count"]:
        issues.append("mapping_count_mismatch")
    if mapping["first_thru_node"] != 1 or not mapping["zone_nodes_are_physical"]:
        issues.append("connector_or_physical_node_semantics_changed")
    if set(mapping["directed_pair_to_link_id"].values()) != set(links):
        issues.append("broken_link_mapping")
    # Verify the numerical TNTP conversion against source values, not just hashes.
    inverse = {int(k): int(v) for k, v in mapping["tntp_to_old"].items()}
    converted_pairs = set()
    for line in (work / "net" / "r2_net.txt").read_text(encoding="ascii").splitlines():
        s = line.strip()
        if not s or s.startswith("<") or s.startswith("~"):
            continue
        f = s.rstrip(";").split()
        if len(f) < 7:
            issues.append("invalid_TNTP_network_row"); continue
        u, v = inverse[int(f[0])], inverse[int(f[1])]
        lid = pair_to_id.get((u, v))
        if not lid:
            issues.append("broken_TNTP_link_mapping"); continue
        converted_pairs.add((u, v))
        l = links[lid]
        for got, key in zip(map(float, (f[2], f[4], f[5], f[6])), ("cap", "t0", "alpha", "beta")):
            if not math.isclose(got, l[key], rel_tol=1e-14, abs_tol=1e-14):
                issues.append("mismatched_BPR_units")
    if len(converted_pairs) != len(links):
        issues.append("TNTP_link_count_mismatch")
    x = {}
    for r in rows(work / "link_flow.csv"):
        lid = r["link_id"]
        v = float(r["volume"])
        if lid not in links or lid in x:
            issues.append("broken_link_mapping")
        if lid in links and (int(r["from_node_id"]), int(r["to_node_id"])) != (links[lid]["u"], links[lid]["v"]):
            issues.append("broken_link_mapping")
        if not math.isfinite(v) or v < policy["nonnegative_floor"]:
            issues.append("negative_or_nonfinite_link_flow")
        x[lid] = v
    if set(x) != set(links):
        issues.append("missing_or_extra_link_flow")
    cost, objective, tstt = {}, 0.0, 0.0
    for lid, l in links.items():
        v = x.get(lid, 0.0)
        t = l["t0"] * (1 + l["alpha"] * (v / l["cap"]) ** l["beta"])
        cost[lid] = t
        tstt += v * t
        objective += l["t0"] * (v + l["alpha"] * l["cap"] / (l["beta"] + 1) * (v / l["cap"]) ** (l["beta"] + 1))
    distances = {o: shortest(o, adjacency, cost) for o in {o for o, _ in od}}
    sptt = 0.0
    for (o, d), q in od.items():
        dd = distances[o].get(d, math.inf)
        if not math.isfinite(dd):
            issues.append("unreachable_OD")
        else:
            sptt += q * dd
    gap = (tstt - sptt) / tstt if tstt > 0 else math.inf
    if not math.isfinite(gap) or gap < -1e-8 or gap > policy["evaluator_relative_gap"]:
        issues.append("relative_gap_gate")
    od_returned = defaultdict(float)
    origin_arcs = defaultdict(float)
    path_count, max_path_slack, used_path_count = 0, 0.0, 0
    for r in iter_rows(work / "path_flow.csv"):
        o, d, q = int(r["origin"]), int(r["destination"]), float(r["volume"])
        lids = r["link_ids"].split(";")
        seq = [int(n) for n in r["node_ids"].split(";")]
        path_count += 1
        if not math.isfinite(q) or q < policy["nonnegative_floor"]:
            issues.append("negative_or_nonfinite_path_flow")
        if (o, d) not in od or seq[0] != o or seq[-1] != d or len(lids) != len(seq)-1 or len(seq) != len(set(seq)):
            issues.append("invalid_origin_path_mapping")
        pcost = 0.0
        for lid, u, v in zip(lids, seq, seq[1:]):
            if lid not in links or (links[lid]["u"], links[lid]["v"]) != (u, v):
                issues.append("broken_path_link_mapping")
                continue
            origin_arcs[o, lid] += q
            pcost += cost[lid]
        od_returned[o, d] += q
        if q >= max(policy["active_flow_abs"], policy["active_flow_rel_od"] * od.get((o,d), 0.0)):
            used_path_count += 1
            slack = pcost - distances.get(o, {}).get(d, math.inf)
            max_path_slack = max(max_path_slack, slack)
    max_od_residual = max((abs(od_returned[k] - v) for k, v in od.items()), default=0.0)
    if max_od_residual > balance_tol or set(od_returned) != set(od):
        issues.append("OD_conservation_gate")
    if max_path_slack > policy["max_used_path_slack_minutes"]:
        issues.append("used_path_slack_gate")
    arc_sum = defaultdict(float)
    origin_net = defaultdict(float)
    origin_edges = defaultdict(list)
    origin_total = defaultdict(float)
    for (o, _), q in od.items():
        origin_total[o] += q
    max_used_arc_slack, min_unused_arc_slack = 0.0, math.inf
    for (o, lid), v in origin_arcs.items():
        arc_sum[lid] += v
        l = links[lid]
        origin_net[o, l["u"]] += v; origin_net[o, l["v"]] -= v
        active = v >= max(policy["active_flow_abs"], policy["active_flow_rel_od"] * origin_total[o])
        if active:
            origin_edges[o].append((l["u"], l["v"]))
            rc = distances[o].get(l["u"], math.inf) + cost[lid] - distances[o].get(l["v"], math.inf)
            max_used_arc_slack = max(max_used_arc_slack, rc)
    for o, dist in distances.items():
        for lid, l in links.items():
            if l["u"] in dist and l["v"] in dist and origin_arcs.get((o, lid), 0.0) < max(policy["active_flow_abs"], policy["active_flow_rel_od"] * origin_total[o]):
                min_unused_arc_slack = min(min_unused_arc_slack, dist[l["u"]] + cost[lid] - dist[l["v"]])
    if max_used_arc_slack > policy["max_used_arc_slack_minutes"]:
        issues.append("used_arc_slack_gate")
    if min_unused_arc_slack < policy["unused_arc_slack_floor_minutes"]:
        issues.append("unused_arc_slack_gate")
    cyclic_origins = [o for o, edges in origin_edges.items() if not acyclic(edges)]
    if cyclic_origins:
        issues.append("cyclic_positive_origin_support")
    max_link_mismatch = max((abs(arc_sum[lid] - x.get(lid, 0.0)) for lid in links), default=0.0)
    if max_link_mismatch > balance_tol:
        issues.append("aggregate_link_flow_mismatch")
    origin_demand = defaultdict(lambda: defaultdict(float))
    for (o, d), q in od.items():
        origin_demand[o][o] += q; origin_demand[o][d] -= q
    max_origin_node_residual = max((abs(origin_net[o, n] - origin_demand[o][n])
                                    for o, n in set(origin_net) |
                                    {(o, n) for o, by_node in origin_demand.items() for n in by_node}), default=0.0)
    if max_origin_node_residual > balance_tol:
        issues.append("origin_node_conservation_gate")
    report = dict(status="ACCEPTED" if not issues else "GATED", issues=sorted(set(issues)),
                  input_hashes=dict(link=digest(link_path), demand=digest(demand_path)),
                  solver_exit_code=process["exit_code"], executable_sha256=process["executable_sha256"],
                  nodes=len({n for l in links.values() for n in (l["u"], l["v"])}), links=len(links),
                  positive_od=len(od), total_demand=demand_total, path_count=path_count,
                  used_path_count=used_path_count, origin_count=len(distances),
                  relative_gap=gap, objective=objective, tstt=tstt, sptt=sptt,
                  max_od_residual=max_od_residual, max_origin_node_residual=max_origin_node_residual,
                  max_link_mismatch=max_link_mismatch, max_used_path_slack_minutes=max_path_slack,
                  max_used_arc_slack_minutes=max_used_arc_slack,
                  min_unused_arc_slack_minutes=min_unused_arc_slack,
                  cyclic_origins=cyclic_origins, policy=policy)
    (work / "evaluation.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    with open(work / "origin_arc_flow.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(("origin", "link_id", "volume"))
        w.writerows((o, lid, f"{v:.17g}") for (o, lid), v in sorted(origin_arcs.items()))
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--link", required=True); ap.add_argument("--demand", required=True)
    ap.add_argument("--run", required=True); ap.add_argument("--expected-exe-sha")
    a = ap.parse_args()
    rep = evaluate(a.link, a.demand, a.run, a.expected_exe_sha)
    print(json.dumps(rep, indent=2, sort_keys=True))
    return 0 if rep["status"] == "ACCEPTED" else 3


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"EVALUATION_FAILED: {type(e).__name__}: {e}", file=sys.stderr)
        raise SystemExit(4)
