"""Task-local native Diagnostic L3 controller for any prepared path instance.

The isolated accepted builder is adapted only for heterogeneous BPR, legal
zero link bounds, and exact feasible initialization. gamma=0 throughout.
"""
from __future__ import annotations
import argparse
import ast
import csv
import ctypes
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

from mcl_assignment import aon, graph, costs, objective, atomic_json, sha, write_rows, GATES
from mcl_path_methods import load_pool

OPTIONS={"tol":1e-8,"constr_viol_tol":1e-9,"dual_inf_tol":1e-6,
         "compl_inf_tol":1e-8,"acceptable_iter":0,"bound_relax_factor":0,
         "honor_original_bounds":"no","max_iter":500,"mu_strategy":"adaptive",
         "linear_solver":"mumps","print_level":5}


def task_tree_memory(root_pid):
    """Read only the current worker PID and descendants on Windows."""
    if os.name!="nt":return {"status":"unavailable_non_windows"}
    from ctypes import wintypes
    class Entry(ctypes.Structure):
        _fields_=[("dwSize",wintypes.DWORD),("cntUsage",wintypes.DWORD),
                  ("th32ProcessID",wintypes.DWORD),("th32DefaultHeapID",ctypes.c_size_t),
                  ("th32ModuleID",wintypes.DWORD),("cntThreads",wintypes.DWORD),
                  ("th32ParentProcessID",wintypes.DWORD),("pcPriClassBase",wintypes.LONG),
                  ("dwFlags",wintypes.DWORD),("szExeFile",wintypes.WCHAR*260)]
    class Counters(ctypes.Structure):
        _fields_=[("cb",wintypes.DWORD),("PageFaultCount",wintypes.DWORD),
                  ("PeakWorkingSetSize",ctypes.c_size_t),("WorkingSetSize",ctypes.c_size_t),
                  ("QuotaPeakPagedPoolUsage",ctypes.c_size_t),("QuotaPagedPoolUsage",ctypes.c_size_t),
                  ("QuotaPeakNonPagedPoolUsage",ctypes.c_size_t),("QuotaNonPagedPoolUsage",ctypes.c_size_t),
                  ("PagefileUsage",ctypes.c_size_t),("PeakPagefileUsage",ctypes.c_size_t),
                  ("PrivateUsage",ctypes.c_size_t)]
    kernel=ctypes.windll.kernel32;psapi=ctypes.windll.psapi
    kernel.CreateToolhelp32Snapshot.restype=ctypes.c_void_p
    kernel.OpenProcess.restype=ctypes.c_void_p
    snap=kernel.CreateToolhelp32Snapshot(2,0)
    if snap in (0,ctypes.c_void_p(-1).value):return {"status":"snapshot_failed"}
    parent={};names={};entry=Entry();entry.dwSize=ctypes.sizeof(Entry)
    okay=kernel.Process32FirstW(ctypes.c_void_p(snap),ctypes.byref(entry))
    while okay:
        parent[int(entry.th32ProcessID)]=int(entry.th32ParentProcessID)
        names[int(entry.th32ProcessID)]=entry.szExeFile
        okay=kernel.Process32NextW(ctypes.c_void_p(snap),ctypes.byref(entry))
    kernel.CloseHandle(ctypes.c_void_p(snap))
    descendants={root_pid};changed=True
    while changed:
        before=len(descendants)
        descendants.update(pid for pid,ppid in parent.items() if ppid in descendants)
        changed=len(descendants)>before
    records=[]
    for pid in sorted(descendants):
        handle=kernel.OpenProcess(0x0400|0x0010,False,pid)
        if not handle:continue
        counter=Counters();counter.cb=ctypes.sizeof(Counters)
        if psapi.GetProcessMemoryInfo(ctypes.c_void_p(handle),ctypes.byref(counter),counter.cb):
            records.append({"pid":pid,"name":names.get(pid),"working_set":int(counter.WorkingSetSize),
                            "peak_working_set":int(counter.PeakWorkingSetSize),"private_bytes":int(counter.PrivateUsage)})
        kernel.CloseHandle(ctypes.c_void_p(handle))
    return {"status":"sampled","processes":records,"working_set_sum":sum(x["working_set"] for x in records),
            "private_bytes_sum":sum(x["private_bytes"] for x in records)}


