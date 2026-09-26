"""Commodity QP in demand-normalized coordinates; no reference-solution inputs."""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize
from scipy.sparse import coo_matrix, eye
from scipy.sparse.linalg import lsmr, spsolve


def initial_potential(p, k):
    distance = np.full(len(p["nodes"]), np.inf)
    distance[p["commodities"][k]["source"]] = 0.0
    for node in p["order"]:
        if not np.isfinite(distance[node]): continue
        for a in p["adj"][node]:
            if p["allowed"][k, a]:
                v = p["v"][a]
                distance[v] = min(distance[v], distance[node] + p["cost"][a])
    distance[~np.isfinite(distance)] = 0.0
    return distance


def incidence(u, v, n):
    m = len(u)
    return coo_matrix((np.r_[np.ones(m), -np.ones(m)],
                       (np.r_[u, v], np.r_[np.arange(m), np.arange(m)])),
                      shape=(n, m)).tocsr()


def solve_local(p, k, q, rho, potential, cfg):
    allowed = np.flatnonzero(p["allowed"][k])
    u, v = p["u"][allowed], p["v"][allowed]
    c, q = p["cost"][allowed], q[allowed]
    d = p["commodities"][k]["volume"]
    n = len(p["nodes"])
    source = p["commodities"][k]["source"]
    sink = p["commodities"][k]["sink"]
    b = np.zeros(n)
    b[source], b[sink] = 1.0, -1.0
    qb = q/d
    cb = c/(rho*d)

    def value_gradient(h):
        y = np.maximum(0.0, qb-cb-h[u]+h[v])
        div = np.bincount(u, weights=y, minlength=n)-np.bincount(v, weights=y, minlength=n)
        return 0.5*float(np.dot(y,y))+float(np.dot(b,h)), b-div

    h0 = potential/(rho*d)
    fit = minimize(value_gradient, h0, jac=True, method="L-BFGS-B",
                   options={"maxiter":cfg["lbfgs_max_iterations"],
                            "gtol":cfg["lbfgs_gradient_tolerance_scaled"],
                            "ftol":cfg["lbfgs_function_tolerance"],
                            "maxls":cfg["max_line_search_steps"]})
    h = fit.x.copy()
    newton_steps = 0
    for _ in range(cfg["newton_max_iterations"]):
        val, grad = value_gradient(h)
        if d*np.max(abs(grad)) <= cfg["local_original_balance_target"]: break
        active = (qb-cb-h[u]+h[v]) > 1e-10
        if not np.any(active): break
        B = incidence(u[active], v[active], n)
        H = B@B.T + 1e-9*eye(n, format="csr")
        step = spsolve(H, -grad)
        if not np.all(np.isfinite(step)): break
        accepted = False
        for j in range(30):
            trial = h+(0.5**j)*step
            trial_val, trial_grad = value_gradient(trial)
            if trial_val < val-1e-12 or np.max(abs(trial_grad)) < 0.8*np.max(abs(grad)):
                h = trial
                accepted = True
                break
        newton_steps += 1
        if not accepted: break
    y = np.maximum(0.0, qb-cb-h[u]+h[v])
    _, grad = value_gradient(h)
    correction_norm = 0.0
    if d*np.max(abs(grad)) > cfg["local_original_balance_target"]:
        # Keep every strictly positive support arc. A demand-normalized
        # threshold of 1e-7 discarded a real ~1e-5 vehicle flow in Sioux 250
        # and made its interior-node correction algebraically impossible.
        active = y > 0.0
        if np.any(active):
            B = incidence(u[active], v[active], n)
            correction = lsmr(B, grad, atol=1e-13, btol=1e-13,
                              maxiter=cfg["lbfgs_max_iterations"])[0]
            candidate = y.copy()
            candidate[active] += correction
            if np.min(candidate) >= -1e-12:
                y = np.maximum(candidate, 0)
                correction_norm = float(d*np.linalg.norm(correction))
    div = np.bincount(u, weights=y, minlength=n)-np.bincount(v, weights=y, minlength=n)
    residual = float(d*np.max(abs(div-b)))
    full = np.zeros(len(p["ids"]))
    full[allowed] = d*y
    return full, rho*d*h, {"balance":residual, "lbfgs_iterations":int(fit.nit),
                             "newton_iterations":newton_steps,"correction_l2":correction_norm,
                             "optimizer_success":bool(fit.success)}
