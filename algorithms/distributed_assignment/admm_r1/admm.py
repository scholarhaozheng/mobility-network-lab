"""Full-arc commodity/consensus ADMM for the finite shared-capacity model."""
from __future__ import annotations

import argparse
import csv
import json
import math
import time
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.sparse import coo_matrix, eye
from scipy.sparse.linalg import lsmr, spsolve

from space_time_contract import load, shortest_path


def project_capacity(values,cap,allowed):
    """Euclidean projection onto nonnegative shared arc capacity simplices."""
    output=np.zeros_like(values);k_count,a_count=values.shape
    for a in range(a_count):
        positions=np.flatnonzero(allowed[:,a]);y=np.maximum(values[positions,a],0)
        if y.sum()<=cap[a]:output[positions,a]=y;continue
        if cap[a]<=0:continue
        sorted_y=np.sort(y)[::-1];prefix=np.cumsum(sorted_y)
        rho=np.flatnonzero(sorted_y-(prefix-cap[a])/(np.arange(len(y))+1)>0)
        if not len(rho):continue
        j=int(rho[-1]);threshold=(prefix[j]-cap[a])/(j+1)
        output[positions,a]=np.maximum(y-threshold,0)
    return output


def initial_potential(p,k):
    """Cost-based node potentials for deterministic full-DAG local QP startup."""
    distance=np.full(len(p["nodes"]),np.inf);distance[p["commodities"][k]["source"]]=0
    for node in p["order"]:
        if not np.isfinite(distance[node]):continue
        for a in p["adj"][node]:
            if p["allowed"][k,a]:
                end=p["v"][a];distance[end]=min(distance[end],distance[node]+p["cost"][a])
    distance[~np.isfinite(distance)]=0
    return distance


def local_qp(p,k,q,rho,potential,maxiter):
    indices=np.flatnonzero(p["allowed"][k]);u=p["u"][indices];v=p["v"][indices]
    c=p["cost"][indices];q=q[indices];commodity=p["commodities"][k]
    b=np.zeros(len(p["nodes"]));b[commodity["source"]]=commodity["volume"];b[commodity["sink"]]=-commodity["volume"]
    def value_grad(potential):
        x=np.maximum(0,q-(c+potential[u]-potential[v])/rho)
        divergence=np.bincount(u,weights=x,minlength=len(b))-np.bincount(v,weights=x,minlength=len(b))
        return 0.5*rho*float(np.dot(x,x))+float(np.dot(b,potential)),b-divergence
    # Do not accept function-value stagnation as local QP convergence. The
    # independent conservation gate, not scipy's success flag, is decisive.
    result=minimize(value_grad,potential,method="L-BFGS-B",jac=True,options={"maxiter":maxiter,"gtol":1e-9,"ftol":0.0,"maxls":40})
    potential=result.x.copy();nit=int(result.nit)
    # Semismooth Newton correction on the current positive-flow active set.
    # This repairs L-BFGS function-value stagnation without changing rho,
    # feasibility tolerances, or the declared local iteration budget.
    while nit<maxiter:
        value,gradient=value_grad(potential)
        if np.max(np.abs(gradient))<=1e-8:break
        active=np.maximum(0,q-(c+potential[u]-potential[v])/rho)>1e-10
        if not np.any(active):break
        ua=u[active];va=v[active];count=len(ua)
        incidence=coo_matrix((np.r_[np.ones(count),-np.ones(count)],
                              (np.r_[ua,va],np.r_[np.arange(count),np.arange(count)])),
                             shape=(len(p["nodes"]),count)).tocsr()
        hessian=(incidence@incidence.T)/rho+1e-8*eye(len(p["nodes"]),format="csr")
        step=spsolve(hessian,-gradient)
        if not np.all(np.isfinite(step)):break
        accepted=False
        for j in range(25):
            trial=potential+(0.5**j)*step
            trial_value,trial_gradient=value_grad(trial)
            if trial_value<value-1e-10 or np.max(np.abs(trial_gradient))<np.max(np.abs(gradient))*0.8:
                potential=trial;accepted=True;break
        nit+=1
        if not accepted:break
    local=np.maximum(0,q-(c+potential[u]-potential[v])/rho)
    _,gradient=value_grad(potential);residual=float(np.max(np.abs(gradient)));repair=0.0
    if residual>1e-8:
        # Explicit minimum-norm primal feasibility correction on positive arcs.
        # If the active support cannot carry the correction, the residual gate
        # still rejects the local QP. This is a numerical solve step, not a
        # reference-solution replacement.
        active=local>1e-7;ua=u[active];va=v[active];count=len(ua)
        if count:
            incidence=coo_matrix((np.r_[np.ones(count),-np.ones(count)],
                                  (np.r_[ua,va],np.r_[np.arange(count),np.arange(count)])),
                                 shape=(len(p["nodes"]),count)).tocsr()
            correction=lsmr(incidence,gradient,atol=1e-13,btol=1e-13,maxiter=maxiter)[0]
            candidate=local.copy();candidate[active]+=correction
            if np.min(candidate)>=-1e-10:
                local=candidate;repair=float(np.linalg.norm(correction))
                divergence=np.bincount(u,weights=local,minlength=len(b))-np.bincount(v,weights=local,minlength=len(b))
                residual=float(np.max(np.abs(b-divergence)))
    x=np.zeros(len(p["ids"]));x[indices]=local
    return x,potential,residual,nit,bool(result.success),repair


