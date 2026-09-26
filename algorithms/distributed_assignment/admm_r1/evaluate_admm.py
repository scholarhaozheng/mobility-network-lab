"""Independent saved-state ADMM residual and flow verifier; zero optimizer calls."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from space_time_contract import load


def evaluate(arc,demand,result,gates_path,reference=None):
    p=load(arc,demand);folder=Path(result);saved=json.loads((folder/"result.json").read_text())
    if not (folder/"state.npz").exists():return {"status":"FAIL","reason":"no saved ADMM state","optimizer_calls":0}
    state=np.load(folder/"state.npz");x,z,w,zprev=(state[k] for k in ("x","z","w","z_previous"))
    gates=json.loads(Path(gates_path).read_text())["admm"];k_count,a_count=x.shape
    if x.shape!=(len(p["commodities"]),len(p["ids"])) or z.shape!=x.shape or w.shape!=x.shape or zprev.shape!=x.shape:
        return {"status":"FAIL","reason":"inconsistent consensus dimensions","optimizer_calls":0}
    balance=0.0
    for k,c in enumerate(p["commodities"]):
        b=np.bincount(p["u"],weights=x[k],minlength=len(p["nodes"]))-np.bincount(p["v"],weights=x[k],minlength=len(p["nodes"]))
        b[c["source"]]-=c["volume"];b[c["sink"]]+=c["volume"];balance=max(balance,float(np.max(np.abs(b))))
    primal=float(np.linalg.norm(x-z));dual=float(gates["rho"]*np.linalg.norm(z-zprev))
    eps_primal=float(np.sqrt(k_count*a_count)*gates["absolute_residual"]+gates["relative_residual"]*max(np.linalg.norm(x),np.linalg.norm(z)))
    eps_dual=float(np.sqrt(k_count*a_count)*gates["absolute_residual"]+gates["relative_residual"]*gates["rho"]*np.linalg.norm(w))
    capacity=float(np.max(np.maximum(x.sum(axis=0)-p["cap"],0)));z_capacity=float(np.max(np.maximum(z.sum(axis=0)-p["cap"],0)))
    objective=float(np.dot(x.sum(axis=0),p["cost"]));forbidden=float(np.max(np.abs(x[~p["allowed"]]))) if np.any(~p["allowed"]) else 0
    out={"optimizer_calls":0,"saved_solver_optimizer_calls":saved.get("optimizer_calls"),"objective_recomputed":objective,
         "primal_residual":primal,"dual_residual":dual,"primal_threshold":eps_primal,"dual_threshold":eps_dual,
         "max_balance_residual":balance,"max_capacity_residual":capacity,"max_consensus_capacity_residual":z_capacity,
         "min_local_flow":float(np.min(x)),"min_consensus_flow":float(np.min(z)),"max_forbidden_connector_flow":forbidden}
    if reference:
        ref=json.loads(Path(reference).read_text());out["reference_objective"]=ref.get("objective_value")
        if ref.get("objective_value") is not None:out["reference_gap"]=abs(objective-ref["objective_value"])/max(1,abs(ref["objective_value"]))
    valid=primal<=eps_primal and dual<=eps_dual and capacity<=gates["max_capacity_residual"] and balance<=gates["max_balance_residual"]
    valid &= z_capacity<=1e-8 and out["min_local_flow"]>=-1e-8 and out["min_consensus_flow"]>=-1e-8 and forbidden<=1e-8
    valid &= saved["status"]=="ADMM_BOUNDED_PILOT"
    out["status"]="PASS" if valid else "FAIL";return out


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--arc",required=True);ap.add_argument("--demand",required=True)
    ap.add_argument("--result",required=True);ap.add_argument("--gates",required=True);ap.add_argument("--reference");args=ap.parse_args()
    try:out=evaluate(args.arc,args.demand,args.result,args.gates,args.reference)
    except Exception as exc:out={"status":"FAIL","reason":str(exc),"optimizer_calls":0}
    (Path(args.result)/"evaluation.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
    print(json.dumps(out));return 0 if out["status"]=="PASS" else 2


if __name__=="__main__":raise SystemExit(main())
