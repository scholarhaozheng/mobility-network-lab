"""Reproduce the two frozen Boston native-L3 ranks using a separately installed native environment."""
from __future__ import annotations
import argparse,json,os,subprocess,sys
from pathlib import Path

def load(p): return json.loads(Path(p).read_text(encoding="utf-8-sig"))
def write(p,x): Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+"\n",encoding="utf-8")
def native_environment(output):
    python=Path(os.environ.get("MCL_NATIVE_PYTHON",sys.executable)).resolve()
    value=os.environ.get("MCL_IPOPT")
    if not value: raise ValueError("Set MCL_IPOPT to the independently installed IPOPT executable; see the experiment README")
    ipopt=Path(value).resolve()
    if not python.is_file() or not ipopt.is_file(): raise ValueError("Native Python/IPOPT executable not found")
    env=os.environ.copy();env.update(MCL_NATIVE_PYTHON=str(python),MCL_IPOPT=str(ipopt),TEMP=str(output/"tmp"),TMP=str(output/"tmp"),TMPDIR=str(output/"tmp"),PYTHONDONTWRITEBYTECODE="1",OMP_NUM_THREADS="2",OPENBLAS_NUM_THREADS="2",MKL_NUM_THREADS="2")
    env["PATH"]=os.pathsep.join((str(ipopt.parent),str(python.parent/"Library/bin"),str(python.parent/"Scripts"),env.get("PATH","")))
    return python,env

def execute(command,cwd,env,output,label,timeout):
    child=subprocess.run(list(map(str,command)),cwd=cwd,env=env,capture_output=True,text=True,timeout=timeout)
    (output/(label+".stdout.log")).write_text(child.stdout,encoding="utf-8");(output/(label+".stderr.log")).write_text(child.stderr,encoding="utf-8")
    if child.returncode: raise RuntimeError(label+" failed; see its stderr log")

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("action",choices=("run","verify"));p.add_argument("--repo-root",type=Path,default=Path(__file__).resolve().parents[2]);p.add_argument("--output",type=Path);p.add_argument("--run",dest="run_dir",type=Path)
    a=p.parse_args();root=a.repo_root.resolve();target=a.output if a.action=="run" else a.run_dir
    if target is None: p.error("run requires --output; verify requires --run")
    out=target.resolve();work=out/"computed";python,env=native_environment(work)
    if a.action=="run":
        if out.exists() and any(out.iterdir()): raise ValueError("Output must be new or empty")
        out.mkdir(parents=True,exist_ok=True)
        execute([sys.executable,"-B",root/"tools/prepare_native_run.py","--case","boston","--output",work],root,env,out,"prepare",120)
        execute([python,"-B",work/"checks/preflight.py"],work,env,out,"preflight",120)
        execute([python,"-u","-B",work/"adapters/controller.py","--execute-native"],work,env,out,"native-controller",2800)
    checks=[];metrics={}
    for rank in (26,52):
        state=load(work/"runs"/f"rank{rank}"/"status.json")
        outer=state.get("accepted_outer")
        if outer!=2: raise ValueError("Historical native replay must accept the frozen second outer iterate; got "+str(state))
        execute([python,"-B",work/"checks/check_returned.py","--rank",rank,"--outer",outer],work,env,out,f"verify-rank{rank}",120)
        report=load(work/"runs"/f"rank{rank}"/f"outer_{outer:02d}_check.json")
        expected=load(root/"examples/boston/assignment_methods_r1/runs"/f"rank{rank}"/"outer_02_check.json")
        delta=abs(report["objective"]["F_reconstructed_paths"]-expected["objective"]["F_reconstructed_paths"])
        checks.extend([{"name":f"rank{rank}_original_space_gates","pass":bool(report["numerical_feasibility_pass"] and report["public_eligibility_pass"])},{"name":f"rank{rank}_historical_objective","pass":delta<=1e-7}])
        metrics[str(rank)]={"accepted_outer":outer,"objective":report["objective"]["F_reconstructed_paths"],"historical_objective_delta":delta,"max_od_residual":report["raw_stats"]["max_abs_OD_residual"],"max_link_residual":report["raw_stats"]["max_abs_link_residual"],"full_network_relative_gap":report["gaps"]["full_network_relative_gap"]}
    result={"success":all(c["pass"] for c in checks),"checks":checks,"optimizer_calls":0,"metrics":metrics,"scope":"Frozen 130-path Boston native-L3 rank26 and rank52, two ALM outer steps each. A checked numerical approximation, not exact full-network UE or expanded-scale success."};result["status"]="PASS" if result["success"] else "FAIL"
    write(out/"verification.json",result);print(json.dumps(result,indent=2))
    if not result["success"]: raise SystemExit(2)
if __name__=="__main__": main()