def run(p,gates):
    k_count=len(p["commodities"]);a_count=len(p["ids"]);n=len(p["nodes"])
    rho=gates["rho"];x=np.zeros((k_count,a_count));w=np.zeros_like(x)
    # Deterministic, method-generated initialization; no reference primal is read.
    for k,commodity in enumerate(p["commodities"]):
        _,path=shortest_path(p,k,p["cost"]);x[k,list(path)]=commodity["volume"]
    z=project_capacity(x,p["cap"],p["allowed"])
    potentials=np.vstack([initial_potential(p,k) for k in range(k_count)])
    history=[];start=time.perf_counter();calls=0;failure=None;previous=z.copy()
    for iteration in range(1,gates["max_iterations"]+1):
        max_local=0;local_iterations=0;local_success=True;max_repair=0.0
        for k in range(k_count):
            x[k],potentials[k],residual,nit,success,repair=local_qp(p,k,z[k]-w[k],rho,potentials[k],gates["local_dual_max_iterations"])
            calls+=1;max_local=max(max_local,residual);local_iterations+=nit;local_success &= success;max_repair=max(max_repair,repair)
        if max_local>gates["max_balance_residual"]:
            failure=f"local commodity QP conservation residual {max_local:.6g} exceeds gate";break
        previous=z.copy();z=project_capacity(x+w,p["cap"],p["allowed"]);w+=x-z
        primal=float(np.linalg.norm(x-z));dual=float(rho*np.linalg.norm(z-previous))
        eps_primal=math.sqrt(k_count*a_count)*gates["absolute_residual"]+gates["relative_residual"]*max(np.linalg.norm(x),np.linalg.norm(z))
        eps_dual=math.sqrt(k_count*a_count)*gates["absolute_residual"]+gates["relative_residual"]*rho*np.linalg.norm(w)
        capacity=float(np.max(np.maximum(x.sum(axis=0)-p["cap"],0)))
        balance=max_local;objective=float(np.dot(x.sum(axis=0),p["cost"]))
        history.append({"iteration":iteration,"objective":objective,"primal_residual":primal,"dual_residual":dual,
                        "primal_threshold":eps_primal,"dual_threshold":eps_dual,"capacity_residual":capacity,
                        "balance_residual":balance,"local_iterations":local_iterations,
                        "max_local_primal_correction_l2":max_repair,"wall_seconds":time.perf_counter()-start})
        if primal<=eps_primal and dual<=eps_dual and capacity<=gates["max_capacity_residual"] and balance<=gates["max_balance_residual"]:break
        if time.perf_counter()-start>gates["wall_seconds_per_case"]:failure="wall-time gate";break
    return x,z,w,previous,history,calls,failure


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--arc",required=True);ap.add_argument("--demand",required=True)
    ap.add_argument("--output",required=True);ap.add_argument("--gates",required=True);ap.add_argument("--case",required=True);args=ap.parse_args()
    p=load(args.arc,args.demand);gates=json.loads(Path(args.gates).read_text())["admm"]
    if not np.isfinite(gates["rho"]) or gates["rho"]<=0:raise ValueError("rho must be positive and finite")
    estimate_gib=4*len(p["commodities"])*len(p["ids"])*8/(1024**3)
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    if estimate_gib>gates["memory_gate_gib"]:
        report={"case":args.case,"status":"RESOURCE_GATED","estimated_main_arrays_gib":estimate_gib,"optimizer_calls":0}
        (out/"result.json").write_text(json.dumps(report,indent=2));print(json.dumps(report));return 2
    start=time.perf_counter();x,z,w,zprev,history,calls,failure=run(p,gates)
    np.savez_compressed(out/"state.npz",x=x,z=z,w=w,z_previous=zprev)
    if history:
        with (out/"history.csv").open("w",newline="",encoding="utf-8") as f:
            writer=csv.DictWriter(f,fieldnames=list(history[0]));writer.writeheader();writer.writerows(history)
    accepted=bool(history and not failure and history[-1]["primal_residual"]<=history[-1]["primal_threshold"] and
                  history[-1]["dual_residual"]<=history[-1]["dual_threshold"] and
                  history[-1]["capacity_residual"]<=gates["max_capacity_residual"] and
                  history[-1]["balance_residual"]<=gates["max_balance_residual"])
    report={"method":"full_arc_consensus_admm","case":args.case,"status":"ADMM_BOUNDED_PILOT" if accepted else "NOT_CONVERGED",
            "iterations":len(history),"optimizer_calls":calls,"wall_seconds":time.perf_counter()-start,"rho":gates["rho"],
            "failure":failure,"last":history[-1] if history else None,"estimated_main_arrays_gib":estimate_gib}
    (out/"result.json").write_text(json.dumps(report,indent=2),encoding="utf-8");print(json.dumps(report));return 0 if accepted else 2


if __name__=="__main__":raise SystemExit(main())
