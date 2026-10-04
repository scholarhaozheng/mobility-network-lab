"""Bounded RMP continuation from the accepted R3 final pool and saved dual."""
import argparse
import csv
import hashlib
import json
import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from independent_pricing_closure import DAG, canonical_hash, evaluate, read_csv, sequence, write_csv

import os
R3 = Path(os.environ["MCL_BOSTON_R3_ROOT"])
ROOT = Path(os.environ["MCL_BOSTON_R4_OUTPUT"])
SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE))
from phase2_oracle_bounded_loop_diagnostic import solve_current_pool  # RMP solver only; no oracle call

MAX_ROUNDS = 25
MAX_ADDED = 100
MAX_SECONDS = 7200
MAX_BATCH = 10
MAX_IDENTICAL_EFFECTIVE = 2
TOL = 1e-6
REF_TOL = 1e-5
REFERENCE_OBJECTIVE = 64.3968615115296

def output_json(path, payload):
    Path(path).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def candidate_row(graph, template, demand_id, arc_sequence, round_number, entry_signal):
    ids = sequence(arc_sequence)
    cost = graph.validate_path(demand_id, ids)
    arcs = [graph.arcs[aid] for aid in ids]
    physical_nodes, links, times = [], [], []
    for arc in arcs:
        u, v = arc["from_physical_node_id"], arc["to_physical_node_id"]
        if u and not u.startswith(("source_", "sink_")) and not physical_nodes:
            physical_nodes.append(u)
        if v and not v.startswith(("source_", "sink_")) and (not physical_nodes or physical_nodes[-1] != v):
            physical_nodes.append(v)
        if arc["arc_type"] == "movement":
            links.append(arc["physical_link_id"])
        if not times:
            times.append(arc["from_time"])
        if times[-1] != arc["to_time"]:
            times.append(arc["to_time"])
    demand = graph.demands[demand_id]
    arrival = arcs[-1]["from_time"]
    cid = f"R4_CLOSURE_R{round_number:02d}_{demand_id}"
    row = {key: "" for key in template}
    row.update({"column_id": cid, "path_id": cid, "demand_id": demand_id,
                "origin_node_id": demand["origin_node_id"], "destination_node_id": demand["destination_node_id"],
                "departure_time": demand["departure_time"], "arrival_time": arrival,
                "travel_time": str(float(arrival) - float(demand["departure_time"])),
                "generalized_cost": str(cost), "node_sequence": "|".join(physical_nodes),
                "link_sequence": "|".join(links), "time_sequence": "|".join(times),
                "arc_sequence": arc_sequence, "phase2_pool_column_type": "independent_closure_candidate",
                "source_metadata": "independent_full_dag_pricing_closure_r4",
                "output_only_phase2_oracle_loop_pool": "true", "pool_membership": "r4_closure_added_candidate",
                "candidate_source": "independent_full_dag_pricing_closure_r4",
                "added_in_phase2_round": str(round_number), "oracle_entry_signal_at_addition": str(entry_signal),
                "written_to_baseline_dynamic_columns": "false", "written_to_fixed_source_outputs": "false",
                "written_to_phase2_initial_pool": "false"})
    return row

def effective_fingerprint(solve):
    outputs = solve["solution_outputs"]
    dual = solve["dual_solution"]
    positive = sorted(r["column_id"] for r in outputs["solution_by_column"] if float(r["flow"]) > TOL)
    binding = sorted(r["arc_id"] for r in outputs["capacity_usage"] if abs(float(r["slack"])) <= TOL)
    return canonical_hash({"objective_rounded": round(float(solve["solver_info"]["objective_value"]), 8),
                           "positive": positive, "binding": binding,
                           "graph_dual": canonical_hash({"pi": dual["demand_equality_duals"], "mu": dual["capacity_inequality_duals"]})}), len(positive), len(binding)

