"""Run fixed Boston/native-L3 checks before starting IPOPT."""
from __future__ import annotations

import csv
import heapq
import math
import sys
from pathlib import Path

import numpy as np
import pyomo.environ as pyo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "adapters"))
from common import INPUT, ROOT, build_native_l3, csv_rows, dump, load_case, model_counts, sha


def bpr(v, t0, alpha, beta, cap):
    return t0 * v + t0 * alpha / (beta + 1) * v * (v / cap) ** beta


def cost(v, t0, alpha, beta, cap):
    return t0 * (1 + alpha * (v / cap) ** beta)


def shortest(adj, start, end):
    heap = [(0.0, start)]
    dist = {start: 0.0}
    while heap:
        d, node = heapq.heappop(heap)
        if node == end:
            return d
        if d > dist[node] + 1e-12:
            continue
        for nxt, weight in adj.get(node, ()):
            candidate = d + weight
            if candidate < dist.get(nxt, math.inf) - 1e-12:
                dist[nxt] = candidate
                heapq.heappush(heap, (candidate, nxt))
    raise ValueError(f"unreachable OD {start}->{end}")


def reference_flow(path):
    rows = csv_rows(path)
    return {r["path_id"]: float(r["flow"]) for r in rows}


def link_flow(path):
    rows = csv_rows(path)
    return {r["link_id"]: float(r["volume"]) for r in rows}


def baseline(data, extra):
    f0 = extra["f0"]
    v = np.asarray(extra["A_link_path"] @ f0).ravel()
    tt = cost(v, data["t0"], data["alpha"], data["beta"], data["capacity"])
    F = float(np.sum(bpr(v, data["t0"], data["alpha"], data["beta"], data["capacity"])))
    T = float(v @ tt)
    adj = {}
    for row, c in zip(extra["links"], tt):
        adj.setdefault(row["from_node_id"], []).append((row["to_node_id"], float(c)))
    full_lower = sum(float(row["volume"]) * shortest(adj, row["o_zone_id"], row["d_zone_id"])
                     for row in extra["demands"])
    path_cost = {row["path_id"]: sum(tt[extra["link_index"][lid]] for lid in row["link_id_sequence"].split(";"))
                 for row in extra["paths"]}
    pool_lower = sum(float(row["volume"]) * min(path_cost[p["path_id"]] for p in extra["paths"]
                                                    if p["o_node_id"] == row["o_zone_id"] and p["d_node_id"] == row["d_zone_id"])
                     for row in extra["demands"])
    saved_paths = reference_flow(ROOT / "reference" / "full_path_flow.csv")
    saved_link = link_flow(ROOT / "reference" / "link_flow.csv")
    saved_fw = link_flow(ROOT / "reference" / "fw_solution.csv")
    max_path_diff = max(abs(f0[i] - saved_paths[p["path_id"]]) for i, p in enumerate(extra["paths"]))
    max_link_diff = max(abs(v[i] - saved_link[lid]) for i, lid in enumerate(data["links"]))
    max_fw_diff = max(abs(v[i] - saved_fw[lid]) for i, lid in enumerate(data["links"]))
    return dict(f0_equals_saved_full_path_max_abs=max_path_diff,
                f0_link_minus_saved_full_max_abs=max_link_diff,
                f0_link_minus_FW_max_abs=max_fw_diff,
                Beckmann_F=F, TSTT=T, full_gap_absolute=T-full_lower,
                full_gap_relative_TSTT=(T-full_lower)/T,
                pool_gap_absolute=T-pool_lower, pool_gap_relative_TSTT=(T-pool_lower)/T)


