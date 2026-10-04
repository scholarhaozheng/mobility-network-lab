"""Saved-result replay on original Hong Kong turn states; no optimizer calls."""
from __future__ import annotations
import argparse
import csv
import hashlib
import heapq
import json
import math
from collections import deque
from pathlib import Path

import numpy as np

BASE = Path(__file__).resolve().parent
SOURCE = BASE.parents[1] / "docs/assets/hong_kong/full_stack_r5/r2r4_baseline"
if not SOURCE.exists():
    SOURCE = BASE / "SOURCE_SNAPSHOT"
GATES = json.loads((BASE / "NUMERICAL_POLICY.json").read_text())["gates"]


def rows(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit_pool(tier):
    inst, pool = BASE / f"{tier}_instance", BASE / f"{tier}_pool"
    manifest = json.loads((inst / "manifest.json").read_text())
    links, od, paths = rows(inst / "link.csv"), rows(inst / "demand.csv"), rows(pool / "paths.csv")
    cross = {r["expanded_link_id"]: r for r in rows(SOURCE / "phase_a/static_input/expanded_network_crosswalk.csv")}
    edge = {r["link_id"]: r for r in links}
    banned = {(r["from_link_id"], r["to_link_id"]) for r in rows(SOURCE / "phase_a/movement_resolved.csv")
              if r["classification"] == "RESOLVED_PROHIBITED" and r["from_link_id"] and r["to_link_id"]}
    bad = []
    prohibited_used = 0
    by_od = [0] * len(od)
    used_ids = set()
    paths_by_od = [[] for _ in od]
    seed = [float(r["flow"]) for r in rows(pool / "f0.csv")]
    physical_projection = {}
    for i, path in enumerate(paths):
        oi = int(path["od_index"])
        by_od[oi] += 1
        paths_by_od[oi].append(path)
        seq = path["link_id_sequence"].split(";")
        at = od[oi]["o_node_id"]
        visited = {at}
        previous_physical = None
        physical_ids = []
        for n, lid in enumerate(seq):
            if lid not in edge or lid not in cross:
                bad.append([i, lid, "unrecognized_link"]); break
            e, x = edge[lid], cross[lid]
            if e["from_node_id"] != at:
                bad.append([i, lid, "discontinuous"])
            at = e["to_node_id"]
            if at in visited:
                bad.append([i, lid, "repeated_node"])
            visited.add(at)
            cls = x["link_class"]
            if cls == "physical":
                if x["physical_link_id"] != lid:
                    bad.append([i, lid, "physical_identity"])
                physical_ids.append(lid)
                physical_projection[lid] = physical_projection.get(lid, 0.0) + seed[i]
                previous_physical = lid
            elif cls == "nonphysical_allowed_movement":
                if previous_physical != x["from_physical_link_id"]:
                    bad.append([i, lid, "movement_entry"])
                if n + 1 >= len(seq) or seq[n+1] != x["to_physical_link_id"]:
                    bad.append([i, lid, "movement_exit"])
            elif cls == "nonphysical_zone_origin":
                if n != 0 or x["zone_id"] != str(int(od[oi]["o_node_id"]) - 4000000000):
                    bad.append([i, lid, "origin_state"])
            elif cls == "nonphysical_zone_destination":
                if n != len(seq)-1 or x["zone_id"] != str(int(od[oi]["d_node_id"]) - 4100000000):
                    bad.append([i, lid, "destination_state"])
            else:
                bad.append([i, lid, "unknown_class"])
            used_ids.add(lid)
        for pair in zip(physical_ids[:-1], physical_ids[1:]):
            if pair in banned:
                prohibited_used += 1
                bad.append([i, pair, "prohibited_turn"])
        if at != od[oi]["d_node_id"]:
            bad.append([i, "", "wrong_endpoint"])
        if not physical_ids:
            bad.append([i, "", "no_physical_link"])
    result = {"tier": tier, "instance_signature": manifest["instance_signature"],
            "path_pool_sha256": digest(pool / "paths.csv"), "od_count": len(od),
            "path_count": len(paths), "paths_per_od": by_od, "all_K5": all(v == 5 for v in by_od),
            "graph_link_count": len(links), "used_link_count": len(used_ids),
            "path_error_count": len(bad), "prohibited_turns_in_paths": prohibited_used,
            "prohibited_source_pair_count": len(banned), "path_errors": bad[:25],
            "turn_legality": "PASS" if not bad else "FAIL",
            "physical_projection": {"unique_original_link_ids": len(physical_projection),
                                    "positive_seed_physical_links": sum(v > 1e-6 for v in physical_projection.values()),
                                    "all_link_ids_original": all(lid == cross[lid]["physical_link_id"] for lid in physical_projection)},
            "crosswalk_sha256": digest(SOURCE / "phase_a/static_input/expanded_network_crosswalk.csv")}
    if tier == "H1":
        singleton_indices = [i for i, count in enumerate(by_od) if count == 1]
        if len(singleton_indices) != 1:
            raise ValueError(f"H1 singleton regression: found {singleton_indices}")
        oi = singleton_indices[0]
        origin = od[oi]["o_node_id"]
        destination = od[oi]["d_node_id"]
        o_zone = int(origin) - 4000000000
        d_zone = int(destination) - 4100000000
        sequence = paths_by_od[oi][0]["link_id_sequence"].split(";")
        adjacency = {}
        for edge_row in links:
            adjacency.setdefault(edge_row["from_node_id"], []).append(
                (edge_row["to_node_id"], edge_row["link_id"]))

        def reachable_without(blocked_link_id):
            seen = {origin}
            queue = deque([origin])
            while queue:
                at = queue.popleft()
                if at == destination:
                    return True
                for nxt, lid in adjacency.get(at, ()):
                    if lid != blocked_link_id and nxt not in seen:
                        seen.add(nxt)
                        queue.append(nxt)
            return False

        removals = [reachable_without(lid) for lid in sequence]
        result["singleton_path_od"] = {
            "od_index": oi, "source_origin_zone": o_zone,
            "source_destination_zone": d_zone, "observed_path_count": by_od[oi],
            "edge_count": len(sequence),
            "reachable_after_each_edge_removal": removals,
            "all_edge_removals_disconnect": not any(removals),
        }
        regression = [(i, by_od[i]) for i, row in enumerate(od)
                      if int(row["o_node_id"]) - 4000000000 == 80
                      and int(row["d_node_id"]) - 4100000000 == 38]
        if regression != [(15, 5)] or (oi, o_zone, d_zone, len(sequence)) != (0, 11, 12, 13) or any(removals):
            raise ValueError("H1 singleton/80-to-38 identity regression failed")
        result["five_path_regression_od"] = {
            "od_index": 15, "source_origin_zone": 80,
            "source_destination_zone": 38, "observed_path_count": 5,
        }
    return result


def distances(links, weights, origin):
    adj = {}
    for i, e in enumerate(links):
        adj.setdefault(e["from_node_id"], []).append((e["to_node_id"], weights[i]))
    best = {origin: 0.0}
    todo = [(0.0, origin)]
    while todo:
        cost, u = heapq.heappop(todo)
        if cost > best[u] + 1e-12:
            continue
        for v, w in adj.get(u, ()):
            alt = cost + w
            if alt < best.get(v, math.inf) - 1e-12:
                best[v] = alt
                heapq.heappush(todo, (alt, v))
    return best


def check_solution(kind):
    inst, pool = BASE / "H1_instance", BASE / "H1_pool"
    manifest = json.loads((inst / "manifest.json").read_text())
    links, od, paths = rows(inst / "link.csv"), rows(inst / "demand.csv"), rows(pool / "paths.csv")
    pool_audit = audit_pool("H1")
    edge_index = {e["link_id"]: i for i, e in enumerate(links)}
    q = np.array([float(o["volume"]) for o in od])
    basis_hash = None
    native_v = None
    solver_success = None
    if kind == "finite":
        folder = BASE / "H1_finite"
        records = rows(folder / "path_flow.csv")
        f = np.array([float(r["flow"]) for r in records])
        native_v = np.array([float(r["flow_pce_per_period"]) for r in rows(folder / "link_flow.csv")])
        solver = json.loads((folder / "run.json").read_text())
        solver_success = bool(solver["solver_success"])
    else:
        folder = BASE / f"H1_L3_rank{kind}"
        basis_dir = BASE / f"H1_basis_rank{kind}"
        basis_hash = digest(basis_dir / "basis.npz")
        status = json.loads((folder / "status.json").read_text())
        if not status.get("attempted_outer"):
            return {"status": "RESOURCE_LIMIT" if "RESOURCE" in status["status"] else "SOLVER_TERMINATED_BUT_NOT_ACCEPTED",
                    "reason": status["status"], "instance_signature": manifest["instance_signature"],
                    "path_pool_sha256": pool_audit["path_pool_sha256"], "basis_sha256": basis_hash,
                    "saved_result_replay": False}
        final = folder / f"outer_{status['attempted_outer']:02d}_solution.npz"
        if not final.exists():
            return {"status": "SOLVER_TERMINATED_BUT_NOT_ACCEPTED", "reason": "No saved iterate",
                    "instance_signature": manifest["instance_signature"], "path_pool_sha256": pool_audit["path_pool_sha256"],
                    "basis_sha256": basis_hash, "saved_result_replay": False}
        with np.load(basis_dir / "basis.npz") as data:
            U, major, minor = data["U"], data["major"], data["minor"]
        with np.load(final) as data:
            f = np.zeros(len(paths))
            f[major] = data["x1"]
            f[minor] = U @ data["theta"]
            native_v = data["v"]
        native = json.loads((folder / f"outer_{status['attempted_outer']:02d}_native.json").read_text())
        solver_success = native.get("termination") == "optimal"
    if len(f) != len(paths) or len(native_v) != len(links):
        raise ValueError("Saved solution dimension mismatch")
    v = np.zeros(len(links))
    qhat = np.zeros(len(od))
    pool_min = np.full(len(od), math.inf)
    seq_index = []
    for path in paths:
        seq_index.append([edge_index[lid] for lid in path["link_id_sequence"].split(";")])
    for j, path in enumerate(paths):
        oi = int(path["od_index"])
        qhat[oi] += f[j]
        for k in seq_index[j]:
            v[k] += f[j]
    t0 = np.array([float(e["vdf_fftt"]) for e in links])
    alpha = np.array([float(e["vdf_alpha"]) for e in links])
    beta = np.array([float(e["vdf_beta"]) for e in links])
    cap = np.array([float(e["capacity"]) for e in links])
    cost = t0 * (1 + alpha * (np.maximum(v, 0) / cap) ** beta)
    obj = float(np.sum(t0 * v + (t0 * alpha / (beta + 1)) * v * (v / cap) ** beta))
    total = float(np.dot(v, cost))
    for j, path in enumerate(paths):
        oi = int(path["od_index"])
        pool_min[oi] = min(pool_min[oi], float(np.sum(cost[seq_index[j]])))
    shortest = {o["o_node_id"]: distances(links, cost, o["o_node_id"]) for o in od}
    full_min = np.array([shortest[o["o_node_id"]][o["d_node_id"]] for o in od])
    pool_gap = (total - float(np.dot(q, pool_min))) / max(total, 1e-12)
    full_gap = (total - float(np.dot(q, full_min))) / max(total, 1e-12)
    cross = {r["expanded_link_id"]: r for r in rows(SOURCE / "phase_a/static_input/expanded_network_crosswalk.csv")}
    physical = {cross[e["link_id"]]["physical_link_id"]: float(v[i]) for i, e in enumerate(links)
                if cross[e["link_id"]]["link_class"] == "physical"}
    native_physical = {cross[e["link_id"]]["physical_link_id"]: float(native_v[i]) for i, e in enumerate(links)
                       if cross[e["link_id"]]["link_class"] == "physical"}
    positive = sorted(k for k, x in physical.items() if x > 1e-6)
    max_od = float(np.max(np.abs(qhat - q)))
    od_l1 = float(np.sum(np.abs(qhat - q))) / max(float(np.sum(q)), 1e-12)
    link_err = float(np.max(np.abs(v - native_v)))
    valid = (pool_audit["path_error_count"] == 0 and float(np.min(f)) >= -GATES["negative_flow_abs"]
             and max_od <= GATES["max_od_error_abs"] + GATES["max_od_error_rel"] * max(1, float(np.max(q)))
             and od_l1 <= GATES["total_od_l1_rel"] and link_err <= GATES["link_reconstruction_abs"])
    status = ("SOLVED_WITHIN_DECLARED_TOLERANCE" if solver_success and valid and abs(full_gap) <= GATES["full_relative_gap_abs"]
              else "RESTRICTED_POOL_ONLY" if solver_success and valid and abs(pool_gap) <= GATES["full_relative_gap_abs"]
              else "SOLVER_TERMINATED_BUT_NOT_ACCEPTED")
    fw = json.loads((BASE / "H1_FW/run.json").read_text())
    return {"status": status, "method": kind, "solver_success": solver_success,
            "instance_signature": manifest["instance_signature"], "path_pool_sha256": pool_audit["path_pool_sha256"],
            "basis_sha256": basis_hash, "path_error_count": pool_audit["path_error_count"],
            "min_path_flow": float(np.min(f)), "max_abs_od_residual": max_od, "relative_od_l1": od_l1,
            "max_movement_link_reconstruction_error": link_err,
            "physical_link_count": len(physical), "max_physical_projection_residual": max(abs(physical[k]-native_physical[k]) for k in physical),
            "beckmann_objective_recomputed": obj, "objective_minus_fw": obj - fw["objective"],
            "finite_pool_relative_gap": pool_gap, "full_graph_relative_gap": full_gap,
            "positive_physical_links_1e_minus_6": len(positive),
            "positive_physical_link_ids_sha256": hashlib.sha256("\n".join(positive).encode()).hexdigest(),
            "saved_result_replay": True, "gates": GATES}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=["pool", "finite", "26", "52"])
    a = parser.parse_args()
    result = {tier: audit_pool(tier) for tier in ("H0", "H1") if (BASE / f"{tier}_pool/paths.csv").exists()} if a.kind == "pool" else check_solution(a.kind)
    name = {"pool": "PATH_POOL_AUDIT.json", "finite": "FINITE_PATH_INDEPENDENT_CHECK.json",
            "26": "L3_RANK26_INDEPENDENT_CHECK.json", "52": "L3_RANK52_INDEPENDENT_CHECK.json"}[a.kind]
    (BASE / name).write_text(json.dumps(result, indent=2, allow_nan=False))
    print(json.dumps(result, indent=2, allow_nan=False))
