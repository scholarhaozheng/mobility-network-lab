"""Portable Hong Kong recovered computations and explicitly separate saved-result checks.

This wrapper changes paths and invocation only. Frozen numerical implementations
are under algorithms/recovered_hk. inspect never executes an optimizer.
"""
from __future__ import annotations
import argparse, csv, hashlib, importlib.util, json, math, os, shutil, subprocess, sys, time
from pathlib import Path
from urllib.request import urlopen


def read(p):
    return json.loads(Path(p).read_text(encoding="utf-8-sig"))


def write(p, obj):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2,allow_nan=False)+"\n",encoding="utf-8")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def safe(root, relative):
    p=(Path(root)/relative).resolve()
    if not p.is_relative_to(Path(root).resolve()):
        raise ValueError("Path escapes declared root: "+relative)
    return p


def load_module(name, p):
    spec=importlib.util.spec_from_file_location(name,p)
    m=importlib.util.module_from_spec(spec); sys.modules[name]=m; spec.loader.exec_module(m)
    return m


def pinned(root, rec):
    bad=[f["path"] for f in rec["files"] if not safe(root,f["path"]).is_file() or sha(safe(root,f["path"]))!=f["sha256"]]
    if bad: raise ValueError("Pinned file mismatch: "+", ".join(bad[:12]))
    return len(rec["files"])


def stage(root, rec, out, inspect=False, input_root=None):
    w=out/"workspace"; w.mkdir(parents=True,exist_ok=True)
    for item in rec["workspaceMappings"]:
        if item.get("use")=="inspect" and not inspect: continue
        dest=safe(w,item["destination"]); dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(safe(root,item["source"]),dest)
    for d in rec.get("dataSources",[]):
        if not d.get("externalRequired"): continue
        if inspect: continue
        if not input_root: raise ValueError("Exact external input required. Supply --input-root DIRECTORY; see dataSources in the recipe.")
        src=safe(input_root,d["path"])
        if not src.is_file() or sha(src)!=d["sha256"]: raise ValueError("External snapshot absent or changed: "+d["path"])
        dest=safe(w,d["path"]); dest.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,dest)
    for d in ["hong_kong_full_stack_r2_r4/phase_b","hong_kong_full_stack_r2_r4/phase_c/case","hong_kong_gmns_pilot_r1/candidate_extract"]:
        (w/d).mkdir(parents=True,exist_ok=True)
    return w