def main():
    start = time.monotonic()
    copy = ROOT / "accepted_r3_copy"
    run = copy / "boston_exact_final"
    data = copy / "dynamic_inputs"
    graph = DAG(read_csv(data / "dynamic_node.csv"), read_csv(data / "dynamic_arc.csv"), read_csv(data / "dynamic_demand.csv"))
    arcs = read_csv(data / "dynamic_arc.csv")
    demands = read_csv(data / "dynamic_demand.csv")
    pool = read_csv(run / "full_cg_v1_phase_ii_final_pool.csv")
    dual = json.loads((run / "full_cg_v1_phase_ii_final_dual_solution.json").read_text(encoding="utf-8"))
    solution = read_csv(run / "full_cg_v1_phase_ii_final_solution_by_column.csv")
    initial = evaluate(graph, pool, dual, solution, TOL)
    # R3's signature hashes the in-memory pool, whose auxiliary fields differ
    # from the exported CSV. The frozen file hash and the declared metadata,
    # dual and solution identities were checked before this continuation.
    metadata = json.loads((run / "full_cg_v1_phase_ii_final_solution_metadata.json").read_text(encoding="utf-8"))
    if dual["pool_signature"] != metadata["pool_signature"] or any(r["pool_signature"] != metadata["pool_signature"] for r in solution):
        raise ValueError("saved R3 declared pool signatures disagree")
    if abs(initial["objective_recomputed"] - 64.39686151152952) > TOL:
        raise ValueError("accepted R3 objective changed")
    trace, added = [], []
    last_solve = None
    current_cert = initial
    objective = initial["objective_recomputed"]
    last_effective = None
    identical = 0
    outcome = None
    for round_number in range(1, MAX_ROUNDS + 1):
        if current_cert["closure_pass"]:
            outcome = "PRICING_CLOSURE_ESTABLISHED"
            break
        if time.monotonic() - start >= MAX_SECONDS:
            outcome = "NO_CLOSURE_RESOURCE_GATE"
            break
        failing = [r for r in current_cert["by_demand"] if not r["closure_pass"]]
        if not failing:
            outcome = "NO_CLOSURE_NUMERICAL_OR_MODEL_INCONSISTENCY"
            break
        if len(failing) > MAX_BATCH or len(added) + len(failing) > MAX_ADDED:
            outcome = "NO_CLOSURE_RESOURCE_GATE"
            break
        selected = []
        for r in failing:
            did = r["demand_id"]
            candidate = candidate_row(graph, pool[0], did, r["min_ungenerated_path_arc_sequence"], round_number,
                                      r["min_ungenerated_reduced_cost"])
            if any(p["arc_sequence"] == candidate["arc_sequence"] and p["demand_id"] == did for p in pool + selected):
                raise ValueError(f"duplicate selected path {did}")
            selected.append(candidate)
        trial_pool = pool + selected
        solve = solve_current_pool(arcs, demands, trial_pool)
        status = solve["solver_info"].get("solver_status")
        trial_objective = float(solve["solver_info"].get("objective_value") or math.nan)
        validation = solve["validation"].get("validation_status")
        if status != "optimal" or validation != "PASS" or not math.isfinite(trial_objective):
            outcome = "NO_CLOSURE_NUMERICAL_OR_MODEL_INCONSISTENCY"
            trace.append({"round": round_number, "commit": "REJECTED", "reason": f"solver {status}; validation {validation}"})
            break
        if trial_objective > objective + TOL or trial_objective < REFERENCE_OBJECTIVE - REF_TOL:
            outcome = "NO_CLOSURE_NUMERICAL_OR_MODEL_INCONSISTENCY"
            trace.append({"round": round_number, "commit": "REJECTED", "reason": "objective inconsistency",
                          "objective_before": objective, "objective_after": trial_objective})
            break
        result = evaluate(graph, trial_pool, solve["dual_solution"], solve["solution_outputs"]["solution_by_column"], TOL)
        if abs(result["objective_recomputed"] - trial_objective) > TOL:
            outcome = "NO_CLOSURE_NUMERICAL_OR_MODEL_INCONSISTENCY"
            trace.append({"round": round_number, "commit": "REJECTED", "reason": "independent objective mismatch"})
            break
        fingerprint, positive_count, binding_count = effective_fingerprint(solve)
        identical = identical + 1 if fingerprint == last_effective else 0
        last_effective = fingerprint
        flow_by_id = {r["column_id"]: float(r["flow"]) for r in solve["solution_outputs"]["solution_by_column"]}
        for row in selected:
            added.append({"round": round_number, "column_id": row["column_id"], "demand_id": row["demand_id"],
                          "arc_sequence": row["arc_sequence"], "generalized_cost": row["generalized_cost"],
                          "entry_signal_at_addition": row["oracle_entry_signal_at_addition"],
                          "flow_after_commit": flow_by_id[row["column_id"]],
                          "pool_signature_after": result["pool_signature"], "dual_signature_after": result["dual_signature"]})
        trace.append({"round": round_number, "commit": "STRICT" if trial_objective < objective - TOL else "DEGENERATE_NONINCREASE",
                      "reason": "", "objective_before": objective, "objective_after": trial_objective,
                      "objective_change": trial_objective - objective, "added_column_ids": "|".join(r["column_id"] for r in selected),
                      "added_count": len(selected), "pool_count": len(trial_pool),
                      "pool_signature": result["pool_signature"], "dual_signature": result["dual_signature"],
                      "effective_state_fingerprint": fingerprint, "consecutive_identical_effective_states": identical,
                      "positive_flow_columns": positive_count, "binding_capacity_arcs": binding_count,
                      "min_ungenerated_reduced_cost": min((r["min_ungenerated_reduced_cost"] for r in result["by_demand"] if r["min_ungenerated_reduced_cost"] is not None), default=""),
                      "closure_pass": result["closure_pass"], "elapsed_seconds": time.monotonic() - start})
        pool, dual, solution = trial_pool, solve["dual_solution"], solve["solution_outputs"]["solution_by_column"]
        objective, current_cert, last_solve = trial_objective, result, solve
        print(json.dumps({"round": round_number, "objective": objective, "pool": len(pool),
                          "added": len(selected), "closure": result["closure_pass"], "identical": identical}), flush=True)
        if result["closure_pass"]:
            outcome = "PRICING_CLOSURE_ESTABLISHED"
            break
        if identical >= MAX_IDENTICAL_EFFECTIVE:
            outcome = "NO_CLOSURE_DUAL_OR_STATE_CYCLE"
            break
    if outcome is None:
        outcome = "NO_CLOSURE_RESOURCE_GATE" if len(trace) >= MAX_ROUNDS else "NO_CLOSURE_NEGATIVE_UNGENERATED_PATH_REMAINS"
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    current_cert["outcome"] = outcome
    current_cert["same_graph_reference_objective_match"] = abs(objective - REFERENCE_OBJECTIVE) <= REF_TOL
    current_cert["independent_pricing_closure_established"] = outcome == "PRICING_CLOSURE_ESTABLISHED"
    current_cert["reference_objective_posthoc"] = REFERENCE_OBJECTIVE
    current_cert["accepted_r3_objective"] = 64.39686151152952
    current_cert["continuation_rounds"] = len([r for r in trace if r["commit"] != "REJECTED"])
    current_cert["added_columns"] = len(added)
    current_cert["elapsed_seconds"] = time.monotonic() - start
    current_cert["r3_source_pool_signature"] = metadata["pool_signature"]
    current_cert["r3_exported_pool_content_signature"] = initial["pool_signature"]
    output_json(out / "INDEPENDENT_PRICING_CLOSURE_CERTIFICATE.json", current_cert)
    write_csv(out / "INDEPENDENT_PRICING_CLOSURE_BY_DEMAND.csv", current_cert["by_demand"])
    write_csv(out / "CLOSURE_CONTINUATION_TRACE.csv", trace)
    write_csv(out / "CLOSURE_ADDED_COLUMNS.csv", added)
    write_csv(out / "FINAL_CLOSURE_POOL.csv", pool)
    write_csv(out / "FINAL_CLOSURE_SOLUTION_BY_COLUMN.csv", solution)
    dual["pool_signature"] = current_cert["pool_signature"]
    dual["graph_signature_independent"] = graph.graph_signature
    dual["dual_signature_independent"] = current_cert["dual_signature"]
    output_json(out / "FINAL_CLOSURE_DUAL_SOLUTION.json", dual)
    if last_solve:
        write_csv(out / "FINAL_CLOSURE_STATIONARITY.csv", last_solve["stationarity_rows"])
    else:
        source = run / "full_cg_v1_phase_ii_final_stationarity.csv"
        (out / "FINAL_CLOSURE_STATIONARITY.csv").write_bytes(source.read_bytes())
    print(json.dumps({"outcome": outcome, "rounds": current_cert["continuation_rounds"],
                      "added": len(added), "objective": objective, "pool": len(pool),
                      "closure": current_cert["independent_pricing_closure_established"]}), flush=True)
    return 0 if outcome == "PRICING_CLOSURE_ESTABLISHED" else 2

if __name__ == "__main__":
    raise SystemExit(main())
