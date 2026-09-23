"""One new timed invocation of the unchanged frozen Boston FW source."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--inputs",type=Path,required=True);ap.add_argument("--solver",type=Path,required=True);ap.add_argument("--deps",type=Path,required=True);ap.add_argument("--out",type=Path,required=True);args=ap.parse_args()
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    run_name="boston_abs_planned_comparison_fw"
    code=("import importlib.util; "
          f"s=importlib.util.spec_from_file_location('frozen_fw',r'{args.solver.resolve()}'); "
          "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
          f"m.solve_fw_refined(r'{args.inputs.resolve()}',run_name='{run_name}',max_iter=50,cap_scale=1.0)")
    command=[sys.executable,"-B","-c",code]
    env=os.environ.copy();env.update({"PYTHONPATH":str(args.deps.resolve()),"PYTHONDONTWRITEBYTECODE":"1","OMP_NUM_THREADS":"2","OPENBLAS_NUM_THREADS":"2","MKL_NUM_THREADS":"2"})
    start=time.perf_counter()
    completed=subprocess.run(command,cwd=out,env=env,text=True,capture_output=True,timeout=600)
    wall=time.perf_counter()-start
    (out/"wrapper_stdout.txt").write_text(completed.stdout,encoding="utf-8")
    (out/"wrapper_stderr.txt").write_text(completed.stderr,encoding="utf-8")
    solution=out/(run_name+"_solution.csv");log=out/(run_name+"_fw_log.txt")
    result={"status":"FW_EXECUTED_NOW" if completed.returncode==0 and solution.exists() and log.exists() else "FW_FAILED","returncode":completed.returncode,"wall_seconds_process_including_python_startup":wall,"source_sha256":sha(args.solver),"link_sha256":sha(args.inputs/"link.csv"),"demand_sha256":sha(args.inputs/"demand.csv"),"command":command,"solution_sha256":sha(solution) if solution.exists() else None,"log_sha256":sha(log) if log.exists() else None,"peak_memory_bytes":None,"peak_memory_method":"not measured for short FW subprocess; process wall includes setup and solve"}
    (out/"run_summary.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="command"},indent=2))
    if result["status"]!="FW_EXECUTED_NOW": raise RuntimeError("FW reference failed")

if __name__=="__main__":main()
