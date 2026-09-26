"""Projected capacity-pricing dual solver; no reference objective or solution access."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import time
from pathlib import Path

import numpy as np

from space_time_capacity_problem_contract import load, shortest_path
from path_pool_manager import PathPool
from restricted_primal_recovery_adapter import recover


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_csv(path, fields, rows):
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(fields)
        writer.writerows(rows)


def coefficient(variant, iteration, norm, dual, upper):
    spec = variant["constants"]
    if variant["rule"] == "normalized diminishing":
        return spec["scale"] / (math.sqrt(iteration) * max(norm, 1.0))
    if upper is not None and upper > dual:
        return min(spec["polyak_fraction"] * (upper - dual) / max(norm * norm, 1.0),
                   spec["coordinate_step_norm_cap"] / max(norm, 1.0))
    return spec["fallback_scale"] / (math.sqrt(iteration) * max(norm, 1.0))


def solve(problem, variant, common):
    lam = np.zeros(len(problem["ids"]), dtype=float)
    pool = PathPool(len(problem["commodities"]), common["max_paths_per_commodity"])
    best_dual = -math.inf
    best_lam = None
    best_primal = None
    history = []
    recoveries = []
    start = time.perf_counter()
    for iteration in range(1, variant["max_iterations"] + 1):
        weights = problem["cost"] + lam
        usage = np.zeros_like(lam)
        shortest_sum = 0.0
        current_paths = []
        for k, commodity in enumerate(problem["commodities"]):
            distance, path = shortest_path(problem, k, weights)
            shortest_sum += commodity["volume"] * distance
            usage[list(path)] += commodity["volume"]
            current_paths.append(path)
            pool.add(k, path, iteration)
        dual = shortest_sum - float(lam @ problem["cap"])
        if dual > best_dual:
            best_dual, best_lam = dual, lam.copy()
        g = usage - problem["cap"]
        projected = np.where((lam > 0) | (g > 0), g, 0)
        norm = float(np.linalg.norm(projected))
        positive_violation = float(np.max(np.maximum(g, 0)))
        if positive_violation <= common["feasibility"]["max_capacity_violation"]:
            direct = {"feasible": True, "objective": float(usage @ problem["cost"]),
                      "path_count": len(current_paths), "message": "direct priced paths",
                      "positive_paths": [(k, path, problem["commodities"][k]["volume"])
                                         for k, path in enumerate(current_paths)]}
            if best_primal is None or direct["objective"] < best_primal["objective"]:
                best_primal = direct
        if iteration == 1 or iteration % 10 == 0 or iteration == variant["max_iterations"]:
            candidate = recover(problem, pool)
            recoveries.append({"iteration": iteration, "feasible": candidate["feasible"],
                               "path_count": candidate["path_count"],
                               "objective": candidate.get("objective"),
                               "message": candidate["message"]})
            if candidate["feasible"] and (best_primal is None or candidate["objective"] < best_primal["objective"]):
                best_primal = candidate
        upper = None if best_primal is None else best_primal["objective"]
        gap = None if upper is None else max(0.0, (upper - best_dual) / max(1.0, abs(upper)))
        step = coefficient(variant, iteration, norm, dual, upper)
        history.append({"iteration": iteration, "dual": dual, "best_dual": best_dual,
                        "best_primal": upper, "gap": gap, "capacity_subgradient_norm": float(np.linalg.norm(g)),
                        "projected_subgradient_norm": norm, "max_current_capacity_violation": positive_violation,
                        "multiplier_positive_count": int(np.count_nonzero(lam > 0)),
                        "max_multiplier": float(np.max(lam)), "step_coefficient": step,
                        "path_pool_size": pool.count(), "wall_seconds": time.perf_counter() - start})
        if gap is not None and gap <= 0.01:
            break
        if time.perf_counter() - start >= variant["wall_seconds_per_case"]:
            break
        lam = np.maximum(0, lam + step * g)
    return best_lam, best_dual, best_primal, pool, history, recoveries


def main():
    parser = argparse.ArgumentParser()
    for name in ("arc", "demand", "plan", "variant", "output", "case"):
        parser.add_argument(f"--{name}", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise FileExistsError(f"run identifier already exists: {output}")
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    variant = next(v for v in plan["variants"] if v["id"] == args.variant)
    problem = load(args.arc, args.demand)
    output.mkdir(parents=True)
    started = time.perf_counter()
    lam, dual, primal, pool, history, recoveries = solve(problem, variant, plan["common"])
    write_csv(output / "best_multipliers.csv", ["arc_id", "lambda"],
              ((arc, format(float(value), ".17g")) for arc, value in zip(problem["ids"], lam)))
    write_csv(output / "history.csv", list(history[0]),
              ([row[field] for field in history[0]] for row in history))
    write_csv(output / "pool_paths.csv", ["iteration", "demand_id", "source", "arc_ids_json"],
              ((iteration, problem["commodities"][k]["id"], source,
                json.dumps([problem["ids"][a] for a in path], separators=(",", ":")))
               for iteration, k, source, path in pool.events))
    (output / "recovery_history.json").write_text(json.dumps(recoveries, indent=2), encoding="utf-8")
    if primal is not None:
        write_csv(output / "positive_paths.csv", ["demand_id", "arc_ids_json", "flow"],
                  ((problem["commodities"][k]["id"],
                    json.dumps([problem["ids"][a] for a in path], separators=(",", ":")),
                    format(flow, ".17g")) for k, path, flow in primal["positive_paths"]))
        flows = {}
        physical = {}
        for k, path, value in primal["positive_paths"]:
            for a in path:
                flows[k, a] = flows.get((k, a), 0.0) + value
                if problem["types"][a] == "movement":
                    link = problem["arcs"][a]["physical_link_id"]
                    physical[link] = physical.get(link, 0.0) + value
        write_csv(output / "commodity_arc_flow.csv", ["demand_id", "arc_id", "flow"],
                  ((problem["commodities"][k]["id"], problem["ids"][a], format(v, ".17g"))
                   for (k, a), v in sorted(flows.items())))
        write_csv(output / "physical_link_flow.csv", ["physical_link_id", "flow"],
                  ((k, format(v, ".17g")) for k, v in sorted(physical.items())))
    result = {"task_id": plan["task_id"], "case": args.case, "variant": args.variant,
              "plan_sha256": digest(args.plan), "arc_sha256": digest(args.arc),
              "demand_sha256": digest(args.demand), "best_dual": dual,
              "best_primal": None if primal is None else primal["objective"],
              "algorithm_gap": history[-1]["gap"], "iterations": len(history),
              "pool_size": pool.count(), "recovery_calls": len(recoveries),
              "wall_seconds": time.perf_counter() - started,
              "status": "FEASIBLE_RECOVERY" if primal is not None else "VALID_DUAL_BOUND_ONLY"}
    (output / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