def build_model(data,comp,rho,lam,source):
    import numpy as np
    import pyomo.environ as pyo
    src=Path(source).read_text(encoding="utf-8")
    tree=ast.parse(src)
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="build_alm_model_levels")
    segment=ast.get_source_segment(src,node)
    old="""routing_cost = sum(data['t0'][a] * m.v[a] + (data['t0'][a] * data['alpha'][a] / 5.0) * m.v[a] * (
                    (m.v[a] / max(data['capacity'][a], 1e-6)) ** 4) for a in m.LINKS)"""
    new="""routing_cost = sum(data['t0'][a] * m.v[a] + (data['t0'][a] * data['alpha'][a] / (data['beta'][a] + 1.0)) * m.v[a] * (
                    (m.v[a] / data['capacity'][a]) ** data['beta'][a]) for a in m.LINKS)"""
    if segment.count(old)!=1:raise ValueError("native BPR source expression identity changed")
    adapted=segment.replace(old,new)
    namespace={"np":np,"pyo":pyo,"defaultdict":defaultdict}
    exec(compile(adapted,str(source)+"::adapted","exec"),namespace)
    model,_=namespace["build_alm_model_levels"](data,comp,level=3,rho=rho,lambda_od=lam,gamma=0.0)
    for a in model.LINKS:model.v[a].setlb(0.0)
    # Accepted source rebuilds each outer from reference. Set the exact
    # source-independent feasible seed instead of its 0.1 link defaults.
    x1=comp["x1_ref"]
    theta=comp["theta_ref"]
    v=comp["B1"].T@x1+comp["D"]@theta
    for i in model.MAJOR:model.x1[i].set_value(float(x1[i]))
    for j in model.LATENT:model.theta[j].set_value(float(theta[j]))
    for a in model.LINKS:model.v[a].set_value(float(v[a]))
    return model,{"source_sha256":sha(source),"original_ast_sha256":hashlib.sha256(ast.dump(node,include_attributes=False).encode()).hexdigest(),
                  "adapted_sha256":hashlib.sha256(adapted.encode()).hexdigest(),"bpr_replacement_count":1,
                  "initial_link_equality_max":float(np.max(np.abs(v-(comp["B1"].T@x1+comp["D"]@theta)))),
                  "initial_link_min":float(np.min(v)),"initial_minor_min":float(np.min(comp["U_r"]@theta)),
                  "initial_od_max":float(np.max(np.abs(comp["A1"]@x1+comp["M"]@theta-data["demand"]))) }


def load_case(instance,pool,basis):
    import numpy as np
    m,links,od,paths,A,C,f0,q=load_pool(instance,pool)
    binfo=json.loads((Path(basis)/"basis.json").read_text(encoding="utf-8"))
    if binfo["instance_signature"]!=m["instance_signature"] or binfo["pool_sha256"]!=sha(Path(pool)/"paths.csv"):
        raise ValueError("basis instance/pool mismatch")
    with np.load(Path(basis)/"basis.npz",allow_pickle=False) as x:
        U=np.array(x["U"]);major=np.array(x["major"],dtype=int);minor=np.array(x["minor"],dtype=int)
        theta=np.array(x["theta_ref"]);D=np.array(x["D"]);M=np.array(x["M"])
    if U.shape!=(len(minor),binfo["rank"]) or D.shape!=(len(links),binfo["rank"]) or M.shape!=(len(od),binfo["rank"]):
        raise ValueError("basis dimensions")
    if not np.array_equal(np.sort(np.r_[major,minor]),np.arange(len(paths))):raise ValueError("basis partition")
    data={"B":A.T.tocsr(),"A":C,"links":[r["link_id"] for r in links],"n_paths":len(paths),
          "n_links":len(links),"n_od":len(od),"x_ref":f0,"demand":q,
          "capacity":np.array([float(r["capacity"]) for r in links]),
          "t0":np.array([float(r["vdf_fftt"]) for r in links]),
          "alpha":np.array([float(r["vdf_alpha"]) for r in links]),
          "beta":np.array([float(r["vdf_beta"]) for r in links])}
    comp={"B1":data["B"][major,:],"A1":C[:,major].tocsr(),"D":D,"M":M,"U_r":U,
          "x1_ref":f0[major],"theta_ref":theta,"n_major":len(major),"n_minor":len(minor),"r":U.shape[1]}
    return m,links,od,paths,A,C,f0,q,data,comp,major,minor


