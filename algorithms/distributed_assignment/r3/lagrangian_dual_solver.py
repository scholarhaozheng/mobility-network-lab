"""City-independent capacity-price dual solver with separate path-LP recovery."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import time
from pathlib import Path

import numpy as np

from problem_contract import shortest_path
from path_pool_manager import PathPool
from restricted_primal_recovery import recover

try:
    import psutil
except ImportError:
    psutil = None


def _write_csv(path, fields, records):
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(fields)
        writer.writerows(records)


def _coefficient(variant, t, direction, dual, upper):
    norm = float(np.linalg.norm(direction))
    if upper is not None and upper > dual:
        return min(variant["polyak_fraction"] * (upper - dual) / max(norm * norm, 1.0),
                   variant["step_norm_cap"] / max(norm, 1.0))
    return variant["fallback_scale"] / (math.sqrt(t) * max(norm, 1.0))


def _choose_recovery(problem, pool, current, best):
    if current is not None and (best is None or current["objective"] < best["objective"]):
        best = current
    candidate = recover(problem, pool)
    if candidate["feasible"] and (best is None or candidate["objective"] < best["objective"]):
        best = candidate
    return best, candidate


def solve(problem, variant, common):
    lam = np.zeros(len(problem["ids"]), dtype=float)
    pool = PathPool(len(problem["commodities"]), common["max_paths_per_commodity"])
    best_dual, best_lam, best_primal = -math.inf, None, None
    previous_direction = np.zeros_like(lam)
    history, recoveries, snapshots = [], [], []
    started = time.perf_counter()
    cpu_started = time.process_time()
    peak_rss = 0 if psutil else None
    stop_reason = "MAX_ITERATIONS"
    for t in range(1, variant["max_iterations"] + 1):
        weights = problem["cost"] + lam
        usage = np.zeros_like(lam)
        shortest_sum = 0.0
        current_paths = []
        for k, commodity in enumerate(problem["commodities"]):
            distance, path = shortest_path(problem, k, weights)
            shortest_sum += commodity["volume"] * distance
            usage[list(path)] += commodity["volume"]
            current_paths.append(path)
            pool.add(k, path, t)
        dual = shortest_sum - float(lam @ problem["cap"])
        prior_best = best_dual
        serious = (not math.isfinite(prior_best) or
                   dual > prior_best + variant["serious_improvement_relative"] * max(1, abs(prior_best)))
        if dual > best_dual:
            best_dual, best_lam = dual, lam.copy()
        g = usage - problem["cap"]
        q = np.where((lam > 0) | (g > 0), g, 0)
        max_violation = float(np.max(np.maximum(g, 0)))
        direct = None
        if max_violation <= common["feasibility"]["max_capacity_violation"]:
            direct = {"feasible": True, "objective": float(usage @ problem["cost"]),
                      "path_count": len(current_paths), "message": "direct priced paths",
                      "positive_paths": [(k, path, problem["commodities"][k]["volume"])
                                         for k, path in enumerate(current_paths)]}
            if best_primal is None or direct["objective"] < best_primal["objective"]:
                best_primal = direct
        if t == 1 or t % common["recovery_every"] == 0 or t == variant["max_iterations"]:
            best_primal, candidate = _choose_recovery(problem, pool, direct, best_primal)
            recoveries.append({"iteration": t, "feasible": candidate["feasible"],
                               "path_count": candidate["path_count"],
                               "objective": candidate.get("objective"),
                               "message": candidate["message"]})
        upper = None if best_primal is None else best_primal["objective"]
        gap = None if upper is None else max(0, (upper - best_dual) / max(1, abs(upper)))
        if variant["update_rule"] == "deflected":
            direction = variant["deflection_current_weight"] * q + (1 - variant["deflection_current_weight"]) * previous_direction
            previous_direction = direction.copy()
        else:
            direction = q
        step = _coefficient(variant, t, direction, dual, upper)
        elapsed = time.perf_counter() - started
        if psutil:
            peak_rss = max(peak_rss, psutil.Process(os.getpid()).memory_info().rss)
        history.append({"iteration": t, "dual": dual, "best_dual": best_dual,
                        "best_primal": upper, "gap": gap, "capacity_subgradient_norm": float(np.linalg.norm(g)),
                        "projected_subgradient_norm": float(np.linalg.norm(q)),
                        "max_current_capacity_violation": max_violation,
                        "multiplier_positive_count": int(np.count_nonzero(lam > 0)),
                        "max_multiplier": float(np.max(lam)), "step_coefficient": step,
                        "serious_step": bool(serious), "path_pool_size": pool.count(),
                        "wall_seconds": elapsed, "cpu_seconds": time.process_time() - cpu_started})
        if t == 1 or t % common["multiplier_snapshot_every"] == 0 or t == variant["max_iterations"]:
            snapshots.extend((t, a, float(value)) for a, value in enumerate(lam) if value > 1e-12)
        if gap is not None and gap <= common["target_gap"]:
            stop_reason = "CERTIFIED_GAP"
            break
        if elapsed >= variant["wall_seconds_per_case"]:
            stop_reason = "WALL_BUDGET"
            break
        if (t >= common["plateau_start"] and t % common["plateau_check_every"] == 0 and
                upper is not None):
            old = history[-common["plateau_window"]]["best_dual"]
            improvement = best_dual - old
            threshold = max(common["plateau_absolute_improvement"],
                            common["plateau_gap_fraction"] * max(0, upper - best_dual))
            if improvement <= threshold:
                stop_reason = "DUAL_PLATEAU"
                break
        if variant["update_rule"] == "deflected":
            trial = np.maximum(0, lam + step * direction)
        else:
            trial = np.maximum(0, lam + step * g)
        if variant["update_rule"] == "stabilized" and not serious:
            lam = np.maximum(0, variant["null_trial_weight"] * trial +
                             (1 - variant["null_trial_weight"]) * best_lam)
        else:
            lam = trial
    if t != 1 and t % common["recovery_every"] != 0 and t != variant["max_iterations"]:
        best_primal, candidate = _choose_recovery(problem, pool, None, best_primal)
        recoveries.append({"iteration": t, "feasible": candidate["feasible"],
                           "path_count": candidate["path_count"],
                           "objective": candidate.get("objective"), "message": candidate["message"]})
        upper = None if best_primal is None else best_primal["objective"]
        history[-1]["best_primal"] = upper
        history[-1]["gap"] = None if upper is None else max(0, (upper - best_dual) / max(1, abs(upper)))
    if snapshots and snapshots[-1][0] != t:
        snapshots.extend((t, a, float(value)) for a, value in enumerate(lam) if value > 1e-12)
    return {"best_lam": best_lam, "best_dual": best_dual, "best_primal": best_primal,
            "pool": pool, "history": history, "recoveries": recoveries, "snapshots": snapshots,
            "stop_reason": stop_reason, "wall_seconds": time.perf_counter() - started,
            "cpu_seconds": time.process_time() - cpu_started, "peak_rss_bytes": peak_rss}


def run_case(problem, metadata, variant, common, plan_file, output_dir):
    output = Path(output_dir)
    if output.exists():
        raise FileExistsError(f"run identifier already exists: {output}")
    output.mkdir(parents=True)
    state = solve(problem, variant, common)
    lam, dual, primal, pool = (state[key] for key in ("best_lam", "best_dual", "best_primal", "pool"))
    history = state["history"]
    _write_csv(output / "best_multipliers.csv", ["arc_id", "lambda"],
               ((arc, format(float(value), ".17g")) for arc, value in zip(problem["ids"], lam)))
    _write_csv(output / "multiplier_snapshots.csv", ["iteration", "arc_id", "lambda"],
               ((t, problem["ids"][a], format(value, ".17g")) for t, a, value in state["snapshots"]))
    _write_csv(output / "history.csv", list(history[0]),
               ([row[field] for field in history[0]] for row in history))
    _write_csv(output / "pool_paths.csv", ["iteration", "demand_id", "source", "arc_ids_json"],
               ((t, problem["commodities"][k]["id"], source,
                 json.dumps([problem["ids"][a] for a in path], separators=(",", ":")))
                for t, k, source, path in pool.events))
    (output / "recovery_history.json").write_text(json.dumps(state["recoveries"], indent=2), encoding="utf-8")
    if primal is not None:
        _write_csv(output / "positive_paths.csv", ["demand_id", "arc_ids_json", "flow"],
                   ((problem["commodities"][k]["id"],
                     json.dumps([problem["ids"][a] for a in path], separators=(",", ":")),
                     format(flow, ".17g")) for k, path, flow in primal["positive_paths"]))
        flows, physical = {}, {}
        for k, path, value in primal["positive_paths"]:
            for a in path:
                flows[k, a] = flows.get((k, a), 0) + value
                if problem["types"][a] == "movement":
                    link = problem["arcs"][a]["physical_link_id"]
                    physical[link] = physical.get(link, 0) + value
        _write_csv(output / "commodity_arc_flow.csv", ["demand_id", "arc_id", "flow"],
                   ((problem["commodities"][k]["id"], problem["ids"][a], format(value, ".17g"))
                    for (k, a), value in sorted(flows.items())))
        _write_csv(output / "physical_link_flow.csv", ["physical_link_id", "flow"],
                   ((link, format(value, ".17g")) for link, value in sorted(physical.items())))
    result = {"method": "generic_lagrangian_capacity_pricing_r3", "case": metadata["case_id"],
              "variant": variant["id"], "model_signature": metadata["model_signature"],
              "case_manifest_sha256": metadata["case_manifest_sha256"],
              "plan_sha256": hashlib.sha256(Path(plan_file).read_bytes()).hexdigest(),
              "arc_sha256": metadata["arc_sha256"], "demand_sha256": metadata["demand_sha256"],
              "best_dual": dual, "best_primal": None if primal is None else primal["objective"],
              "algorithm_gap": history[-1]["gap"], "iterations": len(history),
              "pool_size": pool.count(), "recovery_calls": len(state["recoveries"]),
              "wall_seconds": state["wall_seconds"], "cpu_seconds": state["cpu_seconds"],
              "peak_rss_bytes": state["peak_rss_bytes"], "stop_reason": state["stop_reason"],
              "status": "FEASIBLE_RECOVERY" if primal is not None else "VALID_DUAL_BOUND_ONLY"}
    (output / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
