"""Independent exact pricing certificate for a finite time-expanded DAG.

Uses only graph, demand, generated pool, and RMP primal/dual data. In particular,
this module does not import or call the production Phase-II pricing oracle.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import heapq
import json
import math
from collections import defaultdict
from pathlib import Path

TOL = 1e-6

def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as f:
        if fields:
            writer = csv.DictWriter(f, fields)
            writer.writeheader()
            writer.writerows(rows)

def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()

def sequence(value):
    return tuple(part.strip() for part in value.split("|") if part.strip())

class GraphError(ValueError):
    pass

class DAG:
    def __init__(self, nodes, arcs, demands):
        self.nodes = {r["node_time_id"]: r for r in nodes}
        self.arcs = {r["arc_id"]: r for r in arcs}
        self.demands = {r["demand_id"]: dict(r) for r in demands}
        if len(self.nodes) != len(nodes) or len(self.arcs) != len(arcs) or len(self.demands) != len(demands):
            raise GraphError("duplicate node, arc, or demand ID")
        self.outgoing = defaultdict(list)
        indegree = {n: 0 for n in self.nodes}
        self.arc_types = defaultdict(int)
        for a in arcs:
            u, v = a["from_node_time_id"], a["to_node_time_id"]
            if u not in self.nodes or v not in self.nodes:
                raise GraphError(f"arc {a['arc_id']} has missing endpoint")
            tail_t, head_t = float(a["from_time"]), float(a["to_time"])
            if not all(math.isfinite(x) for x in (tail_t, head_t)) or head_t < tail_t:
                raise GraphError(f"arc {a['arc_id']} is nonmonotone")
            if abs(tail_t - float(self.nodes[u]["time"])) > 1e-9 or abs(head_t - float(self.nodes[v]["time"])) > 1e-9:
                raise GraphError(f"arc {a['arc_id']} endpoint time mismatch")
            typ = a["arc_type"]
            self.arc_types[typ] += 1
            if typ == "movement" and not a.get("physical_link_id"):
                raise GraphError(f"movement arc {a['arc_id']} missing physical link")
            if not math.isfinite(float(a["cost"])) or not math.isfinite(float(a["capacity"])):
                raise GraphError(f"arc {a['arc_id']} nonfinite cost/capacity")
            self.outgoing[u].append(a)
            indegree[v] += 1
        for edges in self.outgoing.values():
            edges.sort(key=lambda a: a["arc_id"])
        queue = [n for n, degree in indegree.items() if degree == 0]
        heapq.heapify(queue)
        order = []
        while queue:
            u = heapq.heappop(queue)
            order.append(u)
            for a in self.outgoing[u]:
                v = a["to_node_time_id"]
                indegree[v] -= 1
                if indegree[v] == 0:
                    heapq.heappush(queue, v)
        if len(order) != len(self.nodes):
            raise GraphError("dynamic graph is not a DAG")
        self.topo = order
        self.graph_signature = canonical_hash({"nodes": nodes, "arcs": arcs})
        self.demand_signature = canonical_hash(demands)
        for demand_id, d in self.demands.items():
            source, sink = f"source_{demand_id}_t{d['departure_time']}", None
            # Dynamic builders may use a final horizon in the sink node ID.
            sinks = [n for n in self.nodes if n.startswith(f"sink_{demand_id}_t")]
            if source not in self.nodes or len(sinks) != 1:
                raise GraphError(f"demand {demand_id} source/sink node missing or ambiguous")
            sink = sinks[0]
            d["_source_node"] = source
            d["_sink_node"] = sink

    def validate_path(self, demand_id, path):
        if not path:
            raise GraphError(f"empty path for {demand_id}")
        d = self.demands[demand_id]
        node = d["_source_node"]
        cost = 0.0
        for arc_id in path:
            a = self.arcs.get(arc_id)
            if a is None or a["from_node_time_id"] != node:
                raise GraphError(f"invalid path continuity at {arc_id} for {demand_id}")
            node = a["to_node_time_id"]
            cost += float(a["cost"])
        if node != d["_sink_node"]:
            raise GraphError(f"path for {demand_id} misses sink")
        if path[0] != f"source_{demand_id}" or self.arcs[path[-1]]["arc_type"] != "sink_connector":
            raise GraphError(f"path for {demand_id} has wrong connector")
        return cost

    def k_shortest(self, demand_id, weights, k):
        """Exact top-k distinct paths, reverse-DAG k-way suffix merge.

        Every outgoing arc contributes a sorted list of suffix paths; merging
        those lists yields the exact ordering even when arc weights are negative.
        """
        d = self.demands[demand_id]
        target = d["_sink_node"]
        labels = {target: [(0.0, ())]}
        for u in reversed(self.topo):
            if u == target:
                continue
            heap = []
            for a in self.outgoing[u]:
                suffixes = labels.get(a["to_node_time_id"])
                if suffixes:
                    aid = a["arc_id"]
                    score = weights[aid] + suffixes[0][0]
                    path = (aid,) + suffixes[0][1]
                    heapq.heappush(heap, (score, path, aid, 0, a["to_node_time_id"]))
            if not heap:
                continue
            best = []
            while heap and len(best) < k:
                score, path, aid, ix, v = heapq.heappop(heap)
                best.append((score, path))
                suffixes = labels[v]
                if ix + 1 < len(suffixes):
                    next_score = weights[aid] + suffixes[ix + 1][0]
                    next_path = (aid,) + suffixes[ix + 1][1]
                    heapq.heappush(heap, (next_score, next_path, aid, ix + 1, v))
            labels[u] = best
        return labels.get(d["_source_node"], [])

def dual_maps(dual, graph):
    cap = dual["capacity_inequality_duals"]
    eq = dual["demand_equality_duals"]
    if set(cap) != set(graph.arcs) or set(eq) != set(graph.demands):
        raise ValueError("dual arc/demand coverage mismatch")
    mu = {a: float(v["marginal"] if isinstance(v, dict) else v) for a, v in cap.items()}
    pi = {d: float(v["marginal"] if isinstance(v, dict) else v) for d, v in eq.items()}
    if any(not math.isfinite(v) or v > TOL for v in mu.values()) or any(not math.isfinite(v) for v in pi.values()):
        raise ValueError("nonfinite or positive inequality dual")
    return mu, pi

def evaluate(graph, pool, dual, solution=None, tolerance=TOL):
    mu, pi = dual_maps(dual, graph)
    lower = dual["lower_bound_marginals"]
    upper = dual["upper_bound_marginals"]
    path_sets = defaultdict(set)
    id_seen = set()
    stationarity_max = 0.0
    flow_map = {r["column_id"]: float(r["flow"]) for r in solution} if solution else {}
    demand_flow = defaultdict(float)
    arc_flow = defaultdict(float)
    objective = 0.0
    for row in pool:
        cid, did = row["column_id"], row["demand_id"]
        if cid in id_seen or did not in graph.demands:
            raise ValueError(f"duplicate column or unknown demand: {cid}")
        id_seen.add(cid)
        path = sequence(row["arc_sequence"])
        cost = graph.validate_path(did, path)
        if abs(cost - float(row["generalized_cost"])) > tolerance:
            raise ValueError(f"path cost mismatch: {cid}")
        path_sets[did].add(path)
        raw = cost - pi[did] - sum(mu[a] for a in path)
        if cid not in lower or cid not in upper:
            raise ValueError(f"bound marginal missing: {cid}")
        lower_mu, upper_mu = float(lower[cid]), float(upper[cid])
        if lower_mu < -tolerance or upper_mu > tolerance:
            raise ValueError(f"bound marginal sign mismatch: {cid}")
        residual = raw - lower_mu - upper_mu
        stationarity_max = max(stationarity_max, abs(residual))
        if solution is not None:
            if cid not in flow_map:
                raise ValueError(f"solution missing column: {cid}")
            flow = flow_map[cid]
            if flow < -tolerance or flow > float(graph.demands[did]["volume"]) + tolerance:
                raise ValueError(f"flow outside bounds: {cid}")
            if flow > tolerance and lower_mu > tolerance:
                raise ValueError(f"lower-bound complementarity failure: {cid}")
            if flow < float(graph.demands[did]["volume"]) - tolerance and upper_mu < -tolerance:
                raise ValueError(f"upper-bound complementarity failure: {cid}")
            demand_flow[did] += flow
            objective += flow * cost
            for aid in path:
                arc_flow[aid] += flow
    if set(lower) != id_seen or set(upper) != id_seen:
        raise ValueError("bound marginal column coverage mismatch")
    if stationarity_max > tolerance:
        raise ValueError(f"stationarity mismatch {stationarity_max}")
    max_demand = max((abs(demand_flow[d] - float(r["volume"])) for d, r in graph.demands.items()), default=0.0) if solution is not None else None
    max_capacity = max((max(0.0, arc_flow[a] - float(r["capacity"])) for a, r in graph.arcs.items()), default=0.0) if solution is not None else None
    if solution is not None and (max_demand > tolerance or max_capacity > tolerance):
        raise ValueError(f"primal infeasible: OD {max_demand}, capacity {max_capacity}")
    if solution is not None:
        for aid, a in graph.arcs.items():
            slack = float(a["capacity"]) - arc_flow[aid]
            if slack > tolerance and mu[aid] < -tolerance:
                raise ValueError(f"capacity dual complementarity failure: {aid}")
    weights = {aid: float(a["cost"]) - mu[aid] for aid, a in graph.arcs.items()}
    pool_signature = canonical_hash(pool)
    pool_path_identity_signature = canonical_hash([(r["column_id"], r["demand_id"], r["arc_sequence"]) for r in pool])
    dual_signature = canonical_hash({"pi": pi, "mu": mu, "lower": lower, "upper": upper})
    by_demand = []
    for did in sorted(graph.demands):
        existing = path_sets[did]
        ranked = graph.k_shortest(did, weights, len(existing) + 1)
        first = None
        examined = 0
        duplicates = 0
        for weighted, path in ranked:
            examined += 1
            if path in existing:
                duplicates += 1
            else:
                first = (weighted, path)
                break
        if first:
            weighted, path = first
            original = graph.validate_path(did, path)
            cap_sum = sum(mu[a] for a in path)
            rc = original - cap_sum - pi[did]
            if abs(rc - (weighted - pi[did])) > 1e-8:
                raise ValueError(f"reduced-cost reconstruction mismatch: {did}")
            exhausted = False
        else:
            path, original, cap_sum, rc = (), None, None, None
            exhausted = len(ranked) < len(existing) + 1
            if not exhausted:
                raise ValueError(f"path enumeration incomplete: {did}")
        by_demand.append({"demand_id": did, "existing_path_count": len(existing),
                          "distinct_paths_examined": examined, "generated_duplicates_skipped": duplicates,
                          "all_feasible_paths_exhausted": exhausted, "min_ungenerated_reduced_cost": rc,
                          "min_ungenerated_path_arc_sequence": "|".join(path), "original_path_cost": original,
                          "capacity_dual_sum_raw": cap_sum, "demand_equality_dual_raw": pi[did],
                          "graph_signature": graph.graph_signature, "demand_signature": graph.demand_signature,
                          "pool_signature": pool_signature, "pool_path_identity_signature": pool_path_identity_signature,
                          "dual_signature": dual_signature,
                          "tolerance": tolerance, "closure_pass": exhausted or rc >= -tolerance})
    return {"status": "PASS", "closure_pass": all(r["closure_pass"] for r in by_demand),
            "by_demand": by_demand, "graph_signature": graph.graph_signature,
            "demand_signature": graph.demand_signature, "pool_signature": pool_signature,
            "pool_path_identity_signature": pool_path_identity_signature,
            "dual_signature": dual_signature, "topological_order_signature": canonical_hash(graph.topo),
            "node_count": len(graph.nodes), "arc_count": len(graph.arcs), "arc_type_counts": dict(graph.arc_types),
            "demand_count": len(graph.demands), "pool_count": len(pool),
            "stationarity_max_abs": stationarity_max, "objective_recomputed": objective if solution is not None else None,
            "max_demand_residual": max_demand, "max_capacity_violation": max_capacity,
            "tolerance": tolerance, "optimization_invocations": 0}

def evaluate_files(data, pool_path, dual_path, solution_path=None, out=None, tolerance=TOL):
    data = Path(data)
    graph = DAG(read_csv(data / "dynamic_node.csv"), read_csv(data / "dynamic_arc.csv"), read_csv(data / "dynamic_demand.csv"))
    pool = read_csv(pool_path)
    dual = json.loads(Path(dual_path).read_text(encoding="utf-8"))
    solution = read_csv(solution_path) if solution_path else None
    result = evaluate(graph, pool, dual, solution, tolerance)
    if out:
        out = Path(out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "INDEPENDENT_PRICING_CLOSURE_CERTIFICATE.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        write_csv(out / "INDEPENDENT_PRICING_CLOSURE_BY_DEMAND.csv", result["by_demand"])
    return result

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    for arg in ("data", "pool", "dual"):
        p.add_argument("--" + arg, required=True)
    p.add_argument("--solution")
    p.add_argument("--out")
    p.add_argument("--tolerance", type=float, default=TOL)
    a = p.parse_args()
    result = evaluate_files(a.data, a.pool, a.dual, a.solution, a.out, a.tolerance)
    print(json.dumps({k: v for k, v in result.items() if k != "by_demand"}))