def main():
    print("PREFLIGHT_START", flush=True)
    derivative = []
    for beta in (2, 4):
        for v in (0.0, 3.0, 17.0):
            t0, alpha, cap = 2.3, 0.25, 20.0
            if v == 0:
                # One-sided derivative on the nonnegative feasible domain.
                h = 1e-6
                numeric = (bpr(h, t0, alpha, beta, cap) - bpr(0.0, t0, alpha, beta, cap)) / h
            else:
                h = 1e-5
                numeric = (bpr(v+h, t0, alpha, beta, cap) - bpr(v-h, t0, alpha, beta, cap)) / (2*h)
            analytic = cost(v, t0, alpha, beta, cap)
            derivative.append(dict(beta=beta, flow=v, value=float(bpr(v,t0,alpha,beta,cap)),
                                   analytic_derivative=float(analytic), numerical_derivative=float(numeric),
                                   abs_error=float(abs(analytic-numeric))))
    if max(x["abs_error"] for x in derivative) > 1e-7:
        raise AssertionError("BPR derivative fixture failed")
    checks = []
    for rank in (26, 52):
        print(f"LOAD_RANK_{rank}", flush=True)
        data, comp, extra = load_case(rank)
        print(f"BUILD_RANK_{rank}", flush=True)
        model, _, adaptation = build_native_l3(data, comp, 10.0, np.zeros(26))
        print(f"BUILT_RANK_{rank}", flush=True)
        counts = model_counts(model, comp, data)
        print(f"COUNTED_RANK_{rank}: {counts}", flush=True)
        if counts["total_native_variables"] != 5091+26+rank or counts["link_equalities"] != 5091 or counts["minor_nonnegative_inequalities"] != 104 or counts["total_active_constraints"] != 5195:
            raise AssertionError("native L3 model count mismatch")
        if any(model.v[a].lb != 0.0 for a in model.LINKS):
            raise AssertionError("link lower bound differs from zero")
        if any(not model.link_con[a].active for a in model.LINKS) or any(not model.minor_con[i].active for i in model.MINOR):
            raise AssertionError("L3 constraints inactive")
        theta_initial = np.array([pyo.value(model.theta[j]) for j in model.LATENT])
        x1_initial = np.array([pyo.value(model.x1[p]) for p in model.MAJOR])
        v_initial = np.array([pyo.value(model.v[a]) for a in model.LINKS])
        if np.max(np.abs(theta_initial - comp["theta_ref"])) > 1e-12 or np.max(np.abs(x1_initial - comp["x1_ref"])) > 1e-12:
            raise AssertionError("source reference initialization differs")
        if np.max(np.abs(v_initial - 0.1)) > 1e-12:
            raise AssertionError("source explicit link initial value differs")
        zero_rows = np.flatnonzero(extra["A_link_path"].getnnz(axis=1) == 0)
        print(f"ZERO_ROWS_RANK_{rank}", flush=True)
        if len(zero_rows) != 4620 or np.max(np.abs(comp["D"][zero_rows])) > 1e-12:
            raise AssertionError("unsupported Boston link rows differ")
        zero_a = int(zero_rows[0])
        model.v[zero_a].set_value(0.0)
        if abs(float(pyo.value(model.link_con[zero_a].body))) > 1e-12:
            raise AssertionError("zero-support link equality incompatible with v=0")
        model.v[zero_a].set_value(0.1)
        # A nonzero basis row can be pushed negative; the active L3 row must reject it.
        row_norm = np.linalg.norm(comp["U_r"], axis=1)
        print(f"FIXTURE_RANK_{rank}", flush=True)
        row_i = int(np.argmax(row_norm))
        theta_bad = -comp["U_r"][row_i, :]
        print(f"FIXTURE_SET_RANK_{rank}", flush=True)
        for j, val in enumerate(theta_bad):
            model.theta[j].set_value(float(val))
        print(f"FIXTURE_EVAL_RANK_{rank}", flush=True)
        bad_flow = float(comp["U_r"][row_i, :] @ theta_bad)
        constraint_body = float(pyo.value(model.minor_con[row_i].body))
        print(f"FIXTURE_BODY_RANK_{rank}: {constraint_body}", flush=True)
        if not (bad_flow < -1e-8 and abs(constraint_body-bad_flow) < 1e-9 and model.minor_con[row_i].lower == 0):
            raise AssertionError("negative reconstructed minor fixture not rejected")
        print(f"FIXTURE_ASSERTED_RANK_{rank}", flush=True)
        initial_link_equality = float(np.max(np.abs(v_initial - (comp["B1"].T @ x1_initial + comp["D"] @ theta_initial))))
        print(f"BASELINE_RANK_{rank}", flush=True)
        base = baseline(data, extra)
        print(f"BASELINE_DONE_RANK_{rank}", flush=True)
        if base["f0_equals_saved_full_path_max_abs"] > 1e-12 or base["full_gap_relative_TSTT"] > 1e-10:
            raise AssertionError("f0 baseline/reference mismatch")
        record = dict(rank=rank, identity=extra["identity"], model_counts=counts,
                      builder_adaptation=adaptation, baseline_f0=base,
                      negative_minor_fixture=dict(minor_row=row_i, raw_flow=bad_flow,
                                                  active_constraint_body=constraint_body,
                                                  constraint_lower_bound=float(model.minor_con[row_i].lower)),
                      initialization=dict(major_min=float(np.min(x1_initial)), major_max=float(np.max(x1_initial)),
                                          theta_max_abs=float(np.max(np.abs(theta_initial))),
                                          explicit_link_initial_min=float(np.min(v_initial)),
                                          explicit_link_initial_max=float(np.max(v_initial)),
                                          max_abs_initial_link_equality_residual=initial_link_equality,
                                          note="Source initializes explicit links to 0.1 even for 4620 zero-support rows; IPOPT must restore linking feasibility."),
                      BPR_derivative_fixtures=derivative,
                      source_sha256=sha(ROOT / "source_snapshot" / "run_diagnostic_levels.py"),
                      basis_sha256=sha(INPUT / "bases" / f"rank{rank}.npz"),
                      accepted_pre_solve=True)
        dump(ROOT / "checks" / f"preflight_rank{rank}.json", record)
        checks.append({"rank": rank, "counts": counts, "baseline_F": base["Beckmann_F"],
                       "baseline_full_gap_relative": base["full_gap_relative_TSTT"]})
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    import json
    main()
