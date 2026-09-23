"""Foreground, resource-bounded orchestration of the frozen native L3 cases."""
import ctypes
import datetime
import json
import os
import pathlib
import subprocess
import sys
import time
from ctypes import wintypes

import numpy as np

from common import ROOT, PYTHON, SOLVER, CONFIGS, IPOPT_OPTIONS, dump, load_case, sha

MAX_INNER_SECONDS=600
MAX_CONFIG_SECONDS=1500
MAX_TOTAL_HEAVY_SECONDS=3600
MAX_OUTER=8
OUTPUT_BUDGET_BYTES=2*1024**3

class MEMORYSTATUSEX(ctypes.Structure):
    _fields_=[("dwLength",wintypes.DWORD),("dwMemoryLoad",wintypes.DWORD),
             ("ullTotalPhys",ctypes.c_ulonglong),("ullAvailPhys",ctypes.c_ulonglong),
             ("ullTotalPageFile",ctypes.c_ulonglong),("ullAvailPageFile",ctypes.c_ulonglong),
             ("ullTotalVirtual",ctypes.c_ulonglong),("ullAvailVirtual",ctypes.c_ulonglong),
             ("ullAvailExtendedVirtual",ctypes.c_ulonglong)]

def available_mib():
    m=MEMORYSTATUSEX();m.dwLength=ctypes.sizeof(MEMORYSTATUSEX)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)): return None
    return m.ullAvailPhys/1024**2

def process_sample(pid,started_iso):
    command=(f"$cut=[datetime]'{started_iso}'; "
             f"Get-Process -Name python,ipopt -ErrorAction SilentlyContinue | "
             f"Where-Object {{$_.Id -eq {pid} -or ($_.ProcessName -eq 'ipopt' -and $_.StartTime -ge $cut)}} | "
             "Select-Object Id,ProcessName,WorkingSet64,PeakWorkingSet64,PrivateMemorySize64,StartTime | ConvertTo-Json -Compress")
    try:
        r=subprocess.run(["powershell","-NoProfile","-Command",command],capture_output=True,text=True,timeout=10)
        return json.loads(r.stdout) if r.stdout.strip() else []
    except Exception as exc:
        return {"measurement_error":repr(exc)}

def terminate_own_tree(pid):
    return subprocess.run(["taskkill","/PID",str(pid),"/T","/F"],capture_output=True,text=True,timeout=20)

def run_command(args,log_path,timeout,kind,city,config,outer,env):
    started=time.time();started_iso=datetime.datetime.now().isoformat()
    with log_path.open("w",encoding="utf-8") as stream:
        proc=subprocess.Popen(args,cwd=str(ROOT),env=env,stdout=stream,stderr=subprocess.STDOUT,
                              creationflags=subprocess.CREATE_NEW_PROCESS_GROUP|subprocess.CREATE_NO_WINDOW)
        low_samples=0;next_sample=0;reason=None
        while proc.poll() is None:
            elapsed=time.time()-started
            if elapsed>=timeout:
                reason="TIME_LIMIT"
                terminate_own_tree(proc.pid)
                break
            if elapsed>=next_sample:
                avail=available_mib()
                sample=dict(timestamp=datetime.datetime.now().isoformat(),kind=kind,city=city,config=config,
                            outer=outer,worker_pid=proc.pid,elapsed_seconds=elapsed,available_physical_mib=avail,
                            processes=process_sample(proc.pid,started_iso))
                with (ROOT/"checks"/"RESOURCE_SAMPLES.jsonl").open("a",encoding="utf-8") as f:
                    f.write(json.dumps(sample,default=str)+"\n")
                low_samples=(low_samples+1) if avail is not None and avail<100 else 0
                if low_samples>=2:
                    reason="RESOURCE_LIMIT_AVAILABLE_MEMORY_BELOW_100_MIB_TWICE"
                    terminate_own_tree(proc.pid)
                    break
                next_sample=elapsed+20
            time.sleep(1)
        try: code=proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            terminate_own_tree(proc.pid);code=None
    return dict(return_code=code,wall_seconds=time.time()-started,stop_reason=reason,worker_pid=proc.pid)