def worker(a):
    import numpy as np
    import pyomo.environ as pyo
    from pyomo.opt import SolverFactory
    t=time.perf_counter()
    out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    m,links,od,paths,A,C,f0,q,data,comp,major,minor=load_case(a.instance,a.pool,a.basis)
    lam=np.array(json.loads(a.lambda_json),dtype=float)
    if lam.shape!=(len(od),):raise ValueError("lambda shape")
    model,adapt=build_model(data,comp,float(a.rho),lam,a.source)
    counts={"path_coordinates":len(major)+comp["r"],"major":len(major),"minor":len(minor),
            "rank":comp["r"],"explicit_link_variables":len(links),
            "total_variables":sum(1 for _ in model.component_data_objects(pyo.Var,active=True)),
            "total_constraints":sum(1 for _ in model.component_data_objects(pyo.Constraint,active=True)),
            "link_equalities":len(model.link_con),"minor_nonnegative":len(model.minor_con)}
    if counts["total_variables"]!=len(links)+len(major)+comp["r"]:raise ValueError("native variable count")
    solver=SolverFactory("ipopt",executable=str(Path(a.ipopt).resolve()))
    if not solver.available(exception_flag=False):raise FileNotFoundError("configured IPOPT unavailable")
    solver.options.update(OPTIONS)
    info={"instance_signature":m["instance_signature"],"outer":a.outer,"rho":a.rho,"gamma":0,
          "lambda_used":lam.tolist(),"adaptation":adapt,"counts":counts,
          "python":sys.executable,"ipopt":str(Path(a.ipopt).resolve()),"options":OPTIONS}
    solve_start=time.perf_counter()
    log=out/f"outer_{a.outer:02d}_ipopt.log"
    try:
        result=solver.solve(model,tee=False,logfile=str(log),load_solutions=False,keepfiles=False)
        info["solver_status"]=str(result.solver.status)
        info["termination"]=str(result.solver.termination_condition)
        info["solution_records"]=len(result.solution)
        if result.solution:
            model.solutions.load_from(result)
            x1=np.array([pyo.value(model.x1[i]) for i in model.MAJOR]);theta=np.array([pyo.value(model.theta[j]) for j in model.LATENT])
            v=np.array([pyo.value(model.v[i]) for i in model.LINKS])
            np.savez_compressed(out/f"outer_{a.outer:02d}_solution.npz",x1=x1,theta=theta,v=v,lambda_used=lam,rho=np.array([a.rho]))
            info["solution_loaded"]=True
            info["model_objective"]=float(pyo.value(model.obj))
        else:info["solution_loaded"]=False
    except Exception as exc:
        info.update(termination="EXCEPTION",solution_loaded=False,error=repr(exc))
    info["solver_seconds"]=time.perf_counter()-solve_start
    info["worker_seconds"]=time.perf_counter()-t
    atomic_json(out/f"outer_{a.outer:02d}_native.json",info)
    print(json.dumps({"termination":info["termination"],"solution_loaded":info["solution_loaded"],"seconds":info["worker_seconds"]}))
    return 0 if info["solution_loaded"] else 2