def call(argv,cwd,log,timeout=7200,allowed=(0,)):
    env=os.environ.copy(); env.update(PYTHONDONTWRITEBYTECODE="1",OMP_NUM_THREADS="2",OPENBLAS_NUM_THREADS="2",MKL_NUM_THREADS="2")
    with log.open("w",encoding="utf-8") as stream:
        result=subprocess.run([str(a) for a in argv],cwd=cwd,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=timeout,
                              creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
    if result.returncode not in allowed:
        raise RuntimeError("Computation failed (exit %s); see %s"%(result.returncode,log))
    return result.returncode


def run_computation(root,rec,out,w,args):
    rid=rec["id"]; py=sys.executable; commands=[]
    def python(script,*argv):
        cmd=[py,"-B",str(script),*map(str,argv)]; commands.append(cmd)
        return call(cmd,w,out/("command-%02d.log"%len(commands)))
    p=w/"hong_kong_gmns_pilot_r1"; f=w/"hong_kong_full_stack_r2_r4"
    if rec.get("pipeline"):
        for filename in rec["pipeline"]: python(w/filename)
    elif rid.startswith("HK-H1"):
        h=w/"h1"; target=rec["resultDirectory"]
        if rid!="HK-H1-FW":
            shutil.copytree(root/"examples/hong-kong/recovered-r14/h1/saved/H1_FW",h/"H1_FW",dirs_exist_ok=True)
        if rid=="HK-H1-FW":
            python(h/"mcl_assignment.py","solve","--method","fw","--instance",h/"H1_instance","--output",h/target)
        elif rid=="HK-H1-FINITE":
            python(h/"mcl_path_methods.py","full-path","--instance",h/"H1_instance","--pool",h/"H1_pool","--output",h/target,"--maxiter","300")
        else:
            ipopt=args.ipopt or shutil.which("ipopt")
            if not ipopt: raise ValueError("Native L3 requires IPOPT/MUMPS. Pass --ipopt EXECUTABLE; use the documented Python 3.9 environment.")
            rank="26" if rid.endswith("R26") else "52"
            python(h/"mcl_native_l3.py","run","--instance",h/"H1_instance","--pool",h/"H1_pool","--basis",h/("H1_basis_rank"+rank),
                   "--output",h/target,"--source",h/"scalable/diagnostic_l3_source.py","--ipopt",ipopt,"--fw-run",h/"H1_FW",
                   "--temp",out/"native-temp","--memory-ceiling","2147483648","--total-timeout","1800","--max-outer","8")
    elif rid=="HK10-CG-R5":
        c=w/"cg"; m=read(c/"run-policy.json")
        m.update(dynamic_data_dir=str(c/"case"),demand_file=str(c/"case/dynamic_demand.csv"),dynamic_arc_file=str(c/"case/dynamic_arc.csv"),
                 current_candidate_pool_file=str(c/"case/dynamic_columns.csv"),output_root=str(c/"cg_run"))
        m.pop("arc_lp_reference_summary_path",None); write(c/"run-policy.json",m)
        python(c/"source/run_full_cg_v1.py","--input-manifest",c/"run-policy.json","--output-dir",c/"cg_run","--benchmark-id",m["benchmark_id"],
               "--max-phase-i-rounds","120","--max-phase-ii-rounds","25","--max-candidates-per-demand","4","--runtime-cap-seconds","7200",
               "--no-mutate-accepted-outputs","--phase-ii-pricing-mode","k_shortest","--k-shortest-k","4","--phase-ii-add-policy","add_best_one_per_demand",
               "--phase-ii-progress-policy","allow_degenerate_nonincrease","--reference-objective","75.03632985794819")
    elif rid=="HK10-CG-R5-CLOSURE":
        raise ValueError("Closure is an independent saved-result validation, not a new optimizer. Use inspect, or verify the output of HK10-CG-R5.")
    elif rid=="HK4-ADMM-R3":
        a=w/"admm"
        python(a/"src/admm_solver.py","--arc",a/"input/dynamic_arc.csv","--demand",a/"input/dynamic_demand.csv","--output",a/"saved",
               "--policy",a/"ADMM_R3_FROZEN_POLICY.json","--variant","R2_S","--case","HK_R3_FRESH_4OD_30S_50STEPS")
    else:
        raise ValueError("This record is a historical failure or scope boundary; use inspect.")
    return commands


def csv_compare(actual,expected):
    def rows(p):
        with Path(p).open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
    a,b=rows(actual),rows(expected)
    if len(a)!=len(b):return {"pass":False,"rows":len(a),"expected_rows":len(b)}
    maximum=0.0
    for x,y in zip(a,b):
        if set(x)!=set(y):return {"pass":False,"reason":"columns"}
        for k in x:
            try:
                u,v=float(x[k]),float(y[k])
                if not math.isfinite(u) or not math.isfinite(v):
                    if x[k]!=y[k]:return {"pass":False,"reason":"nonfinite"}
                    continue
                delta=abs(u-v)/max(1,abs(v));maximum=max(maximum,delta)
            except (ValueError,TypeError):
                if x[k]!=y[k]:return {"pass":False,"reason":"non-numeric field mismatch"}
    return {"pass":maximum<=1e-8,"rows":len(a),"max_scaled_absolute_difference":maximum}


def json_compare(actual,expected):
    a,b=read(actual),read(expected); diffs=[]; count=0
    def walk(x,y):
        nonlocal count
        if isinstance(y,(int,float)) and not isinstance(y,bool):
            count+=1
            if not isinstance(x,(int,float)) or abs(x-y)>1e-8*max(1,abs(y)):diffs.append("numeric mismatch")
        elif isinstance(y,dict):
            for k,v in y.items():
                if isinstance(v,(dict,list,int,float)) and not isinstance(v,bool):walk(x.get(k) if isinstance(x,dict) else None,v)
        elif isinstance(y,list):
            if not isinstance(x,list) or len(x)!=len(y):diffs.append("array length mismatch")
            else:
                for u,v in zip(x,y):walk(u,v)
    walk(a,b)
    return {"pass":count>0 and not diffs,"numeric_fields":count,"mismatches":len(diffs)}


def numerical(root,rec,w,inspection):
    rid=rec["id"]; checks={}; metrics={}
    if rid.startswith("HK-H1"):
        h=w/"h1"; sys.path.insert(0,str(h))
        if rid=="HK-H1-FW":
            m=load_module("mcl_assignment",h/"mcl_assignment.py")
            info=read(h/"H1_FW/run.json");info["instance_path"]=str(h/"H1_instance");write(h/"H1_FW/run.json",info)
            r=m.verify(h/"H1_FW");checks["independent_fw_verification"]=r["status"]=="SOLVED_WITHIN_DECLARED_TOLERANCE";metrics=r
        else:
            m=load_module("recovered_hk_h1_check",h/"independent_check.py")
            m.SOURCE=root/"docs/assets/hong_kong/full_stack_r5/r2r4_baseline"
            kind="finite" if rid.endswith("FINITE") else "26" if rid.endswith("R26") else "52"
            r=m.check_solution(kind);checks["independent_original_unit_gates"]=r["status"]=="SOLVED_WITHIN_DECLARED_TOLERANCE";metrics=r
    elif rid in ("HK10-CG-R5","HK10-CG-R5-CLOSURE"):
        c=w/"cg";m=load_module("recovered_hk_independent_closure",c/"source/independent_pricing_closure.py")
        r=m.evaluate_files(c/"case",c/"cg_run/full_cg_v1_phase_ii_final_pool.csv",c/"cg_run/full_cg_v1_phase_ii_final_dual_solution.json",
                           c/"cg_run/full_cg_v1_phase_ii_final_solution_by_column.csv")
        checks["independent_full_pricing_closure"]=r["status"]=="PASS" and r["closure_pass"]
        metrics={k:v for k,v in r.items() if k!="by_demand"}
        checks["same_graph_lp_objective"]=abs(r["objective_recomputed"]-75.03632985794819)<=1e-6
    elif rid=="HK4-ADMM-R3":
        a=w/"admm";sys.path.insert(0,str(a/"src"))
        m=load_module("recovered_hk_admm_evaluator",a/"src/independent_admm_evaluator.py")
        r=m.evaluate_files(a/"input/dynamic_arc.csv",a/"input/dynamic_demand.csv",a/"saved",read(a/"ADMM_R3_FROZEN_POLICY.json"))
        checks["independent_original_unit_admm_gates"]=r["status"]=="PASS"
        metrics={k:v for k,v in r.items() if k not in ("physical_link_flow","local")}
    elif inspection:
        # This checks published saved outputs, not the omitted raw data or a fresh solve.
        checks["saved_evidence_files_present"]=all(safe(root,p).is_file() for p in rec["savedEvidence"])
        metrics={"saved_evidence_files":len(rec["savedEvidence"]),"numerical_recalculation":False}
        if rec["state"]=="historical_failure":metrics["expected_scientific_outcome"]="FAILURE_RETAINED"
        if rec["state"]=="scope_only":metrics["expected_scientific_outcome"]="NO_OPTIMIZATION_RESULT"
    else:
        for idx,o in enumerate(rec.get("expectedOutputs",[])):
            result=(json_compare if o["generated"].endswith(".json") else csv_compare)(w/o["generated"],root/o["reference"])
            checks["table_%02d_matches"%idx]=result["pass"];metrics[o["generated"]]=result
        if not checks:raise ValueError("No numerical output comparison configured")
    return checks,metrics


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("action",choices=["run","verify","inspect","acquire"])
    p.add_argument("--repo-root",type=Path,default=Path(__file__).resolve().parents[2]);p.add_argument("--record",required=True)
    p.add_argument("--output",type=Path);p.add_argument("--run",type=Path);p.add_argument("--input-root",type=Path);p.add_argument("--ipopt")
    a=p.parse_args();root=a.repo_root.resolve();catalog=read(root/"experiments/recovered/hong-kong.json")
    rec=next(x for x in catalog["records"] if x["id"]==a.record);start=time.perf_counter()
    if a.action=="acquire":
        if not a.output:raise ValueError("--output is required")
        for d in rec["dataSources"]:
            if not d.get("externalRequired"):continue
            if d["mode"]=="supply_exact_snapshot":raise ValueError("Supply original snapshot locally: "+d["path"])
            dest=safe(a.output,d["path"]);dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists():
                if sha(dest)!=d["sha256"]:raise ValueError("Existing input hash mismatch: "+d["path"])
                continue
            with urlopen(d["url"],timeout=180) as response:data=response.read(200_000_001)
            if len(data)>200_000_000 or hashlib.sha256(data).hexdigest()!=d["sha256"]:raise ValueError("Provider snapshot changed: "+d["path"])
            dest.write_bytes(data)
        return 0
    count=pinned(root,rec)
    out=(a.run if a.action=="verify" else a.output)
    if out is None:raise ValueError("Specify --output for run/inspect, or --run for verify")
    out=out.resolve()
    if out.is_relative_to(root):raise ValueError("Output must be outside the repository to keep private acquired inputs and generated outputs out of version control")
    commands=[]
    if a.action=="verify":
        receipt=read(out/"execution.json")
        if receipt["record"]!=rec["id"]:raise ValueError("Run identity mismatch")
        inspection=receipt["action"]=="inspect";w=out/"workspace"
    else:
        if out.exists() and any(out.iterdir()):raise ValueError("Output directory must be empty")
        out.mkdir(parents=True,exist_ok=True);inspection=a.action=="inspect"
        w=stage(root,rec,out,inspection,a.input_root)
        if not inspection:commands=run_computation(root,rec,out,w,a)
        write(out/"execution.json",{"record":rec["id"],"action":a.action,"commands":commands,
              "fresh_computation":not inspection,"scope":rec["scope"],"recipe_sha256":sha(root/"experiments/recovered/hong-kong.json")})
    checks,metrics=numerical(root,rec,w,inspection);checks["pinned_source_input_files"]=count>0
    report={"record":rec["id"],"success":bool(checks) and all(checks.values()),"checks":checks,"metrics":metrics,
            "optimizer_calls":0,"evidence_basis":"independent_saved_result_validation" if inspection and rec.get("independentSavedValidator") else "saved_output_integrity_only" if inspection else "fresh_computation_independently_checked",
            "fresh_solver_run":not inspection and rec.get("usesOptimizer",False),"wall_seconds":time.perf_counter()-start,
            "note":"optimizer_calls counts this verifier only; run commands, if any, are recorded separately in execution.json"}
    write(out/"verification.json",report);print(json.dumps(report,allow_nan=False));return 0 if report["success"] else 2


if __name__=="__main__":
    try:raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"success":False,"error":str(exc)}),file=sys.stderr);raise SystemExit(2)