def size_tree(root):
    return sum(p.stat().st_size for p in root.rglob("*") if p.is_file())

def run_config(city,config,total_heavy,env):
    out=ROOT/"runs"/city/config
    out.mkdir(parents=True,exist_ok=True)
    data,comp,preflight=load_case(city)
    if preflight["errors"]:
        status=dict(city=city,config=config,status="FROZEN_PREFLIGHT_FAILED",errors=preflight["errors"])
        dump(out/"status.json",status);return status,total_heavy
    lam=np.zeros(data["n_od"]);rho=10.0
    history=[];config_start=time.time();status="STARTED";accepted_outer=None
    dump(out/"CONFIG.json",dict(city=city,config=config,gamma=CONFIGS[config]["gamma"],
        level=3,link_lower_bound=0,initial_rho=10.0,initial_lambda="all zeros",max_outer=8,
        ipopt_options=IPOPT_OPTIONS,source_reference_initialization_each_outer=True,
        original_space_od_tolerance="1e-6 + 1e-8*max(1,abs(q)) per OD",
        path_and_bounds_abs_tolerance=1e-8,
        link_abs_tolerance="1e-6 + 1e-8*max(1,abs(reconstructed_link_flow))"))
    for outer in range(1,MAX_OUTER+1):
        remaining=min(MAX_INNER_SECONDS,MAX_CONFIG_SECONDS-(time.time()-config_start),
                      MAX_TOTAL_HEAVY_SECONDS-total_heavy)
        if remaining<=0:
            status="TIME_BUDGET_EXHAUSTED";break
        if size_tree(ROOT)>OUTPUT_BUDGET_BYTES:
            status="OUTPUT_BUDGET_EXHAUSTED";break
        np.savez_compressed(out/f"outer_{outer:02d}_state.npz",lambda_used=lam,rho=np.array([rho]))
        args=[str(PYTHON),"-B",str(ROOT/"runner"/"solve_inner.py"),city,config,str(outer)]
        print(f"START {city} {config} outer {outer} rho={rho} timeout={remaining:.1f}s",flush=True)
        obs=run_command(args,out/f"outer_{outer:02d}_controller.log",remaining,"native_inner",city,config,outer,env)
        total_heavy+=obs["wall_seconds"]
        row=dict(outer=outer,rho=rho,lambda_norm=float(np.linalg.norm(lam)),monitor=obs)
        native_path=out/f"outer_{outer:02d}_native.json"
        if native_path.exists(): row["native"]=json.loads(native_path.read_text(encoding="utf-8"))
        if obs["stop_reason"]:
            status=obs["stop_reason"];history.append(row);break
        if not native_path.exists():
            status="WORKER_NO_NATIVE_RECORD";history.append(row);break
        native=row["native"]
        if not native.get("solution_loaded"):
            status="NATIVE_NO_RETURNED_ITERATE";history.append(row);break
        checker=[str(PYTHON),"-B",str(ROOT/"runner"/"check_inner.py"),city,config,str(outer)]
        try:
            cr=subprocess.run(checker,cwd=str(ROOT),env=env,capture_output=True,text=True,timeout=120)
            (out/f"outer_{outer:02d}_checker_stdout_stderr.log").write_text(cr.stdout+cr.stderr,encoding="utf-8")
        except subprocess.TimeoutExpired as exc:
            status="CHECKER_TIMEOUT";history.append(row);break
        check_path=out/f"outer_{outer:02d}_check.json"
        if cr.returncode!=0 or not check_path.exists():
            status="CHECKER_FAILED";row["checker_return_code"]=cr.returncode;history.append(row);break
        check=json.loads(check_path.read_text(encoding="utf-8"));row["check_summary"]={
            "accepted":check["accepted"],"criteria":check["criteria"],"stats":check["stats"]}
        history.append(row)
        print(f"RESULT {city} {config} outer {outer}: {native.get('termination')} "
              f"OD={check['stats']['max_abs_od']:.9g} failedOD={check['stats']['failed_od_count']} "
              f"minf={check['stats']['min_path_flow']:.9g} accepted={check['accepted']}",flush=True)
        dump(out/"control_history.json",history)
        if check["accepted"]:
            status="NUMERICAL_ACCEPTED";accepted_outer=outer;break
        if native.get("solver_status")!="ok" or native.get("termination")!="optimal":
            status="NONOPTIMAL_INNER_TERMINATION";break
        if not check["criteria"]["objective_decomposition_agrees_with_pyomo"] or not check["criteria"]["objective_decomposition_agrees_with_native"]:
            status="OBJECTIVE_AUDIT_FAILED";break
        residual=np.load(out/f"outer_{outer:02d}_od_residual.npy",allow_pickle=False)
        lam=lam+rho*residual
        rho*=2
    else:
        status="MAX_OUTER_NUMERICAL_CRITERIA_NOT_MET"
    final=dict(city=city,config=config,status=status,accepted_outer=accepted_outer,
               attempted_outers=len(history),wall_seconds=time.time()-config_start,
               total_heavy_seconds_after=total_heavy)
    dump(out/"status.json",final)
    dump(out/"control_history.json",history)
    print(f"END {city} {config}: {status}",flush=True)
    return final,total_heavy

