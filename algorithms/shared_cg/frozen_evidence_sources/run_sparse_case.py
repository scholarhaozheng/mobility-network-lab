"""Measured-resource launcher for the common sparse-CG solve entry.

Invoke this only inside the established mcl_batch_guard heavy lock.
"""
from pathlib import Path
import argparse,json,os,subprocess,sys,time
from run_case import system_memory,tree_private,save,sha
R=Path(__file__).resolve().parent
def main():
 a=argparse.ArgumentParser()
 a.add_argument("--config",required=True)
 a.add_argument("--budget",required=True)
 args=a.parse_args()
 config=Path(args.config).resolve()
 budget_path=Path(args.budget).resolve()
 c=json.loads(config.read_text(encoding="utf-8-sig"))
 b=json.loads(budget_path.read_text(encoding="utf-8-sig"))
 output=Path(c["output_dir"]).resolve()
 if output.exists() and any(output.iterdir()):
  raise FileExistsError("existing sparse solver output")
 output.parent.mkdir(parents=True,exist_ok=True)
 receipt_path=output.parent/"RUN_RECEIPT.json"
 initial=system_memory()
 core_root=Path(c.get("core_root",str(R))).resolve()
 entry=core_root/"shared_cg"/"solve.py"
 source_files={str(p):sha(p) for p in sorted((core_root/"shared_cg").glob("*.py"))}
 receipt={"schema":"SHARED_CG_SPARSE_ACTUAL_RUN_R1","case_id":c["case_id"],
          "build_id":c["build_id"],"entry":str(entry),"source_files":source_files,
          "config":str(config),"config_sha256":sha(config),
          "budget":str(budget_path),"budget_sha256":sha(budget_path),
          "initial_memory":initial,"started":False}
 if initial["physical_available"]<b["minimum_launch_physical_bytes"] or initial["pagefile_available"]<b["minimum_launch_pagefile_bytes"]:
  receipt["status"]="CURRENT_OS_PRESSURE_NO_START";save(receipt_path,receipt)
  print(receipt["status"]);return 2
 command=[sys.executable,"-B","-m","shared_cg.solve","--config",str(config)]
 env=os.environ.copy()
 env["PYTHONPATH"]=str(core_root)+os.pathsep+env.get("PYTHONPATH","")
 env["PYTHONDONTWRITEBYTECODE"]="1"
 env["OMP_NUM_THREADS"]=env["OPENBLAS_NUM_THREADS"]=env["MKL_NUM_THREADS"]="1"
 receipt["command"]=command
 samples=[];breaches=0;stop=None;started=time.monotonic()
 with (output.parent/"solver_stdout.log").open("w",encoding="utf-8") as log:
  proc=subprocess.Popen(command,cwd=str(core_root),env=env,stdout=log,stderr=subprocess.STDOUT,
                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP|subprocess.CREATE_NO_WINDOW)
  receipt.update(started=True,status="RUNNING",pid=proc.pid)
  save(receipt_path,receipt)
  print("Sparse CG started",c["case_id"],proc.pid,flush=True)
  while proc.poll() is None:
   elapsed=time.monotonic()-started
   memory=system_memory()
   private,processes=tree_private(proc.pid)
   samples.append({"elapsed_seconds":elapsed,"os":memory,
                   "tree_private_bytes":private,"processes":processes})
   breach=(private>b["maximum_tree_private_bytes"] or
           memory["physical_available"]<b["minimum_runtime_physical_bytes"] or
           memory["pagefile_available"]<b["minimum_runtime_pagefile_bytes"])
   breaches=breaches+1 if breach else 0
   if breaches>=3 or elapsed>=b["solver_wall_seconds"]:
    stop="MEASURED_RESOURCE_LIMIT" if breaches>=3 else "WALL_BUDGET"
    subprocess.run(["taskkill","/PID",str(proc.pid),"/T","/F"],capture_output=True)
    break
   time.sleep(b["sampling_seconds"])
  proc.wait()
 receipt.update(exit_code=proc.returncode,elapsed_seconds=time.monotonic()-started,
                sampled_peak_private_bytes=max((x["tree_private_bytes"] for x in samples),default=0),
                sampled_min_physical_bytes=min((x["os"]["physical_available"] for x in samples),default=None),
                stop_reason=stop,status=stop or ("SOLVER_EXIT_ZERO" if proc.returncode==0 else "SOLVER_EXIT_NONZERO"))
 save(output.parent/"RESOURCE_SAMPLES.json",{"sampling_seconds":b["sampling_seconds"],"samples":samples})
 save(receipt_path,receipt)
 print(json.dumps({x:receipt[x] for x in ("status","exit_code","elapsed_seconds","sampled_peak_private_bytes")}),flush=True)
 return 0 if receipt["status"]=="SOLVER_EXIT_ZERO" else 2
if __name__=="__main__":raise SystemExit(main())