def evaluate(instance,pool,basis,solution,fw_run=None):
    import numpy as np
    m,links,od,paths,A,C,f0,q,data,comp,major,minor=load_case(instance,pool,basis)
    with np.load(solution,allow_pickle=False) as x:
        x1=np.array(x["x1"]);theta=np.array(x["theta"]);v=np.array(x["v"])
    f=np.empty(len(paths));f[major]=x1;f[minor]=comp["U_r"]@theta
    v_path=np.asarray(A@f).ravel();odflow=np.asarray(C@f).ravel();res=odflow-q
    c=np.asarray(costs(v_path,links));adj,_=graph(links)
    _,_,short_sum=aon(links,adj,od,c)
    total=float(v_path@c);gap=total-short_sum;rel=gap/max(total,1e-12)
    pool_short=0.0
    for i,r in enumerate(od):
        members=C.getrow(i).indices
        pool_short+=q[i]*min(float(A[:,j].T@c) for j in members)
    pool_gap=total-pool_short
    out={"instance_signature":m["instance_signature"],"path_count":len(paths),"rank":comp["r"],
         "min_path_flow_raw":float(np.min(f)),"negative_path_count_raw":int(np.sum(f<0)),
         "negative_path_mass_raw":float(np.sum(np.maximum(-f,0))),
         "min_explicit_link_flow_raw":float(np.min(v)),"negative_explicit_link_count_raw":int(np.sum(v<0)),
         "max_abs_od_residual":float(np.max(np.abs(res))),"od_residual_sum":float(np.sum(res)),
         "od_residual_l1":float(np.sum(np.abs(res))),"max_link_reconstruction_error":float(np.max(np.abs(v-v_path))),
         "objective_checked":objective(v_path,links),"signed_full_gap":float(gap),"full_relative_gap":float(rel),
         "signed_pool_gap":float(pool_gap),"pool_relative_gap":float(pool_gap/max(total,1e-12)),
         "demand_total":float(np.sum(q)),"positive_links_strict":int(np.sum(v_path>0)),
         "positive_links_display_1e_minus_6":int(np.sum(v_path>1e-6)),"gates":GATES}
    if fw_run:
        fw=json.loads((Path(fw_run)/"run.json").read_text(encoding="utf-8"))
        if fw["instance_signature"]!=m["instance_signature"]:raise ValueError("FW signature mismatch")
        out["objective_minus_fw"]=out["objective_checked"]-fw["objective"]
    valid=(np.isfinite(f).all() and np.isfinite(v).all() and np.min(f)>=-GATES["negative_flow_abs"]
           and np.min(v)>=-GATES["negative_flow_abs"] and out["max_link_reconstruction_error"]<=GATES["link_reconstruction_abs"]
           and all(abs(res[i])<=GATES["max_od_error_abs"]+GATES["max_od_error_rel"]*max(1,q[i]) for i in range(len(q)))
           and out["od_residual_l1"]/max(out["demand_total"],1e-12)<=GATES["total_od_l1_rel"])
    out["status"]=("SOLVED_WITHIN_DECLARED_TOLERANCE" if valid and abs(rel)<=GATES["full_relative_gap_abs"]
                   else "RESTRICTED_POOL_ONLY" if valid and abs(out["pool_relative_gap"])<=GATES["full_relative_gap_abs"]
                   else "SOLVER_TERMINATED_BUT_NOT_ACCEPTED")
    return out,res,f,v,v_path


