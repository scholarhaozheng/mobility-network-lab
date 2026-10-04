"""Solver-free, original-unit checks for the finite shared-capacity ADMM split."""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from space_time_capacity_problem_contract import load


def capacity_projection(y, cap, allowed):
    """Independent simplex projection, including forbidden-connector zeros."""
    out = np.zeros_like(y)
    for a in range(y.shape[1]):
        ix = np.flatnonzero(allowed[:, a])
        vals = np.maximum(y[ix, a], 0.0)
        if vals.sum() <= cap[a]:
            out[ix, a] = vals
        elif cap[a] > 0:
            lo, hi = 0.0, float(vals.max())
            for _ in range(70):
                threshold = (lo + hi) / 2
                if np.maximum(vals - threshold, 0).sum() > cap[a]: lo = threshold
                else: hi = threshold
            out[ix, a] = np.maximum(vals - hi, 0.0)
    return out


def local_metrics(p, k, x, q, rho, potential=None):
    c = p["commodities"][k]
    n = len(p["nodes"])
    balance = np.bincount(p["u"], weights=x, minlength=n) - np.bincount(p["v"], weights=x, minlength=n)
    expected = np.zeros(n)
    expected[c["source"]] = c["volume"]
    expected[c["sink"]] = -c["volume"]
    err = balance - expected
    a = int(np.argmax(abs(err)))
    out = {"commodity": c["id"], "volume": c["volume"], "max_balance": float(abs(err[a])),
           "max_balance_scaled_by_volume": float(abs(err[a]) / c["volume"]),
           "worst_node": p["nodes"][a], "source_error": float(err[c["source"]]),
           "sink_error": float(err[c["sink"]]), "minimum_flow": float(x.min()),
           "max_forbidden": float(abs(x[~p["allowed"][k]]).max()) if np.any(~p["allowed"][k]) else 0.0,
           "linear_objective": float(np.dot(p["cost"], x)),
           "penalty": float(rho * 0.5 * np.dot(x-q, x-q))}
    if potential is not None:
        stationarity = p["cost"] + rho * (x-q) + potential[p["u"]] - potential[p["v"]]
        mask = p["allowed"][k]
        positive = mask & (x > 1e-8)
        inactive = mask & ~positive
        out["kkt_active_max"] = float(abs(stationarity[positive]).max()) if np.any(positive) else 0.0
        out["kkt_inactive_negative_max"] = float(np.maximum(-stationarity[inactive], 0).max()) if np.any(inactive) else 0.0
    return out


def evaluate(p, x, z, w, z_previous, local_q, rho, potential=None, gates=None, saved=None):
    if not all(np.all(np.isfinite(v)) for v in (x, z, w, z_previous, local_q)) or not math.isfinite(rho) or rho <= 0:
        return {"status": "FAIL", "reason": "nonfinite state or invalid rho", "optimizer_calls": 0}
    shape = (len(p["commodities"]), len(p["ids"]))
    if any(v.shape != shape for v in (x,z,w,z_previous,local_q)):
        return {"status": "FAIL", "reason": "arc/commodity mapping mismatch", "optimizer_calls": 0}
    if potential is not None and potential.shape != (shape[0], len(p["nodes"])):
        return {"status": "FAIL", "reason": "potential mapping mismatch", "optimizer_calls": 0}
    local = [local_metrics(p,k,x[k],local_q[k],rho,None if potential is None else potential[k]) for k in range(shape[0])]
    prior_w = z_previous - local_q
    projected = capacity_projection(x + prior_w, p["cap"], p["allowed"])
    total = x.sum(axis=0)
    physical = {}
    for a, arc in enumerate(p["arcs"]):
        if arc["arc_type"] == "movement":
            lid = arc["physical_link_id"]
            physical[lid] = physical.get(lid,0.0) + float(total[a])
    primal = float(np.linalg.norm(x-z))
    dual = float(rho*np.linalg.norm(z-z_previous))
    atol = gates.get("absolute_residual", 1e-5) if gates else 1e-5
    rtol = gates.get("relative_residual", 1e-4) if gates else 1e-4
    eps_p = float(np.sqrt(x.size)*atol + rtol*max(np.linalg.norm(x),np.linalg.norm(z)))
    eps_d = float(np.sqrt(x.size)*atol + rtol*rho*np.linalg.norm(w))
    out = {"optimizer_calls": 0, "local": local, "max_balance": max(d["max_balance"] for d in local),
           "max_kkt_active": max(d.get("kkt_active_max", 0) for d in local),
           "max_kkt_inactive_negative": max(d.get("kkt_inactive_negative_max", 0) for d in local),
           "min_flow": float(x.min()), "max_forbidden": max(d["max_forbidden"] for d in local),
           "primal_residual": primal, "dual_residual": dual, "primal_threshold": eps_p, "dual_threshold": eps_d,
           "max_capacity_excess": float(np.maximum(total-p["cap"],0).max()),
           "max_z_capacity_excess": float(np.maximum(z.sum(axis=0)-p["cap"],0).max()),
           "max_projection_error": float(abs(z-projected).max()),
           "max_dual_update_error": float(abs(w-(prior_w+x-z)).max()),
           "objective": float(np.dot(total,p["cost"])),
           "local_objective_sum": sum(d["linear_objective"] for d in local),
           "physical_link_flow": physical}
    if saved is not None:
        out["saved_objective_error"] = abs(out["objective"]-saved.get("objective",out["objective"]))
    if gates is not None:
        tol = gates["max_balance_residual"]
        pass_items = {"local_conservation":out["max_balance"]<=tol,
                      "nonnegative":out["min_flow"]>=-1e-8,
                      "forbidden":out["max_forbidden"]<=1e-8,
                      "primal":primal<=eps_p,"dual":dual<=eps_d,
                      "capacity":out["max_capacity_excess"]<=gates["max_capacity_residual"],
                      "consensus_capacity":out["max_z_capacity_excess"]<=1e-8,
                      "projection":out["max_projection_error"]<=1e-7,
                      "dual_update":out["max_dual_update_error"]<=1e-7,
                      "objective_recompute":out.get("saved_objective_error",0)<=1e-7*max(1,abs(out["objective"]))}
        if potential is not None:
            pass_items["local_kkt"] = max(out["max_kkt_active"],out["max_kkt_inactive_negative"]) <= gates["max_kkt_residual"]
        out["gates"] = pass_items
        out["status"] = "PASS" if all(pass_items.values()) else "FAIL"
    return out


def evaluate_files(arc, demand, run_dir, policy):
    p = load(arc,demand)
    run_dir = Path(run_dir)
    state = np.load(run_dir/"state.npz")
    result = json.loads((run_dir/"result.json").read_text())
    return evaluate(p,*(state[k] for k in ("x","z","w","z_previous","local_q")),
                    rho=float(result["rho_final"]),potential=state["potential"],gates=policy["gates"],
                    saved=result.get("last",{}))
