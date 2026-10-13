"""One input-configured shared-CG case launch with real resource sampling.

Invoke only through the established mcl_batch_guard heavy lock.
"""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
import psutil

R=Path(__file__).resolve().parent
def j(p):return json.loads(Path(p).read_text(encoding="utf-8-sig"))
def save(p,value):
    p=Path(p)
    p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+".tmp")
    tmp.write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    os.replace(tmp,p)
def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for block in iter(lambda:f.read(1048576),b""):h.update(block)
    return h.hexdigest()
def system_memory():
    m=psutil.virtual_memory()
    s=psutil.swap_memory()
    return {"physical_available":m.available,"pagefile_available":s.free}
def tree_private(pid):
    try:
        root=psutil.Process(pid)
        group=[root]+root.children(recursive=True)
    except psutil.Error:return 0,[]
    rows=[]
    for proc in group:
        try:
            mem=proc.memory_info()
            rows.append({"pid":proc.pid,"name":proc.name(),
                         "rss":mem.rss,"private":getattr(mem,"private",mem.rss)})
        except psutil.Error:pass
    return sum(x["private"] for x in rows),rows
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--case-id",required=True)
    ap.add_argument("--build",default="legacy_baseline0")
    a=ap.parse_args()
    build_cfg=R/"cases"/(a.case_id+"__"+a.build+".json")
    cfg=j(build_cfg if build_cfg.is_file() else R/"cases"/(a.case_id+".json"))
    if cfg["case_id"]!=a.case_id or cfg["build"]!=a.build:raise ValueError("case/build mismatch")
    budget=j(R/cfg["budget"])
    manifest=R/cfg["input_manifest"]
    m=j(manifest)
    output=R/"runs"/a.build/a.case_id/"solver"
    receipt_root=output.parent
    if output.exists() and any(output.iterdir()):raise ValueError("existing solver output")
    if Path(m["output_root"]).resolve()!=output.resolve():raise ValueError("manifest output mismatch")
    receipt_root.mkdir(parents=True,exist_ok=True)
    initial=system_memory()
    src=R/a.build/"source"
    entry=src/"run_full_cg_v1.py"
    source_hashes={f.name:sha(f) for f in sorted(src.glob("*.py"))}
    rec={"schema":"SHARED_CG_ACTUAL_RUN_R2","case_id":a.case_id,
         "build":a.build,"source_entry":str(entry),"source_entry_sha256":sha(entry),
         "source_snapshot_file_count":len(source_hashes),
         "source_snapshot_module_hashes":source_hashes,
         "input_manifest":str(manifest),"input_manifest_sha256":sha(manifest),
         "initial_memory":initial,"started":False}
    if cfg.get("trace_real_calls",False):
        rec["trace_wrapper_sha256"]=sha(R/"trace_old_core.py")
    if (initial["physical_available"]<budget["minimum_launch_physical_bytes"] or
        initial["pagefile_available"]<budget["minimum_launch_pagefile_bytes"]):
        rec["status"]="CURRENT_OS_PRESSURE_NO_START"
        save(receipt_root/"RUN_RECEIPT.json",rec)
        print(rec["status"],flush=True)
        return 2
    c=cfg["cli"]
    launch_entry=R/"trace_old_core.py" if cfg.get("trace_real_calls",False) else entry
    prefix=[sys.executable,"-B",str(launch_entry)]
    if cfg.get("trace_real_calls",False):
        prefix+=["--core-source-root",str(src)]
    cmd=prefix+[
         "--input-manifest",str(manifest),"--output-dir",str(output),
         "--benchmark-id",cfg["benchmark_id"],
         "--max-phase-i-rounds",str(c["max_phase_i_rounds"]),
         "--max-phase-ii-rounds",str(c["max_phase_ii_rounds"]),
         "--max-candidates-per-demand",str(c["max_candidates_per_demand"]),
         "--phase-ii-pricing-mode",c["phase_ii_pricing_mode"],
         "--k-shortest-k",str(c["k_shortest_k"]),
         "--phase-ii-add-policy",c["phase_ii_add_policy"],
         "--phase-ii-progress-policy",c["phase_ii_progress_policy"],
         "--phase-ii-objective-tolerance",str(c["phase_ii_objective_tolerance"]),
         "--max-consecutive-degenerate-commits",str(c["max_consecutive_degenerate_commits"]),
         "--phase-ii-repeated-state-limit",str(c["phase_ii_repeated_state_limit"]),
         "--max-phase-ii-candidates-per-demand",str(c["max_phase_ii_candidates_per_demand"]),
         "--max-phase-ii-candidates-per-round",str(c["max_phase_ii_candidates_per_round"]),
         "--runtime-cap-seconds",str(c["runtime_cap_seconds"])]
    if c["no_mutate_accepted_outputs"]:cmd.append("--no-mutate-accepted-outputs")
    if c["write_review_artifacts"]:cmd.append("--write-review-artifacts")
    if "reference_objective" in c:
        cmd+=["--reference-objective",str(c["reference_objective"])]
    if "reference_summary" in c:
        cmd+=["--reference-summary",c["reference_summary"]]
    env=os.environ.copy()
    env["PYTHONPATH"]=str(src)+os.pathsep+env.get("PYTHONPATH","")
    env["PYTHONDONTWRITEBYTECODE"]="1"
    env["OMP_NUM_THREADS"]=env["OPENBLAS_NUM_THREADS"]=env["MKL_NUM_THREADS"]="1"
    rec["command"]=cmd
    samples=[]
    breaches=0
    stop_reason=None
    start=time.monotonic()
    with (receipt_root/"solver_stdout.log").open("w",encoding="utf-8") as log:
        proc=subprocess.Popen(cmd,cwd=str(R),env=env,stdout=log,stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP|subprocess.CREATE_NO_WINDOW)
        rec.update(started=True,status="RUNNING",solver_pid=proc.pid)
        save(receipt_root/"RUN_RECEIPT.json",rec)
        print("CG solver started",a.case_id,proc.pid,flush=True)
        while proc.poll() is None:
            elapsed=time.monotonic()-start
            osmem=system_memory()
            private,processes=tree_private(proc.pid)
            samples.append({"elapsed_seconds":elapsed,"os":osmem,
                            "tree_private_bytes":private,"processes":processes})
            breach=(private>budget["maximum_tree_private_bytes"] or
                    osmem["physical_available"]<budget["minimum_runtime_physical_bytes"] or
                    osmem["pagefile_available"]<budget["minimum_runtime_pagefile_bytes"])
            breaches=breaches+1 if breach else 0
            if breaches>=3 or elapsed>=budget["solver_wall_seconds"]:
                stop_reason="MEASURED_RESOURCE_LIMIT" if breaches>=3 else "WALL_BUDGET"
                subprocess.run(["taskkill","/PID",str(proc.pid),"/T","/F"],capture_output=True)
                break
            time.sleep(budget["sampling_seconds"])
        proc.wait()
    rec.update(exit_code=proc.returncode,elapsed_seconds=time.monotonic()-start,
               sampled_peak_private_bytes=max((x["tree_private_bytes"] for x in samples),default=0),
               sampled_min_physical_bytes=min((x["os"]["physical_available"] for x in samples),default=None),
               stop_reason=stop_reason,status=stop_reason or ("SOLVER_EXIT_ZERO" if proc.returncode==0 else "SOLVER_EXIT_NONZERO"))
    save(receipt_root/"RESOURCE_SAMPLES.json",{"samples":samples,"sample_seconds":budget["sampling_seconds"]})
    save(receipt_root/"RUN_RECEIPT.json",rec)
    print(json.dumps({k:rec[k] for k in ("status","exit_code","elapsed_seconds","sampled_peak_private_bytes")}),flush=True)
    return 0 if proc.returncode==0 and stop_reason is None else 2
if __name__=="__main__":sys.exit(main())