def controller(a):
    import numpy as np
    t=time.perf_counter();out=Path(a.output)
    if out.exists() and any(out.iterdir()):raise ValueError("nonempty L3 output")
    out.mkdir(parents=True)
    m,links,od,paths,A,C,f0,q,data,comp,major,minor=load_case(a.instance,a.pool,a.basis)
    # Explicit native model gate; Python expression plus MUMPS factor workspace.
    expression_terms=int(np.count_nonzero(np.abs(comp["D"])>1e-12))+int(np.count_nonzero(np.abs(comp["M"])>1e-12))+int(np.count_nonzero(np.abs(comp["U_r"])>1e-12))
    estimated=expression_terms*800+(len(links)+len(paths)+len(od))**2*64
    if estimated>a.memory_ceiling:
        result={"status":"RESOURCE_LIMIT","reason":"conservative native expression/factorization estimate exceeds declared ceiling",
                "estimated_bytes":estimated,"ceiling_bytes":a.memory_ceiling,"expression_terms":expression_terms,
                "instance_signature":m["instance_signature"]}
        atomic_json(out/"status.json",result);return result
    lam=np.zeros(len(od));rho=10.0;history=[]
    env=os.environ.copy();env["PATH"]=str(Path(a.ipopt).resolve().parent)+os.pathsep+env.get("PATH","")
    env.update({"PYTHONDONTWRITEBYTECODE":"1","OMP_NUM_THREADS":"2","OPENBLAS_NUM_THREADS":"2","MKL_NUM_THREADS":"2"})
    for key in ("TEMP","TMP","TMPDIR"):env[key]=str(Path(a.temp).resolve())
    Path(a.temp).mkdir(parents=True,exist_ok=True)
    for outer in range(1,a.max_outer+1):
        remaining=min(a.inner_timeout,a.total_timeout-(time.perf_counter()-t))
        if remaining<=0:break
        cmd=[sys.executable,"-B",str(Path(__file__).resolve()),"worker","--instance",a.instance,"--pool",a.pool,
             "--basis",a.basis,"--output",str(out),"--source",a.source,"--ipopt",a.ipopt,
             "--lambda-json",json.dumps(lam.tolist()),"--rho",str(rho),"--outer",str(outer)]
        log=out/f"outer_{outer:02d}_controller.log"
        samples=[]
        with log.open("w",encoding="utf-8") as stream:
            proc=subprocess.Popen(cmd,stdout=stream,stderr=subprocess.STDOUT,cwd=str(out),env=env,
                                  creationflags=subprocess.CREATE_NEW_PROCESS_GROUP|subprocess.CREATE_NO_WINDOW if os.name=="nt" else 0)
            outer_start=time.perf_counter();code=None
            while proc.poll() is None:
                elapsed=time.perf_counter()-outer_start
                if elapsed>=remaining:
                    if os.name=="nt":subprocess.run(["taskkill","/PID",str(proc.pid),"/T","/F"],capture_output=True)
                    else:proc.kill()
                    break
                sample=task_tree_memory(proc.pid)
                sample["elapsed_seconds"]=elapsed
                samples.append(sample)
                time.sleep(2)
            else:code=proc.returncode
        atomic_json(out/f"outer_{outer:02d}_resource_samples.json",{"samples":samples,
            "sampled_peak_tree_working_set":max((s.get("working_set_sum",0) for s in samples),default=None),
            "missed_short_peaks_possible":True})
        native_path=out/f"outer_{outer:02d}_native.json"
        rec={"outer":outer,"rho":rho,"worker_exit_code":code,"native_record_present":native_path.exists()}
        if code is None:rec["status"]="RESOURCE_LIMIT_TIMEOUT";history.append(rec);break
        if not native_path.exists():rec["status"]="NATIVE_NO_RECORD";history.append(rec);break
        native=json.loads(native_path.read_text(encoding="utf-8"));rec["native_termination"]=native["termination"]
        if not native.get("solution_loaded"):rec["status"]="NATIVE_NO_RETURNED_ITERATE";history.append(rec);break
        check,res,f,v,v_path=evaluate(a.instance,a.pool,a.basis,out/f"outer_{outer:02d}_solution.npz",a.fw_run)
        atomic_json(out/f"outer_{outer:02d}_check.json",check)
        rec["check_status"]=check["status"];rec["max_abs_od_residual"]=check["max_abs_od_residual"]
        rec["full_relative_gap"]=check["full_relative_gap"]
        history.append(rec)
        if check["status"]=="SOLVED_WITHIN_DECLARED_TOLERANCE":break
        if native["termination"]!="optimal":break
        lam=lam+rho*res;rho*=2
    result={"status":history[-1].get("check_status",history[-1].get("status","NOT_EXECUTED")) if history else "RESOURCE_LIMIT",
            "attempted_outer":len(history),"history":history,"rank":comp["r"],"path_count":len(paths),
            "od_count":len(od),"link_count":len(links),"estimated_bytes":estimated,
            "ceiling_bytes":a.memory_ceiling,"total_seconds":time.perf_counter()-t,
            "instance_signature":m["instance_signature"]}
    atomic_json(out/"status.json",result)
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    sub=ap.add_subparsers(dest="action",required=True)
    for name in ("run","worker"):
        p=sub.add_parser(name);p.add_argument("--instance",required=True);p.add_argument("--pool",required=True)
        p.add_argument("--basis",required=True);p.add_argument("--output",required=True)
        p.add_argument("--source",required=True);p.add_argument("--ipopt",required=True)
        if name=="run":
            p.add_argument("--fw-run");p.add_argument("--temp",required=True)
            p.add_argument("--memory-ceiling",type=int,required=True);p.add_argument("--inner-timeout",type=float,default=600)
            p.add_argument("--total-timeout",type=float,default=2700);p.add_argument("--max-outer",type=int,default=8)
        else:
            p.add_argument("--lambda-json",required=True);p.add_argument("--rho",type=float,required=True);p.add_argument("--outer",type=int,required=True)
    a=ap.parse_args()
    try:
        result=controller(a) if a.action=="run" else worker(a)
        if a.action=="run":print(json.dumps(result,indent=2,allow_nan=False));return 0 if result["status"]=="SOLVED_WITHIN_DECLARED_TOLERANCE" else 2
        return result
    except Exception as exc:
        print(json.dumps({"status":"ERROR","action":a.action,"reason":str(exc)}),file=sys.stderr)
        return 2


if __name__=="__main__":raise SystemExit(main())
