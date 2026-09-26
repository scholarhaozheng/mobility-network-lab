"""Solver-free, saved-result evaluator for finite shared-capacity flow."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from space_time_contract import load


def rows(path):
    with Path(path).open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))


def separate_shortest(p,k,weights):
    """Independent topological Bellman recursion used only for certification."""
    commodity=p["commodities"][k];distance=np.full(len(p["nodes"]),np.inf);distance[commodity["source"]]=0
    for node in p["order"]:
        if not np.isfinite(distance[node]):continue
        for a in p["adj"][node]:
            if p["allowed"][k,a]:distance[p["v"][a]]=min(distance[p["v"][a]],distance[node]+weights[a])
    return float(distance[commodity["sink"]])


def evaluate(arc_file,demand_file,result_dir,reference_file=None):
    p=load(arc_file,demand_file);folder=Path(result_dir)
    result=json.loads((folder/"result.json").read_text(encoding="utf-8")); kmap={c["id"]:i for i,c in enumerate(p["commodities"])}
    amap={name:i for i,name in enumerate(p["ids"])};k_count=len(kmap);a_count=len(amap)
    multiplier_rows=rows(folder/"multipliers.csv")
    lam=np.zeros(a_count)
    for r in multiplier_rows:lam[amap[r["arc_id"]]]=float(r["lambda"])
    if np.min(lam)<-1e-10:raise ValueError("negative multiplier")
    recomputed_dual=sum(c["volume"]*separate_shortest(p,k,p["cost"]+lam) for k,c in enumerate(p["commodities"]))-float(np.dot(lam,p["cap"]))
    history=rows(folder/"history.csv");last_dual=float(history[-1]["dual"]);best_dual=max(float(r["dual"]) for r in history)
    out={"case":result["case"],"optimizer_calls":0,"saved_solver_optimizer_calls":result.get("optimizer_calls"),
         "min_multiplier":float(np.min(lam)),"last_dual_recomputed":float(recomputed_dual),
         "last_dual_saved":last_dual,"last_dual_error":abs(recomputed_dual-last_dual),
         "best_dual_from_history":best_dual,"best_dual_saved":result["best_dual"],
         "primal_available":(folder/"commodity_arc_flow.csv").exists()}
    if out["primal_available"]:
        x=np.zeros((k_count,a_count))
        for r in rows(folder/"commodity_arc_flow.csv"):x[kmap[r["demand_id"]],amap[r["arc_id"]]]+=float(r["flow"])
        node_balance=np.zeros((k_count,len(p["nodes"])))
        for k in range(k_count):
            np.add.at(node_balance[k],p["u"],x[k]);np.add.at(node_balance[k],p["v"],-x[k])
            node_balance[k,p["commodities"][k]["source"]]-=p["commodities"][k]["volume"]
            node_balance[k,p["commodities"][k]["sink"]]+=p["commodities"][k]["volume"]
        total=x.sum(axis=0);physical={}
        for a,arc in enumerate(p["arcs"]):
            if arc["arc_type"]=="movement":
                lid=arc["physical_link_id"];physical[lid]=physical.get(lid,0)+float(total[a])
        supplied={r["physical_link_id"]:float(r["flow"]) for r in rows(folder/"physical_link_flow.csv")}
        physical_error=max((abs(physical.get(lid,0)-supplied.get(lid,0)) for lid in physical.keys()|supplied.keys()),default=0)
        obj=float(np.dot(total,p["cost"]));balance=float(np.max(np.abs(node_balance)));capacity=float(np.max(np.maximum(total-p["cap"],0)))
        forbidden=float(np.max(x[~p["allowed"]])) if np.any(~p["allowed"]) else 0
        out.update({"objective_recomputed":obj,"objective_saved":result["best_primal"],"max_balance_residual":balance,
                    "max_capacity_residual":capacity,"max_physical_projection_residual":physical_error,
                    "min_flow":float(np.min(x)),"max_forbidden_connector_flow":forbidden,
                    "duality_gap_recomputed":max(0,(obj-best_dual)/max(1,abs(obj))),
                    "positive_commodity_arcs":int(np.sum(x>1e-8))})
    if reference_file:
        ref=json.loads(Path(reference_file).read_text(encoding="utf-8"));out["reference_objective"]=ref.get("objective_value")
        if ref.get("objective_value") is not None:
            out["dual_exceeds_reference_by"]=max(0,best_dual-ref["objective_value"])
            if out["primal_available"]:out["primal_reference_gap"]=abs(out["objective_recomputed"]-ref["objective_value"])/max(1,abs(ref["objective_value"]))
    valid=out["last_dual_error"]<=1e-5*max(1,abs(last_dual)) and abs(best_dual-result["best_dual"])<=1e-5*max(1,abs(best_dual))
    if out["primal_available"]:
        valid &= out["max_balance_residual"]<=1e-6 and out["max_capacity_residual"]<=1e-6 and out["min_flow"]>=-1e-8
        valid &= out["max_physical_projection_residual"]<=1e-6 and out["max_forbidden_connector_flow"]<=1e-8
        valid &= abs(out["objective_recomputed"]-out["objective_saved"])<=1e-5*max(1,abs(out["objective_recomputed"]))
    if "dual_exceeds_reference_by" in out:valid &= out["dual_exceeds_reference_by"]<=1e-5*max(1,abs(out["reference_objective"]))
    out["status"]="PASS" if valid else "FAIL"
    return out


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--arc",required=True);ap.add_argument("--demand",required=True)
    ap.add_argument("--result",required=True);ap.add_argument("--reference");args=ap.parse_args()
    try:out=evaluate(args.arc,args.demand,args.result,args.reference)
    except Exception as e:
        out={"status":"FAIL","error":str(e),"optimizer_calls":0}
    (Path(args.result)/"evaluation.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
    print(json.dumps(out));return 0 if out["status"]=="PASS" else 2


if __name__=="__main__":raise SystemExit(main())
