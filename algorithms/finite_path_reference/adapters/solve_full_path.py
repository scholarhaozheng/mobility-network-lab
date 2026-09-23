"""One finite-pool non-compressed Beckmann solve with exact OD equalities."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, minimize

from common import beckmann, link_cost, load_instance, load_pool, peak_working_set_bytes, write_rows

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--inputs",type=Path,required=True);ap.add_argument("--pool",type=Path,required=True);ap.add_argument("--out",type=Path,required=True);ap.add_argument("--config",type=Path,required=True);args=ap.parse_args()
    started=time.perf_counter();inst=load_instance(args.inputs);pool=load_pool(args.pool,inst)
    config=json.loads(args.config.read_text(encoding="utf-8"))["full_path_solver"]
    A,C,q=pool["A"],pool["C"],inst["q"]
    prep=time.perf_counter()-started
    calls=0
    def value(f):
        nonlocal calls
        calls+=1
        return beckmann(np.asarray(A@f).ravel(),inst)
    def grad(f): return np.asarray(A.T@link_cost(np.asarray(A@f).ravel(),inst)).ravel()
    solve_start=time.perf_counter()
    result=minimize(value,pool["f0"].copy(),jac=grad,method="SLSQP",bounds=Bounds(0,np.inf),
                    constraints=[LinearConstraint(C,q,q)],options={"maxiter":config["maxiter"],"ftol":config["ftol"],"disp":False})
    solve_seconds=time.perf_counter()-solve_start
    f=np.asarray(result.x,dtype=float);v=np.asarray(A@f).ravel();out=args.out;out.mkdir(parents=True,exist_ok=True)
    write_rows(out/"full_path_flow.csv",[{"path_id":p["path_id"],"path_index":i,"od_index":p["od_index"],"flow":f[i]} for i,p in enumerate(pool["paths"])],["path_id","path_index","od_index","flow"])
    write_rows(out/"link_flow.csv",[{"link_id":lid,"link_index":i,"volume":v[i]} for i,lid in enumerate(inst["link_ids"])],["link_id","link_index","volume"])
    info={"method":"noncompressed_finite_path_SLSQP","status":"success" if result.success else "solver_nonconverged","message":str(result.message),"iterations":int(result.nit),"function_calls":calls,"solver_function_evaluations":int(result.nfev),"reported_objective":float(result.fun),"preparation_seconds":prep,"solver_seconds":solve_seconds,"export_seconds":time.perf_counter()-solve_start-solve_seconds,"wall_seconds":time.perf_counter()-started,"peak_working_set_bytes":peak_working_set_bytes(),"max_abs_od_residual":float(np.max(np.abs(C@f-q))),"min_path_flow":float(np.min(f)),"path_count":len(f),"link_count":len(v),"od_count":len(q),"config":config}
    (out/"solver_result.json").write_text(json.dumps(info,indent=2),encoding="utf-8")
    (out/"solver_log.txt").write_text(json.dumps(info,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(info,indent=2))

if __name__=="__main__":main()
