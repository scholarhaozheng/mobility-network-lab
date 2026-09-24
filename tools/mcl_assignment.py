"""Input-driven, single-class static GMNS assignment (research candidate R1).

The numerical core follows the public static FW implementation's BPR
cost/integral and per-origin all-or-nothing convention. This adapter keeps
parallel link identities, validates units and writes independent inputs.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import heapq
import json
import math
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

VERSION = "MCL_SCALABLE_ASSIGNMENT_R1"
GATES = {"max_od_error_abs": 1e-6, "max_od_error_rel": 1e-8,
         "total_od_l1_rel": 1e-8, "full_relative_gap_abs": 1e-5,
         "negative_flow_abs": 1e-8, "link_reconstruction_abs": 1e-7}


def rows(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_rows(path, records, fields):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".partial")
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")
    tmp.replace(path)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def number(value, name, positive=False, nonnegative=False):
    try:
        x = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"missing/invalid {name}: {value!r}") from exc
    if not math.isfinite(x) or (positive and x <= 0) or (nonnegative and x < 0):
        raise ValueError(f"out-of-contract {name}: {value!r}")
    return x


def config(path):
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    allowed = {"scenario", "period", "demand_unit", "period_hours", "capacity_basis",
               "pce_factor", "unreachable_policy", "access_csv", "link_file",
               "physical_only", "max_iterations", "gap_tolerance", "source_note"}
    unknown = set(obj) - allowed
    if unknown:
        raise ValueError(f"unknown config fields: {sorted(unknown)}")
    for key in ("scenario", "period", "demand_unit", "period_hours", "capacity_basis", "pce_factor"):
        if key not in obj:
            raise ValueError(f"missing config field {key}")
    if obj["demand_unit"] not in ("vehicle_trips_per_period", "vehicles_per_hour", "pce_per_hour"):
        raise ValueError("unsupported demand_unit")
    if obj["capacity_basis"] not in ("effective_period_pce", "hourly_pce_per_lane"):
        raise ValueError("unsupported capacity_basis")
    number(obj["period_hours"], "period_hours", positive=True)
    number(obj["pce_factor"], "pce_factor", positive=True)
    if obj.get("unreachable_policy", "error") not in ("error", "exclude_and_account"):
        raise ValueError("unsupported unreachable_policy")
    return obj


def safe_output(output, inputs):
    out = Path(output).resolve()
    if out.exists() and any(out.iterdir()):
        raise ValueError(f"output is not empty: {out}")
    for raw in inputs:
        p = Path(raw).resolve()
        if out == p or p in out.parents or out in p.parents:
            raise ValueError("source/output overlap")
    return out


def graph(links):
    adj = defaultdict(list)
    nodes = set()
    for i, r in enumerate(links):
        u, v = r["from_node_id"], r["to_node_id"]
        nodes.update((u, v))
        adj[u].append((v, i))
    for seq in adj.values():
        seq.sort(key=lambda x: (links[x[1]]["link_id"], x[0]))
    return adj, nodes


def shortest(links, adj, source, costs):
    dist = {source: 0.0}
    pred = {}
    heap = [(0.0, source)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u] + 1e-12:
            continue
        for v, i in adj.get(u, ()):
            nd = d + costs[i]
            if nd < dist.get(v, math.inf) - 1e-12:
                dist[v] = nd
                pred[v] = (u, i)
                heapq.heappush(heap, (nd, v))
    return dist, pred


def trace(pred, source, target):
    seq = []
    at = target
    while at != source:
        if at not in pred:
            return None
        at, i = pred[at]
        seq.append(i)
    seq.reverse()
    return tuple(seq)


def prepare(args):
    t = time.perf_counter()
    source = Path(args.input).resolve()
    demand = Path(args.demand).resolve()
    cfg = config(args.config)
    link_path = source / cfg.get("link_file", "link.csv")
    access_path = ((Path(cfg["access_csv"]) if Path(cfg["access_csv"]).is_absolute()
                    else Path(args.config).resolve().parent / cfg["access_csv"]).resolve()
                   if cfg.get("access_csv") else None)
    out = safe_output(args.output, [source, demand, args.config] + ([access_path] if access_path else []))
    for turn_name in ("turn.csv", "turn_restrictions.csv"):
        if (source / turn_name).exists():
            raise ValueError("turn restrictions require a supported turn-state contract")
    raw_links = rows(link_path)
    node_path = source / "node.csv"
    declared_nodes = None
    if node_path.is_file():
        node_rows = rows(node_path)
        declared_nodes = [r.get("node_id", "") for r in node_rows]
        if not declared_nodes or any(not x for x in declared_nodes) or len(set(declared_nodes)) != len(declared_nodes):
            raise ValueError("empty/duplicate GMNS node_id")
    if any("allowed_uses" in r and r["allowed_uses"].strip() not in ("", "auto", "car", "all") for r in raw_links):
        raise ValueError("unsupported link mode permission; single auto class required")
    links = []
    seen_links = set()
    for r in raw_links:
        if cfg.get("physical_only", True) and r.get("is_physical", "true").lower() != "true":
            continue
        lid = r["link_id"]
        if not lid or lid in seen_links:
            raise ValueError("empty/duplicate physical link_id")
        seen_links.add(lid)
        t0 = number(r.get("vdf_fftt"), "vdf_fftt", positive=True)
        alpha = number(r.get("vdf_alpha"), "vdf_alpha", nonnegative=True)
        beta = number(r.get("vdf_beta"), "vdf_beta", positive=True)
        cap = number(r.get("capacity"), "capacity", positive=True)
        if cfg["capacity_basis"] == "hourly_pce_per_lane":
            cap *= number(r.get("lanes"), "lanes", positive=True) * number(cfg["period_hours"], "period_hours")
            cap *= number(r.get("vdf_plf"), "vdf_plf", positive=True)
        links.append({"link_id": lid, "from_node_id": r["from_node_id"], "to_node_id": r["to_node_id"],
                      "vdf_fftt": t0, "vdf_alpha": alpha, "vdf_beta": beta,
                      "capacity": cap, "capacity_source": r["capacity"],
                      "geometry": r.get("geometry", "")})
    if not links:
        raise ValueError("no physical links")
    if declared_nodes is not None:
        declared_node_set = set(declared_nodes)
        if any(r["from_node_id"] not in declared_node_set or
               r["to_node_id"] not in declared_node_set for r in links):
            raise ValueError("physical link endpoint absent from node.csv")
    links.sort(key=lambda r: r["link_id"])
    adj, nodes = graph(links)
    access = {}
    if access_path:
        for r in rows(access_path):
            z = r.get("zone_id") or r.get("original_h3_zone_id")
            n = r.get("access_node_id") or r.get("source_physical_access_node_id")
            if not z or not n or (z in access and access[z] != n):
                raise ValueError("missing/ambiguous zone access")
            access[z] = n
    raw_demand = rows(demand)
    if not raw_demand:
        raise ValueError("empty demand")
    allowed_demand_columns = {"o_node_id", "d_node_id", "o_zone_id", "d_zone_id", "volume"}
    if set(raw_demand[0]) - allowed_demand_columns:
        raise ValueError("unsupported demand columns; class/time must be resolved explicitly")
    prepared = []
    ledger = []
    aggregate = defaultdict(float)
    factor = number(cfg["pce_factor"], "pce_factor", positive=True)
    hours = number(cfg["period_hours"], "period_hours", positive=True)
    for idx, r in enumerate(raw_demand):
        original_o = r.get("o_zone_id", r.get("o_node_id", ""))
        original_d = r.get("d_zone_id", r.get("d_node_id", ""))
        if not original_o or not original_d:
            raise ValueError("missing OD identifier")
        o = access.get(original_o) if access_path else original_o
        d = access.get(original_d) if access_path else original_d
        q = number(r.get("volume"), "volume", nonnegative=True)
        if cfg["demand_unit"] == "vehicles_per_hour":
            q *= hours * factor
        elif cfg["demand_unit"] == "pce_per_hour":
            q *= hours
        else:
            q *= factor
        reason = "loaded"
        if original_o == original_d:
            reason = "intrazonal"
        elif o is None or d is None:
            reason = "unresolved_access"
        elif o == d:
            reason = "same_access_node"
        elif o not in nodes or d not in nodes:
            reason = "node_absent"
        ledger.append({"row": idx, "source_o": original_o, "source_d": original_d,
                       "o_node_id": o or "", "d_node_id": d or "", "input_volume": r["volume"],
                       "effective_pce": q, "status": reason})
        if reason == "loaded" and q > 0:
            aggregate[(o, d)] += q
        elif reason in ("unresolved_access", "node_absent") and cfg.get("unreachable_policy", "error") == "error":
            raise ValueError(f"OD {idx}: {reason}")
    for (o, d), q in sorted(aggregate.items()):
        prepared.append({"o_node_id": o, "d_node_id": d, "volume": q})
    # Structural unreachability is an explicit ledger category.
    by_origin = defaultdict(list)
    for r in prepared:
        by_origin[r["o_node_id"]].append(r)
    reachable = []
    for o, od_rows in by_origin.items():
        dist, _ = shortest(links, adj, o, [r["vdf_fftt"] for r in links])
        for r in od_rows:
            if r["d_node_id"] not in dist:
                if cfg.get("unreachable_policy", "error") == "error":
                    raise ValueError(f"unreachable OD {o}->{r['d_node_id']}")
                for x in ledger:
                    if x["o_node_id"] == o and x["d_node_id"] == r["d_node_id"] and x["status"] == "loaded":
                        x["status"] = "unreachable"
            else:
                reachable.append(r)
    if not reachable:
        raise ValueError("no loadable OD")
    out.mkdir(parents=True)
    write_rows(out / "link.csv", links, ["link_id", "from_node_id", "to_node_id", "vdf_fftt", "vdf_alpha", "vdf_beta", "capacity", "capacity_source", "geometry"])
    write_rows(out / "demand.csv", reachable, ["o_node_id", "d_node_id", "volume"])
    write_rows(out / "demand_ledger.csv", ledger, ["row", "source_o", "source_d", "o_node_id", "d_node_id", "input_volume", "effective_pce", "status"])
    manifest = {"schema": VERSION, "scenario": cfg["scenario"], "period": cfg["period"],
                "demand_unit_input": cfg["demand_unit"], "assignment_unit": "pce_per_declared_period",
                "period_hours": hours, "capacity_basis": cfg["capacity_basis"], "pce_factor": factor,
                "source_hashes": {"link": sha(link_path), "demand": sha(demand), "config": sha(args.config),
                                  **({"node": sha(node_path)} if declared_nodes is not None else {}),
                                  **({"access": sha(access_path)} if access_path else {})},
                "physical_links": len(links), "declared_nodes": len(declared_nodes) if declared_nodes is not None else None,
                "source_rows": len(raw_demand), "node_od": len(reachable),
                "source_effective_pce": sum(x["effective_pce"] for x in ledger),
                "loaded_pce": sum(x["volume"] for x in reachable),
                "excluded_by_reason_pce": {k: sum(x["effective_pce"] for x in ledger if x["status"] == k)
                                           for k in sorted({x["status"] for x in ledger}) if k != "loaded"},
                "prepare_seconds": time.perf_counter() - t}
    manifest["link_sha256"] = sha(out / "link.csv")
    manifest["demand_sha256"] = sha(out / "demand.csv")
    manifest["instance_signature"] = hashlib.sha256((manifest["link_sha256"] + manifest["demand_sha256"] + sha(args.config)).encode()).hexdigest()
    atomic_json(out / "manifest.json", manifest)
    return manifest


def load_instance(path):
    path = Path(path)
    m = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
    if sha(path / "link.csv") != m["link_sha256"] or sha(path / "demand.csv") != m["demand_sha256"]:
        raise ValueError("prepared instance integrity failure")
    links = rows(path / "link.csv")
    od = rows(path / "demand.csv")
    return m, links, od


def costs(v, links):
    return [float(r["vdf_fftt"]) * (1 + float(r["vdf_alpha"]) * (max(0.0, v[i]) / float(r["capacity"])) ** float(r["vdf_beta"])) for i, r in enumerate(links)]


def objective(v, links):
    return sum(float(r["vdf_fftt"]) * v[i] + float(r["vdf_fftt"]) * float(r["vdf_alpha"]) / (float(r["vdf_beta"]) + 1) * v[i] * (v[i] / float(r["capacity"])) ** float(r["vdf_beta"]) for i, r in enumerate(links))


def aon(links, adj, od, weights):
    v = [0.0] * len(links)
    paths = {}
    shortest_sum = 0.0
    by_origin = defaultdict(list)
    for i, r in enumerate(od):
        by_origin[r["o_node_id"]].append((i, r))
    for o, pairs in by_origin.items():
        dist, pred = shortest(links, adj, o, weights)
        for i, r in pairs:
            d = r["d_node_id"]
            if d not in dist:
                raise ValueError(f"unreachable during solve {o}->{d}")
            q = float(r["volume"])
            shortest_sum += q * dist[d]
            seq = trace(pred, o, d)
            paths[i] = seq
            for j in seq:
                v[j] += q
    return v, paths, shortest_sum


def solve_fw(instance, output, max_iterations=300, gap_tolerance=1e-5):
    t = time.perf_counter()
    m, links, od = load_instance(instance)
    out = safe_output(output, [instance])
    adj, _ = graph(links)
    v, seed_paths, _ = aon(links, adj, od, [float(r["vdf_fftt"]) for r in links])
    path_flows = {(i, p): float(od[i]["volume"]) for i, p in seed_paths.items()}
    history = []
    status = "ITERATION_LIMIT"
    for iteration in range(max_iterations + 1):
        c = costs(v, links)
        aux, paths, shortest_sum = aon(links, adj, od, c)
        total_cost = sum(a*b for a, b in zip(v, c))
        gap = total_cost - shortest_sum
        relative = gap / max(total_cost, 1e-12)
        history.append({"iteration": iteration, "objective": objective(v, links), "signed_gap": gap,
                        "relative_gap": relative})
        if abs(relative) <= gap_tolerance and gap >= -1e-8:
            status = "SOLVER_TERMINATED"
            break
        if iteration == max_iterations:
            break
        direction = [a-b for a, b in zip(aux, v)]
        deriv1 = sum(d*c0 for d, c0 in zip(direction, costs(aux, links)))
        if deriv1 <= 0:
            step = 1.0
        else:
            lo, hi = 0.0, 1.0
            for _ in range(45):
                mid = (lo + hi) / 2
                derivative = sum(d*c0 for d, c0 in zip(direction, costs([x + mid*y for x,y in zip(v,direction)], links)))
                if derivative < 0:
                    lo = mid
                else:
                    hi = mid
            step = (lo + hi) / 2
        v = [x + step*y for x,y in zip(v,direction)]
        for key in list(path_flows):
            path_flows[key] *= 1-step
            if path_flows[key] < 1e-15:
                del path_flows[key]
        for i, p in paths.items():
            key = (i,p)
            path_flows[key] = path_flows.get(key,0.0) + step*float(od[i]["volume"])
        history[-1]["step"] = step
    out.mkdir(parents=True)
    flow_rows = [{"link_id": r["link_id"], "flow_pce_per_period": v[i], "cost_min": costs(v, links)[i]}
                 for i,r in enumerate(links)]
    write_rows(out / "link_flow.csv", flow_rows, ["link_id", "flow_pce_per_period", "cost_min"])
    p_records = [{"od_index": i, "o_node_id": od[i]["o_node_id"], "d_node_id": od[i]["d_node_id"],
                  "link_ids": ";".join(links[j]["link_id"] for j in p), "flow": f}
                 for (i,p), f in sorted(path_flows.items())]
    write_rows(out / "path_flow.csv", p_records, ["od_index", "o_node_id", "d_node_id", "link_ids", "flow"])
    write_rows(out / "history.csv", history, ["iteration", "objective", "signed_gap", "relative_gap", "step"])
    record = {"schema": VERSION, "method": "fw", "instance_signature": m["instance_signature"],
              "invocation": [sys.executable] + sys.argv, "tool_source_sha256": sha(__file__),
              "python_version": sys.version.split()[0],
              "instance_path": str(Path(instance).resolve()), "solver_status": status,
              "iterations": len(history)-1, "solver_wall_seconds": time.perf_counter()-t,
              "objective": history[-1]["objective"], "signed_gap": history[-1]["signed_gap"],
              "relative_gap": history[-1]["relative_gap"], "path_count": len(p_records),
              "link_flow_sha256": sha(out / "link_flow.csv"), "path_flow_sha256": sha(out / "path_flow.csv")}
    atomic_json(out / "run.json", record)
    return record


def verify(run):
    t = time.perf_counter()
    run = Path(run)
    record = json.loads((run / "run.json").read_text(encoding="utf-8"))
    if record.get("solver",{}).get("status")=="RESOURCE_LIMIT":
        result={"status":"RESOURCE_LIMIT","reason":record["solver"]["reason"],
                "instance_signature":record["instance_signature"]}
        atomic_json(run/"verification.json",result)
        return result
    if record["method"] == "full-path":
        from mcl_path_methods import check_path_solution
        pool_path=record.get("pool_path",str(run/"pool"))
        result = check_path_solution(record["instance_path"],pool_path,run/"solution"/"path_flow.csv",
                                     run/"solution"/"link_flow.csv",record.get("fw_run"))
        result["verify_seconds"] = time.perf_counter()-t
        atomic_json(run/"verification.json",result)
        return result
    if record["method"] == "diagnostic-l3":
        from mcl_native_l3 import evaluate
        import numpy as np
        status=json.loads((run/"solution"/"status.json").read_text(encoding="utf-8"))
        if not status.get("attempted_outer"):
            result={"status":status["status"],"reason":status.get("reason","no returned iterate"),
                    "instance_signature":record["instance_signature"]}
        else:
            i=status["attempted_outer"]
            path=run/"solution"/f"outer_{i:02d}_solution.npz"
            if not path.is_file():
                result={"status":"SOLVER_TERMINATED_BUT_NOT_ACCEPTED","reason":"no returned iterate",
                        "instance_signature":record["instance_signature"]}
            else:
                result,_,f,v,v_path=evaluate(record["instance_path"],record.get("pool_path",str(run/"pool")),run/"basis",path,record.get("fw_run"))
                m,links,od=load_instance(record["instance_path"])
                write_rows(run/"link_flow.csv",[{"link_id":r["link_id"],"flow_pce_per_period":float(v_path[j])}
                                                 for j,r in enumerate(links)],["link_id","flow_pce_per_period"])
                result["native_status"] = status["status"]
        result["verify_seconds"] = time.perf_counter()-t
        atomic_json(run/"verification.json",result)
        return result
    m, links, od = load_instance(record["instance_path"])
    if m["instance_signature"] != record["instance_signature"]:
        raise ValueError("run/instance signature mismatch")
    if sha(run / "link_flow.csv") != record["link_flow_sha256"] or sha(run / "path_flow.csv") != record["path_flow_sha256"]:
        raise ValueError("run output integrity failure")
    flow = rows(run / "link_flow.csv")
    paths = rows(run / "path_flow.csv")
    if [x["link_id"] for x in flow] != [x["link_id"] for x in links]:
        raise ValueError("link identities/order changed")
    edge = {r["link_id"]: i for i,r in enumerate(links)}
    reconstructed = [0.0]*len(links)
    od_sum = [0.0]*len(od)
    min_path = math.inf
    neg_path_mass = 0.0
    for p in paths:
        k = int(p["od_index"])
        f = number(p["flow"], "path flow")
        min_path = min(min_path, f)
        neg_path_mass += max(0.0, -f)
        if (p["o_node_id"], p["d_node_id"]) != (od[k]["o_node_id"],od[k]["d_node_id"]):
            raise ValueError("path OD identity mismatch")
        at = p["o_node_id"]
        visited = {at}
        for lid in p["link_ids"].split(";"):
            j = edge[lid]
            r = links[j]
            if r["from_node_id"] != at or r["to_node_id"] in visited:
                raise ValueError("discontinuous/cyclic path")
            at = r["to_node_id"]
            visited.add(at)
            reconstructed[j] += f
        if at != p["d_node_id"]:
            raise ValueError("path ends at wrong node")
        od_sum[k] += f
    v = [number(r["flow_pce_per_period"], "link flow") for r in flow]
    if min(v) < -GATES["negative_flow_abs"]:
        status = "SOLVER_TERMINATED_BUT_NOT_ACCEPTED"
    else:
        status = "PENDING"
    residuals = [od_sum[i]-float(r["volume"]) for i,r in enumerate(od)]
    max_od = max(abs(x) for x in residuals)
    l1 = sum(abs(x) for x in residuals)
    link_diff = max(abs(a-b) for a,b in zip(v,reconstructed))
    c = costs(v, links)
    adj, _ = graph(links)
    _, _, shortest_sum = aon(links, adj, od, c)
    gap = sum(a*b for a,b in zip(v,c)) - shortest_sum
    denominator = max(sum(a*b for a,b in zip(v,c)), 1e-12)
    rel = gap/denominator
    objective_checked = objective(v, links)
    od_gate = all(abs(residuals[i]) <= GATES["max_od_error_abs"]+GATES["max_od_error_rel"]*max(1,float(od[i]["volume"])) for i in range(len(od)))
    accepted = (status == "PENDING" and od_gate and l1/max(sum(float(x["volume"]) for x in od),1e-12) <= GATES["total_od_l1_rel"]
                and link_diff <= GATES["link_reconstruction_abs"] and abs(rel) <= GATES["full_relative_gap_abs"]
                and abs(objective_checked-record["objective"]) <= 1e-7*max(1,objective_checked))
    status = "SOLVED_WITHIN_DECLARED_TOLERANCE" if accepted else "SOLVER_TERMINATED_BUT_NOT_ACCEPTED"
    result = {"status": status, "gates": GATES, "instance_signature": m["instance_signature"],
              "od_pairs": len(od), "physical_links": len(links), "demand_pce": sum(float(x["volume"]) for x in od),
              "path_count": len(paths), "min_path_flow_raw": min_path, "negative_path_mass_raw": neg_path_mass,
              "min_link_flow_raw": min(v), "negative_link_count_raw": sum(x<0 for x in v),
              "negative_link_mass_raw": sum(max(0,-x) for x in v),
              "max_od_residual": max_od, "od_residual_sum": sum(residuals), "od_residual_l1": l1,
              "max_link_reconstruction_error": link_diff, "objective_checked": objective_checked,
              "objective_reported": record["objective"], "signed_gap_numerator": gap,
              "gap_denominator": denominator, "full_network_relative_gap": rel,
              "positive_links_strict": sum(x>0 for x in v),
              "positive_links_display_1e_minus_6": sum(x>1e-6 for x in v),
              "verify_seconds": time.perf_counter()-t}
    atomic_json(run / "verification.json", result)
    return result


def plot(run, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import colors
    from matplotlib.collections import LineCollection
    from matplotlib.cm import ScalarMappable
    import re
    def save_map(fig, ax, caption, png, svg):
        # Equal-aspect maps can occupy only the center of a wide figure. Anchor
        # the footnote to the actual map edge, then trim the unused canvas.
        fig.subplots_adjust(left=.10,right=.90,top=.89,bottom=.15)
        fig.canvas.draw()
        fig.text(ax.get_position().x0,.018,caption,fontsize=8,color="#536b78",va="bottom")
        fig.savefig(png,dpi=160,bbox_inches="tight",pad_inches=.12)
        fig.savefig(svg,bbox_inches="tight",pad_inches=.12)
        plt.close(fig)
    t=time.perf_counter()
    run=Path(run); record=json.loads((run/"run.json").read_text(encoding="utf-8"))
    m, links, od=load_instance(record["instance_path"])
    flow_path=run/"link_flow.csv"
    if record["method"]=="full-path":flow_path=run/"solution"/"link_flow.csv"
    flow=rows(flow_path)
    out=safe_output(output,[run,record["instance_path"]]);out.mkdir(parents=True)
    maxflow=max(float(x["flow_pce_per_period"]) for x in flow)
    fw_comparator=None
    if record.get("fw_run"):
        fw_root=Path(record["fw_run"])
        fw_record=json.loads((fw_root/"run.json").read_text(encoding="utf-8"))
        if fw_record["instance_signature"]!=m["instance_signature"]:raise ValueError("plot FW comparator signature mismatch")
        fw_comparator=rows(fw_root/"link_flow.csv")
        if [r["link_id"] for r in fw_comparator]!=[r["link_id"] for r in links]:raise ValueError("plot FW comparator link order mismatch")
        maxflow=max(maxflow,max(float(r["flow_pce_per_period"]) for r in fw_comparator))
    parsed=0;segments=[];plot_rows=[];node_xy={}
    lon0,lat0=-71.08,42.35
    sx=111.320*math.cos(math.radians(lat0));sy=110.574
    for i,r in enumerate(links):
        geom=r.get("geometry","")
        if not geom.startswith("LINESTRING"):
            continue
        coords=[tuple(map(float,p.strip().split()[:2])) for p in re.sub(r"^LINESTRING\s*\(|\)$","",geom).split(",")]
        if len(coords)<2:continue
        parsed+=1
        xy=[((x-lon0)*sx,(y-lat0)*sy) for x,y in coords]
        segments.append(xy)
        node_xy.setdefault(r["from_node_id"],xy[0]);node_xy.setdefault(r["to_node_id"],xy[-1])
        f=float(flow[i]["flow_pce_per_period"])
        plot_rows.append({"link_index":i,"link_id":r["link_id"],"from_node_id":r["from_node_id"],"to_node_id":r["to_node_id"],
                          "geometry":geom,"flow_pce_per_period":f})
    if parsed:
        write_rows(out/"plot_link_table.csv",plot_rows,["link_index","link_id","from_node_id","to_node_id","geometry","flow_pce_per_period"])
        allxy=[p for seg in segments for p in seg]
        xs,ys=zip(*allxy);extent=[min(xs)-.4,max(xs)+.4,min(ys)-.4,max(ys)+.4]
        fig,ax=plt.subplots(figsize=(11.5,7.8),dpi=160)
        fig.patch.set_facecolor("white");ax.set_facecolor("#f7fafb")
        ax.add_collection(LineCollection(segments,colors="#d7e2e6",linewidths=.48,zorder=1))
        keep=[i for i,r in enumerate(plot_rows) if r["flow_pce_per_period"]>1e-6]
        norm=colors.PowerNorm(gamma=.5,vmin=0,vmax=max(maxflow,1e-12));cmap=plt.get_cmap("viridis")
        ax.add_collection(LineCollection([segments[i] for i in keep],
            colors=[cmap(norm(plot_rows[i]["flow_pce_per_period"])) for i in keep],
            linewidths=[.5+2.5*math.sqrt(plot_rows[i]["flow_pce_per_period"]/maxflow) for i in keep],alpha=.92,zorder=2))
        ax.set_xlim(extent[0],extent[1]);ax.set_ylim(extent[2],extent[3]);ax.set_aspect("equal")
        ax.set_xlabel("East–west distance from −71.08° (km)");ax.set_ylabel("North–south distance from 42.35° (km)")
        short_title=("Boston HBW midday | " if "Boston" in m["scenario"] else "Static GMNS | ")+record["method"].upper()+" | planned service"
        ax.set_title(short_title,loc="left",fontsize=16,color="#102c3e",pad=16)
        fig.colorbar(ScalarMappable(norm=norm,cmap=cmap),ax=ax,fraction=.035,pad=.025,label="Physical-link flow · PCE/declared period")
        stem=record["method"].replace("-","_")+"_flow"
        save_map(fig,ax,f"{len(od)} node OD · {m['loaded_pce']:.3f} PCE/period · {len(links)} physical links · {m['instance_signature'][:12]}\n{m['period']}; gray = all modeled roads; colored > 1e-6 PCE. No background traffic.",out/(stem+".png"),out/(stem+".svg"))
        if fw_comparator is not None and record["method"]=="diagnostic-l3":
            diff=[r["flow_pce_per_period"]-float(fw_comparator[r["link_index"]]["flow_pce_per_period"]) for r in plot_rows]
            maxdiff=max((abs(x) for x in diff),default=0.0)
            write_rows(out/"l3_minus_fw_table.csv",[{"link_id":plot_rows[i]["link_id"],"l3_minus_fw_pce":d} for i,d in enumerate(diff)],
                       ["link_id","l3_minus_fw_pce"])
            fig,ax=plt.subplots(figsize=(11.5,7.8),dpi=160)
            fig.patch.set_facecolor("white");ax.set_facecolor("#f7fafb")
            ax.add_collection(LineCollection(segments,colors="#d7e2e6",linewidths=.48,zorder=1))
            shown=[i for i,d in enumerate(diff) if abs(d)>1e-12]
            lim=max(maxdiff,1e-12);dnorm=colors.TwoSlopeNorm(vmin=-lim,vcenter=0,vmax=lim);dcmap=plt.get_cmap("coolwarm")
            ax.add_collection(LineCollection([segments[i] for i in shown],colors=[dcmap(dnorm(diff[i])) for i in shown],
                        linewidths=[.45+2*math.sqrt(abs(diff[i])/lim) for i in shown],zorder=2))
            ax.set_xlim(extent[0],extent[1]);ax.set_ylim(extent[2],extent[3]);ax.set_aspect("equal")
            ax.set_xlabel("East–west distance from −71.08° (km)");ax.set_ylabel("North–south distance from 42.35° (km)")
            ax.set_title("Boston HBW midday | native L3 − FW" if "Boston" in m["scenario"] else "Static GMNS | native L3 − FW",loc="left",fontsize=16,color="#102c3e",pad=16)
            fig.colorbar(ScalarMappable(norm=dnorm,cmap=dcmap),ax=ax,fraction=.035,pad=.025,label="L3 − FW · PCE/declared period")
            save_map(fig,ax,f"Same physical links and instance {m['instance_signature'][:12]} · signed linkwise difference · display |difference| > 1e-12 PCE",out/"l3_minus_fw.png",out/"l3_minus_fw.svg")
        production=defaultdict(float);attraction=defaultdict(float)
        for r in od:
            production[r["o_node_id"]]+=float(r["volume"])
            attraction[r["d_node_id"]]+=float(r["volume"])
        coverage=[{"node_id":n,"x_km":node_xy[n][0],"y_km":node_xy[n][1],
                   "origin_pce":production.get(n,0),"destination_pce":attraction.get(n,0)}
                  for n in sorted(set(production)|set(attraction)) if n in node_xy]
        write_rows(out/"endpoint_coverage.csv",coverage,["node_id","x_km","y_km","origin_pce","destination_pce"])
        fig,ax=plt.subplots(figsize=(11.5,7.8),dpi=160)
        fig.patch.set_facecolor("white");ax.set_facecolor("#f7fafb")
        ax.add_collection(LineCollection(segments,colors="#d7e2e6",linewidths=.48,zorder=1))
        for field,color,label,offset in (("origin_pce","#087e8b","Mapped origins",-.015),
                                         ("destination_pce","#dd8b32","Mapped destinations",.015)):
            vals=[r for r in coverage if r[field]>0]
            ax.scatter([r["x_km"]+offset for r in vals],[r["y_km"] for r in vals],
                       s=[18+120*math.sqrt(r[field]/max(m["loaded_pce"],1e-12)) for r in vals],
                       c=color,alpha=.8,edgecolors="white",linewidths=.4,label=label,zorder=3)
        ax.set_xlim(extent[0],extent[1]);ax.set_ylim(extent[2],extent[3]);ax.set_aspect("equal")
        ax.set_xlabel("East–west distance from −71.08° (km)");ax.set_ylabel("North–south distance from 42.35° (km)")
        ax.set_title("Boston HBW midday | mapped endpoint coverage" if "Boston" in m["scenario"] else "Static GMNS | mapped endpoint coverage",loc="left",fontsize=16,color="#102c3e",pad=16)
        ax.legend(loc="upper right")
        save_map(fig,ax,f"{len(od)} node OD · {len(production)} physical origins · {len(attraction)} physical destinations · {m['instance_signature'][:12]}\nBubble area scales with square root of modeled PCE; source-zone selection is reported separately.",out/"endpoint_coverage.png",out/"endpoint_coverage.svg")
    result={"status":"PLOTTED" if parsed else "NO_GEOMETRY", "parsed_geometry_links":parsed,"physical_links":len(links),"display_cutoff":1e-6,"plot_seconds":time.perf_counter()-t,
            "instance_signature":m["instance_signature"],"link_flow_sha256":sha(run/"link_flow.csv"),
            "palette":"accepted Boston viridis flow, gray physical roads, teal origins, amber destinations",
            "layout":"caption aligned to actual map edge; unused canvas cropped",
            "link_table_sha256":sha(out/"plot_link_table.csv") if parsed else None}
    atomic_json(out/"plot.json",result)
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    sub=ap.add_subparsers(dest="action",required=True)
    p=sub.add_parser("prepare");p.add_argument("--input",required=True);p.add_argument("--demand",required=True);p.add_argument("--config",required=True);p.add_argument("--output",required=True)
    p=sub.add_parser("solve");p.add_argument("--instance",required=True);p.add_argument("--method",choices=("fw","full-path","diagnostic-l3"),required=True);p.add_argument("--config");p.add_argument("--output",required=True)
    p=sub.add_parser("verify");p.add_argument("--run",required=True)
    p=sub.add_parser("plot");p.add_argument("--run",required=True);p.add_argument("--output",required=True)
    p=sub.add_parser("scale");p.add_argument("--profile",required=True);p.add_argument("--levels");p.add_argument("--output",required=True)
    args=ap.parse_args()
    try:
        if args.action=="prepare": value=prepare(args)
        elif args.action=="solve":
            if args.method=="fw":
                cfg=config(args.config) if args.config else {}
                value=solve_fw(args.instance,args.output,int(cfg.get("max_iterations",300)),float(cfg.get("gap_tolerance",1e-5)))
            else:
                if not args.config:raise ValueError("method config required")
                cfg=json.loads(Path(args.config).read_text(encoding="utf-8"))
                out=safe_output(args.output,[args.instance,args.config])
                out.mkdir(parents=True)
                from mcl_path_methods import build_pool,full_path,basis
                from mcl_path_methods import load_pool
                from mcl_scale import available_ram
                available=available_ram()
                measured_ceiling=min(8*1024**3,available//2) if available else 2*1024**3
                pool=Path(cfg["pool_dir"]).resolve() if cfg.get("pool_dir") else out/"pool"
                if cfg.get("pool_dir"):
                    _,_,_,_,_,_,_,_=load_pool(args.instance,pool)
                    prep=json.loads((pool/"pool.json").read_text(encoding="utf-8"))
                    if prep["k"]!=int(cfg.get("k",5)):raise ValueError("configured K differs from reused path pool")
                    prep["cache_status"]="VERIFIED_SHARED_POOL_HIT"
                else:
                    prep=build_pool(args.instance,pool,int(cfg.get("k",5)))
                    prep["cache_status"]="NEW_POOL"
                try:
                    if args.method=="full-path":
                        result=full_path(args.instance,pool,out/"solution",int(cfg.get("max_iterations",300)),measured_ceiling)
                    else:
                        required={"rank_fraction","ipopt_executable","temp_dir"}
                        if not required.issubset(cfg):raise ValueError(f"missing native config: {sorted(required-set(cfg))}")
                        from mcl_native_l3 import controller
                        basis(args.instance,pool,out/"basis",float(cfg["rank_fraction"]),measured_ceiling)
                        native_args=argparse.Namespace(instance=args.instance,pool=str(pool),basis=str(out/"basis"),
                            output=str(out/"solution"),source=str(Path(__file__).parent/"scalable"/"diagnostic_l3_source.py"),
                            ipopt=cfg["ipopt_executable"],fw_run=cfg.get("fw_run"),temp=cfg["temp_dir"],
                            memory_ceiling=measured_ceiling,inner_timeout=float(cfg.get("inner_timeout",600)),
                            total_timeout=float(cfg.get("total_timeout",2700)),max_outer=int(cfg.get("max_outer",8)))
                        result=controller(native_args)
                except MemoryError as exc:
                    result={"status":"RESOURCE_LIMIT","reason":str(exc)}
                m,_,_=load_instance(args.instance)
                value={"schema":VERSION,"method":args.method,"instance_signature":m["instance_signature"],
                       "invocation":[sys.executable]+sys.argv,"tool_source_sha256":sha(__file__),
                       "python_version":sys.version.split()[0],
                       "instance_path":str(Path(args.instance).resolve()),"pool_path":str(pool.resolve()),"pool":prep,"solver":result,
                       "config_sha256":sha(args.config),"fw_run":cfg.get("fw_run"),
                       "available_physical_before_method_bytes":available,"working_memory_ceiling_bytes":measured_ceiling}
                atomic_json(out/"run.json",value)
        elif args.action=="verify": value=verify(args.run)
        elif args.action=="plot": value=plot(args.run,args.output)
        else:
            from mcl_scale import run_scale
            value=run_scale(args)
        print(json.dumps(value,indent=2,allow_nan=False))
        if args.action=="verify" and value["status"]!="SOLVED_WITHIN_DECLARED_TOLERANCE":return 2
        if args.action=="scale" and value["status"]!="COMPLETE_REQUESTED_LEVELS":return 2
        if args.action=="solve" and args.method=="fw" and value["solver_status"]!="SOLVER_TERMINATED":return 2
        if args.action=="solve" and args.method=="full-path" and not value["solver"].get("solver_success",False):return 2
        if args.action=="solve" and args.method=="diagnostic-l3" and value["solver"].get("status")!="SOLVED_WITHIN_DECLARED_TOLERANCE":return 2
        return 0
    except Exception as exc:
        print(json.dumps({"status":"ERROR","action":args.action,"reason":str(exc)},allow_nan=False),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
