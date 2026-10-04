"""R2 full-arc consensus ADMM. Inputs are only the contract and preregistered policy."""
from __future__ import annotations

import argparse
import csv
import json
import math
import time
from pathlib import Path

import numpy as np

from local_subproblem_adapter import initial_potential, solve_local
from space_time_capacity_problem_contract import load, shortest_path


def project_capacity(y, cap, allowed):
    out = np.where(allowed, np.maximum(y,0), 0.0)
    overloaded = np.flatnonzero(out.sum(axis=0) > cap)
    for a in overloaded:
        ix = np.flatnonzero(allowed[:,a])
        if cap[a] <= 0:
            out[ix,a] = 0
            continue
        vals = out[ix,a]
        order = np.sort(vals)[::-1]
        prefix = np.cumsum(order)
        good = np.flatnonzero(order-(prefix-cap[a])/np.arange(1,len(order)+1) > 0)
        if len(good):
            j = int(good[-1])
            out[ix,a] = np.maximum(vals-(prefix[j]-cap[a])/(j+1),0)
        else: out[ix,a] = 0
    return out


def initial_rho(p):
    costs = p["cost"][(p["cost"] > 0) & np.isfinite(p["cost"])]
    volumes = np.array([c["volume"] for c in p["commodities"]])
    if not len(costs): raise ValueError("no positive arc cost for generic rho scale")
    return float(np.clip(np.median(costs)/np.median(volumes),1e-4,1.0))


def run(p, policy, variant):
    K,A = len(p["commodities"]),len(p["ids"])
    cfg,gates,limits = policy["local_solver"],policy["gates"],policy["limits"]
    rho0 = initial_rho(p)
    rho = rho0
    x = np.zeros((K,A)); w = np.zeros_like(x)
    for k,c in enumerate(p["commodities"]):
        _,path = shortest_path(p,k,p["cost"])
        x[k,list(path)] = c["volume"]
    z = project_capacity(x,p["cap"],p["allowed"])
    potential = np.vstack([initial_potential(p,k) for k in range(K)])
    zp = z.copy(); local_q = z-w
    history = []
    start = time.perf_counter()
    failure = None
    attempted = 0
    for iteration in range(1,limits["max_outer_iterations"]+1):
        if time.perf_counter()-start > limits["wall_seconds_per_case"]:
            failure = "wall-time gate"
            break
        attempted = iteration
        local_q = z-w
        infos=[]
        for k in range(K):
            x[k],potential[k],info = solve_local(p,k,local_q[k],rho,potential[k],cfg)
            infos.append(info)
        balance = max(i["balance"] for i in infos)
        if not math.isfinite(balance) or balance > gates["max_balance_residual"]:
            failure = f"local commodity QP conservation residual {balance:.8g} exceeds gate"
            break
        zp = z.copy()
        z = project_capacity(x+w,p["cap"],p["allowed"])
        w += x-z
        primal = float(np.linalg.norm(x-z))
        dual = float(rho*np.linalg.norm(z-zp))
        ep = float(np.sqrt(K*A)*gates["absolute_residual"]+gates["relative_residual"]*max(np.linalg.norm(x),np.linalg.norm(z)))
        ed = float(np.sqrt(K*A)*gates["absolute_residual"]+gates["relative_residual"]*rho*np.linalg.norm(w))
        capacity = float(np.maximum(x.sum(axis=0)-p["cap"],0).max())
        objective = float(np.dot(x.sum(axis=0),p["cost"]))
        history.append({"iteration":iteration,"rho":rho,"objective":objective,
                        "primal_residual":primal,"dual_residual":dual,
                        "primal_threshold":ep,"dual_threshold":ed,
                        "capacity_residual":capacity,"balance_residual":balance,
                        "local_lbfgs_iterations":sum(i["lbfgs_iterations"] for i in infos),
                        "local_newton_iterations":sum(i["newton_iterations"] for i in infos),
                        "max_local_correction_l2":max(i["correction_l2"] for i in infos),
                        "wall_seconds":time.perf_counter()-start})
        if primal<=ep and dual<=ed and capacity<=gates["max_capacity_residual"]: break
        if variant=="R2_R" and iteration%10==0:
            old = rho
            if primal>10*dual: rho = min(rho*2,min(16,rho0*16))
            elif dual>10*primal: rho = max(rho/2,max(1e-4,rho0/16))
            if old!=rho: w *= old/rho
    accepted = bool(history and failure is None and
                    history[-1]["primal_residual"]<=history[-1]["primal_threshold"] and
                    history[-1]["dual_residual"]<=history[-1]["dual_threshold"] and
                    history[-1]["capacity_residual"]<=gates["max_capacity_residual"] and
                    history[-1]["balance_residual"]<=gates["max_balance_residual"])
    return {"x":x,"z":z,"w":w,"z_previous":zp,"local_q":local_q,"potential":potential},history,{
        "status":"SOLVER_CONVERGED" if accepted else "NOT_CONVERGED","failure":failure,
        "rho_initial":rho0,"rho_final":rho,"attempted_iterations":attempted,
        "completed_iterations":len(history),"optimizer_calls":attempted*K,
        "wall_seconds":time.perf_counter()-start,"last":history[-1] if history else None}


def main():
    parser=argparse.ArgumentParser()
    for arg in ("arc","demand","output","policy","variant","case"):
        parser.add_argument("--"+arg,required=True)
    args=parser.parse_args()
    if args.variant not in ("R2_S","R2_R"): raise ValueError("unregistered variant")
    policy=json.loads(Path(args.policy).read_text())
    p=load(args.arc,args.demand)
    state,history,result=run(p,policy,args.variant)
    result.update({"method":"full_arc_consensus_admm_r2","variant":args.variant,"case":args.case,
                   "arc_count":len(p["ids"]),"commodity_count":len(p["commodities"])})
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(out/"state.npz",**state)
    if history:
        with (out/"history.csv").open("w",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=list(history[0]))
            writer.writeheader();writer.writerows(history)
    (out/"result.json").write_text(json.dumps(result,indent=2))
    print(json.dumps(result))
    return 0 if result["status"]=="SOLVER_CONVERGED" else 2


if __name__=="__main__": raise SystemExit(main())
