"""Solver-free certificate from saved outputs; never imports the Lagrangian solver."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from space_time_capacity_problem_contract import load


def rows(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def independent_shortest(problem, commodity_index, weights):
    commodity = problem["commodities"][commodity_index]
    dist = np.full(len(problem["nodes"]), np.inf)
    predecessor = np.full(len(problem["nodes"]), -1, dtype=int)
    dist[commodity["source"]] = 0.0
    for node in problem["order"]:
        if not np.isfinite(dist[node]):
            continue
        for arc in problem["adj"][node]:
            if problem["allowed"][commodity_index, arc]:
                successor = problem["v"][arc]
                candidate = dist[node] + weights[arc]
                if candidate < dist[successor] - 1e-10:
                    dist[successor] = candidate
                    predecessor[successor] = arc
    path = []
    node = commodity["sink"]
    while node != commodity["source"]:
        arc = predecessor[node]
        if arc < 0:
            raise ValueError("unreachable commodity in independent dual evaluation")
        path.append(arc)
        node = problem["u"][arc]
    return float(dist[commodity["sink"]]), path[::-1]


def evaluate(arc_file, demand_file, result_dir, plan_file, reference_file=None):
    problem = load(arc_file, demand_file)
    result_dir = Path(result_dir)
    result = json.loads((result_dir / "result.json").read_text(encoding="utf-8"))
    plan = json.loads(Path(plan_file).read_text(encoding="utf-8"))
    tol = plan["common"]["feasibility"]
    checks = {}
    checks["graph_signature"] = (result["arc_sha256"] == sha(arc_file) and
                                  result["demand_sha256"] == sha(demand_file) and
                                  result["plan_sha256"] == sha(plan_file))
    amap = {name: index for index, name in enumerate(problem["ids"])}
    kmap = {item["id"]: index for index, item in enumerate(problem["commodities"])}
    multipliers = rows(result_dir / "best_multipliers.csv")
    checks["multiplier_ids"] = (len(multipliers) == len(amap) and
                                set(r["arc_id"] for r in multipliers) == set(amap))
    if not checks["multiplier_ids"]:
        raise ValueError("multiplier arc IDs mismatch")
    lam = np.zeros(len(amap))
    for row in multipliers:
        lam[amap[row["arc_id"]]] = float(row["lambda"])
    checks["multipliers_finite_nonnegative"] = bool(np.all(np.isfinite(lam)) and np.min(lam) >= 0)
    if not checks["multipliers_finite_nonnegative"]:
        raise ValueError("invalid negative or NaN multiplier")
    usage = np.zeros(len(amap))
    shortest_sum = 0.0
    for k, item in enumerate(problem["commodities"]):
        distance, path = independent_shortest(problem, k, problem["cost"] + lam)
        shortest_sum += item["volume"] * distance
        usage[path] += item["volume"]
    dual = shortest_sum - float(lam @ problem["cap"])
    subgradient = usage - problem["cap"]
    history = rows(result_dir / "history.csv")
    history_best = max(float(row["dual"]) for row in history)
    checks["dual_recomputed"] = abs(dual - result["best_dual"]) <= tol["dual_relative_error"] * max(1, abs(dual))
    checks["history_best"] = abs(history_best - result["best_dual"]) <= tol["dual_relative_error"] * max(1, abs(dual))
    output = {"case": result["case"], "variant": result["variant"], "optimizer_calls": 0,
              "dual_recomputed": dual, "dual_saved": result["best_dual"],
              "best_history_dual": history_best, "min_multiplier": float(np.min(lam)),
              "max_multiplier": float(np.max(lam)),
              "capacity_subgradient_norm": float(np.linalg.norm(subgradient)),
              "max_priced_path_capacity_violation": float(np.max(np.maximum(subgradient, 0))),
              "checks": checks}
    positive_file = result_dir / "positive_paths.csv"
    if positive_file.exists():
        path_rows = rows(positive_file)
        pool_rows = rows(result_dir / "pool_paths.csv")
        pool = {(r["demand_id"], tuple(json.loads(r["arc_ids_json"]))) for r in pool_rows}
        checks["pool_duplicates"] = len(pool) == len(pool_rows)
        seen_paths = set()
        flows = np.zeros((len(kmap), len(amap)))
        path_start_end = True
        path_allowed = True
        path_times = True
        path_pool_membership = True
        path_duplicate = False
        for row in path_rows:
            demand = row["demand_id"]
            if demand not in kmap:
                raise ValueError("unknown commodity in positive path")
            k = kmap[demand]
            names = tuple(json.loads(row["arc_ids_json"]))
            if any(name not in amap for name in names):
                raise ValueError("unknown arc in path")
            path = tuple(amap[name] for name in names)
            value = float(row["flow"])
            if not math.isfinite(value) or value < tol["min_flow"]:
                raise ValueError("invalid path flow")
            if (demand, names) in seen_paths:
                path_duplicate = True
            seen_paths.add((demand, names))
            path_pool_membership &= (demand, names) in pool
            if not path:
                path_start_end = False
                continue
            path_start_end &= (problem["u"][path[0]] == problem["commodities"][k]["source"] and
                               problem["v"][path[-1]] == problem["commodities"][k]["sink"])
            for previous, following in zip(path, path[1:]):
                path_start_end &= problem["v"][previous] == problem["u"][following]
            path_allowed &= bool(np.all(problem["allowed"][k, list(path)]))
            for a in path:
                arc = problem["arcs"][a]
                path_times &= float(arc["to_time"]) >= float(arc["from_time"])
                flows[k, a] += value
        checks["path_continuity"] = bool(path_start_end)
        checks["path_time_monotonicity"] = bool(path_times)
        checks["own_connector_only"] = bool(path_allowed)
        checks["path_pool_membership"] = bool(path_pool_membership)
        checks["positive_path_uniqueness"] = not path_duplicate
        demand_balance = np.zeros((len(kmap), len(problem["nodes"])))
        for k, commodity in enumerate(problem["commodities"]):
            np.add.at(demand_balance[k], problem["u"], flows[k])
            np.add.at(demand_balance[k], problem["v"], -flows[k])
            demand_balance[k, commodity["source"]] -= commodity["volume"]
            demand_balance[k, commodity["sink"]] += commodity["volume"]
        total = flows.sum(axis=0)
        objective = float(total @ problem["cost"])
        max_balance = float(np.max(np.abs(demand_balance)))
        max_capacity = float(np.max(np.maximum(total - problem["cap"], 0)))
        min_flow = float(np.min(flows))
        supplied = np.zeros_like(flows)
        for row in rows(result_dir / "commodity_arc_flow.csv"):
            supplied[kmap[row["demand_id"]], amap[row["arc_id"]]] += float(row["flow"])
        flow_error = float(np.max(np.abs(flows - supplied)))
        physical = {}
        for a, arc in enumerate(problem["arcs"]):
            if arc["arc_type"] == "movement":
                link = arc["physical_link_id"]
                physical[link] = physical.get(link, 0) + total[a]
        physical_saved = {r["physical_link_id"]: float(r["flow"])
                          for r in rows(result_dir / "physical_link_flow.csv")}
        physical_error = max((abs(physical.get(link, 0) - physical_saved.get(link, 0))
                              for link in physical.keys() | physical_saved.keys()), default=0)
        checks["demand_balance"] = max_balance <= tol["max_demand_balance_residual"]
        checks["capacity"] = max_capacity <= tol["max_capacity_violation"]
        checks["nonnegative_flow"] = min_flow >= tol["min_flow"]
        checks["commodity_arc_flow"] = flow_error <= tol["max_demand_balance_residual"]
        checks["physical_projection"] = physical_error <= tol["max_demand_balance_residual"]
        checks["primal_objective"] = abs(objective - result["best_primal"]) <= tol["objective_relative_error"] * max(1, abs(objective))
        gap = max(0.0, (objective - dual) / max(1, abs(objective)))
        output.update({"primal_available": True, "objective_recomputed": objective,
                       "max_balance_residual": max_balance, "max_capacity_violation": max_capacity,
                       "min_flow": min_flow, "flow_reconstruction_error": flow_error,
                       "physical_projection_error": physical_error, "duality_gap": gap,
                       "positive_paths": len(path_rows), "physical_links": len(physical_saved)})
    else:
        output["primal_available"] = False
        checks["primal_absence_consistent"] = result["best_primal"] is None
    if reference_file is not None:
        reference = json.loads(Path(reference_file).read_text(encoding="utf-8"))
        optimum = reference["objective_value"]
        output["reference_objective"] = optimum
        output["dual_exceeds_reference_by"] = max(0.0, dual - optimum)
        checks["dual_reference_bound"] = dual <= optimum + 1e-6 * max(1, abs(optimum))
        if output["primal_available"]:
            output["primal_reference_relative_gap"] = abs(output["objective_recomputed"] - optimum) / max(1, abs(optimum))
    output["checks"] = {key: bool(value) for key, value in checks.items()}
    output["status"] = "PASS" if all(output["checks"].values()) else "FAIL"
    return output


def main():
    parser = argparse.ArgumentParser()
    for name in ("arc", "demand", "result", "plan"):
        parser.add_argument(f"--{name}", required=True)
    parser.add_argument("--reference")
    args = parser.parse_args()
    try:
        output = evaluate(args.arc, args.demand, args.result, args.plan, args.reference)
    except Exception as exc:
        output = {"status": "FAIL", "error": str(exc), "optimizer_calls": 0}
    Path(args.result, "evaluation.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output))
    return 0 if output["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