def main():
    assert pathlib.Path.cwd().resolve()==ROOT.resolve(),"Controller cwd must be fresh run root"
    if not SOLVER.is_file() or not PYTHON.is_file():
        raise RuntimeError("Set MCL_NATIVE_PYTHON and MCL_IPOPT to existing native-environment executables")
    env=os.environ.copy()
    env["PATH"]=str(SOLVER.parent)+os.pathsep+str(PYTHON.parent/"Scripts")+os.pathsep+env.get("PATH","")
    env["PYTHONDONTWRITEBYTECODE"]="1"
    for k in ("TMP","TEMP","TMPDIR","MPLCONFIGDIR"):
        env[k]=str(ROOT/"tmp")
    dump(ROOT/"configs"/"EXECUTION.json",dict(python=str(PYTHON),solver=str(SOLVER),
          source_sha256=sha(ROOT/"source_snapshot"/"run_diagnostic_levels.py"),
          cwd=str(ROOT),tmp=str(ROOT/"tmp"),ipopt_options=IPOPT_OPTIONS,
          max_inner_seconds=MAX_INNER_SECONDS,max_config_seconds=MAX_CONFIG_SECONDS,
          max_total_heavy_seconds=MAX_TOTAL_HEAVY_SECONDS,max_outer=MAX_OUTER,
          output_budget_bytes=OUTPUT_BUDGET_BYTES,initial_available_physical_mib=available_mib()))
    total_heavy=0.0;statuses={}
    # Keep the recorded Sioux A-before-B sequence; Anaheim is a separate supplemental record.
    for city in ("SiouxFalls",):
        status,total_heavy=run_config(city,"A_REG001",total_heavy,env)
        statuses[f"{city}/A_REG001"]=status
    for city in ("SiouxFalls",):
        if statuses[f"{city}/A_REG001"]["status"]=="NUMERICAL_ACCEPTED":
            status,total_heavy=run_config(city,"B_BECKMANN",total_heavy,env)
        else:
            status=dict(city=city,config="B_BECKMANN",status="SKIPPED_A_NOT_ACCEPTED",
                        reason=statuses[f"{city}/A_REG001"]["status"])
            out=ROOT/"runs"/city/"B_BECKMANN";out.mkdir(parents=True,exist_ok=True)
            dump(out/"status.json",status)
        statuses[f"{city}/B_BECKMANN"]=status
    dump(ROOT/"checks"/"CONTROLLER_SUMMARY.json",dict(statuses=statuses,total_heavy_seconds=total_heavy))
    print(json.dumps({k:v["status"] for k,v in statuses.items()},indent=2),flush=True)

if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser(description="Opt-in Sioux Falls native Diagnostic L3 controller. Requires staged fresh run root and native Pyomo/IPOPT/MUMPS environment.")
    parser.add_argument("--execute-native",action="store_true",help="explicitly authorize a NEW native solver run")
    args=parser.parse_args()
    if not args.execute_native:
        parser.error("native solve is opt-in; use tools/mcl_results.py for saved inspection")
    main()
